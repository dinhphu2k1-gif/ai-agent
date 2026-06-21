from __future__ import annotations

import anyio
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.cache.redis_client import UserContextCache
from app.core.config import get_settings
from app.schemas.metadata_contract import (
    MetadataApiResponse,
    MetadataFormatResultsRequest,
    MetadataHybridSearchRequest,
    MetadataKeywordSearchRequest,
    MetadataRelationshipsRequest,
)
from app.services.metadata_service import MetadataHttpError, run_metadata_format_results
from app.services.metadata_service import (
    run_metadata_hybrid_search,
    run_metadata_keyword_search,
    run_metadata_relationships,
    run_metadata_table,
    run_metadata_table_columns,
)
from app.services.user_context_service import (
    TrustedUserContextError,
    build_user_context_from_trusted_user_id,
)

router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])


def _get_cache(request: Request) -> UserContextCache:
    return request.app.state.user_context_cache


def _metadata_error_response(exc: MetadataHttpError | TrustedUserContextError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "data": {},
            },
        },
    )


def _ok(payload: MetadataApiResponse) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content=payload.model_dump(by_alias=True, exclude_none=True),
    )


def _require_opensearch(request: Request) -> JSONResponse | None:
    executor = getattr(request.app.state, "opensearch_executor", None)
    if executor is None:
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "error": {
                    "code": "UPSTREAM_ERROR",
                    "message": "OpenSearch executor not configured",
                    "data": {},
                },
            },
        )
    return None


def _resolve_user(
    request: Request,
    db: Session,
    user_id: str,
):
    cfg = get_settings()
    cache = _get_cache(request)
    try:
        return build_user_context_from_trusted_user_id(db, cache, user_id, cfg)
    except TrustedUserContextError as e:
        raise e


@router.post("/hybrid-search", response_model=None)
async def metadata_hybrid_search(
    request: Request,
    body: MetadataHybridSearchRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    missing = _require_opensearch(request)
    if missing is not None:
        return missing
    try:
        uc = _resolve_user(request, db, body.user_id)
    except TrustedUserContextError as e:
        return _metadata_error_response(e)

    cfg = get_settings()
    cache = _get_cache(request)
    executor = request.app.state.opensearch_executor

    embedder = getattr(request.app.state, "metadata_embedder", None)

    def _work() -> MetadataApiResponse:
        return run_metadata_hybrid_search(
            db, uc, cache, cfg, body, executor, embedder
        )

    try:
        return _ok(await anyio.to_thread.run_sync(_work))
    except MetadataHttpError as e:
        return _metadata_error_response(e)


@router.post("/keyword-search", response_model=None)
async def metadata_keyword_search(
    request: Request,
    body: MetadataKeywordSearchRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    missing = _require_opensearch(request)
    if missing is not None:
        return missing
    try:
        uc = _resolve_user(request, db, body.user_id)
    except TrustedUserContextError as e:
        return _metadata_error_response(e)

    cfg = get_settings()
    cache = _get_cache(request)
    executor = request.app.state.opensearch_executor

    def _work() -> MetadataApiResponse:
        return run_metadata_keyword_search(db, uc, cache, cfg, body, executor)

    try:
        return _ok(await anyio.to_thread.run_sync(_work))
    except MetadataHttpError as e:
        return _metadata_error_response(e)


@router.get("/tables/{table_name}", response_model=None)
async def metadata_table(
    request: Request,
    table_name: str,
    user_id: str = Query(..., alias="userId"),
    thread_id: str | None = Query(default=None, alias="threadId"),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> JSONResponse:
    _ = thread_id
    missing = _require_opensearch(request)
    if missing is not None:
        return missing
    try:
        uc = _resolve_user(request, db, user_id)
    except TrustedUserContextError as e:
        return _metadata_error_response(e)

    cfg = get_settings()
    cache = _get_cache(request)
    executor = request.app.state.opensearch_executor

    def _work() -> MetadataApiResponse:
        return run_metadata_table(
            db, uc, cache, cfg, table_name, size=size, executor=executor
        )

    try:
        return _ok(await anyio.to_thread.run_sync(_work))
    except MetadataHttpError as e:
        return _metadata_error_response(e)


@router.get("/tables/{table_name}/columns", response_model=None)
async def metadata_table_columns(
    request: Request,
    table_name: str,
    user_id: str = Query(..., alias="userId"),
    thread_id: str | None = Query(default=None, alias="threadId"),
    size: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> JSONResponse:
    _ = thread_id
    missing = _require_opensearch(request)
    if missing is not None:
        return missing
    try:
        uc = _resolve_user(request, db, user_id)
    except TrustedUserContextError as e:
        return _metadata_error_response(e)

    cfg = get_settings()
    cache = _get_cache(request)
    executor = request.app.state.opensearch_executor

    def _work() -> MetadataApiResponse:
        return run_metadata_table_columns(
            db, uc, cache, cfg, table_name, size=size, executor=executor
        )

    try:
        return _ok(await anyio.to_thread.run_sync(_work))
    except MetadataHttpError as e:
        return _metadata_error_response(e)


@router.post("/relationships", response_model=None)
async def metadata_relationships(
    request: Request,
    body: MetadataRelationshipsRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    missing = _require_opensearch(request)
    if missing is not None:
        return missing
    try:
        uc = _resolve_user(request, db, body.user_id)
    except TrustedUserContextError as e:
        return _metadata_error_response(e)

    cfg = get_settings()
    cache = _get_cache(request)
    executor = request.app.state.opensearch_executor

    def _work() -> MetadataApiResponse:
        return run_metadata_relationships(db, uc, cache, cfg, body, executor)

    try:
        return _ok(await anyio.to_thread.run_sync(_work))
    except MetadataHttpError as e:
        return _metadata_error_response(e)


@router.post("/format-results", response_model=None)
async def metadata_format_results(
    body: MetadataFormatResultsRequest,
) -> JSONResponse:
    return _ok(run_metadata_format_results(body))
