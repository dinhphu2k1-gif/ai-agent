"""Phase 2 integration tests — POST SSE with mock supervisor graph."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.deps import create_chat_container, reset_chat_container, set_chat_container


class _MockSnapshot:
    def __init__(
        self,
        *,
        final_output: str = "",
        message_to_user: str = "",
        next_nodes: tuple[str, ...] = (),
    ) -> None:
        self.values = {
            "final_output": final_output,
            "message_to_user": message_to_user,
        }
        self.next = next_nodes


class MockSupervisorGraph:
    """Minimal graph stub — no OpenSearch / LLM."""

    def __init__(
        self,
        *,
        final_output: str = "SELECT id, name FROM gl_accounts LIMIT 10",
        hitl: bool = False,
    ) -> None:
        self._final_output = final_output
        self._hitl = hitl
        self._stream_done = False

    async def astream_events(self, current_input, config, version="v2"):
        self._stream_done = True
        yield {"event": "on_chain_start", "name": "planner"}
        yield {"event": "on_chain_start", "name": "sql_writer_worker_node"}

    def get_state(self, config):
        if self._hitl and self._stream_done:
            return _MockSnapshot(
                message_to_user="Which table should we focus on?",
                next_nodes=("clarification_node",),
            )
        return _MockSnapshot(final_output=self._final_output, next_nodes=())

    async def aget_state(self, config):
        return self.get_state(config)

    def update_state(self, config, values):
        if "final_output" in values and values.get("final_output") == "":
            self._final_output = ""

    async def aupdate_state(self, config, values):
        self.update_state(config, values)


def _parse_sse_events(raw: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    blocks = raw.replace("\r\n", "\n").split("\n\n")
    for block in blocks:
        if not block.strip() or block.strip().startswith(":"):
            continue
        event_name = "message"
        data_json = None
        for line in block.split("\n"):
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                import json

                data_json = json.loads(line.split(":", 1)[1].strip())
        if data_json is not None:
            events.append((event_name, data_json))
    return events


@pytest.fixture
def mock_client():
    reset_chat_container()
    container = create_chat_container(
        graph_app=MockSupervisorGraph(), force_memory=True
    )
    set_chat_container(container)
    return TestClient(create_app())


def test_post_sse_happy_path_event_order(mock_client):
    response = mock_client.post(
        "/api/v1/chat/channels/market-trends/messages",
        json={"type": "text", "content": "Cho tôi schema bảng GL_ACCOUNTS"},
        headers={"Accept": "text/event-stream"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    events = _parse_sse_events(response.text)
    names = [name for name, _ in events]
    assert names[0] == "run.start"
    assert "user.ack" in names
    assert "message.start" in names
    assert "trace.step" in names
    assert "content.paragraph" in names
    assert names[-1] == "message.end"

    paragraph_events = [p for n, p in events if n == "content.paragraph"]
    assert any("gl_accounts" in p.get("text", "").lower() for p in paragraph_events)


def test_post_sse_hitl_emits_action_prompt():
    reset_chat_container()
    container = create_chat_container(
        graph_app=MockSupervisorGraph(hitl=True), force_memory=True
    )
    set_chat_container(container)
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/chat/channels/market-trends/messages",
        json={"type": "text", "content": "Need help"},
        headers={"Accept": "text/event-stream"},
    )
    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    names = [name for name, _ in events]
    assert "action.prompt" in names


def test_post_sse_409_when_run_active():
    reset_chat_container()
    active: dict[str, str] = {"market-trends": "existing-run"}
    set_chat_container(
        create_chat_container(
            graph_app=MockSupervisorGraph(),
            active_runs=active,
            force_memory=True,
        )
    )
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/chat/channels/market-trends/messages",
        json={"type": "text", "content": "Second message"},
        headers={"Accept": "text/event-stream"},
    )
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "RUN_IN_PROGRESS"


def test_get_history_after_post_includes_new_messages(mock_client):
    mock_client.post(
        "/api/v1/chat/channels/threat-intel/messages",
        json={"type": "text", "content": "List GL tables"},
        headers={"Accept": "text/event-stream"},
    )
    history = mock_client.get(
        "/api/v1/chat/channels/threat-intel/messages",
        params={"page": 1, "pageSize": 50},
    )
    assert history.status_code == 200
    data = history.json()["data"]
    senders = [m["sender"] for m in data]
    assert "user" in senders
    assert "agent" in senders


def test_post_empty_text_returns_400(mock_client):
    response = mock_client.post(
        "/api/v1/chat/channels/market-trends/messages",
        json={"type": "text", "content": "   "},
        headers={"Accept": "text/event-stream"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_post_missing_body_returns_422(mock_client):
    response = mock_client.post(
        "/api/v1/chat/channels/market-trends/messages",
        json={},
        headers={"Accept": "text/event-stream"},
    )
    assert response.status_code == 422
