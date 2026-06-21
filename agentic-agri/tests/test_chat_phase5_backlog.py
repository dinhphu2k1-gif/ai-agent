"""Phase 5 backlog — attachments, deltas, recovery, async POST, retention, ui_options."""

from __future__ import annotations

import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.deps import create_chat_container, reset_chat_container, set_chat_container
from api.middleware.rate_limit import reset_rate_limiter
from chat.mappers.agent_message_mapper import build_action_prompt_data
from chat.repositories.run_event_repository import PostgresRunEventRepository
from chat.settings import get_chat_settings
from universal_agent.supervisor.state import PlannerDecision, PlannerUIOption

from chat_graph_mocks import wire_async_graph_state


def _parse_sse_events(raw: str) -> list[tuple[str | None, dict]]:
    events: list[tuple[str | None, dict]] = []
    for block in raw.split("\n\n"):
        if not block.strip():
            continue
        event_name = None
        data: dict = {}
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_name = line.removeprefix("event: ").strip()
            elif line.startswith("data: "):
                data = json.loads(line.removeprefix("data: "))
        events.append((event_name, data))
    return events


async def _delta_then_done_async_iter(*_args, **_kwargs):
    for piece in ("Hel", "lo"):
        yield {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_node": "result_synthesizer"},
            "data": {"chunk": MagicMock(content=piece)},
        }


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CHAT_USE_MEMORY", "true")
    monkeypatch.setenv("CHAT_ENFORCE_CHANNEL_ACL", "false")
    monkeypatch.setenv("CHAT_EMIT_CONTENT_DELTA", "true")
    get_chat_settings.cache_clear()
    reset_rate_limiter()
    reset_chat_container()
    set_chat_container(create_chat_container(force_memory=True))
    yield TestClient(create_app())
    reset_chat_container()
    reset_rate_limiter()
    get_chat_settings.cache_clear()


def test_build_action_prompt_uses_ui_options():
    data = build_action_prompt_data(
        "Pick next step",
        ui_options=[
            {"label": "Option A", "actionId": "option_a"},
            {"label": "Option B", "actionId": "option_b"},
            {"label": "Option C", "actionId": "option_c"},
        ],
    )
    assert len(data.options) == 3
    assert data.options[0].action_id == "option_a"
    assert data.options[0].label != "Pick next step"


def test_planner_decision_accepts_ui_options():
    decision = PlannerDecision(
        intent="ask_user",
        reasoning="need input",
        message_to_user="How should we proceed?",
        ui_options=[
            PlannerUIOption(label="A", action_id="option_a"),
            PlannerUIOption(label="B", action_id="option_b"),
        ],
    )
    assert len(decision.ui_options or []) == 2


def test_system_message_in_channel_history(client):
    response = client.get("/api/v1/chat/channels/market-trends/messages")
    assert response.status_code == 200
    senders = [m["sender"] for m in response.json()["data"]]
    assert "system" in senders


def test_get_message_by_id_returns_agent_data(client):
    listed = client.get("/api/v1/chat/channels/market-trends/messages").json()
    agent_id = next(m["id"] for m in listed["data"] if m["sender"] == "agent")
    response = client.get(f"/api/v1/chat/messages/{agent_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["agentData"]["paragraphs"]


def test_post_async_returns_202_and_stream_run(client):
    mock_graph = MagicMock()
    wire_async_graph_state(mock_graph, values={"final_output": "Done."})
    mock_graph.astream_events = lambda *a, **k: _empty_async_iter()

    with patch(
        "chat.adapters.supervisor_stream.SupervisorStreamAdapter._get_graph",
        return_value=mock_graph,
    ):
        post = client.post(
            "/api/v1/chat/channels/threat-intel/messages?async=true",
            json={"type": "text", "content": "async hello"},
        )
    assert post.status_code == 202
    run_id = post.json()["data"]["runId"]
    user_message_id = post.json()["data"]["userMessageId"]
    assert run_id
    assert user_message_id

    with patch(
        "chat.adapters.supervisor_stream.SupervisorStreamAdapter._get_graph",
        return_value=mock_graph,
    ):
        stream = client.get(
            f"/api/v1/chat/runs/{run_id}/stream",
            headers={"Accept": "text/event-stream"},
        )
    assert stream.status_code == 200
    names = [e[0] for e in _parse_sse_events(stream.text)]
    assert "run.start" in names
    assert "user.ack" in names


async def _empty_async_iter():
    if False:
        yield {}


def test_content_delta_events_emitted(monkeypatch, client):
    mock_graph = MagicMock()
    wire_async_graph_state(
        mock_graph, values={"final_output": "Final paragraph."}
    )
    mock_graph.astream_events = _delta_then_done_async_iter

    with patch(
        "chat.adapters.supervisor_stream.SupervisorStreamAdapter._get_graph",
        return_value=mock_graph,
    ):
        response = client.post(
            "/api/v1/chat/channels/threat-intel/messages",
            json={"type": "text", "content": "stream deltas"},
            headers={"Accept": "text/event-stream"},
        )
    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    delta_events = [e for e in events if e[0] == "content.delta"]
    paragraph_events = [e for e in events if e[0] == "content.paragraph"]
    assert len(delta_events) >= 2
    # Avoid duplicate full text when synthesizer already streamed via delta.
    assert len(paragraph_events) == 0
    assert delta_events[0][1].get("paragraphIndex") == 0


def test_upload_attachment_and_post_with_ids(client, tmp_path, monkeypatch):
    monkeypatch.setenv("CHAT_ATTACHMENT_STORAGE_PATH", str(tmp_path / "atts"))
    get_chat_settings.cache_clear()
    reset_chat_container()
    set_chat_container(create_chat_container(force_memory=True))
    test_client = TestClient(create_app())

    upload = test_client.post(
        "/api/v1/chat/channels/threat-intel/attachments",
        files={"file": ("notes.txt", io.BytesIO(b"hello attach"), "text/plain")},
    )
    assert upload.status_code == 201
    attachment_id = upload.json()["data"]["attachmentId"]

    mock_graph = MagicMock()
    wire_async_graph_state(mock_graph)
    mock_graph.astream_events = lambda *a, **k: _empty_async_iter()

    with patch(
        "chat.adapters.supervisor_stream.SupervisorStreamAdapter._get_graph",
        return_value=mock_graph,
    ):
        post = test_client.post(
            "/api/v1/chat/channels/threat-intel/messages?async=true",
            json={
                "type": "text",
                "content": "see attachment",
                "attachmentIds": [attachment_id],
            },
        )
    assert post.status_code == 202
    message_id = post.json()["data"]["userMessageId"]
    got = test_client.get(f"/api/v1/chat/messages/{message_id}").json()
    assert got["data"]["attachments"]
    assert got["data"]["attachments"][0]["fileName"] == "notes.txt"


def test_delete_older_than_days_on_repository(monkeypatch):
    class _FakeCursor:
        rowcount = 42

        def execute(self, *_a, **_k):
            return None

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    class _FakeConn:
        def cursor(self):
            return _FakeCursor()

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(
        "chat.repositories.run_event_repository.transaction",
        lambda: _FakeConn(),
    )
    repo = PostgresRunEventRepository()
    assert repo.delete_older_than_days(7) == 42
