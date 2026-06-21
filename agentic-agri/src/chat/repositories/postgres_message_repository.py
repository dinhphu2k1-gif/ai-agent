"""Postgres-backed message history and run persistence helpers."""

from __future__ import annotations

import json
import math
from datetime import timezone
from typing import Any
from uuid import UUID, uuid4

from psycopg2.extensions import connection as PgConnection

from api.schemas.chat import (
    ActionPromptData,
    AgentMessageData,
    Message,
)
from chat.db import transaction
from chat.repositories.message_repository import MessagePage, MessageRepository
from chat.repositories.thread_repository import PostgresThreadRepository


def _iso_timestamp(value) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _row_to_message(row: tuple) -> Message:
    msg_id, sender, content, agent_data, prompt_data, created_at = row
    kwargs: dict[str, Any] = {
        "id": str(msg_id),
        "sender": sender,
        "timestamp": _iso_timestamp(created_at),
    }
    if content is not None:
        kwargs["content"] = content
    if agent_data is not None:
        data = agent_data if isinstance(agent_data, dict) else json.loads(agent_data)
        kwargs["agent_data"] = AgentMessageData.model_validate(data)
    if prompt_data is not None:
        data = prompt_data if isinstance(prompt_data, dict) else json.loads(prompt_data)
        kwargs["prompt_data"] = ActionPromptData.model_validate(data)
    return Message.model_validate(kwargs)


class PostgresMessageRepository(MessageRepository):
    def __init__(self, thread_repository: PostgresThreadRepository | None = None) -> None:
        self._thread_repository = thread_repository or PostgresThreadRepository()

    def channel_exists(self, channel_id: str) -> bool:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM chat.chat_channels
                    WHERE id = %s AND is_active = TRUE
                    """,
                    (channel_id,),
                )
                return cur.fetchone() is not None

    def list_by_channel(
        self,
        channel_id: str,
        page: int,
        page_size: int,
        user_id: str | None = None,
    ) -> MessagePage | None:
        if not self.channel_exists(channel_id):
            return None
        if not user_id:
            user_id = "dev-user"
        thread = self._thread_repository.get_or_create(channel_id, user_id)
        return self.list_by_thread(thread.id, page, page_size)

    def list_by_thread(
        self, thread_id: UUID, page: int, page_size: int
    ) -> MessagePage:
        if page_size < 1:
            page_size = 50
        if page < 1:
            page = 1
        offset = (page - 1) * page_size

        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM chat.chat_messages WHERE thread_id = %s
                    """,
                    (str(thread_id),),
                )
                total_items = int(cur.fetchone()[0])

                cur.execute(
                    """
                    SELECT id, sender, content, agent_data, prompt_data, created_at
                    FROM chat.chat_messages
                    WHERE thread_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (str(thread_id), page_size, offset),
                )
                rows = cur.fetchall()

        items = [_row_to_message(row) for row in rows]
        total_pages = (
            math.ceil(total_items / page_size) if total_items > 0 else 0
        )
        return MessagePage(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def append_message(self, channel_id: str, message: Message) -> Message | None:
        """Legacy in-memory-style append — not used on postgres POST path."""
        if not self.channel_exists(channel_id):
            return None
        return message

    def resolve_pending_action_prompts(self, channel_id: str) -> int:
        return 0

    def get_by_id(self, message_id: str, user_id: str) -> Message | None:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT m.id, m.sender, m.content, m.agent_data, m.prompt_data, m.created_at
                    FROM chat.chat_messages m
                    JOIN chat.chat_threads t ON t.id = m.thread_id
                    WHERE m.id = %s AND t.user_id = %s
                    """,
                    (message_id, user_id),
                )
                row = cur.fetchone()
        if not row:
            return None
        return _row_to_message(row)

    def resolve_pending_on_conn(self, conn: PgConnection, thread_id: UUID) -> int:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE chat.chat_messages
                SET status = 'resolved', updated_at = now()
                WHERE thread_id = %s
                  AND sender = 'action_prompt'
                  AND status = 'pending'
                """,
                (str(thread_id),),
            )
            count = cur.rowcount
            cur.execute(
                """
                UPDATE chat.chat_threads
                SET pending_prompt_message_id = NULL, updated_at = now()
                WHERE id = %s
                """,
                (str(thread_id),),
            )
        return count

    def insert_user_message_on_conn(
        self,
        conn: PgConnection,
        thread_id: UUID,
        run_id: UUID | None,
        content: str,
        *,
        message_id: UUID | None = None,
        client_request_id: str | None = None,
    ) -> UUID:
        msg_id = message_id or uuid4()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat.chat_messages (
                    id, thread_id, run_id, sender, content, status, client_request_id
                )
                VALUES (%s, %s, %s, 'user', %s, 'final', %s)
                """,
                (
                    str(msg_id),
                    str(thread_id),
                    str(run_id) if run_id else None,
                    content,
                    client_request_id,
                ),
            )
        return msg_id

    def insert_agent_stub_on_conn(
        self,
        conn: PgConnection,
        thread_id: UUID,
        run_id: UUID,
        message_id: UUID,
    ) -> UUID:
        stub = json.dumps({"paragraphs": [], "executionTrace": []})
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat.chat_messages (
                    id, thread_id, run_id, sender, agent_data, status
                )
                VALUES (%s, %s, %s, 'agent', %s::jsonb, 'streaming')
                """,
                (str(message_id), str(thread_id), str(run_id), stub),
            )
        return message_id

    def finalize_agent_message(
        self,
        message_id: UUID,
        agent_data: AgentMessageData,
    ) -> None:
        payload = agent_data.model_dump(by_alias=True, mode="json")
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat.chat_messages
                    SET agent_data = %s::jsonb,
                        status = 'final',
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (json.dumps(payload), str(message_id)),
                )

    def insert_prompt_on_conn(
        self,
        conn: PgConnection,
        thread_id: UUID,
        run_id: UUID,
        message_id: UUID,
        prompt_data: ActionPromptData,
    ) -> UUID:
        payload = prompt_data.model_dump(by_alias=True, mode="json")
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat.chat_messages (
                    id, thread_id, run_id, sender, prompt_data, status
                )
                VALUES (%s, %s, %s, 'action_prompt', %s::jsonb, 'pending')
                """,
                (str(message_id), str(thread_id), str(run_id), json.dumps(payload)),
            )
            cur.execute(
                """
                UPDATE chat.chat_threads
                SET pending_prompt_message_id = %s, updated_at = now()
                WHERE id = %s
                """,
                (str(message_id), str(thread_id)),
            )
        return message_id
