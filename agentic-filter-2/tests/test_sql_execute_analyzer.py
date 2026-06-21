"""Unit tests for sql_execute_analyzer."""

from __future__ import annotations

import pytest

from app.query.sql_execute_analyzer import (
    SqlExecuteUnsupportedQueryError,
    parse_sql_execute_select,
)


def test_parse_where_in_subquery() -> None:
    sql = """
    SELECT
        c.CIF_NUMBER,
        c.FULL_NAME,
        a.ADDRESS_LINE
    FROM CIF_CUSTOMERS c
    JOIN CIF_ADDRESSES a ON c.CUSTOMER_ID = a.CUSTOMER_ID
    WHERE c.CUSTOMER_ID IN (
        SELECT CUSTOMER_ID FROM CIF_CUSTOMERS ORDER BY CUSTOMER_ID ASC LIMIT 10
    )
    ORDER BY c.CUSTOMER_ID, a.ADDRESS_ID
    """
    parsed = parse_sql_execute_select(sql)
    assert parsed.tables == ("CIF_CUSTOMERS", "CIF_ADDRESSES")
    assert parsed.projections == (
        ("CIF_NUMBER", "CIF_CUSTOMERS", "CIF_NUMBER"),
        ("FULL_NAME", "CIF_CUSTOMERS", "FULL_NAME"),
        ("ADDRESS_LINE", "CIF_ADDRESSES", "ADDRESS_LINE"),
    )
    assert ("CIF_ADDRESSES", "ADDRESS_LINE") in parsed.referenced_columns
    assert ("CIF_CUSTOMERS", "FULL_NAME") in parsed.referenced_columns


def test_join_referenced_columns_include_joined_table() -> None:
    sql = """
    SELECT c.FULL_NAME, a.ADDRESS_LINE
    FROM CIF_CUSTOMERS c
    JOIN CIF_ADDRESSES a ON c.CUSTOMER_ID = a.CUSTOMER_ID
    """
    parsed = parse_sql_execute_select(sql)
    assert ("CIF_ADDRESSES", "ADDRESS_LINE") in parsed.referenced_columns
    assert ("CIF_ADDRESSES", "CUSTOMER_ID") in parsed.referenced_columns
    assert ("CIF_CUSTOMERS", "FULL_NAME") in parsed.referenced_columns


def test_parse_subquery_in_from_and_aggregate_projection() -> None:
    sql = """
    SELECT
        c.CUSTOMER_ID,
        c.FULL_NAME,
        COALESCE(SUM(CASE WHEN ga.ACCOUNT_TYPE = 'ASSET' THEN lb.CLOSING_BALANCE_DR ELSE 0 END), 0) AS TOTAL_BALANCE
    FROM CIF_CUSTOMERS c
    LEFT JOIN CIF_ACCOUNTS ca ON c.CUSTOMER_ID = ca.CUSTOMER_ID
    LEFT JOIN GL_ACCOUNTS ga ON ca.ACCOUNT_ID = ga.ACCOUNT_ID
    LEFT JOIN (
        SELECT ACCOUNT_ID, CLOSING_BALANCE_DR, CLOSING_BALANCE_CR
        FROM GL_BALANCES
    ) AS lb ON ga.ACCOUNT_ID = lb.ACCOUNT_ID
    WHERE c.STATUS = 'ACTIVE'
    GROUP BY c.CUSTOMER_ID, c.FULL_NAME
    """
    parsed = parse_sql_execute_select(sql)
    assert "CIF_CUSTOMERS" in parsed.tables
    assert "GL_BALANCES" in parsed.tables
    assert parsed.projections == (
        ("CUSTOMER_ID", "CIF_CUSTOMERS", "CUSTOMER_ID"),
        ("FULL_NAME", "CIF_CUSTOMERS", "FULL_NAME"),
    )
    assert ("CIF_CUSTOMERS", "CUSTOMER_ID") in parsed.referenced_columns
    assert ("GL_BALANCES", "ACCOUNT_ID") in parsed.referenced_columns


def test_infer_cif_schema_when_sql_omits_schema_prefix() -> None:
    sql = """
    SELECT c.CIF_NUMBER
    FROM CIF_CUSTOMERS c
    JOIN CIF_ADDRESSES a ON c.CUSTOMER_ID = a.CUSTOMER_ID
    """
    parsed = parse_sql_execute_select(sql)
    assert parsed.schema_by_table["CIF_CUSTOMERS"] == "CIF"
    assert parsed.schema_by_table["CIF_ADDRESSES"] == "CIF"
