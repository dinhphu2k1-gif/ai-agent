"""Phase 1: PermissionGrantService validation and UUID path resolve."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.permission import PermissionType
from app.models.resource import Resource
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin_contract import (
    ColumnMaskGrant,
    PermissionGrantBody,
    ResourcePathSegment,
    RowFilterGrant,
)
from app.services.permission_grant_service import GrantValidationError, PermissionGrantService
from scripts.seed_demo_data import seed_permission_wizard_resource_tree


@pytest.fixture(autouse=True)
def _permission_types(db_session: Session) -> None:
    for name in ("SELECT", "USAGE", "INSERT", "UPDATE", "DELETE", "DESCRIBE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


@pytest.fixture
def analytics_users_path(db_session: Session) -> list[ResourcePathSegment]:
    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    db_rid = rr.find_database_resource_id_by_name("analytics_db")
    assert db_rid is not None
    sch_rid = rr.find_schema_resource_id(db_rid, "public")
    assert sch_rid is not None
    tbl_rid = rr.find_table_resource_id(sch_rid, "users")
    assert tbl_rid is not None
    return [
        ResourcePathSegment(id=str(db_rid), name="analytics_db", type="database"),
        ResourcePathSegment(id=str(sch_rid), name="public", type="schema"),
        ResourcePathSegment(id=str(tbl_rid), name="users", type="table"),
    ]


def _grant_svc(db_session: Session) -> PermissionGrantService:
    return PermissionGrantService(
        db_session,
        ResourceRepository(db_session),
        PermissionRepository(db_session),
    )


def test_resolve_valid_table_path(
    db_session: Session, analytics_users_path: list[ResourcePathSegment]
) -> None:
    body = PermissionGrantBody(
        resourcePath=analytics_users_path,
        resourceType="TABLE",
        actions=["SELECT"],
        effect="ALLOW",
    )
    rid = _grant_svc(db_session).resolve_resource_id(body)
    assert rid == uuid.UUID(analytics_users_path[-1].id)


def test_resolve_wrong_path_order(db_session: Session) -> None:
    body = PermissionGrantBody(
        resourcePath=[
            ResourcePathSegment(id=str(uuid.uuid4()), name="t", type="table"),
        ],
        resourceType="TABLE",
        actions=["SELECT"],
        effect="ALLOW",
    )
    with pytest.raises(GrantValidationError) as exc:
        _grant_svc(db_session).resolve_resource_id(body)
    assert exc.value.code == "BAD_REQUEST"


def test_resolve_unknown_id_not_found(
    db_session: Session, analytics_users_path: list[ResourcePathSegment]
) -> None:
    bad_path = list(analytics_users_path)
    bad_path[0] = ResourcePathSegment(
        id=str(uuid.uuid4()), name="analytics_db", type="database"
    )
    body = PermissionGrantBody(
        resourcePath=bad_path,
        resourceType="TABLE",
        actions=["SELECT"],
        effect="ALLOW",
    )
    with pytest.raises(GrantValidationError) as exc:
        _grant_svc(db_session).resolve_resource_id(body)
    assert exc.value.status == 404
    assert exc.value.code == "RESOURCE_NOT_FOUND"


@pytest.mark.parametrize(
    "body_kwargs,code",
    [
        ({"actions": []}, "BAD_REQUEST"),
        ({"actions": ["NOT_A_REAL_ACTION"]}, "INVALID_ACTION"),
        (
            {
                "rowFilter": RowFilterGrant(enabled=True, conditionExpression=""),
            },
            "BAD_REQUEST",
        ),
        (
            {
                "columnMask": ColumnMaskGrant(
                    enabled=True, maskType="PARTIAL", maskPattern=""
                ),
            },
            "BAD_REQUEST",
        ),
    ],
)
def test_validate_grant_errors(
    db_session: Session,
    analytics_users_path: list[ResourcePathSegment],
    body_kwargs: dict,
    code: str,
) -> None:
    base = dict(
        resourcePath=analytics_users_path,
        resourceType="TABLE",
        actions=["SELECT"],
        effect="ALLOW",
    )
    if "columnMask" in body_kwargs:
        base["resourceType"] = "COLUMN"
        seed_permission_wizard_resource_tree(db_session)
        rr = ResourceRepository(db_session)
        db_rid = rr.find_database_resource_id_by_name("analytics_db")
        sch_rid = rr.find_schema_resource_id(db_rid, "public")
        tbl_rid = rr.find_table_resource_id(sch_rid, "users")
        col_rid = rr.find_column_resource_id(tbl_rid, "email")
        assert col_rid is not None
        base["resourcePath"] = [
            ResourcePathSegment(id=str(db_rid), name="analytics_db", type="database"),
            ResourcePathSegment(id=str(sch_rid), name="public", type="schema"),
            ResourcePathSegment(id=str(tbl_rid), name="users", type="table"),
            ResourcePathSegment(id=str(col_rid), name="email", type="column"),
        ]
    base.update(body_kwargs)
    body = PermissionGrantBody(**base)
    with pytest.raises(GrantValidationError) as exc:
        _grant_svc(db_session).validate_grant(body)
    assert exc.value.code == code


def test_invalid_modifier_row_filter_on_column(
    db_session: Session, analytics_users_path: list[ResourcePathSegment]
) -> None:
    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    db_rid = rr.find_database_resource_id_by_name("analytics_db")
    sch_rid = rr.find_schema_resource_id(db_rid, "public")
    tbl_rid = rr.find_table_resource_id(sch_rid, "users")
    col_rid = rr.find_column_resource_id(tbl_rid, "email")
    assert col_rid is not None
    body = PermissionGrantBody(
        resourcePath=[
            ResourcePathSegment(id=str(db_rid), name="analytics_db", type="database"),
            ResourcePathSegment(id=str(sch_rid), name="public", type="schema"),
            ResourcePathSegment(id=str(tbl_rid), name="users", type="table"),
            ResourcePathSegment(id=str(col_rid), name="email", type="column"),
        ],
        resourceType="COLUMN",
        actions=["SELECT"],
        effect="ALLOW",
        rowFilter=RowFilterGrant(enabled=True, conditionExpression="x = 1"),
    )
    with pytest.raises(GrantValidationError) as exc:
        _grant_svc(db_session).validate_grant(body)
    assert exc.value.code == "INVALID_MODIFIER"


def test_grant_does_not_create_catalog_resources(
    db_session: Session, analytics_users_path: list[ResourcePathSegment]
) -> None:
    before = db_session.scalar(select(func.count()).select_from(Resource)) or 0
    ir = IdentityRepository(db_session)
    role = ir.create_role("No_Auto_Create")
    db_session.flush()
    svc = _grant_svc(db_session)
    bad = PermissionGrantBody(
        resourcePath=[
            ResourcePathSegment(id=str(uuid.uuid4()), name="x", type="database"),
        ],
        resourceType="DATABASE",
        actions=["SELECT"],
        effect="ALLOW",
    )
    with pytest.raises(GrantValidationError):
        svc.apply_grant_role(role.id, bad, ir)
    after = db_session.scalar(select(func.count()).select_from(Resource)) or 0
    assert after == before


def test_api_grant_missing_row_filter_expression_400(
    admin_client,
    db_session: Session,
    analytics_users_path: list[ResourcePathSegment],
) -> None:
    ir = IdentityRepository(db_session)
    role = ir.create_role("Row_Filter_Val")
    db_session.flush()
    response = admin_client.post(
        f"/api/v1/admin/roles/{role.id}/permissions",
        json={
            "resourcePath": [s.model_dump(by_alias=True) for s in analytics_users_path],
            "resourceType": "TABLE",
            "actions": ["SELECT"],
            "effect": "ALLOW",
            "rowFilter": {"enabled": True, "conditionExpression": ""},
        },
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["data"]["code"] == "BAD_REQUEST"
