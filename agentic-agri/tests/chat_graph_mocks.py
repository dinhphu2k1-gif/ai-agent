"""Shared mocks for supervisor graph in chat API tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock


def wire_async_graph_state(
    mock_graph: MagicMock,
    *,
    next_nodes: tuple[str, ...] = (),
    values: dict[str, Any] | None = None,
) -> MagicMock:
    """SupervisorStreamAdapter uses aget_state / aupdate_state (AsyncRedisSaver)."""
    snap = MagicMock(next=next_nodes, values=values or {})
    mock_graph.aget_state = AsyncMock(return_value=snap)
    mock_graph.aupdate_state = AsyncMock()
    return snap
