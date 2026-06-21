"""Orchestrate POST message → SSE stream with supervisor graph."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from api.schemas.chat import (
    ActionPromptData,
    AgentMessageData,
    ExecutionTraceStep,
    Message,
    PostMessageRequest,
    StartRunResponse,
)
from api.streaming.sse import format_sse
from chat.adapters.supervisor_stream import SupervisorStreamAdapter
from chat.db import transaction
from chat.logging_utils import log_chat_event
from chat.repositories.channel_repository import ChannelRepository
from chat.repositories.message_repository import MessageRepository
from chat.repositories.postgres_message_repository import PostgresMessageRepository
from chat.repositories.run_event_repository import RunEventRepository
from chat.repositories.run_repository import (
    PostgresRunRepository,
    RunConflictError,
    RunExecutionContext,
    RunRepository,
)
from chat.repositories.thread_repository import PostgresThreadRepository, ThreadRepository
from chat.services.attachment_service import AttachmentService
from chat.services.channel_access_service import ChannelAccessService
from chat.services.post_message_validator import PostMessageValidator
from chat.settings import ChatSettings, get_chat_settings


class RunInProgressError(Exception):
    def __init__(self, channel_id: str, run_id: str) -> None:
        self.channel_id = channel_id
        self.run_id = run_id
        super().__init__(f"Run in progress for channel {channel_id}: {run_id}")


class RunNotFoundError(Exception):
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        super().__init__(f"Run not found: {run_id}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(str(value))
    except ValueError:
        return None


def _maybe_capture_sentry(exc: BaseException) -> None:
    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    except ImportError:
        pass


@dataclass
class _PreparedRun:
    channel_id: str
    user_id: str
    body: PostMessageRequest
    run_id: str
    user_message_id: str
    thread_id: UUID | None = None
    run_uuid: UUID | None = None


@dataclass
class _PersistCollector:
    agent_message_id: str | None = None
    agent_message_uuid: UUID | None = None
    trace_steps: list[ExecutionTraceStep] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    prompt_data: ActionPromptData | None = None
    prompt_message_id: str | None = None
    prompt_message_uuid: UUID | None = None


class RunService:
    def __init__(
        self,
        message_repository: MessageRepository,
        channel_repository: ChannelRepository,
        stream_adapter: SupervisorStreamAdapter,
        active_runs: dict[str, str] | None = None,
        *,
        thread_repository: ThreadRepository | None = None,
        run_repository: RunRepository | None = None,
        run_event_repository: RunEventRepository | None = None,
        chat_settings: ChatSettings | None = None,
        channel_access: ChannelAccessService | None = None,
        post_message_validator: PostMessageValidator | None = None,
        attachment_service: AttachmentService | None = None,
    ) -> None:
        self._message_repository = message_repository
        self._channel_repository = channel_repository
        self._stream_adapter = stream_adapter
        self._active_runs = active_runs if active_runs is not None else {}
        self._thread_repository = thread_repository
        self._run_repository = run_repository
        self._run_event_repository = run_event_repository
        self._settings = chat_settings or get_chat_settings()
        self._channel_access = channel_access
        self._validator = post_message_validator
        self._attachment_service = attachment_service
        self._memory_idempotency: dict[str, str] = {}
        self._pending_runs: dict[str, _PreparedRun] = {}
        self._postgres_messages: PostgresMessageRepository | None = (
            message_repository
            if isinstance(message_repository, PostgresMessageRepository)
            else None
        )

    @property
    def _persist_enabled(self) -> bool:
        return self._run_repository is not None and self._postgres_messages is not None

    def _langgraph_thread_id(self, user_id: str, channel_id: str) -> str:
        return SupervisorStreamAdapter.langgraph_thread_id(user_id, channel_id)

    def _user_display_text(self, body: PostMessageRequest) -> str:
        if body.type == "text":
            return (body.content or "").strip()
        return (body.label or "").strip()

    def check_can_start(
        self,
        channel_id: str,
        user_id: str,
        *,
        idempotency_key: str | None = None,
    ) -> None:
        """Validate ACL and no conflicting active run (call before StreamingResponse)."""
        if self._channel_access:
            self._channel_access.authorize_participant(channel_id, user_id)
        elif not self._channel_repository.exists(channel_id):
            from api.errors import ChannelNotFoundError

            raise ChannelNotFoundError(f"Channel not found: {channel_id}")

        if idempotency_key:
            self._check_idempotency_not_active(channel_id, user_id, idempotency_key)
            return

        if self._run_repository and self._thread_repository:
            thread = self._thread_repository.get_or_create(channel_id, user_id)
            active = self._run_repository.get_active(thread.id)
            if active:
                raise RunInProgressError(channel_id, str(active.id))
            return

        if channel_id in self._active_runs:
            raise RunInProgressError(channel_id, self._active_runs[channel_id])

    def _idempotency_memory_key(
        self, channel_id: str, user_id: str, idempotency_key: str
    ) -> str:
        return f"{channel_id}:{user_id}:{idempotency_key}"

    def _check_idempotency_not_active(
        self, channel_id: str, user_id: str, idempotency_key: str
    ) -> None:
        if self._run_repository and self._thread_repository:
            thread = self._thread_repository.get_or_create(channel_id, user_id)
            existing = self._run_repository.find_by_idempotency(
                thread.id, idempotency_key
            )
            if existing and existing.status in ("queued", "running"):
                raise RunInProgressError(channel_id, str(existing.id))
            return

        mem_key = self._idempotency_memory_key(channel_id, user_id, idempotency_key)
        prior_run_id = self._memory_idempotency.get(mem_key)
        if prior_run_id and channel_id in self._active_runs:
            if self._active_runs[channel_id] == prior_run_id:
                raise RunInProgressError(channel_id, prior_run_id)

    async def _replay_idempotent_stream(
        self,
        channel_id: str,
        user_id: str,
        idempotency_key: str,
    ) -> AsyncIterator[str]:
        """Yield replay frames for a completed idempotent run, or nothing."""
        if (
            self._run_repository
            and self._thread_repository
            and self._run_event_repository
        ):
            thread = self._thread_repository.get_or_create(channel_id, user_id)
            existing = self._run_repository.find_by_idempotency(
                thread.id, idempotency_key
            )
            if not existing or existing.status != "completed":
                return
            log_chat_event(
                "run.idempotent_replay",
                run_id=str(existing.id),
                channel_id=channel_id,
                user_id=user_id,
                thread_id=thread.langgraph_thread_id,
            )
            async for frame in self.replay_run_stream(str(existing.id), 0):
                yield frame
            return

        mem_key = self._idempotency_memory_key(channel_id, user_id, idempotency_key)
        prior_run_id = self._memory_idempotency.get(mem_key)
        if not prior_run_id or channel_id in self._active_runs:
            return
        log_chat_event(
            "run.idempotent_replay_memory",
            run_id=prior_run_id,
            channel_id=channel_id,
            user_id=user_id,
            thread_id=self._langgraph_thread_id(user_id, channel_id),
        )
        yield format_sse(
            "run.start",
            {"runId": prior_run_id, "channelId": channel_id},
            event_id=prior_run_id,
        )

    def _begin_run_transaction(
        self,
        channel_id: str,
        user_id: str,
        body: PostMessageRequest,
        *,
        idempotency_key: str | None = None,
    ) -> tuple[UUID, UUID, UUID, str]:
        """Resolve prompts, insert user message + queued run; return ids."""
        assert self._thread_repository is not None
        assert self._run_repository is not None
        assert self._postgres_messages is not None

        langgraph_thread_id = self._langgraph_thread_id(user_id, channel_id)
        thread_repo = self._thread_repository
        run_repo = self._run_repository
        if not isinstance(thread_repo, PostgresThreadRepository):
            raise RuntimeError("Postgres thread repository required")
        if not isinstance(run_repo, PostgresRunRepository):
            raise RuntimeError("Postgres run repository required")

        user_message_uuid = uuid4()
        request_payload = body.model_dump(by_alias=True, mode="json")

        with transaction() as conn:
            thread = thread_repo.get_or_create_on_conn(
                conn, channel_id, user_id, langgraph_thread_id
            )
            active = run_repo.get_active_on_conn(conn, thread.id)
            if active:
                raise RunInProgressError(channel_id, str(active.id))

            self._postgres_messages.resolve_pending_on_conn(conn, thread.id)

            self._postgres_messages.insert_user_message_on_conn(
                conn,
                thread.id,
                None,
                self._user_display_text(body),
                message_id=user_message_uuid,
            )

            try:
                run_record = run_repo.create_queued_on_conn(
                    conn,
                    thread.id,
                    user_message_uuid,
                    request_payload,
                    idempotency_key=idempotency_key,
                )
            except RunConflictError as exc:
                raise RunInProgressError(channel_id, "unknown") from exc

            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat.chat_messages SET run_id = %s WHERE id = %s
                    """,
                    (str(run_record.id), str(user_message_uuid)),
                )

        if self._attachment_service and body.attachment_ids:
            self._attachment_service.link_to_message(
                user_message_uuid,
                body.attachment_ids,
                channel_id,
                user_id,
            )

        return run_record.id, thread.id, user_message_uuid, str(run_record.id)

    async def prepare_run(
        self,
        channel_id: str,
        user_id: str,
        body: PostMessageRequest,
        *,
        idempotency_key: str | None = None,
    ) -> StartRunResponse:
        """Create queued run and user message; client opens GET /runs/{id}/stream."""
        if self._channel_access:
            self._channel_access.authorize_participant(channel_id, user_id)
        if self._validator:
            self._validator.validate(channel_id, user_id, body)
        self.check_can_start(
            channel_id, user_id, idempotency_key=idempotency_key
        )

        if self._persist_enabled:
            run_uuid, thread_id, user_message_uuid, run_id = (
                self._begin_run_transaction(
                    channel_id,
                    user_id,
                    body,
                    idempotency_key=idempotency_key,
                )
            )
            return StartRunResponse(
                run_id=run_id,
                user_message_id=str(user_message_uuid),
            )

        run_id = str(uuid4())
        user_message_id = str(uuid4())
        self._active_runs[channel_id] = run_id
        self._message_repository.resolve_pending_action_prompts(channel_id)
        user_text = self._user_display_text(body)
        user_message = Message(
            id=user_message_id,
            sender="user",
            timestamp=_utc_now_iso(),
            content=user_text,
        )
        self._message_repository.append_message(channel_id, user_message)
        if self._attachment_service and body.attachment_ids:
            self._attachment_service.link_to_message(
                UUID(user_message_id),
                body.attachment_ids,
                channel_id,
                user_id,
            )
        self._pending_runs[run_id] = _PreparedRun(
            channel_id=channel_id,
            user_id=user_id,
            body=body,
            run_id=run_id,
            user_message_id=user_message_id,
        )
        if idempotency_key:
            mem_key = self._idempotency_memory_key(
                channel_id, user_id, idempotency_key
            )
            self._memory_idempotency[mem_key] = run_id
        return StartRunResponse(
            run_id=run_id,
            user_message_id=user_message_id,
        )

    def _persist_stream_results_memory(
        self, channel_id: str, collector: _PersistCollector
    ) -> None:
        if collector.paragraphs and collector.agent_message_id:
            self._message_repository.append_message(
                channel_id,
                Message(
                    id=collector.agent_message_id,
                    sender="agent",
                    timestamp=_utc_now_iso(),
                    agent_data=AgentMessageData(
                        execution_trace=collector.trace_steps or None,
                        paragraphs=collector.paragraphs,
                    ),
                ),
            )

        if collector.prompt_data and collector.prompt_message_id:
            self._message_repository.append_message(
                channel_id,
                Message(
                    id=collector.prompt_message_id,
                    sender="action_prompt",
                    timestamp=_utc_now_iso(),
                    prompt_data=collector.prompt_data,
                ),
            )

    def _finalize_postgres_run(
        self,
        run_id: UUID,
        collector: _PersistCollector,
        channel_id: str,
        thread_id: UUID,
    ) -> None:
        assert self._postgres_messages is not None
        assert self._run_repository is not None

        if collector.agent_message_uuid and collector.paragraphs:
            agent_data = AgentMessageData(
                execution_trace=collector.trace_steps or None,
                paragraphs=collector.paragraphs,
            )
            self._postgres_messages.finalize_agent_message(
                collector.agent_message_uuid, agent_data
            )

        if (
            collector.prompt_data
            and collector.prompt_message_uuid
            and self._postgres_messages
        ):
            with transaction() as conn:
                self._postgres_messages.insert_prompt_on_conn(
                    conn,
                    thread_id,
                    run_id,
                    collector.prompt_message_uuid,
                    collector.prompt_data,
                )

        last_event = collector.agent_message_id or str(run_id)
        self._run_repository.complete(
            run_id,
            agent_message_id=collector.agent_message_uuid,
            last_event_id=last_event,
        )

    def _maybe_persist_sse(
        self,
        run_id: UUID,
        event_name: str,
        payload: dict[str, Any],
        event_id: str | None,
    ) -> str | None:
        if not self._settings.persist_sse_events or not self._run_event_repository:
            return event_id
        record = self._run_event_repository.append(run_id, event_name, payload)
        if self._run_repository:
            self._run_repository.update_last_event_id(run_id, str(record.id))
        return str(record.id)

    async def _stream_adapter_events(
        self,
        channel_id: str,
        user_id: str,
        body: PostMessageRequest,
        collector: _PersistCollector,
        *,
        run_uuid: UUID | None,
        thread_id: UUID | None,
        run_id: str,
        _persist_event,
    ) -> AsyncIterator[str]:
        timeout = self._settings.run_timeout_sec
        adapter_iter = self._stream_adapter.stream(
            channel_id, user_id, body
        ).__aiter__()

        while True:
            try:
                event_name, payload = await asyncio.wait_for(
                    adapter_iter.__anext__(), timeout=timeout
                )
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                log_chat_event(
                    "run.timeout",
                    run_id=run_id,
                    channel_id=channel_id,
                    user_id=user_id,
                    thread_id=self._langgraph_thread_id(user_id, channel_id),
                )
                err_payload = {
                    "code": "AGENT_TIMEOUT",
                    "message": f"Run exceeded {timeout}s",
                    "messageId": collector.agent_message_id,
                }
                out_id = _persist_event("error", err_payload, run_id)
                yield format_sse("error", err_payload, event_id=out_id)
                fail_payload = {
                    "code": "AGENT_TIMEOUT",
                    "message": f"Run exceeded {timeout}s",
                }
                out_fail = _persist_event("run.failed", fail_payload, run_id)
                yield format_sse("run.failed", fail_payload, event_id=out_fail)
                if self._persist_enabled and self._run_repository and run_uuid:
                    self._run_repository.fail(
                        run_uuid, error_code="AGENT_TIMEOUT"
                    )
                return

            if event_name == "message.start":
                collector.agent_message_id = payload.get("messageId")
                collector.agent_message_uuid = _parse_uuid(
                    collector.agent_message_id
                ) or uuid4()
                if (
                    self._persist_enabled
                    and thread_id is not None
                    and self._postgres_messages
                ):
                    with transaction() as conn:
                        self._postgres_messages.insert_agent_stub_on_conn(
                            conn,
                            thread_id,
                            run_uuid,
                            collector.agent_message_uuid,
                        )
                    if isinstance(self._run_repository, PostgresRunRepository):
                        self._run_repository.set_agent_message_id(
                            run_uuid, collector.agent_message_uuid
                        )
            elif event_name == "trace.step":
                step_data = payload.get("step", {})
                collector.trace_steps.append(
                    ExecutionTraceStep.model_validate(step_data)
                )
            elif event_name == "content.paragraph":
                text = payload.get("text", "")
                if text:
                    collector.paragraphs.append(text)
            elif event_name == "action.prompt":
                collector.prompt_message_id = payload.get("messageId")
                collector.prompt_message_uuid = (
                    _parse_uuid(collector.prompt_message_id) or uuid4()
                )
                prompt_raw = payload.get("promptData", {})
                collector.prompt_data = ActionPromptData.model_validate(
                    prompt_raw
                )

            out_id = _persist_event(
                event_name,
                payload,
                payload.get("messageId") or collector.agent_message_id,
            )
            yield format_sse(
                event_name,
                payload,
                event_id=out_id,
            )

    async def stream_message(
        self,
        channel_id: str,
        user_id: str,
        body: PostMessageRequest,
        *,
        idempotency_key: str | None = None,
    ) -> AsyncIterator[str]:
        thread_id_str = self._langgraph_thread_id(user_id, channel_id)

        if self._channel_access:
            self._channel_access.authorize_participant(channel_id, user_id)
        if self._validator:
            self._validator.validate(channel_id, user_id, body)

        if idempotency_key:
            replayed = False
            async for frame in self._replay_idempotent_stream(
                channel_id, user_id, idempotency_key
            ):
                replayed = True
                yield frame
            if replayed:
                return

        self.check_can_start(
            channel_id, user_id, idempotency_key=idempotency_key
        )

        thread_id: UUID | None = None
        run_uuid: UUID | None = None
        if self._persist_enabled:
            run_uuid, thread_id, user_message_uuid, run_id = self._begin_run_transaction(
                channel_id,
                user_id,
                body,
                idempotency_key=idempotency_key,
            )
            user_message_id = str(user_message_uuid)
            if isinstance(self._run_repository, PostgresRunRepository):
                self._run_repository.mark_running(run_uuid)
        else:
            run_id = str(uuid4())
            self._active_runs[channel_id] = run_id
            user_message_id = str(uuid4())

        log_chat_event(
            "run.stream_start",
            run_id=run_id,
            channel_id=channel_id,
            user_id=user_id,
            thread_id=thread_id_str,
        )

        collector = _PersistCollector()

        def _persist_event(
            event_name: str, payload: dict[str, Any], default_id: str | None
        ) -> str | None:
            if not self._persist_enabled or run_uuid is None:
                return default_id
            return self._maybe_persist_sse(run_uuid, event_name, payload, default_id)

        try:
            if not self._persist_enabled:
                self._message_repository.resolve_pending_action_prompts(channel_id)
                user_text = self._user_display_text(body)
                user_message = Message(
                    id=user_message_id,
                    sender="user",
                    timestamp=_utc_now_iso(),
                    content=user_text,
                )
                self._message_repository.append_message(channel_id, user_message)
                if self._attachment_service and body.attachment_ids:
                    self._attachment_service.link_to_message(
                        UUID(user_message_id),
                        body.attachment_ids,
                        channel_id,
                        user_id,
                    )

            sse_run_id = _persist_event(
                "run.start",
                {"runId": run_id, "channelId": channel_id},
                run_id,
            ) or run_id
            yield format_sse(
                "run.start",
                {"runId": run_id, "channelId": channel_id},
                event_id=sse_run_id,
            )

            ack_id = _persist_event(
                "user.ack",
                {
                    "messageId": user_message_id,
                    "sender": "user",
                    "timestamp": _utc_now_iso(),
                },
                user_message_id,
            ) or user_message_id
            yield format_sse(
                "user.ack",
                {
                    "messageId": user_message_id,
                    "sender": "user",
                    "timestamp": _utc_now_iso(),
                },
                event_id=ack_id,
            )

            async for frame in self._stream_adapter_events(
                channel_id,
                user_id,
                body,
                collector,
                run_uuid=run_uuid,
                thread_id=thread_id,
                run_id=run_id,
                _persist_event=_persist_event,
            ):
                yield frame

            if self._persist_enabled and thread_id is not None and run_uuid:
                self._finalize_postgres_run(
                    run_uuid, collector, channel_id, thread_id
                )
            else:
                self._persist_stream_results_memory(channel_id, collector)

            if idempotency_key and not self._persist_enabled:
                mem_key = self._idempotency_memory_key(
                    channel_id, user_id, idempotency_key
                )
                self._memory_idempotency[mem_key] = run_id

            log_chat_event(
                "run.stream_complete",
                run_id=run_id,
                channel_id=channel_id,
                user_id=user_id,
                thread_id=thread_id_str,
            )

        except Exception as exc:
            _maybe_capture_sentry(exc)
            log_chat_event(
                "run.stream_error",
                run_id=run_id,
                channel_id=channel_id,
                user_id=user_id,
                thread_id=thread_id_str,
                extra={"error": str(exc)},
            )
            if self._persist_enabled and self._run_repository and run_uuid is not None:
                self._run_repository.fail(run_uuid, error_code="STREAM_ERROR")
            raise
        finally:
            if not self._persist_enabled:
                self._active_runs.pop(channel_id, None)
                self._pending_runs.pop(run_id, None)

    async def _stream_prepared_run(self, pending: _PreparedRun) -> AsyncIterator[str]:
        """Execute SSE for async POST (memory mode)."""
        channel_id = pending.channel_id
        user_id = pending.user_id
        body = pending.body
        run_id = pending.run_id
        user_message_id = pending.user_message_id
        thread_id_str = self._langgraph_thread_id(user_id, channel_id)
        collector = _PersistCollector()

        log_chat_event(
            "run.stream_start",
            run_id=run_id,
            channel_id=channel_id,
            user_id=user_id,
            thread_id=thread_id_str,
        )

        def _persist_event(
            event_name: str, payload: dict[str, Any], default_id: str | None
        ) -> str | None:
            return default_id

        try:
            yield format_sse(
                "run.start",
                {"runId": run_id, "channelId": channel_id},
                event_id=run_id,
            )
            yield format_sse(
                "user.ack",
                {
                    "messageId": user_message_id,
                    "sender": "user",
                    "timestamp": _utc_now_iso(),
                },
                event_id=user_message_id,
            )
            async for frame in self._stream_adapter_events(
                channel_id,
                user_id,
                body,
                collector,
                run_uuid=None,
                thread_id=None,
                run_id=run_id,
                _persist_event=_persist_event,
            ):
                yield frame
            self._persist_stream_results_memory(channel_id, collector)
            log_chat_event(
                "run.stream_complete",
                run_id=run_id,
                channel_id=channel_id,
                user_id=user_id,
                thread_id=thread_id_str,
            )
        except Exception as exc:
            _maybe_capture_sentry(exc)
            raise
        finally:
            self._active_runs.pop(channel_id, None)
            self._pending_runs.pop(run_id, None)

    async def _execute_persisted_run(
        self,
        ctx: RunExecutionContext,
        *,
        last_event_id: int,
    ) -> AsyncIterator[str]:
        """Stream agent work for a queued/running postgres run (2-step POST pattern)."""
        run_uuid = ctx.run.id
        run_id = str(run_uuid)
        channel_id = ctx.channel_id
        user_id = ctx.user_id
        body = PostMessageRequest.model_validate(ctx.request_payload)
        thread_id = ctx.run.thread_id
        user_message_id = (
            str(ctx.run.user_message_id) if ctx.run.user_message_id else str(uuid4())
        )
        thread_id_str = self._langgraph_thread_id(user_id, channel_id)

        if self._run_event_repository and last_event_id > 0:
            events = self._run_event_repository.list_after(run_uuid, last_event_id)
            for record in events:
                yield format_sse(
                    record.event_name,
                    record.payload,
                    event_id=str(record.id),
                )
            if ctx.run.status == "completed":
                return

        if ctx.run.status not in ("queued", "running"):
            return

        if ctx.run.status == "queued" and self._run_repository:
            self._run_repository.mark_running(run_uuid)

        collector = _PersistCollector()

        def _persist_event(
            event_name: str, payload: dict[str, Any], default_id: str | None
        ) -> str | None:
            return self._maybe_persist_sse(run_uuid, event_name, payload, default_id)

        log_chat_event(
            "run.stream_start",
            run_id=run_id,
            channel_id=channel_id,
            user_id=user_id,
            thread_id=thread_id_str,
        )

        try:
            sse_run_id = _persist_event(
                "run.start",
                {"runId": run_id, "channelId": channel_id},
                run_id,
            ) or run_id
            yield format_sse(
                "run.start",
                {"runId": run_id, "channelId": channel_id},
                event_id=sse_run_id,
            )
            ack_id = _persist_event(
                "user.ack",
                {
                    "messageId": user_message_id,
                    "sender": "user",
                    "timestamp": _utc_now_iso(),
                },
                user_message_id,
            ) or user_message_id
            yield format_sse(
                "user.ack",
                {
                    "messageId": user_message_id,
                    "sender": "user",
                    "timestamp": _utc_now_iso(),
                },
                event_id=ack_id,
            )

            async for frame in self._stream_adapter_events(
                channel_id,
                user_id,
                body,
                collector,
                run_uuid=run_uuid,
                thread_id=thread_id,
                run_id=run_id,
                _persist_event=_persist_event,
            ):
                yield frame

            if thread_id is not None:
                self._finalize_postgres_run(
                    run_uuid, collector, channel_id, thread_id
                )

            log_chat_event(
                "run.stream_complete",
                run_id=run_id,
                channel_id=channel_id,
                user_id=user_id,
                thread_id=thread_id_str,
            )
        except Exception as exc:
            _maybe_capture_sentry(exc)
            if self._run_repository:
                self._run_repository.fail(run_uuid, error_code="STREAM_ERROR")
            raise

    async def stream_run_by_id(
        self,
        run_id: str,
        user_id: str,
        last_event_id: int = 0,
    ) -> AsyncIterator[str]:
        """Replay persisted events and/or execute queued run (spec §4.4)."""
        pending = self._pending_runs.get(run_id)
        if pending:
            if pending.user_id != user_id:
                raise RunNotFoundError(run_id)
            if last_event_id > 0:
                return
            async for frame in self._stream_prepared_run(pending):
                yield frame
            return

        if not self._run_repository:
            raise RunNotFoundError(run_id)

        run_uuid = _parse_uuid(run_id)
        if not run_uuid:
            raise RunNotFoundError(run_id)

        ctx = self._run_repository.get_execution_context(run_uuid)
        if not ctx or ctx.user_id != user_id:
            raise RunNotFoundError(run_id)

        if ctx.run.status not in ("queued", "running", "completed", "failed"):
            raise RunNotFoundError(run_id)

        if self._run_event_repository:
            events = self._run_event_repository.list_after(run_uuid, last_event_id)
            for record in events:
                yield format_sse(
                    record.event_name,
                    record.payload,
                    event_id=str(record.id),
                )
            if events and ctx.run.status in ("completed", "failed"):
                return

        if ctx.run.status in ("queued", "running"):
            async for frame in self._execute_persisted_run(
                ctx, last_event_id=last_event_id
            ):
                yield frame
            return

        if not self._run_event_repository:
            raise RunNotFoundError(run_id)

    async def replay_run_stream(
        self,
        run_id: str,
        last_event_id: int,
        *,
        user_id: str = "dev-user",
    ) -> AsyncIterator[str]:
        """Replay persisted SSE events after disconnect (P1b)."""
        async for frame in self.stream_run_by_id(run_id, user_id, last_event_id):
            yield frame
