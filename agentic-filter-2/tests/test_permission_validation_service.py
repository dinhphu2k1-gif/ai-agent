"""Phase 5: row-filter validate and column-mask preview."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import PermissionType
from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin_contract import ResourcePathSegment
from app.services.column_mask_engine import apply_partial_mask
from app.services.permission_validation_service import PermissionValidationService
from scripts.seed_demo_data import seed_permission_wizard_resource_tree


@pytest.fixture(autouse=True)
def _permission_types(db_session: Session) -> None:
    for name in ("SELECT", "USAGE", "INSERT", "UPDATE", "DELETE", "DESCRIBE"):
        if db_session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            db_session.add(PermissionType(name=name))
    db_session.flush()


def _users_table_path(rr: ResourceRepository) -> list[ResourcePathSegment]:
    db_id = rr.find_database_resource_id_by_name("analytics_db")
    sch_id = rr.find_schema_resource_id(db_id, "public")
    tbl_id = rr.find_table_resource_id(sch_id, "users")
    assert db_id and sch_id and tbl_id
    return [
        ResourcePathSegment(id=str(db_id), name="analytics_db", type="database"),
        ResourcePathSegment(id=str(sch_id), name="public", type="schema"),
        ResourcePathSegment(id=str(tbl_id), name="users", type="table"),
    ]


def test_partial_mask_fe_example() -> None:
    assert apply_partial_mask("091-XXX-XXXX", "0912345678") == "091***5678"


def test_validate_row_filter_rejects_semicolon(db_session: Session) -> None:
    svc = PermissionValidationService(db_session)
    result = svc.validate_row_filter([], "a = 1; drop")
    assert result.valid is False
    assert any(";" in e for e in result.errors)


def test_validate_row_filter_normalizes_whitespace(db_session: Session) -> None:
    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    path = _users_table_path(rr)
    svc = PermissionValidationService(db_session)
    result = svc.validate_row_filter(path, "  region   =   'north'  ")
    assert result.valid is True
    assert result.normalized_expression == "region = 'north'"
    assert result.errors == []


def test_validate_row_filter_requires_table_path(db_session: Session) -> None:
    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    db_id = rr.find_database_resource_id_by_name("analytics_db")
    assert db_id
    path = [
        ResourcePathSegment(id=str(db_id), name="analytics_db", type="database"),
    ]
    result = PermissionValidationService(db_session).validate_row_filter(
        path, "tenant_id = 1"
    )
    assert result.valid is False
    assert any("TABLE" in e for e in result.errors)


def test_preview_column_mask_types(db_session: Session) -> None:
    svc = PermissionValidationService(db_session)
    partial = svc.preview_column_mask("PARTIAL", "091-XXX-XXXX", "0912345678")
    assert partial.masked_value == "091***5678"
    assert partial.algorithm == "PARTIAL_PATTERN"

    full = svc.preview_column_mask("FULL", None, "secret")
    assert full.masked_value == "******"
    assert full.algorithm == "FULL"

    nullify = svc.preview_column_mask("NULLIFY", None, "x")
    assert nullify.masked_value == "null"

    hash_out = svc.preview_column_mask("HASH", None, "0912345678")
    assert len(hash_out.masked_value) == 12
    assert hash_out.algorithm == "HASH"


def test_preview_partial_requires_pattern(db_session: Session) -> None:
    with pytest.raises(ValueError, match="maskPattern"):
        PermissionValidationService(db_session).preview_column_mask(
            "PARTIAL", "", "0912345678"
        )


def test_validate_row_filter_route(
    admin_client: TestClient, db_session: Session
) -> None:
    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    path = _users_table_path(rr)
    response = admin_client.post(
        "/api/v1/admin/permissions/validate/row-filter",
        json={
            "resourcePath": [s.model_dump(by_alias=True) for s in path],
            "conditionExpression": "tenant_id = 1",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["valid"] is True
    assert data["normalizedExpression"] == "tenant_id = 1"


def test_preview_column_mask_route(
    admin_client: TestClient, db_session: Session
) -> None:
    response = admin_client.post(
        "/api/v1/admin/permissions/preview/column-mask",
        json={
            "maskType": "PARTIAL",
            "maskPattern": "091-XXX-XXXX",
            "sampleValue": "0912345678",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["maskedValue"] == "091***5678"
    assert data["algorithm"] == "PARTIAL_PATTERN"
