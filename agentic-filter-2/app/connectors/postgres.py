from __future__ import annotations

import time
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, OperationalError


class PostgresSqlExecutor:
    """Read-only SELECT executor (§3.6): only pre-authorized SQL from rewriter."""

    def __init__(self, url: str, *, pool_size: int = 5, query_timeout_seconds: float = 30.0) -> None:
        self._engine: Engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=pool_size,
        )
        self._query_timeout_seconds = query_timeout_seconds

    def dispose(self) -> None:
        self._engine.dispose()

    def execute_select(
        self, sql: str, parameters: dict[str, Any] | None = None
    ) -> tuple[list[str], list[dict[str, Any]]]:
        params = parameters or {}
        stmt = text(sql)
        if params:
            stmt = stmt.bindparams(**params)
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                with self._engine.connect() as conn:
                    res = conn.execution_options(
                        timeout=self._query_timeout_seconds
                    ).execute(stmt)
                    keys = list(res.keys())
                    rows_raw = res.fetchall()
                    rows = [dict(zip(keys, row)) for row in rows_raw]
                    return keys, rows
            except OperationalError as e:
                last_err = e
                time.sleep(0.05 * (attempt + 1))
                continue
            except DBAPIError as e:
                if getattr(e.orig, "__class__", type).__name__ in (
                    "OperationalError",
                    "TransientError",
                ):
                    last_err = e
                    time.sleep(0.05 * (attempt + 1))
                    continue
                raise
        if last_err:
            raise last_err
        raise RuntimeError("execute_select failed")
