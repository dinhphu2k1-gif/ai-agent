"""Agri integration user seed — stable ids and COREDB permission actions."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.seed_agri_integration_user import (
    PERMISSION_ACTIONS,
    agri_stable_id,
    integration_username,
    seed_agri_integration_user,
)
from scripts.seed_gl_resource_dictionary import DATABASE_NAME, seed_gl_resource_dictionary


@pytest.fixture(autouse=True)
def _permission_types(db_session: Session) -> None:
    from app.models.permission import PermissionType

    for name in ("SELECT", "USAGE", "DESCRIBE", "INSERT", "UPDATE", "DELETE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


def test_stable_ids_deterministic() -> None:
    assert agri_stable_id("user-agri-agent") == agri_stable_id("user-agri-agent")


def test_seed_agri_user_requires_coredb(db_session: Session) -> None:
    with pytest.raises(RuntimeError, match="COREDB"):
        seed_agri_integration_user(db_session)


def test_seed_agri_user_with_catalog(db_session: Session) -> None:
    from app.models.identity import RolePermission
    from app.models.permission import Permission, PermissionType
    from app.repositories.identity_repo import IdentityRepository
    from app.repositories.resource_repo import ResourceRepository

    records = [
        {
            "record_type": "COLUMN",
            "database_name": DATABASE_NAME,
            "schema_name": "GL",
            "table_name": "GL_ACCOUNTS",
            "column_name": "ACCOUNT_ID",
            "data_type": "NUMBER",
        },
    ]
    seed_gl_resource_dictionary(db_session, records)
    info = seed_agri_integration_user(db_session)
    db_session.flush()

    assert info["username"] == integration_username()
    ir = IdentityRepository(db_session)
    rr = ResourceRepository(db_session)
    db_rid = rr.find_database_resource_id_by_name(DATABASE_NAME)
    assert db_rid is not None

    groups = ir.list_groups_for_user(info["user_id"])
    assert any(g.name == "agri_integration" for g in groups)

    roles = ir.list_roles_for_user(info["user_id"])
    assert any(r.name == "Agri_Integration_Reader" for r in roles)

    perm_ids = list(
        db_session.scalars(
            select(RolePermission.permission_id).where(
                RolePermission.role_id == info["role_id"]
            )
        ).all()
    )
    assert len(perm_ids) == len(PERMISSION_ACTIONS)

    type_names: set[str] = set()
    for pid in perm_ids:
        perm = db_session.get(Permission, pid)
        assert perm is not None
        assert perm.resource_id == db_rid
        assert perm.effect == "ALLOW"
        pname = db_session.scalars(
            select(PermissionType.name).where(
                PermissionType.id == perm.permission_type_id
            )
        ).one()
        type_names.add(pname)

    assert type_names == set(PERMISSION_ACTIONS)
