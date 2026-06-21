from __future__ import annotations

import anyio
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.cache.redis_client import UserContextCache
from app.core.config import get_settings
from app.schemas.sql_contract import SqlExecuteRequest, SqlExecuteResponse
from app.services.sql_execute_service import SqlExecuteHttpError, run_sql_execute
from app.services.user_context_service import (
    TrustedUserContextError,
    build_user_context_from_trusted_user_id,
)

router = APIRouter(prefix="/api/v1/sql", tags=["sql"])


def _get_cache(request: Request) -> UserContextCache:
    return request.app.state.user_context_cache


def _ok(payload: SqlExecuteResponse) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content=payload.model_dump(by_alias=True, exclude_none=True),
    )


def _error(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
    sql_state: str | None = None,
    dialect: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "sqlState": sql_state,
                "dialect": dialect,
            },
        },
    )


def _require_sql_executor(request: Request) -> JSONResponse | None:
    ex = getattr(request.app.state, "sql_executor", None)
    if ex is None:
        return _error(
            status_code=500,
            code="INTERNAL_ERROR",
            message="SQL executor not configured",
        )
    return None


def _resolve_user(request: Request, db: Session, user_id: str):
    cfg = get_settings()
    cache = _get_cache(request)
    return build_user_context_from_trusted_user_id(db, cache, user_id, cfg)


@router.post("/execute", response_model=None)
async def sql_execute(
    request: Request,
    body: SqlExecuteRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    missing = _require_sql_executor(request)
    if missing is not None:
        return missing

    cfg = get_settings()
    cache = _get_cache(request)
    executor = request.app.state.sql_executor

    try:
        uc = _resolve_user(request, db, body.user_id)
    except TrustedUserContextError as e:
        return _error(status_code=e.status_code, code=e.code, message=e.message)

    def _work() -> SqlExecuteResponse:
        return run_sql_execute(db, uc, cache, cfg, body, executor)

    try:
        return _ok(await anyio.to_thread.run_sync(_work))
    except SqlExecuteHttpError as e:
        return _error(
            status_code=e.status_code,
            code=e.code,
            message=e.message,
            details=e.details,
            sql_state=e.sql_state,
            dialect=e.dialect,
        )

