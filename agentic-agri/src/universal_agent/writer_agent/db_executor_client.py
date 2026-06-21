import os
import re
from dataclasses import dataclass
from typing import Any

import psycopg2
from dotenv import load_dotenv

from universal_agent.utils import strip_markdown_json

load_dotenv()


@dataclass
class ExecutionResult:
    success: bool
    dialect: str
    sql_text: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    error_message: str | None = None
    error_code: str | None = None
    repairable: bool = True


class DBExecutorClient:
    def execute_query(self, sql_text: str, limit: int = 100) -> ExecutionResult:
        raise NotImplementedError

    def validate_connection(self) -> None:
        raise NotImplementedError

    @property
    def dialect(self) -> str:
        raise NotImplementedError


class PostgresExecutorClient(DBExecutorClient):
    def __init__(self):
        self._config = {
            "host": os.environ.get("PG_HOST", "localhost"),
            "port": int(os.environ.get("PG_PORT", 5432)),
            "user": os.environ.get("PG_USER", "postgres"),
            "password": os.environ.get("PG_PASSWORD", "postgres"),
            "database": os.environ.get("PG_DATABASE", "core_banking"),
        }

    @property
    def dialect(self) -> str:
        return "postgresql"

    def _normalize_sql(self, sql_text: str, limit: int) -> str:
        normalized = sql_text.strip()
        fenced_match = re.match(
            r"^```[a-zA-Z0-9_-]*\s*\n(?P<body>[\s\S]*?)\n```$",
            normalized,
        )
        if fenced_match:
            normalized = fenced_match.group("body").strip()
        else:
            normalized = strip_markdown_json(normalized).strip()

        normalized = re.sub(r"^(sql|postgresql|oracle)\s*\n", "", normalized, flags=re.IGNORECASE)
        normalized = normalized.strip().rstrip(";").strip()

        if ";" in normalized:
            raise ValueError("Chỉ cho phép một câu SQL duy nhất.")
        if not re.match(r"^SELECT\b", normalized, re.IGNORECASE):
            raise ValueError("Chỉ cho phép truy vấn SELECT trong giai đoạn này.")

        fetch_first_match = re.search(
            r"FETCH\s+FIRST\s+(\d+)\s+ROWS\s+ONLY$",
            normalized,
            re.IGNORECASE,
        )
        if fetch_first_match:
            row_limit = fetch_first_match.group(1)
            normalized = re.sub(
                r"FETCH\s+FIRST\s+\d+\s+ROWS\s+ONLY$",
                f"LIMIT {row_limit}",
                normalized,
                flags=re.IGNORECASE,
            )

        if not re.search(r"\bLIMIT\b", normalized, re.IGNORECASE):
            normalized = f"{normalized}\nLIMIT {limit}"
        return normalized

    def validate_connection(self) -> None:
        with psycopg2.connect(**self._config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

    def execute_query(self, sql_text: str, limit: int = 100) -> ExecutionResult:
        try:
            normalized_sql = self._normalize_sql(sql_text, limit)
        except Exception as exc:
            return ExecutionResult(
                success=False,
                dialect=self.dialect,
                sql_text=sql_text,
                columns=[],
                rows=[],
                row_count=0,
                error_message=str(exc),
                error_code=type(exc).__name__,
            )

        try:
            with psycopg2.connect(**self._config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(normalized_sql)
                    fetched_rows = cursor.fetchall()
                    columns = [description[0] for description in cursor.description or []]
            return ExecutionResult(
                success=True,
                dialect=self.dialect,
                sql_text=normalized_sql,
                columns=columns,
                rows=[list(row) for row in fetched_rows],
                row_count=len(fetched_rows),
            )
        except psycopg2.Error as exc:
            return ExecutionResult(
                success=False,
                dialect=self.dialect,
                sql_text=normalized_sql,
                columns=[],
                rows=[],
                row_count=0,
                error_message=str(exc).strip(),
                error_code=getattr(exc, "pgcode", None),
            )


class OracleExecutorClient(DBExecutorClient):
    @property
    def dialect(self) -> str:
        return "oracle"

    def validate_connection(self) -> None:
        raise NotImplementedError("Oracle executor chưa được triển khai.")

    def execute_query(self, sql_text: str, limit: int = 100) -> ExecutionResult:
        return ExecutionResult(
            success=False,
            dialect=self.dialect,
            sql_text=sql_text,
            columns=[],
            rows=[],
            row_count=0,
            error_message="Oracle executor chưa được triển khai.",
            error_code="NotImplemented",
        )


def create_db_executor() -> DBExecutorClient:
    dialect = os.environ.get("SQL_EXECUTOR_DIALECT", "postgresql").lower().strip()
    if dialect == "oracle":
        return OracleExecutorClient()
    return PostgresExecutorClient()
