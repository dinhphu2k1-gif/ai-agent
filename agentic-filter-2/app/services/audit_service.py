"""Audit persistence: policy changes (Epic 3) + runtime access (Epic 8 §3.8)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.cache.invalidation import bump_permission_version
from app.core.errors import ErrorCode
from app.repositories.audit_repo import AuditRepository

_logger = logging.getLogger("app.runtime_audit")


def record_policy_change(
    session: Session,
    *,
    changed_by: str,
    change_type: str,
    permission_id: uuid.UUID | None = None,
    detail: dict | None = None,
) -> None:
    """Append PERMISSION_CHANGE_LOG and bump permission version (MVP §10)."""
    AuditRepository(session).create_permission_change_log(
        permission_id=permission_id,
        changed_by=changed_by,
        change_type=change_type,
        detail=detail,
    )
    bump_permission_version()


def record_runtime_access(
    session: Session,
    *,
    user_id: uuid.UUID | None,
    resource_id: uuid.UUID | None,
    action: str,
    result: str,
    decision: str | None = None,
    request_id: str | None = None,
) -> None:
    """
    Persist ACCESS_LOG. Do not pass tokens, raw SQL, or row payloads (§12).
    """
    AuditRepository(session).create_access_log(
        user_id=user_id,
        resource_id=resource_id,
        action=action,
        result=result,
        decision=decision,
        request_id=request_id,
    )
    _logger.info(
        "runtime_access",
        extra={
            "audit_action": action,
            "audit_result": result,
            "audit_decision": decision or "",
            "request_id": request_id or "",
            "user_id": str(user_id) if user_id else "",
            "resource_id": str(resource_id) if resource_id else "",
        },
    )


def record_runtime_access_for_http_error(
    session: Session,
    *,
    user_id: uuid.UUID | None,
    resource_id: uuid.UUID | None,
    action: str,
    status_code: int,
    code: ErrorCode,
    request_id: str | None = None,
) -> None:
    if status_code == 403:
        result = "deny"
    elif status_code in (502, 504, 500):
        result = "error"
    else:
        result = "reject"
    record_runtime_access(
        session,
        user_id=user_id,
        resource_id=resource_id,
        action=action,
        result=result,
        decision=code.value,
        request_id=request_id,
    )
