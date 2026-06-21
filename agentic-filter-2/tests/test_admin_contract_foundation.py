"""M1: admin contract envelope, pagination, identity repo extensions."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.admin_response import fail, ok
from app.repositories.identity_repo import IdentityRepository
from app.schemas.admin_contract import PageParams, build_pageable


def test_api_response_ok_and_fail_shape() -> None:
    wrapped = ok({"items": []}, message="OK")
    assert wrapped.success is True
    assert wrapped.message == "OK"
    assert wrapped.data == {"items": []}

    err = fail("bad", code="VALIDATION_ERROR", field="pageSize")
    assert err.success is False
    assert err.data is not None
    assert err.data.code == "VALIDATION_ERROR"
    assert err.data.field == "pageSize"


def test_page_params_one_based_offset() -> None:
    params = PageParams(page=1, page_size=10)
    assert params.offset == 0
    params2 = PageParams(page=3, page_size=25)
    assert params2.offset == 50


def test_page_params_rejects_invalid_page_size() -> None:
    with pytest.raises(ValueError, match="pageSize"):
        PageParams(page=1, page_size=0)


def test_build_pageable_first_page_and_beyond_range() -> None:
    items = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    page1 = build_pageable(items[:2], page=1, page_size=2, total_items=3)
    assert page1.current_page == 1
    assert page1.total_items == 3
    assert page1.total_pages == 2
    assert len(page1.data) == 2

    empty = build_pageable([], page=99, page_size=10, total_items=3)
    assert empty.data == []
    assert empty.current_page == 99
    assert empty.total_items == 3
    assert empty.total_pages == 1


def test_identity_repo_list_users_pagination(db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    for i in range(5):
        ir.create_user(f"user{i}", f"user{i}@example.com", full_name=f"User {i}")

    rows, total = ir.list_users(page=1, page_size=2)
    assert total == 5
    assert len(rows) == 2

    rows_p3, total_p3 = ir.list_users(page=3, page_size=2)
    assert total_p3 == 5
    assert len(rows_p3) == 1

    rows_search, total_search = ir.list_users(page=1, page_size=10, search="user2")
    assert total_search == 1
    assert rows_search[0].username == "user2"


def test_identity_repo_get_user_by_id_eager_loads(db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    user = ir.create_user("eager", "eager@example.com")
    group = ir.create_group("g1")
    role = ir.create_role("r1", display_name="Role One")
    ir.add_user_to_group(user.id, group.id)
    ir.add_user_role(user.id, role.id)

    loaded = ir.get_user_by_id(user.id)
    assert loaded is not None
    assert {g.id for g in loaded.groups} == {group.id}
    assert {r.id for r in loaded.direct_roles} == {role.id}


def test_identity_repo_add_user_role_idempotent(db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    user = ir.create_user("idem", "idem@example.com")
    role = ir.create_role("idem-role")

    ir.add_user_role(user.id, role.id)
    ir.add_user_role(user.id, role.id)

    assert len(ir.list_users_for_role(role.id)) == 1


def test_identity_repo_remove_user_role_and_list_for_role(db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    user = ir.create_user("rem", "rem@example.com")
    other = ir.create_user("other", "other@example.com")
    role = ir.create_role("rem-role")
    ir.add_user_role(user.id, role.id)
    ir.add_user_role(other.id, role.id)

    assert len(ir.list_users_for_role(role.id)) == 2
    assert ir.remove_user_role(user.id, role.id) is True
    assert ir.remove_user_role(user.id, role.id) is False
    remaining = ir.list_users_for_role(role.id)
    assert len(remaining) == 1
    assert remaining[0].id == other.id


def test_create_role_defaults_display_name(db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    role = ir.create_role("Technical_Name")
    assert role.display_name == "Technical_Name"


def test_admin_roles_envelope_empty(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/roles?page=1&pageSize=10")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "OK"
    assert body["data"]["data"] == []
    assert body["data"]["currentPage"] == 1
    assert body["data"]["totalItems"] == 0


def test_admin_roles_envelope_with_seed(admin_client: TestClient, db_session: Session) -> None:
    ir = IdentityRepository(db_session)
    ir.create_role("Alpha", display_name="Alpha Display")
    ir.create_role("Beta", display_name="Beta Display")
    db_session.flush()

    response = admin_client.get("/api/v1/admin/roles?page=1&pageSize=1&sort=name")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["totalItems"] == 2
    assert payload["totalPages"] == 2
    assert len(payload["data"]) == 1
    assert payload["data"][0]["name"] == "Alpha"


def test_admin_roles_rejects_page_size_zero(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/roles?page=1&pageSize=0")
    # App maps RequestValidationError to 400 (see main.create_app).
    assert response.status_code == 400
