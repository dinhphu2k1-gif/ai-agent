"""M3: Admin Role Management API (contract §E, §H #9–24)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import PermissionType
from app.repositories.identity_repo import IdentityRepository
from app.repositories.resource_repo import ResourceRepository
from scripts.seed_demo_data import (
    seed_data_scientist_role_permissions,
    seed_permission_wizard_resource_tree,
)


@pytest.fixture(autouse=True)
def _permission_types(db_session: Session) -> None:
    for name in ("SELECT", "USAGE", "INSERT", "UPDATE", "DELETE", "DESCRIBE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


def test_role_crud_duplicate_and_delete_conflict(
    admin_client: TestClient, db_session: Session
) -> None:
    create = admin_client.post(
        "/api/v1/admin/roles", json={"name": "Role_M3_Test"}
    )
    assert create.status_code == 201
    role_id = create.json()["data"]["id"]
    assert create.json()["data"]["permissionCount"] == 0

    dup = admin_client.post(f"/api/v1/admin/roles/{role_id}/duplicate")
    assert dup.status_code == 201
    copy = dup.json()["data"]
    assert copy["userCount"] == 0
    assert copy["groupCount"] == 0

    patch = admin_client.patch(
        f"/api/v1/admin/roles/{role_id}", json={"name": "Role_M3_Renamed"}
    )
    assert patch.status_code == 200

    ir = IdentityRepository(db_session)
    role_uuid = uuid.UUID(role_id)
    user = ir.create_user("m3user", "m3@example.com")
    ir.add_user_role(user.id, role_uuid)
    db_session.flush()

    blocked = admin_client.delete(f"/api/v1/admin/roles/{role_uuid}")
    assert blocked.status_code == 409
    assert blocked.json()["data"]["code"] == "ENTITY_IN_USE"

    ir.remove_user_role(user.id, role_uuid)
    db_session.flush()
    ok_delete = admin_client.delete(f"/api/v1/admin/roles/{role_uuid}")
    assert ok_delete.status_code == 200


def test_data_scientist_eight_permissions(
    admin_client: TestClient, db_session: Session
) -> None:
    from scripts.seed_demo_data import _admin_demo_id

    seed_data_scientist_role_permissions(db_session)
    db_session.flush()

    role_id = _admin_demo_id("role-data-scientist-eu")
    response = admin_client.get(f"/api/v1/admin/roles/{role_id}/permissions")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    perms = body["data"]["permissions"]
    assert len(perms) == 8
    assert body["data"]["summary"]["denyCount"] == 1
    deny = next(p for p in perms if p["effect"] == "DENY")
    assert deny["isHighlighted"] is True

    dup = admin_client.post(f"/api/v1/admin/roles/{role_id}/duplicate")
    assert dup.status_code == 201
    copy_id = dup.json()["data"]["id"]
    copy_perms = admin_client.get(f"/api/v1/admin/roles/{copy_id}/permissions")
    assert len(copy_perms.json()["data"]["permissions"]) == 8
    actors = admin_client.get(f"/api/v1/admin/roles/{copy_id}/actors")
    assert actors.json()["data"]["users"] == []


def test_grant_and_delete_permission(
    admin_client: TestClient, db_session: Session
) -> None:
    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    db_rid = rr.find_database_resource_id_by_name("analytics_db")
    sch_rid = rr.find_schema_resource_id(db_rid, "public")
    tbl_rid = rr.find_table_resource_id(sch_rid, "users")
    assert tbl_rid is not None

    ir = IdentityRepository(db_session)
    role = ir.create_role("Grant_Test")
    db_session.flush()

    grant = admin_client.post(
        f"/api/v1/admin/roles/{role.id}/permissions",
        json={
            "resourcePath": [
                {"id": str(db_rid), "name": "analytics_db", "type": "database"},
                {"id": str(sch_rid), "name": "public", "type": "schema"},
                {"id": str(tbl_rid), "name": "users", "type": "table"},
            ],
            "resourceType": "table",
            "actions": ["SELECT"],
            "effect": "ALLOW",
        },
    )
    assert grant.status_code == 201
    created = grant.json()["data"]["created"]
    assert len(created) == 1
    perm_id = created[0]["id"]

    delete = admin_client.delete(
        f"/api/v1/admin/roles/{role.id}/permissions/{perm_id}"
    )
    assert delete.status_code == 200


def test_role_actors_and_catalogs(admin_client: TestClient, db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    role = ir.create_role("Actors_Test")
    user = ir.create_user("actor1", "a1@example.com", full_name="Actor One")
    group = ir.create_group("Actors Group")
    ir.add_user_role(user.id, role.id)
    ir.add_group_role(group.id, role.id)
    db_session.flush()

    actors = admin_client.get(f"/api/v1/admin/roles/{role.id}/actors")
    assert actors.status_code == 200
    data = actors.json()["data"]
    assert len(data["users"]) == 1
    assert len(data["groups"]) == 1

    users_cat = admin_client.get("/api/v1/admin/users/catalog?page=1&pageSize=10")
    assert users_cat.status_code == 200
    assert users_cat.json()["data"]["totalItems"] >= 1

    groups_cat = admin_client.get("/api/v1/admin/groups/catalog?page=1&pageSize=10")
    assert groups_cat.status_code == 200
    assert groups_cat.json()["data"]["totalItems"] >= 1
