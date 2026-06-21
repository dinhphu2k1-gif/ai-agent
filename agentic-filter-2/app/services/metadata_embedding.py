"""Lazy-loaded query embeddings for metadata hybrid search (BAAI/bge-m3)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger(__name__)


class MetadataEmbeddingError(Exception):
    """Embedding model cannot be loaded or encode failed."""


class MetadataEmbeddingService:
    """SentenceTransformer wrapper aligned with agentic-agri OpenSearchClient."""

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.metadata_embedding_model
        self._expected_dim = settings.metadata_embedding_dim
        self._model: object | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def expected_dim(self) -> int:
        return self._expected_dim

    def encode_query(self, query_text: str) -> list[float]:
        """Normalized embedding vector for kNN on ``description_vector``."""
        text = query_text.strip()
        if not text:
            raise MetadataEmbeddingError("Query text is empty")
        model = self._load_model()
        try:
            vec = model.encode([text], normalize_embeddings=True)[0]  # type: ignore[union-attr]
            out = vec.tolist() if hasattr(vec, "tolist") else list(vec)
        except MetadataEmbeddingError:
            raise
        except Exception as e:
            raise MetadataEmbeddingError(f"Embedding encode failed: {e}") from e

        if len(out) != self._expected_dim:
            raise MetadataEmbeddingError(
                f"Embedding dimension {len(out)} != expected {self._expected_dim}"
            )
        return out

    def _load_model(self) -> object:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise MetadataEmbeddingError(
                "sentence-transformers is not installed. "
                'Install with: pip install -e ".[metadata]"'
            ) from e
        logger.info("Loading metadata embedding model %s", self._model_name)
        self._model = SentenceTransformer(self._model_name)
        logger.info("Metadata embedding model ready (dim=%s)", self._expected_dim)
        return self._model


def embedding_dependencies_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401

        return True
    except ImportError:
        return False
