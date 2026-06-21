"""
Nodes cho Supervisor Graph.
Bao gồm: context_retriever, planner, clarification, metadata_worker (wrapper).
"""

from .state import UniversalState, PlannerDecision
from .prompts import PLANNER_SYSTEM_PROMPT
from ..models import llm
from ..utils import get_text_content, strip_markdown_json

from langchain_core.runnables import RunnableConfig
from langchain_core.output_parsers import PydanticOutputParser

# Khởi tạo Parser ép kiểu JSON cho Planner (Không dùng json_mode wrapper vì lỗi vLLM EOS)
parser = PydanticOutputParser(pydantic_object=PlannerDecision)


def context_retriever_node(state: UniversalState) -> dict:
    """Mock lấy dữ liệu Long-term Memory từ PostgreSQL."""
    # Trong thực tế: query DB lấy thông tin user.
    mock_pg_context = "Hệ thống: Core Banking Data Warehouse. Dialect: PostgreSQL. Chứa các bảng quản lý thông tin khách hàng (Customer Information File - CIF), Thẻ ngân hàng, và Giao dịch. Bắt buộc tra cứu Metadata nếu truy xuất thông tin người dùng."
    return {"long_term_context": mock_pg_context}


def investigative_planner_node(state: UniversalState) -> dict:
    """Node Supervisor cốt lõi: Đưa ra quyết định định tuyến động."""
    user_input = state.get("user_input", "")
    context = state.get("long_term_context", "")
    log = "\n".join(state.get("investigation_log", []))

    meta_data = state.get("metadata_context") or "Không có metadata nào được tra cứu."

    prompt = f"""
    {PLANNER_SYSTEM_PROMPT}
    
    --- DỮ LIỆU HIỆN TẠI ---
    USER INPUT: {user_input}
    LONG TERM CONTEXT: {context}
    INVESTIGATION LOG: {log}

    --- CHỈ THỊ BẮT BUỘC (CRITICAL INSTRUCTION) ---
    Bạn là hệ thống Supervisor định tuyến. BẠN BẮT BUỘC PHẢI TRẢ VỀ DUY NHẤT 1 ĐỐI TƯỢNG JSON THEO CẤU TRÚC SAU.
    TUYỆT ĐỐI KHÔNG giải thích hay in thêm text nằm ngoài JSON này.
    {{
        "intent": "consult_agent" | "ask_user" | "finalize_plan",
        "reasoning": "Lý luận chi tiết tại sao chọn intent này",
        "target_agent": "metadata_worker" | "sql_writer_worker" | null,
        "message_to_user": "Câu hỏi gửi cho người dùng (nếu có)" | null
    }}
    """

    # 1. Yêu cầu LLM sinh chuỗi text và tự bóc tách JSON để an toàn nhất
    response = llm.invoke(prompt)
    raw_content = strip_markdown_json(get_text_content(response))

    print("response:.............: ", response)
          
    try:
        decision: PlannerDecision = parser.parse(raw_content)
    except Exception as e:
        print(f"⚠️ [JSON PARSE ERROR] Phân tích JSON thất bại: {e}")
        # Chuyển hướng xin trợ giúp user làm fallback
        decision = PlannerDecision(
            intent="ask_user",
            reasoning="Fallback do lỗi parse json",
            target_agent=None,
            message_to_user="Hệ thống đang quá tải, không sinh được chuẩn JSON. Vui lòng thử lại bằng cách nhắn một nội dung khác.",
        )

    # 2.5 Đảm bảo luôn có câu hỏi nếu Intent là ask_user
    if decision.intent == "ask_user" and not decision.message_to_user:
        decision.message_to_user = (
            "Hệ thống cần thêm thông tin. Xin vui lòng cung cấp thêm chi tiết."
        )

    ui_options_payload = None
    if decision.ui_options:
        ui_options_payload = [
            option.model_dump(by_alias=True) for option in decision.ui_options
        ]

    state_update = {
        "intent": decision.intent,
        "investigation_log": [f"Supervisor ({decision.intent}): {decision.reasoning}"],
        "target_agent": decision.target_agent,
        "message_to_user": decision.message_to_user,
        "planner_ui_options": ui_options_payload,
    }

    if decision.intent == "ask_user":
        state_update["investigation_log"].append(
            f"Chờ phản hồi (HITL): {decision.message_to_user}"
        )

    return state_update


def clarification_node(state: UniversalState) -> dict:
    """Điểm chờ Human-in-the-loop.
    Hàm này thực chất bị bỏ qua vì có interrupt_before.
    Khi update_state(as_node="clarification_node"), nội dung đó sẽ đi ra từ node này.
    """

    return {
        # Xóa câu hỏi cũ để khỏi vướng bận
        "message_to_user": None,
        # Đưa intent về None để bắt Planner phải suy luận lại từ đầu
        "intent": "None",
    }


def metadata_worker_node(state: UniversalState, config: RunnableConfig) -> dict:
    """Worker tra cứu Data Dictionary (Sub-Graph)."""
    from ..metadata_agent.graph import metadata_subgraph
    from ..metadata_agent.metadata_retrieval_client import resolve_metadata_user_context

    user_input = state.get("user_input", "")
    log = "\n".join(state.get("investigation_log", []))
    user_id, thread_id = resolve_metadata_user_context(state, config)

    print(f"\n{'─' * 50}")
    print(f"🔍 [Metadata Worker] Bắt đầu tra cứu Data Dictionary (userId={user_id})...")
    print(f"{'─' * 50}")

    try:
        result = metadata_subgraph.invoke(
            {
                "user_input": user_input,
                "investigation_log_input": log,
                "user_id": user_id,
                "thread_id": thread_id,
            },
            config=config,
        )

        synthesized = result.get("synthesized_schema", "Không tìm thấy metadata")
        from ..writer_agent.query_scope import build_query_scope

        table_names = result.get("expanded_tables") or result.get("list_tables") or []
        raw_results = result.get("raw_results") or ""
        metadata_hits = result.get("metadata_hits") or []
        query_scope = build_query_scope(
            table_names,
            raw_results=raw_results,
            raw_hits=metadata_hits,
        )
        if not query_scope.get("tables"):
            print(
                "⚠️ [Metadata Worker] query_scope.tables rỗng — "
                f"expanded_tables={result.get('expanded_tables')!r}, "
                f"list_tables={result.get('list_tables')!r}, "
                f"raw_len={len(raw_results)}"
            )
    except Exception as e:
        print(f"⚠️ [Metadata Worker] Lỗi khi chạy sub-graph: {e}")
        synthesized = f"Lỗi tra cứu metadata: {str(e)}"
        query_scope = None
        raw_results = ""
        metadata_hits = []

    payload = {
        "investigation_log": [f"Metadata Worker tìm thấy: {synthesized}"],
        "metadata_context": synthesized,
        # Chat/Telegram surface user-facing text via final_output (not planner JSON).
        "final_output": synthesized,
    }
    if raw_results:
        payload["metadata_raw_results"] = raw_results
    if query_scope is not None and query_scope.get("tables"):
        payload["query_scope"] = query_scope
    if metadata_hits:
        payload["metadata_hits"] = metadata_hits
    return payload


def sql_writer_worker_node(state: UniversalState, config: RunnableConfig) -> dict:
    """Worker sinh và thực thi SQL qua Writer sub-graph."""
    from ..writer_agent.graph import writer_subgraph
    from ..metadata_agent.metadata_retrieval_client import resolve_metadata_user_context
    from ..writer_agent.nodes import finalize_output

    user_input = state.get("user_input", "")
    metadata = state.get("metadata_context") or ""
    if not metadata:
        logs = state.get("investigation_log") or []
        metadata = "\n".join(logs)

    user_id, thread_id = resolve_metadata_user_context(state, config)
    from ..writer_agent.query_scope import resolve_query_scope

    query_scope = resolve_query_scope(
        state.get("query_scope"),
        metadata_context=metadata,
        raw_results=state.get("metadata_raw_results"),
        raw_hits=state.get("metadata_hits"),
    )
    table_count = len((query_scope or {}).get("tables") or [])
    if table_count:
        print(f"📋 [SQL Writer Worker] queryScope: {table_count} table(s)")
    else:
        print("⚠️ [SQL Writer Worker] queryScope.tables trống — filter-service sẽ từ chối SQL")

    print(f"\n{'─' * 50}")
    print(f"✍️ [SQL Writer Worker] Bắt đầu (userId={user_id})...")
    print(f"{'─' * 50}")

    try:
        result = writer_subgraph.invoke(
            {
                "user_input": user_input,
                "metadata_context": metadata,
                "metadata_raw_results": state.get("metadata_raw_results"),
                "metadata_hits": state.get("metadata_hits"),
                "query_scope": query_scope,
                "user_id": user_id,
                "thread_id": thread_id,
                "db_dialect": state.get("db_dialect"),
            },
            config=config,
        )
    except Exception as exc:
        print(f"⚠️ [SQL Writer Worker] Lỗi sub-graph: {exc}")
        return {
            "final_output": f"Lỗi SQL Writer: {exc}",
            "investigation_log": [f"SQL Writer Worker lỗi: {exc}"],
        }

    generated_sql = result.get("generated_sql") or ""
    preview = result.get("sql_result_preview")
    execution_error = result.get("sql_execution_error")
    attempts = (result.get("sql_repair_attempts") or 0) + 1
    row_count = result.get("execution_row_count") or 0
    repaired = (result.get("sql_repair_attempts") or 0) > 0

    if preview:
        final_output = finalize_output(
            generated_sql,
            row_count,
            preview,
            repaired=repaired,
        )
        return {
            "db_dialect": result.get("db_dialect"),
            "generated_sql": generated_sql,
            "sql_result_preview": preview,
            "sql_execution_error": None,
            "execution_attempts": attempts,
            "final_output": final_output,
            "investigation_log": [
                f"SQL Writer Worker: Sinh và thực thi SQL thành công sau {attempts} lần thử."
            ],
        }

    if not result.get("sql_repairable", True):
        final_output = (
            f"Không có quyền thực thi truy vấn.\n\n"
            f"Lỗi ({result.get('sql_error_code')}): {execution_error}"
        )
    else:
        final_output = (
            "Không thể thực thi query sau nhiều lần tự sửa.\n\n"
            f"SQL cuối cùng:\n{generated_sql}\n\n"
            f"Lỗi: {execution_error}"
        )

    return {
        "db_dialect": result.get("db_dialect"),
        "generated_sql": generated_sql,
        "sql_result_preview": None,
        "sql_execution_error": execution_error,
        "execution_attempts": attempts,
        "final_output": final_output,
        "investigation_log": [
            f"SQL Writer Worker: Không thể thực thi SQL sau {attempts} lần thử."
        ],
    }
