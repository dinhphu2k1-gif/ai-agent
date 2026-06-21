"""Add Permission wizard helper APIs (search, scope stats, action catalog)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_admin_mvp
from app.core.admin_response import fail, not_found, ok
from app.core.permission_actions import catalog_actions_for_resource_type
from app.schemas.admin_contract import (
    ActionCatalogOut,
    ApiResponse,
    ColumnMaskPreviewBody,
    ColumnMaskPreviewResult,
    ResourceScopeStatsOut,
    ResourceSearchData,
    RowFilterValidateBody,
    RowFilterValidateResult,
)
from app.services.permission_validation_service import PermissionValidationService
from app.services.resource_catalog_service import (
    ResourceCatalogError,
    ResourceCatalogService,
)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin-permission-wizard"],
    dependencies=[Depends(verify_admin_mvp)],
)


def _catalog_error(exc: ResourceCatalogError) -> JSONResponse:
    if exc.code == "NOT_FOUND":
        return not_found(exc.message)
    body = fail(exc.message, code=exc.code)
    return JSONResponse(status_code=400, content=body.model_dump())


@router.get(
    "/resources/search",
    response_model=ApiResponse[ResourceSearchData],
)
def search_resources(
    q: str = Query("", description="Search text matched against resource names"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ApiResponse[ResourceSearchData]:
    data = ResourceCatalogService(db).search(q, limit=limit)
    return ok(data)


@router.get(
    "/resources/{resource_id}/scope-stats",
    response_model=ApiResponse[ResourceScopeStatsOut],
)
def resource_scope_stats(
    resource_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ApiResponse[ResourceScopeStatsOut] | JSONResponse:
    try:
        stats = ResourceCatalogService(db).scope_stats(resource_id)
    except ResourceCatalogError as exc:
        return _catalog_error(exc)
    return ok(stats)


@router.get(
    "/permissions/action-catalog",
    response_model=ApiResponse[ActionCatalogOut],
)
def permission_action_catalog(
    resource_type: str = Query(
        ...,
        alias="resourceType",
        description="DATABASE, SCHEMA, TABLE, or COLUMN",
    ),
    db: Session = Depends(get_db),
) -> ApiResponse[ActionCatalogOut] | JSONResponse:
    actions = catalog_actions_for_resource_type(db, resource_type)
    if not actions:
        body = fail(
            f"Unknown or unsupported resourceType: {resource_type}",
            code="BAD_REQUEST",
        )
        return JSONResponse(status_code=400, content=body.model_dump())
    return ok(ActionCatalogOut(actions=actions))


@router.post(
    "/permissions/validate/row-filter",
    response_model=ApiResponse[RowFilterValidateResult],
)
def validate_row_filter(
    body: RowFilterValidateBody,
    db: Session = Depends(get_db),
) -> ApiResponse[RowFilterValidateResult]:
    result = PermissionValidationService(db).validate_row_filter(
        body.resource_path,
        body.condition_expression,
    )
    return ok(result)


@router.post(
    "/permissions/preview/column-mask",
    response_model=ApiResponse[ColumnMaskPreviewResult],
)
def preview_column_mask(
    body: ColumnMaskPreviewBody,
    db: Session = Depends(get_db),
) -> ApiResponse[ColumnMaskPreviewResult] | JSONResponse:
    try:
        result = PermissionValidationService(db).preview_column_mask(
            body.mask_type,
            body.mask_pattern,
            body.sample_value,
        )
    except ValueError as exc:
        err_body = fail(str(exc), code="BAD_REQUEST")
        return JSONResponse(status_code=400, content=err_body.model_dump())
    return ok(result)
