"""Phase 0: row_filters unique, permission_types DESCRIBE, permissions effect CHECK."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.permission import Permission, PermissionType, RowFilter
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository


@pytest.fixture
def seed_permission_types(db_session: Session) -> None:
    for name in ("SELECT", "USAGE", "INSERT", "UPDATE", "DELETE", "DESCRIBE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


def test_permission_types_include_select_and_describe(
    db_session: Session, seed_permission_types: None
) -> None:
    names = set(db_session.scalars(select(PermissionType.name)).all())
    assert "SELECT" in names
    assert "DESCRIBE" in names


def test_row_filters_unique_per_permission(
    db_session: Session, seed_permission_types: None
) -> None:
    assert "uq_row_filters_permission_id" in {
        c.name for c in RowFilter.__table__.constraints
    }

    rr = ResourceRepository(db_session)
    pr = PermissionRepository(db_session)
    pt_id = db_session.scalars(
        select(PermissionType.id).where(PermissionType.name == "SELECT")
    ).one()

    res = rr.create_resource("TABLE")
    db_res = rr.create_resource("DATABASE")
    rr.create_database(db_res.id, f"phase0_{uuid.uuid4().hex[:8]}", None)
    sch_res = rr.create_resource("SCHEMA")
    rr.create_schema(sch_res.id, db_res.id, "public")
    rr.create_table(res.id, sch_res.id, "t_phase0_unique")

    perm = pr.create_permission(
        resource_id=res.id, permission_type_id=pt_id, effect="ALLOW"
    )
    pr.create_row_filter(permission_id=perm.id, condition_expr="1 = 1")
    db_session.flush()

    with pytest.raises(IntegrityError):
        db_session.add(
            RowFilter(permission_id=perm.id, condition_expr="2 = 2")
        )
        db_session.flush()
    db_session.rollback()


def test_permissions_effect_check_rejects_invalid(
    db_session: Session, seed_permission_types: None
) -> None:
    rr = ResourceRepository(db_session)
    pr = PermissionRepository(db_session)
    pt_id = db_session.scalars(
        select(PermissionType.id).where(PermissionType.name == "SELECT")
    ).one()

    res = rr.create_resource("TABLE")
    db_res = rr.create_resource("DATABASE")
    rr.create_database(db_res.id, f"phase0_eff_{uuid.uuid4().hex[:8]}", None)
    sch_res = rr.create_resource("SCHEMA")
    rr.create_schema(sch_res.id, db_res.id, "public")
    rr.create_table(res.id, sch_res.id, "t_phase0_effect")

    with pytest.raises(IntegrityError):
        db_session.add(
            Permission(
                resource_id=res.id,
                permission_type_id=pt_id,
                effect="FOO",
            )
        )
        db_session.flush()
    db_session.rollback()
