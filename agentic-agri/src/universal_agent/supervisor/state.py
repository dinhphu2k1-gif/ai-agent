"""
State definitions cho Supervisor Graph.
"""

from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, ConfigDict, Field
from operator import add


class UniversalState(TypedDict):
    """
    Cấu trúc bộ nhớ State di chuyển qua các node trong Graph.
    """

    user_input: str
    long_term_context: str
    investigation_log: Annotated[list[str], add]

    # Các trường phục vụ Dynamic Routing
    intent: str
    target_agent: Optional[str]  # Tên Agent nội bộ cần gọi
    message_to_user: Optional[str]  # Câu hỏi dành cho user (HITL)

    # Metadata đã tra cứu từ OpenSearch (do Metadata Agent ghi)
    metadata_context: Optional[str]
    metadata_raw_results: Optional[str]
    query_scope: Optional[dict]
    metadata_hits: Optional[list]
    neo4j_context: Optional[str]

    # SQL generation / execution
    db_dialect: Optional[str]
    generated_sql: Optional[str]
    sql_result_preview: Optional[str]
    sql_execution_error: Optional[str]
    execution_attempts: int

    final_output: str
    planner_ui_options: Optional[list[dict]]


class PlannerUIOption(BaseModel):
    """Structured HITL choices for action.prompt (FE three-option pattern)."""

    model_config = ConfigDict(populate_by_name=True)

    label: str
    action_id: str = Field(alias="actionId")


class PlannerDecision(BaseModel):
    """
    Schema ép buộc LLM xuất JSON chứa các quyết định định tuyến.
    """

    intent: Literal["consult_agent", "ask_user", "finalize_plan"] = Field(
        description="Quyết định bước đi tiếp theo:\n"
        " - 'consult_agent': Cần hỏi/tra cứu thông tin từ một Agent nội bộ khác.\n"
        " - 'ask_user': Thiếu thông tin nghiệp vụ, cần dừng lại hỏi người dùng.\n"
        " - 'finalize_plan': Đã đủ thông tin schema và nghiệp vụ, chốt kế hoạch thực thi."
    )
    reasoning: str = Field(
        description="Lý luận chi tiết giải thích quyết định dựa trên log và context."
    )
    target_agent: Optional[str] = Field(
        description="Tên của Agent cần gọi nếu intent là 'consult_agent'. "
        "Các Agent khả dụng: 'metadata_worker', 'sql_writer_worker'.",
        default=None,
    )
    message_to_user: Optional[str] = Field(
        description="Nội dung câu hỏi gửi cho khách hàng nếu intent là 'ask_user'.",
        default=None,
    )
    ui_options: Optional[list[PlannerUIOption]] = Field(
        description="2–3 structured choices when intent is ask_user (label + actionId).",
        default=None,
    )
