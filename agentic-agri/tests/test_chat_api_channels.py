"""Chat channels API — list, create, delete."""

from fastapi.testclient import TestClient

from api.app import create_app
from api.deps import create_chat_container, reset_chat_container, set_chat_container


def _memory_client() -> TestClient:
    reset_chat_container()
    set_chat_container(create_chat_container(force_memory=True))
    return TestClient(create_app())


def test_list_channels_returns_four_channels():
    client = _memory_client()
    response = client.get("/api/v1/chat/channels")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 4

    ids = {channel["id"] for channel in body["data"]}
    assert ids == {
        "threat-intel",
        "network-anomaly",
        "insider-risk",
        "market-trends",
    }


def test_channel_shape_matches_spec():
    client = _memory_client()
    response = client.get("/api/v1/chat/channels")
    market = next(c for c in response.json()["data"] if c["id"] == "market-trends")

    assert market["title"] == "Market Trends"
    assert market["icon"] == "trending_up"
    assert market.get("category") is None

    threat = next(c for c in response.json()["data"] if c["id"] == "threat-intel")
    assert threat["title"] == "threat-intel-global"
    assert threat["icon"] == "shield"
    assert threat["category"] == "Active Channels"


def test_create_channel_returns_201():
    client = _memory_client()
    response = client.post(
        "/api/v1/chat/channels",
        json={"title": "Q4 revenue analysis", "icon": "analytics"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    channel = body["data"]
    assert channel["title"] == "Q4 revenue analysis"
    assert channel["icon"] == "analytics"
    assert channel["category"] == "Active Channels"
    assert "-" in channel["id"]

    listed = client.get("/api/v1/chat/channels").json()["data"]
    assert any(c["id"] == channel["id"] for c in listed)


def test_create_channel_default_icon():
    client = _memory_client()
    response = client.post(
        "/api/v1/chat/channels",
        json={"title": "New workspace"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["icon"] == "forum"


def test_create_channel_empty_title_validation_error():
    client = _memory_client()
    response = client.post(
        "/api/v1/chat/channels",
        json={"title": "   "},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_delete_user_channel_returns_204():
    client = _memory_client()
    created = client.post(
        "/api/v1/chat/channels",
        json={"title": "Temporary channel"},
    ).json()["data"]
    channel_id = created["id"]

    delete_resp = client.delete(f"/api/v1/chat/channels/{channel_id}")
    assert delete_resp.status_code == 204

    listed_ids = {c["id"] for c in client.get("/api/v1/chat/channels").json()["data"]}
    assert channel_id not in listed_ids


def test_delete_seed_channel_forbidden():
    client = _memory_client()
    response = client.delete("/api/v1/chat/channels/market-trends")
    assert response.status_code == 403
    assert response.json()["code"] == "CHANNEL_FORBIDDEN"


def test_delete_unknown_channel_not_found():
    client = _memory_client()
    response = client.delete("/api/v1/chat/channels/does-not-exist")
    assert response.status_code == 404
    assert response.json()["code"] == "CHANNEL_NOT_FOUND"
