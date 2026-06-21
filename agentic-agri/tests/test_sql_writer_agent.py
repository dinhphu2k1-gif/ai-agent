import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, "F:/data/src/agentic-agri/src")

from universal_agent.sql_writer_agent.db_executor_client import PostgresExecutorClient
from universal_agent.sql_writer_agent.nodes import (
    _format_result_preview,
    _finalize_output,
    sql_writer_worker_node,
)


def build_seeded_postgres_executor():
    os.environ.setdefault("PG_HOST", "192.168.2.161")
    os.environ.setdefault("PG_PORT", "5432")
    os.environ.setdefault("PG_USER", "admin")
    os.environ.setdefault("PG_PASSWORD", "password123")
    os.environ.setdefault("PG_DATABASE", "my_database")
    os.environ.setdefault("SQL_EXECUTOR_DIALECT", "postgresql")
    os.environ.setdefault("SQL_USE_FILTER_SERVICE", "false")
    return PostgresExecutorClient()


def test_postgres_executor_rejects_non_select():
    executor = PostgresExecutorClient()
    result = executor.execute_query("DELETE FROM gl_accounts")

    assert not result.success
    assert result.error_message == "Chỉ cho phép truy vấn SELECT trong giai đoạn này."


def test_extract_table_names_from_metadata_report_section():
    pytest.importorskip("neo4j")
    from universal_agent.sql_writer_agent.neo4j_client import Neo4jRelationshipClient

    client = Neo4jRelationshipClient()
    metadata_context = """BÁO CÁO METADATA
1. BẢNG LIÊN QUAN

*   CIF_CUSTOMERS
    *   Mô tả: Bảng master lưu trữ thông tin định danh khách hàng.

*   CIF_ADDRESSES
    *   Mô tả: Bảng lưu trữ các địa chỉ liên hệ của khách hàng.

*   CIF_ACCOUNTS
    *   Mô tả: Bảng cầu nối giữa CIF và GL.

2. SCHEMA CHI TIẾT

*   Bảng: CIF_CUSTOMERS
    *   CUSTOMER_ID (NUMBER(15)) [PK]
"""

    table_names = client.extract_table_names(metadata_context)
    client.close()

    assert table_names == ["CIF_CUSTOMERS", "CIF_ADDRESSES", "CIF_ACCOUNTS"]


def test_postgres_executor_rejects_multiple_statements():
    executor = PostgresExecutorClient()
    result = executor.execute_query("SELECT 1; SELECT 2")

    assert not result.success
    assert result.error_message == "Chỉ cho phép một câu SQL duy nhất."


def test_format_result_preview_returns_empty_message():
    preview = _format_result_preview(["id", "name"], [])

    assert preview == "Không có dữ liệu phù hợp với truy vấn."


def test_format_result_preview_formats_rows():
    preview = _format_result_preview(["id", "name"], [[1, "Alice"], [2, "Bob"]])

    assert "id" in preview
    assert "Alice" in preview
    assert "Bob" in preview


def test_finalize_output_includes_preview_and_row_count():
    final_output = _finalize_output("SELECT 1", 2, "id\n1", repaired=True)

    assert "Query đã được tự động sửa" in final_output
    assert "SELECT 1" in final_output
    assert "Rows: 2" in final_output
    assert "Preview:" in final_output


def test_postgres_executor_accepts_fenced_sql_block():
    executor = build_seeded_postgres_executor()
    result = executor.execute_query(
        """```sql
SELECT account_code, account_name
FROM gl_accounts
ORDER BY account_code
LIMIT 2;
```"""
    )

    assert result.success
    assert result.row_count == 2
    assert result.columns == ["account_code", "account_name"]


def test_postgres_executor_translates_fetch_first_to_limit():
    executor = build_seeded_postgres_executor()
    result = executor.execute_query(
        "SELECT account_code, account_name FROM gl_accounts ORDER BY account_code FETCH FIRST 2 ROWS ONLY"
    )

    assert result.success
    assert result.row_count == 2
    assert result.sql_text.strip().endswith("LIMIT 2")


def test_postgres_executor_returns_real_rows():
    executor = build_seeded_postgres_executor()
    result = executor.execute_query(
        "SELECT account_code, account_name FROM gl_accounts ORDER BY account_code",
        limit=3,
    )

    assert result.success
    assert result.sql_text.endswith("LIMIT 3")
    assert result.columns == ["account_code", "account_name"]
    assert result.row_count == 3
    assert result.rows[0][0] == "1001"
    assert "Account" in result.rows[0][1]


def test_postgres_executor_returns_join_results():
    executor = build_seeded_postgres_executor()
    result = executor.execute_query(
        """
        SELECT c.cif_number, a.account_code
        FROM cif_customers c
        JOIN cif_accounts ca ON c.customer_id = ca.customer_id
        JOIN gl_accounts a ON ca.account_id = a.account_id
        ORDER BY c.cif_number
        """,
        limit=5,
    )

    assert result.success
    assert result.columns == ["cif_number", "account_code"]
    assert result.row_count == 5
    assert result.rows[0][0].startswith("CIF")
    assert result.rows[0][1].isdigit()


@patch("universal_agent.writer_agent.graph.writer_subgraph")
@patch("universal_agent.writer_agent.nodes.sql_writer_llm")
def test_sql_writer_worker_returns_sql_and_preview(mock_llm, mock_subgraph):
    class Response:
        content = (
            "SELECT account_code, account_name FROM gl_accounts ORDER BY account_code"
        )

    mock_llm.invoke.return_value = Response()
    mock_subgraph.invoke.return_value = {
        "generated_sql": "SELECT account_code, account_name FROM gl_accounts ORDER BY account_code",
        "sql_result_preview": "account_code | account_name\n1001 | Cash",
        "execution_row_count": 3,
        "sql_repair_attempts": 0,
        "db_dialect": "postgresql",
    }

    state = {
        "user_input": "Cho tôi 3 tài khoản đầu tiên",
        "metadata_context": "[TABLE] GL_ACCOUNTS\n[COLUMN] GL_ACCOUNTS.ACCOUNT_CODE\n[COLUMN] GL_ACCOUNTS.ACCOUNT_NAME",
        "query_scope": {
            "source": "metadata_agent",
            "tables": [{"name": "GL_ACCOUNTS", "schema": "GL"}],
        },
        "investigation_log": [],
        "db_dialect": "postgresql",
    }

    result = sql_writer_worker_node(state, {})

    assert "SQL:" in result["final_output"]
    assert "Rows:" in result["final_output"]
    assert "account_code" in result["sql_result_preview"]
    assert result["generated_sql"].startswith("SELECT account_code")
    assert result["execution_attempts"] == 1
    assert result["sql_execution_error"] is None


@patch("universal_agent.writer_agent.graph.writer_subgraph")
@patch("universal_agent.writer_agent.nodes.sql_writer_llm")
def test_sql_writer_worker_repairs_failed_query(mock_llm, mock_subgraph):
    mock_subgraph.invoke.return_value = {
        "generated_sql": "SELECT account_code FROM gl_accounts ORDER BY account_code",
        "sql_result_preview": "account_code\n1001",
        "execution_row_count": 100,
        "sql_repair_attempts": 1,
        "db_dialect": "postgresql",
    }

    state = {
        "user_input": "Cho tôi danh sách mã tài khoản",
        "metadata_context": "[TABLE] GL_ACCOUNTS\n[COLUMN] GL_ACCOUNTS.ACCOUNT_CODE",
        "query_scope": {
            "source": "metadata_agent",
            "tables": [{"name": "GL_ACCOUNTS", "schema": "GL"}],
        },
        "investigation_log": [],
        "db_dialect": "postgresql",
    }

    result = sql_writer_worker_node(state, {})

    assert result["execution_attempts"] == 2
    assert "Query đã được tự động sửa" in result["final_output"]
    assert result["generated_sql"].startswith("SELECT account_code")
    assert result["sql_execution_error"] is None
