"""
HTTP API configuration — single source for Chat API server settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_cors_origins(value: str | None) -> list[str]:
    if not value or not value.strip():
        return ["http://localhost:5173"]
    return [origin.strip() for origin in value.split(",") if origin.strip()]


@dataclass(frozen=True)
class ApiSettings:
    host: str
    port: int
    cors_origins: list[str]
    require_auth: bool
    jwt_secret: str | None
    jwt_algorithm: str
    sentry_dsn: str | None
    allow_test_user_header: bool


@lru_cache
def get_api_settings() -> ApiSettings:
    return ApiSettings(
        host=os.environ.get("API_HOST", "0.0.0.0"),
        port=int(os.environ.get("API_PORT", "8080")),
        cors_origins=_parse_cors_origins(os.environ.get("API_CORS_ORIGINS")),
        require_auth=_parse_bool(os.environ.get("CHAT_REQUIRE_AUTH"), default=False),
        jwt_secret=os.environ.get("CHAT_JWT_SECRET", "").strip() or None,
        jwt_algorithm=os.environ.get("CHAT_JWT_ALGORITHM", "HS256"),
        sentry_dsn=os.environ.get("SENTRY_DSN", "").strip() or None,
        allow_test_user_header=_parse_bool(
            os.environ.get("API_ALLOW_TEST_USER_HEADER"), default=False
        ),
    )
