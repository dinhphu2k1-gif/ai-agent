from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db, verify_admin_mvp
from app.repositories.audit_repo import AuditRepository
from app.schemas.admin import AccessLogOut, PermissionChangeLogOut

router = APIRouter(
    prefix="/api/v1/admin/audit",
    tags=["admin-audit"],
    dependencies=[Depends(verify_admin_mvp)],
)


@router.get("/access-logs", response_model=list[AccessLogOut])
def list_access_logs(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[AccessLogOut]:
    rows = AuditRepository(db).list_access_logs(limit=limit, offset=offset)
    return [AccessLogOut.model_validate(r) for r in rows]


@router.get("/permission-change-logs", response_model=list[PermissionChangeLogOut])
def list_permission_change_logs(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[PermissionChangeLogOut]:
    rows = AuditRepository(db).list_permission_change_logs(limit=limit, offset=offset)
    return [PermissionChangeLogOut.model_validate(r) for r in rows]
