"""Thread ↔ LangGraph thread_id mapping."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from psycopg2.extensions import connection as PgConnection

from chat.db import transaction


@dataclass(frozen=True)
class ThreadRecord:
    id: UUID
    channel_id: str
    user_id: str
    langgraph_thread_id: str


class ThreadRepository(ABC):
    @abstractmethod
    def get_or_create(self, channel_id: str, user_id: str) -> ThreadRecord:
        """Return thread for (channel, user), creating if missing."""


class PostgresThreadRepository(ThreadRepository):
    def get_or_create(self, channel_id: str, user_id: str) -> ThreadRecord:
        langgraph_thread_id = f"{user_id}:{channel_id}"
        with transaction() as conn:
            return self._get_or_create_on_conn(conn, channel_id, user_id, langgraph_thread_id)

    def get_or_create_on_conn(
        self,
        conn: PgConnection,
        channel_id: str,
        user_id: str,
        langgraph_thread_id: str,
    ) -> ThreadRecord:
        return self._get_or_create_on_conn(
            conn, channel_id, user_id, langgraph_thread_id
        )

    def _get_or_create_on_conn(
        self,
        conn: PgConnection,
        channel_id: str,
        user_id: str,
        langgraph_thread_id: str,
    ) -> ThreadRecord:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, channel_id, user_id, langgraph_thread_id
                FROM chat.chat_threads
                WHERE channel_id = %s AND user_id = %s
                """,
                (channel_id, user_id),
            )
            row = cur.fetchone()
            if row:
                return ThreadRecord(
                    id=row[0],
                    channel_id=row[1],
                    user_id=row[2],
                    langgraph_thread_id=row[3],
                )

            cur.execute(
                """
                INSERT INTO chat.chat_threads (channel_id, user_id, langgraph_thread_id)
                VALUES (%s, %s, %s)
                RETURNING id, channel_id, user_id, langgraph_thread_id
                """,
                (channel_id, user_id, langgraph_thread_id),
            )
            inserted = cur.fetchone()
        return ThreadRecord(
            id=inserted[0],
            channel_id=inserted[1],
            user_id=inserted[2],
            langgraph_thread_id=inserted[3],
        )
