#!/usr/bin/env python3
"""Smoke metadata API against live OpenSearch + PostgreSQL (agri_agent).

Prerequisites:
  pip install -e ".[metadata]"
  python scripts/seed_gl_resource_dictionary.py
  python scripts/seed_agri_integration_user.py

Usage:
  python scripts/smoke_metadata_api.py
  python scripts/smoke_metadata_api.py --query "tài khoản kế toán"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps import get_db  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from contextlib import contextmanager

from app.db import configure_engine, get_session_factory  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.metadata_embedding import (  # noqa: E402
    MetadataEmbeddingError,
    embedding_dependencies_available,
)
from scripts.seed_agri_integration_user import (  # noqa: E402
    integration_username,
    seed_agri_integration_user,
)


def _print_result(label: str, resp) -> None:
    print(f"\n=== {label} ===")
    print(f"HTTP {resp.status_code}")
    try:
        body = resp.json()
    except Exception:
        print(resp.text[:500])
        return
    print(json.dumps(body, ensure_ascii=False, indent=2)[:4000])
    if resp.status_code != 200:
        return
    data = body.get("data") or {}
    hits = data.get("hits") or []
    debug = data.get("debug") or {}
    print(f"hits: {len(hits)} | queryMode={debug.get('queryMode')} hybridLeg={debug.get('hybridLeg')}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Smoke metadata API (agri_agent)")
    parser.add_argument("--query", default="GL_ACCOUNT", help="Search query text")
    parser.add_argument("--user-id", default=None, help="Trusted userId (default: agri_agent)")
    parser.add_argument("--skip-seed", action="store_true", help="Skip agri integration user seed")
    args = parser.parse_args()

    cfg = get_settings()
    user_id = args.user_id or integration_username()

    if not cfg.opensearch_effective_base_url:
        print("OpenSearch not configured (OPENSEARCH_HOST or OPENSEARCH_BASE_URL)", file=sys.stderr)
        return 1
    if cfg.metadata_hybrid_enabled and not embedding_dependencies_available():
        print(
            'Hybrid enabled but sentence-transformers missing. Run: pip install -e ".[metadata]"',
            file=sys.stderr,
        )
        return 1

    configure_engine(cfg.database_url)

    @contextmanager
    def _db_session():
        factory = get_session_factory()
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    if not args.skip_seed:
        with _db_session() as session:
            info = seed_agri_integration_user(session)
            print(f"Seeded integration user: {info['username']} ({info['user_id']})")

    app = create_app()

    def override_get_db():
        factory = get_session_factory()
        session = factory()
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    if getattr(app.state, "metadata_embedder", None) is not None:
        try:
            dim = app.state.metadata_embedder.encode_query("warmup")
            print(f"Embedding warmup OK (dim={len(dim)})")
        except MetadataEmbeddingError as e:
            print(f"Embedding warmup failed: {e}", file=sys.stderr)
            return 1

    payload_base = {"userId": user_id, "size": 5}

    with TestClient(app) as client:
        _print_result(
            "keyword-search",
            client.post(
                "/api/v1/metadata/keyword-search",
                json={**payload_base, "query": args.query},
            ),
        )
        _print_result(
            "hybrid-search",
            client.post(
                "/api/v1/metadata/hybrid-search",
                json={**payload_base, "query": args.query, "recordType": "TABLE"},
            ),
        )
        _print_result(
            "keyword-search (table filter)",
            client.post(
                "/api/v1/metadata/keyword-search",
                json={
                    **payload_base,
                    "query": args.query,
                    "tableName": "GL_ACCOUNT",
                },
            ),
        )

    app.dependency_overrides.clear()
    print("\nSmoke finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
