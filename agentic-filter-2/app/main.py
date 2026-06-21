from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json
import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError

from app.api.admin_assignments import router as admin_assignments_router
from app.api.admin_audit import router as admin_audit_router
from app.api.admin_permissions import router as admin_permissions_router
from app.api.admin_resources import router as admin_resources_router
from app.api.admin_groups import router as admin_groups_router
from app.api.admin_permission_wizard import router as admin_permission_wizard_router
from app.api.admin_shared import router as admin_shared_router
from app.api.admin_roles import router as admin_roles_router
from app.api.admin_users import router as admin_users_router
from app.api.filter import router as filter_router
from app.api.metadata import router as metadata_router
from app.api.sql import router as sql_router
from app.api.health import router as health_router
from app.api.runtime import router as runtime_router
from app.cache.redis_client import create_user_context_cache
from app.connectors.opensearch import OpenSearchExecutor
from app.connectors.postgres import PostgresSqlExecutor
from app.services.metadata_embedding import MetadataEmbeddingService
from app.core.config import get_settings, settings
from app.core.errors import ErrorCode, error_response
from app.core.logging import configure_logging
from app.db import configure_engine, dispose_engine
from app.iam.client import IamHttpClient

logger = logging.getLogger(__name__)


def _runtime_target_label(cfg) -> str:  # noqa: ANN001
    explicit = (cfg.runtime_postgres_url or "").strip()
    if explicit:
        return "RUNTIME_POSTGRES_URL"
    if (cfg.pg_database or "").strip() and (cfg.pg_user or "").strip():
        return f"PG_* → {cfg.pg_host}:{cfg.pg_port}/{cfg.pg_database}"
    return "DATABASE_URL (same as catalog)"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    cfg = get_settings()
    if cfg.auth_bypass_enabled:
        logger.warning(
            "AUTH_BYPASS_ENABLED is on: runtime/filter Bearer tokens skip IAM "
            "(user_id=%s). Do not use in production.",
            cfg.auth_bypass_user_id,
        )
    configure_engine(cfg.database_url)
    app.state.iam_client = IamHttpClient(cfg)
    app.state.user_context_cache = create_user_context_cache(cfg)
    runtime_url = cfg.effective_runtime_postgres_url
    logger.info(
        "Runtime SQL executor: %s (catalog/permissions use DATABASE_URL)",
        _runtime_target_label(cfg),
    )
    app.state.sql_executor = PostgresSqlExecutor(
        runtime_url,
        query_timeout_seconds=cfg.runtime_query_timeout_seconds,
    )
    app.state.opensearch_executor = None
    app.state.metadata_embedder = None
    os_base = cfg.opensearch_effective_base_url
    if os_base:
        app.state.opensearch_executor = OpenSearchExecutor(
            os_base,
            timeout_seconds=cfg.opensearch_timeout_seconds,
            auth=cfg.opensearch_auth,
            verify=cfg.opensearch_verify_certs,
        )
        if cfg.metadata_hybrid_enabled:
            app.state.metadata_embedder = MetadataEmbeddingService(cfg)
    yield
    app.state.sql_executor.dispose()
    ex_os = getattr(app.state, "opensearch_executor", None)
    if ex_os is not None:
        ex_os.close()
    dispose_engine()
    app.state.iam_client.close()
    app.state.user_context_cache.close()


def _parse_cors_origins(raw: str) -> list[str]:
    trimmed = raw.strip()
    if trimmed == "*":
        return ["*"]
    return [o.strip() for o in trimmed.split(",") if o.strip()]


def create_app() -> FastAPI:
    application = FastAPI(
        title="Filter Service",
        lifespan=lifespan,
    )
    cfg = get_settings()
    cors_origins = _parse_cors_origins(cfg.cors_allowed_origins)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(IntegrityError)
    async def _integrity_error_handler(  # type: ignore[no-untyped-def]
        _request: Request, _exc: IntegrityError
    ):
        return error_response(
            status_code=400,
            code=ErrorCode.BAD_REQUEST,
            message="Request could not be applied (constraint violation)",
            detail=None,
        )

    @application.exception_handler(RequestValidationError)
    async def _validation_error_handler(  # type: ignore[no-untyped-def]
        _request: Request, _exc: RequestValidationError
    ):
        return error_response(
            status_code=400,
            code=ErrorCode.BAD_REQUEST,
            message="Invalid request body",
            detail=None,
        )

    @application.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = rid
        # #region agent log
        if request.method == "OPTIONS":
            try:
                with open("debug-a234d2.log", "a", encoding="utf-8") as _df:
                    _df.write(
                        json.dumps(
                            {
                                "sessionId": "a234d2",
                                "hypothesisId": "H1",
                                "location": "app/main.py:request_id_middleware",
                                "message": "preflight OPTIONS received",
                                "data": {
                                    "path": request.url.path,
                                    "origin": request.headers.get("origin"),
                                    "access_control_request_method": request.headers.get(
                                        "access-control-request-method"
                                    ),
                                    "cors_origins_configured": cors_origins,
                                },
                                "timestamp": int(time.time() * 1000),
                            }
                        )
                        + "\n"
                    )
            except OSError:
                pass
        # #endregion
        response: Response = await call_next(request)
        # #region agent log
        if request.method == "OPTIONS":
            try:
                with open("debug-a234d2.log", "a", encoding="utf-8") as _df:
                    _df.write(
                        json.dumps(
                            {
                                "sessionId": "a234d2",
                                "hypothesisId": "H1",
                                "location": "app/main.py:request_id_middleware",
                                "message": "preflight OPTIONS response",
                                "data": {
                                    "path": request.url.path,
                                    "status_code": response.status_code,
                                    "acao": response.headers.get(
                                        "access-control-allow-origin"
                                    ),
                                },
                                "timestamp": int(time.time() * 1000),
                            }
                        )
                        + "\n"
                    )
            except OSError:
                pass
        # #endregion
        response.headers["X-Request-ID"] = rid
        return response

    application.include_router(health_router)
    application.include_router(runtime_router)
    application.include_router(filter_router)
    application.include_router(metadata_router)
    application.include_router(sql_router)
    application.include_router(admin_resources_router)
    application.include_router(admin_permissions_router)
    application.include_router(admin_assignments_router)
    application.include_router(admin_audit_router)
    application.include_router(admin_users_router)
    application.include_router(admin_roles_router)
    application.include_router(admin_groups_router)
    application.include_router(admin_shared_router)
    application.include_router(admin_permission_wizard_router)
    return application


app = create_app()

__all__ = ["app", "create_app", "settings"]
