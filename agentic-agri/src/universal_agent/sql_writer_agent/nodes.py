"""
Backward-compatible re-exports — SQL Writer implementation lives in writer_agent + supervisor.
"""

from universal_agent.supervisor.nodes import sql_writer_worker_node
from universal_agent.writer_agent.nodes import (
    _format_result_preview,
    finalize_output as _finalize_output,
)

__all__ = [
    "sql_writer_worker_node",
    "_format_result_preview",
    "_finalize_output",
]
