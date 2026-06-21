"""Admin Group Management use cases (contract §F, milestone M4)."""

from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cache.invalidation import invalidate_cache_for_users
from app.cache.redis_client import UserContextCache
from app.models.identity import Group, User
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin_contract import (
    AssignMembersBody,
    AssignRolesToGroupBody,
    BulkUpdatedData,
    EffectivePermissionsData,
    FePermissionOut,
    GroupCreateBody,
    GroupListItem,
    GroupMemberOut,
    GroupRoleOut,
    PermissionGrantBody,
    PermissionsCreatedData,
    RoleCatalogItem,
    UserCatalogItem,
)
from app.services.permission_grant_service import PermissionGrantService
from app.services.admin_user_service import _display_name, _initials, _status_label
from app.services.audit_service import record_policy_change
from app.services.effective_permission_service import EffectivePermissionService
from app.services.permission_presenter import PermissionPresenter


class AdminGroupService:
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
        self._effective = EffectivePermissionService(session)
        self._grant = PermissionGrantService(
            session, self._rr, self._pr, changed_by=changed_by
        )
        self._changed_by = changed_by
        self._cache = cache

    def list_groups(
        self,
        *,
        page: int,
        page_size: int,
        sort: str | None,
        order_by: str | None,
        search: str | None,
    ) -> tuple[list[GroupListItem], int]:
        rows, total = self._ir.list_groups(
            page=page,
            page_size=page_size,
            sort=sort,
            order_by=order_by,
            search=search,
        )
        return [self._to_list_item(g) for g in rows], total

    def create_group(self, body: GroupCreateBody) -> GroupListItem:
        try:
            group = self._ir.create_group(body.name.strip(), description=body.description)
        except IntegrityError as exc:
            raise ValueError("group_name_conflict") from exc
        return self._to_list_item(group)

    def delete_group(self, group_id: uuid.UUID) -> bool:
        if self._ir.get_group(group_id) is None:
            return False
        user_ids = [u.id for u in self._ir.list_users_for_group(group_id)]
        for perm in self._pr.list_permissions_for_group(group_id):
            self._ir.remove_group_permission(group_id, perm.id)
            self._pr.delete_permission(perm.id)
        deleted = self._ir.delete_group(group_id)
        if deleted:
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="GROUP_DELETE",
                detail={"group_id": str(group_id)},
            )
            if user_ids:
                invalidate_cache_for_users(user_ids, self._cache)
        return deleted

    def list_members(self, group_id: uuid.UUID) -> list[GroupMemberOut] | None:
        if self._ir.get_group(group_id) is None:
            return None
        return [self._to_member(u) for u in self._ir.list_users_for_group(group_id)]

    def add_members(
        self, group_id: uuid.UUID, body: AssignMembersBody
    ) -> BulkUpdatedData | None:
        if self._ir.get_group(group_id) is None:
            return None
        updated = 0
        touched: list[uuid.UUID] = []
        for raw in body.member_ids:
            uid = uuid.UUID(raw)
            if self._ir.get_user(uid) is None:
                continue
            self._ir.add_user_to_group(uid, group_id)
            updated += 1
            touched.append(uid)
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="USER_GROUP_ADD",
                detail={"user_id": str(uid), "group_id": str(group_id)},
            )
        if touched:
            invalidate_cache_for_users(touched, self._cache)
        return BulkUpdatedData(updatedCount=updated)

    def remove_member(self, group_id: uuid.UUID, member_id: uuid.UUID) -> bool:
        if self._ir.get_group(group_id) is None:
            raise ValueError("group_not_found")
        if self._ir.get_user(member_id) is None:
            raise ValueError("user_not_found")
        removed = self._ir.remove_user_from_group(member_id, group_id)
        if removed:
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="USER_GROUP_REMOVE",
                detail={"user_id": str(member_id), "group_id": str(group_id)},
            )
            invalidate_cache_for_users([member_id], self._cache)
        return removed

    def list_group_roles(self, group_id: uuid.UUID) -> list[GroupRoleOut] | None:
        if self._ir.get_group(group_id) is None:
            return None
        items: list[GroupRoleOut] = []
        for role in self._ir.list_roles_for_group(group_id):
            items.append(
                GroupRoleOut(
                    id=str(role.id),
                    name=role.display_name,
                    description=None,
                    permissionCount=self._ir.count_permissions_for_role(role.id),
                )
            )
        return items

    def assign_roles(
        self, group_id: uuid.UUID, body: AssignRolesToGroupBody
    ) -> BulkUpdatedData | None:
        if self._ir.get_group(group_id) is None:
            return None
        updated = 0
        for raw in body.role_ids:
            rid = uuid.UUID(raw)
            if self._ir.get_role(rid) is None:
                continue
            self._ir.add_group_role(group_id, rid)
            updated += 1
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="GROUP_ROLE_ADD",
                detail={"group_id": str(group_id), "role_id": str(rid)},
            )
        self._invalidate_group_members(group_id)
        return BulkUpdatedData(updatedCount=updated)

    def unassign_role(self, group_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        if self._ir.get_group(group_id) is None:
            raise ValueError("group_not_found")
        if self._ir.get_role(role_id) is None:
            raise ValueError("role_not_found")
        removed = self._ir.remove_group_role(group_id, role_id)
        if removed:
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="GROUP_ROLE_REMOVE",
                detail={"group_id": str(group_id), "role_id": str(role_id)},
            )
            self._invalidate_group_members(group_id)
        return removed

    def list_direct_permissions(self, group_id: uuid.UUID) -> list[FePermissionOut] | None:
        if self._ir.get_group(group_id) is None:
            return None
        perms = self._pr.list_permissions_for_group(group_id)
        return [self._presenter.to_fe_permission(p) for p in perms]

    def grant_permissions(
        self, group_id: uuid.UUID, body: PermissionGrantBody
    ) -> PermissionsCreatedData | None:
        if self._ir.get_group(group_id) is None:
            return None
        perm_ids = self._grant.apply_grant_group(group_id, body, self._ir)
        created: list[FePermissionOut] = []
        for pid in perm_ids:
            perm = self._pr.get_permission(pid)
            assert perm is not None
            created.append(self._presenter.to_fe_permission(perm))
        self._invalidate_group_members(group_id)
        return PermissionsCreatedData(created=created)

    def update_direct_permission(
        self,
        group_id: uuid.UUID,
        permission_id: uuid.UUID,
        body: PermissionGrantBody,
    ) -> FePermissionOut | None:
        guard = self.update_direct_permission_guard(group_id, permission_id)
        if guard == "not_direct":
            raise ValueError("not_direct")
        if guard == "not_found":
            return None
        perm = self._pr.get_permission(permission_id)
        if perm is None:
            return None
        self._grant.apply_update_permission(
            permission_id,
            body,
            owner_detail={"group_id": str(group_id)},
        )
        self._invalidate_group_members(group_id)
        refreshed = self._pr.get_permission(permission_id)
        assert refreshed is not None
        return self._presenter.to_fe_permission(refreshed)

    def delete_direct_permission(
        self, group_id: uuid.UUID, permission_id: uuid.UUID
    ) -> str | bool:
        """Returns False if not found, True if deleted, 'not_direct' if inherited-only."""
        if self._ir.get_group(group_id) is None:
            return False
        if not self._pr.permission_linked_to_group(group_id, permission_id):
            if self._is_inherited_only(group_id, permission_id):
                return "not_direct"
            return False
        self._ir.remove_group_permission(group_id, permission_id)
        record_policy_change(
            self._session,
            changed_by=self._changed_by,
            change_type="PERMISSION_DELETE",
            permission_id=permission_id,
            detail={"group_id": str(group_id)},
        )
        deleted = self._pr.delete_permission(permission_id)
        if deleted:
            self._invalidate_group_members(group_id)
        return deleted

    def update_direct_permission_guard(
        self, group_id: uuid.UUID, permission_id: uuid.UUID
    ) -> str | None:
        """None if OK to edit; 'not_direct' if permission is role-only for this group."""
        if not self._pr.permission_linked_to_group(group_id, permission_id):
            if self._permission_visible_via_roles(group_id, permission_id):
                return "not_direct"
            return "not_found"
        return None

    def get_effective_permissions(
        self, group_id: uuid.UUID
    ) -> EffectivePermissionsData | None:
        return self._effective.get_effective_permissions(group_id)

    def members_catalog(
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

    def roles_catalog(
        self,
        *,
        page: int,
        page_size: int,
        sort: str | None,
        order_by: str | None,
        search: str | None,
    ) -> tuple[list[RoleCatalogItem], int]:
        rows, total = self._ir.list_roles(
            page=page,
            page_size=page_size,
            sort=sort,
            order_by=order_by,
            search=search,
        )
        items = [
            RoleCatalogItem(
                id=str(r.id),
                name=r.display_name,
                description=None,
                permissionCount=self._ir.count_permissions_for_role(r.id),
            )
            for r in rows
        ]
        return items, total

    def _to_list_item(self, group: Group) -> GroupListItem:
        return GroupListItem(
            id=str(group.id),
            name=group.name,
            memberCount=self._ir.count_group_members(group.id),
            roleCount=self._ir.count_roles_for_group(group.id),
            description=group.description,
        )

    def _to_member(self, user: User) -> GroupMemberOut:
        return GroupMemberOut(
            id=str(user.id),
            name=_display_name(user),
            email=user.email,
            initials=_initials(user),
            status=_status_label(user.is_active),
        )

    def _permission_visible_via_roles(
        self, group_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        for role in self._ir.list_roles_for_group(group_id):
            if self._pr.permission_linked_to_role(role.id, permission_id):
                return True
        return False

    def _is_inherited_only(self, group_id: uuid.UUID, permission_id: uuid.UUID) -> bool:
        return self._permission_visible_via_roles(
            group_id, permission_id
        ) and not self._pr.permission_linked_to_group(group_id, permission_id)

    def _invalidate_group_members(self, group_id: uuid.UUID) -> None:
        user_ids = [u.id for u in self._ir.list_users_for_group(group_id)]
        if user_ids:
            invalidate_cache_for_users(user_ids, self._cache)
