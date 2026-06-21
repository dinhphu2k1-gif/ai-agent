from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_changed_by, get_db, verify_admin_mvp
from app.cache.redis_client import UserContextCache
from app.core.admin_response import conflict, forbidden, grant_validation_error, not_found, ok
from app.services.permission_grant_service import GrantValidationError
from app.schemas.admin_contract import (
    ApiResponse,
    AssignMembersBody,
    AssignRolesToGroupBody,
    EffectivePermissionsData,
    FePermissionOut,
    GroupCreateBody,
    GroupListItem,
    GroupMemberOut,
    GroupRoleOut,
    PageableResponse,
    PageParams,
    PermissionGrantBody,
    PermissionsCreatedData,
    RoleCatalogItem,
    UserCatalogItem,
    build_pageable,
    parse_page_params,
)
from app.services.admin_group_service import AdminGroupService

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin-groups"],
    dependencies=[Depends(verify_admin_mvp)],
)


def _group_service(
    request: Request,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> AdminGroupService:
    cache: UserContextCache | None = getattr(
        request.app.state, "user_context_cache", None
    )
    return AdminGroupService(db, changed_by=changed_by, cache=cache)


@router.get("/groups")
def list_groups(
    svc: AdminGroupService = Depends(_group_service),
    page_params: PageParams = Depends(parse_page_params),
) -> ApiResponse[PageableResponse[GroupListItem]]:
    items, total = svc.list_groups(
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


@router.post("/groups", status_code=201)
def create_group(
    body: GroupCreateBody,
    svc: AdminGroupService = Depends(_group_service),
) -> ApiResponse[GroupListItem]:
    try:
        data = svc.create_group(body)
    except ValueError as exc:
        if str(exc) == "group_name_conflict":
            return conflict("Group name already exists", code="GROUP_NAME_CONFLICT")
        raise
    return ok(data, message="Group created")


@router.delete("/groups/{group_id}", response_model=None)
def delete_group(
    group_id: uuid.UUID,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    deleted = svc.delete_group(group_id)
    if not deleted:
        return not_found("Group not found")
    return ok(message="Group deleted")


@router.get("/members/catalog")
def members_catalog(
    svc: AdminGroupService = Depends(_group_service),
    page_params: PageParams = Depends(parse_page_params),
) -> ApiResponse[PageableResponse[UserCatalogItem]]:
    items, total = svc.members_catalog(
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


@router.get("/roles/catalog")
def roles_catalog(
    svc: AdminGroupService = Depends(_group_service),
    page_params: PageParams = Depends(parse_page_params),
) -> ApiResponse[PageableResponse[RoleCatalogItem]]:
    items, total = svc.roles_catalog(
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


@router.get("/groups/{group_id}/members", response_model=None)
def list_group_members(
    group_id: uuid.UUID,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    data = svc.list_members(group_id)
    if data is None:
        return not_found("Group not found")
    return ok(data)


@router.post("/groups/{group_id}/members", response_model=None)
def add_group_members(
    group_id: uuid.UUID,
    body: AssignMembersBody,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    data = svc.add_members(group_id, body)
    if data is None:
        return not_found("Group not found")
    return ok(data, message="Members added")


@router.delete("/groups/{group_id}/members/{member_id}", response_model=None)
def remove_group_member(
    group_id: uuid.UUID,
    member_id: uuid.UUID,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    try:
        removed = svc.remove_member(group_id, member_id)
    except ValueError as exc:
        if str(exc) == "group_not_found":
            return not_found("Group not found")
        if str(exc) == "user_not_found":
            return not_found("Member not found")
        raise
    return ok({"removed": removed})


@router.get("/groups/{group_id}/roles", response_model=None)
def list_group_roles(
    group_id: uuid.UUID,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    data = svc.list_group_roles(group_id)
    if data is None:
        return not_found("Group not found")
    return ok(data)


@router.post("/groups/{group_id}/roles", response_model=None)
def assign_group_roles(
    group_id: uuid.UUID,
    body: AssignRolesToGroupBody,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    data = svc.assign_roles(group_id, body)
    if data is None:
        return not_found("Group not found")
    return ok(data, message="Roles assigned")


@router.delete("/groups/{group_id}/roles/{role_id}", response_model=None)
def unassign_group_role(
    group_id: uuid.UUID,
    role_id: uuid.UUID,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    try:
        removed = svc.unassign_role(group_id, role_id)
    except ValueError as exc:
        if str(exc) == "group_not_found":
            return not_found("Group not found")
        if str(exc) == "role_not_found":
            return not_found("Role not found")
        raise
    return ok({"removed": removed})


@router.get("/groups/{group_id}/permissions", response_model=None)
def list_group_permissions(
    group_id: uuid.UUID,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    data = svc.list_direct_permissions(group_id)
    if data is None:
        return not_found("Group not found")
    return ok(data)


@router.post("/groups/{group_id}/permissions", status_code=201, response_model=None)
def grant_group_permissions(
    group_id: uuid.UUID,
    body: PermissionGrantBody,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    try:
        data = svc.grant_permissions(group_id, body)
    except GrantValidationError as exc:
        return grant_validation_error(exc.message, code=exc.code, status=exc.status)
    if data is None:
        return not_found("Group not found")
    return ok(data, message="Permissions created")


@router.put("/groups/{group_id}/permissions/{permission_id}", response_model=None)
def update_group_permission(
    group_id: uuid.UUID,
    permission_id: uuid.UUID,
    body: PermissionGrantBody,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    try:
        data = svc.update_direct_permission(group_id, permission_id, body)
    except ValueError as exc:
        if str(exc) == "not_direct":
            return forbidden(
                "Cannot modify inherited role permission via group API",
                code="PERMISSION_NOT_DIRECT",
            )
        raise
    except GrantValidationError as exc:
        return grant_validation_error(exc.message, code=exc.code, status=exc.status)
    if data is None:
        return not_found("Group or permission not found")
    return ok(data, message="Permission updated")


@router.delete("/groups/{group_id}/permissions/{permission_id}", response_model=None)
def delete_group_permission(
    group_id: uuid.UUID,
    permission_id: uuid.UUID,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    result = svc.delete_direct_permission(group_id, permission_id)
    if result == "not_direct":
        return forbidden(
            "Cannot delete inherited role permission via group API",
            code="PERMISSION_NOT_DIRECT",
        )
    if not result:
        return not_found("Group or permission not found")
    return ok(message="Permission deleted")


@router.get("/groups/{group_id}/effective-permissions", response_model=None)
def get_effective_permissions(
    group_id: uuid.UUID,
    svc: AdminGroupService = Depends(_group_service),
) -> Any:
    data = svc.get_effective_permissions(group_id)
    if data is None:
        return not_found("Group not found")
    return ok(data)
