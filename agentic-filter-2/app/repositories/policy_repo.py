from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import GroupPermission, RolePermission, UserPermission
from app.models.permission import ColumnMask, Permission, PermissionType, RowFilter


@dataclass(frozen=True)
class LoadedPermission:
    permission_id: uuid.UUID
    resource_id: uuid.UUID
    permission_type_name: str
    effect: str
    row_filter_exprs: tuple[str, ...]
    mask_type: str | None
    mask_pattern: str | None


class PolicyRepository:
    """Loads permission rows + row filters + column masks for PDP (Epic 5)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def load_permission_bundle(
        self,
        *,
        user_id: uuid.UUID,
        group_ids: Sequence[uuid.UUID],
        direct_role_ids: Sequence[uuid.UUID],
        inherited_role_ids: Sequence[uuid.UUID],
    ) -> list[LoadedPermission]:
        perm_ids: set[uuid.UUID] = set()
        for pid in self._session.scalars(
            select(UserPermission.permission_id).where(UserPermission.user_id == user_id)
        ):
            perm_ids.add(pid)
        if group_ids:
            for pid in self._session.scalars(
                select(GroupPermission.permission_id).where(
                    GroupPermission.group_id.in_(list(group_ids))
                )
            ):
                perm_ids.add(pid)
        role_ids = set(direct_role_ids) | set(inherited_role_ids)
        if role_ids:
            for pid in self._session.scalars(
                select(RolePermission.permission_id).where(
                    RolePermission.role_id.in_(list(role_ids))
                )
            ):
                perm_ids.add(pid)
        if not perm_ids:
            return []

        stmt = (
            select(Permission, PermissionType.name)
            .join(PermissionType, Permission.permission_type_id == PermissionType.id)
            .where(Permission.id.in_(perm_ids))
        )
        rows = list(self._session.execute(stmt).all())

        filters_by_perm: dict[uuid.UUID, list[str]] = defaultdict(list)
        for rf in self._session.scalars(
            select(RowFilter).where(RowFilter.permission_id.in_(perm_ids))
        ):
            filters_by_perm[rf.permission_id].append(rf.condition_expr)

        masks_by_perm: dict[uuid.UUID, ColumnMask] = {}
        for cm in self._session.scalars(
            select(ColumnMask).where(ColumnMask.permission_id.in_(perm_ids))
        ):
            masks_by_perm[cm.permission_id] = cm

        bundle: list[LoadedPermission] = []
        for perm, type_name in rows:
            cm = masks_by_perm.get(perm.id)
            bundle.append(
                LoadedPermission(
                    permission_id=perm.id,
                    resource_id=perm.resource_id,
                    permission_type_name=type_name,
                    effect=perm.effect,
                    row_filter_exprs=tuple(filters_by_perm.get(perm.id, ())),
                    mask_type=cm.mask_type if cm else None,
                    mask_pattern=cm.mask_pattern if cm else None,
                )
            )
        return bundle
