"""SSE event log for reconnect (P1b)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import json

from psycopg2.extensions import connection as PgConnection

from chat.db import transaction


@dataclass(frozen=True)
class RunEventRecord:
    id: int
    run_id: UUID
    event_name: str
    payload: dict[str, Any]


class RunEventRepository(ABC):
    @abstractmethod
    def append(
        self, run_id: UUID, event_name: str, payload: dict[str, Any]
    ) -> RunEventRecord:
        """Persist one SSE event."""

    @abstractmethod
    def list_after(self, run_id: UUID, last_event_id: int) -> list[RunEventRecord]:
        """Return events with id > last_event_id, ascending."""

    @abstractmethod
    def delete_older_than_days(self, days: int) -> int:
        """Delete events older than retention window; return rows removed."""


class PostgresRunEventRepository(RunEventRepository):
    def append(
        self, run_id: UUID, event_name: str, payload: dict[str, Any]
    ) -> RunEventRecord:
        with transaction() as conn:
            return self.append_on_conn(conn, run_id, event_name, payload)

    def append_on_conn(
        self,
        conn: PgConnection,
        run_id: UUID,
        event_name: str,
        payload: dict[str, Any],
    ) -> RunEventRecord:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat.chat_run_events (run_id, event_name, payload)
                VALUES (%s, %s, %s::jsonb)
                RETURNING id, run_id, event_name, payload
                """,
                (str(run_id), event_name, json.dumps(payload)),
            )
            row = cur.fetchone()
        return RunEventRecord(
            id=row[0],
            run_id=row[1],
            event_name=row[2],
            payload=row[3] if isinstance(row[3], dict) else json.loads(row[3]),
        )

    def list_after(self, run_id: UUID, last_event_id: int) -> list[RunEventRecord]:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, run_id, event_name, payload
                    FROM chat.chat_run_events
                    WHERE run_id = %s AND id > %s
                    ORDER BY id ASC
                    """,
                    (str(run_id), last_event_id),
                )
                rows = cur.fetchall()
        return [
            RunEventRecord(
                id=row[0],
                run_id=row[1],
                event_name=row[2],
                payload=row[3] if isinstance(row[3], dict) else json.loads(row[3]),
            )
            for row in rows
        ]

    def delete_older_than_days(self, days: int) -> int:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM chat.chat_run_events
                    WHERE created_at < now() - (%s || ' days')::interval
                    """,
                    (str(max(1, days)),),
                )
                return cur.rowcount
