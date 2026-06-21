"""M5: Assert seeded admin state matches contract §I snapshot (subset)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import PermissionType
from scripts.seed_demo_data import (
    _admin_demo_id,
    seed_admin_identity_demo,
    seed_data_scientist_role_permissions,
    seed_permission_wizard_modifier_demo,
    seed_role_catalog_permissions,
)

SNAPSHOT_PATH = Path(__file__).parent / "fixtures" / "admin_contract_snapshot.json"


@pytest.fixture(autouse=True)
def _permission_types(db_session: Session) -> None:
    for name in ("SELECT", "USAGE", "INSERT", "UPDATE", "DELETE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


@pytest.fixture
def snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def seeded_admin(db_session: Session) -> None:
    seed_admin_identity_demo(db_session)
    seed_data_scientist_role_permissions(db_session)
    seed_permission_wizard_modifier_demo(db_session)
    seed_role_catalog_permissions(db_session)
    db_session.flush()


def test_contract_snapshot_users_roles_groups(
    admin_client: TestClient, seeded_admin: None, snapshot: dict
) -> None:
    users = admin_client.get("/api/v1/admin/users?page=1&pageSize=50")
    assert users.status_code == 200
    user_rows = users.json()["data"]["data"]
    assert len(user_rows) == snapshot["users"]["count"]
    active = sum(1 for u in user_rows if u["status"] == "Active")
    assert active == snapshot["users"]["activeCount"]

    roles = admin_client.get("/api/v1/admin/roles?page=1&pageSize=50")
    role_rows = {r["id"]: r for r in roles.json()["data"]["data"]}
    for expected in snapshot["roles"]:
        rid = str(_admin_demo_id(expected["id"]))
        row = role_rows[rid]
        if "permissionCount" in expected:
            assert row["permissionCount"] == expected["permissionCount"]
        else:
            assert row["permissionCount"] >= expected["permissionCountMin"]

    groups = admin_client.get("/api/v1/admin/groups?page=1&pageSize=50")
    group_rows = {g["id"]: g for g in groups.json()["data"]["data"]}
    for expected in snapshot["groups"]:
        gid = str(_admin_demo_id(expected["id"]))
        row = group_rows[gid]
        if "roleCount" in expected:
            assert row["roleCount"] == expected["roleCount"]
        else:
            assert row["roleCount"] >= expected["roleCountMin"]


def test_contract_snapshot_grp_de_core(
    admin_client: TestClient, seeded_admin: None, snapshot: dict
) -> None:
    gid = _admin_demo_id("grp-de-core")
    spec = snapshot["grp-de-core"]

    members = admin_client.get(f"/api/v1/admin/groups/{gid}/members")
    assert len(members.json()["data"]) == spec["memberCount"]

    assigned = admin_client.get(f"/api/v1/admin/groups/{gid}/roles")
    assert len(assigned.json()["data"]) == spec["assignedRoleCount"]

    direct = admin_client.get(f"/api/v1/admin/groups/{gid}/permissions")
    assert len(direct.json()["data"]) == spec["directPermissionCount"]

    effective = admin_client.get(f"/api/v1/admin/groups/{gid}/effective-permissions")
    body = effective.json()["data"]
    assert body["summary"]["total"] >= spec["inheritedPermissionCountMin"]
    assert body["inheritedSummary"]["roleCount"] == spec["assignedRoleCount"]


def test_contract_snapshot_resource_tree(
    admin_client: TestClient, seeded_admin: None, snapshot: dict
) -> None:
    spec = snapshot["resourceTree"]
    response = admin_client.get("/api/v1/admin/resources/tree")
    assert response.status_code == 200
    tree = response.json()["data"]
    assert len(tree) >= spec["minTopLevelNodes"]
    names = {node["name"] for node in tree}
    for db_name in spec["databaseNames"]:
        assert db_name in names

    analytics = next(n for n in tree if n["name"] == "analytics_db")
    public = next(c for c in analytics["children"] if c["name"] == "public")
    users_tbl = next(c for c in public["children"] if c["name"] == "users")
    id_col = next(c for c in users_tbl["children"] if c["name"] == "id")
    assert id_col.get("isPrimaryKey") is True
    events_tbl = next(c for c in public["children"] if c["name"] == "events")
    user_id_col = next(c for c in events_tbl["children"] if c["name"] == "user_id")
    assert user_id_col.get("isForeignKey") is True


def test_contract_snapshot_data_scientist_permission_modifiers(
    admin_client: TestClient, seeded_admin: None
) -> None:
    role_id = _admin_demo_id("role-data-scientist-eu")
    response = admin_client.get(f"/api/v1/admin/roles/{role_id}/permissions")
    assert response.status_code == 200
    perms = response.json()["data"]["permissions"]
    row_perms = [
        p
        for p in perms
        if p.get("modifier", {}) and p["modifier"].get("type") == "ROW_FILTER"
    ]
    assert len(row_perms) >= 1
    for row_perm in row_perms:
        assert (
            row_perm["modifier"]["label"]
            == row_perm["modifier"]["conditionExpression"]
        )
        assert row_perm["modifier"]["conditionExpression"]

    wizard_table = next(
        p for p in row_perms if p["modifier"]["conditionExpression"] == "tenant_id = 1"
    )
    assert len(wizard_table["path"]) == 3

    mask_perms = [
        p
        for p in perms
        if p.get("modifier", {}) and p["modifier"].get("type") == "COLUMN_MASK"
    ]
    assert len(mask_perms) >= 1
    wizard_mask = next(
        p for p in mask_perms if p["modifier"].get("maskPattern") == "091-XXX-XXXX"
    )
    assert wizard_mask["modifier"]["maskType"] == "PARTIAL"
    assert wizard_mask["modifier"]["label"] == "PARTIAL: 091-XXX-XXXX"
    assert len(wizard_mask["path"]) == 4


def test_resource_tree_epic3_shape_unchanged(
    admin_client: TestClient, seeded_admin: None
) -> None:
    response = admin_client.get("/api/v1/admin/resources/mvp-tree")
    assert response.status_code == 200
    body = response.json()
    assert "databases" in body
    assert isinstance(body["databases"], list)
