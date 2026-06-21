"""Structured logging helpers for chat orchestration."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("chat.api")


def log_chat_event(
    event: str,
    *,
    run_id: str | None = None,
    channel_id: str | None = None,
    user_id: str | None = None,
    thread_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {"event": event}
    if run_id:
        payload["run_id"] = run_id
    if channel_id:
        payload["channel_id"] = channel_id
    if user_id:
        payload["user_id"] = user_id
    if thread_id:
        payload["thread_id"] = thread_id
    if extra:
        payload.update(extra)
    logger.info("chat %s", event, extra={"chat": payload})
