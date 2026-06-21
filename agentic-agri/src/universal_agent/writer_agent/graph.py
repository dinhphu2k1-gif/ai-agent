"""
Writer Agent Sub-Graph — OOP wrapper.
"""

from langgraph.graph import StateGraph, START, END

from .nodes import (
    should_continue_repair,
    sql_execution_node,
    sql_generation_node,
    sql_repair_node,
)
from .state import WriterState


class WriterAgentGraph:
    """
    Writer Agent Sub-Graph:
      sql_generation → sql_execution → [repair loop] → END
    """

    def __init__(self):
        self._workflow = StateGraph(WriterState)
        self._build()

    def _build(self):
        wf = self._workflow

        wf.add_node("sql_generation", sql_generation_node)
        wf.add_node("sql_execution", sql_execution_node)
        wf.add_node("sql_repair", sql_repair_node)

        wf.add_edge(START, "sql_generation")
        wf.add_edge("sql_generation", "sql_execution")
        wf.add_conditional_edges(
            "sql_execution",
            should_continue_repair,
            {
                "success": END,
                "repair": "sql_repair",
                "give_up": END,
            },
        )
        wf.add_edge("sql_repair", "sql_execution")

    def compile(self):
        return self._workflow.compile()


writer_subgraph = WriterAgentGraph().compile()
