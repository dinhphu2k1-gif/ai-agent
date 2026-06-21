from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.identity import GroupPermission, RolePermission
from app.models.permission import ColumnMask, Permission, PermissionType, RowFilter


class PermissionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_permission_type_by_name(self, name: str) -> PermissionType | None:
        return self._session.scalars(
            select(PermissionType).where(PermissionType.name == name)
        ).first()

    def create_permission(
        self,
        *,
        resource_id: uuid.UUID,
        permission_type_id: uuid.UUID,
        effect: str,
    ) -> Permission:
        row = Permission(
            resource_id=resource_id,
            permission_type_id=permission_type_id,
            effect=effect,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get_permission(self, permission_id: uuid.UUID) -> Permission | None:
        return self._session.get(Permission, permission_id)

    def update_permission_effect(
        self, permission_id: uuid.UUID, effect: str
    ) -> Permission | None:
        row = self.get_permission(permission_id)
        if row is None:
            return None
        row.effect = effect
        self._session.flush()
        return row

    def delete_permission(self, permission_id: uuid.UUID) -> bool:
        row = self.get_permission(permission_id)
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def list_permissions(self, *, limit: int = 100, offset: int = 0) -> list[Permission]:
        return list(
            self._session.scalars(
                select(Permission).order_by(Permission.id).limit(limit).offset(offset)
            ).all()
        )

    def create_row_filter(
        self, *, permission_id: uuid.UUID, condition_expr: str
    ) -> RowFilter:
        row = RowFilter(permission_id=permission_id, condition_expr=condition_expr)
        self._session.add(row)
        self._session.flush()
        return row

    def get_column_mask_for_permission(
        self, permission_id: uuid.UUID
    ) -> ColumnMask | None:
        return self._session.scalars(
            select(ColumnMask).where(ColumnMask.permission_id == permission_id)
        ).first()

    def get_row_filter_for_permission(
        self, permission_id: uuid.UUID
    ) -> RowFilter | None:
        return self._session.scalars(
            select(RowFilter).where(RowFilter.permission_id == permission_id)
        ).first()

    def upsert_row_filter(
        self, *, permission_id: uuid.UUID, condition_expr: str
    ) -> RowFilter:
        existing = self.get_row_filter_for_permission(permission_id)
        if existing is None:
            return self.create_row_filter(
                permission_id=permission_id, condition_expr=condition_expr
            )
        existing.condition_expr = condition_expr
        self._session.flush()
        return existing

    def delete_row_filter(self, permission_id: uuid.UUID) -> None:
        row = self.get_row_filter_for_permission(permission_id)
        if row is not None:
            self._session.delete(row)
            self._session.flush()

    def delete_column_mask(self, permission_id: uuid.UUID) -> None:
        row = self.get_column_mask_for_permission(permission_id)
        if row is not None:
            self._session.delete(row)
            self._session.flush()

    def list_permissions_for_role(self, role_id: uuid.UUID) -> list[Permission]:
        return list(
            self._session.scalars(
                select(Permission)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id == role_id)
                .options(selectinload(Permission.permission_type))
                .order_by(Permission.id)
            ).all()
        )

    def list_permissions_for_group(self, group_id: uuid.UUID) -> list[Permission]:
        return list(
            self._session.scalars(
                select(Permission)
                .join(
                    GroupPermission,
                    GroupPermission.permission_id == Permission.id,
                )
                .where(GroupPermission.group_id == group_id)
                .options(selectinload(Permission.permission_type))
                .order_by(Permission.id)
            ).all()
        )

    def permission_linked_to_group(
        self, group_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        row = self._session.scalars(
            select(GroupPermission).where(
                GroupPermission.group_id == group_id,
                GroupPermission.permission_id == permission_id,
            )
        ).first()
        return row is not None

    def permission_linked_to_role(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        row = self._session.scalars(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        ).first()
        return row is not None

    def upsert_column_mask(
        self,
        *,
        permission_id: uuid.UUID,
        mask_type: str,
        mask_pattern: str | None,
    ) -> ColumnMask:
        existing = self.get_column_mask_for_permission(permission_id)
        if existing is None:
            row = ColumnMask(
                permission_id=permission_id,
                mask_type=mask_type,
                mask_pattern=mask_pattern,
            )
            self._session.add(row)
            self._session.flush()
            return row
        existing.mask_type = mask_type
        existing.mask_pattern = mask_pattern
        self._session.flush()
        return existing


class PermissionTypeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, name: str) -> PermissionType:
        row = PermissionType(name=name)
        self._session.add(row)
        self._session.flush()
        return row

    def get_by_id(self, type_id: uuid.UUID) -> PermissionType | None:
        return self._session.get(PermissionType, type_id)
