from __future__ import annotations

from datetime import datetime
from typing import Generic, Literal, TypeVar

from fastapi import HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class ApiErrorData(BaseModel):
    code: str
    field: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None


class PageableResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)

    data: list[T]
    current_page: int = Field(alias="currentPage")
    total_items: int = Field(alias="totalItems")
    total_pages: int = Field(alias="totalPages")


class PageParams(BaseModel):
    """1-based pagination parameters for admin list endpoints."""

    page: int = 1
    page_size: int = 10
    sort: str | None = None
    order_by: str | None = None
    search: str | None = None

    @field_validator("page")
    @classmethod
    def _page_at_least_one(cls, value: int) -> int:
        if value < 1:
            raise ValueError("page must be >= 1")
        return value

    @field_validator("page_size")
    @classmethod
    def _page_size_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("pageSize must be >= 1")
        return value

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def parse_page_params(
    page: int = Query(1, ge=1, alias="page"),
    page_size: int = Query(10, ge=1, le=500, alias="pageSize"),
    sort: str | None = Query(default=None),
    order_by: str | None = Query(default=None, alias="orderBy"),
    search: str | None = Query(default=None),
) -> PageParams:
    try:
        return PageParams(
            page=page,
            page_size=page_size,
            sort=sort,
            order_by=order_by,
            search=search,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


def build_pageable(
    items: list[T],
    *,
    page: int,
    page_size: int,
    total_items: int,
) -> PageableResponse[T]:
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0
    return PageableResponse(
        data=items,
        currentPage=page,
        totalItems=total_items,
        totalPages=total_pages,
    )


class NamedRef(BaseModel):
    id: str
    name: str


class UserListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    email: str
    status: str
    groups: list[str]
    roles: list[str]
    initials: str
    last_active: str | None = Field(default=None, alias="lastActive")
    last_active_at: datetime | None = Field(default=None, alias="lastActiveAt")


class UserDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    email: str
    username: str
    status: str
    groups: list[NamedRef]
    roles: list[NamedRef]
    initials: str
    last_active: str | None = Field(default=None, alias="lastActive")
    last_active_at: datetime | None = Field(default=None, alias="lastActiveAt")


class UserCreateBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(alias="fullName")
    email: str
    username: str
    groups: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    is_active: bool = Field(default=True, alias="isActive")


class GroupOptionsOut(BaseModel):
    groups: list[str]


class RoleOptionsOut(BaseModel):
    roles: list[str]


class BulkUpdatedData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    updated_count: int = Field(alias="updatedCount")


class BulkAssignGroupsBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_ids: list[str] = Field(alias="userIds")
    group_ids: list[str] = Field(default_factory=list, alias="groupIds")
    group_names: list[str] = Field(default_factory=list, alias="groupNames")


class BulkAssignRolesBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_ids: list[str] = Field(alias="userIds")
    role_ids: list[str] = Field(default_factory=list, alias="roleIds")
    role_names: list[str] = Field(default_factory=list, alias="roleNames")


class BulkDeactivateBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_ids: list[str] = Field(alias="userIds")


class AssignUsersToRoleBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_ids: list[str] = Field(alias="userIds")


class PathLabel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str
    resource_id: str | None = Field(default=None, alias="resourceId")


class PermissionModifierOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["ROW_FILTER", "COLUMN_MASK"]
    label: str
    condition_expression: str | None = Field(
        default=None, alias="conditionExpression"
    )
    mask_type: str | None = Field(default=None, alias="maskType")
    mask_pattern: str | None = Field(default=None, alias="maskPattern")


class FePermissionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    resource_type: str = Field(alias="resourceType")
    path: list[PathLabel]
    effect: str
    action: str
    modifier: PermissionModifierOut | None = None
    is_highlighted: bool | None = Field(default=None, alias="isHighlighted")


class RolePermissionsSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    allow_count: int = Field(alias="allowCount")
    deny_count: int = Field(alias="denyCount")
    modifier_count: int = Field(alias="modifierCount")


class RolePermissionsData(BaseModel):
    permissions: list[FePermissionOut]
    summary: RolePermissionsSummary


class PermissionsCreatedData(BaseModel):
    created: list[FePermissionOut]


class RoleListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    display_name: str = Field(alias="displayName")
    permission_count: int = Field(alias="permissionCount")
    user_count: int = Field(alias="userCount")
    group_count: int = Field(alias="groupCount")
    icon: str = "shield"


class RoleCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class RoleRenameBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ResourcePathSegment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    type: str


class ColumnMaskGrant(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = False
    mask_type: str | None = Field(default=None, alias="maskType")
    mask_pattern: str | None = Field(default=None, alias="maskPattern")


class RowFilterGrant(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = False
    condition_expression: str | None = Field(
        default=None, alias="conditionExpression"
    )


class PermissionGrantBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resource_path: list[ResourcePathSegment] = Field(alias="resourcePath")
    resource_type: str = Field(alias="resourceType")
    actions: list[str]
    effect: Literal["ALLOW", "DENY"]
    column_mask: ColumnMaskGrant | None = Field(default=None, alias="columnMask")
    row_filter: RowFilterGrant | None = Field(default=None, alias="rowFilter")


class ActorUserOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    email: str
    avatar_url: str | None = Field(default=None, alias="avatarUrl")
    is_online: bool = Field(default=False, alias="isOnline")


class ActorGroupOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    member_count: int = Field(alias="memberCount")


class RoleActorsData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    users: list[ActorUserOut]
    groups: list[ActorGroupOut]
    total_affected_users: int = Field(alias="totalAffectedUsers")


class AssignGroupsToRoleBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_ids: list[str] = Field(alias="groupIds")


class UserCatalogItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    email: str
    is_online: bool = Field(alias="isOnline")
    avatar_url: str | None = Field(default=None, alias="avatarUrl")


class GroupCatalogItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    member_count: int = Field(alias="memberCount")
    description: str | None = None


class EffectivePermissionOut(FePermissionOut):
    model_config = ConfigDict(populate_by_name=True)

    ownership: Literal["group", "role"]
    source_role_id: str | None = Field(default=None, alias="sourceRoleId")
    source_role_name: str = Field(alias="sourceRoleName")


class InheritedSummaryOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    permission_count: int = Field(alias="permissionCount")
    resource_type_count: int = Field(alias="resourceTypeCount")
    role_count: int = Field(alias="roleCount")


class EffectivePermissionsData(BaseModel):
    permissions: list[EffectivePermissionOut]
    summary: RolePermissionsSummary
    inherited_summary: InheritedSummaryOut = Field(alias="inheritedSummary")


class GroupListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    member_count: int = Field(alias="memberCount")
    role_count: int = Field(alias="roleCount")
    description: str | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    created_at_label: str | None = Field(default=None, alias="createdAtLabel")


class GroupCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)


class GroupMemberOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    email: str
    initials: str
    status: str


class AssignMembersBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    member_ids: list[str] = Field(alias="memberIds")


class AssignRolesToGroupBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role_ids: list[str] = Field(alias="roleIds")


class GroupRoleOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: str | None = None
    permission_count: int = Field(alias="permissionCount")


class RoleCatalogItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: str | None = None
    permission_count: int = Field(alias="permissionCount")


class ResourceTreeNodeOut(BaseModel):
    """Permission wizard tree node (contract §G.1)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    type: Literal["database", "schema", "table", "column"]
    children: list[ResourceTreeNodeOut] | None = None
    is_primary_key: bool | None = Field(default=None, alias="isPrimaryKey")
    is_foreign_key: bool | None = Field(default=None, alias="isForeignKey")


class ResourceSearchResultOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    node: ResourceTreeNodeOut
    path: list[ResourcePathSegment]
    breadcrumb: str


class ResourceSearchData(BaseModel):
    results: list[ResourceSearchResultOut]


class ResourceScopeStatsOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resource_id: str = Field(alias="resourceId")
    resource_name: str = Field(alias="resourceName")
    resource_type: Literal["database", "schema"] = Field(alias="resourceType")
    schema_count: int = Field(alias="schemaCount")
    table_count: int = Field(alias="tableCount")
    column_count: int = Field(alias="columnCount")
    message: str


class ActionCatalogOut(BaseModel):
    actions: list[str]


class RowFilterValidateBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resource_path: list[ResourcePathSegment] = Field(
        default_factory=list, alias="resourcePath"
    )
    condition_expression: str = Field(alias="conditionExpression")


class RowFilterValidateResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    valid: bool
    normalized_expression: str | None = Field(
        default=None, alias="normalizedExpression"
    )
    errors: list[str] = Field(default_factory=list)


class ColumnMaskPreviewBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mask_type: str = Field(alias="maskType")
    mask_pattern: str | None = Field(default=None, alias="maskPattern")
    sample_value: str = Field(alias="sampleValue")


class ColumnMaskPreviewResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    masked_value: str = Field(alias="maskedValue")
    algorithm: str
