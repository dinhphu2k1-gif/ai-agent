"""
State definition cho Writer Agent Sub-Graph.
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class QueryScopeTable(TypedDict, total=False):
    name: str
    schema: str
    columns: list[str]
    alias: str


class QueryScope(TypedDict, total=False):
    source: str
    tables: list[QueryScopeTable]


class WriterState(TypedDict, total=False):
    """State nội bộ của Writer Sub-Graph."""

    user_input: str
    metadata_context: str
    metadata_raw_results: Optional[str]
    metadata_hits: Optional[list]
    query_scope: Optional[QueryScope]
    user_id: str
    thread_id: Optional[str]

    db_dialect: Optional[str]
    generated_sql: Optional[str]
    sql_result_preview: Optional[str]
    sql_execution_error: Optional[str]
    sql_error_code: Optional[str]
    sql_repairable: bool
    sql_repair_attempts: int
    execution_row_count: int
    final_output: Optional[str]
