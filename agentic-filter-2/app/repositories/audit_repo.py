from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AccessLog, PermissionChangeLog


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_access_log(
        self,
        *,
        user_id: uuid.UUID | None,
        resource_id: uuid.UUID | None,
        action: str,
        result: str,
        decision: str | None = None,
        request_id: str | None = None,
    ) -> AccessLog:
        row = AccessLog(
            user_id=user_id,
            resource_id=resource_id,
            action=action,
            result=result,
            decision=decision,
            request_id=request_id,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get_access_log(self, log_id: uuid.UUID) -> AccessLog | None:
        return self._session.get(AccessLog, log_id)

    def create_permission_change_log(
        self,
        *,
        permission_id: uuid.UUID | None,
        changed_by: str,
        change_type: str,
        detail: dict | None = None,
    ) -> PermissionChangeLog:
        row = PermissionChangeLog(
            permission_id=permission_id,
            changed_by=changed_by,
            change_type=change_type,
            detail=detail,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get_permission_change_log(self, log_id: uuid.UUID) -> PermissionChangeLog | None:
        return self._session.get(PermissionChangeLog, log_id)

    def list_access_logs(self, *, limit: int = 100, offset: int = 0) -> list[AccessLog]:
        return list(
            self._session.scalars(
                select(AccessLog)
                .order_by(AccessLog.accessed_at.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )

    def list_permission_change_logs(
        self, *, limit: int = 100, offset: int = 0
    ) -> list[PermissionChangeLog]:
        return list(
            self._session.scalars(
                select(PermissionChangeLog)
                .order_by(PermissionChangeLog.changed_at.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )
