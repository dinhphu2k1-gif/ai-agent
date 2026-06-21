# tests/test_opensearch_integration.py
"""
Test suite cho Metadata Agent — Level 3.
Integration tests với OpenSearch thật (index data_dictionary phải đã nạp dữ liệu).

Chạy: pytest tests/test_opensearch_integration.py -v
Yêu cầu: OpenSearch đang chạy và index 'data_dictionary' đã được nạp.
"""

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

pytestmark = pytest.mark.skipif(
    not OPENSEARCH_AVAILABLE,
    reason="OpenSearch không khả dụng. Bỏ qua integration tests.",
)


# ════════════════════════════════════════════════════════════
# LEVEL 3: INTEGRATION TESTS VỚI OPENSEARCH THẬT
# ════════════════════════════════════════════════════════════


class TestLevel3KeywordSearch:
    """Test keyword search trên Data Dictionary thật."""

    def test_keyword_search_so_du(self):
        """3.1 — Tìm 'số dư' trả về bảng GL_BALANCES."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient
        osc = OpenSearchClient()

        hits = osc.search_by_keyword("số dư", size=10)

        assert len(hits) > 0
        table_names = [h["_source"].get("table_name", "") for h in hits]
        assert "GL_BALANCES" in table_names, (
            f"Kỳ vọng GL_BALANCES trong kết quả, nhận được: {table_names}"
        )

    def test_keyword_search_khach_hang(self):
        """3.2 — Tìm 'khách hàng' trả về bảng CIF_CUSTOMERS."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient
        osc = OpenSearchClient()

        hits = osc.search_by_keyword("khách hàng", size=10)

        assert len(hits) > 0
        table_names = [h["_source"].get("table_name", "") for h in hits]
        assert any(
            "CIF" in t for t in table_names
        ), f"Kỳ vọng bảng CIF trong kết quả, nhận được: {table_names}"


class TestLevel3GetTableSchema:
    """Test lấy schema bảng."""

    def test_get_table_schema_gl_accounts(self):
        """3.3 — Lấy schema GL_ACCOUNTS trả về >= 10 COLUMN records."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient
        osc = OpenSearchClient()

        hits = osc.get_table_schema("GL_ACCOUNTS")

        assert len(hits) >= 10, f"GL_ACCOUNTS phải có >= 10 cột, nhận được {len(hits)}"

        column_names = [h["_source"]["column_name"] for h in hits]
        assert "ACCOUNT_ID" in column_names
        assert "ACCOUNT_CODE" in column_names

        # Tất cả phải là COLUMN records
        for h in hits:
            assert h["_source"]["record_type"] == "COLUMN"

    def test_get_table_metadata_gl_balances(self):
        """3.4 — Lấy TABLE metadata GL_BALANCES."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient
        osc = OpenSearchClient()

        hits = osc.get_table_metadata("GL_BALANCES")

        assert len(hits) == 1
        src = hits[0]["_source"]
        assert src["record_type"] == "TABLE"
        assert src["table_name"] == "GL_BALANCES"
        assert "business_name" in src
        assert "related_tables" in src
        assert len(src["related_tables"]) > 0


class TestLevel3GetRelationships:
    """Test lấy relationship records."""

    def test_get_relationships_cross_domain(self):
        """3.5 — Tìm RELATIONSHIP chứa CIF_CUSTOMERS và GL bảng."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient
        osc = OpenSearchClient()

        hits = osc.get_relationships(["CIF_CUSTOMERS", "GL_JOURNAL_LINES"])

        assert len(hits) > 0

        # Ít nhất 1 relationship phải chứa join_path
        found_cross_domain = False
        for h in hits:
            src = h["_source"]
            assert src["record_type"] == "RELATIONSHIP"
            join_path = src.get("join_path", "")
            if "CIF" in join_path or "GL" in join_path:
                found_cross_domain = True

        assert found_cross_domain, "Phải tìm thấy ít nhất 1 cross-domain relationship"


class TestLevel3HybridSearch:
    """Test hybrid search (BM25 + k-NN)."""

    def test_hybrid_search_semantic(self):
        """3.6 — Hybrid search với semantic query trả về kết quả liên quan."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient
        osc = OpenSearchClient()

        hits = osc.hybrid_search("xem thông tin tài khoản tiền gửi của khách hàng", size=10)

        assert len(hits) > 0

        # Phải tìm thấy ít nhất bảng liên quan đến tài khoản hoặc khách hàng
        table_names = set()
        for h in hits:
            tbl = h["_source"].get("table_name", "")
            if tbl:
                table_names.add(tbl)

        relevant = {"GL_ACCOUNTS", "CIF_ACCOUNTS", "CIF_CUSTOMERS"}
        found = table_names & relevant
        assert len(found) > 0, (
            f"Kỳ vọng ít nhất 1 trong {relevant}, nhận được: {table_names}"
        )

    def test_hybrid_search_with_record_type_filter(self):
        """3.7 — Hybrid search filter record_type=TABLE chỉ trả TABLE records."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient
        osc = OpenSearchClient()

        hits = osc.hybrid_search("bút toán kế toán", record_type="TABLE", size=5)

        assert len(hits) > 0
        for h in hits:
            assert h["_source"]["record_type"] == "TABLE", (
                f"Record type phải là TABLE, nhận được: {h['_source']['record_type']}"
            )


class TestLevel3FormatIntegration:
    """Test format kết quả thật từ OpenSearch."""

    def test_format_real_search_results(self):
        """3.8 — Format kết quả hybrid search thật thành text có cấu trúc."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient
        osc = OpenSearchClient()

        hits = osc.hybrid_search("số dư tài khoản cuối kỳ", size=5)
        formatted = OpenSearchClient.format_search_results(hits)

        assert len(formatted) > 100, "Kết quả format phải có nội dung thực chất"
        # Phải chứa ít nhất 1 tag loại record
        assert any(tag in formatted for tag in ["[TABLE]", "[COLUMN]", "[RELATIONSHIP]"])
