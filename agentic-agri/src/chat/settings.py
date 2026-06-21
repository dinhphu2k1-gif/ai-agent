"""Chat persistence and streaming configuration."""

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


@dataclass(frozen=True)
class ChatSettings:
    database_url: str | None
    use_memory: bool
    persist_sse_events: bool
    redis_url: str | None
    run_timeout_sec: float
    rate_limit_max: int
    rate_limit_window_sec: int
    enforce_channel_acl: bool
    attachment_storage_path: str
    run_events_retention_days: int
    emit_content_delta: bool

    @property
    def use_postgres(self) -> bool:
        return bool(self.database_url) and not self.use_memory


@lru_cache
def get_chat_settings() -> ChatSettings:
    database_url = os.environ.get("CHAT_DATABASE_URL", "").strip() or None
    use_memory = _parse_bool(os.environ.get("CHAT_USE_MEMORY"), default=False)
    if not database_url:
        use_memory = True
    return ChatSettings(
        database_url=database_url,
        use_memory=use_memory,
        persist_sse_events=_parse_bool(
            os.environ.get("CHAT_PERSIST_SSE_EVENTS"), default=False
        ),
        redis_url=os.environ.get("REDIS_URL", "").strip() or None,
        run_timeout_sec=float(os.environ.get("CHAT_RUN_TIMEOUT_SEC", "60")),
        rate_limit_max=int(os.environ.get("CHAT_RATE_LIMIT_MAX", "30")),
        rate_limit_window_sec=int(os.environ.get("CHAT_RATE_LIMIT_WINDOW_SEC", "60")),
        enforce_channel_acl=_parse_bool(
            os.environ.get("CHAT_ENFORCE_CHANNEL_ACL"), default=True
        ),
        attachment_storage_path=os.environ.get(
            "CHAT_ATTACHMENT_STORAGE_PATH", "./data/chat_attachments"
        ).strip(),
        run_events_retention_days=int(
            os.environ.get("CHAT_RUN_EVENTS_RETENTION_DAYS", "7")
        ),
        emit_content_delta=_parse_bool(
            os.environ.get("CHAT_EMIT_CONTENT_DELTA"), default=False
        ),
    )
