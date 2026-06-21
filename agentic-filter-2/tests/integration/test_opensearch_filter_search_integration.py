"""End-to-end filter search: real Postgres catalog + real OpenSearch index."""

from __future__ import annotations

import uuid
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.iam.schemas import IamUserClaims
from app.main import create_app
from app.models.identity import User
from app.models.permission import PermissionType
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository

from .opensearch_seed import (
    CUSTOMERS_INDEX,
    delete_customers_index,
    seed_customers_index_two_documents,
)


def _select_type_id(db_session: Session) -> uuid.UUID:
    return db_session.scalars(
        select(PermissionType.id).where(PermissionType.name == "SELECT")
    ).one()


def _seed_customers_catalog(
    db_session: Session, *, with_row_filter: bool
) -> tuple[User, str]:
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
    p_tenant = pr.create_permission(resource_id=r_tenant.id, permission_type_id=pt, effect="ALLOW")
    ir.add_user_permission(user.id, p_tbl.id)
    ir.add_user_permission(user.id, p_name.id)
    ir.add_user_permission(user.id, p_tenant.id)
    if with_row_filter:
        pr.create_row_filter(permission_id=p_tbl.id, condition_expr="tenant_id = 1")
    db_session.commit()
    return user, CUSTOMERS_INDEX


def _install_iam(client: TestClient, claims: IamUserClaims) -> None:
    m = Mock(spec_set=["validate_bearer_token", "close"])
    m.validate_bearer_token.return_value = claims
    m.close = Mock(return_value=None)
    client.app.state.iam_client = m


@pytest.mark.integration
def test_real_opensearch_row_filter_returns_one_hit(
    integration_database_url: str,
    integration_opensearch_base_url: str,
    alembic_clean_database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", integration_database_url)
    monkeypatch.setenv("RUNTIME_POSTGRES_URL", integration_database_url)
    monkeypatch.setenv("OPENSEARCH_BASE_URL", integration_opensearch_base_url)
    monkeypatch.setenv("USER_CONTEXT_CACHE_BACKEND", "memory")
    get_settings.cache_clear()

    eng = create_engine(integration_database_url)
    factory = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    db_session = factory()
    try:
        user, index_name = _seed_customers_catalog(db_session, with_row_filter=True)
        uid, uname, uemail = user.id, user.username, user.email
    finally:
        db_session.close()
    eng.dispose()

    with httpx.Client(
        base_url=integration_opensearch_base_url, timeout=60.0
    ) as os_client:
        seed_customers_index_two_documents(os_client)
        try:
            with TestClient(create_app()) as client:
                _install_iam(
                    client,
                    IamUserClaims(
                        user_id=uid,
                        username=uname,
                        email=uemail,
                        is_active=True,
                    ),
                )
                r = client.post(
                    "/api/v1/filter/search",
                    headers={"Authorization": "Bearer t"},
                    json={
                        "backend": "opensearch",
                        "index": index_name,
                        "query": {"match_all": {}},
                        "size": 20,
                    },
                )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["policy"]["decision"] == "ALLOW_WITH_FILTER"
            hits_wrap = body["hits"]
            inner = hits_wrap.get("hits", [])
            assert len(inner) == 1
            src = inner[0]["_source"]
            assert src["name"] == "Alice"
            assert src["tenant_id"] == 1
        finally:
            delete_customers_index(os_client)


@pytest.mark.integration
def test_real_opensearch_without_row_filter_returns_two_hits(
    integration_database_url: str,
    integration_opensearch_base_url: str,
    alembic_clean_database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", integration_database_url)
    monkeypatch.setenv("RUNTIME_POSTGRES_URL", integration_database_url)
    monkeypatch.setenv("OPENSEARCH_BASE_URL", integration_opensearch_base_url)
    monkeypatch.setenv("USER_CONTEXT_CACHE_BACKEND", "memory")
    get_settings.cache_clear()

    eng = create_engine(integration_database_url)
    factory = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    db_session = factory()
    try:
        user, index_name = _seed_customers_catalog(db_session, with_row_filter=False)
        uid, uname, uemail = user.id, user.username, user.email
    finally:
        db_session.close()
    eng.dispose()

    with httpx.Client(
        base_url=integration_opensearch_base_url, timeout=60.0
    ) as os_client:
        seed_customers_index_two_documents(os_client)
        try:
            with TestClient(create_app()) as client:
                _install_iam(
                    client,
                    IamUserClaims(
                        user_id=uid,
                        username=uname,
                        email=uemail,
                        is_active=True,
                    ),
                )
                r = client.post(
                    "/api/v1/filter/search",
                    headers={"Authorization": "Bearer t"},
                    json={
                        "backend": "opensearch",
                        "index": index_name,
                        "query": {"match_all": {}},
                        "size": 20,
                    },
                )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["policy"]["decision"] == "ALLOW"
            hits_wrap = body["hits"]
            assert len(hits_wrap.get("hits", [])) == 2
        finally:
            delete_customers_index(os_client)
