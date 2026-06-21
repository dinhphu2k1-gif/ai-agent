"""Unit tests for queryScope builder."""

import sys

sys.path.insert(0, "F:/data/src/agentic-agri/src")

from universal_agent.writer_agent.query_scope import build_query_scope


def test_build_query_scope_from_raw_results():
    raw = """
[TABLE] CIF_CUSTOMERS — Customers
[COLUMN] CIF_CUSTOMERS.customer_id
[COLUMN] CIF_CUSTOMERS.customer_name
[COLUMN] CIF_ACCOUNTS.account_number
"""
    scope = build_query_scope(
        ["CIF_CUSTOMERS", "CIF_ACCOUNTS"],
        raw_results=raw,
    )

    assert scope["source"] == "metadata_agent"
    assert len(scope["tables"]) == 2
    by_name = {t["name"]: t for t in scope["tables"]}
    assert "customer_id" in by_name["CIF_CUSTOMERS"]["columns"]
    assert "account_number" in by_name["CIF_ACCOUNTS"]["columns"]


def test_build_query_scope_deduplicates_tables():
    scope = build_query_scope(["CIF_CUSTOMERS", "cif_customers", ""])
    assert scope["tables"] == [{"name": "CIF_CUSTOMERS", "schema": "CIF"}]


def test_build_query_scope_uses_schema_from_hits():
    hits = [
        {
            "_source": {
                "record_type": "TABLE",
                "schema_name": "GL",
                "table_name": "GL_ACCOUNTS",
            }
        }
    ]
    scope = build_query_scope(["GL_ACCOUNTS"], raw_hits=hits)
    assert scope["tables"][0]["schema"] == "GL"


def test_ensure_table_schemas_replaces_public():
    from universal_agent.writer_agent.query_scope import resolve_query_scope

    stale = {
        "source": "metadata_agent",
        "tables": [{"name": "CIF_CUSTOMERS", "schema": "public"}],
    }
    scope = resolve_query_scope(stale)
    assert scope["tables"][0]["schema"] == "CIF"


def test_build_query_scope_from_table_lines_only():
    raw = """
[TABLE] CIF_CUSTOMERS — Customers
[TABLE] CIF_ACCOUNTS — Accounts
"""
    scope = build_query_scope([], raw_results=raw)
    names = {t["name"] for t in scope["tables"]}
    assert names == {"CIF_CUSTOMERS", "CIF_ACCOUNTS"}


def test_build_query_scope_from_columns_when_table_names_missing():
    raw = """
[COLUMN] CIF_CUSTOMERS.customer_id
[COLUMN] CIF_ACCOUNTS.account_number
"""
    scope = build_query_scope([], raw_results=raw)
    assert len(scope["tables"]) == 2


def test_resolve_query_scope_rebuilds_from_raw_results():
    from universal_agent.writer_agent.query_scope import resolve_query_scope

    raw = "[TABLE] GL_ACCOUNTS\n[COLUMN] GL_ACCOUNTS.account_code"
    scope = resolve_query_scope(None, raw_results=raw)
    assert scope is not None
    assert scope["tables"][0]["name"] == "GL_ACCOUNTS"
    assert "account_code" in scope["tables"][0]["columns"]


def test_resolve_query_scope_from_synthesized_metadata():
    from universal_agent.writer_agent.query_scope import resolve_query_scope

    metadata = "Dùng bảng CIF_CUSTOMERS và CIF_ACCOUNTS để tra cứu."
    raw = "[TABLE] CIF_CUSTOMERS\n[TABLE] CIF_ACCOUNTS"
    scope = resolve_query_scope(None, metadata_context=metadata, raw_results=raw)
    names = {t["name"] for t in scope["tables"]}
    assert "CIF_CUSTOMERS" in names
    assert "CIF_ACCOUNTS" in names


def test_build_query_scope_from_hits():
    hits = [
        {
            "_source": {
                "record_type": "COLUMN",
                "table_name": "GL_ACCOUNTS",
                "column_name": "ACCOUNT_CODE",
            }
        }
    ]
    scope = build_query_scope(["GL_ACCOUNTS"], raw_hits=hits)
    assert scope["tables"][0]["columns"] == ["account_code"]


def test_extract_tables_from_sql_join():
    from universal_agent.writer_agent.query_scope import extract_tables_from_sql

    known = [
        "GL_JOURNAL_HEADERS",
        "GL_JOURNAL_LINES",
        "GL_ACCOUNTS",
        "GL_BALANCES",
        "GL_PERIODS",
        "CIF_CUSTOMERS",
        "CIF_ACCOUNTS",
    ]
    sql = """
    SELECT h.journal_id, l.amount
    FROM GL.GL_JOURNAL_HEADERS h
    JOIN GL.GL_JOURNAL_LINES l ON h.journal_id = l.journal_id
    """
    assert set(extract_tables_from_sql(sql, known)) == {
        "GL_JOURNAL_HEADERS",
        "GL_JOURNAL_LINES",
    }


def test_extract_tables_ignores_column_identifiers():
    from universal_agent.writer_agent.query_scope import extract_tables_from_sql

    known = [
        "CIF_CUSTOMERS",
        "CIF_ACCOUNTS",
        "GL_ACCOUNTS",
        "GL_BALANCES",
        "GL_PERIODS",
    ]
    sql = """
    SELECT
        c.CIF_NUMBER,
        c.FULL_NAME
    FROM CIF_CUSTOMERS c
    LEFT JOIN CIF_ACCOUNTS ca ON c.CUSTOMER_ID = ca.CUSTOMER_ID
    LEFT JOIN GL_ACCOUNTS ga ON ca.ACCOUNT_ID = ga.ACCOUNT_ID
    LEFT JOIN GL_BALANCES gb ON ga.ACCOUNT_ID = gb.ACCOUNT_ID
    WHERE gb.PERIOD_ID = (SELECT MAX(PERIOD_ID) FROM GL_PERIODS WHERE FISCAL_YEAR = 2024)
    """
    refs = extract_tables_from_sql(sql, known)
    assert "CIF_NUMBER" not in refs
    assert set(refs) == {
        "CIF_CUSTOMERS",
        "CIF_ACCOUNTS",
        "GL_ACCOUNTS",
        "GL_BALANCES",
        "GL_PERIODS",
    }


def test_narrow_query_scope_drops_unused_metadata_tables():
    from universal_agent.writer_agent.query_scope import narrow_query_scope_to_sql

    scope = build_query_scope(
        ["GL_JOURNAL_HEADERS", "GL_JOURNAL_LINES", "GL_ACCOUNTS", "CIF_CUSTOMERS"],
    )
    sql = "SELECT * FROM GL_JOURNAL_HEADERS h JOIN GL_JOURNAL_LINES l USING (journal_id)"
    narrowed = narrow_query_scope_to_sql(scope, sql)

    assert narrowed is not None
    assert narrowed["source"] == "sql_parser"
    names = {t["name"] for t in narrowed["tables"]}
    assert names == {"GL_JOURNAL_HEADERS", "GL_JOURNAL_LINES"}
    assert "GL_ACCOUNTS" not in names
    assert "CIF_CUSTOMERS" not in names
