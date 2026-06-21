from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_changed_by, get_db, verify_admin_mvp
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin import (
    ColumnMaskCreate,
    ColumnMaskOut,
    PermissionCreate,
    PermissionOut,
    PermissionPatch,
    RowFilterCreate,
    RowFilterOut,
)
from app.services.audit_service import record_policy_change

router = APIRouter(
    prefix="/api/v1/admin/permissions",
    tags=["admin-permissions"],
    dependencies=[Depends(verify_admin_mvp)],
)


@router.post("", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
def create_permission(
    body: PermissionCreate,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> PermissionOut:
    rr = ResourceRepository(db)
    if rr.get_resource(body.resource_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    pr = PermissionRepository(db)
    perm = pr.create_permission(
        resource_id=body.resource_id,
        permission_type_id=body.permission_type_id,
        effect=body.effect,
    )
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="PERMISSION_CREATE",
        permission_id=perm.id,
        detail={"resource_id": str(body.resource_id), "effect": body.effect},
    )
    return PermissionOut.model_validate(perm)


@router.get("", response_model=list[PermissionOut])
def list_permissions(
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
) -> list[PermissionOut]:
    pr = PermissionRepository(db)
    rows = pr.list_permissions(limit=min(limit, 500), offset=max(offset, 0))
    return [PermissionOut.model_validate(p) for p in rows]


@router.patch("/{permission_id}", response_model=PermissionOut)
def patch_permission(
    permission_id: uuid.UUID,
    body: PermissionPatch,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> PermissionOut:
    pr = PermissionRepository(db)
    row = pr.update_permission_effect(permission_id, body.effect)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="PERMISSION_UPDATE",
        permission_id=permission_id,
        detail={"effect": body.effect},
    )
    return PermissionOut.model_validate(row)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> None:
    pr = PermissionRepository(db)
    if pr.get_permission(permission_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="PERMISSION_DELETE",
        permission_id=permission_id,
        detail=None,
    )
    pr.delete_permission(permission_id)


@router.post(
    "/{permission_id}/row-filters",
    response_model=RowFilterOut,
    status_code=status.HTTP_201_CREATED,
)
def create_row_filter(
    permission_id: uuid.UUID,
    body: RowFilterCreate,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> RowFilterOut:
    pr = PermissionRepository(db)
    if pr.get_permission(permission_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    rf = pr.create_row_filter(permission_id=permission_id, condition_expr=body.condition_expr)
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="ROW_FILTER_CREATE",
        permission_id=permission_id,
        detail={"row_filter_id": str(rf.id)},
    )
    return RowFilterOut.model_validate(rf)


@router.post(
    "/{permission_id}/column-masks",
    response_model=ColumnMaskOut,
    status_code=status.HTTP_201_CREATED,
)
def upsert_column_mask(
    permission_id: uuid.UUID,
    body: ColumnMaskCreate,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> ColumnMaskOut:
    pr = PermissionRepository(db)
    if pr.get_permission(permission_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    if body.mask_type == "CUSTOM" and not (body.mask_pattern and body.mask_pattern.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mask_pattern is required when mask_type is CUSTOM",
        )
    cm = pr.upsert_column_mask(
        permission_id=permission_id,
        mask_type=body.mask_type,
        mask_pattern=body.mask_pattern,
    )
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="COLUMN_MASK_UPSERT",
        permission_id=permission_id,
        detail={"mask_type": body.mask_type},
    )
    return ColumnMaskOut.model_validate(cm)
