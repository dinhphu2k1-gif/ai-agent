"""
HTTP client for filter-service SQL execution API (/api/v1/sql/*).
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from ..config import FILTER_SERVICE_BASE_URL, SQL_EXECUTION_TIMEOUT_SEC
from .db_executor_client import ExecutionResult
from .sql_normalize import prepare_sql_for_filter_service


class FilterServiceSqlError(Exception):
    """Raised when filter-service SQL API returns an error."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "UPSTREAM_ERROR",
        status_code: int | None = None,
        repairable: bool = True,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message
        self.repairable = repairable


_NON_REPAIRABLE_CODES = frozenset({"FORBIDDEN", "POLICY_VIOLATION"})


class FilterServiceSqlClient:
    """Execute SQL via filter-service with permission check, row filter, and masking."""

    _API_PREFIX = "/api/v1/sql"

    def __init__(
        self,
        user_id: str,
        thread_id: str | None = None,
        *,
        base_url: str | None = None,
        timeout_sec: float | None = None,
    ) -> None:
        self._user_id = user_id
        self._thread_id = thread_id
        self._base_url = (base_url or FILTER_SERVICE_BASE_URL or "").rstrip("/")
        self._timeout = (
            timeout_sec if timeout_sec is not None else SQL_EXECUTION_TIMEOUT_SEC
        )
        if not self._base_url:
            raise ValueError("FILTER_SERVICE_BASE_URL is required for FilterServiceSqlClient")

    @property
    def dialect(self) -> str:
        return "postgresql"

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Request-Id": str(uuid.uuid4()),
        }

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{self._API_PREFIX}{path}"
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=body, headers=self._headers())

        if response.status_code >= 400:
            payload = {}
            try:
                payload = response.json()
            except Exception:
                pass
            err = payload.get("error") if isinstance(payload, dict) else None
            code = "UPSTREAM_ERROR"
            message = response.text or f"HTTP {response.status_code}"
            if isinstance(err, dict):
                code = str(err.get("code") or code)
                message = str(err.get("message") or message)
            raise FilterServiceSqlError(
                message,
                code=code,
                status_code=response.status_code,
                repairable=code not in _NON_REPAIRABLE_CODES
                and response.status_code not in {403},
            )

        payload = response.json()
        if not isinstance(payload, dict):
            raise FilterServiceSqlError("Invalid JSON response from filter-service")

        if not payload.get("success", False):
            err = payload.get("error") or {}
            code = str(err.get("code") or "EXECUTION_ERROR")
            message = str(err.get("message") or "SQL execution failed")
            raise FilterServiceSqlError(
                message,
                code=code,
                status_code=response.status_code,
                repairable=code not in _NON_REPAIRABLE_CODES,
            )

        data = payload.get("data")
        if not isinstance(data, dict):
            raise FilterServiceSqlError("Missing data in filter-service response")
        return data

    def execute_query(
        self,
        sql_text: str,
        query_scope: dict[str, Any],
        limit: int = 100,
        *,
        dialect: str = "postgresql",
    ) -> ExecutionResult:
        if not query_scope or not query_scope.get("tables"):
            return ExecutionResult(
                success=False,
                dialect=dialect,
                sql_text=sql_text,
                columns=[],
                rows=[],
                row_count=0,
                error_message="queryScope.tables is required for filter-service SQL execution",
                error_code="VALIDATION_ERROR",
                repairable=False,
            )

        body: dict[str, Any] = {
            "userId": self._user_id,
            "sql": prepare_sql_for_filter_service(sql_text),
            "dialect": dialect,
            "limit": limit,
            "queryScope": query_scope,
            "options": {
                "applyRowFilter": True,
                "applyColumnMasking": True,
                "allowRewrite": True,
                "strictScopeMatch": True,
            },
        }
        if self._thread_id:
            body["threadId"] = self._thread_id

        try:
            data = self._post("/execute", body)
        except FilterServiceSqlError as exc:
            return ExecutionResult(
                success=False,
                dialect=dialect,
                sql_text=sql_text,
                columns=[],
                rows=[],
                row_count=0,
                error_message=exc.message,
                error_code=exc.code,
                repairable=exc.repairable,
            )

        columns = [str(c) for c in data.get("columns") or []]
        raw_rows = data.get("rows") or []
        rows = [list(row) for row in raw_rows]
        executed_sql = str(data.get("executedSql") or sql_text)
        row_count = int(data.get("rowCount") if data.get("rowCount") is not None else len(rows))

        return ExecutionResult(
            success=True,
            dialect=dialect,
            sql_text=executed_sql,
            columns=columns,
            rows=rows,
            row_count=row_count,
            repairable=True,
        )
