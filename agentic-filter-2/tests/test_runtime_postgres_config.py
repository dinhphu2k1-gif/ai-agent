"""Runtime Postgres URL resolution (separate from permission DATABASE_URL)."""

from __future__ import annotations

import pytest

from app.core.config import Settings


def test_runtime_url_from_pg_env_components(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://filter:filter@localhost:5433/filter_db")
    monkeypatch.delenv("RUNTIME_POSTGRES_URL", raising=False)
    monkeypatch.setenv("PG_HOST", "db.example.com")
    monkeypatch.setenv("PG_PORT", "5432")
    monkeypatch.setenv("PG_USER", "admin")
    monkeypatch.setenv("PG_PASSWORD", "p@ss")
    monkeypatch.setenv("PG_DATABASE", "my_database")

    cfg = Settings()
    assert cfg.effective_runtime_postgres_url == (
        "postgresql+psycopg://admin:p%40ss@db.example.com:5432/my_database"
    )


def test_runtime_url_explicit_overrides_pg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://filter:filter@localhost:5433/filter_db")
    monkeypatch.setenv("RUNTIME_POSTGRES_URL", "postgresql+psycopg://run:run@runhost:5432/runtime")
    monkeypatch.setenv("PG_DATABASE", "my_database")
    monkeypatch.setenv("PG_USER", "admin")

    cfg = Settings()
    assert cfg.effective_runtime_postgres_url == (
        "postgresql+psycopg://run:run@runhost:5432/runtime"
    )


def test_runtime_url_falls_back_to_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    catalog = "postgresql+psycopg://filter:filter@localhost:5433/filter_db"
    monkeypatch.setenv("DATABASE_URL", catalog)
    monkeypatch.delenv("RUNTIME_POSTGRES_URL", raising=False)
    monkeypatch.setenv("PG_DATABASE", "")
    monkeypatch.setenv("PG_USER", "")

    cfg = Settings()
    assert cfg.effective_runtime_postgres_url == catalog
