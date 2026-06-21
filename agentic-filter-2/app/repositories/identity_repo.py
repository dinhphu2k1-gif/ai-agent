from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.identity import (
    Group,
    GroupPermission,
    GroupRole,
    Role,
    RolePermission,
    User,
    UserGroup,
    UserPermission,
    UserRole,
)

SortOrder = Literal["asc", "desc"]

_USER_SORT_FIELDS = {
    "username": User.username,
    "email": User.email,
    "name": User.full_name,
    "full_name": User.full_name,
    "last_active_at": User.last_active_at,
    "is_active": User.is_active,
}
_ROLE_SORT_FIELDS = {
    "name": Role.name,
    "display_name": Role.display_name,
}
_GROUP_SORT_FIELDS = {
    "name": Group.name,
    "description": Group.description,
}


class IdentityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_user(
        self,
        username: str,
        email: str,
        *,
        is_active: bool = True,
        full_name: str | None = None,
    ) -> User:
        row = User(
            username=username,
            email=email,
            is_active=is_active,
            full_name=full_name,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get_user(self, user_id: uuid.UUID) -> User | None:
        return self._session.get(User, user_id)

    def get_user_by_username(self, username: str) -> User | None:
        label = username.strip()
        if not label:
            return None
        return self._session.scalars(
            select(User).where(User.username == label)
        ).first()

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.groups),
                selectinload(User.direct_roles),
            )
        )
        return self._session.scalars(stmt).first()

    def update_user_email(self, user_id: uuid.UUID, email: str) -> User | None:
        row = self.get_user(user_id)
        if row is None:
            return None
        row.email = email
        self._session.flush()
        return row

    def delete_user(self, user_id: uuid.UUID) -> bool:
        row = self.get_user(user_id)
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def create_group(self, name: str, *, description: str | None = None) -> Group:
        row = Group(name=name, description=description)
        self._session.add(row)
        self._session.flush()
        return row

    def get_group(self, group_id: uuid.UUID) -> Group | None:
        return self._session.get(Group, group_id)

    def get_role(self, role_id: uuid.UUID) -> Role | None:
        return self._session.get(Role, role_id)

    def create_role(self, name: str, *, display_name: str | None = None) -> Role:
        row = Role(name=name, display_name=display_name or name)
        self._session.add(row)
        self._session.flush()
        return row

    def add_user_to_group(
        self, user_id: uuid.UUID, group_id: uuid.UUID
    ) -> UserGroup | None:
        existing = self._session.scalars(
            select(UserGroup).where(
                UserGroup.user_id == user_id,
                UserGroup.group_id == group_id,
            )
        ).first()
        if existing is not None:
            return existing
        row = UserGroup(user_id=user_id, group_id=group_id)
        self._session.add(row)
        self._session.flush()
        return row

    def add_user_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> UserRole | None:
        existing = self._session.scalars(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        ).first()
        if existing is not None:
            return existing
        row = UserRole(user_id=user_id, role_id=role_id)
        self._session.add(row)
        self._session.flush()
        return row

    def remove_user_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        row = self._session.scalars(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        ).first()
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def list_users_for_role(self, role_id: uuid.UUID) -> list[User]:
        stmt = select(User).join(UserRole).where(UserRole.role_id == role_id)
        return list(self._session.scalars(stmt).all())

    def add_group_role(self, group_id: uuid.UUID, role_id: uuid.UUID) -> GroupRole | None:
        existing = self._session.scalars(
            select(GroupRole).where(
                GroupRole.group_id == group_id,
                GroupRole.role_id == role_id,
            )
        ).first()
        if existing is not None:
            return existing
        row = GroupRole(group_id=group_id, role_id=role_id)
        self._session.add(row)
        self._session.flush()
        return row

    def add_user_permission(
        self,
        user_id: uuid.UUID,
        permission_id: uuid.UUID,
        granted_by: str | None = None,
    ) -> UserPermission:
        row = UserPermission(
            user_id=user_id, permission_id=permission_id, granted_by=granted_by
        )
        self._session.add(row)
        self._session.flush()
        return row

    def add_group_permission(
        self, group_id: uuid.UUID, permission_id: uuid.UUID
    ) -> GroupPermission | None:
        existing = self._session.scalars(
            select(GroupPermission).where(
                GroupPermission.group_id == group_id,
                GroupPermission.permission_id == permission_id,
            )
        ).first()
        if existing is not None:
            return existing
        row = GroupPermission(group_id=group_id, permission_id=permission_id)
        self._session.add(row)
        self._session.flush()
        return row

    def remove_group_permission(
        self, group_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        row = self._session.scalars(
            select(GroupPermission).where(
                GroupPermission.group_id == group_id,
                GroupPermission.permission_id == permission_id,
            )
        ).first()
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def remove_user_from_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        row = self._session.scalars(
            select(UserGroup).where(
                UserGroup.user_id == user_id,
                UserGroup.group_id == group_id,
            )
        ).first()
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def list_users_for_group(self, group_id: uuid.UUID) -> list[User]:
        return list(
            self._session.scalars(
                select(User).join(UserGroup).where(UserGroup.group_id == group_id)
            ).all()
        )

    def list_roles_for_group(self, group_id: uuid.UUID) -> list[Role]:
        return list(
            self._session.scalars(
                select(Role).join(GroupRole).where(GroupRole.group_id == group_id)
            ).all()
        )

    def count_roles_for_group(self, group_id: uuid.UUID) -> int:
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(GroupRole)
                .where(GroupRole.group_id == group_id)
            )
            or 0
        )

    def delete_group(self, group_id: uuid.UUID) -> bool:
        row = self.get_group(group_id)
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def add_role_permission(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> RolePermission | None:
        existing = self._session.scalars(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        ).first()
        if existing is not None:
            return existing
        row = RolePermission(role_id=role_id, permission_id=permission_id)
        self._session.add(row)
        self._session.flush()
        return row

    def remove_role_permission(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        row = self._session.scalars(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        ).first()
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def remove_group_role(self, group_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        row = self._session.scalars(
            select(GroupRole).where(
                GroupRole.group_id == group_id,
                GroupRole.role_id == role_id,
            )
        ).first()
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def list_groups_for_role(self, role_id: uuid.UUID) -> list[Group]:
        return list(
            self._session.scalars(
                select(Group).join(GroupRole).where(GroupRole.role_id == role_id)
            ).all()
        )

    def count_users_for_role(self, role_id: uuid.UUID) -> int:
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(UserRole)
                .where(UserRole.role_id == role_id)
            )
            or 0
        )

    def count_groups_for_role(self, role_id: uuid.UUID) -> int:
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(GroupRole)
                .where(GroupRole.role_id == role_id)
            )
            or 0
        )

    def count_permissions_for_role(self, role_id: uuid.UUID) -> int:
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(RolePermission)
                .where(RolePermission.role_id == role_id)
            )
            or 0
        )

    def role_has_references(self, role_id: uuid.UUID) -> bool:
        if self.count_users_for_role(role_id) > 0:
            return True
        if self.count_groups_for_role(role_id) > 0:
            return True
        return False

    def update_role_name(self, role_id: uuid.UUID, name: str) -> Role | None:
        row = self.get_role(role_id)
        if row is None:
            return None
        row.name = name
        self._session.flush()
        return row

    def delete_role(self, role_id: uuid.UUID) -> bool:
        row = self.get_role(role_id)
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def count_group_members(self, group_id: uuid.UUID) -> int:
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(UserGroup)
                .where(UserGroup.group_id == group_id)
            )
            or 0
        )

    def list_user_ids_for_groups(self, group_ids: list[uuid.UUID]) -> list[uuid.UUID]:
        if not group_ids:
            return []
        rows = self._session.scalars(
            select(UserGroup.user_id).where(UserGroup.group_id.in_(group_ids))
        ).all()
        return list(rows)

    def list_users(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        sort: str | None = None,
        order_by: str | None = None,
        search: str | None = None,
        status: str | None = None,
    ) -> tuple[list[User], int]:
        stmt = select(User).options(
            selectinload(User.groups),
            selectinload(User.direct_roles),
        )
        count_stmt = select(func.count()).select_from(User)

        if status and status.strip().lower() not in ("all", ""):
            active = status.strip().lower() == "active"
            stmt = stmt.where(User.is_active == active)
            count_stmt = count_stmt.where(User.is_active == active)

        if search and search.strip():
            term = f"%{search.strip()}%"
            predicate = or_(
                User.username.ilike(term),
                User.email.ilike(term),
                User.full_name.ilike(term),
            )
            stmt = stmt.where(predicate)
            count_stmt = count_stmt.where(predicate)

        order_column, direction = self._resolve_sort(
            _USER_SORT_FIELDS, sort=sort, order_by=order_by
        )
        if direction == "desc":
            stmt = stmt.order_by(order_column.desc())
        else:
            stmt = stmt.order_by(order_column.asc())

        offset = (page - 1) * page_size
        total = int(self._session.scalar(count_stmt) or 0)
        rows = list(self._session.scalars(stmt.offset(offset).limit(page_size)).all())
        return rows, total

    def find_group_by_name(self, name: str) -> Group | None:
        label = name.strip()
        if not label:
            return None
        return self._session.scalars(
            select(Group).where(Group.name == label)
        ).first()

    def find_role_by_label(self, label: str) -> Role | None:
        text = label.strip()
        if not text:
            return None
        return self._session.scalars(
            select(Role).where(
                or_(Role.display_name == text, Role.name == text)
            )
        ).first()

    def list_all_group_names(self) -> list[str]:
        return list(self._session.scalars(select(Group.name).order_by(Group.name)).all())

    def list_all_role_labels(self) -> list[str]:
        rows = self._session.scalars(
            select(Role).order_by(Role.display_name)
        ).all()
        return [r.display_name for r in rows]

    def deactivate_users(self, user_ids: list[uuid.UUID]) -> int:
        updated = 0
        for user_id in user_ids:
            row = self.get_user(user_id)
            if row is None or not row.is_active:
                continue
            row.is_active = False
            updated += 1
        if updated:
            self._session.flush()
        return updated

    def list_roles(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        sort: str | None = None,
        order_by: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Role], int]:
        return self._list_entities(
            Role,
            _ROLE_SORT_FIELDS,
            page=page,
            page_size=page_size,
            sort=sort,
            order_by=order_by,
            search=search,
            search_columns=(Role.name, Role.display_name),
        )

    def list_groups(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        sort: str | None = None,
        order_by: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Group], int]:
        return self._list_entities(
            Group,
            _GROUP_SORT_FIELDS,
            page=page,
            page_size=page_size,
            sort=sort,
            order_by=order_by,
            search=search,
            search_columns=(Group.name, Group.description),
        )

    def list_roles_for_user(self, user_id: uuid.UUID) -> list[Role]:
        direct = self._session.scalars(
            select(Role).join(UserRole).where(UserRole.user_id == user_id)
        ).all()
        return list(direct)

    def list_groups_for_user(self, user_id: uuid.UUID) -> list[Group]:
        return list(
            self._session.scalars(
                select(Group).join(UserGroup).where(UserGroup.user_id == user_id)
            ).all()
        )

    def list_roles_inherited_via_groups(self, user_id: uuid.UUID) -> list[Role]:
        stmt = (
            select(Role)
            .join(GroupRole, GroupRole.role_id == Role.id)
            .join(UserGroup, UserGroup.group_id == GroupRole.group_id)
            .where(UserGroup.user_id == user_id)
        )
        return list(self._session.scalars(stmt).unique().all())

    def _list_entities(
        self,
        model: type[User] | type[Role] | type[Group],
        sort_fields: dict[str, object],
        *,
        page: int,
        page_size: int,
        sort: str | None,
        order_by: str | None,
        search: str | None,
        search_columns: tuple[object, ...],
    ) -> tuple[list[User] | list[Role] | list[Group], int]:
        stmt = select(model)
        count_stmt = select(func.count()).select_from(model)

        if search and search.strip():
            term = f"%{search.strip()}%"
            predicate = or_(*[col.ilike(term) for col in search_columns])
            stmt = stmt.where(predicate)
            count_stmt = count_stmt.where(predicate)

        order_column, direction = self._resolve_sort(
            sort_fields, sort=sort, order_by=order_by
        )
        if direction == "desc":
            stmt = stmt.order_by(order_column.desc())
        else:
            stmt = stmt.order_by(order_column.asc())

        offset = (page - 1) * page_size
        total = int(self._session.scalar(count_stmt) or 0)
        rows = list(
            self._session.scalars(stmt.offset(offset).limit(page_size)).all()
        )
        return rows, total

    @staticmethod
    def _resolve_sort(
        sort_fields: dict[str, object],
        *,
        sort: str | None,
        order_by: str | None,
    ) -> tuple[object, SortOrder]:
        field_name: str | None = None
        direction: SortOrder = "asc"

        if sort:
            raw = sort.strip()
            if raw.startswith("-"):
                direction = "desc"
                field_name = raw[1:] or None
            else:
                field_name = raw

        if order_by and order_by.strip().lower() in ("desc", "asc"):
            direction = order_by.strip().lower()  # type: ignore[assignment]

        if field_name and field_name in sort_fields:
            return sort_fields[field_name], direction

        default_key = next(iter(sort_fields))
        return sort_fields[default_key], direction
