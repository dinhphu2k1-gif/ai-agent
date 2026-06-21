from __future__ import annotations

from collections.abc import Generator

from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_session_factory


def get_db() -> Generator[Session, None, None]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def verify_admin_mvp(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    """MVP: optional shared secret; otherwise rely on network policy (epic-03)."""
    expected = settings.admin_api_token
    if expected and x_admin_token != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin API token required",
        )


def get_changed_by(
    x_changed_by: str | None = Header(default=None, alias="X-Changed-By"),
) -> str:
    if x_changed_by and x_changed_by.strip():
        return x_changed_by.strip()[:255]
    return "admin-api"
