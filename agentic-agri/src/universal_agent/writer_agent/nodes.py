"""
Nodes cho Writer Agent Sub-Graph.
"""

from __future__ import annotations

import os

from langchain_core.runnables import RunnableConfig

from ..models import sql_writer_llm
from ..utils import get_text_content
from .prompts import SQL_WRITER_GENERATION_PROMPT, SQL_WRITER_REPAIR_PROMPT
from .sql_execution_client import create_sql_execution_client
from .query_scope import narrow_query_scope_to_sql, resolve_query_scope
from .state import WriterState

MAX_SQL_REPAIR_ATTEMPTS = int(os.environ.get("MAX_SQL_REPAIR_ATTEMPTS", "2"))


def _resolve_dialect() -> str:
    return os.environ.get("SQL_EXECUTOR_DIALECT", "postgresql").lower().strip()


def _build_generation_prompt(state: WriterState, metadata: str, dialect: str) -> str:
    return SQL_WRITER_GENERATION_PROMPT.format(
        user_input=state.get("user_input", ""),
        metadata=metadata,
        db_dialect=dialect,
    )


def _build_repair_prompt(
    state: WriterState,
    metadata: str,
    dialect: str,
    generated_sql: str,
    execution_error: str,
) -> str:
    return SQL_WRITER_REPAIR_PROMPT.format(
        user_input=state.get("user_input", ""),
        metadata=metadata,
        db_dialect=dialect,
        generated_sql=generated_sql,
        execution_error=execution_error,
    )


def _generate_sql(prompt: str) -> str:
    response = sql_writer_llm.invoke(prompt)
    return get_text_content(response).strip()


def _format_result_preview(columns: list[str], rows: list[list[object]]) -> str:
    if not columns:
        return "Query chạy thành công nhưng không có cột trả về."
    if not rows:
        return "Không có dữ liệu phù hợp với truy vấn."

    preview_rows = rows[:10]
    widths = []
    for idx, column in enumerate(columns):
        cell_values = [
            str(row[idx]) if row[idx] is not None else "NULL" for row in preview_rows
        ]
        widths.append(min(max(len(column), *(len(value) for value in cell_values)), 40))

    header = " | ".join(
        column[:width].ljust(width) for column, width in zip(columns, widths)
    )
    separator = "-+-".join("-" * width for width in widths)
    body = []
    for row in preview_rows:
        body.append(
            " | ".join(
                (str(value) if value is not None else "NULL")[:width].ljust(width)
                for value, width in zip(row, widths)
            )
        )
    return "\n".join([header, separator, *body])


def sql_generation_node(state: WriterState) -> dict:
    """Sinh câu SQL từ metadata context (đã gồm JOIN paths)."""
    metadata = state.get("metadata_context") or ""
    dialect = state.get("db_dialect") or _resolve_dialect()
    prompt = _build_generation_prompt(state, metadata, dialect)
    print(f"Prompt: {prompt}")
    generated_sql = _generate_sql(prompt)
    print(f"Generated SQL: {generated_sql}")
    return {
        "generated_sql": generated_sql,
        "db_dialect": dialect,
        "sql_repair_attempts": 0,
        "sql_repairable": True,
    }


def sql_execution_node(state: WriterState, config: RunnableConfig) -> dict:
    """Thực thi SQL qua filter-service hoặc Postgres fallback."""
    generated_sql = state.get("generated_sql") or ""
    if not generated_sql:
        return {
            "sql_execution_error": "Không có SQL để thực thi.",
            "sql_error_code": "VALIDATION_ERROR",
            "sql_repairable": False,
        }

    dialect = state.get("db_dialect") or _resolve_dialect()
    query_scope = resolve_query_scope(
        state.get("query_scope"),
        metadata_context=state.get("metadata_context"),
        raw_results=state.get("metadata_raw_results"),
        raw_hits=state.get("metadata_hits"),
    )
    query_scope = narrow_query_scope_to_sql(query_scope, generated_sql)
    executor = create_sql_execution_client(
        state.get("user_id"),
        state.get("thread_id"),
        state=state,
        config=config,
    )

    scope_names = [t.get("name") for t in (query_scope or {}).get("tables") or []]
    print(f"📋 [SQL Execution] queryScope tables ({len(scope_names)}): {scope_names}")
    result = executor.execute_query(
        generated_sql,
        query_scope=query_scope,
        limit=100,
    )

    if result.success:
        preview = _format_result_preview(result.columns, result.rows)
        return {
            "generated_sql": result.sql_text,
            "sql_result_preview": preview,
            "sql_execution_error": None,
            "sql_error_code": None,
            "sql_repairable": True,
            "execution_row_count": result.row_count,
        }

    print(f"⚠️ [SQL Execution] {result.error_code}: {result.error_message}")
    return {
        "sql_result_preview": None,
        "sql_execution_error": result.error_message,
        "sql_error_code": result.error_code,
        "sql_repairable": getattr(result, "repairable", True),
    }


def sql_repair_node(state: WriterState) -> dict:
    """Sửa SQL sau lỗi thực thi có thể repair."""
    metadata = state.get("metadata_context") or ""
    dialect = state.get("db_dialect") or _resolve_dialect()
    generated_sql = state.get("generated_sql") or ""
    execution_error = state.get("sql_execution_error") or ""
    attempts = state.get("sql_repair_attempts") or 0

    prompt = _build_repair_prompt(
        state, metadata, dialect, generated_sql, execution_error
    )
    repaired_sql = _generate_sql(prompt)
    return {
        "generated_sql": repaired_sql,
        "sql_repair_attempts": attempts + 1,
    }


def should_continue_repair(state: WriterState) -> str:
    if state.get("sql_result_preview"):
        return "success"
    if not state.get("sql_repairable", True):
        return "give_up"
    error = state.get("sql_execution_error")
    attempts = state.get("sql_repair_attempts") or 0
    if error and attempts < MAX_SQL_REPAIR_ATTEMPTS:
        return "repair"
    return "give_up"


def finalize_output(
    generated_sql: str,
    row_count: int,
    preview: str,
    *,
    repaired: bool = False,
) -> str:
    parts = []
    if repaired:
        parts.append("Query đã được tự động sửa sau khi thực thi lỗi.")
    parts.append("SQL:")
    parts.append(generated_sql)
    parts.append("")
    parts.append(f"Rows: {row_count}")
    parts.append("Preview:")
    parts.append(preview)
    return "\n".join(parts).strip()
