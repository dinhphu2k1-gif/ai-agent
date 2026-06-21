"""M2: admin user management API."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.cache.invalidation import get_permission_version
from app.repositories.identity_repo import IdentityRepository


def test_list_users_envelope(admin_client: TestClient, db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    user = ir.create_user("john", "john@example.com", full_name="John Doe")
    role = ir.create_role("AdminRole", display_name="Admin")
    group = ir.create_group("Data Science")
    ir.add_user_role(user.id, role.id)
    ir.add_user_to_group(user.id, group.id)
    db_session.flush()

    response = admin_client.get("/api/v1/admin/users?page=1&pageSize=10")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["totalItems"] >= 1
    row = next(
        item for item in body["data"]["data"] if item["email"] == "john@example.com"
    )
    assert row["roles"] == ["Admin"]
    assert "Data Science" in row["groups"]
    assert row["status"] == "Active"


def test_list_users_status_inactive(admin_client: TestClient, db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    ir.create_user("active", "active@example.com", is_active=True)
    ir.create_user("inactive", "inactive@example.com", is_active=False)
    db_session.flush()

    response = admin_client.get(
        "/api/v1/admin/users?page=1&pageSize=10&status=Inactive"
    )
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()["data"]["data"]]
    assert "inactive@example.com" in emails
    assert "active@example.com" not in emails


def test_create_user_with_groups_and_roles(
    admin_client: TestClient, db_session: Session
) -> None:
    ir = IdentityRepository(db_session)
    ir.create_group("Alpha Team")
    ir.create_role("EditorRole", display_name="Editor")
    db_session.flush()

    version_before = get_permission_version()
    response = admin_client.post(
        "/api/v1/admin/users",
        json={
            "fullName": "Jane Doe",
            "email": "jane@example.com",
            "username": "jane.doe",
            "groups": ["Alpha Team"],
            "roles": ["Editor"],
            "isActive": True,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert get_permission_version() > version_before

    user_id = payload["data"]["id"]
    detail = admin_client.get(f"/api/v1/admin/users/{user_id}")
    assert detail.status_code == 200
    data = detail.json()["data"]
    assert data["email"] == "jane@example.com"
    assert data["groups"][0]["name"] == "Alpha Team"
    assert data["roles"][0]["name"] == "Editor"


def test_get_user_not_found_envelope(admin_client: TestClient) -> None:
    missing = uuid.uuid4()
    response = admin_client.get(f"/api/v1/admin/users/{missing}")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["data"]["code"] == "NOT_FOUND"


def test_bulk_assign_roles_idempotent(
    admin_client: TestClient, db_session: Session
) -> None:
    ir = IdentityRepository(db_session)
    user = ir.create_user("bulk", "bulk@example.com")
    role = ir.create_role("BulkRole", display_name="Bulk Role")
    db_session.flush()

    body = {
        "userIds": [str(user.id)],
        "roleIds": [str(role.id)],
    }
    first = admin_client.post("/api/v1/admin/users/bulk/assign-roles", json=body)
    second = admin_client.post("/api/v1/admin/users/bulk/assign-roles", json=body)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["updatedCount"] == 1
    assert second.json()["data"]["updatedCount"] == 0


def test_bulk_deactivate(admin_client: TestClient, db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    user = ir.create_user("deact", "deact@example.com", is_active=True)
    db_session.flush()

    response = admin_client.post(
        "/api/v1/admin/users/bulk/deactivate",
        json={"userIds": [str(user.id)]},
    )
    assert response.status_code == 200
    assert response.json()["data"]["updatedCount"] == 1
    assert ir.get_user(user.id).is_active is False


def test_role_assign_and_unassign_user(
    admin_client: TestClient, db_session: Session
) -> None:
    ir = IdentityRepository(db_session)
    user = ir.create_user("actor", "actor@example.com")
    role = ir.create_role("ActorRole", display_name="Actor")
    db_session.flush()

    assign = admin_client.post(
        f"/api/v1/admin/roles/{role.id}/users",
        json={"userIds": [str(user.id)]},
    )
    assert assign.status_code == 200

    detail = admin_client.get(f"/api/v1/admin/users/{user.id}")
    assert detail.json()["data"]["roles"][0]["name"] == "Actor"

    remove = admin_client.delete(f"/api/v1/admin/roles/{role.id}/users/{user.id}")
    assert remove.status_code == 200
    assert remove.json()["data"]["removed"] is True

    detail2 = admin_client.get(f"/api/v1/admin/users/{user.id}")
    assert detail2.json()["data"]["roles"] == []


def test_group_and_role_options(admin_client: TestClient, db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    ir.create_group("Engineering")
    ir.create_role("ViewerRole", display_name="Viewer")
    db_session.flush()

    groups = admin_client.get("/api/v1/admin/groups/options")
    roles = admin_client.get("/api/v1/admin/roles/options")
    assert groups.status_code == 200
    assert roles.status_code == 200
    assert "Engineering" in groups.json()["data"]["groups"]
    assert "Viewer" in roles.json()["data"]["roles"]
