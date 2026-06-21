from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_changed_by, get_db, verify_admin_mvp
from app.cache.redis_client import UserContextCache
from app.core.admin_response import conflict, grant_validation_error, not_found, ok
from app.services.permission_grant_service import GrantValidationError
from app.schemas.admin_contract import (
    ApiResponse,
    AssignGroupsToRoleBody,
    AssignUsersToRoleBody,
    GroupCatalogItem,
    PageableResponse,
    PageParams,
    PermissionGrantBody,
    RoleCreateBody,
    RoleListItem,
    RoleRenameBody,
    build_pageable,
    parse_page_params,
)
from app.services.admin_role_service import AdminRoleService
from app.services.admin_user_service import AdminUserService, _parse_user_ids

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin-roles"],
    dependencies=[Depends(verify_admin_mvp)],
)


def _role_service(
    request: Request,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> AdminRoleService:
    cache: UserContextCache | None = getattr(
        request.app.state, "user_context_cache", None
    )
    return AdminRoleService(db, changed_by=changed_by, cache=cache)


def _user_service(
    request: Request,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> AdminUserService:
    cache: UserContextCache | None = getattr(
        request.app.state, "user_context_cache", None
    )
    return AdminUserService(db, changed_by=changed_by, cache=cache)


@router.get("/roles")
def list_roles(
    svc: AdminRoleService = Depends(_role_service),
    page_params: PageParams = Depends(parse_page_params),
) -> ApiResponse[PageableResponse[RoleListItem]]:
    items, total = svc.list_roles(
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


@router.post("/roles", status_code=201)
def create_role(
    body: RoleCreateBody,
    svc: AdminRoleService = Depends(_role_service),
) -> ApiResponse[RoleListItem]:
    try:
        data = svc.create_role(body)
    except ValueError as exc:
        if str(exc) == "role_name_conflict":
            return conflict("Role name already exists", code="ROLE_NAME_CONFLICT")
        raise
    return ok(data, message="Role created")


@router.patch("/roles/{role_id}", response_model=None)
def rename_role(
    role_id: uuid.UUID,
    body: RoleRenameBody,
    svc: AdminRoleService = Depends(_role_service),
) -> Any:
    try:
        data = svc.rename_role(role_id, body)
    except ValueError as exc:
        if str(exc) == "role_name_conflict":
            return conflict("Role name already exists", code="ROLE_NAME_CONFLICT")
        raise
    if data is None:
        return not_found("Role not found")
    return ok(data, message="Role renamed")


@router.post("/roles/{role_id}/duplicate", status_code=201, response_model=None)
def duplicate_role(
    role_id: uuid.UUID,
    svc: AdminRoleService = Depends(_role_service),
) -> Any:
    try:
        data = svc.duplicate_role(role_id)
    except ValueError as exc:
        if str(exc) == "role_name_conflict":
            return conflict("Role name already exists", code="ROLE_NAME_CONFLICT")
        raise
    if data is None:
        return not_found("Role not found")
    return ok(data, message="Role duplicated")


@router.delete("/roles/{role_id}", response_model=None)
def delete_role(
    role_id: uuid.UUID,
    svc: AdminRoleService = Depends(_role_service),
) -> Any:
    try:
        deleted = svc.delete_role(role_id)
    except ValueError as exc:
        if str(exc) == "role_in_use":
            return conflict(
                "Role is assigned to users or groups",
                code="ENTITY_IN_USE",
            )
        raise
    if not deleted:
        return not_found("Role not found")
    return ok(message="Role deleted")


@router.get("/roles/{role_id}/permissions", response_model=None)
def list_role_permissions(
    role_id: uuid.UUID,
    svc: AdminRoleService = Depends(_role_service),
) -> Any:
    data = svc.list_permissions(role_id)
    if data is None:
        return not_found("Role not found")
    return ok(data)


@router.post("/roles/{role_id}/permissions", status_code=201, response_model=None)
def grant_role_permissions(
    role_id: uuid.UUID,
    body: PermissionGrantBody,
    svc: AdminRoleService = Depends(_role_service),
) -> Any:
    try:
        data = svc.grant_permissions(role_id, body)
    except GrantValidationError as exc:
        return grant_validation_error(exc.message, code=exc.code, status=exc.status)
    if data is None:
        return not_found("Role not found")
    return ok(data, message="Permissions created")


@router.put("/roles/{role_id}/permissions/{permission_id}", response_model=None)
def update_role_permission(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    body: PermissionGrantBody,
    svc: AdminRoleService = Depends(_role_service),
) -> Any:
    try:
        data = svc.update_permission(role_id, permission_id, body)
    except GrantValidationError as exc:
        return grant_validation_error(exc.message, code=exc.code, status=exc.status)
    if data is None:
        return not_found("Role or permission not found")
    return ok(data, message="Permission updated")


@router.delete("/roles/{role_id}/permissions/{permission_id}", response_model=None)
def delete_role_permission(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    svc: AdminRoleService = Depends(_role_service),
) -> Any:
    deleted = svc.delete_permission(role_id, permission_id)
    if not deleted:
        return not_found("Role or permission not found")
    return ok(message="Permission deleted")


@router.get("/roles/{role_id}/actors", response_model=None)
def get_role_actors(
    role_id: uuid.UUID,
    svc: AdminRoleService = Depends(_role_service),
) -> Any:
    data = svc.get_actors(role_id)
    if data is None:
        return not_found("Role not found")
    return ok(data)


@router.post("/roles/{role_id}/users", response_model=None)
def assign_users_to_role(
    role_id: uuid.UUID,
    body: AssignUsersToRoleBody,
    svc: AdminUserService = Depends(_user_service),
) -> Any:
    try:
        data = svc.assign_users_to_role(role_id, _parse_user_ids(body.user_ids))
    except ValueError as exc:
        if str(exc) == "role_not_found":
            return not_found("Role not found")
        raise
    return ok(data, message="Users assigned to role")


@router.delete("/roles/{role_id}/users/{user_id}", response_model=None)
def remove_user_from_role(
    role_id: uuid.UUID,
    user_id: uuid.UUID,
    svc: AdminUserService = Depends(_user_service),
) -> Any:
    try:
        removed = svc.remove_user_from_role(role_id, user_id)
    except ValueError as exc:
        if str(exc) == "role_not_found":
            return not_found("Role not found")
        if str(exc) == "user_not_found":
            return not_found("User not found")
        raise
    return ok({"removed": removed})


@router.post("/roles/{role_id}/groups", response_model=None)
def assign_groups_to_role(
    role_id: uuid.UUID,
    body: AssignGroupsToRoleBody,
    svc: AdminRoleService = Depends(_role_service),
) -> Any:
    data = svc.assign_groups_to_role(role_id, body)
    if data is None:
        return not_found("Role not found")
    return ok(data, message="Groups assigned to role")


@router.delete("/roles/{role_id}/groups/{group_id}", response_model=None)
def remove_group_from_role(
    role_id: uuid.UUID,
    group_id: uuid.UUID,
    svc: AdminRoleService = Depends(_role_service),
) -> Any:
    try:
        removed = svc.remove_group_from_role(role_id, group_id)
    except ValueError as exc:
        if str(exc) == "role_not_found":
            return not_found("Role not found")
        if str(exc) == "group_not_found":
            return not_found("Group not found")
        raise
    return ok({"removed": removed})


@router.get("/groups/catalog")
def groups_catalog(
    svc: AdminRoleService = Depends(_role_service),
    page_params: PageParams = Depends(parse_page_params),
) -> ApiResponse[PageableResponse[GroupCatalogItem]]:
    items, total = svc.groups_catalog(
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
