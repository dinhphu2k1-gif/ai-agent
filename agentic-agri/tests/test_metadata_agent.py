# tests/test_metadata_agent.py
"""
Test suite cho Metadata Agent — Level 1 & Level 2.
Level 1: Unit tests pure logic (Mock hoàn toàn, không cần OpenSearch / LLM).
Level 2: Unit tests với mock LLM responses.
"""

import json
from unittest.mock import patch, MagicMock

# ════════════════════════════════════════════════════════════
# LEVEL 1: UNIT TESTS — PURE LOGIC
# ════════════════════════════════════════════════════════════


class TestLevel1FormatSearchResults:
    """Test format_search_results với mock hits."""

    def test_format_column_record(self):
        """1.1 — Format COLUMN record hiển thị đúng table, column, data_type."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient

        hits = [
            {
                "_id": "GL_ACCOUNTS_ACCOUNT_ID",
                "_score": 1.0,
                "_source": {
                    "record_type": "COLUMN",
                    "table_name": "GL_ACCOUNTS",
                    "column_name": "ACCOUNT_ID",
                    "data_type": "NUMBER(10)",
                    "business_name": "Mã Tài Khoản",
                    "description": "Khóa chính định danh duy nhất mỗi tài khoản kế toán.",
                    "is_primary_key": True,
                    "is_foreign_key": False,
                    "allowed_values": None,
                    "business_rules": "Sinh tự động bởi GL_ACCOUNTS_SEQ.",
                },
            }
        ]

        result = OpenSearchClient.format_search_results(hits)

        assert "GL_ACCOUNTS" in result
        assert "ACCOUNT_ID" in result
        assert "NUMBER(10)" in result
        assert "[PK]" in result
        assert "Mã Tài Khoản" in result

    def test_format_table_record(self):
        """1.2 — Format TABLE record hiển thị business_name, table_purpose, PK."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient

        hits = [
            {
                "_id": "TABLE_GL_ACCOUNTS",
                "_score": 1.0,
                "_source": {
                    "record_type": "TABLE",
                    "table_name": "GL_ACCOUNTS",
                    "business_name": "Danh Mục Tài Khoản Kế Toán",
                    "description": "Bảng master lưu trữ hệ thống tài khoản...",
                    "table_purpose": "Tra cứu mã tài khoản, xác định bản chất Nợ/Có.",
                    "primary_key_columns": "ACCOUNT_ID",
                    "natural_key": "ACCOUNT_CODE",
                    "related_tables": ["GL_JOURNAL_LINES", "GL_BALANCES"],
                    "estimated_row_count": "~5,000",
                    "business_rules": "Chỉ tài khoản cấp 4 mới được phép hạch toán.",
                },
            }
        ]

        result = OpenSearchClient.format_search_results(hits)

        assert "[TABLE]" in result
        assert "GL_ACCOUNTS" in result
        assert "Danh Mục Tài Khoản Kế Toán" in result
        assert "ACCOUNT_ID" in result
        assert "GL_JOURNAL_LINES" in result

    def test_format_relationship_record(self):
        """1.3 — Format RELATIONSHIP record hiển thị join_path, sample_sql."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient

        hits = [
            {
                "_id": "REL_chi_tiet_but_toan",
                "_score": 1.0,
                "_source": {
                    "record_type": "RELATIONSHIP",
                    "relationship_name": "Chi tiết bút toán kế toán",
                    "description": "Truy vấn chi tiết các dòng ghi Nợ/Có.",
                    "join_path": "GL_JOURNAL_HEADERS → GL_JOURNAL_LINES → GL_ACCOUNTS",
                    "sample_sql": "SELECT h.JOURNAL_NUMBER FROM GL_JOURNAL_HEADERS h JOIN GL_JOURNAL_LINES l ON h.JOURNAL_ID = l.JOURNAL_ID",
                    "related_tables": [
                        "GL_JOURNAL_HEADERS",
                        "GL_JOURNAL_LINES",
                        "GL_ACCOUNTS",
                    ],
                },
            }
        ]

        result = OpenSearchClient.format_search_results(hits)

        assert "[RELATIONSHIP]" in result
        assert "join_path" in result.lower() or "Join Path" in result
        assert "GL_JOURNAL_HEADERS" in result
        assert "SELECT" in result

    def test_format_empty_results(self):
        """1.4 — Empty hits trả về thông báo không tìm thấy."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient

        result = OpenSearchClient.format_search_results([])

        assert "Không tìm thấy" in result

    def test_format_foreign_key_display(self):
        """1.5 — COLUMN với FK hiển thị thông tin references."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient

        hits = [
            {
                "_id": "GL_JOURNAL_LINES_ACCOUNT_ID",
                "_score": 1.0,
                "_source": {
                    "record_type": "COLUMN",
                    "table_name": "GL_JOURNAL_LINES",
                    "column_name": "ACCOUNT_ID",
                    "data_type": "NUMBER(10)",
                    "business_name": "Mã Tài Khoản",
                    "description": "Khóa ngoại trỏ đến tài khoản kế toán.",
                    "is_primary_key": False,
                    "is_foreign_key": True,
                    "references_table": "GL_ACCOUNTS",
                    "references_column": "ACCOUNT_ID",
                    "allowed_values": None,
                    "business_rules": None,
                },
            }
        ]

        result = OpenSearchClient.format_search_results(hits)

        assert "FK" in result
        assert "GL_ACCOUNTS" in result


class TestLevel1MetadataState:
    """Test MetadataState schema."""

    def test_metadata_state_creation(self):
        """1.6 — MetadataState khởi tạo đúng các field."""
        from universal_agent.metadata_agent.state import MetadataState

        state: MetadataState = {
            "user_input": "test query",
            "investigation_log_input": "some log",
            "search_strategy": None,
            "raw_results": "",
            "synthesized_schema": "",
        }

        assert state["user_input"] == "test query"
        assert state["search_strategy"] is None

    def test_mixed_record_types_format(self):
        """1.7 — Mix TABLE + COLUMN + RELATIONSHIP trong cùng 1 kết quả."""
        from universal_agent.metadata_agent.opensearch_client import OpenSearchClient

        hits = [
            {
                "_id": "TABLE_GL_ACCOUNTS",
                "_score": 2.0,
                "_source": {
                    "record_type": "TABLE",
                    "table_name": "GL_ACCOUNTS",
                    "business_name": "Danh Mục Tài Khoản",
                    "description": "Bảng master.",
                    "table_purpose": "Tra cứu.",
                    "primary_key_columns": "ACCOUNT_ID",
                    "natural_key": "ACCOUNT_CODE",
                    "related_tables": [],
                    "estimated_row_count": "~5,000",
                    "business_rules": None,
                },
            },
            {
                "_id": "GL_ACCOUNTS_ACCOUNT_ID",
                "_score": 1.5,
                "_source": {
                    "record_type": "COLUMN",
                    "table_name": "GL_ACCOUNTS",
                    "column_name": "ACCOUNT_ID",
                    "data_type": "NUMBER(10)",
                    "business_name": "Mã Tài Khoản",
                    "description": "PK.",
                    "is_primary_key": True,
                    "is_foreign_key": False,
                    "allowed_values": None,
                    "business_rules": None,
                },
            },
            {
                "_id": "REL_test",
                "_score": 1.0,
                "_source": {
                    "record_type": "RELATIONSHIP",
                    "relationship_name": "Test Relationship",
                    "description": "Test join.",
                    "join_path": "A → B",
                    "sample_sql": "SELECT 1",
                    "related_tables": ["A", "B"],
                },
            },
        ]

        result = OpenSearchClient.format_search_results(hits)

        assert "[TABLE]" in result
        assert "[COLUMN]" in result
        assert "[RELATIONSHIP]" in result


# ════════════════════════════════════════════════════════════
# LEVEL 2: UNIT TESTS — MOCK LLM
# ════════════════════════════════════════════════════════════


class TestLevel2QueryAnalyzerNode:
    """Test query_analyzer_node với mock LLM."""

    @patch("universal_agent.metadata_agent.nodes.worker_llm")
    def test_output_format_valid_json(self, mock_llm):
        """2.1 — LLM trả JSON hợp lệ → output search_strategy đúng format."""
        from universal_agent.metadata_agent.nodes import query_analyzer_node

        strategy_json = json.dumps(
            {
                "semantic_query": "số dư tài khoản cuối kỳ",
                "keywords": ["số dư", "balance", "GL_BALANCES"],
                "target_tables": ["GL_BALANCES"],
                "record_types": ["TABLE", "COLUMN"],
            }
        )

        mock_response = MagicMock()
        mock_response.content = strategy_json
        mock_llm.invoke.return_value = mock_response

        state = {
            "user_input": "Cho tôi xem số dư cuối kỳ",
            "investigation_log_input": "",
        }

        result = query_analyzer_node(state)

        assert "search_strategy" in result
        strategy = result["search_strategy"]
        assert "semantic_query" in strategy
        assert "keywords" in strategy
        assert "target_tables" in strategy
        assert "record_types" in strategy
        assert "GL_BALANCES" in strategy["target_tables"]

    @patch("universal_agent.metadata_agent.nodes.worker_llm")
    def test_fallback_on_invalid_json(self, mock_llm):
        """2.2 — LLM trả text không phải JSON → fallback strategy hợp lý."""
        from universal_agent.metadata_agent.nodes import query_analyzer_node

        mock_response = MagicMock()
        mock_response.content = "Đây không phải JSON, LLM trả lời sai format..."
        mock_llm.invoke.return_value = mock_response

        state = {
            "user_input": "Xem thông tin khách hàng",
            "investigation_log_input": "",
        }

        result = query_analyzer_node(state)

        # Phải fallback, không crash
        assert "search_strategy" in result
        strategy = result["search_strategy"]
        assert strategy["semantic_query"] == "Xem thông tin khách hàng"
        assert isinstance(strategy["keywords"], list)
        assert "COLUMN" in strategy["record_types"]

    @patch("universal_agent.metadata_agent.nodes.worker_llm")
    def test_markdown_wrapped_json(self, mock_llm):
        """2.3 — LLM trả JSON bọc trong markdown → parse thành công."""
        from universal_agent.metadata_agent.nodes import query_analyzer_node

        strategy_json = json.dumps(
            {
                "semantic_query": "bút toán kế toán",
                "keywords": ["bút toán", "journal"],
                "target_tables": ["GL_JOURNAL_HEADERS"],
                "record_types": ["TABLE", "COLUMN", "RELATIONSHIP"],
            }
        )

        mock_response = MagicMock()
        mock_response.content = f"```json\n{strategy_json}\n```"
        mock_llm.invoke.return_value = mock_response

        state = {
            "user_input": "Xem bút toán kế toán",
            "investigation_log_input": "",
        }

        result = query_analyzer_node(state)

        assert "search_strategy" in result
        assert result["search_strategy"]["target_tables"] == ["GL_JOURNAL_HEADERS"]


class TestLevel2ResultSynthesizerNode:
    """Test result_synthesizer_node với mock LLM."""

    @patch("universal_agent.metadata_agent.nodes.worker_llm")
    def test_synthesize_with_results(self, mock_llm):
        """2.4 — Có raw_results → LLM tổng hợp schema."""
        from universal_agent.metadata_agent.nodes import result_synthesizer_node

        mock_response = MagicMock()
        mock_response.content = (
            "BẢNG LIÊN QUAN:\n"
            "GL_BALANCES — Số Dư Tài Khoản Theo Kỳ\n"
            "SCHEMA:\n"
            "- BALANCE_ID (NUMBER) [PK]\n"
            "- CLOSING_BALANCE_DR (NUMBER) — Số dư cuối kỳ Nợ"
        )
        mock_llm.invoke.return_value = mock_response

        state = {
            "user_input": "Xem số dư cuối kỳ",
            "raw_results": "[TABLE] GL_BALANCES — Số Dư Tài Khoản...",
            "neo4j_join_context": "",
        }

        result = result_synthesizer_node(state)

        assert "synthesized_schema" in result
        assert result["synthesized_schema"] != ""
        assert "GL_BALANCES" in result["synthesized_schema"]

    def test_synthesize_with_empty_results(self):
        """2.5 — Không có raw_results → trả thông báo lỗi."""
        from universal_agent.metadata_agent.nodes import result_synthesizer_node

        state = {
            "user_input": "Query vô nghĩa",
            "raw_results": "Không tìm thấy kết quả nào trong Data Dictionary.",
        }

        result = result_synthesizer_node(state)

        assert "synthesized_schema" in result
        assert "Không tìm thấy" in result["synthesized_schema"]


class TestLevel2MetadataWorkerNode:
    """Test metadata_worker_node (wrapper gọi sub-graph)."""

    @patch(
        "universal_agent.supervisor.nodes.metadata_subgraph"
        if False
        else "universal_agent.metadata_agent.graph.metadata_subgraph"
    )
    def test_metadata_worker_returns_correct_state(self, mock_subgraph):
        """2.6 — metadata_worker_node ghi investigation_log + metadata_context."""
        # Mock sẽ patch tại nơi import trong supervisor/nodes.py
        # Sử dụng cách khác: patch trực tiếp metadata_subgraph

        mock_subgraph_result = {
            "synthesized_schema": "GL_BALANCES: BALANCE_ID (PK), CLOSING_BALANCE_DR..."
        }

        with patch("universal_agent.metadata_agent.graph.metadata_subgraph") as mock_sg:
            mock_sg.invoke.return_value = mock_subgraph_result

            from universal_agent.supervisor.nodes import metadata_worker_node

            state = {
                "user_input": "Xem số dư",
                "investigation_log": ["Nhận yêu cầu: Xem số dư"],
            }

            result = metadata_worker_node(
                state,
                {"configurable": {"user_id": "dev-user", "thread_id": "dev-user:test"}},
            )

            assert "investigation_log" in result
            assert "metadata_context" in result
            assert "Metadata Worker tìm thấy" in result["investigation_log"][0]
            assert "GL_BALANCES" in result["metadata_context"]
