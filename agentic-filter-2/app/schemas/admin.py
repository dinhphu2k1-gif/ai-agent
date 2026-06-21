from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DatabaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)


class DatabaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_id: uuid.UUID
    name: str
    description: str | None


class SchemaCreate(BaseModel):
    database_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)


class SchemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_id: uuid.UUID
    database_id: uuid.UUID
    name: str


class TableCreate(BaseModel):
    schema_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)


class TableOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_id: uuid.UUID
    schema_id: uuid.UUID
    name: str


class ColumnCreate(BaseModel):
    table_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    data_type: str = Field(..., min_length=1, max_length=128)
    is_primary_key: bool | None = Field(default=None, alias="isPrimaryKey")
    is_foreign_key: bool | None = Field(default=None, alias="isForeignKey")


class ColumnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_id: uuid.UUID
    table_id: uuid.UUID
    name: str
    data_type: str
    is_primary_key: bool | None = Field(default=None, alias="isPrimaryKey")
    is_foreign_key: bool | None = Field(default=None, alias="isForeignKey")


class ColumnTreeOut(BaseModel):
    resource_id: uuid.UUID
    name: str
    data_type: str


class TableTreeOut(BaseModel):
    resource_id: uuid.UUID
    name: str
    columns: list[ColumnTreeOut]


class SchemaTreeOut(BaseModel):
    resource_id: uuid.UUID
    name: str
    tables: list[TableTreeOut]


class DatabaseTreeOut(BaseModel):
    resource_id: uuid.UUID
    name: str
    schemas: list[SchemaTreeOut]


class ResourceTreeOut(BaseModel):
    databases: list[DatabaseTreeOut]


EffectLiteral = Literal["ALLOW", "DENY"]


class PermissionCreate(BaseModel):
    resource_id: uuid.UUID
    permission_type_id: uuid.UUID
    effect: EffectLiteral


class PermissionPatch(BaseModel):
    effect: EffectLiteral


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resource_id: uuid.UUID
    permission_type_id: uuid.UUID
    effect: str


class AssignPermissionBody(BaseModel):
    permission_id: uuid.UUID
    granted_by: str | None = Field(default=None, max_length=255)


class AssignGroupBody(BaseModel):
    group_id: uuid.UUID


class AssignRoleBody(BaseModel):
    role_id: uuid.UUID


class RowFilterCreate(BaseModel):
    condition_expr: str = Field(..., min_length=1)


class RowFilterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    permission_id: uuid.UUID
    condition_expr: str


MaskTypeLiteral = Literal["FULL", "PARTIAL", "HASH", "NULLIFY", "CUSTOM"]


class ColumnMaskCreate(BaseModel):
    mask_type: MaskTypeLiteral
    mask_pattern: str | None = None


class ColumnMaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    permission_id: uuid.UUID
    mask_type: str
    mask_pattern: str | None


class AccessLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    resource_id: uuid.UUID | None
    action: str
    result: str
    decision: str | None = None
    request_id: str | None = None
    accessed_at: datetime


class PermissionChangeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    permission_id: uuid.UUID | None
    changed_by: str
    change_type: str
    changed_at: datetime
    detail: dict | None
