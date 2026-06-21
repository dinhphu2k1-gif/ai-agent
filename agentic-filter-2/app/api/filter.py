from __future__ import annotations

import anyio
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.runtime import _user_context_from_bearer
from app.cache.redis_client import UserContextCache
from app.core.config import get_settings
from app.core.errors import ErrorCode, error_response
from app.observability import metrics as runtime_metrics
from app.schemas.runtime import (
    FilterQueryRequest,
    FilterQueryResponse,
    FilterSearchRequest,
    FilterSearchResponse,
)
from app.services.audit_service import record_runtime_access_for_http_error
from app.services.filter_query_service import FilterQueryHttpError, run_filter_query
from app.services.filter_search_service import run_filter_search

router = APIRouter(prefix="/api/v1/filter", tags=["filter"])


def _get_cache(request: Request) -> UserContextCache:
    return request.app.state.user_context_cache


def _audit_bearer_failure(
    db: Session, *, action: str, response: JSONResponse, request_id: str | None
) -> None:
    sc = response.status_code
    if sc >= 400:
        runtime_metrics.inc_runtime_deny()
    code = ErrorCode.UNAUTHORIZED
    if sc == 403:
        code = ErrorCode.FORBIDDEN
    elif sc == 504:
        code = ErrorCode.GATEWAY_TIMEOUT
    elif sc == 502:
        code = ErrorCode.BAD_GATEWAY
    record_runtime_access_for_http_error(
        db,
        user_id=None,
        resource_id=None,
        action=action,
        status_code=sc,
        code=code,
        request_id=request_id,
    )


@router.post("/query", response_model=None)
async def filter_query(
    request: Request,
    body: FilterQueryRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> FilterQueryResponse | JSONResponse:
    rid = getattr(request.state, "request_id", None)
    uc = await _user_context_from_bearer(request, authorization, db)
    if isinstance(uc, JSONResponse):
        _audit_bearer_failure(db, action="POSTGRES_FILTER_QUERY", response=uc, request_id=rid)
        return uc

    executor = getattr(request.app.state, "sql_executor", None)
    if executor is None:
        return error_response(
            status_code=500,
            code=ErrorCode.INTERNAL,
            message="SQL executor not configured",
            detail=None,
        )

    cfg = get_settings()
    cache = _get_cache(request)
    runtime_metrics.inc_runtime_request()

    def _work() -> FilterQueryResponse:
        return run_filter_query(db, uc, cache, cfg, body, executor, request_id=rid)

    try:
        return await anyio.to_thread.run_sync(_work)
    except FilterQueryHttpError as e:
        runtime_metrics.inc_runtime_deny()
        return error_response(
            status_code=e.status_code,
            code=e.code,
            message=e.message,
            detail=None,
        )


@router.post("/search", response_model=None)
async def filter_search(
    request: Request,
    body: FilterSearchRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> FilterSearchResponse | JSONResponse:
    rid = getattr(request.state, "request_id", None)
    uc = await _user_context_from_bearer(request, authorization, db)
    if isinstance(uc, JSONResponse):
        _audit_bearer_failure(db, action="OPENSEARCH_FILTER_SEARCH", response=uc, request_id=rid)
        return uc

    executor = getattr(request.app.state, "opensearch_executor", None)
    if executor is None:
        return error_response(
            status_code=500,
            code=ErrorCode.INTERNAL,
            message="OpenSearch executor not configured",
            detail=None,
        )

    cfg = get_settings()
    cache = _get_cache(request)
    runtime_metrics.inc_runtime_request()

    def _work() -> FilterSearchResponse:
        return run_filter_search(db, uc, cache, cfg, body, executor, request_id=rid)

    try:
        return await anyio.to_thread.run_sync(_work)
    except FilterQueryHttpError as e:
        runtime_metrics.inc_runtime_deny()
        return error_response(
            status_code=e.status_code,
            code=e.code,
            message=e.message,
            detail=None,
        )
