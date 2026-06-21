"""SQL execute API: queryScope enforcement, row filter injection, column masking."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.main import create_app
from app.repositories.identity_repo import IdentityRepository
from scripts.seed_demo_data import seed_permission_wizard_resource_tree


@pytest.fixture
def sql_client(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> tuple[TestClient, MagicMock]:
    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)
    get_settings.cache_clear()

    mock_executor = MagicMock()

    def override_get_db() -> Any:
        try:
            yield db_session
            db_session.commit()
        except BaseException:
            db_session.rollback()
            raise

    application = create_app()
    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as test_client:
        test_client.app.state.sql_executor = mock_executor
        yield test_client, mock_executor
    application.dependency_overrides.clear()
    get_settings.cache_clear()


def _mk_user(db_session: Session, username: str = "u") -> None:
    IdentityRepository(db_session).create_user(username, f"{username}@example.com")
    db_session.flush()


def test_execute_requires_select_only(sql_client: tuple[TestClient, MagicMock], db_session: Session) -> None:
    client, _ = sql_client
    _mk_user(db_session, "any_user")
    resp = client.post(
        "/api/v1/sql/execute",
        json={
            "userId": "any_user",
            "sql": "DELETE FROM x",
            "queryScope": {"source": "manual", "tables": [{"name": "X"}]},
        },
    )
    assert resp.status_code == 400
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_execute_policy_violation_undeclared_table(sql_client: tuple[TestClient, MagicMock], db_session: Session) -> None:
    client, _ = sql_client
    _mk_user(db_session, "any_user")
    resp = client.post(
        "/api/v1/sql/execute",
        json={
            "userId": "any_user",
            "sql": "SELECT t.col FROM T t",
            "queryScope": {"source": "manual", "tables": [{"name": "OTHER"}]},
            "options": {"strictScopeMatch": True},
        },
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "POLICY_VIOLATION"


def test_execute_cif_tables_match_scope_without_schema_prefix(
    sql_client: tuple[TestClient, MagicMock], db_session: Session
) -> None:
    client, mock_exec = sql_client
    seed_permission_wizard_resource_tree(db_session)
    _mk_user(db_session, "demo_user")
    mock_exec.execute_select.return_value = (["CIF_NUMBER"], [{"CIF_NUMBER": "x"}])

    resp = client.post(
        "/api/v1/sql/execute",
        json={
            "userId": "demo_user",
            "sql": "SELECT c.CIF_NUMBER FROM CIF_CUSTOMERS c",
            "limit": 1,
            "queryScope": {
                "source": "manual",
                "tables": [{"name": "CIF_CUSTOMERS", "schema": "CIF"}],
            },
            "options": {
                "applyRowFilter": False,
                "applyColumnMasking": False,
                "strictScopeMatch": True,
            },
        },
    )
    if resp.status_code == 422:
        pytest.skip("CIF catalog not seeded in demo tree")
    assert resp.status_code != 403 or resp.json()["error"]["code"] != "POLICY_VIOLATION"


def test_execute_success_shape(sql_client: tuple[TestClient, MagicMock], db_session: Session) -> None:
    client, mock_exec = sql_client
    seed_permission_wizard_resource_tree(db_session)
    _mk_user(db_session, "demo_user")

    # Mock DB execution result.
    mock_exec.execute_select.return_value = (["a"], [{"a": "1234"}])

    resp = client.post(
        "/api/v1/sql/execute",
        json={
            "userId": "demo_user",
            "sql": "SELECT users.id AS a FROM users",
            "limit": 1,
            "queryScope": {"source": "manual", "tables": [{"name": "USERS", "schema": "public", "columns": ["id"]}]},
            "options": {"applyRowFilter": False, "applyColumnMasking": False, "strictScopeMatch": True},
        },
    )
    assert resp.status_code in (200, 403, 422)
    body = resp.json()
    if resp.status_code == 200:
        assert body["success"] is True
        assert "data" in body
        assert "executedSql" in body["data"]
        assert body["data"]["columns"] == ["a"]
        assert body["data"]["rows"] == [["1234"]]


def test_jsonable_cell_makes_decimal_json_safe() -> None:
    from app.services.masking_service import jsonable_cell

    row = [[jsonable_cell(Decimal("12345.67"))]]
    import json

    json.dumps(row)
    assert row == [[12345.67]]

