"""End-to-end filter query against a real PostgreSQL instance (opt-in)."""

from __future__ import annotations

import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.iam.schemas import IamUserClaims
from app.main import create_app
from app.models.identity import User
from app.models.permission import PermissionType
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository


def _select_type_id(db_session: Session) -> uuid.UUID:
    return db_session.scalars(
        select(PermissionType.id).where(PermissionType.name == "SELECT")
    ).one()


def _seed_appdb_orders(
    db_session: Session, *, with_row_filter: bool = False
) -> tuple[User, str]:
    """Returns (user, logical_database_name)."""
    rr = ResourceRepository(db_session)
    r_db = rr.create_resource("DATABASE")
    rr.create_database(r_db.id, "appdb", None)
    r_sch = rr.create_resource("SCHEMA")
    rr.create_schema(r_sch.id, r_db.id, "public")
    r_tbl = rr.create_resource("TABLE")
    rr.create_table(r_tbl.id, r_sch.id, "orders")
    r_id = rr.create_resource("COLUMN")
    rr.create_column(r_id.id, r_tbl.id, "id", "int")
    r_email = rr.create_resource("COLUMN")
    rr.create_column(r_email.id, r_tbl.id, "email", "text")
    ir = IdentityRepository(db_session)
    user = ir.create_user(f"u{uuid.uuid4().hex[:8]}", "u@e.com")
    pt = _select_type_id(db_session)
    pr = PermissionRepository(db_session)
    p_tbl = pr.create_permission(resource_id=r_tbl.id, permission_type_id=pt, effect="ALLOW")
    p_id = pr.create_permission(resource_id=r_id.id, permission_type_id=pt, effect="ALLOW")
    p_email = pr.create_permission(resource_id=r_email.id, permission_type_id=pt, effect="ALLOW")
    ir.add_user_permission(user.id, p_tbl.id)
    ir.add_user_permission(user.id, p_id.id)
    ir.add_user_permission(user.id, p_email.id)
    if with_row_filter:
        pr.create_row_filter(permission_id=p_tbl.id, condition_expr="tenant_id = 1")
    db_session.commit()
    return user, "appdb"


def _install_iam(client: TestClient, claims: IamUserClaims) -> None:
    m = Mock(spec_set=["validate_bearer_token", "close"])
    m.validate_bearer_token.return_value = claims
    m.close = Mock(return_value=None)
    client.app.state.iam_client = m


def _physical_orders_table(url: str) -> None:
    eng = create_engine(url)
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS public.orders"))
        conn.execute(
            text(
                "CREATE TABLE public.orders ("
                "id integer NOT NULL PRIMARY KEY, "
                "email text NOT NULL, "
                "tenant_id integer NOT NULL)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO public.orders (id, email, tenant_id) VALUES "
                "(1, 'alice@example.com', 1), "
                "(2, 'bob@example.com', 2)"
            )
        )
    eng.dispose()


@pytest.mark.integration
def test_filter_query_returns_real_postgres_rows(
    integration_database_url: str,
    alembic_clean_database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", integration_database_url)
    monkeypatch.setenv("RUNTIME_POSTGRES_URL", integration_database_url)
    monkeypatch.setenv("USER_CONTEXT_CACHE_BACKEND", "memory")
    get_settings.cache_clear()

    _physical_orders_table(integration_database_url)

    eng = create_engine(integration_database_url)
    factory = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    db_session = factory()
    try:
        user, db_name = _seed_appdb_orders(db_session)
        user_id, username, email = user.id, user.username, user.email
    finally:
        db_session.close()
    eng.dispose()

    with TestClient(create_app()) as client:
        _install_iam(
            client,
            IamUserClaims(
                user_id=user_id,
                username=username,
                email=email,
                is_active=True,
            ),
        )
        r = client.post(
            "/api/v1/filter/query",
            headers={"Authorization": "Bearer t"},
            json={
                "backend": "postgres",
                "database": db_name,
                "query": "SELECT id, email FROM public.orders",
                "parameters": {},
            },
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["columns"] == ["id", "email"]
    assert body["policy"]["decision"] == "ALLOW"
    rows = sorted(body["rows"], key=lambda x: x["id"])
    assert rows == [
        {"id": 1, "email": "alice@example.com"},
        {"id": 2, "email": "bob@example.com"},
    ]


@pytest.mark.integration
def test_filter_query_row_filter_limits_real_postgres_rows(
    integration_database_url: str,
    alembic_clean_database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", integration_database_url)
    monkeypatch.setenv("RUNTIME_POSTGRES_URL", integration_database_url)
    monkeypatch.setenv("USER_CONTEXT_CACHE_BACKEND", "memory")
    get_settings.cache_clear()

    _physical_orders_table(integration_database_url)

    eng = create_engine(integration_database_url)
    factory = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    db_session = factory()
    try:
        user, db_name = _seed_appdb_orders(db_session, with_row_filter=True)
        user_id, username, email = user.id, user.username, user.email
    finally:
        db_session.close()
    eng.dispose()

    with TestClient(create_app()) as client:
        _install_iam(
            client,
            IamUserClaims(
                user_id=user_id,
                username=username,
                email=email,
                is_active=True,
            ),
        )
        r = client.post(
            "/api/v1/filter/query",
            headers={"Authorization": "Bearer t"},
            json={
                "backend": "postgres",
                "database": db_name,
                "query": "SELECT id, email FROM public.orders",
                "parameters": {},
            },
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["policy"]["decision"] == "ALLOW_WITH_FILTER"
    assert body["rows"] == [{"id": 1, "email": "alice@example.com"}]
