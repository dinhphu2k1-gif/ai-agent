import os
import sys
from pathlib import Path

import pytest

_TESTS_DIR = str(Path(__file__).resolve().parent)
sys.path.insert(0, _TESTS_DIR)
sys.path.insert(0, "F:/data/src/agentic-agri/scripts")
sys.path.insert(0, "F:/data/src/agentic-agri/src")

from scripts.postgres_scenario_catalog import SCENARIOS
from universal_agent.sql_writer_agent.db_executor_client import PostgresExecutorClient


def seeded_postgres_env():
    os.environ.setdefault("PG_HOST", "192.168.2.161")
    os.environ.setdefault("PG_PORT", "5432")
    os.environ.setdefault("PG_USER", "admin")
    os.environ.setdefault("PG_PASSWORD", "password123")
    os.environ.setdefault("PG_DATABASE", "my_database")
    os.environ.setdefault("SQL_EXECUTOR_DIALECT", "postgresql")
    return PostgresExecutorClient()


def scenario_catalog():
    return SCENARIOS


@pytest.fixture(autouse=True)
def _chat_api_uses_memory_repos(monkeypatch, request):
    """Keep chat API tests on in-memory repos unless running DB repository tests."""
    if request.module and request.module.__name__ == "test_chat_db_repositories":
        yield
        return

    from api.deps import reset_chat_container
    from api.middleware.rate_limit import reset_rate_limiter
    from api.settings import get_api_settings
    from chat.settings import get_chat_settings

    monkeypatch.setenv("CHAT_USE_MEMORY", "true")
    monkeypatch.setenv("CHAT_REQUIRE_AUTH", "false")
    monkeypatch.setenv("CHAT_ENFORCE_CHANNEL_ACL", "false")
    get_chat_settings.cache_clear()
    get_api_settings.cache_clear()
    reset_rate_limiter()
    reset_chat_container()
    yield
    reset_chat_container()
    reset_rate_limiter()
    get_chat_settings.cache_clear()
    get_api_settings.cache_clear()


def chat_database_url() -> str | None:
    """CHAT_DATABASE_URL for Phase 3 Postgres tests (optional)."""
    return os.environ.get("CHAT_DATABASE_URL", "").strip() or None


def truncate_chat_schema() -> None:
    """Clear chat tables between integration tests (requires CHAT_DATABASE_URL)."""
    url = chat_database_url()
    if not url:
        return
    from chat.db import transaction

    with transaction() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE chat.chat_run_events RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE chat.chat_runs RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE chat.chat_messages RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE chat.chat_threads RESTART IDENTITY CASCADE")
