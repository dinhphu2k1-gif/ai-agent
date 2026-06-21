"""Map LangGraph supervisor execution to Chat SSE events."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Any

from api.schemas.chat import ExecutionTraceStep, PostMessageRequest
from chat.mappers.agent_message_mapper import (
    build_action_prompt_data,
    build_sql_preview_table_events,
    format_final_output_paragraphs,
)
from chat.logging_utils import log_chat_event
from chat.settings import get_chat_settings

# LLM streams from these nodes may be shown to users when CHAT_EMIT_CONTENT_DELTA=true.
_STREAM_DELTA_NODES = frozenset({"result_synthesizer", "sql_writer_worker_node"})
# Internal routing / strategy JSON — never stream to chat clients.
_INTERNAL_LLM_NODES = frozenset({"planner", "query_analyzer"})


def _langgraph_node_from_event(event: dict) -> str | None:
    metadata = event.get("metadata")
    if not isinstance(metadata, dict):
        return None
    node = metadata.get("langgraph_node")
    return node if isinstance(node, str) else None


def _looks_like_internal_json_chunk(text: str) -> bool:
    """Heuristic guard when event metadata lacks langgraph_node."""
    snippet = (text or "").strip()
    if not snippet:
        return False
    lowered = snippet.lower()
    if '"intent"' in lowered and (
        '"consult_agent"' in lowered or '"ask_user"' in lowered
    ):
        return True
    if '"semantic_query"' in lowered and '"target_tables"' in lowered:
        return True
    if snippet.startswith("{") and '"reasoning"' in lowered:
        return True
    return False


def _should_emit_llm_delta(event: dict, text: str) -> bool:
    node = _langgraph_node_from_event(event)
    if node in _INTERNAL_LLM_NODES:
        return False
    if node in _STREAM_DELTA_NODES:
        return not _looks_like_internal_json_chunk(text)
    if node is not None:
        return False
    return not _looks_like_internal_json_chunk(text)


NODE_STATUS_MAP: dict[str, tuple[str, str, str]] = {
    "planner": ("Supervisor", "Đang phân tích kế hoạch", "psychology"),
    "metadata_worker_node": (
        "Metadata",
        "Kích hoạt tra cứu metadata",
        "dataset",
    ),
    "query_analyzer": ("Query Analyzer", "Phân tích truy vấn", "search"),
    "opensearch_retriever": (
        "OpenSearch",
        "Truy vấn vector DB",
        "travel_explore",
    ),
    "result_synthesizer": (
        "Synthesizer",
        "Tổng hợp schema",
        "description",
    ),
    "sql_writer_worker_node": ("SQL Writer", "Sinh SQL", "code"),
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class _StreamState:
    agent_message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_steps: list[ExecutionTraceStep] = field(default_factory=list)
    seen_trace_keys: set[str] = field(default_factory=set)
    paragraphs: list[str] = field(default_factory=list)
    paragraph_index: int = 0
    emitted_user_delta: bool = False


class SupervisorStreamAdapter:
    """Stream supervisor graph events as SSE payloads (not formatted SSE strings)."""

    def __init__(self, graph_app: Any | None = None) -> None:
        self._graph_app = graph_app

    def _get_graph(self) -> Any:
        if self._graph_app is not None:
            return self._graph_app
        from universal_agent.supervisor.graph import app

        return app

    @staticmethod
    def langgraph_thread_id(user_id: str, channel_id: str) -> str:
        return f"{user_id}:{channel_id}"

    async def _build_graph_input(
        self, graph: Any, config: dict, body: PostMessageRequest
    ) -> dict | None:
        snapshot = await graph.aget_state(config)
        if snapshot.next and "clarification_node" in snapshot.next:
            await graph.aupdate_state(
                config,
                {
                    "investigation_log": [
                        f"Người dùng trả lời (HITL): {body.label or body.content or ''}"
                    ],
                },
            )
            return None

        content = (body.content or "").strip()
        return {
            "user_input": content,
            "investigation_log": [f"Nhận yêu cầu: {content}"],
        }

    async def stream(
        self,
        channel_id: str,
        user_id: str,
        body: PostMessageRequest,
    ) -> AsyncIterator[tuple[str, dict]]:
        graph = self._get_graph()
        thread_id = self.langgraph_thread_id(user_id, channel_id)
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
            }
        }
        state = _StreamState()
        timestamp = _utc_now_iso()
        log_chat_event(
            "adapter.stream_start",
            channel_id=channel_id,
            user_id=user_id,
            thread_id=thread_id,
        )

        yield (
            "message.start",
            {
                "messageId": state.agent_message_id,
                "sender": "agent",
                "timestamp": timestamp,
            },
        )

        current_input = await self._build_graph_input(graph, config, body)
        settings = get_chat_settings()
        emit_delta = settings.emit_content_delta

        try:
            async for event in graph.astream_events(
                current_input, config=config, version="v2"
            ):
                event_kind = event.get("event")
                if emit_delta and event_kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    text = ""
                    if chunk is not None:
                        content = getattr(chunk, "content", None)
                        if isinstance(content, str):
                            text = content
                        elif isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    text += part.get("text", "")
                                elif isinstance(part, str):
                                    text += part
                    if text and _should_emit_llm_delta(event, text):
                        state.emitted_user_delta = True
                        yield (
                            "content.delta",
                            {
                                "messageId": state.agent_message_id,
                                "text": text,
                                "paragraphIndex": state.paragraph_index,
                            },
                        )
                    continue

                if event_kind != "on_chain_start":
                    continue
                node_name = event.get("name", "")
                mapping = NODE_STATUS_MAP.get(node_name)
                if not mapping or node_name in state.seen_trace_keys:
                    continue
                state.seen_trace_keys.add(node_name)
                title, description, icon = mapping
                step = ExecutionTraceStep(
                    title=title, description=description, icon=icon
                )
                state.trace_steps.append(step)
                yield (
                    "trace.step",
                    {
                        "messageId": state.agent_message_id,
                        "step": step.model_dump(by_alias=True),
                    },
                )

            snapshot = await graph.aget_state(config)
            values = snapshot.values or {}

            if values.get("final_output") and not snapshot.next:
                state.paragraphs = format_final_output_paragraphs(
                    values.get("final_output", "")
                )
                # Skip duplicate full text when synthesizer/SQL already streamed deltas.
                if not state.emitted_user_delta:
                    for paragraph in state.paragraphs:
                        yield (
                            "content.paragraph",
                            {
                                "messageId": state.agent_message_id,
                                "text": paragraph,
                            },
                        )
                        state.paragraph_index += 1
                sql_preview = values.get("sql_result_preview") or ""
                if isinstance(sql_preview, str) and sql_preview.strip():
                    for event_name, payload in build_sql_preview_table_events(
                        state.agent_message_id, sql_preview
                    ):
                        yield (event_name, payload)
                await graph.aupdate_state(
                    config, {"final_output": "", "message_to_user": ""}
                )

            elif snapshot.next and "clarification_node" in snapshot.next:
                question = values.get(
                    "message_to_user",
                    "Tôi cần thêm một chút thông tin để có thể giúp bạn tốt hơn.",
                )
                prompt_id = str(uuid.uuid4())
                prompt_data = build_action_prompt_data(
                    str(question),
                    ui_options=values.get("planner_ui_options"),
                )
                yield (
                    "action.prompt",
                    {
                        "messageId": prompt_id,
                        "promptData": prompt_data.model_dump(by_alias=True),
                    },
                )

            yield ("message.end", {"messageId": state.agent_message_id})

        except Exception as exc:
            yield (
                "error",
                {
                    "code": "AGENT_ERROR",
                    "message": str(exc),
                    "messageId": state.agent_message_id,
                },
            )
            yield (
                "run.failed",
                {
                    "code": "AGENT_ERROR",
                    "message": str(exc),
                    "messageId": state.agent_message_id,
                },
            )
            raise
