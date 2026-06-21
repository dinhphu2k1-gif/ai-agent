"""Phase 6: lazy resource tree, mask runtime/preview alignment, inherited PUT guard."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import PermissionType

from app.core.config import get_settings
from app.repositories.resource_repo import ResourceRepository
from app.services.column_mask_engine import apply_partial_mask, mask_value
from app.services.masking_service import _apply_mask_value
from app.services.permission_validation_service import PermissionValidationService
from scripts.seed_demo_data import (
    seed_admin_identity_demo,
    seed_data_scientist_role_permissions,
    seed_permission_wizard_resource_tree,
)


def test_lazy_tree_children_one_level(
    admin_client: TestClient, db_session: Session
) -> None:
    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    db_id = rr.find_database_resource_id_by_name("analytics_db")
    sch_id = rr.find_schema_resource_id(db_id, "public")
    tbl_id = rr.find_table_resource_id(sch_id, "users")
    assert db_id and sch_id and tbl_id

    full = admin_client.get("/api/v1/admin/resources/tree")
    assert full.status_code == 200
    assert full.json()["data"][0]["children"] is not None

    schemas = admin_client.get(
        "/api/v1/admin/resources/tree",
        params={"parentId": str(db_id)},
    )
    assert schemas.status_code == 200
    names = {n["name"] for n in schemas.json()["data"]}
    assert "public" in names
    assert all(n.get("children") is None for n in schemas.json()["data"])

    tables = admin_client.get(
        "/api/v1/admin/resources/tree",
        params={"parentId": str(sch_id)},
    )
    assert tables.status_code == 200
    assert any(n["name"] == "users" for n in tables.json()["data"])

    columns = admin_client.get(
        "/api/v1/admin/resources/tree",
        params={"parentId": str(tbl_id)},
    )
    assert columns.status_code == 200
    assert any(n["name"] == "email" for n in columns.json()["data"])


def test_mask_runtime_matches_preview_partial_and_hash(db_session: Session) -> None:
    salt = get_settings().masking_hash_salt
    sample = "0912345678"
    pattern = "091-XXX-XXXX"
    preview = PermissionValidationService(db_session).preview_column_mask(
        "PARTIAL", pattern, sample
    )
    runtime = _apply_mask_value(sample, "PARTIAL", pattern, hash_salt=salt)
    assert preview.masked_value == runtime == apply_partial_mask(pattern, sample)

    preview_hash = PermissionValidationService(db_session).preview_column_mask(
        "HASH", None, sample
    )
    runtime_hash = _apply_mask_value(sample, "HASH", None, hash_salt=salt)
    assert preview_hash.masked_value == runtime_hash
    assert mask_value(sample, "HASH", None, hash_salt=salt, for_preview=True) == (
        runtime_hash
    )


def _ensure_permission_types(db_session: Session) -> None:
    for name in ("SELECT", "USAGE", "INSERT", "UPDATE", "DELETE", "DESCRIBE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


def test_cannot_update_inherited_permission_via_group(
    admin_client: TestClient, db_session: Session
) -> None:
    _ensure_permission_types(db_session)
    seed_admin_identity_demo(db_session)
    db_session.flush()

    from scripts.seed_demo_data import _admin_demo_id

    gid = _admin_demo_id("grp-de-core")
    perm_id = _admin_demo_id("perm-db-1")
    db_rid = ResourceRepository(db_session).find_database_resource_id_by_name(
        "prod_eu_central"
    )
    assert db_rid is not None
    response = admin_client.put(
        f"/api/v1/admin/groups/{gid}/permissions/{perm_id}",
        json={
            "resourcePath": [
                {
                    "id": str(db_rid),
                    "name": "prod_eu_central",
                    "type": "database",
                }
            ],
            "resourceType": "DATABASE",
            "actions": ["USAGE"],
            "effect": "ALLOW",
        },
    )
    assert response.status_code == 403
    assert response.json()["data"]["code"] == "PERMISSION_NOT_DIRECT"
