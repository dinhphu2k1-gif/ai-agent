"""Epic 5: authorization engine (PDP), snapshot cache, resolver rules."""

from __future__ import annotations

import json
import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.cache.invalidation import bump_permission_version, get_permission_version
from app.cache.keys import permission_snapshot_key
from app.core.config import get_settings
from app.iam.schemas import IamUserClaims
from app.main import create_app
from app.models.permission import PermissionType
from app.repositories.identity_repo import IdentityRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.policy_repo import PolicyRepository
from app.repositories.resource_repo import ResourceRepository
from app.services.authorization_service import resolve_access
from app.services.permission_resolver import DecisionType, resolve_from_bundle
from app.services.row_filter_service import combine_row_filters
from app.services.user_context_service import UserContext


@pytest.fixture(autouse=True)
def _seed_select_type(db_session: Session) -> None:
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


@pytest.fixture
def auth_client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> TestClient:
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


def _install_mock_iam(client: TestClient, claims: IamUserClaims) -> None:
    m = Mock(spec_set=["validate_bearer_token", "close"])
    m.validate_bearer_token.return_value = claims
    m.close = Mock(return_value=None)
    client.app.state.iam_client = m


def _tree(db_session: Session) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
    rr = ResourceRepository(db_session)
    r_db = rr.create_resource("DATABASE")
    rr.create_database(r_db.id, "db1", None)
    r_sch = rr.create_resource("SCHEMA")
    rr.create_schema(r_sch.id, r_db.id, "public")
    r_tbl = rr.create_resource("TABLE")
    rr.create_table(r_tbl.id, r_sch.id, "orders")
    r_col = rr.create_resource("COLUMN")
    rr.create_column(r_col.id, r_tbl.id, "email", "text")
    db_session.flush()
    return r_db.id, r_sch.id, r_tbl.id, r_col.id


def _ctx(uid: uuid.UUID, **kwargs: object) -> UserContext:
    return UserContext(
        user_id=uid,
        username="u",
        email="u@e.com",
        is_active=True,
        group_ids=list(kwargs.get("group_ids", [])),  # type: ignore[arg-type]
        direct_role_ids=list(kwargs.get("direct_role_ids", [])),  # type: ignore[arg-type]
        inherited_role_ids=list(kwargs.get("inherited_role_ids", [])),  # type: ignore[arg-type]
    )


def test_resolve_direct_user_allow(db_session: Session) -> None:
    _, _, tbl_id, col_id = _tree(db_session)
    ir = IdentityRepository(db_session)
    user = ir.create_user("u1", "u1@e.com")
    pt = _select_type_id(db_session)
    pr = PermissionRepository(db_session)
    perm = pr.create_permission(resource_id=tbl_id, permission_type_id=pt, effect="ALLOW")
    ir.add_user_permission(user.id, perm.id)
    db_session.commit()

    bundle = PolicyRepository(db_session).load_permission_bundle(
        user_id=user.id,
        group_ids=[],
        direct_role_ids=[],
        inherited_role_ids=[],
    )
    rr = ResourceRepository(db_session)
    anc = frozenset(rr.get_ancestor_resource_ids(tbl_id))
    assert resolve_from_bundle(bundle, anc, "SELECT").decision == DecisionType.ALLOW

    anc_col = frozenset(rr.get_ancestor_resource_ids(col_id))
    assert resolve_from_bundle(bundle, anc_col, "SELECT").decision == DecisionType.ALLOW


def test_group_permission(db_session: Session) -> None:
    _, _, tbl_id, _ = _tree(db_session)
    ir = IdentityRepository(db_session)
    user = ir.create_user("guser", "g@e.com")
    g = ir.create_group("g1")
    ir.add_user_to_group(user.id, g.id)
    pt = _select_type_id(db_session)
    pr = PermissionRepository(db_session)
    perm = pr.create_permission(resource_id=tbl_id, permission_type_id=pt, effect="ALLOW")
    ir.add_group_permission(g.id, perm.id)
    db_session.commit()

    bundle = PolicyRepository(db_session).load_permission_bundle(
        user_id=user.id,
        group_ids=[g.id],
        direct_role_ids=[],
        inherited_role_ids=[],
    )
    anc = frozenset(ResourceRepository(db_session).get_ancestor_resource_ids(tbl_id))
    assert resolve_from_bundle(bundle, anc, "SELECT").decision == DecisionType.ALLOW


def test_role_permission(db_session: Session) -> None:
    _, _, tbl_id, _ = _tree(db_session)
    ir = IdentityRepository(db_session)
    user = ir.create_user("ruser", "r@e.com")
    role = ir.create_role("r1")
    ir.add_user_role(user.id, role.id)
    pt = _select_type_id(db_session)
    pr = PermissionRepository(db_session)
    perm = pr.create_permission(resource_id=tbl_id, permission_type_id=pt, effect="ALLOW")
    ir.add_role_permission(role.id, perm.id)
    db_session.commit()

    bundle = PolicyRepository(db_session).load_permission_bundle(
        user_id=user.id,
        group_ids=[],
        direct_role_ids=[role.id],
        inherited_role_ids=[],
    )
    anc = frozenset(ResourceRepository(db_session).get_ancestor_resource_ids(tbl_id))
    assert resolve_from_bundle(bundle, anc, "SELECT").decision == DecisionType.ALLOW


def test_inherited_role_via_group(db_session: Session) -> None:
    _, _, tbl_id, _ = _tree(db_session)
    ir = IdentityRepository(db_session)
    user = ir.create_user("iuser", "i@e.com")
    g = ir.create_group("gg")
    role = ir.create_role("gr")
    ir.add_user_to_group(user.id, g.id)
    ir.add_group_role(g.id, role.id)
    pt = _select_type_id(db_session)
    pr = PermissionRepository(db_session)
    perm = pr.create_permission(resource_id=tbl_id, permission_type_id=pt, effect="ALLOW")
    ir.add_role_permission(role.id, perm.id)
    db_session.commit()

    bundle = PolicyRepository(db_session).load_permission_bundle(
        user_id=user.id,
        group_ids=[g.id],
        direct_role_ids=[],
        inherited_role_ids=[role.id],
    )
    anc = frozenset(ResourceRepository(db_session).get_ancestor_resource_ids(tbl_id))
    assert resolve_from_bundle(bundle, anc, "SELECT").decision == DecisionType.ALLOW


def test_deny_beats_allow(db_session: Session) -> None:
    _, _, tbl_id, col_id = _tree(db_session)
    pt = _select_type_id(db_session)
    pr = PermissionRepository(db_session)
    allow_p = pr.create_permission(resource_id=tbl_id, permission_type_id=pt, effect="ALLOW")
    deny_p = pr.create_permission(resource_id=col_id, permission_type_id=pt, effect="DENY")
    ir = IdentityRepository(db_session)
    user = ir.create_user("duser", "d@e.com")
    ir.add_user_permission(user.id, allow_p.id)
    ir.add_user_permission(user.id, deny_p.id)
    db_session.commit()

    bundle = PolicyRepository(db_session).load_permission_bundle(
        user_id=user.id,
        group_ids=[],
        direct_role_ids=[],
        inherited_role_ids=[],
    )
    anc = frozenset(ResourceRepository(db_session).get_ancestor_resource_ids(col_id))
    dec = resolve_from_bundle(bundle, anc, "SELECT")
    assert dec.decision == DecisionType.DENY


def test_default_deny(db_session: Session) -> None:
    _, _, tbl_id, _ = _tree(db_session)
    ir = IdentityRepository(db_session)
    user = ir.create_user("nouser", "n@e.com")
    db_session.commit()
    bundle = PolicyRepository(db_session).load_permission_bundle(
        user_id=user.id,
        group_ids=[],
        direct_role_ids=[],
        inherited_role_ids=[],
    )
    anc = frozenset(ResourceRepository(db_session).get_ancestor_resource_ids(tbl_id))
    dec = resolve_from_bundle(bundle, anc, "SELECT")
    assert dec.decision == DecisionType.DENY
    assert dec.deny_reason == "default_deny"


def test_row_filters_and_mask_output(db_session: Session) -> None:
    _, _, tbl_id, _ = _tree(db_session)
    ir = IdentityRepository(db_session)
    user = ir.create_user("muser", "m@e.com")
    pt = _select_type_id(db_session)
    pr = PermissionRepository(db_session)
    p1 = pr.create_permission(resource_id=tbl_id, permission_type_id=pt, effect="ALLOW")
    pr.create_row_filter(permission_id=p1.id, condition_expr="tenant_id = 1")
    p2 = pr.create_permission(resource_id=tbl_id, permission_type_id=pt, effect="ALLOW")
    pr.create_row_filter(permission_id=p2.id, condition_expr="region = 'VN'")
    pr.upsert_column_mask(
        permission_id=p2.id, mask_type="PARTIAL", mask_pattern=None
    )
    ir.add_user_permission(user.id, p1.id)
    ir.add_user_permission(user.id, p2.id)
    db_session.commit()

    bundle = PolicyRepository(db_session).load_permission_bundle(
        user_id=user.id,
        group_ids=[],
        direct_role_ids=[],
        inherited_role_ids=[],
    )
    anc = frozenset(ResourceRepository(db_session).get_ancestor_resource_ids(tbl_id))
    dec = resolve_from_bundle(bundle, anc, "SELECT")
    assert dec.decision == DecisionType.ALLOW_WITH_FILTER_AND_MASK
    assert len(dec.row_filter_exprs) == 2
    combined = combine_row_filters(dec.row_filter_exprs)
    assert "tenant_id = 1" in combined and "region = 'VN'" in combined


def test_combine_row_filters_empty() -> None:
    assert combine_row_filters([]) is None


def test_lineage_unknown_resource_deny(db_session: Session) -> None:
    from app.cache.redis_client import MemoryUserContextCache

    ir = IdentityRepository(db_session)
    user = ir.create_user("x", "x@e.com")
    db_session.commit()
    cache = MemoryUserContextCache()
    try:
        dec = resolve_access(
            db_session,
            _ctx(user.id),
            uuid.uuid4(),
            "SELECT",
            cache,
            60,
        )
        assert dec.decision == DecisionType.DENY
        assert dec.deny_reason == "unknown_resource"
    finally:
        cache.close()


def test_fail_closed_resolve_exception(db_session: Session) -> None:
    from app.cache.redis_client import MemoryUserContextCache

    ir = IdentityRepository(db_session)
    user = ir.create_user("e", "e@e.com")
    _, _, tbl_id, _ = _tree(db_session)
    db_session.commit()
    cache = MemoryUserContextCache()
    try:
        with patch.object(
            ResourceRepository,
            "get_ancestor_resource_ids",
            side_effect=RuntimeError("db down"),
        ):
            dec = resolve_access(
                db_session,
                _ctx(user.id),
                tbl_id,
                "SELECT",
                cache,
                60,
            )
        assert dec.decision == DecisionType.DENY
        assert dec.deny_reason == "policy_resolve_error"
    finally:
        cache.close()


def test_snapshot_cache_version_invalidation(db_session: Session) -> None:
    from app.cache.redis_client import MemoryUserContextCache

    _, _, tbl_id, _ = _tree(db_session)
    ir = IdentityRepository(db_session)
    user = ir.create_user("cacheu", "c@e.com")
    pt = _select_type_id(db_session)
    pr = PermissionRepository(db_session)
    perm = pr.create_permission(resource_id=tbl_id, permission_type_id=pt, effect="ALLOW")
    ir.add_user_permission(user.id, perm.id)
    db_session.commit()

    cache = MemoryUserContextCache()
    try:
        v0 = get_permission_version()
        ctx = _ctx(user.id)
        resolve_access(db_session, ctx, tbl_id, "SELECT", cache, 300)
        raw = cache.get(permission_snapshot_key(user.id))
        assert raw is not None
        data = json.loads(raw.decode("utf-8"))
        assert data["pv"] == v0

        bump_permission_version()
        v1 = get_permission_version()
        assert v1 > v0
        resolve_access(db_session, ctx, tbl_id, "SELECT", cache, 300)
        data2 = json.loads(cache.get(permission_snapshot_key(user.id)).decode("utf-8"))
        assert data2["pv"] == v1
    finally:
        cache.close()


def test_policy_bundle_load_called_once_with_cache(
    db_session: Session, auth_client: TestClient
) -> None:
    _, _, tbl_id, _ = _tree(db_session)
    ir = IdentityRepository(db_session)
    user = ir.create_user("apiu", "a@e.com")
    pt = _select_type_id(db_session)
    pr = PermissionRepository(db_session)
    perm = pr.create_permission(resource_id=tbl_id, permission_type_id=pt, effect="ALLOW")
    ir.add_user_permission(user.id, perm.id)
    db_session.commit()

    claims = IamUserClaims(
        user_id=user.id,
        username="apiu",
        email="a@e.com",
        is_active=True,
    )
    _install_mock_iam(auth_client, claims)

    calls: list[int] = []
    _orig = PolicyRepository.load_permission_bundle

    def _tracking(self: PolicyRepository, **kwargs: object) -> object:
        calls.append(1)
        return _orig(self, **kwargs)

    with patch.object(PolicyRepository, "load_permission_bundle", _tracking):
        r1 = auth_client.post(
            "/api/v1/runtime/authorize",
            headers={"Authorization": "Bearer t"},
            json={"resource_id": str(tbl_id), "action": "SELECT"},
        )
        r2 = auth_client.post(
            "/api/v1/runtime/authorize",
            headers={"Authorization": "Bearer t"},
            json={"resource_id": str(tbl_id), "action": "SELECT"},
        )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["decision"] == "ALLOW"
    assert len(calls) == 1


def test_authorize_endpoint_deny(auth_client: TestClient, db_session: Session) -> None:
    _, _, tbl_id, _ = _tree(db_session)
    ir = IdentityRepository(db_session)
    user = ir.create_user("denyapi", "da@e.com")
    db_session.commit()
    claims = IamUserClaims(
        user_id=user.id,
        username="denyapi",
        email="da@e.com",
        is_active=True,
    )
    _install_mock_iam(auth_client, claims)
    r = auth_client.post(
        "/api/v1/runtime/authorize",
        headers={"Authorization": "Bearer x"},
        json={"resource_id": str(tbl_id), "action": "SELECT"},
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "DENY"
