def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_id_header(client):
    response = client.get("/health", headers={"X-Request-ID": "fixed-id"})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "fixed-id"
