"""Tests for SQL normalization before filter-service execution."""

import sys

sys.path.insert(0, "F:/data/src/agentic-agri/src")

from universal_agent.writer_agent.sql_normalize import (
    prepare_sql_for_filter_service,
    strip_trailing_limit,
)


def test_strip_trailing_limit_and_offset():
    sql = "SELECT * FROM gl_accounts ORDER BY id LIMIT 10 OFFSET 5"
    assert strip_trailing_limit(sql) == "SELECT * FROM gl_accounts ORDER BY id"


def test_strip_fetch_first():
    sql = "SELECT 1 FETCH FIRST 25 ROWS ONLY"
    assert strip_trailing_limit(sql) == "SELECT 1"


def test_prepare_sql_removes_markdown_and_limit():
    sql = "```sql\nSELECT * FROM t LIMIT 5;\n```"
    assert prepare_sql_for_filter_service(sql) == "SELECT * FROM t"
