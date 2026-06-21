"""Phase 2 unit tests — SSE formatter and agent message mapper (no LLM)."""

import json

from api.streaming.sse import format_sse
from chat.adapters.supervisor_stream import (
    _looks_like_internal_json_chunk,
    _should_emit_llm_delta,
)
from chat.mappers.agent_message_mapper import (
    build_action_prompt_data,
    format_final_output_paragraphs,
)


def test_format_sse_ends_with_double_newline():
    frame = format_sse("run.start", {"runId": "run-1"})
    assert frame.endswith("\n\n")
    assert "event: run.start\n" in frame
    assert frame.count("\n\n") >= 1

    data_line = [line for line in frame.split("\n") if line.startswith("data: ")][0]
    payload = json.loads(data_line.removeprefix("data: "))
    assert payload["runId"] == "run-1"


def test_format_sse_includes_event_id():
    frame = format_sse("user.ack", {"messageId": "m1"}, event_id="evt-1")
    assert "id: evt-1\n" in frame


def test_format_final_output_sql_fenced():
    paragraphs = format_final_output_paragraphs(
        "SELECT id, name FROM gl_accounts LIMIT 10"
    )
    assert len(paragraphs) == 1
    assert paragraphs[0].startswith("```sql")
    assert "gl_accounts" in paragraphs[0]


def test_format_final_output_plain_text():
    paragraphs = format_final_output_paragraphs("Hello from agent.")
    assert paragraphs == ["Hello from agent."]


def test_format_final_output_splits_metadata_sections():
    text = "BÁO CÁO METADATA\n\n1. BẢNG\n\nCIF_CUSTOMERS — mô tả.\n\n2. CỘT\n\nid: khóa chính."
    paragraphs = format_final_output_paragraphs(text)
    assert len(paragraphs) >= 3
    assert paragraphs[0].startswith("BÁO CÁO")


def test_internal_json_chunk_detection():
    planner = '{"intent": "consult_agent", "reasoning": "test"}'
    assert _looks_like_internal_json_chunk(planner) is True
    assert _looks_like_internal_json_chunk('{"semantic_query": "x", "target_tables": []}') is True
    assert _looks_like_internal_json_chunk("BÁO CÁO METADATA cho CIF_CUSTOMERS") is False


def test_should_emit_llm_delta_blocks_planner():
    event = {
        "metadata": {"langgraph_node": "planner"},
        "data": {"chunk": None},
    }
    assert _should_emit_llm_delta(event, '{"intent": "consult_agent"}') is False


def test_should_emit_llm_delta_allows_synthesizer():
    event = {"metadata": {"langgraph_node": "result_synthesizer"}}
    assert _should_emit_llm_delta(event, "BÁO CÁO METADATA") is True


def test_build_action_prompt_data_default_three_options():
    prompt = build_action_prompt_data("Which region should we audit?")
    assert prompt.title == "Awaiting your direction"
    assert prompt.description == "Which region should we audit?"
    assert len(prompt.options) == 3
    assert prompt.options[0].action_id == "option_a"
    assert prompt.custom_option_label == "Option D: Custom Input"
