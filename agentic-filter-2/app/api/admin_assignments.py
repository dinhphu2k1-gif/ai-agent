from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_changed_by, get_db, verify_admin_mvp
from app.core.errors import ErrorCode, error_response
from app.models.identity import UserGroup
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.schemas.admin import AssignGroupBody, AssignPermissionBody, AssignRoleBody
from app.services.audit_service import record_policy_change

router = APIRouter(
    prefix="/api/v1/admin/assignments",
    tags=["admin-assignments"],
    dependencies=[Depends(verify_admin_mvp)],
)


def _require_permission(db: Session, permission_id: uuid.UUID) -> None:
    pr = PermissionRepository(db)
    if pr.get_permission(permission_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )


@router.post("/users/{user_id}/permissions", status_code=status.HTTP_201_CREATED)
def assign_user_permission(
    user_id: uuid.UUID,
    body: AssignPermissionBody,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> dict[str, str]:
    ir = IdentityRepository(db)
    if ir.get_user(user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _require_permission(db, body.permission_id)
    ir.add_user_permission(
        user_id, body.permission_id, granted_by=body.granted_by or changed_by
    )
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="USER_PERMISSION_ASSIGN",
        permission_id=body.permission_id,
        detail={"user_id": str(user_id)},
    )
    return {"status": "ok"}


@router.post("/groups/{group_id}/permissions", status_code=status.HTTP_201_CREATED)
def assign_group_permission(
    group_id: uuid.UUID,
    body: AssignPermissionBody,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> dict[str, str]:
    ir = IdentityRepository(db)
    if ir.get_group(group_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    _require_permission(db, body.permission_id)
    ir.add_group_permission(group_id, body.permission_id)
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="GROUP_PERMISSION_ASSIGN",
        permission_id=body.permission_id,
        detail={"group_id": str(group_id)},
    )
    return {"status": "ok"}


@router.post("/roles/{role_id}/permissions", status_code=status.HTTP_201_CREATED)
def assign_role_permission(
    role_id: uuid.UUID,
    body: AssignPermissionBody,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> dict[str, str]:
    ir = IdentityRepository(db)
    if ir.get_role(role_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    _require_permission(db, body.permission_id)
    ir.add_role_permission(role_id, body.permission_id)
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="ROLE_PERMISSION_ASSIGN",
        permission_id=body.permission_id,
        detail={"role_id": str(role_id)},
    )
    return {"status": "ok"}


@router.post("/users/{user_id}/groups", status_code=status.HTTP_201_CREATED)
def add_user_to_group(
    user_id: uuid.UUID,
    body: AssignGroupBody,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> dict[str, str]:
    ir = IdentityRepository(db)
    if ir.get_user(user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if ir.get_group(body.group_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    existing = db.scalars(
        select(UserGroup).where(
            UserGroup.user_id == user_id,
            UserGroup.group_id == body.group_id,
        )
    ).first()
    if existing is not None:
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.BAD_REQUEST,
            message="User is already in this group",
            detail=None,
        )
    ir.add_user_to_group(user_id, body.group_id)
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="USER_GROUP_ADD",
        permission_id=None,
        detail={"user_id": str(user_id), "group_id": str(body.group_id)},
    )
    return {"status": "ok"}


@router.post("/users/{user_id}/roles", status_code=status.HTTP_201_CREATED)
def add_user_role(
    user_id: uuid.UUID,
    body: AssignRoleBody,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> dict[str, str]:
    ir = IdentityRepository(db)
    if ir.get_user(user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if ir.get_role(body.role_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    ir.add_user_role(user_id, body.role_id)
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="USER_ROLE_ADD",
        permission_id=None,
        detail={"user_id": str(user_id), "role_id": str(body.role_id)},
    )
    return {"status": "ok"}


@router.post("/groups/{group_id}/roles", status_code=status.HTTP_201_CREATED)
def add_group_role(
    group_id: uuid.UUID,
    body: AssignRoleBody,
    db: Session = Depends(get_db),
    changed_by: str = Depends(get_changed_by),
) -> dict[str, str]:
    ir = IdentityRepository(db)
    if ir.get_group(group_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if ir.get_role(body.role_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    ir.add_group_role(group_id, body.role_id)
    record_policy_change(
        db,
        changed_by=changed_by,
        change_type="GROUP_ROLE_ADD",
        permission_id=None,
        detail={"group_id": str(group_id), "role_id": str(body.role_id)},
    )
    return {"status": "ok"}
