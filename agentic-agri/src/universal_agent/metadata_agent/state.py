"""
State definition cho Metadata Agent Sub-Graph.
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class MetadataState(TypedDict, total=False):
    """State nội bộ của Metadata Sub-Graph."""

    user_input: str
    investigation_log_input: str
    user_id: str
    thread_id: Optional[str]
    search_strategy: Optional[dict]
    raw_results: str
    synthesized_schema: str
    list_tables: list[str]
    neo4j_join_context: Optional[str]
    expanded_tables: list[str]
    metadata_hits: list[dict]