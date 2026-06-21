"""Epic 3: admin API integration (SQLite + dependency override)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache.invalidation import get_permission_version
from app.models.permission import PermissionType
from app.repositories.identity_repo import IdentityRepository
from app.repositories.resource_repo import ResourceRepository


@pytest.fixture(autouse=True)
def _seed_select_type(db_session: Session) -> None:
    existing = db_session.scalar(
        select(PermissionType).where(PermissionType.name == "SELECT")
    )
    if existing is None:
        db_session.add(PermissionType(name="SELECT"))
        db_session.flush()


def _select_type_id(db_session: Session) -> uuid.UUID:
    return db_session.scalars(
        select(PermissionType.id).where(PermissionType.name == "SELECT")
    ).one()


def test_admin_resource_tree_and_permission_happy_path(
    admin_client: TestClient, db_session: Session
) -> None:
    v0 = get_permission_version()
    r = admin_client.post(
        "/api/v1/admin/resources/databases",
        json={"name": "analytics", "description": "main"},
    )
    assert r.status_code == 201
    db_id = uuid.UUID(r.json()["resource_id"])

    r = admin_client.post(
        "/api/v1/admin/resources/schemas",
        json={"database_id": str(db_id), "name": "public"},
    )
    assert r.status_code == 201
    schema_id = uuid.UUID(r.json()["resource_id"])

    r = admin_client.post(
        "/api/v1/admin/resources/tables",
        json={"schema_id": str(schema_id), "name": "customers"},
    )
    assert r.status_code == 201
    table_id = uuid.UUID(r.json()["resource_id"])

    r = admin_client.post(
        "/api/v1/admin/resources/columns",
        json={
            "table_id": str(table_id),
            "name": "email",
            "data_type": "text",
        },
    )
    assert r.status_code == 201

    tree = admin_client.get("/api/v1/admin/resources/mvp-tree")
    assert tree.status_code == 200
    body = tree.json()
    assert len(body["databases"]) == 1
    assert body["databases"][0]["name"] == "analytics"
    assert body["databases"][0]["schemas"][0]["tables"][0]["columns"][0]["name"] == "email"

    pt_id = _select_type_id(db_session)
    r = admin_client.post(
        "/api/v1/admin/permissions",
        json={
            "resource_id": str(table_id),
            "permission_type_id": str(pt_id),
            "effect": "ALLOW",
        },
    )
    assert r.status_code == 201
    perm_id = uuid.UUID(r.json()["id"])
    assert get_permission_version() > v0

    r = admin_client.patch(
        f"/api/v1/admin/permissions/{perm_id}",
        json={"effect": "DENY"},
    )
    assert r.status_code == 200
    assert r.json()["effect"] == "DENY"

    r = admin_client.post(
        f"/api/v1/admin/permissions/{perm_id}/row-filters",
        json={"condition_expr": "tenant_id = current_setting('app.tenant_id')"},
    )
    assert r.status_code == 201

    r = admin_client.post(
        f"/api/v1/admin/permissions/{perm_id}/column-masks",
        json={"mask_type": "PARTIAL", "mask_pattern": None},
    )
    assert r.status_code == 201

    ir = IdentityRepository(db_session)
    user = ir.create_user("alice", "alice@example.com")
    group = ir.create_group("analysts")
    role = ir.create_role("reader")
    db_session.commit()

    r = admin_client.post(
        f"/api/v1/admin/assignments/users/{user.id}/permissions",
        json={"permission_id": str(perm_id), "granted_by": "bootstrap"},
    )
    assert r.status_code == 201

    r = admin_client.post(
        f"/api/v1/admin/assignments/groups/{group.id}/permissions",
        json={"permission_id": str(perm_id)},
    )
    assert r.status_code == 201

    r = admin_client.post(
        f"/api/v1/admin/assignments/roles/{role.id}/permissions",
        json={"permission_id": str(perm_id)},
    )
    assert r.status_code == 201

    r = admin_client.post(
        f"/api/v1/admin/assignments/users/{user.id}/groups",
        json={"group_id": str(group.id)},
    )
    assert r.status_code == 201

    r = admin_client.post(
        f"/api/v1/admin/assignments/users/{user.id}/roles",
        json={"role_id": str(role.id)},
    )
    assert r.status_code == 201

    r = admin_client.post(
        f"/api/v1/admin/assignments/groups/{group.id}/roles",
        json={"role_id": str(role.id)},
    )
    assert r.status_code == 201

    logs = admin_client.get("/api/v1/admin/audit/permission-change-logs?limit=50")
    assert logs.status_code == 200
    entries = logs.json()
    assert len(entries) >= 8
    types = {e["change_type"] for e in entries}
    assert "PERMISSION_CREATE" in types
    assert "USER_PERMISSION_ASSIGN" in types


def test_schema_not_found(admin_client: TestClient) -> None:
    r = admin_client.post(
        "/api/v1/admin/resources/schemas",
        json={"database_id": str(uuid.uuid4()), "name": "x"},
    )
    assert r.status_code == 404


def test_validation_error_shape(admin_client: TestClient) -> None:
    r = admin_client.post("/api/v1/admin/resources/databases", json={"name": ""})
    assert r.status_code == 400
    assert r.json()["code"] == "bad_request"


def test_custom_mask_requires_pattern(admin_client: TestClient, db_session: Session) -> None:
    rr = ResourceRepository(db_session)
    r_db = rr.create_resource("DATABASE")
    rr.create_database(r_db.id, "d", None)
    r_sch = rr.create_resource("SCHEMA")
    rr.create_schema(r_sch.id, r_db.id, "p")
    r_tbl = rr.create_resource("TABLE")
    rr.create_table(r_tbl.id, r_sch.id, "t")
    db_session.commit()

    pt_id = _select_type_id(db_session)
    pr = admin_client.post(
        "/api/v1/admin/permissions",
        json={
            "resource_id": str(r_tbl.id),
            "permission_type_id": str(pt_id),
            "effect": "ALLOW",
        },
    )
    perm_id = pr.json()["id"]
    r = admin_client.post(
        f"/api/v1/admin/permissions/{perm_id}/column-masks",
        json={"mask_type": "CUSTOM", "mask_pattern": None},
    )
    assert r.status_code == 400
    detail = r.json().get("detail", "")
    assert "CUSTOM" in str(detail) or "mask_pattern" in str(detail)


def test_duplicate_membership_integrity(admin_client: TestClient, db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    u = ir.create_user("bob", "bob@example.com")
    g = ir.create_group("g1")
    db_session.commit()

    admin_client.post(
        f"/api/v1/admin/assignments/users/{u.id}/groups",
        json={"group_id": str(g.id)},
    )
    r2 = admin_client.post(
        f"/api/v1/admin/assignments/users/{u.id}/groups",
        json={"group_id": str(g.id)},
    )
    assert r2.status_code == 400
    assert r2.json()["code"] == "bad_request"
