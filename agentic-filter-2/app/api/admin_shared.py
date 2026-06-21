"""Shared admin contract endpoints (§H #41+)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_admin_mvp
from app.core.admin_response import fail, not_found, ok
from app.schemas.admin_contract import ApiResponse, ResourceTreeNodeOut
from app.services.resource_tree_service import ResourceTreeError, ResourceTreeService

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin-shared"],
    dependencies=[Depends(verify_admin_mvp)],
)


@router.get("/resources/tree", response_model=ApiResponse[list[ResourceTreeNodeOut]])
def get_admin_resource_tree(
    parent_id: Annotated[
        uuid.UUID | None,
        Query(alias="parentId", description="Lazy-load direct children of this node"),
    ] = None,
    db: Session = Depends(get_db),
) -> ApiResponse[list[ResourceTreeNodeOut]] | JSONResponse:
    """Contract §G.1 — full nested tree, or one level when ``parentId`` is set (Phase 6)."""
    svc = ResourceTreeService(db)
    if parent_id is not None:
        try:
            return ok(svc.build_children_for_parent(parent_id))
        except ResourceTreeError as exc:
            if exc.code == "NOT_FOUND":
                return not_found(exc.message)
            body = fail(exc.message, code=exc.code)
            return JSONResponse(status_code=400, content=body.model_dump())
    return ok(svc.build_fe_tree())
