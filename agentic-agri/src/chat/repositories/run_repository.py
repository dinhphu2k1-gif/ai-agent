"""Run lifecycle persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import psycopg2
from psycopg2.extensions import connection as PgConnection

from chat.db import transaction


@dataclass(frozen=True)
class RunRecord:
    id: UUID
    thread_id: UUID
    status: str
    user_message_id: UUID | None = None
    agent_message_id: UUID | None = None
    last_event_id: str | None = None


@dataclass(frozen=True)
class RunExecutionContext:
    run: RunRecord
    channel_id: str
    user_id: str
    request_payload: dict[str, Any]


class RunRepository(ABC):
    @abstractmethod
    def get_active(self, thread_id: UUID) -> RunRecord | None:
        """Return queued/running run for thread, if any."""

    @abstractmethod
    def get_by_id(self, run_id: UUID) -> RunRecord | None:
        """Load run by primary key."""

    @abstractmethod
    def find_by_idempotency(
        self, thread_id: UUID, idempotency_key: str
    ) -> RunRecord | None:
        """Return existing run for (thread, idempotency key) if any."""

    @abstractmethod
    def create_queued(
        self,
        thread_id: UUID,
        user_message_id: UUID,
        request_payload: dict[str, Any],
        *,
        trigger_type: str = "message",
        idempotency_key: str | None = None,
    ) -> RunRecord:
        """Insert run with status queued (must be inside transaction when composed)."""

    @abstractmethod
    def mark_running(self, run_id: UUID) -> None:
        """Transition queued → running."""

    @abstractmethod
    def complete(
        self,
        run_id: UUID,
        *,
        agent_message_id: UUID | None = None,
        last_event_id: str | None = None,
    ) -> None:
        """Mark run completed."""

    @abstractmethod
    def fail(
        self,
        run_id: UUID,
        *,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Mark run failed."""

    @abstractmethod
    def update_last_event_id(self, run_id: UUID, event_id: str) -> None:
        """Persist last SSE id for reconnect."""

    @abstractmethod
    def get_execution_context(self, run_id: UUID) -> RunExecutionContext | None:
        """Load run with thread channel/user and stored POST body."""


class PostgresRunRepository(RunRepository):
    def get_active(self, thread_id: UUID) -> RunRecord | None:
        with transaction() as conn:
            return self._get_active_on_conn(conn, thread_id)

    def get_active_on_conn(
        self, conn: PgConnection, thread_id: UUID
    ) -> RunRecord | None:
        return self._get_active_on_conn(conn, thread_id)

    def _get_active_on_conn(
        self, conn: PgConnection, thread_id: UUID
    ) -> RunRecord | None:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, thread_id, status, user_message_id, agent_message_id, last_event_id
                FROM chat.chat_runs
                WHERE thread_id = %s AND status IN ('queued', 'running')
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (str(thread_id),),
            )
            row = cur.fetchone()
        if not row:
            return None
        return _row_to_run(row)

    def get_by_id(self, run_id: UUID) -> RunRecord | None:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, thread_id, status, user_message_id, agent_message_id, last_event_id
                    FROM chat.chat_runs WHERE id = %s
                    """,
                    (str(run_id),),
                )
                row = cur.fetchone()
        if not row:
            return None
        return _row_to_run(row)

    def find_by_idempotency(
        self, thread_id: UUID, idempotency_key: str
    ) -> RunRecord | None:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, thread_id, status, user_message_id, agent_message_id, last_event_id
                    FROM chat.chat_runs
                    WHERE thread_id = %s AND idempotency_key = %s
                    ORDER BY started_at DESC
                    LIMIT 1
                    """,
                    (str(thread_id), idempotency_key),
                )
                row = cur.fetchone()
        if not row:
            return None
        return _row_to_run(row)

    def create_queued(
        self,
        thread_id: UUID,
        user_message_id: UUID,
        request_payload: dict[str, Any],
        *,
        trigger_type: str = "message",
        idempotency_key: str | None = None,
    ) -> RunRecord:
        import json

        with transaction() as conn:
            return self.create_queued_on_conn(
                conn,
                thread_id,
                user_message_id,
                request_payload,
                trigger_type=trigger_type,
                idempotency_key=idempotency_key,
            )

    def create_queued_on_conn(
        self,
        conn: PgConnection,
        thread_id: UUID,
        user_message_id: UUID,
        request_payload: dict[str, Any],
        *,
        trigger_type: str = "message",
        idempotency_key: str | None = None,
    ) -> RunRecord:
        import json

        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO chat.chat_runs (
                        thread_id, status, trigger_type, request_payload,
                        user_message_id, idempotency_key
                    )
                    VALUES (%s, 'queued', %s, %s::jsonb, %s, %s)
                    RETURNING id, thread_id, status, user_message_id, agent_message_id, last_event_id
                    """,
                    (
                        str(thread_id),
                        trigger_type,
                        json.dumps(request_payload),
                        str(user_message_id),
                        idempotency_key,
                    ),
                )
            except psycopg2.errors.UniqueViolation as exc:
                raise RunConflictError("Active run already exists for thread") from exc
            row = cur.fetchone()
        return _row_to_run(row)

    def mark_running(self, run_id: UUID) -> None:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat.chat_runs SET status = 'running' WHERE id = %s
                    """,
                    (str(run_id),),
                )

    def complete(
        self,
        run_id: UUID,
        *,
        agent_message_id: UUID | None = None,
        last_event_id: str | None = None,
    ) -> None:
        finished = datetime.now(timezone.utc)
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat.chat_runs
                    SET status = 'completed',
                        finished_at = %s,
                        agent_message_id = COALESCE(%s, agent_message_id),
                        last_event_id = COALESCE(%s, last_event_id)
                    WHERE id = %s
                    """,
                    (
                        finished,
                        str(agent_message_id) if agent_message_id else None,
                        last_event_id,
                        str(run_id),
                    ),
                )

    def fail(
        self,
        run_id: UUID,
        *,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        finished = datetime.now(timezone.utc)
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat.chat_runs
                    SET status = 'failed',
                        finished_at = %s,
                        error_code = %s,
                        error_message = %s
                    WHERE id = %s
                    """,
                    (finished, error_code, error_message, str(run_id)),
                )

    def update_last_event_id(self, run_id: UUID, event_id: str) -> None:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat.chat_runs SET last_event_id = %s WHERE id = %s
                    """,
                    (event_id, str(run_id)),
                )

    def set_agent_message_id(self, run_id: UUID, agent_message_id: UUID) -> None:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat.chat_runs SET agent_message_id = %s WHERE id = %s
                    """,
                    (str(agent_message_id), str(run_id)),
                )

    def get_execution_context(self, run_id: UUID) -> RunExecutionContext | None:
        import json

        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT r.id, r.thread_id, r.status, r.user_message_id,
                           r.agent_message_id, r.last_event_id,
                           t.channel_id, t.user_id, r.request_payload
                    FROM chat.chat_runs r
                    JOIN chat.chat_threads t ON t.id = r.thread_id
                    WHERE r.id = %s
                    """,
                    (str(run_id),),
                )
                row = cur.fetchone()
        if not row:
            return None
        payload = row[8]
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            payload = {}
        return RunExecutionContext(
            run=_row_to_run(row[:6]),
            channel_id=row[6],
            user_id=row[7],
            request_payload=payload,
        )


def _row_to_run(row: tuple) -> RunRecord:
    return RunRecord(
        id=row[0],
        thread_id=row[1],
        status=row[2],
        user_message_id=row[3],
        agent_message_id=row[4],
        last_event_id=row[5],
    )


class RunConflictError(Exception):
    """Raised when unique index blocks a second active run."""
