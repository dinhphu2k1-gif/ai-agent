"""Fixtures for optional integration tests (PostgreSQL, OpenSearch)."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
import httpx
from sqlalchemy import create_engine, text

REPO_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_OPENSEARCH_URL = "http://127.0.0.1:9201"

# Matches docker-compose.yml (postgres service). Used when FILTER_INTEGRATION_DATABASE_URL is unset.
_DEFAULT_INTEGRATION_URL = (
    "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
)


def _postgres_reachable(url: str, *, connect_timeout: int = 2) -> bool:
    try:
        eng = create_engine(
            url,
            pool_pre_ping=False,
            connect_args={"connect_timeout": connect_timeout},
        )
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        eng.dispose()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def integration_database_url() -> str:
    explicit = os.environ.get("FILTER_INTEGRATION_DATABASE_URL", "").strip()
    if explicit:
        if not _postgres_reachable(explicit):
            pytest.skip(
                "FILTER_INTEGRATION_DATABASE_URL is set but PostgreSQL is not reachable "
                f"(check URL / network): {explicit!r}"
            )
        return explicit

    if _postgres_reachable(_DEFAULT_INTEGRATION_URL):
        os.environ.setdefault(
            "FILTER_INTEGRATION_DATABASE_URL", _DEFAULT_INTEGRATION_URL
        )
        return _DEFAULT_INTEGRATION_URL

    pytest.skip(
        "PostgreSQL integration: no URL set and default stack not reachable. "
        f"Start Postgres (e.g. `docker compose up -d postgres`) or set "
        f"FILTER_INTEGRATION_DATABASE_URL. Default tried: {_DEFAULT_INTEGRATION_URL!r}"
    )


def _opensearch_reachable(url: str) -> bool:
    base = url.rstrip("/")
    try:
        with httpx.Client(timeout=3.0) as c:
            r = c.get(f"{base}/")
            return r.status_code < 500
    except Exception:
        return False


@pytest.fixture(scope="session")
def integration_opensearch_base_url() -> str:
    explicit = os.environ.get("FILTER_INTEGRATION_OPENSEARCH_URL", "").strip()
    if explicit:
        if not _opensearch_reachable(explicit):
            pytest.skip(
                "FILTER_INTEGRATION_OPENSEARCH_URL is set but OpenSearch is not reachable: "
                f"{explicit!r}"
            )
        return explicit.rstrip("/")

    if _opensearch_reachable(_DEFAULT_OPENSEARCH_URL):
        os.environ.setdefault(
            "FILTER_INTEGRATION_OPENSEARCH_URL", _DEFAULT_OPENSEARCH_URL
        )
        return _DEFAULT_OPENSEARCH_URL.rstrip("/")

    pytest.skip(
        "OpenSearch integration: no URL set and default stack not reachable. "
        "Start OpenSearch (e.g. `docker compose up -d opensearch`) or set "
        f"FILTER_INTEGRATION_OPENSEARCH_URL. Default tried: {_DEFAULT_OPENSEARCH_URL!r}"
    )


@pytest.fixture(scope="session")
def configured_env_urls() -> tuple[str, str]:
    """Permission catalog + runtime Postgres from .env (does not wipe DB).

    Skips when either database is unreachable or COREDB catalog is missing.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        pytest.skip("python-dotenv required for configured-env integration tests")

    load_dotenv(REPO_ROOT / ".env")
    from app.core.config import Settings

    settings = Settings()
    catalog = str(settings.database_url)
    runtime = settings.effective_runtime_postgres_url

    if not _postgres_reachable(catalog):
        pytest.skip(f"DATABASE_URL not reachable: {catalog!r}")
    if not _postgres_reachable(runtime):
        pytest.skip(f"Runtime Postgres not reachable: {runtime!r}")

    eng = create_engine(catalog, connect_args={"connect_timeout": 3})
    try:
        with eng.connect() as conn:
            row = conn.execute(
                text("SELECT 1 FROM databases WHERE name = 'COREDB' LIMIT 1")
            ).first()
            if row is None:
                pytest.skip("COREDB catalog not seeded (run seed_gl_resource_dictionary.py)")
            user = conn.execute(
                text("SELECT 1 FROM users WHERE username = 'agri_agent' LIMIT 1")
            ).first()
            if user is None:
                pytest.skip("agri_agent user not found (run seed_agri_integration_user.py)")
    finally:
        eng.dispose()

    return catalog, runtime


@pytest.fixture
def live_sql_client(
    configured_env_urls: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> Generator:
    """FastAPI client wired to configured catalog + runtime Postgres."""
    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.main import create_app

    catalog, runtime = configured_env_urls
    monkeypatch.setenv("DATABASE_URL", catalog)
    monkeypatch.setenv("RUNTIME_POSTGRES_URL", runtime)
    monkeypatch.setenv("USER_CONTEXT_CACHE_BACKEND", "memory")
    get_settings.cache_clear()

    with TestClient(create_app()) as client:
        yield client

    get_settings.cache_clear()


@pytest.fixture
def alembic_clean_database(integration_database_url: str) -> None:
    """Wipe and recreate app schema via Alembic (only safe on a disposable DB)."""
    env = {**os.environ, "DATABASE_URL": integration_database_url}
    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "base"],
        cwd=str(REPO_ROOT),
        env=env,
        check=True,
        timeout=120,
    )
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(REPO_ROOT),
        env=env,
        check=True,
        timeout=120,
    )
