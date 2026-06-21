"""Epic 6: PostgreSQL runtime filter query (MVP SELECT + PDP + rewriter)."""

from __future__ import annotations

import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.iam.schemas import IamUserClaims
from app.main import create_app
from app.models.permission import PermissionType
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository


@pytest.fixture(autouse=True)
def _seed_select(db_session: Session) -> None:
    existing = db_session.scalar(
        select(PermissionType).where(PermissionType.name == "SELECT")
    )
    if existing is None:
        db_session.add(PermissionType(name="SELECT"))
        db_session.flush()


def _select_type_id(db_session: Session) -> uuid.UUID:
    return db_session.scalars(
        select(PermissionType.id).where(PermissionType.name == "SELECT")
    ).one()


class _CapturingExecutor:
    def __init__(self) -> None:
        self.last_sql: str | None = None

    def execute_select(self, sql: str, parameters: dict | None = None) -> tuple[list[str], list[dict]]:
        self.last_sql = sql
        return (["id", "email"], [{"id": 1, "email": "alice@example.com"}])

    def dispose(self) -> None:
        pass


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
        real_ex = client.app.state.sql_executor
        cap = _CapturingExecutor()
        client.app.state.sql_executor = cap
        setattr(client.app.state, "_test_capturing_executor", cap)
        yield client
        client.app.state.sql_executor = real_ex
        delattr(client.app.state, "_test_capturing_executor")
    application.dependency_overrides.clear()
    get_settings.cache_clear()


def _install_iam(client: TestClient, claims: IamUserClaims) -> None:
    m = Mock(spec_set=["validate_bearer_token", "close"])
    m.validate_bearer_token.return_value = claims
    m.close = Mock(return_value=None)
    client.app.state.iam_client = m


def _seed_appdb_orders(db_session: Session, *, with_row_filter: bool = False) -> tuple:
    """Returns (user, db_name, table_id, col_id_email)."""
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
    return user, "appdb", r_tbl.id, r_email.id


def test_filter_query_allow_path(filter_client: TestClient, db_session: Session) -> None:
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
    assert body["columns"] == ["id", "email"]
    assert len(body["rows"]) == 1
    assert body["policy"]["decision"] == "ALLOW"


def test_filter_query_row_filter_in_sql(filter_client: TestClient, db_session: Session) -> None:
    user, db_name, _, _ = _seed_appdb_orders(db_session, with_row_filter=True)
    _install_iam(
        filter_client,
        IamUserClaims(
            user_id=user.id,
            username=user.username,
            email=user.email,
            is_active=True,
        ),
    )
    filter_client.post(
        "/api/v1/filter/query",
        headers={"Authorization": "Bearer t"},
        json={
            "backend": "postgres",
            "database": db_name,
            "query": "SELECT id, email FROM public.orders",
            "parameters": {},
        },
    )
    cap: _CapturingExecutor = filter_client.app.state._test_capturing_executor  # type: ignore[attr-defined]
    assert cap.last_sql is not None
    assert "tenant_id = 1" in cap.last_sql


def test_filter_query_column_deny_403(filter_client: TestClient, db_session: Session) -> None:
    user, db_name, tbl_id, col_email = _seed_appdb_orders(db_session)
    pr = PermissionRepository(db_session)
    pt = _select_type_id(db_session)
    p_deny = pr.create_permission(resource_id=col_email, permission_type_id=pt, effect="DENY")
    ir = IdentityRepository(db_session)
    ir.add_user_permission(user.id, p_deny.id)
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
    assert r.status_code == 403
    assert r.json()["code"] == "forbidden"


def test_filter_query_multi_statement_422(filter_client: TestClient, db_session: Session) -> None:
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
    r = filter_client.post(
        "/api/v1/filter/query",
        headers={"Authorization": "Bearer t"},
        json={
            "backend": "postgres",
            "database": db_name,
            "query": "SELECT id FROM public.orders; SELECT id FROM public.orders",
            "parameters": {},
        },
    )
    assert r.status_code == 422
    assert r.json()["code"] == "unsupported_query"


def test_filter_query_join_unsupported_422(filter_client: TestClient, db_session: Session) -> None:
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
    r = filter_client.post(
        "/api/v1/filter/query",
        headers={"Authorization": "Bearer t"},
        json={
            "backend": "postgres",
            "database": db_name,
            "query": "SELECT orders.id FROM public.orders JOIN public.orders o2 ON true",
            "parameters": {},
        },
    )
    assert r.status_code == 422


def test_filter_query_unknown_database_422(filter_client: TestClient, db_session: Session) -> None:
    user, _, _, _ = _seed_appdb_orders(db_session)
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
            "database": "nope",
            "query": "SELECT id FROM public.orders",
            "parameters": {},
        },
    )
    assert r.status_code == 422


def test_parse_select_star_rejected() -> None:
    from app.query.analyzer import UnsupportedQueryError, parse_select_query

    with pytest.raises(UnsupportedQueryError):
        parse_select_query("SELECT * FROM public.orders")


def test_combine_row_filter_rewrite() -> None:
    from app.query.postgres_rewriter import inject_row_filter_predicate

    sql = "SELECT id FROM public.orders WHERE x = 1"
    out = inject_row_filter_predicate(sql, "tenant_id = 1")
    assert "tenant_id = 1" in out
    assert "x = 1" in out
