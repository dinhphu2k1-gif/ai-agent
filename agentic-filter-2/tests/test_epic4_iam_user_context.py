"""Epic 4: IAM client, user context, Redis/memory cache, runtime route."""

from __future__ import annotations

import uuid
from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import Settings, get_settings
from app.iam.client import IamHttpClient, IamInvalidTokenError, IamUnavailableError
from app.iam.schemas import IamUserClaims
from app.main import create_app
from app.repositories.identity_repo import IdentityRepository


@pytest.fixture
def runtime_client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> TestClient:
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
        yield client
    application.dependency_overrides.clear()
    get_settings.cache_clear()


def _claims(uid: uuid.UUID, *, is_active: bool = True) -> IamUserClaims:
    return IamUserClaims(
        user_id=uid,
        username="alice",
        email="alice@example.com",
        is_active=is_active,
    )


def _install_mock_iam(client: TestClient, *, claims: IamUserClaims | None = None, err: Exception | None = None) -> None:
    m = Mock(spec_set=["validate_bearer_token", "close"])
    if err is not None:
        m.validate_bearer_token.side_effect = err
    else:
        assert claims is not None
        m.validate_bearer_token.return_value = claims
    m.close = Mock(return_value=None)
    client.app.state.iam_client = m


def test_runtime_user_context_valid_token(runtime_client: TestClient, db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    u = ir.create_user("alice", "alice@example.com")
    uid = u.id
    g = ir.create_group("g1")
    r = ir.create_role("r1")
    ir.add_user_to_group(uid, g.id)
    ir.add_user_role(uid, r.id)
    db_session.commit()

    claims = _claims(uid)
    _install_mock_iam(runtime_client, claims=claims)

    resp = runtime_client.get(
        "/api/v1/runtime/user-context",
        headers={"Authorization": "Bearer any"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == str(uid)
    assert len(body["group_ids"]) == 1
    assert len(body["direct_role_ids"]) == 1


def test_user_context_cache_hit_skips_db_membership_query(
    runtime_client: TestClient, db_session: Session
) -> None:
    ir = IdentityRepository(db_session)
    u = ir.create_user("bob", "bob@example.com")
    uid = u.id
    db_session.commit()
    claims = _claims(uid)
    _install_mock_iam(runtime_client, claims=claims)

    calls: list[object] = []
    orig = IdentityRepository.list_groups_for_user

    def counting(self: IdentityRepository, user_id: uuid.UUID) -> list:
        calls.append(1)
        return orig(self, user_id)

    with patch.object(IdentityRepository, "list_groups_for_user", counting):
        r1 = runtime_client.get(
            "/api/v1/runtime/user-context",
            headers={"Authorization": "Bearer t1"},
        )
        r2 = runtime_client.get(
            "/api/v1/runtime/user-context",
            headers={"Authorization": "Bearer t2"},
        )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert len(calls) == 1


def test_auth_bypass_skips_iam(
    runtime_client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    ir = IdentityRepository(db_session)
    u = ir.create_user("bypass", "bypass@example.com")
    db_session.commit()

    monkeypatch.setenv("AUTH_BYPASS_ENABLED", "true")
    monkeypatch.setenv("AUTH_BYPASS_USER_ID", str(u.id))
    get_settings.cache_clear()

    iam = Mock(spec_set=["validate_bearer_token", "close"])
    iam.validate_bearer_token.side_effect = AssertionError("IAM must not be called")
    runtime_client.app.state.iam_client = iam

    r = runtime_client.get(
        "/api/v1/runtime/user-context",
        headers={"Authorization": "Bearer fe-test-token"},
    )
    assert r.status_code == 200
    assert r.json()["user_id"] == str(u.id)
    get_settings.cache_clear()


def test_missing_bearer_401(runtime_client: TestClient) -> None:
    _install_mock_iam(runtime_client, claims=_claims(uuid.uuid4()))
    r = runtime_client.get("/api/v1/runtime/user-context")
    assert r.status_code == 401
    assert r.json()["code"] == "unauthorized"


def test_invalid_token_401(runtime_client: TestClient) -> None:
    _install_mock_iam(runtime_client, err=IamInvalidTokenError("bad"))
    r = runtime_client.get(
        "/api/v1/runtime/user-context",
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 401
    assert r.json()["code"] == "unauthorized"


def test_inactive_local_user_403(runtime_client: TestClient, db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    u = ir.create_user("carol", "c@example.com", is_active=False)
    db_session.commit()
    _install_mock_iam(runtime_client, claims=_claims(u.id, is_active=True))
    r = runtime_client.get(
        "/api/v1/runtime/user-context",
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 403
    assert r.json()["code"] == "forbidden"


def test_iam_timeout_504(runtime_client: TestClient) -> None:
    _install_mock_iam(runtime_client, err=IamUnavailableError("IAM request timed out"))
    r = runtime_client.get(
        "/api/v1/runtime/user-context",
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 504
    assert r.json()["code"] == "gateway_timeout"


def test_iam_unavailable_502(runtime_client: TestClient) -> None:
    _install_mock_iam(runtime_client, err=IamUnavailableError("IAM down"))
    r = runtime_client.get(
        "/api/v1/runtime/user-context",
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 502
    assert r.json()["code"] == "bad_gateway"


def test_iam_http_client_retries_on_5xx() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(503)
        uid = str(uuid.uuid4())
        return httpx.Response(
            200,
            json={
                "sub": uid,
                "username": "u",
                "email": "u@e.com",
                "active": True,
            },
        )

    transport = httpx.MockTransport(handler)
    cfg = Settings(
        iam_base_url="http://iam.test",
        iam_token_validate_path="/validate",
        iam_timeout_seconds=5.0,
        iam_max_retries=2,
        user_context_cache_backend="memory",
    )
    inner = httpx.Client(transport=transport, base_url="http://iam.test")
    try:
        client = IamHttpClient(cfg, client=inner)
        claims = client.validate_bearer_token("tok")
        assert claims.username == "u"
        assert calls["n"] == 2
    finally:
        client.close()
        inner.close()
