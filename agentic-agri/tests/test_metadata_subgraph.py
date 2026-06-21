# tests/test_metadata_subgraph.py
"""
Test suite cho Metadata Agent — Level 4.
Sub-Graph end-to-end tests (cần OpenSearch + LLM thật).

Chạy: pytest tests/test_metadata_subgraph.py -v
Yêu cầu: OpenSearch đang chạy + LLM endpoint khả dụng.
"""

import pytest
from dotenv import load_dotenv

load_dotenv()

# Skip toàn bộ module nếu không kết nối được OpenSearch
try:
    from universal_agent.metadata_agent.opensearch_client import OpenSearchClient

    osc = OpenSearchClient()
    client = osc.client
    client.info()
    OPENSEARCH_AVAILABLE = True
except Exception:
    OPENSEARCH_AVAILABLE = False

# Skip nếu LLM không khả dụng
try:
    from universal_agent.models import worker_llm

    worker_llm.invoke("test")
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not (OPENSEARCH_AVAILABLE and LLM_AVAILABLE),
    reason="OpenSearch hoặc LLM không khả dụng. Bỏ qua sub-graph tests.",
)


# ════════════════════════════════════════════════════════════
# LEVEL 4: SUB-GRAPH END-TO-END TESTS
# ════════════════════════════════════════════════════════════


class TestLevel4SubGraphEndToEnd:
    """Chạy toàn bộ metadata sub-graph với LLM + OpenSearch thật."""

    def _run_subgraph(self, user_input: str, log: str = "") -> dict:
        """Helper: chạy metadata sub-graph và trả kết quả."""
        from universal_agent.metadata_agent.graph import metadata_subgraph

        return metadata_subgraph.invoke(
            {
                "user_input": user_input,
                "investigation_log_input": log,
            }
        )

    def test_subgraph_single_table(self):
        """4.1 — Yêu cầu schema 1 bảng cụ thể → trả đúng schema."""
        result = self._run_subgraph("Cho tôi schema bảng GL_ACCOUNTS")

        schema = result.get("synthesized_schema", "")
        assert len(schema) > 100, f"Schema phải có nội dung, nhận được {len(schema)} ký tự"

        # Phải chứa thông tin bảng GL_ACCOUNTS
        schema_upper = schema.upper()
        assert "GL_ACCOUNTS" in schema_upper, f"Phải chứa GL_ACCOUNTS: {schema[:200]}"

        # Phải chứa ít nhất 1 cột đặc trưng
        assert any(
            col in schema_upper
            for col in ["ACCOUNT_ID", "ACCOUNT_CODE", "ACCOUNT_NAME", "ACCOUNT_TYPE"]
        ), f"Phải chứa ít nhất 1 cột đặc trưng: {schema[:300]}"

    def test_subgraph_business_term(self):
        """4.2 — Yêu cầu bằng thuật ngữ nghiệp vụ → tìm đúng bảng."""
        result = self._run_subgraph("Tôi muốn xem số dư cuối kỳ")

        schema = result.get("synthesized_schema", "")
        schema_upper = schema.upper()

        assert "GL_BALANCES" in schema_upper or "SỐ DƯ" in schema.upper(), (
            f"Phải liên quan đến số dư/GL_BALANCES: {schema[:300]}"
        )

    def test_subgraph_cross_domain(self):
        """4.3 — Yêu cầu cross-domain → schema chứa cả CIF + GL."""
        result = self._run_subgraph("Liệt kê giao dịch của khách hàng VIP")

        schema = result.get("synthesized_schema", "")
        schema_upper = schema.upper()

        # Phải chứa cả thông tin CIF và GL
        has_cif = "CIF" in schema_upper or "KHÁCH HÀNG" in schema_upper
        has_gl = (
            "GL_JOURNAL" in schema_upper
            or "GIAO DỊCH" in schema_upper
            or "BÚT TOÁN" in schema_upper
        )

        assert has_cif, f"Phải chứa thông tin CIF/khách hàng: {schema[:300]}"
        assert has_gl, f"Phải chứa thông tin GL/giao dịch: {schema[:300]}"

    def test_subgraph_relationship_query(self):
        """4.4 — Yêu cầu JOIN → output chứa join path hoặc SQL sample."""
        result = self._run_subgraph("Làm sao JOIN từ khách hàng sang sổ cái?")

        schema = result.get("synthesized_schema", "")
        schema_upper = schema.upper()

        assert "JOIN" in schema_upper or "→" in schema, (
            f"Phải chứa thông tin JOIN: {schema[:300]}"
        )

    def test_subgraph_ambiguous_query(self):
        """4.5 — Yêu cầu mơ hồ → không crash, trả kết quả hợp lý."""
        result = self._run_subgraph("Xem thông tin tài khoản")

        schema = result.get("synthesized_schema", "")

        # Phải trả về gì đó (không crash, không rỗng)
        assert len(schema) > 50, f"Phải trả kết quả hợp lý, nhận được {len(schema)} ký tự"

    def test_subgraph_state_completeness(self):
        """4.6 — Verify tất cả state fields được điền sau khi chạy sub-graph."""
        result = self._run_subgraph("Cho tôi thông tin bảng GL_PERIODS")

        # Tất cả field output phải có giá trị
        assert result.get("search_strategy") is not None, "search_strategy phải được điền"
        assert result.get("raw_results"), "raw_results phải có nội dung"
        assert result.get("synthesized_schema"), "synthesized_schema phải có nội dung"
