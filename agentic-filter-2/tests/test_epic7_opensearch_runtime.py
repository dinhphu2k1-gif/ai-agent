"""Epic 7: OpenSearch runtime (MVP DSL + PDP + rewriter + mock executor)."""

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
from app.models.identity import User
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


class _CapturingOpenSearchExecutor:
    def __init__(self) -> None:
        self.last_index: str | None = None
        self.last_body: dict | None = None

    def search(self, index: str, body: dict) -> dict:
        self.last_index = index
        self.last_body = body
        return {"hits": {"hits": [], "total": {"value": 0}}}

    def close(self) -> None:
        pass


@pytest.fixture
def search_client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> TestClient:
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
        cap = _CapturingOpenSearchExecutor()
        client.app.state.opensearch_executor = cap
        setattr(client.app.state, "_test_capturing_os", cap)
        yield client
        delattr(client.app.state, "_test_capturing_os")
    application.dependency_overrides.clear()
    get_settings.cache_clear()


def _install_iam(client: TestClient, claims: IamUserClaims) -> None:
    m = Mock(spec_set=["validate_bearer_token", "close"])
    m.validate_bearer_token.return_value = claims
    m.close = Mock(return_value=None)
    client.app.state.iam_client = m


def _seed_customers_index(
    db_session: Session, *, with_row_filter: bool = False, deny_tenant_column: bool = False
) -> tuple[User, str]:
    """Table name ``customers`` matches OpenSearch index (MVP resolver)."""
    rr = ResourceRepository(db_session)
    r_db = rr.create_resource("DATABASE")
    rr.create_database(r_db.id, "osdb", None)
    r_sch = rr.create_resource("SCHEMA")
    rr.create_schema(r_sch.id, r_db.id, "public")
    r_tbl = rr.create_resource("TABLE")
    rr.create_table(r_tbl.id, r_sch.id, "customers")
    r_name = rr.create_resource("COLUMN")
    rr.create_column(r_name.id, r_tbl.id, "name", "text")
    r_tenant = rr.create_resource("COLUMN")
    rr.create_column(r_tenant.id, r_tbl.id, "tenant_id", "int")
    ir = IdentityRepository(db_session)
    user = ir.create_user(f"u{uuid.uuid4().hex[:8]}", "u@e.com")
    pt = _select_type_id(db_session)
    pr = PermissionRepository(db_session)
    p_tbl = pr.create_permission(resource_id=r_tbl.id, permission_type_id=pt, effect="ALLOW")
    p_name = pr.create_permission(resource_id=r_name.id, permission_type_id=pt, effect="ALLOW")
    p_tenant = pr.create_permission(
        resource_id=r_tenant.id,
        permission_type_id=pt,
        effect="DENY" if deny_tenant_column else "ALLOW",
    )
    ir.add_user_permission(user.id, p_tbl.id)
    ir.add_user_permission(user.id, p_name.id)
    ir.add_user_permission(user.id, p_tenant.id)
    if with_row_filter:
        pr.create_row_filter(permission_id=p_tbl.id, condition_expr="tenant_id = 1")
    db_session.commit()
    return user, "customers"


def test_filter_search_injects_row_filter_into_bool_filter(
    search_client: TestClient, db_session: Session
) -> None:
    user, index = _seed_customers_index(db_session, with_row_filter=True)
    uid, uname, uemail = user.id, user.username, user.email
    _install_iam(
        search_client,
        IamUserClaims(
            user_id=uid,
            username=uname,
            email=uemail,
            is_active=True,
        ),
    )
    r = search_client.post(
        "/api/v1/filter/search",
        headers={"Authorization": "Bearer t"},
        json={
            "backend": "opensearch",
            "index": index,
            "query": {"match": {"name": "An"}},
        },
    )
    assert r.status_code == 200, r.text
    cap: _CapturingOpenSearchExecutor = search_client.app.state._test_capturing_os  # type: ignore[attr-defined]
    assert cap.last_body is not None
    q = cap.last_body["query"]
    assert "bool" in q
    fl = q["bool"].get("filter") or []
    assert any(
        isinstance(x, dict) and x.get("term") == {"tenant_id": 1} for x in fl
    ), fl


def test_filter_search_denied_query_field_403(search_client: TestClient, db_session: Session) -> None:
    user, index = _seed_customers_index(db_session, deny_tenant_column=True)
    uid, uname, uemail = user.id, user.username, user.email
    _install_iam(
        search_client,
        IamUserClaims(
            user_id=uid,
            username=uname,
            email=uemail,
            is_active=True,
        ),
    )
    r = search_client.post(
        "/api/v1/filter/search",
        headers={"Authorization": "Bearer t"},
        json={
            "backend": "opensearch",
            "index": index,
            "query": {"term": {"tenant_id": 1}},
        },
    )
    assert r.status_code == 403


def test_filter_search_source_includes_denied_field_403(
    search_client: TestClient, db_session: Session
) -> None:
    user, index = _seed_customers_index(db_session, deny_tenant_column=True)
    uid, uname, uemail = user.id, user.username, user.email
    _install_iam(
        search_client,
        IamUserClaims(
            user_id=uid,
            username=uname,
            email=uemail,
            is_active=True,
        ),
    )
    r = search_client.post(
        "/api/v1/filter/search",
        headers={"Authorization": "Bearer t"},
        json={
            "backend": "opensearch",
            "index": index,
            "query": {"match_all": {}},
            "_source": {"includes": ["name", "tenant_id"]},
        },
    )
    assert r.status_code == 403


def test_filter_search_rejects_script_query(search_client: TestClient, db_session: Session) -> None:
    user, index = _seed_customers_index(db_session)
    uid, uname, uemail = user.id, user.username, user.email
    _install_iam(
        search_client,
        IamUserClaims(
            user_id=uid,
            username=uname,
            email=uemail,
            is_active=True,
        ),
    )
    r = search_client.post(
        "/api/v1/filter/search",
        headers={"Authorization": "Bearer t"},
        json={
            "backend": "opensearch",
            "index": index,
            "query": {"script_score": {"query": {"match_all": {}}, "script": {"source": "1"}}},
        },
    )
    assert r.status_code == 422


def test_merge_policy_filters_preserves_client_bool_must() -> None:
    from app.query.opensearch_rewriter import merge_policy_filters_into_clause

    q = {"bool": {"must": [{"match": {"name": "x"}}], "filter": [{"term": {"a": 1}}]}}
    out = merge_policy_filters_into_clause(q, [{"term": {"tenant_id": 1}}])
    assert out["bool"]["must"] == [{"match": {"name": "x"}}]
    assert {"term": {"tenant_id": 1}} in out["bool"]["filter"]


def test_row_filter_combined_exprs_to_terms() -> None:
    from app.query.opensearch_row_filter import row_filter_exprs_to_term_clauses

    clauses = row_filter_exprs_to_term_clauses(["(tenant_id = 1) AND (name = 'x')"])
    assert {"term": {"tenant_id": 1}} in clauses
    assert {"term": {"name": "x"}} in clauses
