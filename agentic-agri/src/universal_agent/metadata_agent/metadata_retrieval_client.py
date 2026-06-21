"""
Factory for metadata retrieval: filter-service (HTTP) or direct OpenSearch.
"""

from __future__ import annotations

import os
from typing import Any

from .filter_service_client import FilterServiceClient
from .opensearch_client import OpenSearchClient


DEFAULT_METADATA_USER_ID = "dev-user"
# Placeholder IDs from chat auth / LangGraph when auth is off — not real filter-service users.
_PLACEHOLDER_USER_IDS = frozenset({DEFAULT_METADATA_USER_ID, "anonymous"})


def _is_placeholder_user_id(user_id: str | None) -> bool:
    if not user_id:
        return True
    return user_id.strip() in _PLACEHOLDER_USER_IDS


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_metadata_user_context(
    state: dict | None = None,
    config: Any | None = None,
) -> tuple[str, str | None]:
    """
    Resolve userId / threadId for metadata calls.

    Priority: state → LangGraph configurable → METADATA_TEST_USER_ID env → dev-user.
    Placeholder IDs (dev-user, anonymous) are ignored so METADATA_TEST_USER_ID works in dev.
    """
    user_id: str | None = None
    thread_id: str | None = None

    if state:
        user_id = state.get("user_id") or None
        thread_id = state.get("thread_id") or None

    if config:
        configurable = config.get("configurable") or {}
        user_id = user_id or configurable.get("user_id")
        thread_id = thread_id or configurable.get("thread_id")

    if _is_placeholder_user_id(user_id):
        user_id = None

    test_user = os.environ.get("METADATA_TEST_USER_ID", "").strip()
    if not user_id and test_user:
        user_id = test_user

    if not user_id:
        user_id = DEFAULT_METADATA_USER_ID

    return str(user_id), thread_id


def create_metadata_retrieval_client(
    user_id: str | None = None,
    thread_id: str | None = None,
):
    """
    Return FilterServiceClient when enabled, else OpenSearchClient (direct dev fallback).
    """
    uid = user_id
    if _is_placeholder_user_id(uid):
        uid = None
    uid = uid or os.environ.get("METADATA_TEST_USER_ID", "").strip() or DEFAULT_METADATA_USER_ID
    use_filter = _env_bool("METADATA_USE_FILTER_SERVICE", False)
    base_url = os.environ.get("FILTER_SERVICE_BASE_URL", "").strip() or None
    if use_filter and base_url:
        print(
            f"🔐 [Metadata] Using filter-service at {base_url} userId={uid}"
            + (f" threadId={thread_id}" if thread_id else "")
        )
        return FilterServiceClient(uid, thread_id, base_url=base_url)
    return OpenSearchClient()
