"""Metadata embedding service unit tests (no model download)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.config import Settings, get_settings
from app.services.metadata_embedding import (
    MetadataEmbeddingError,
    MetadataEmbeddingService,
)


def _settings(monkeypatch: pytest.MonkeyPatch, *, dim: int) -> Settings:
    monkeypatch.setenv("METADATA_EMBEDDING_DIM", str(dim))
    monkeypatch.setenv("METADATA_EMBEDDING_MODEL", "test/model")
    get_settings.cache_clear()
    return get_settings()


def test_encode_query_validates_dimension(monkeypatch: pytest.MonkeyPatch) -> None:
    svc = MetadataEmbeddingService(_settings(monkeypatch, dim=4))
    fake_model = MagicMock()
    fake_model.encode.return_value = [[0.1, 0.2, 0.3]]  # wrong dim
    svc._model = fake_model

    with pytest.raises(MetadataEmbeddingError, match="dimension"):
        svc.encode_query("hello")


def test_encode_query_success(monkeypatch: pytest.MonkeyPatch) -> None:
    svc = MetadataEmbeddingService(_settings(monkeypatch, dim=3))
    fake_model = MagicMock()
    fake_model.encode.return_value = [[0.1, 0.2, 0.3]]
    svc._model = fake_model

    vec = svc.encode_query("  query  ")
    assert vec == [0.1, 0.2, 0.3]
    fake_model.encode.assert_called_once()
    args, kwargs = fake_model.encode.call_args
    assert args[0] == ["query"]
    assert kwargs.get("normalize_embeddings") is True
