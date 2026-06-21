from __future__ import annotations

from typing import Protocol, runtime_checkable

import redis

from app.core.config import Settings


@runtime_checkable
class UserContextCache(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def setex(self, key: str, ttl_seconds: int, value: bytes) -> None: ...
    def delete(self, key: str) -> None: ...
    def close(self) -> None: ...


class MemoryUserContextCache:
    """Process-local cache (tests / environments without Redis)."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    def get(self, key: str) -> bytes | None:
        return self._data.get(key)

    def setex(self, key: str, ttl_seconds: int, value: bytes) -> None:
        _ = ttl_seconds
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def close(self) -> None:
        self._data.clear()


class RedisUserContextCache:
    def __init__(self, url: str) -> None:
        self._r = redis.Redis.from_url(
            url,
            decode_responses=False,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )

    def get(self, key: str) -> bytes | None:
        raw = self._r.get(key)
        if raw is None:
            return None
        if isinstance(raw, memoryview):
            return raw.tobytes()
        if isinstance(raw, bytes):
            return raw
        return str(raw).encode()

    def setex(self, key: str, ttl_seconds: int, value: bytes) -> None:
        self._r.setex(key, ttl_seconds, value)

    def delete(self, key: str) -> None:
        self._r.delete(key)

    def close(self) -> None:
        self._r.close()


def create_user_context_cache(settings: Settings) -> UserContextCache:
    if settings.user_context_cache_backend == "memory":
        return MemoryUserContextCache()
    return RedisUserContextCache(settings.redis_url)
