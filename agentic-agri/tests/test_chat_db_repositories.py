"""Postgres chat repository tests — skip when CHAT_DATABASE_URL unset."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from chat.repositories.postgres_channel_repository import PostgresChannelRepository
from chat.repositories.postgres_message_repository import PostgresMessageRepository
from chat.repositories.run_repository import PostgresRunRepository, RunConflictError
from chat.repositories.thread_repository import PostgresThreadRepository
from chat.db import transaction


pytestmark = pytest.mark.skipif(
    not os.environ.get("CHAT_DATABASE_URL", "").strip(),
    reason="CHAT_DATABASE_URL not set",
)


@pytest.fixture(scope="module", autouse=True)
def _ensure_schema():
    import psycopg2
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    migration = root / "scripts" / "migrations" / "chat" / "001_init.sql"
    if migration.exists():
        from chat.db import run_migration_sql

        try:
            run_migration_sql(str(migration))
        except psycopg2.OperationalError as exc:
            pytest.skip(f"Cannot connect to CHAT_DATABASE_URL: {exc}")


@pytest.fixture(autouse=True)
def truncate_chat_tables():
    with transaction() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE chat.chat_run_events RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE chat.chat_runs RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE chat.chat_messages RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE chat.chat_threads RESTART IDENTITY CASCADE")
            cur.execute(
                """
                INSERT INTO chat.chat_channels (id, title, icon, category, sort_order)
                VALUES ('market-trends', 'Market Trends', 'trending_up', NULL, 0)
                ON CONFLICT (id) DO NOTHING
                """
            )
    yield


def test_channel_list_and_thread_get_or_create():
    channels = PostgresChannelRepository().list_all()
    assert any(channel.id == "market-trends" for channel in channels)

    thread_repo = PostgresThreadRepository()
    thread = thread_repo.get_or_create("market-trends", "test-user")
    assert thread.langgraph_thread_id == "test-user:market-trends"

    again = thread_repo.get_or_create("market-trends", "test-user")
    assert again.id == thread.id


def test_active_run_unique_index():
    thread_repo = PostgresThreadRepository()
    run_repo = PostgresRunRepository()
    msg_repo = PostgresMessageRepository(thread_repository=thread_repo)

    thread = thread_repo.get_or_create("market-trends", "run-user")
    user_msg = uuid4()

    with transaction() as conn:
        msg_repo.insert_user_message_on_conn(conn, thread.id, None, "hello", message_id=user_msg)
        run_repo.create_queued_on_conn(conn, thread.id, user_msg, {"type": "text"})

    with transaction() as conn:
        msg_repo.insert_user_message_on_conn(
            conn, thread.id, None, "second", message_id=uuid4()
        )
        with pytest.raises(RunConflictError):
            run_repo.create_queued_on_conn(
                conn, thread.id, uuid4(), {"type": "text"}
            )

    active = run_repo.get_active(thread.id)
    assert active is not None
    assert active.status == "queued"


def test_message_list_by_channel_for_user():
    thread_repo = PostgresThreadRepository()
    msg_repo = PostgresMessageRepository(thread_repository=thread_repo)
    thread = thread_repo.get_or_create("market-trends", "history-user")

    with transaction() as conn:
        msg_repo.insert_user_message_on_conn(
            conn, thread.id, None, "Question?", message_id=uuid4()
        )

    page = msg_repo.list_by_channel("market-trends", page=1, page_size=10, user_id="history-user")
    assert page is not None
    assert page.total_items >= 1
    assert page.items[0].content == "Question?"
