"""M4: Admin Group Management API (contract §F, §H #25–40)."""

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
from scripts.seed_demo_data import (
    seed_admin_identity_demo,
    seed_data_scientist_role_permissions,
    seed_role_catalog_permissions,
)


@pytest.fixture(autouse=True)
def _types(db_session: Session) -> None:
    for name in ("SELECT", "USAGE", "INSERT", "UPDATE", "DELETE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


def test_group_crud_and_members(admin_client: TestClient, db_session: Session) -> None:
    create = admin_client.post(
        "/api/v1/admin/groups",
        json={"name": "M4 Test Group", "description": "desc"},
    )
    assert create.status_code == 201
    gid = create.json()["data"]["id"]

    ir = IdentityRepository(db_session)
    user = ir.create_user("gmember", "g@example.com", full_name="Group Member")
    db_session.flush()

    add = admin_client.post(
        f"/api/v1/admin/groups/{gid}/members",
        json={"memberIds": [str(user.id)]},
    )
    assert add.status_code == 200

    members = admin_client.get(f"/api/v1/admin/groups/{gid}/members")
    assert members.status_code == 200
    assert len(members.json()["data"]) == 1

    remove = admin_client.delete(f"/api/v1/admin/groups/{gid}/members/{user.id}")
    assert remove.status_code == 200

    delete = admin_client.delete(f"/api/v1/admin/groups/{gid}")
    assert delete.status_code == 200


def test_grp_de_core_effective_permissions(
    admin_client: TestClient, db_session: Session
) -> None:
    seed_admin_identity_demo(db_session)
    seed_data_scientist_role_permissions(db_session)
    seed_role_catalog_permissions(db_session)
    db_session.flush()

    from scripts.seed_demo_data import _admin_demo_id

    gid = _admin_demo_id("grp-de-core")
    response = admin_client.get(
        f"/api/v1/admin/groups/{gid}/effective-permissions"
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["summary"]["total"] >= 10
    assert body["inheritedSummary"]["roleCount"] == 3
    role_owned = [p for p in body["permissions"] if p["ownership"] == "role"]
    assert len(role_owned) >= 8
    assert any(p["sourceRoleName"] for p in role_owned)


def test_cannot_delete_inherited_permission_via_group(
    admin_client: TestClient, db_session: Session
) -> None:
    seed_admin_identity_demo(db_session)
    seed_data_scientist_role_permissions(db_session)
    db_session.flush()

    from scripts.seed_demo_data import _admin_demo_id

    gid = _admin_demo_id("grp-de-core")
    perm_id = _admin_demo_id("perm-db-1")
    response = admin_client.delete(
        f"/api/v1/admin/groups/{gid}/permissions/{perm_id}"
    )
    assert response.status_code == 403
    assert response.json()["data"]["code"] == "PERMISSION_NOT_DIRECT"


def test_direct_group_permission_crud(
    admin_client: TestClient, db_session: Session
) -> None:
    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    db_rid = rr.find_database_resource_id_by_name("marketing_db")
    assert db_rid is not None

    ir = IdentityRepository(db_session)
    group = ir.create_group("PermGroup")
    db_session.flush()

    grant = admin_client.post(
        f"/api/v1/admin/groups/{group.id}/permissions",
        json={
            "resourcePath": [
                {"id": str(db_rid), "name": "marketing_db", "type": "database"},
            ],
            "resourceType": "database",
            "actions": ["USAGE"],
            "effect": "ALLOW",
        },
    )
    assert grant.status_code == 201
    perm_id = grant.json()["data"]["created"][0]["id"]

    direct = admin_client.get(f"/api/v1/admin/groups/{group.id}/permissions")
    assert len(direct.json()["data"]) == 1

    delete = admin_client.delete(
        f"/api/v1/admin/groups/{group.id}/permissions/{perm_id}"
    )
    assert delete.status_code == 200
