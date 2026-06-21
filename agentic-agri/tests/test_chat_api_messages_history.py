"""Phase 1: GET /api/v1/chat/channels/{channelId}/messages."""

from fastapi.testclient import TestClient

from api.app import create_app
from api.deps import reset_chat_container


def test_market_trends_history_has_user_agent_and_action_prompt():
    reset_chat_container()
    client = TestClient(create_app())
    response = client.get(
        "/api/v1/chat/channels/market-trends/messages",
        params={"page": 1, "pageSize": 50},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["currentPage"] == 1
    assert body["totalItems"] == 3
    assert body["totalPages"] == 1
    assert len(body["data"]) == 3

    senders = [message["sender"] for message in body["data"]]
    assert senders == ["user", "agent", "action_prompt"]

    agent = body["data"][1]
    assert "agentData" in agent
    assert agent["agentData"]["paragraphs"]
    assert agent["agentData"]["executionTrace"]
    assert agent["agentData"]["tableRows"]
    assert agent["agentData"]["actionButtons"]

    prompt = body["data"][2]
    assert prompt["promptData"]["title"] == "Awaiting your direction"
    assert len(prompt["promptData"]["options"]) == 3
    assert prompt["promptData"]["customOptionLabel"] == "Option D: Custom Input"


def test_unknown_channel_returns_404():
    reset_chat_container()
    client = TestClient(create_app())
    response = client.get("/api/v1/chat/channels/unknown/messages")

    assert response.status_code == 404


def test_empty_channel_returns_empty_page():
    reset_chat_container()
    client = TestClient(create_app())
    response = client.get(
        "/api/v1/chat/channels/threat-intel/messages",
        params={"page": 1, "pageSize": 50},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["totalItems"] == 0
    assert body["totalPages"] == 0


def test_pagination_first_page():
    reset_chat_container()
    client = TestClient(create_app())
    response = client.get(
        "/api/v1/chat/channels/market-trends/messages",
        params={"page": 1, "pageSize": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 2
    assert body["totalItems"] == 3
    assert body["totalPages"] == 2
    assert body["currentPage"] == 1
