"""OpenSearch settings: host/port URL build and index env aliases."""

from __future__ import annotations

import pytest

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_effective_base_url_from_host_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENSEARCH_BASE_URL", raising=False)
    monkeypatch.setenv("OPENSEARCH_HOST", "localhost")
    monkeypatch.setenv("OPENSEARCH_PORT", "9200")
    monkeypatch.setenv("OPENSEARCH_USE_SSL", "false")
    cfg = Settings()
    assert cfg.opensearch_effective_base_url == "http://localhost:9200"


def test_base_url_overrides_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSEARCH_BASE_URL", "http://127.0.0.1:9201")
    monkeypatch.setenv("OPENSEARCH_HOST", "ignored.example")
    cfg = Settings()
    assert cfg.opensearch_effective_base_url == "http://127.0.0.1:9201"


def test_opensearch_index_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSEARCH_INDEX", "data_dictionary")
    cfg = Settings()
    assert cfg.opensearch_index == "data_dictionary"


def test_opensearch_auth_when_user_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSEARCH_USER", "admin")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "secret")
    cfg = Settings()
    assert cfg.opensearch_auth == ("admin", "secret")


def test_effective_base_url_https_when_use_ssl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENSEARCH_BASE_URL", raising=False)
    monkeypatch.setenv("OPENSEARCH_HOST", "localhost")
    monkeypatch.setenv("OPENSEARCH_PORT", "9200")
    monkeypatch.setenv("OPENSEARCH_USE_SSL", "true")
    cfg = Settings()
    assert cfg.opensearch_effective_base_url == "https://localhost:9200"


def test_verify_certs_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSEARCH_VERIFY_CERTS", "false")
    cfg = Settings()
    assert cfg.opensearch_verify_certs is False
