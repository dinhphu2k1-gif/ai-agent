"""M3: PermissionPresenter path and modifier mapping."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import PermissionType
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.services.permission_presenter import PermissionPresenter, build_path_labels


@pytest.fixture(autouse=True)
def _permission_types(db_session: Session) -> None:
    for name in ("SELECT", "USAGE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


def _build_tree(db_session: Session) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
    rr = ResourceRepository(db_session)
    res_db = rr.create_resource("DATABASE")
    db = rr.create_database(res_db.id, "prod_eu_central", None)
    res_sch = rr.create_resource("SCHEMA")
    sch = rr.create_schema(res_sch.id, db.resource_id, "analytics")
    res_tbl = rr.create_resource("TABLE")
    tbl = rr.create_table(res_tbl.id, sch.resource_id, "users")
    res_col = rr.create_resource("COLUMN")
    col = rr.create_column(res_col.id, tbl.resource_id, "email", "text")
    db_session.flush()
    return db.resource_id, sch.resource_id, tbl.resource_id, col.resource_id


def test_build_path_labels_four_levels(db_session: Session) -> None:
    rr = ResourceRepository(db_session)
    db_id, sch_id, tbl_id, col_id = _build_tree(db_session)

    db_path = build_path_labels(rr, db_id)
    assert [p.label for p in db_path] == ["prod_eu_central"]

    sch_path = build_path_labels(rr, sch_id)
    assert [p.label for p in sch_path] == ["prod_eu_central", "analytics"]

    tbl_path = build_path_labels(rr, tbl_id)
    assert [p.label for p in tbl_path] == ["prod_eu_central", "analytics", "users"]
    assert [p.resource_id for p in tbl_path] == [
        str(db_id),
        str(sch_id),
        str(tbl_id),
    ]

    col_path = build_path_labels(rr, col_id)
    assert [p.label for p in col_path] == [
        "prod_eu_central",
        "analytics",
        "users",
        "email",
    ]
    assert len(col_path) == 4
    assert col_path[-1].resource_id == str(col_id)


def test_to_fe_permission_deny_highlight_and_modifier(db_session: Session) -> None:
    rr = ResourceRepository(db_session)
    pr = PermissionRepository(db_session)
    ir = IdentityRepository(db_session)
    _, sch_id, tbl_id, _ = _build_tree(db_session)

    role = ir.create_role("Presenter_Role")
    ptype = pr.get_permission_type_by_name("SELECT")
    assert ptype is not None
    perm = pr.create_permission(
        resource_id=tbl_id,
        permission_type_id=ptype.id,
        effect="DENY",
    )
    ir.add_role_permission(role.id, perm.id)
    pr.create_row_filter(permission_id=perm.id, condition_expr="1=1")
    db_session.flush()

    presenter = PermissionPresenter(rr, pr)
    fe = presenter.to_fe_permission(perm)
    assert fe.resource_type == "TABLE"
    assert fe.effect == "DENY"
    assert fe.is_highlighted is True
    assert fe.modifier is not None
    assert fe.modifier.type == "ROW_FILTER"
    assert fe.modifier.label == "1=1"
    assert fe.modifier.condition_expression == "1=1"

    listed = presenter.list_for_role(role.id)
    assert listed.summary.total == 1
    assert listed.summary.deny_count == 1


def test_to_fe_permission_column_mask_partial_label(db_session: Session) -> None:
    rr = ResourceRepository(db_session)
    pr = PermissionRepository(db_session)
    _, _, _, col_id = _build_tree(db_session)
    ptype = pr.get_permission_type_by_name("SELECT")
    assert ptype is not None
    perm = pr.create_permission(
        resource_id=col_id,
        permission_type_id=ptype.id,
        effect="ALLOW",
    )
    pr.upsert_column_mask(
        permission_id=perm.id,
        mask_type="PARTIAL",
        mask_pattern="***@***.com",
    )
    db_session.flush()

    fe = PermissionPresenter(rr, pr).to_fe_permission(perm)
    assert fe.modifier is not None
    assert fe.modifier.type == "COLUMN_MASK"
    assert fe.modifier.label == "PARTIAL: ***@***.com"
    assert fe.modifier.mask_type == "PARTIAL"
    assert fe.modifier.mask_pattern == "***@***.com"
