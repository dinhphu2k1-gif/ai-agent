from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_changed_by, get_db, verify_admin_mvp
from app.cache.redis_client import UserContextCache
from app.core.admin_response import not_found, ok
from app.schemas.admin_contract import (
    ApiResponse,
    BulkAssignGroupsBody,
    BulkAssignRolesBody,
    BulkDeactivateBody,
    BulkUpdatedData,
    GroupOptionsOut,
    PageableResponse,
    PageParams,
    RoleOptionsOut,
    UserCatalogItem,
    UserCreateBody,
    UserDetail,
    UserListItem,
    build_pageable,
    parse_page_params,
)
from app.services.admin_role_service import AdminRoleService
from app.services.admin_user_service import AdminUserService

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin-users"],
    dependencies=[Depends(verify_admin_mvp)],
)


def _user_service(
    request: Request,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> AdminUserService:
    cache: UserContextCache | None = getattr(
        request.app.state, "user_context_cache", None
    )
    return AdminUserService(db, changed_by=changed_by, cache=cache)


def _role_service(
    request: Request,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> AdminRoleService:
    cache: UserContextCache | None = getattr(
        request.app.state, "user_context_cache", None
    )
    return AdminRoleService(db, changed_by=changed_by, cache=cache)


@router.get("/users/catalog")
def users_catalog(
    svc: AdminRoleService = Depends(_role_service),
    page_params: PageParams = Depends(parse_page_params),
) -> ApiResponse[PageableResponse[UserCatalogItem]]:
    items, total = svc.users_catalog(
        page=page_params.page,
        page_size=page_params.page_size,
        sort=page_params.sort,
        order_by=page_params.order_by,
        search=page_params.search,
    )
    page = build_pageable(
        items,
        page=page_params.page,
        page_size=page_params.page_size,
        total_items=total,
    )
    return ok(page)


@router.get("/users")
def list_users(
    page_params: PageParams = Depends(parse_page_params),
    status: str | None = Query(default="All"),
    svc: AdminUserService = Depends(_user_service),
) -> ApiResponse[PageableResponse[UserListItem]]:
    items, total = svc.list_users(
        page=page_params.page,
        page_size=page_params.page_size,
        sort=page_params.sort,
        order_by=page_params.order_by,
        search=page_params.search,
        status=status,
    )
    page = build_pageable(
        items,
        page=page_params.page,
        page_size=page_params.page_size,
        total_items=total,
    )
    return ok(page)


@router.get("/users/{user_id}", response_model=None)
def get_user(
    user_id: uuid.UUID,
    svc: AdminUserService = Depends(_user_service),
) -> Any:
    detail = svc.get_user(user_id)
    if detail is None:
        return not_found("User not found")
    return ok(detail)


@router.post("/users", status_code=201)
def create_user(
    body: UserCreateBody,
    svc: AdminUserService = Depends(_user_service),
) -> ApiResponse[UserDetail]:
    detail = svc.create_user(body)
    return ok(detail, message="User created")


@router.get("/groups/options")
def group_options(
    svc: AdminUserService = Depends(_user_service),
) -> ApiResponse[GroupOptionsOut]:
    return ok(svc.group_options())


@router.get("/roles/options")
def role_options(
    svc: AdminUserService = Depends(_user_service),
) -> ApiResponse[RoleOptionsOut]:
    return ok(svc.role_options())


@router.post("/users/bulk/assign-groups")
def bulk_assign_groups(
    body: BulkAssignGroupsBody,
    svc: AdminUserService = Depends(_user_service),
) -> ApiResponse[BulkUpdatedData]:
    data = svc.bulk_assign_groups(body)
    return ok(data, message="Groups assigned")


@router.post("/users/bulk/assign-roles")
def bulk_assign_roles(
    body: BulkAssignRolesBody,
    svc: AdminUserService = Depends(_user_service),
) -> ApiResponse[BulkUpdatedData]:
    data = svc.bulk_assign_roles(body)
    return ok(data, message="Roles assigned")


@router.post("/users/bulk/deactivate")
def bulk_deactivate(
    body: BulkDeactivateBody,
    svc: AdminUserService = Depends(_user_service),
) -> ApiResponse[BulkUpdatedData]:
    data = svc.bulk_deactivate(body)
    return ok(data, message="Users deactivated")
