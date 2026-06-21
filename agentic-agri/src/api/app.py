"""
FastAPI application factory for Chat API (health, CORS, chat REST).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.exception_handlers import register_chat_exception_handlers
from api.middleware.auth import ChatAuthMiddleware
from api.middleware.rate_limit import ChatRateLimitMiddleware
from api.routers.chat import (
    attachments_router,
    channels_router,
    messages_router,
    runs_router,
)
from api.settings import get_api_settings


def _init_sentry(dsn: str | None) -> None:
    if not dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.1)
    except ImportError:
        pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_dotenv()
    settings = get_api_settings()
    _init_sentry(settings.sentry_dsn)
    from universal_agent.supervisor.graph import setup_supervisor_checkpointer

    await setup_supervisor_checkpointer()
    yield


def create_app() -> FastAPI:
    settings = get_api_settings()

    application = FastAPI(
        title="Agentic Agri Chat API",
        version="0.1.0",
        lifespan=lifespan,
    )

    register_chat_exception_handlers(application)

    # Outermost first: CORS → Auth → RateLimit → routes
    application.add_middleware(ChatRateLimitMiddleware)
    application.add_middleware(ChatAuthMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(
        channels_router,
        prefix="/api/v1/chat",
    )
    application.include_router(
        messages_router,
        prefix="/api/v1/chat",
    )
    application.include_router(
        attachments_router,
        prefix="/api/v1/chat",
    )
    application.include_router(
        runs_router,
        prefix="/api/v1/chat",
    )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
