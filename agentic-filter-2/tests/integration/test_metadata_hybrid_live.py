"""Live smoke: hybrid kNN + DESCRIBE filter with agri_agent (OpenSearch + Postgres)."""

from __future__ import annotations

import os
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.api.deps import get_db
from app.core.config import get_settings
from app.main import create_app
from app.services.metadata_embedding import embedding_dependencies_available
from scripts.seed_agri_integration_user import integration_username, seed_agri_integration_user

pytestmark = pytest.mark.integration

sentence_transformers = pytest.importorskip(
    "sentence_transformers",
    reason='Install metadata extras: pip install -e ".[metadata]"',
)


def _opensearch_env_from_settings(monkeypatch: pytest.MonkeyPatch, cfg) -> None:
    base = cfg.opensearch_effective_base_url
    if not base:
        pytest.skip("OpenSearch not configured in environment")
    monkeypatch.setenv("OPENSEARCH_BASE_URL", base)
    if cfg.opensearch_user:
        monkeypatch.setenv("OPENSEARCH_USER", cfg.opensearch_user)
    if cfg.opensearch_password:
        monkeypatch.setenv("OPENSEARCH_PASSWORD", cfg.opensearch_password)
    monkeypatch.setenv("OPENSEARCH_INDEX", cfg.opensearch_index)
    monkeypatch.setenv(
        "OPENSEARCH_VERIFY_CERTS", "true" if cfg.opensearch_verify_certs else "false"
    )
    monkeypatch.setenv("METADATA_HYBRID_ENABLED", "true")
    get_settings.cache_clear()


@pytest.mark.integration
def test_metadata_hybrid_live_agri_agent(
    integration_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not embedding_dependencies_available():
        pytest.skip("sentence-transformers not installed")

    monkeypatch.setenv("DATABASE_URL", integration_database_url)
    monkeypatch.setenv("RUNTIME_POSTGRES_URL", integration_database_url)
    monkeypatch.setenv("USER_CONTEXT_CACHE_BACKEND", "memory")
    get_settings.cache_clear()

    cfg = get_settings()
    _opensearch_env_from_settings(monkeypatch, cfg)

    eng = create_engine(integration_database_url)
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=eng)
    with Session() as session:
        seed_agri_integration_user(session)
        session.commit()
    eng.dispose()

    application = create_app()

    def override_get_db() -> Any:
        db = Session()
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    user_id = integration_username()

    with TestClient(application) as client:
        assert getattr(client.app.state, "metadata_embedder", None) is not None
        resp = client.post(
            "/api/v1/metadata/hybrid-search",
            json={
                "userId": user_id,
                "query": os.environ.get("METADATA_SMOKE_QUERY", "GL_ACCOUNT"),
                "size": 5,
                "recordType": "TABLE",
            },
            timeout=120.0,
        )

    application.dependency_overrides.clear()
    get_settings.cache_clear()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["debug"]["queryMode"] == "hybrid"
    assert body["data"]["debug"]["hybridLeg"] == "knn_bm25"
