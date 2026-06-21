"""
Factory for SQL execution: filter-service (HTTP) or direct PostgreSQL (dev fallback).
"""

from __future__ import annotations

import os
from typing import Any, Protocol

from ..config import FILTER_SERVICE_BASE_URL
from ..metadata_agent.metadata_retrieval_client import resolve_metadata_user_context
from .db_executor_client import DBExecutorClient, PostgresExecutorClient, create_db_executor
from .filter_service_sql_client import FilterServiceSqlClient


class SqlExecutionClient(Protocol):
    dialect: str

    def execute_query(
        self,
        sql_text: str,
        query_scope: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> Any: ...


class _PostgresWrapper:
    """Wrap direct Postgres executor to match filter-service client signature."""

    def __init__(self, inner: DBExecutorClient) -> None:
        self._inner = inner

    @property
    def dialect(self) -> str:
        return self._inner.dialect

    def execute_query(
        self,
        sql_text: str,
        query_scope: dict[str, Any] | None = None,
        limit: int = 100,
    ):
        return self._inner.execute_query(sql_text, limit=limit)


def create_sql_execution_client(
    user_id: str | None = None,
    thread_id: str | None = None,
    *,
    state: dict | None = None,
    config: Any | None = None,
) -> SqlExecutionClient:
    """
    Return FilterServiceSqlClient when SQL_USE_FILTER_SERVICE=true and base URL set,
    else PostgresExecutorClient (local dev).
    """
    uid, tid = resolve_metadata_user_context(state, config)
    if user_id and user_id.strip() not in {"", "dev-user", "anonymous"}:
        uid = user_id
    if thread_id:
        tid = thread_id

    use_filter = os.environ.get("SQL_USE_FILTER_SERVICE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    base_url = (
        os.environ.get("FILTER_SERVICE_BASE_URL", "").strip()
        or FILTER_SERVICE_BASE_URL
        or ""
    )
    if use_filter and base_url:
        print(
            f"🔐 [SQL] Using filter-service at {base_url} userId={uid}"
            + (f" threadId={tid}" if tid else "")
        )
        return FilterServiceSqlClient(uid, tid, base_url=base_url)

    return _PostgresWrapper(create_db_executor())
