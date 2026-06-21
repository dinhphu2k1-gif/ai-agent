"""Live /api/v1/sql/execute against configured COREDB permissions + GL/CIF runtime data.

Requires (from .env):
  - DATABASE_URL → permission catalog with COREDB + agri_agent permissions
  - PG_* or RUNTIME_POSTGRES_URL → physical public.cif_* / gl_* tables

Nghiệp vụ: user/role/group → permission → row filter / column mask (SRS §2.4).
Seed metadata: agentic-agri/scripts/seed_data_dictionary.py (GL + CIF domain).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

AGRI_USER = "agri_agent"
DEMO_USER = "demo_user"

SQL_CIF_CUSTOMER_PROFILE = """
SELECT
    c.CIF_NUMBER,
    c.FULL_NAME,
    c.CUSTOMER_TYPE,
    a.ADDRESS_TYPE,
    a.ADDRESS_LINE,
    a.WARD_NAME
FROM CIF_CUSTOMERS c
JOIN CIF_ADDRESSES a ON c.CUSTOMER_ID = a.CUSTOMER_ID
ORDER BY c.CUSTOMER_ID, a.ADDRESS_ID
"""

SQL_CIF_GL_ACCOUNT_BRIDGE = """
SELECT
    c.CIF_NUMBER,
    c.FULL_NAME,
    ca.ACCOUNT_NUMBER,
    ca.ACCOUNT_ROLE,
    ga.ACCOUNT_CODE,
    ga.ACCOUNT_NAME,
    ga.ACCOUNT_TYPE
FROM CIF_CUSTOMERS c
JOIN CIF_ACCOUNTS ca ON c.CUSTOMER_ID = ca.CUSTOMER_ID
JOIN GL_ACCOUNTS ga ON ca.ACCOUNT_ID = ga.ACCOUNT_ID
ORDER BY c.CIF_NUMBER, ca.ACCOUNT_NUMBER
"""

SQL_GL_JOURNAL_DETAIL = """
SELECT
    h.JOURNAL_NUMBER,
    h.JOURNAL_DATE,
    h.STATUS,
    l.LINE_NUMBER,
    l.DEBIT_AMOUNT,
    l.CREDIT_AMOUNT,
    ga.ACCOUNT_CODE
FROM GL_JOURNAL_HEADERS h
JOIN GL_JOURNAL_LINES l ON h.JOURNAL_ID = l.JOURNAL_ID
JOIN GL_ACCOUNTS ga ON l.ACCOUNT_ID = ga.ACCOUNT_ID
ORDER BY h.JOURNAL_ID, l.LINE_NUMBER
"""


def _execute(
    client: TestClient,
    *,
    user_id: str,
    sql: str,
    tables: list[dict[str, str]],
    limit: int = 5,
    apply_row_filter: bool = True,
    apply_column_masking: bool = True,
) -> dict:
    resp = client.post(
        "/api/v1/sql/execute",
        json={
            "userId": user_id,
            "sql": sql,
            "limit": limit,
            "queryScope": {"source": "manual", "tables": tables},
            "options": {
                "applyRowFilter": apply_row_filter,
                "applyColumnMasking": apply_column_masking,
                "strictScopeMatch": True,
            },
        },
    )
    return {"status_code": resp.status_code, "body": resp.json()}


@pytest.mark.integration
def test_cif_join_returns_six_columns_with_column_masking(
    live_sql_client: TestClient,
) -> None:
    """CIF_CUSTOMERS ⨝ CIF_ADDRESSES — multi-table, multi-column, mask theo policy."""
    out = _execute(
        live_sql_client,
        user_id=AGRI_USER,
        sql=SQL_CIF_CUSTOMER_PROFILE,
        tables=[
            {"name": "CIF_CUSTOMERS", "schema": "CIF"},
            {"name": "CIF_ADDRESSES", "schema": "CIF"},
        ],
    )
    assert out["status_code"] == 200, out["body"]
    body = out["body"]
    assert body["success"] is True
    data = body["data"]
    assert data["columns"] == [
        "cif_number",
        "full_name",
        "customer_type",
        "address_type",
        "address_line",
        "ward_name",
    ]
    assert data["rowCount"] >= 1
    assert set(data["filtered"]["checkedTables"]) == {"CIF_CUSTOMERS", "CIF_ADDRESSES"}
    assert "FULL_NAME" in data["filtered"]["maskedColumns"]
    assert "ADDRESS_LINE" in data["filtered"]["maskedColumns"]

    first = data["rows"][0]
    full_name = first[1]
    address_line = first[4]
    assert "***" in full_name
    assert address_line
    assert set(address_line) == {"*"}


@pytest.mark.integration
def test_cif_gl_three_table_join_returns_seven_columns(
    live_sql_client: TestClient,
) -> None:
    """CIF_CUSTOMERS → CIF_ACCOUNTS → GL_ACCOUNTS (cross-domain join từ seed dictionary)."""
    out = _execute(
        live_sql_client,
        user_id=AGRI_USER,
        sql=SQL_CIF_GL_ACCOUNT_BRIDGE,
        tables=[
            {"name": "CIF_CUSTOMERS", "schema": "CIF"},
            {"name": "CIF_ACCOUNTS", "schema": "CIF"},
            {"name": "GL_ACCOUNTS", "schema": "GL"},
        ],
    )
    assert out["status_code"] == 200, out["body"]
    data = out["body"]["data"]
    assert len(data["columns"]) == 7
    assert data["rowCount"] >= 1
    scope = data["filtered"]["scopeMatch"]
    assert scope["strictScopeMatch"] is True
    assert set(scope["parsedTables"]) == {
        "CIF_CUSTOMERS",
        "CIF_ACCOUNTS",
        "GL_ACCOUNTS",
    }
    assert "GL_ACCOUNTS" in data["filtered"]["checkedTables"]


@pytest.mark.integration
def test_gl_journal_join_denied_when_table_select_not_granted(
    live_sql_client: TestClient,
) -> None:
    """agri_agent có SELECT GL_ACCOUNTS nhưng không có SELECT GL_JOURNAL_* → 403."""
    out = _execute(
        live_sql_client,
        user_id=AGRI_USER,
        sql=SQL_GL_JOURNAL_DETAIL,
        tables=[
            {"name": "GL_JOURNAL_HEADERS", "schema": "GL"},
            {"name": "GL_JOURNAL_LINES", "schema": "GL"},
            {"name": "GL_ACCOUNTS", "schema": "GL"},
        ],
    )
    assert out["status_code"] == 403
    err = out["body"]["error"]
    assert err["code"] == "FORBIDDEN"
    assert "GL_JOURNAL_HEADERS" in err["message"]


@pytest.mark.integration
def test_strict_scope_rejects_undeclared_join_table(
    live_sql_client: TestClient,
) -> None:
    """SQL tham chiếu CIF_ADDRESSES nhưng queryScope chỉ khai báo CIF_CUSTOMERS."""
    sql = """
    SELECT c.CIF_NUMBER, a.ADDRESS_LINE
    FROM CIF_CUSTOMERS c
    JOIN CIF_ADDRESSES a ON c.CUSTOMER_ID = a.CUSTOMER_ID
    """
    out = _execute(
        live_sql_client,
        user_id=AGRI_USER,
        sql=sql,
        tables=[{"name": "CIF_CUSTOMERS", "schema": "CIF"}],
    )
    assert out["status_code"] == 403
    err = out["body"]["error"]
    assert err["code"] == "POLICY_VIOLATION"
    assert "CIF_ADDRESSES" in err["message"]


@pytest.mark.integration
def test_demo_user_with_describe_only_cannot_execute_select(
    live_sql_client: TestClient,
) -> None:
    """demo_user chỉ có DESCRIBE trên bảng COREDB — runtime SELECT bị từ chối."""
    out = _execute(
        live_sql_client,
        user_id=DEMO_USER,
        sql="SELECT c.CIF_NUMBER FROM CIF_CUSTOMERS c",
        tables=[{"name": "CIF_CUSTOMERS", "schema": "CIF"}],
    )
    assert out["status_code"] == 403
    assert out["body"]["error"]["code"] == "FORBIDDEN"
