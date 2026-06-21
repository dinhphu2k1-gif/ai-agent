"""Admin User Management use cases (contract §D, milestone M2)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache.invalidation import invalidate_cache_for_users
from app.cache.redis_client import UserContextCache
from app.models.identity import Group, Role, User, UserGroup, UserRole
from app.repositories.identity_repo import IdentityRepository
from app.schemas.admin_contract import (
    BulkAssignGroupsBody,
    BulkAssignRolesBody,
    BulkDeactivateBody,
    BulkUpdatedData,
    GroupOptionsOut,
    NamedRef,
    RoleOptionsOut,
    UserCreateBody,
    UserDetail,
    UserListItem,
)
from app.services.audit_service import record_policy_change


def _display_name(user: User) -> str:
    if user.full_name and user.full_name.strip():
        return user.full_name.strip()
    return user.username


def _initials(user: User) -> str:
    name = _display_name(user)
    parts = [p for p in name.replace(".", " ").split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    if parts:
        token = parts[0]
        return (token[:2]).upper()
    return (user.email[:2] if user.email else "??").upper()


def _status_label(is_active: bool) -> str:
    return "Active" if is_active else "Inactive"


def _format_last_active(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    now = datetime.now(UTC)
    seconds = int((now - dt).total_seconds())
    if seconds < 0:
        seconds = 0
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        mins = max(1, seconds // 60)
        return f"{mins} min ago" if mins == 1 else f"{mins} mins ago"
    if seconds < 86400:
        hrs = max(1, seconds // 3600)
        return f"{hrs} hr ago" if hrs == 1 else f"{hrs} hrs ago"
    days = max(1, seconds // 86400)
    return f"{days} day ago" if days == 1 else f"{days} days ago"


def _parse_user_ids(raw: list[str]) -> list[uuid.UUID]:
    return [uuid.UUID(value) for value in raw]


def _parse_optional_ids(raw: list[str]) -> list[uuid.UUID]:
    return [uuid.UUID(value) for value in raw if value.strip()]


class AdminUserService:
    def __init__(
        self,
        session: Session,
        *,
        changed_by: str = "admin-api",
        cache: UserContextCache | None = None,
    ) -> None:
        self._session = session
        self._ir = IdentityRepository(session)
        self._changed_by = changed_by
        self._cache = cache

    def list_users(
        self,
        *,
        page: int,
        page_size: int,
        sort: str | None,
        order_by: str | None,
        search: str | None,
        status: str | None,
    ) -> tuple[list[UserListItem], int]:
        rows, total = self._ir.list_users(
            page=page,
            page_size=page_size,
            sort=sort,
            order_by=order_by,
            search=search,
            status=status,
        )
        items = [self._to_list_item(user) for user in rows]
        return items, total

    def get_user(self, user_id: uuid.UUID) -> UserDetail | None:
        user = self._ir.get_user_by_id(user_id)
        if user is None:
            return None
        return self._to_detail(user)

    def create_user(self, body: UserCreateBody) -> UserDetail:
        user = self._ir.create_user(
            body.username.strip(),
            body.email.strip(),
            is_active=body.is_active,
            full_name=body.full_name.strip(),
        )
        for group_label in body.groups:
            group = self._resolve_group(group_label)
            if group is not None:
                self._ir.add_user_to_group(user.id, group.id)
                record_policy_change(
                    self._session,
                    changed_by=self._changed_by,
                    change_type="USER_GROUP_ADD",
                    permission_id=None,
                    detail={"user_id": str(user.id), "group_id": str(group.id)},
                )
        for role_label in body.roles:
            role = self._resolve_role(role_label)
            if role is not None:
                self._ir.add_user_role(user.id, role.id)
                record_policy_change(
                    self._session,
                    changed_by=self._changed_by,
                    change_type="USER_ROLE_ADD",
                    permission_id=None,
                    detail={"user_id": str(user.id), "role_id": str(role.id)},
                )
        invalidate_cache_for_users([user.id], self._cache)
        loaded = self._ir.get_user_by_id(user.id)
        assert loaded is not None
        return self._to_detail(loaded)

    def group_options(self) -> GroupOptionsOut:
        return GroupOptionsOut(groups=self._ir.list_all_group_names())

    def role_options(self) -> RoleOptionsOut:
        return RoleOptionsOut(roles=self._ir.list_all_role_labels())

    def bulk_assign_groups(self, body: BulkAssignGroupsBody) -> BulkUpdatedData:
        user_ids = _parse_user_ids(body.user_ids)
        group_ids = _resolve_group_ids(self._ir, body.group_ids, body.group_names)
        updated = 0
        for user_id in user_ids:
            if self._ir.get_user(user_id) is None:
                continue
            user_touched = False
            for group_id in group_ids:
                exists = self._session.scalars(
                    select(UserGroup).where(
                        UserGroup.user_id == user_id,
                        UserGroup.group_id == group_id,
                    )
                ).first()
                if exists is not None:
                    continue
                self._ir.add_user_to_group(user_id, group_id)
                user_touched = True
                record_policy_change(
                    self._session,
                    changed_by=self._changed_by,
                    change_type="USER_GROUP_ADD",
                    permission_id=None,
                    detail={
                        "user_id": str(user_id),
                        "group_id": str(group_id),
                    },
                )
            if user_touched:
                updated += 1
        invalidate_cache_for_users(user_ids, self._cache)
        return BulkUpdatedData(updatedCount=updated)

    def bulk_assign_roles(self, body: BulkAssignRolesBody) -> BulkUpdatedData:
        user_ids = _parse_user_ids(body.user_ids)
        role_ids = _resolve_role_ids(self._ir, body.role_ids, body.role_names)
        updated = 0
        for user_id in user_ids:
            if self._ir.get_user(user_id) is None:
                continue
            for role_id in role_ids:
                exists = self._session.scalars(
                    select(UserRole).where(
                        UserRole.user_id == user_id,
                        UserRole.role_id == role_id,
                    )
                ).first()
                if exists is not None:
                    continue
                self._ir.add_user_role(user_id, role_id)
                updated += 1
                record_policy_change(
                    self._session,
                    changed_by=self._changed_by,
                    change_type="USER_ROLE_ADD",
                    permission_id=None,
                    detail={
                        "user_id": str(user_id),
                        "role_id": str(role_id),
                    },
                )
        invalidate_cache_for_users(user_ids, self._cache)
        return BulkUpdatedData(updatedCount=updated)

    def bulk_deactivate(self, body: BulkDeactivateBody) -> BulkUpdatedData:
        user_ids = _parse_user_ids(body.user_ids)
        count = self._ir.deactivate_users(user_ids)
        for user_id in user_ids:
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="USER_DEACTIVATE",
                permission_id=None,
                detail={"user_id": str(user_id)},
            )
        invalidate_cache_for_users(user_ids, self._cache)
        return BulkUpdatedData(updatedCount=count)

    def assign_users_to_role(
        self, role_id: uuid.UUID, user_ids: list[uuid.UUID]
    ) -> BulkUpdatedData:
        if self._ir.get_role(role_id) is None:
            raise ValueError("role_not_found")
        updated = 0
        for user_id in user_ids:
            if self._ir.get_user(user_id) is None:
                continue
            exists = self._session.scalars(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                )
            ).first()
            if exists is not None:
                continue
            self._ir.add_user_role(user_id, role_id)
            updated += 1
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="USER_ROLE_ADD",
                permission_id=None,
                detail={"user_id": str(user_id), "role_id": str(role_id)},
            )
        invalidate_cache_for_users(user_ids, self._cache)
        return BulkUpdatedData(updatedCount=updated)

    def remove_user_from_role(self, role_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        if self._ir.get_role(role_id) is None:
            raise ValueError("role_not_found")
        if self._ir.get_user(user_id) is None:
            raise ValueError("user_not_found")
        removed = self._ir.remove_user_role(user_id, role_id)
        if removed:
            record_policy_change(
                self._session,
                changed_by=self._changed_by,
                change_type="USER_ROLE_REMOVE",
                permission_id=None,
                detail={"user_id": str(user_id), "role_id": str(role_id)},
            )
            invalidate_cache_for_users([user_id], self._cache)
        return removed

    def _to_list_item(self, user: User) -> UserListItem:
        return UserListItem(
            id=str(user.id),
            name=_display_name(user),
            email=user.email,
            status=_status_label(user.is_active),
            groups=[g.name for g in user.groups],
            roles=[r.display_name for r in user.direct_roles],
            initials=_initials(user),
            lastActive=_format_last_active(user.last_active_at),
            lastActiveAt=user.last_active_at,
        )

    def _to_detail(self, user: User) -> UserDetail:
        return UserDetail(
            id=str(user.id),
            name=_display_name(user),
            email=user.email,
            username=user.username,
            status=_status_label(user.is_active),
            groups=[NamedRef(id=str(g.id), name=g.name) for g in user.groups],
            roles=[
                NamedRef(id=str(r.id), name=r.display_name) for r in user.direct_roles
            ],
            initials=_initials(user),
            lastActive=_format_last_active(user.last_active_at),
            lastActiveAt=user.last_active_at,
        )

    def _resolve_group(self, label: str) -> Group | None:
        return self._ir.find_group_by_name(label)

    def _resolve_role(self, label: str) -> Role | None:
        return self._ir.find_role_by_label(label)


def _resolve_group_ids(
    ir: IdentityRepository,
    group_ids: list[str],
    group_names: list[str],
) -> list[uuid.UUID]:
    resolved: list[uuid.UUID] = []
    for gid in _parse_optional_ids(group_ids):
        if ir.get_group(gid) is not None:
            resolved.append(gid)
    for name in group_names:
        group = ir.find_group_by_name(name)
        if group is not None and group.id not in resolved:
            resolved.append(group.id)
    return resolved


def _resolve_role_ids(
    ir: IdentityRepository,
    role_ids: list[str],
    role_names: list[str],
) -> list[uuid.UUID]:
    resolved: list[uuid.UUID] = []
    for rid in _parse_optional_ids(role_ids):
        if ir.get_role(rid) is not None:
            resolved.append(rid)
    for name in role_names:
        role = ir.find_role_by_label(name)
        if role is not None and role.id not in resolved:
            resolved.append(role.id)
    return resolved
