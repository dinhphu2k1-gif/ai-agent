"""Import all model modules so Alembic and metadata see every table."""

from app.models.audit import AccessLog, PermissionChangeLog
from app.models.base import Base
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
from app.models.permission import ColumnMask, Permission, PermissionType, RowFilter
from app.models.resource import Column, Database, Resource, Schema, Table

metadata = Base.metadata

__all__ = [
    "Base",
    "metadata",
    "Resource",
    "Database",
    "Schema",
    "Table",
    "Column",
    "PermissionType",
    "Permission",
    "RowFilter",
    "ColumnMask",
    "User",
    "Group",
    "Role",
    "UserGroup",
    "UserRole",
    "GroupRole",
    "UserPermission",
    "GroupPermission",
    "RolePermission",
    "AccessLog",
    "PermissionChangeLog",
]
