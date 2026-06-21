"""Unit tests for Writer Agent sub-graph and supervisor worker."""

from unittest.mock import patch

from universal_agent.writer_agent.nodes import (
    _format_result_preview,
    finalize_output,
    should_continue_repair,
)
from universal_agent.supervisor.nodes import sql_writer_worker_node


def test_should_continue_repair_success():
    assert should_continue_repair({"sql_result_preview": "data"}) == "success"


def test_should_continue_repair_non_repairable():
    state = {
        "sql_execution_error": "denied",
        "sql_repairable": False,
        "sql_repair_attempts": 0,
    }
    assert should_continue_repair(state) == "give_up"


def test_should_continue_repair_retries():
    state = {
        "sql_execution_error": "syntax error",
        "sql_repairable": True,
        "sql_repair_attempts": 0,
    }
    assert should_continue_repair(state) == "repair"


def test_format_result_preview_formats_rows():
    preview = _format_result_preview(["id", "name"], [[1, "Alice"]])
    assert "Alice" in preview


def test_finalize_output_includes_preview():
    out = finalize_output("SELECT 1", 2, "id\n1", repaired=True)
    assert "Query đã được tự động sửa" in out
    assert "Rows: 2" in out


@patch("universal_agent.writer_agent.graph.writer_subgraph")
def test_sql_writer_worker_maps_subgraph_success(mock_subgraph):
    mock_subgraph.invoke.return_value = {
        "generated_sql": "SELECT 1",
        "sql_result_preview": "x\n1",
        "execution_row_count": 1,
        "sql_repair_attempts": 0,
        "db_dialect": "postgresql",
    }

    result = sql_writer_worker_node(
        {
            "user_input": "test",
            "metadata_context": "[TABLE] T",
            "query_scope": {"source": "metadata_agent", "tables": [{"name": "T"}]},
            "investigation_log": [],
        },
        {"configurable": {"user_id": "u1"}},
    )

    assert "SQL:" in result["final_output"]
    assert result["sql_execution_error"] is None


@patch("universal_agent.writer_agent.graph.writer_subgraph")
def test_sql_writer_worker_maps_forbidden(mock_subgraph):
    mock_subgraph.invoke.return_value = {
        "generated_sql": "SELECT secret FROM t",
        "sql_result_preview": None,
        "sql_execution_error": "No permission",
        "sql_error_code": "FORBIDDEN",
        "sql_repairable": False,
        "sql_repair_attempts": 0,
    }

    result = sql_writer_worker_node(
        {
            "user_input": "test",
            "metadata_context": "[TABLE] T",
            "investigation_log": [],
        },
        {},
    )

    assert "Không có quyền" in result["final_output"]
