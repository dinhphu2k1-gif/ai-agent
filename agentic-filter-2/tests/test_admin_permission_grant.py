"""Phase 2: E2E grant + list permissions with row filter and column mask."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import PermissionType
from app.repositories.identity_repo import IdentityRepository
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


def _analytics_table_path(db_session: Session) -> tuple[list[dict], uuid.UUID]:
    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    db_rid = rr.find_database_resource_id_by_name("analytics_db")
    assert db_rid is not None
    sch_rid = rr.find_schema_resource_id(db_rid, "public")
    tbl_rid = rr.find_table_resource_id(sch_rid, "users")
    assert tbl_rid is not None
    path = [
        {"id": str(db_rid), "name": "analytics_db", "type": "database"},
        {"id": str(sch_rid), "name": "public", "type": "schema"},
        {"id": str(tbl_rid), "name": "users", "type": "table"},
    ]
    return path, tbl_rid


def _analytics_column_path(db_session: Session) -> tuple[list[dict], uuid.UUID]:
    path, tbl_rid = _analytics_table_path(db_session)
    rr = ResourceRepository(db_session)
    col_rid = rr.find_column_resource_id(tbl_rid, "email")
    assert col_rid is not None
    path.append({"id": str(col_rid), "name": "email", "type": "column"})
    return path, col_rid


def test_grant_table_row_filter_list_has_condition_expression(
    admin_client: TestClient, db_session: Session
) -> None:
    path, _ = _analytics_table_path(db_session)
    ir = IdentityRepository(db_session)
    role = ir.create_role("Grant_RowFilter_E2E")
    db_session.flush()
    expr = "tenant_id = 42 AND region = 'EU'"

    grant = admin_client.post(
        f"/api/v1/admin/roles/{role.id}/permissions",
        json={
            "resourcePath": path,
            "resourceType": "TABLE",
            "actions": ["SELECT"],
            "effect": "ALLOW",
            "rowFilter": {"enabled": True, "conditionExpression": expr},
        },
    )
    assert grant.status_code == 201
    created = grant.json()["data"]["created"]
    assert len(created) == 1
    perm = created[0]
    assert perm["resourceType"] == "TABLE"
    assert len(perm["path"]) == 3
    assert perm["modifier"]["type"] == "ROW_FILTER"
    assert perm["modifier"]["conditionExpression"] == expr
    assert perm["modifier"]["label"] == expr

    listed = admin_client.get(f"/api/v1/admin/roles/{role.id}/permissions")
    assert listed.status_code == 200
    found = next(
        p for p in listed.json()["data"]["permissions"] if p["id"] == perm["id"]
    )
    assert found["modifier"]["conditionExpression"] == expr
    assert found["modifier"]["label"] == expr


def test_grant_column_partial_mask_list_has_mask_fields(
    admin_client: TestClient, db_session: Session
) -> None:
    path, _ = _analytics_column_path(db_session)
    ir = IdentityRepository(db_session)
    role = ir.create_role("Grant_ColumnMask_E2E")
    db_session.flush()
    pattern = "091-XXX-XXXX"

    grant = admin_client.post(
        f"/api/v1/admin/roles/{role.id}/permissions",
        json={
            "resourcePath": path,
            "resourceType": "COLUMN",
            "actions": ["SELECT"],
            "effect": "ALLOW",
            "columnMask": {
                "enabled": True,
                "maskType": "PARTIAL",
                "maskPattern": pattern,
            },
        },
    )
    assert grant.status_code == 201
    perm = grant.json()["data"]["created"][0]
    assert perm["resourceType"] == "COLUMN"
    assert len(perm["path"]) == 4
    mod = perm["modifier"]
    assert mod["type"] == "COLUMN_MASK"
    assert mod["maskType"] == "PARTIAL"
    assert mod["maskPattern"] == pattern
    assert mod["label"] == f"PARTIAL: {pattern}"

    listed = admin_client.get(f"/api/v1/admin/roles/{role.id}/permissions")
    listed_perm = next(
        p
        for p in listed.json()["data"]["permissions"]
        if p["id"] == perm["id"]
    )
    assert listed_perm["modifier"]["maskPattern"] == pattern


def test_grant_group_column_mask(
    admin_client: TestClient, db_session: Session
) -> None:
    path, _ = _analytics_column_path(db_session)
    ir = IdentityRepository(db_session)
    group = ir.create_group("Grant_Group_Mask")
    db_session.flush()

    grant = admin_client.post(
        f"/api/v1/admin/groups/{group.id}/permissions",
        json={
            "resourcePath": path,
            "resourceType": "COLUMN",
            "actions": ["SELECT"],
            "effect": "ALLOW",
            "columnMask": {
                "enabled": True,
                "maskType": "PARTIAL",
                "maskPattern": "***",
            },
        },
    )
    assert grant.status_code == 201
    assert grant.json()["data"]["created"][0]["modifier"]["maskType"] == "PARTIAL"
