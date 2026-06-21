"""FastAPI exception handlers for Chat API."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.errors import ChatApiError, RateLimitedError

logger = logging.getLogger("chat.api")


def register_chat_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(ChatApiError)
    async def chat_api_error_handler(
        _request: Request, exc: ChatApiError
    ) -> JSONResponse:
        headers: dict[str, str] = {}
        if isinstance(exc, RateLimitedError):
            headers["Retry-After"] = str(exc.retry_after_sec)
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_detail(),
            headers=headers,
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        if request.url.path.endswith("/messages") and request.method == "POST":
            logger.exception(
                "unhandled error on POST messages",
                extra={"chat": {"path": request.url.path}},
            )
        _maybe_capture_sentry(exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "data": None,
            },
        )


def _maybe_capture_sentry(exc: BaseException) -> None:
    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    except ImportError:
        pass
