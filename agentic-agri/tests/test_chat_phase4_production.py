"""Phase 4 production hardening — auth, ACL, validation, rate limit, idempotency."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.auth.jwt import encode_access_token
from api.deps import create_chat_container, reset_chat_container, set_chat_container
from api.middleware.rate_limit import reset_rate_limiter
from api.settings import get_api_settings
from chat.mappers.agent_message_mapper import build_sql_preview_table_events
from chat.repositories.channel_member_repository import InMemoryChannelMemberRepository
from chat.settings import get_chat_settings

from chat_graph_mocks import wire_async_graph_state


def _parse_sse_events(raw: str) -> list[tuple[str | None, dict]]:
    events: list[tuple[str | None, dict]] = []
    for block in raw.split("\n\n"):
        if not block.strip():
            continue
        event_name = None
        data = {}
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_name = line.removeprefix("event: ").strip()
            elif line.startswith("data: "):
                data = json.loads(line.removeprefix("data: "))
        events.append((event_name, data))
    return events


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CHAT_USE_MEMORY", "true")
    monkeypatch.setenv("CHAT_ENFORCE_CHANNEL_ACL", "false")
    get_chat_settings.cache_clear()
    reset_rate_limiter()
    reset_chat_container()
    set_chat_container(create_chat_container(force_memory=True))
    yield TestClient(create_app())
    reset_chat_container()
    reset_rate_limiter()
    get_chat_settings.cache_clear()
    get_api_settings.cache_clear()


def test_post_without_token_returns_401_when_auth_required(monkeypatch):
    monkeypatch.setenv("CHAT_REQUIRE_AUTH", "true")
    monkeypatch.setenv("CHAT_JWT_SECRET", "test-secret-phase4")
    get_api_settings.cache_clear()
    reset_chat_container()
    app = create_app()
    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/chat/channels/threat-intel/messages",
            json={"type": "text", "content": "hello"},
            headers={"Accept": "text/event-stream"},
        )
    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "UNAUTHORIZED"


def test_post_with_valid_jwt_succeeds(monkeypatch, client):
    monkeypatch.setenv("CHAT_REQUIRE_AUTH", "true")
    monkeypatch.setenv("CHAT_JWT_SECRET", "test-secret-phase4")
    get_api_settings.cache_clear()
    token = encode_access_token("dev-user")
    mock_graph = MagicMock()
    wire_async_graph_state(mock_graph)
    mock_graph.astream_events = lambda *a, **k: _empty_async_iter()

    with patch(
        "chat.adapters.supervisor_stream.SupervisorStreamAdapter._get_graph",
        return_value=mock_graph,
    ):
        response = client.post(
            "/api/v1/chat/channels/threat-intel/messages",
            json={"type": "text", "content": "ping"},
            headers={
                "Accept": "text/event-stream",
                "Authorization": f"Bearer {token}",
            },
        )
    assert response.status_code == 200


async def _empty_async_iter():
    if False:
        yield {}


def test_channel_forbidden_when_acl_enforced(monkeypatch):
    monkeypatch.setenv("CHAT_USE_MEMORY", "true")
    monkeypatch.setenv("CHAT_ENFORCE_CHANNEL_ACL", "true")
    get_chat_settings.cache_clear()
    reset_rate_limiter()
    reset_chat_container()

    members = InMemoryChannelMemberRepository(
        memberships={"dev-user": {"threat-intel"}}
    )
    container = create_chat_container(force_memory=True)
    container.channel_service._member_repository = members  # noqa: SLF001
    container.channel_access._members = members  # noqa: SLF001
    container.message_service._channel_access = container.channel_access  # noqa: SLF001
    set_chat_container(container)

    with TestClient(create_app()) as test_client:
        response = test_client.get(
            "/api/v1/chat/channels/insider-risk/messages",
        )
    assert response.status_code == 403
    assert response.json()["code"] == "CHANNEL_FORBIDDEN"


def test_empty_text_content_returns_400(client):
    response = client.post(
        "/api/v1/chat/channels/threat-intel/messages",
        json={"type": "text", "content": "   "},
        headers={"Accept": "text/event-stream"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_rate_limit_returns_429(monkeypatch, client):
    monkeypatch.setenv("CHAT_RATE_LIMIT_MAX", "2")
    monkeypatch.setenv("CHAT_RATE_LIMIT_WINDOW_SEC", "60")
    get_chat_settings.cache_clear()
    reset_rate_limiter()

    mock_graph = MagicMock()
    wire_async_graph_state(mock_graph)
    mock_graph.astream_events = lambda *a, **k: _empty_async_iter()

    headers = {"Accept": "text/event-stream"}
    with patch(
        "chat.adapters.supervisor_stream.SupervisorStreamAdapter._get_graph",
        return_value=mock_graph,
    ):
        for _ in range(2):
            r = client.post(
                "/api/v1/chat/channels/threat-intel/messages",
                json={"type": "text", "content": "a"},
                headers=headers,
            )
            assert r.status_code == 200
        third = client.post(
            "/api/v1/chat/channels/threat-intel/messages",
            json={"type": "text", "content": "b"},
            headers=headers,
        )
    assert third.status_code == 429
    assert third.headers.get("retry-after")
    assert third.json()["code"] == "RATE_LIMITED"


def test_run_in_progress_409_body(client):
    from api.deps import get_chat_container

    get_chat_container().run_service._active_runs["network-anomaly"] = "run-abc"  # noqa: SLF001

    response = client.post(
        "/api/v1/chat/channels/network-anomaly/messages",
        json={"type": "text", "content": "again"},
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "RUN_IN_PROGRESS"
    assert body["data"]["channelId"] == "network-anomaly"


def test_idempotency_key_replay_memory(client):
    mock_graph = MagicMock()
    wire_async_graph_state(mock_graph)
    mock_graph.astream_events = lambda *a, **k: _empty_async_iter()

    headers = {
        "Accept": "text/event-stream",
        "Idempotency-Key": "idem-test-1",
    }
    with patch(
        "chat.adapters.supervisor_stream.SupervisorStreamAdapter._get_graph",
        return_value=mock_graph,
    ):
        first = client.post(
            "/api/v1/chat/channels/threat-intel/messages",
            json={"type": "text", "content": "once"},
            headers=headers,
        )
        assert first.status_code == 200
        first_events = _parse_sse_events(first.text)
        run_ids = [
            data.get("runId")
            for name, data in first_events
            if name == "run.start"
        ]
        assert len(run_ids) == 1

        second = client.post(
            "/api/v1/chat/channels/threat-intel/messages",
            json={"type": "text", "content": "once"},
            headers=headers,
        )
        assert second.status_code == 200
        second_events = _parse_sse_events(second.text)
        replay_run_ids = [
            data.get("runId")
            for name, data in second_events
            if name == "run.start"
        ]
        assert replay_run_ids == run_ids
        assert len(second_events) <= len(first_events)


def test_agent_timeout_emits_error_event(monkeypatch):
    monkeypatch.setenv("CHAT_USE_MEMORY", "true")
    monkeypatch.setenv("CHAT_RUN_TIMEOUT_SEC", "0.05")
    get_chat_settings.cache_clear()
    reset_chat_container()
    set_chat_container(create_chat_container(force_memory=True))

    mock_graph = MagicMock()
    wire_async_graph_state(mock_graph)

    async def slow(*_args, **_kwargs):
        import asyncio

        await asyncio.sleep(2)
        yield {"event": "on_chain_start", "name": "planner"}

    mock_graph.astream_events = slow

    with TestClient(create_app()) as test_client:
        with patch(
            "chat.adapters.supervisor_stream.SupervisorStreamAdapter._get_graph",
            return_value=mock_graph,
        ):
            response = test_client.post(
                "/api/v1/chat/channels/threat-intel/messages",
                json={"type": "text", "content": "timeout"},
                headers={"Accept": "text/event-stream"},
            )
    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    error_events = [data for name, data in events if name == "error"]
    assert error_events
    assert error_events[0]["code"] == "AGENT_TIMEOUT"


def test_sql_preview_mapper_emits_table_and_buttons():
    preview = "region | actual | projected\n---|---|---\nNorth | 10 | 12"
    events = build_sql_preview_table_events("msg-1", preview)
    names = [name for name, _ in events]
    assert "table" in names
    assert "action.buttons" in names
