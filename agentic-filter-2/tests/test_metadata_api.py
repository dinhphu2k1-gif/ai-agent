"""Metadata API: DESCRIBE filter, RELATIONSHIP pass-through, trusted userId."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.main import create_app
from app.models.permission import PermissionType
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.services.metadata_service import _filter_hits
from app.services.user_context_service import (
    TrustedUserContextError,
    UserContext,
    build_user_context_from_trusted_user_id,
)
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
def metadata_client(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> tuple[TestClient, MagicMock]:
    from app.api.deps import get_db
    from app.main import create_app

    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)
    get_settings.cache_clear()

    mock_executor = MagicMock()

    def override_get_db() -> Any:
        try:
            yield db_session
            db_session.commit()
        except BaseException:
            db_session.rollback()
            raise

    mock_embedder = MagicMock()
    mock_embedder.encode_query.return_value = [0.0] * 1024

    application = create_app()
    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as test_client:
        test_client.app.state.opensearch_executor = mock_executor
        test_client.app.state.metadata_embedder = mock_embedder
        yield test_client, mock_executor
    application.dependency_overrides.clear()
    get_settings.cache_clear()


def _os_response(hits: list[dict[str, Any]]) -> dict[str, Any]:
    return {"hits": {"hits": hits, "total": {"value": len(hits)}}}


def _table_hit(schema: str = "public", table: str = "users") -> dict[str, Any]:
    return {
        "_id": f"table-{table}",
        "_score": 1.0,
        "_source": {
            "record_type": "TABLE",
            "database_name": "analytics_db",
            "schema_name": schema,
            "table_name": table,
            "description": "Users table",
        },
    }


def _column_hit(
    schema: str = "public", table: str = "users", column: str = "email"
) -> dict[str, Any]:
    return {
        "_id": f"col-{column}",
        "_score": 0.9,
        "_source": {
            "record_type": "COLUMN",
            "database_name": "analytics_db",
            "schema_name": schema,
            "table_name": table,
            "column_name": column,
            "description": "Email",
        },
    }


def _relationship_hit() -> dict[str, Any]:
    return {
        "_id": "rel-1",
        "_score": 0.5,
        "_source": {
            "record_type": "RELATIONSHIP",
            "relationship_name": "users_events",
            "description": "User activity link",
            "join_path": "users.id = events.user_id",
            "related_tables": ["users", "events"],
        },
    }


def _grant_describe_on_table(
    db_session: Session, user_id: uuid.UUID, table_resource_id: uuid.UUID
) -> None:
    pr = PermissionRepository(db_session)
    ptype = pr.get_permission_type_by_name("DESCRIBE")
    assert ptype is not None
    perm = pr.create_permission(
        resource_id=table_resource_id,
        permission_type_id=ptype.id,
        effect="ALLOW",
    )
    IdentityRepository(db_session).add_user_permission(user_id, perm.id)
    db_session.flush()


def test_get_user_by_username(db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    user = ir.create_user("meta_user", "meta@example.com")
    db_session.flush()
    found = ir.get_user_by_username("meta_user")
    assert found is not None
    assert found.id == user.id


def test_trusted_user_context_uuid_and_username(db_session: Session) -> None:
    from app.cache.redis_client import create_user_context_cache

    ir = IdentityRepository(db_session)
    user = ir.create_user("trusted_ctx", "t@example.com")
    db_session.flush()
    cache = create_user_context_cache(get_settings())
    try:
        by_name = build_user_context_from_trusted_user_id(
            db_session, cache, "trusted_ctx", get_settings()
        )
        assert by_name.user_id == user.id
        by_uuid = build_user_context_from_trusted_user_id(
            db_session, cache, str(user.id), get_settings()
        )
        assert by_uuid.user_id == user.id
    finally:
        cache.close()


def test_trusted_user_not_found(db_session: Session) -> None:
    from app.cache.redis_client import create_user_context_cache

    cache = create_user_context_cache(get_settings())
    try:
        with pytest.raises(TrustedUserContextError) as exc:
            build_user_context_from_trusted_user_id(
                db_session, cache, "no-such-user", get_settings()
            )
        assert exc.value.code == "USER_NOT_FOUND"
    finally:
        cache.close()


def test_filter_hits_describe_inheritance(db_session: Session) -> None:
    from app.cache.redis_client import create_user_context_cache

    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    tbl_rid = rr.find_table_resource_id(
        rr.find_schema_resource_id(
            rr.find_database_resource_id_by_name("analytics_db"), "public"
        ),
        "users",
    )
    assert tbl_rid is not None

    ir = IdentityRepository(db_session)
    allowed = ir.create_user("allowed", "a@example.com")
    denied = ir.create_user("denied", "d@example.com")
    db_session.flush()
    _grant_describe_on_table(db_session, allowed.id, tbl_rid)

    cache = create_user_context_cache(get_settings())
    settings = get_settings()
    try:
        uc_allow = build_user_context_from_trusted_user_id(
            db_session, cache, "allowed", settings
        )
        uc_deny = build_user_context_from_trusted_user_id(
            db_session, cache, "denied", settings
        )
        hits = [_table_hit(), _column_hit(), _relationship_hit()]
        kept, filtered, warnings = _filter_hits(
            db_session, uc_allow, cache, settings, hits
        )
        assert len(kept) == 3
        assert warnings == []

        kept_d, _, warnings_d = _filter_hits(
            db_session, uc_deny, cache, settings, hits
        )
        assert len(kept_d) == 1
        assert kept_d[0]["_source"]["record_type"] == "RELATIONSHIP"
        assert warnings_d
        assert warnings_d[0].code == "ACCESS_FILTERED"
    finally:
        cache.close()


def test_hybrid_search_filters_table_column(
    metadata_client: tuple[TestClient, MagicMock], db_session: Session
) -> None:
    client, mock_exec = metadata_client
    seed_permission_wizard_resource_tree(db_session)
    rr = ResourceRepository(db_session)
    db_rid = rr.find_database_resource_id_by_name("analytics_db")
    sch_rid = rr.find_schema_resource_id(db_rid, "public")
    tbl_rid = rr.find_table_resource_id(sch_rid, "users")
    assert tbl_rid is not None

    ir = IdentityRepository(db_session)
    user = ir.create_user("hybrid_ok", "h@example.com")
    db_session.flush()
    _grant_describe_on_table(db_session, user.id, tbl_rid)

    mock_exec.search.return_value = _os_response(
        [_table_hit(), _column_hit(), _relationship_hit()]
    )

    resp = client.post(
        "/api/v1/metadata/hybrid-search",
        json={"userId": "hybrid_ok", "query": "users email", "size": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]["hits"]) == 3
    assert body["data"]["debug"]["queryMode"] == "hybrid"
    assert body["data"]["debug"]["hybridLeg"] == "knn_bm25"


def test_hybrid_search_denied_user_only_relationship(
    metadata_client: tuple[TestClient, MagicMock], db_session: Session
) -> None:
    client, mock_exec = metadata_client
    seed_permission_wizard_resource_tree(db_session)
    ir = IdentityRepository(db_session)
    ir.create_user("no_describe", "n@example.com")
    db_session.flush()

    mock_exec.search.return_value = _os_response(
        [_table_hit(), _column_hit(), _relationship_hit()]
    )

    resp = client.post(
        "/api/v1/metadata/hybrid-search",
        json={"userId": "no_describe", "query": "users", "size": 5},
    )
    assert resp.status_code == 200
    hits = resp.json()["data"]["hits"]
    assert len(hits) == 1
    assert hits[0]["_source"]["record_type"] == "RELATIONSHIP"
    assert resp.json()["data"]["warnings"]


def test_format_results_prefixes() -> None:
    from app.schemas.metadata_contract import MetadataFormatResultsRequest
    from app.services.metadata_service import run_metadata_format_results

    out = run_metadata_format_results(
        MetadataFormatResultsRequest(
            hits=[_table_hit(), _column_hit(), _relationship_hit()]
        )
    )
    raw = out.data.raw_results  # type: ignore[union-attr]
    assert "[TABLE]" in raw
    assert "Users table" in raw
    assert "[COLUMN]" in raw
    assert "email" in raw
    assert "[RELATIONSHIP]" in raw
    assert "users_events" in raw
    assert "join_path" in raw.lower() or "Join Path" in raw


def test_opensearch_not_configured(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.deps import get_db

    monkeypatch.setenv("OPENSEARCH_BASE_URL", "")
    monkeypatch.setenv("OPENSEARCH_HOST", "")
    get_settings.cache_clear()

    def override_get_db() -> Any:
        try:
            yield db_session
            db_session.commit()
        except BaseException:
            db_session.rollback()
            raise

    application = create_app()
    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as c:
        ir = IdentityRepository(db_session)
        ir.create_user("any_user", "any@example.com")
        db_session.flush()
        resp = c.post(
            "/api/v1/metadata/hybrid-search",
            json={"userId": "any_user", "query": "x", "size": 1},
        )
    application.dependency_overrides.clear()
    get_settings.cache_clear()
    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "UPSTREAM_ERROR"
