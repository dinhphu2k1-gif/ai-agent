"""Per-user per-channel sliding-window rate limit."""

from __future__ import annotations

import time
from collections import defaultdict
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from api.errors import RateLimitedError
from api.settings import get_api_settings
from chat.settings import get_chat_settings

CHAT_API_PREFIX = "/api/v1/chat"
MUTATING_SUFFIX = "/messages"


class _SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_sec: int) -> None:
        self._max = max_requests
        self._window = window_sec
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> int | None:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > self._window:
            bucket.popleft()
        if len(bucket) >= self._max:
            retry_after = max(1, int(self._window - (now - bucket[0])))
            return retry_after
        bucket.append(now)
        return None


_limiter: _SlidingWindowLimiter | None = None


def _get_limiter() -> _SlidingWindowLimiter:
    global _limiter
    settings = get_chat_settings()
    if _limiter is None:
        _limiter = _SlidingWindowLimiter(
            settings.rate_limit_max,
            settings.rate_limit_window_sec,
        )
    return _limiter


def reset_rate_limiter() -> None:
    global _limiter
    _limiter = None


class ChatRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "POST" or not request.url.path.endswith(MUTATING_SUFFIX):
            return await call_next(request)
        if not request.url.path.startswith(CHAT_API_PREFIX):
            return await call_next(request)

        _ = get_api_settings()
        user_id = getattr(request.state, "user_id", "anonymous")
        parts = request.url.path.strip("/").split("/")
        channel_id = parts[-2] if len(parts) >= 2 else "unknown"
        key = f"{user_id}:{channel_id}"

        retry_after = _get_limiter().check(key)
        if retry_after is not None:
            err = RateLimitedError(
                "Too many requests for this channel",
                retry_after_sec=retry_after,
            )
            return JSONResponse(
                status_code=err.status_code,
                content=err.to_detail(),
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
