"""
Supervisor Graph — OOP wrapper quanh LangGraph StateGraph.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import UniversalState
from .nodes import (
    context_retriever_node,
    investigative_planner_node,
    clarification_node,
    metadata_worker_node,
)
from .nodes import sql_writer_worker_node

_compiled_app: Any | None = None
_checkpointer: Any | None = None
_checkpointer_ready = False


class SupervisorGraph:
    """
    Supervisor Graph builder — quản lý luồng điều phối ReAct.
    """

    def __init__(self):
        self._workflow = StateGraph(UniversalState)
        self._build()

    def _build(self):
        """Đăng ký nodes và edges."""
        wf = self._workflow

        # Add Nodes
        wf.add_node("context_retriever", context_retriever_node)
        wf.add_node("planner", investigative_planner_node)
        wf.add_node("clarification_node", clarification_node)
        wf.add_node("metadata_worker_node", metadata_worker_node)
        wf.add_node("sql_writer_worker_node", sql_writer_worker_node)

        # Luồng bắt đầu
        wf.add_edge(START, "context_retriever")
        wf.add_edge("context_retriever", "planner")

        # Định tuyến Conditional Edges từ Planner
        wf.add_conditional_edges(
            "planner",
            self.dynamic_router,
            {
                "metadata_worker_node": "metadata_worker_node",
                "sql_writer_worker_node": "sql_writer_worker_node",
                "clarification_node": "clarification_node",
                END: END,
            },
        )

        # Khép kín vòng lặp ReAct về lại Planner sau khi Worker làm xong việc
        wf.add_edge("metadata_worker_node", "planner")
        wf.add_edge("sql_writer_worker_node", "planner")
        wf.add_edge("clarification_node", "planner")

    @staticmethod
    def dynamic_router(state: UniversalState):
        """
        Định tuyến dựa trên Intent của Planner.
        """
        intent = state.get("intent")

        if intent == "consult_agent":
            target = state.get("target_agent")
            # Danh sách các Agent nội bộ hiện có
            valid_agents = ["metadata_worker", "sql_writer_worker"]

            if target in valid_agents:
                return f"{target}_node"
            else:
                # Fallback nếu LLM bị ảo giác gọi sai tên Agent
                return "metadata_worker_node"

        elif intent == "ask_user":
            return "clarification_node"

        elif intent == "finalize_plan":
            return END

        return END

    def compile(self, checkpointer=None, interrupt_before=None):
        """Compile graph với checkpointer."""
        return self._workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=interrupt_before or ["clarification_node"],
        )


def _redis_url() -> str:
    return os.environ.get("REDIS_URL", "").strip()


def _compile_supervisor(checkpointer: Any) -> Any:
    return SupervisorGraph().compile(checkpointer=checkpointer)


async def setup_supervisor_checkpointer() -> None:
    """
    Initialize checkpointer and compiled graph.

    AsyncRedisSaver requires await setup() before astream_events; sync RedisSaver
    does not implement aget_tuple (NotImplementedError).
    """
    global _compiled_app, _checkpointer, _checkpointer_ready

    if _checkpointer_ready and _compiled_app is not None:
        return

    redis_url = _redis_url()
    if redis_url:
        from langgraph.checkpoint.redis.aio import AsyncRedisSaver

        try:
            saver = AsyncRedisSaver(redis_url=redis_url)
            await saver.setup()
            _checkpointer = saver
            _compiled_app = _compile_supervisor(saver)
        except Exception as exc:
            logger.warning(
                "Redis checkpoint setup failed (%s). Use image redis/redis-stack-server "
                "in docker-compose, or unset REDIS_URL. Falling back to MemorySaver.",
                exc,
            )
            _checkpointer = MemorySaver()
            _compiled_app = _compile_supervisor(_checkpointer)
    else:
        _checkpointer = MemorySaver()
        _compiled_app = _compile_supervisor(_checkpointer)

    _checkpointer_ready = True


def get_supervisor_app() -> Any:
    """Return compiled supervisor graph; MemorySaver works without async setup."""
    global _compiled_app, _checkpointer, _checkpointer_ready

    if _compiled_app is not None:
        return _compiled_app

    if _redis_url():
        raise RuntimeError(
            "Supervisor graph with REDIS_URL requires setup_supervisor_checkpointer() "
            "before use (e.g. FastAPI lifespan)."
        )

    _checkpointer = MemorySaver()
    _compiled_app = _compile_supervisor(_checkpointer)
    _checkpointer_ready = True
    return _compiled_app


class _LazySupervisorApp:
    """Backward-compatible module-level `app` that delegates after setup."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_supervisor_app(), name)


# Telegram / tests import `app`; Chat API should call setup in lifespan first.
app = _LazySupervisorApp()
