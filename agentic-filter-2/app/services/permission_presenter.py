"""Map Permission + resource catalog rows to FE contract shape (§C, M3)."""

from __future__ import annotations

import uuid

from app.models.permission import ColumnMask, Permission, RowFilter
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin_contract import (
    FePermissionOut,
    PathLabel,
    PermissionModifierOut,
    RolePermissionsData,
    RolePermissionsSummary,
)


def _mask_modifier_label(mask: ColumnMask) -> str:
    if mask.mask_type == "PARTIAL" and mask.mask_pattern:
        return f"PARTIAL: {mask.mask_pattern}"
    return mask.mask_type


def build_path_labels(
    rr: ResourceRepository, resource_id: uuid.UUID
) -> list[PathLabel]:
    res = rr.get_resource(resource_id)
    if res is None:
        return [PathLabel(label=str(resource_id), resourceId=str(resource_id))]

    rtype = res.resource_type
    if rtype == "DATABASE":
        db = rr.get_database(resource_id)
        if db is None:
            return []
        return [PathLabel(label=db.name, resourceId=str(resource_id))]

    if rtype == "SCHEMA":
        sch = rr.get_schema(resource_id)
        if sch is None:
            return []
        db = rr.get_database(sch.database_id)
        if db is None:
            return [PathLabel(label=sch.name, resourceId=str(resource_id))]
        return [
            PathLabel(label=db.name, resourceId=str(sch.database_id)),
            PathLabel(label=sch.name, resourceId=str(resource_id)),
        ]

    if rtype == "TABLE":
        tbl = rr.get_table(resource_id)
        if tbl is None:
            return []
        sch = rr.get_schema(tbl.schema_id)
        if sch is None:
            return [PathLabel(label=tbl.name, resourceId=str(resource_id))]
        db = rr.get_database(sch.database_id)
        if db is None:
            return [
                PathLabel(label=sch.name, resourceId=str(tbl.schema_id)),
                PathLabel(label=tbl.name, resourceId=str(resource_id)),
            ]
        return [
            PathLabel(label=db.name, resourceId=str(sch.database_id)),
            PathLabel(label=sch.name, resourceId=str(tbl.schema_id)),
            PathLabel(label=tbl.name, resourceId=str(resource_id)),
        ]

    if rtype == "COLUMN":
        col = rr.get_column(resource_id)
        if col is None:
            return []
        tbl = rr.get_table(col.table_id)
        if tbl is None:
            return [PathLabel(label=col.name, resourceId=str(resource_id))]
        sch = rr.get_schema(tbl.schema_id)
        if sch is None:
            return [
                PathLabel(label=tbl.name, resourceId=str(col.table_id)),
                PathLabel(label=col.name, resourceId=str(resource_id)),
            ]
        db = rr.get_database(sch.database_id)
        if db is None:
            return [
                PathLabel(label=sch.name, resourceId=str(tbl.schema_id)),
                PathLabel(label=tbl.name, resourceId=str(col.table_id)),
                PathLabel(label=col.name, resourceId=str(resource_id)),
            ]
        return [
            PathLabel(label=db.name, resourceId=str(sch.database_id)),
            PathLabel(label=sch.name, resourceId=str(tbl.schema_id)),
            PathLabel(label=tbl.name, resourceId=str(col.table_id)),
            PathLabel(label=col.name, resourceId=str(resource_id)),
        ]

    return [PathLabel(label=rtype, resourceId=str(resource_id))]


class PermissionPresenter:
    def __init__(
        self,
        resource_repo: ResourceRepository,
        permission_repo: PermissionRepository,
    ) -> None:
        self._rr = resource_repo
        self._pr = permission_repo

    def to_fe_permission(self, perm: Permission) -> FePermissionOut:
        res = self._rr.get_resource(perm.resource_id)
        resource_type = res.resource_type if res else "DATABASE"
        action = perm.permission_type.name if perm.permission_type else "SELECT"
        path = build_path_labels(self._rr, perm.resource_id)
        modifier: PermissionModifierOut | None = None

        row_filter = self._pr.get_row_filter_for_permission(perm.id)
        if row_filter is not None:
            modifier = PermissionModifierOut(
                type="ROW_FILTER",
                label=row_filter.condition_expr,
                conditionExpression=row_filter.condition_expr,
            )
        else:
            mask = self._pr.get_column_mask_for_permission(perm.id)
            if mask is not None:
                modifier = PermissionModifierOut(
                    type="COLUMN_MASK",
                    label=_mask_modifier_label(mask),
                    maskType=mask.mask_type,
                    maskPattern=mask.mask_pattern,
                )

        effect = perm.effect.upper()
        return FePermissionOut(
            id=str(perm.id),
            resourceType=resource_type,
            path=path,
            effect=effect,
            action=action,
            modifier=modifier,
            isHighlighted=True if effect == "DENY" else None,
        )

    def list_for_role(self, role_id: uuid.UUID) -> RolePermissionsData:
        perms = self._pr.list_permissions_for_role(role_id)
        items = [self.to_fe_permission(p) for p in perms]
        allow_count = sum(1 for p in items if p.effect == "ALLOW")
        deny_count = sum(1 for p in items if p.effect == "DENY")
        modifier_count = sum(1 for p in items if p.modifier is not None)
        return RolePermissionsData(
            permissions=items,
            summary=RolePermissionsSummary(
                total=len(items),
                allowCount=allow_count,
                denyCount=deny_count,
                modifierCount=modifier_count,
            ),
        )
