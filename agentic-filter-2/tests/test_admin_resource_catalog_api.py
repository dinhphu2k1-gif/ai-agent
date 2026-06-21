"""Phase 4: resource search, scope-stats, action-catalog APIs."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import PermissionType
from app.repositories.resource_repo import ResourceRepository
from scripts.seed_demo_data import seed_permission_wizard_resource_tree


@pytest.fixture(autouse=True)
def _permission_types(db_session: Session) -> None:
    for name in ("SELECT", "USAGE", "INSERT", "UPDATE", "DELETE", "DESCRIBE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


def _seed_tree(db_session: Session) -> ResourceRepository:
    seed_permission_wizard_resource_tree(db_session)
    return ResourceRepository(db_session)


def test_search_email_returns_column_breadcrumb(
    admin_client: TestClient, db_session: Session
) -> None:
    _seed_tree(db_session)
    response = admin_client.get(
        "/api/v1/admin/resources/search",
        params={"q": "email", "limit": 50},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    results = body["data"]["results"]
    assert len(results) >= 1
    hit = next(r for r in results if r["node"]["name"] == "email")
    assert hit["node"]["type"] == "column"
    assert "analytics_db" in hit["breadcrumb"]
    assert hit["path"][-1]["name"] == "email"


def test_scope_stats_database_matches_tree_counts(
    admin_client: TestClient, db_session: Session
) -> None:
    rr = _seed_tree(db_session)
    db_id = rr.find_database_resource_id_by_name("analytics_db")
    assert db_id is not None

    expected_schemas = len(rr.list_schemas_for_database(db_id))
    expected_tables = 0
    expected_columns = 0
    for sch in rr.list_schemas_for_database(db_id):
        for tbl in rr.list_tables_for_schema(sch.resource_id):
            expected_tables += 1
            expected_columns += len(rr.list_columns_for_table(tbl.resource_id))

    response = admin_client.get(
        f"/api/v1/admin/resources/{db_id}/scope-stats",
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["resourceType"] == "database"
    assert data["schemaCount"] == expected_schemas
    assert data["tableCount"] == expected_tables
    assert data["columnCount"] == expected_columns
    assert "analytics_db" in data["message"]


def test_scope_stats_schema_counts_tables_and_columns(
    admin_client: TestClient, db_session: Session
) -> None:
    rr = _seed_tree(db_session)
    db_id = rr.find_database_resource_id_by_name("analytics_db")
    sch_id = rr.find_schema_resource_id(db_id, "public")
    assert sch_id is not None

    expected_tables = len(rr.list_tables_for_schema(sch_id))
    expected_columns = 0
    for tbl in rr.list_tables_for_schema(sch_id):
        expected_columns += len(rr.list_columns_for_table(tbl.resource_id))

    response = admin_client.get(
        f"/api/v1/admin/resources/{sch_id}/scope-stats",
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["resourceType"] == "schema"
    assert data["schemaCount"] == 1
    assert data["tableCount"] == expected_tables
    assert data["columnCount"] == expected_columns


def test_scope_stats_table_returns_400(
    admin_client: TestClient, db_session: Session
) -> None:
    rr = _seed_tree(db_session)
    db_id = rr.find_database_resource_id_by_name("analytics_db")
    sch_id = rr.find_schema_resource_id(db_id, "public")
    tbl_id = rr.find_table_resource_id(sch_id, "users")
    assert tbl_id is not None

    response = admin_client.get(
        f"/api/v1/admin/resources/{tbl_id}/scope-stats",
    )
    assert response.status_code == 400
    assert response.json()["data"]["code"] == "BAD_REQUEST"


def test_scope_stats_unknown_resource_404(
    admin_client: TestClient,
) -> None:
    missing = uuid.uuid4()
    response = admin_client.get(
        f"/api/v1/admin/resources/{missing}/scope-stats",
    )
    assert response.status_code == 404


def test_action_catalog_table_includes_select_describe(
    admin_client: TestClient, db_session: Session
) -> None:
    for resource_type in ("TABLE", "table"):
        response = admin_client.get(
            "/api/v1/admin/permissions/action-catalog",
            params={"resourceType": resource_type},
        )
        assert response.status_code == 200
        actions = response.json()["data"]["actions"]
        assert "SELECT" in actions
        assert "DESCRIBE" in actions


def test_action_catalog_database_includes_usage(
    admin_client: TestClient, db_session: Session
) -> None:
    response = admin_client.get(
        "/api/v1/admin/permissions/action-catalog",
        params={"resourceType": "DATABASE"},
    )
    assert response.status_code == 200
    assert "USAGE" in response.json()["data"]["actions"]


def test_action_catalog_unknown_type_400(
    admin_client: TestClient, db_session: Session
) -> None:
    response = admin_client.get(
        "/api/v1/admin/permissions/action-catalog",
        params={"resourceType": "VIEW"},
    )
    assert response.status_code == 400
