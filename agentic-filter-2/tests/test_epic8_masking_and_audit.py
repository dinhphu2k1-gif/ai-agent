"""Epic 8: masking service + access audit (ACCESS_LOG)."""

from __future__ import annotations

import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.iam.schemas import IamUserClaims
from app.main import create_app
from app.models.audit import AccessLog
from app.models.permission import Permission, PermissionType
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from tests.test_epic6_postgresql_runtime import (
    _CapturingExecutor,
    _install_iam,
    _seed_appdb_orders,
)


@pytest.fixture(autouse=True)
def _seed_select(db_session: Session) -> None:
    existing = db_session.scalar(
        select(PermissionType).where(PermissionType.name == "SELECT")
    )
    if existing is None:
        db_session.add(PermissionType(name="SELECT"))
        db_session.flush()


@pytest.fixture
def filter_client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)
    get_settings.cache_clear()

    def override_get_db():
        try:
            yield db_session
            db_session.commit()
        except BaseException:
            db_session.rollback()
            raise

    application = create_app()
    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as client:
        cap = _CapturingExecutor()
        client.app.state.sql_executor = cap
        yield client
    application.dependency_overrides.clear()
    get_settings.cache_clear()


def test_hash_mask_uses_salt() -> None:
    from app.services.masking_service import _apply_mask_value

    a = _apply_mask_value("secret", "HASH", None, hash_salt="salt-a")
    b = _apply_mask_value("secret", "HASH", None, hash_salt="salt-b")
    assert a != b
    assert len(str(a)) == 12


def test_alias_column_still_masked() -> None:
    from app.services.masking_service import apply_column_masks_to_row
    from app.services.permission_resolver import ColumnMaskPolicy

    pol = ColumnMaskPolicy(
        permission_id=uuid.uuid4(), mask_type="FULL", mask_pattern=None
    )
    masks = {"email": pol}
    row = {"em": "x@y.com"}
    apply_column_masks_to_row(
        row, {"email": "em"}, masks, hash_salt="dev-masking-salt-change-in-prod"
    )
    assert row["em"] == "*" * len("x@y.com")


def test_access_log_on_allow(filter_client: TestClient, db_session: Session) -> None:
    user, db_name, _, _ = _seed_appdb_orders(db_session)
    before = db_session.scalar(select(func.count()).select_from(AccessLog))
    _install_iam(
        filter_client,
        IamUserClaims(
            user_id=user.id,
            username=user.username,
            email=user.email,
            is_active=True,
        ),
    )
    r = filter_client.post(
        "/api/v1/filter/query",
        headers={"Authorization": "Bearer t"},
        json={
            "backend": "postgres",
            "database": db_name,
            "query": "SELECT id, email FROM public.orders",
            "parameters": {},
        },
    )
    assert r.status_code == 200
    db_session.expire_all()
    after = db_session.scalar(select(func.count()).select_from(AccessLog))
    assert after == before + 1
    last = db_session.scalars(select(AccessLog).order_by(AccessLog.accessed_at.desc())).first()
    assert last is not None
    assert last.action == "POSTGRES_FILTER_QUERY"
    assert last.result == "allow"
    assert last.decision == "ALLOW"
    assert last.user_id == user.id


def test_access_log_on_deny(filter_client: TestClient, db_session: Session) -> None:
    user, db_name, _, _ = _seed_appdb_orders(db_session)
    _install_iam(
        filter_client,
        IamUserClaims(
            user_id=user.id,
            username=user.username,
            email=user.email,
            is_active=True,
        ),
    )
    before = db_session.scalar(select(func.count()).select_from(AccessLog))
    r = filter_client.post(
        "/api/v1/filter/query",
        headers={"Authorization": "Bearer t"},
        json={
            "backend": "postgres",
            "database": "nope",
            "query": "SELECT id FROM public.orders",
            "parameters": {},
        },
    )
    assert r.status_code == 422
    db_session.expire_all()
    after = db_session.scalar(select(func.count()).select_from(AccessLog))
    assert after == before + 1
    last = db_session.scalars(select(AccessLog).order_by(AccessLog.accessed_at.desc())).first()
    assert last.result == "reject"


def test_response_masks_email_when_column_mask_configured(
    filter_client: TestClient, db_session: Session
) -> None:
    user, db_name, _, _ = _seed_appdb_orders(db_session)
    rr = ResourceRepository(db_session)
    db_id = rr.find_database_resource_id_by_name(db_name)
    sch_id = rr.find_schema_resource_id(db_id, "public")
    tbl_id = rr.find_table_resource_id(sch_id, "orders")
    col_rid = rr.find_column_resource_id(tbl_id, "email")
    assert col_rid is not None
    perm = db_session.scalars(
        select(Permission).where(Permission.resource_id == col_rid)
    ).first()
    assert perm is not None
    pr = PermissionRepository(db_session)
    pr.upsert_column_mask(
        permission_id=perm.id, mask_type="FULL", mask_pattern=None
    )
    db_session.commit()

    _install_iam(
        filter_client,
        IamUserClaims(
            user_id=user.id,
            username=user.username,
            email=user.email,
            is_active=True,
        ),
    )
    r = filter_client.post(
        "/api/v1/filter/query",
        headers={"Authorization": "Bearer t"},
        json={
            "backend": "postgres",
            "database": db_name,
            "query": "SELECT id, email FROM public.orders",
            "parameters": {},
        },
    )
    assert r.status_code == 200
    body = r.json()
    email = body["rows"][0]["email"]
    assert email and set(email) == {"*"}
