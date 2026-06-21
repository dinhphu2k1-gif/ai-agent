"""
Metadata Agent Sub-Graph — OOP wrapper.
"""

from langgraph.graph import StateGraph, START, END

from .state import MetadataState
from .nodes import (
    query_analyzer_node,
    opensearch_retriever_node,
    result_synthesizer_node,
)


class MetadataAgentGraph:
    """
    Metadata Agent Sub-Graph builder.
    Sub-graph gồm 3 nodes:
      1. query_analyzer        — LLM phân tích yêu cầu → sinh search strategy
      2. opensearch_retriever  — Hybrid search + Neo4j expand + schema fetch
      3. result_synthesizer    — LLM tổng hợp kết quả → schema có cấu trúc
    """

    def __init__(self):
        self._workflow = StateGraph(MetadataState)
        self._build()

    def _build(self):
        """Đăng ký nodes và edges."""
        wf = self._workflow

        wf.add_node("query_analyzer", query_analyzer_node)
        wf.add_node("opensearch_retriever", opensearch_retriever_node)
        wf.add_node("result_synthesizer", result_synthesizer_node)

        wf.add_edge(START, "query_analyzer")
        wf.add_edge("query_analyzer", "opensearch_retriever")
        wf.add_edge("opensearch_retriever", "result_synthesizer")
        wf.add_edge("result_synthesizer", END)

    def compile(self):
        """Compile sub-graph."""
        return self._workflow.compile()


# ── Backward-compatible module-level instance ──
metadata_subgraph = MetadataAgentGraph().compile()
