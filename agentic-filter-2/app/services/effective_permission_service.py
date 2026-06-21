"""Merge direct group permissions and inherited role permissions (contract §C.2, §F.14)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin_contract import (
    EffectivePermissionOut,
    EffectivePermissionsData,
    InheritedSummaryOut,
    RolePermissionsSummary,
)
from app.services.permission_presenter import PermissionPresenter


@dataclass
class _Entry:
    resource_id: uuid.UUID
    action: str
    effect: str
    fe: EffectivePermissionOut


class EffectivePermissionService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._ir = IdentityRepository(session)
        self._pr = PermissionRepository(session)
        self._rr = ResourceRepository(session)
        self._presenter = PermissionPresenter(self._rr, self._pr)

    def get_effective_permissions(
        self, group_id: uuid.UUID
    ) -> EffectivePermissionsData | None:
        if self._ir.get_group(group_id) is None:
            return None

        entries: list[_Entry] = []

        for perm in self._pr.list_permissions_for_group(group_id):
            fe = self._to_effective(
                perm,
                ownership="group",
                source_role_id=None,
                source_role_name="Direct",
            )
            entries.append(self._wrap(fe, perm))

        roles = self._ir.list_roles_for_group(group_id)
        for role in roles:
            for perm in self._pr.list_permissions_for_role(role.id):
                fe = self._to_effective(
                    perm,
                    ownership="role",
                    source_role_id=role.id,
                    source_role_name=role.display_name,
                )
                entries.append(self._wrap(fe, perm))

        merged = self._dedupe_deny_wins(entries)
        permissions = [e.fe for e in merged]

        allow_count = sum(1 for p in permissions if p.effect == "ALLOW")
        deny_count = sum(1 for p in permissions if p.effect == "DENY")
        modifier_count = sum(1 for p in permissions if p.modifier is not None)

        inherited_perms = [p for p in permissions if p.ownership == "role"]
        resource_types = {p.resource_type for p in permissions}

        return EffectivePermissionsData(
            permissions=permissions,
            summary=RolePermissionsSummary(
                total=len(permissions),
                allowCount=allow_count,
                denyCount=deny_count,
                modifierCount=modifier_count,
            ),
            inheritedSummary=InheritedSummaryOut(
                permissionCount=len(inherited_perms),
                resourceTypeCount=len(resource_types),
                roleCount=len(roles),
            ),
        )

    def _to_effective(
        self,
        perm: Permission,
        *,
        ownership: str,
        source_role_id: uuid.UUID | None,
        source_role_name: str,
    ) -> EffectivePermissionOut:
        base = self._presenter.to_fe_permission(perm)
        return EffectivePermissionOut(
            id=base.id,
            resourceType=base.resource_type,
            path=base.path,
            effect=base.effect,
            action=base.action,
            modifier=base.modifier,
            isHighlighted=base.is_highlighted,
            ownership=ownership,  # type: ignore[arg-type]
            sourceRoleId=str(source_role_id) if source_role_id else None,
            sourceRoleName=source_role_name,
        )

    @staticmethod
    def _wrap(fe: EffectivePermissionOut, perm: Permission) -> _Entry:
        return _Entry(
            resource_id=perm.resource_id,
            action=fe.action,
            effect=fe.effect,
            fe=fe,
        )

    @staticmethod
    def _dedupe_deny_wins(entries: list[_Entry]) -> list[_Entry]:
        by_key: dict[tuple[uuid.UUID, str], _Entry] = {}
        for entry in entries:
            key = (entry.resource_id, entry.action)
            existing = by_key.get(key)
            if existing is None:
                by_key[key] = entry
                continue
            if entry.effect == "DENY":
                by_key[key] = entry
            elif existing.effect != "DENY":
                by_key[key] = entry
        return list(by_key.values())
