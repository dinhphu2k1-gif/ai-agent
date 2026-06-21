#!/usr/bin/env python3
"""Seed golden market-trends conversation into Postgres chat schema."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

load_dotenv(ROOT / ".env")

from chat.db import borrow_connection, run_migration_sql  # noqa: E402
from chat.fixtures.seed_data import MARKET_TRENDS_MESSAGES  # noqa: E402
from chat.settings import get_chat_settings  # noqa: E402


def main() -> None:
    settings = get_chat_settings()
    if not settings.database_url:
        print("CHAT_DATABASE_URL is required", file=sys.stderr)
        sys.exit(1)

    migration = ROOT / "scripts" / "migrations" / "chat" / "001_init.sql"
    if migration.exists():
        print(f"Applying migration {migration}...")
        run_migration_sql(str(migration))

    channel_id = "market-trends"
    user_id = os.environ.get("CHAT_SEED_USER_ID", "dev-user")
    langgraph_thread_id = f"{user_id}:{channel_id}"

    with borrow_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat.chat_threads (channel_id, user_id, langgraph_thread_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (channel_id, user_id) DO UPDATE
                SET langgraph_thread_id = EXCLUDED.langgraph_thread_id
                RETURNING id
                """,
                (channel_id, user_id, langgraph_thread_id),
            )
            thread_id = cur.fetchone()[0]

            cur.execute(
                "DELETE FROM chat.chat_messages WHERE thread_id = %s",
                (str(thread_id),),
            )

            for message in MARKET_TRENDS_MESSAGES:
                agent_data = None
                prompt_data = None
                if message.agent_data is not None:
                    agent_data = json.dumps(
                        message.agent_data.model_dump(by_alias=True, mode="json")
                    )
                if message.prompt_data is not None:
                    prompt_data = json.dumps(
                        message.prompt_data.model_dump(by_alias=True, mode="json")
                    )
                status = "pending" if message.sender == "action_prompt" else "final"
                cur.execute(
                    """
                    INSERT INTO chat.chat_messages (
                        id, thread_id, sender, content, agent_data, prompt_data, status, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s::timestamptz)
                    """,
                    (
                        str(uuid4()),
                        str(thread_id),
                        message.sender,
                        message.content,
                        agent_data,
                        prompt_data,
                        status,
                        message.timestamp,
                    ),
                )

        conn.commit()

    print(f"Seeded {len(MARKET_TRENDS_MESSAGES)} messages for thread {channel_id}/{user_id}")


if __name__ == "__main__":
    main()
