"""Wizard permission grant: UUID path resolve, validation (plan §5), apply modifiers."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin_contract import PermissionGrantBody
from app.services.audit_service import record_policy_change

_PATH_CHAIN = ("database", "schema", "table", "column")
_LEAF_BY_RESOURCE_TYPE = {
    "DATABASE": "database",
    "SCHEMA": "schema",
    "TABLE": "table",
    "COLUMN": "column",
}


class GrantValidationError(Exception):
    """Grant payload or resource path failed validation."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


class PermissionGrantService:
    def __init__(
        self,
        session: Session,
        resource_repo: ResourceRepository,
        permission_repo: PermissionRepository,
        *,
        changed_by: str = "admin-api",
    ) -> None:
        self._session = session
        self._rr = resource_repo
        self._pr = permission_repo
        self._changed_by = changed_by

    def resolve_resource_id(self, body: PermissionGrantBody) -> uuid.UUID:
        """Walk resourcePath by UUID; verify hierarchy. No catalog auto-create."""
        if not body.resource_path:
            raise GrantValidationError("BAD_REQUEST", "resourcePath must not be empty")

        path_types = [seg.type.strip().lower() for seg in body.resource_path]
        if path_types != list(_PATH_CHAIN[: len(path_types)]):
            raise GrantValidationError(
                "BAD_REQUEST",
                "resourcePath must follow database → schema → table → column order",
            )

        db_id: uuid.UUID | None = None
        schema_id: uuid.UUID | None = None
        table_id: uuid.UUID | None = None
        column_id: uuid.UUID | None = None

        for seg, kind in zip(body.resource_path, path_types, strict=True):
            try:
                rid = uuid.UUID(seg.id)
            except ValueError as exc:
                raise GrantValidationError(
                    "RESOURCE_NOT_FOUND",
                    f"Invalid resource id: {seg.id}",
                    status=404,
                ) from exc

            resource = self._rr.get_resource(rid)
            if resource is None:
                raise GrantValidationError(
                    "RESOURCE_NOT_FOUND",
                    f"Resource not found: {seg.id}",
                    status=404,
                )

            if kind == "database":
                if resource.resource_type != "DATABASE":
                    raise GrantValidationError(
                        "RESOURCE_NOT_FOUND",
                        "Path segment is not a database",
                        status=404,
                    )
                db = self._rr.get_database(rid)
                if db is None:
                    raise GrantValidationError(
                        "RESOURCE_NOT_FOUND",
                        "Database not found",
                        status=404,
                    )
                db_id = rid
            elif kind == "schema":
                if db_id is None:
                    raise GrantValidationError(
                        "BAD_REQUEST",
                        "Schema segment requires a preceding database",
                    )
                if resource.resource_type != "SCHEMA":
                    raise GrantValidationError(
                        "RESOURCE_NOT_FOUND",
                        "Path segment is not a schema",
                        status=404,
                    )
                sch = self._rr.get_schema(rid)
                if sch is None or sch.database_id != db_id:
                    raise GrantValidationError(
                        "RESOURCE_NOT_FOUND",
                        "Schema not found or not under database",
                        status=404,
                    )
                schema_id = rid
            elif kind == "table":
                if schema_id is None:
                    raise GrantValidationError(
                        "BAD_REQUEST",
                        "Table segment requires a preceding schema",
                    )
                if resource.resource_type != "TABLE":
                    raise GrantValidationError(
                        "RESOURCE_NOT_FOUND",
                        "Path segment is not a table",
                        status=404,
                    )
                tbl = self._rr.get_table(rid)
                if tbl is None or tbl.schema_id != schema_id:
                    raise GrantValidationError(
                        "RESOURCE_NOT_FOUND",
                        "Table not found or not under schema",
                        status=404,
                    )
                table_id = rid
            elif kind == "column":
                if table_id is None:
                    raise GrantValidationError(
                        "BAD_REQUEST",
                        "Column segment requires a preceding table",
                    )
                if resource.resource_type != "COLUMN":
                    raise GrantValidationError(
                        "RESOURCE_NOT_FOUND",
                        "Path segment is not a column",
                        status=404,
                    )
                col = self._rr.get_column(rid)
                if col is None or col.table_id != table_id:
                    raise GrantValidationError(
                        "RESOURCE_NOT_FOUND",
                        "Column not found or not under table",
                        status=404,
                    )
                column_id = rid

        target_type = body.resource_type.strip().upper()
        leaf_kind = path_types[-1]
        if _LEAF_BY_RESOURCE_TYPE.get(target_type) != leaf_kind:
            raise GrantValidationError(
                "BAD_REQUEST",
                "resourceType does not match the last resourcePath segment",
            )

        if target_type == "COLUMN":
            if column_id is None:
                raise GrantValidationError(
                    "RESOURCE_NOT_FOUND", "Column resource not resolved", status=404
                )
            return column_id
        if target_type == "TABLE":
            if table_id is None:
                raise GrantValidationError(
                    "RESOURCE_NOT_FOUND", "Table resource not resolved", status=404
                )
            return table_id
        if target_type == "SCHEMA":
            if schema_id is None:
                raise GrantValidationError(
                    "RESOURCE_NOT_FOUND", "Schema resource not resolved", status=404
                )
            return schema_id
        if target_type == "DATABASE":
            if db_id is None:
                raise GrantValidationError(
                    "RESOURCE_NOT_FOUND", "Database resource not resolved", status=404
                )
            return db_id
        raise GrantValidationError("BAD_REQUEST", f"Unsupported resourceType: {target_type}")

    def validate_grant(self, body: PermissionGrantBody) -> uuid.UUID:
        """Plan §5 matrix; returns leaf resource_id."""
        resource_id = self.resolve_resource_id(body)

        if not body.actions:
            raise GrantValidationError("BAD_REQUEST", "actions must not be empty")

        effect = body.effect.strip().upper()
        if effect not in ("ALLOW", "DENY"):
            raise GrantValidationError("BAD_REQUEST", "effect must be ALLOW or DENY")

        target_type = body.resource_type.strip().upper()
        row_on = body.row_filter is not None and body.row_filter.enabled
        mask_on = body.column_mask is not None and body.column_mask.enabled

        if row_on and mask_on:
            raise GrantValidationError(
                "BAD_REQUEST",
                "rowFilter and columnMask cannot both be enabled",
            )

        if row_on:
            if target_type != "TABLE":
                raise GrantValidationError(
                    "INVALID_MODIFIER",
                    "rowFilter is only allowed for TABLE resources",
                )
            expr = (body.row_filter.condition_expression or "").strip()
            if not expr:
                raise GrantValidationError(
                    "BAD_REQUEST",
                    "conditionExpression is required when rowFilter is enabled",
                )

        if mask_on:
            if target_type != "COLUMN":
                raise GrantValidationError(
                    "INVALID_MODIFIER",
                    "columnMask is only allowed for COLUMN resources",
                )
            mask_type = (body.column_mask.mask_type or "PARTIAL").strip().upper()
            if mask_type == "PARTIAL":
                pattern = (body.column_mask.mask_pattern or "").strip()
                if not pattern:
                    raise GrantValidationError(
                        "BAD_REQUEST",
                        "maskPattern is required for PARTIAL columnMask",
                    )

        for action in body.actions:
            name = action.strip().upper()
            if not name:
                raise GrantValidationError("BAD_REQUEST", "action names must be non-empty")
            if self._pr.get_permission_type_by_name(name) is None:
                raise GrantValidationError(
                    "INVALID_ACTION",
                    f"Unknown permission action: {action}",
                )

        return resource_id

    def _apply_modifiers(self, permission_id: uuid.UUID, body: PermissionGrantBody) -> None:
        if body.row_filter and body.row_filter.enabled:
            expr = (body.row_filter.condition_expression or "").strip()
            self._pr.upsert_row_filter(permission_id=permission_id, condition_expr=expr)
        if body.column_mask and body.column_mask.enabled:
            mask_type = (body.column_mask.mask_type or "PARTIAL").strip().upper()
            self._pr.upsert_column_mask(
                permission_id=permission_id,
                mask_type=mask_type,
                mask_pattern=body.column_mask.mask_pattern,
            )

    def apply_grant_role(
        self,
        role_id: uuid.UUID,
        body: PermissionGrantBody,
        identity_repo: IdentityRepository,
    ) -> list[uuid.UUID]:
        """Create permissions and role links; returns new permission ids."""
        resource_id = self.validate_grant(body)
        created_ids: list[uuid.UUID] = []
        for action in body.actions:
            ptype = self._pr.get_permission_type_by_name(action.strip().upper())
            assert ptype is not None
            perm = self._pr.create_permission(
                resource_id=resource_id,
                permission_type_id=ptype.id,
                effect=body.effect.strip().upper(),
            )
            identity_repo.add_role_permission(role_id, perm.id)
            self._apply_modifiers(perm.id, body)
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="PERMISSION_CREATE",
                permission_id=perm.id,
                detail={"role_id": str(role_id)},
            )
            created_ids.append(perm.id)
        return created_ids

    def apply_grant_group(
        self,
        group_id: uuid.UUID,
        body: PermissionGrantBody,
        identity_repo: IdentityRepository,
    ) -> list[uuid.UUID]:
        resource_id = self.validate_grant(body)
        created_ids: list[uuid.UUID] = []
        for action in body.actions:
            ptype = self._pr.get_permission_type_by_name(action.strip().upper())
            assert ptype is not None
            perm = self._pr.create_permission(
                resource_id=resource_id,
                permission_type_id=ptype.id,
                effect=body.effect.strip().upper(),
            )
            identity_repo.add_group_permission(group_id, perm.id)
            self._apply_modifiers(perm.id, body)
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="PERMISSION_CREATE",
                permission_id=perm.id,
                detail={"group_id": str(group_id)},
            )
            created_ids.append(perm.id)
        return created_ids

    def apply_update_permission(
        self,
        permission_id: uuid.UUID,
        body: PermissionGrantBody,
        *,
        owner_detail: dict[str, str],
    ) -> None:
        """Update existing permission row and modifiers after validate_grant."""
        resource_id = self.validate_grant(body)
        if not body.actions:
            raise GrantValidationError("BAD_REQUEST", "actions must not be empty")
        action = body.actions[0].strip().upper()
        ptype = self._pr.get_permission_type_by_name(action)
        if ptype is None:
            raise GrantValidationError("INVALID_ACTION", f"Unknown permission action: {action}")

        perm = self._pr.get_permission(permission_id)
        if perm is None:
            raise GrantValidationError("RESOURCE_NOT_FOUND", "Permission not found", status=404)

        perm.resource_id = resource_id
        perm.permission_type_id = ptype.id
        perm.effect = body.effect.strip().upper()
        self._session.flush()
        self._pr.delete_row_filter(permission_id)
        self._pr.delete_column_mask(permission_id)
        self._apply_modifiers(permission_id, body)
        record_policy_change(
            self._session,
            changed_by=self._changed_by,
            change_type="PERMISSION_UPDATE",
            permission_id=permission_id,
            detail=owner_detail,
        )
