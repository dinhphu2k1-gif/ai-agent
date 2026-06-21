"""M4: EffectivePermissionService merge and DENY-wins."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import PermissionType
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.services.effective_permission_service import EffectivePermissionService


@pytest.fixture(autouse=True)
def _types(db_session: Session) -> None:
    for name in ("SELECT", "USAGE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


def test_direct_only_group_permissions(db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    pr = PermissionRepository(db_session)
    rr = ResourceRepository(db_session)
    group = ir.create_group("DirectOnly")
    res = rr.create_resource("DATABASE")
    db = rr.create_database(res.id, "db_a", None)
    ptype = pr.get_permission_type_by_name("USAGE")
    assert ptype is not None
    perm = pr.create_permission(
        resource_id=db.resource_id, permission_type_id=ptype.id, effect="ALLOW"
    )
    ir.add_group_permission(group.id, perm.id)
    db_session.flush()

    data = EffectivePermissionService(db_session).get_effective_permissions(group.id)
    assert data is not None
    assert len(data.permissions) == 1
    assert data.permissions[0].ownership == "group"
    assert data.permissions[0].source_role_name == "Direct"


def test_inherited_from_role(db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    pr = PermissionRepository(db_session)
    rr = ResourceRepository(db_session)
    group = ir.create_group("Inherited")
    role = ir.create_role("R1", display_name="Role One")
    ir.add_group_role(group.id, role.id)
    res = rr.create_resource("DATABASE")
    db = rr.create_database(res.id, "db_b", None)
    ptype = pr.get_permission_type_by_name("SELECT")
    assert ptype is not None
    perm = pr.create_permission(
        resource_id=db.resource_id, permission_type_id=ptype.id, effect="ALLOW"
    )
    ir.add_role_permission(role.id, perm.id)
    db_session.flush()

    data = EffectivePermissionService(db_session).get_effective_permissions(group.id)
    assert data is not None
    assert len(data.permissions) == 1
    assert data.permissions[0].ownership == "role"
    assert data.permissions[0].source_role_name == "Role One"


def test_deny_wins_on_same_resource_action(db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    pr = PermissionRepository(db_session)
    rr = ResourceRepository(db_session)
    group = ir.create_group("DenyWins")
    role = ir.create_role("R2", display_name="Role Two")
    ir.add_group_role(group.id, role.id)
    res = rr.create_resource("DATABASE")
    db = rr.create_database(res.id, "shared_db", None)
    ptype = pr.get_permission_type_by_name("SELECT")
    assert ptype is not None
    allow = pr.create_permission(
        resource_id=db.resource_id, permission_type_id=ptype.id, effect="ALLOW"
    )
    deny = pr.create_permission(
        resource_id=db.resource_id, permission_type_id=ptype.id, effect="DENY"
    )
    ir.add_role_permission(role.id, allow.id)
    ir.add_group_permission(group.id, deny.id)
    db_session.flush()

    data = EffectivePermissionService(db_session).get_effective_permissions(group.id)
    assert data is not None
    assert len(data.permissions) == 1
    assert data.permissions[0].effect == "DENY"
    assert data.summary.deny_count == 1
