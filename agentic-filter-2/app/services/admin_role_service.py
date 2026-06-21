"""Admin Role Management use cases (contract §E, milestone M3)."""

from __future__ import annotations

import time
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cache.invalidation import invalidate_cache_for_users
from app.cache.redis_client import UserContextCache
from app.models.identity import Role
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin_contract import (
    ActorGroupOut,
    ActorUserOut,
    AssignGroupsToRoleBody,
    BulkUpdatedData,
    FePermissionOut,
    GroupCatalogItem,
    PermissionGrantBody,
    PermissionsCreatedData,
    RoleActorsData,
    RoleCreateBody,
    RoleListItem,
    RolePermissionsData,
    RoleRenameBody,
    UserCatalogItem,
)
from app.services.admin_user_service import _display_name
from app.services.audit_service import record_policy_change
from app.services.permission_grant_service import PermissionGrantService
from app.services.permission_presenter import PermissionPresenter


def _role_icon(role: Role) -> str:
    if "sysadmin" in role.name.lower() or "admin" in role.name.lower():
        return "shield_lock"
    return "shield"


class AdminRoleService:
    def __init__(
        self,
        session: Session,
        *,
        changed_by: str = "admin-api",
        cache: UserContextCache | None = None,
    ) -> None:
        self._session = session
        self._ir = IdentityRepository(session)
        self._pr = PermissionRepository(session)
        self._rr = ResourceRepository(session)
        self._presenter = PermissionPresenter(self._rr, self._pr)
        self._grant = PermissionGrantService(
            session, self._rr, self._pr, changed_by=changed_by
        )
        self._changed_by = changed_by
        self._cache = cache

    def _to_list_item(self, role: Role) -> RoleListItem:
        return RoleListItem(
            id=str(role.id),
            name=role.name,
            displayName=role.display_name,
            permissionCount=self._ir.count_permissions_for_role(role.id),
            userCount=self._ir.count_users_for_role(role.id),
            groupCount=self._ir.count_groups_for_role(role.id),
            icon=_role_icon(role),
        )

    def list_roles(
        self,
        *,
        page: int,
        page_size: int,
        sort: str | None,
        order_by: str | None,
        search: str | None,
    ) -> tuple[list[RoleListItem], int]:
        rows, total = self._ir.list_roles(
            page=page,
            page_size=page_size,
            sort=sort,
            order_by=order_by,
            search=search,
        )
        return [self._to_list_item(r) for r in rows], total

    def create_role(self, body: RoleCreateBody) -> RoleListItem:
        try:
            role = self._ir.create_role(body.name.strip(), display_name=body.name.strip())
        except IntegrityError as exc:
            raise ValueError("role_name_conflict") from exc
        return self._to_list_item(role)

    def rename_role(self, role_id: uuid.UUID, body: RoleRenameBody) -> RoleListItem | None:
        try:
            role = self._ir.update_role_name(role_id, body.name.strip())
        except IntegrityError as exc:
            raise ValueError("role_name_conflict") from exc
        if role is None:
            return None
        return self._to_list_item(role)

    def duplicate_role(self, role_id: uuid.UUID) -> RoleListItem | None:
        source = self._ir.get_role(role_id)
        if source is None:
            return None
        suffix = f"_copy_{int(time.time())}"
        new_name = f"{source.name}{suffix}"[:255]
        new_display = f"{source.display_name} (copy)"[:255]
        try:
            clone = self._ir.create_role(new_name, display_name=new_display)
            for perm in self._pr.list_permissions_for_role(role_id):
                new_perm = self._pr.create_permission(
                    resource_id=perm.resource_id,
                    permission_type_id=perm.permission_type_id,
                    effect=perm.effect,
                )
                rf = self._pr.get_row_filter_for_permission(perm.id)
                if rf is not None:
                    self._pr.create_row_filter(
                        permission_id=new_perm.id,
                        condition_expr=rf.condition_expr,
                    )
                mask = self._pr.get_column_mask_for_permission(perm.id)
                if mask is not None:
                    self._pr.upsert_column_mask(
                        permission_id=new_perm.id,
                        mask_type=mask.mask_type,
                        mask_pattern=mask.mask_pattern,
                    )
                self._ir.add_role_permission(clone.id, new_perm.id)
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="ROLE_DUPLICATE",
                detail={"source_role_id": str(role_id), "new_role_id": str(clone.id)},
            )
        except IntegrityError as exc:
            raise ValueError("role_name_conflict") from exc
        return self._to_list_item(clone)

    def delete_role(self, role_id: uuid.UUID) -> bool:
        role = self._ir.get_role(role_id)
        if role is None:
            return False
        if self._ir.role_has_references(role_id):
            raise ValueError("role_in_use")
        for perm in self._pr.list_permissions_for_role(role_id):
            self._ir.remove_role_permission(role_id, perm.id)
            self._pr.delete_permission(perm.id)
        deleted = self._ir.delete_role(role_id)
        if deleted:
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="ROLE_DELETE",
                detail={"role_id": str(role_id)},
            )
        return deleted

    def list_permissions(self, role_id: uuid.UUID) -> RolePermissionsData | None:
        if self._ir.get_role(role_id) is None:
            return None
        return self._presenter.list_for_role(role_id)

    def grant_permissions(
        self, role_id: uuid.UUID, body: PermissionGrantBody
    ) -> PermissionsCreatedData | None:
        if self._ir.get_role(role_id) is None:
            return None
        perm_ids = self._grant.apply_grant_role(role_id, body, self._ir)
        created: list[FePermissionOut] = []
        for pid in perm_ids:
            perm = self._pr.get_permission(pid)
            assert perm is not None
            created.append(self._presenter.to_fe_permission(perm))
        self._invalidate_role_members(role_id)
        return PermissionsCreatedData(created=created)

    def update_permission(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
        body: PermissionGrantBody,
    ) -> FePermissionOut | None:
        if self._ir.get_role(role_id) is None:
            return None
        if not self._pr.permission_linked_to_role(role_id, permission_id):
            return None
        perm = self._pr.get_permission(permission_id)
        if perm is None:
            return None
        self._grant.apply_update_permission(
            permission_id,
            body,
            owner_detail={"role_id": str(role_id)},
        )
        self._invalidate_role_members(role_id)
        refreshed = self._pr.get_permission(permission_id)
        assert refreshed is not None
        return self._presenter.to_fe_permission(refreshed)

    def delete_permission(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        if self._ir.get_role(role_id) is None:
            return False
        if not self._pr.permission_linked_to_role(role_id, permission_id):
            return False
        self._ir.remove_role_permission(role_id, permission_id)
        record_policy_change(
            self._session,
            changed_by=self._changed_by,
            change_type="PERMISSION_DELETE",
            permission_id=permission_id,
            detail={"role_id": str(role_id)},
        )
        deleted = self._pr.delete_permission(permission_id)
        if deleted:
            self._invalidate_role_members(role_id)
        return deleted

    def get_actors(self, role_id: uuid.UUID) -> RoleActorsData | None:
        if self._ir.get_role(role_id) is None:
            return None
        users = self._ir.list_users_for_role(role_id)
        groups = self._ir.list_groups_for_role(role_id)
        user_items = [
            ActorUserOut(
                id=str(u.id),
                name=_display_name(u),
                email=u.email,
                isOnline=bool(u.is_active),
            )
            for u in users
        ]
        group_items = [
            ActorGroupOut(
                id=str(g.id),
                name=g.name,
                memberCount=self._ir.count_group_members(g.id),
            )
            for g in groups
        ]
        direct_ids = {u.id for u in users}
        group_ids = [g.id for g in groups]
        via_group = self._ir.list_user_ids_for_groups(group_ids)
        total = len(direct_ids | set(via_group))
        return RoleActorsData(
            users=user_items,
            groups=group_items,
            totalAffectedUsers=total,
        )

    def assign_groups_to_role(
        self, role_id: uuid.UUID, body: AssignGroupsToRoleBody
    ) -> BulkUpdatedData | None:
        if self._ir.get_role(role_id) is None:
            return None
        updated = 0
        for raw in body.group_ids:
            gid = uuid.UUID(raw)
            if self._ir.get_group(gid) is None:
                continue
            self._ir.add_group_role(gid, role_id)
            updated += 1
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="GROUP_ROLE_ADD",
                detail={"group_id": str(gid), "role_id": str(role_id)},
            )
        self._invalidate_role_members(role_id)
        return BulkUpdatedData(updatedCount=updated)

    def remove_group_from_role(
        self, role_id: uuid.UUID, group_id: uuid.UUID
    ) -> bool:
        if self._ir.get_role(role_id) is None:
            raise ValueError("role_not_found")
        if self._ir.get_group(group_id) is None:
            raise ValueError("group_not_found")
        removed = self._ir.remove_group_role(group_id, role_id)
        if removed:
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="GROUP_ROLE_REMOVE",
                detail={"group_id": str(group_id), "role_id": str(role_id)},
            )
            self._invalidate_role_members(role_id)
        return removed

    def users_catalog(
        self,
        *,
        page: int,
        page_size: int,
        sort: str | None,
        order_by: str | None,
        search: str | None,
    ) -> tuple[list[UserCatalogItem], int]:
        rows, total = self._ir.list_users(
            page=page,
            page_size=page_size,
            sort=sort,
            order_by=order_by,
            search=search,
            status=None,
        )
        items = [
            UserCatalogItem(
                id=str(u.id),
                name=_display_name(u),
                email=u.email,
                isOnline=bool(u.is_active),
            )
            for u in rows
        ]
        return items, total

    def groups_catalog(
        self,
        *,
        page: int,
        page_size: int,
        sort: str | None,
        order_by: str | None,
        search: str | None,
    ) -> tuple[list[GroupCatalogItem], int]:
        rows, total = self._ir.list_groups(
            page=page,
            page_size=page_size,
            sort=sort,
            order_by=order_by,
            search=search,
        )
        items = [
            GroupCatalogItem(
                id=str(g.id),
                name=g.name,
                memberCount=self._ir.count_group_members(g.id),
                description=g.description,
            )
            for g in rows
        ]
        return items, total

    def _invalidate_role_members(self, role_id: uuid.UUID) -> None:
        user_ids = [u.id for u in self._ir.list_users_for_role(role_id)]
        groups = self._ir.list_groups_for_role(role_id)
        user_ids.extend(self._ir.list_user_ids_for_groups([g.id for g in groups]))
        if user_ids:
            invalidate_cache_for_users(list(set(user_ids)), self._cache)
