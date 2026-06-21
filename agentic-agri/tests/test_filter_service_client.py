"""Unit tests for filter-service metadata client and retrieval factory."""

import importlib
from unittest.mock import MagicMock, patch

import pytest

importlib.import_module("universal_agent.metadata_agent.nodes")

from universal_agent.metadata_agent.filter_service_client import (
    FilterServiceClient,
    FilterServiceError,
)
from universal_agent.metadata_agent.metadata_retrieval_client import (
    create_metadata_retrieval_client,
    resolve_metadata_user_context,
)
from universal_agent.metadata_agent.opensearch_client import OpenSearchClient


class TestResolveMetadataUserContext:
    def test_priority_state_over_env(self, monkeypatch):
        monkeypatch.setenv("METADATA_TEST_USER_ID", "env-user")
        uid, tid = resolve_metadata_user_context(
            {"user_id": "state-user", "thread_id": "t1"},
            {"configurable": {"user_id": "cfg-user", "thread_id": "t2"}},
        )
        assert uid == "state-user"
        assert tid == "t1"

    def test_configurable_fallback(self):
        uid, tid = resolve_metadata_user_context(
            {},
            {"configurable": {"user_id": "cfg-user", "thread_id": "u:ch1"}},
        )
        assert uid == "cfg-user"
        assert tid == "u:ch1"

    def test_env_test_user_id(self, monkeypatch):
        monkeypatch.setenv("METADATA_TEST_USER_ID", "analyst-gl")
        uid, _ = resolve_metadata_user_context({}, None)
        assert uid == "analyst-gl"

    def test_env_overrides_dev_user_placeholder_from_config(self, monkeypatch):
        monkeypatch.setenv("METADATA_TEST_USER_ID", "845069b7-a70f-58f5-b8df-1e0c5682f3e0")
        uid, _ = resolve_metadata_user_context(
            {},
            {"configurable": {"user_id": "dev-user", "thread_id": "dev-user:ch1"}},
        )
        assert uid == "845069b7-a70f-58f5-b8df-1e0c5682f3e0"

    def test_real_user_id_not_overridden_by_env(self, monkeypatch):
        monkeypatch.setenv("METADATA_TEST_USER_ID", "env-user")
        uid, _ = resolve_metadata_user_context(
            {},
            {"configurable": {"user_id": "real-jwt-user"}},
        )
        assert uid == "real-jwt-user"

    def test_default_dev_user(self, monkeypatch):
        monkeypatch.delenv("METADATA_TEST_USER_ID", raising=False)
        uid, _ = resolve_metadata_user_context({}, None)
        assert uid == "dev-user"


class TestCreateMetadataRetrievalClient:
    def test_returns_opensearch_when_disabled(self, monkeypatch):
        monkeypatch.setenv("METADATA_USE_FILTER_SERVICE", "false")
        monkeypatch.setenv("FILTER_SERVICE_BASE_URL", "http://localhost:8080")
        client = create_metadata_retrieval_client("u1", "u1:ch1")
        assert isinstance(client, OpenSearchClient)

    def test_returns_filter_client_when_enabled(self, monkeypatch):
        monkeypatch.setenv("METADATA_USE_FILTER_SERVICE", "true")
        monkeypatch.setenv("FILTER_SERVICE_BASE_URL", "http://localhost:8080")
        client = create_metadata_retrieval_client("analyst-gl", "analyst-gl:demo")
        assert isinstance(client, FilterServiceClient)


class TestFilterServiceClient:
    def _mock_response(self, payload: dict) -> MagicMock:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = payload
        resp.text = ""
        return resp

    @patch("universal_agent.metadata_agent.filter_service_client.httpx.Client")
    def test_hybrid_search_parses_hits(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.request.return_value = self._mock_response(
            {
                "success": True,
                "data": {
                    "hits": [
                        {
                            "_id": "doc-1",
                            "_score": 1.5,
                            "_source": {
                                "record_type": "TABLE",
                                "table_name": "CIF_CUSTOMERS",
                            },
                        }
                    ],
                    "warnings": [],
                },
            }
        )

        client = FilterServiceClient(
            "analyst-cif", "analyst-cif:demo", base_url="http://localhost:8080"
        )
        hits = client.hybrid_search("CIF customers", size=5)

        assert len(hits) == 1
        assert hits[0]["_id"] == "doc-1"
        assert hits[0]["_source"]["table_name"] == "CIF_CUSTOMERS"
        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["json"]["userId"] == "analyst-cif"
        assert call_kwargs["json"]["threadId"] == "analyst-cif:demo"

    @patch("universal_agent.metadata_agent.filter_service_client.httpx.Client")
    def test_api_error_raises_filter_service_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.request.return_value = self._mock_response(
            {
                "success": False,
                "error": {"code": "FORBIDDEN", "message": "No access"},
            }
        )

        client = FilterServiceClient(
            "restricted-user", base_url="http://localhost:8080"
        )
        with pytest.raises(FilterServiceError) as exc_info:
            client.hybrid_search("GL_ACCOUNTS")
        assert exc_info.value.code == "FORBIDDEN"


class TestRetrieverWithFilterClient:
    @patch("universal_agent.metadata_agent.nodes.expand_tables_from_neo4j")
    @patch("universal_agent.metadata_agent.nodes.create_metadata_retrieval_client")
    def test_retriever_passes_user_context(self, mock_factory, mock_neo4j):
        mock_neo4j.return_value = (["GL_JOURNAL_LINES"], "")
        mock_client = MagicMock()
        mock_client.hybrid_search.return_value = []
        mock_client.search_by_keyword.return_value = []
        mock_client.format_search_results.return_value = "Không tìm thấy"
        mock_factory.return_value = mock_client

        from universal_agent.metadata_agent.nodes import opensearch_retriever_node

        state = {
            "search_strategy": {
                "semantic_query": "test",
                "keywords": [],
                "target_tables": [],
                "record_types": ["TABLE"],
            },
            "user_id": "analyst-gl",
            "thread_id": "analyst-gl:ch1",
        }
        config = {"configurable": {"user_id": "analyst-gl", "thread_id": "analyst-gl:ch1"}}

        opensearch_retriever_node(state, config)

        mock_factory.assert_called_once_with("analyst-gl", "analyst-gl:ch1")
        mock_client.hybrid_search.assert_called_once()
        mock_client.get_relationships.assert_not_called()


class TestRetrieverNeo4jSchemaExpansion:
    @patch("universal_agent.metadata_agent.nodes.expand_tables_from_neo4j")
    @patch("universal_agent.metadata_agent.nodes.create_metadata_retrieval_client")
    def test_fetches_schema_for_neo4j_expanded_table(self, mock_factory, mock_neo4j):
        mock_neo4j.return_value = (
            ["GL_JOURNAL_LINES", "GL_ACCOUNTS"],
            "[RELATIONSHIP] FK link",
        )
        mock_client = MagicMock()
        mock_client.hybrid_search.return_value = [
            {
                "_id": "col1",
                "_source": {
                    "record_type": "COLUMN",
                    "table_name": "GL_JOURNAL_LINES",
                    "column_name": "ACCOUNT_ID",
                },
            }
        ]
        mock_client.get_table_metadata.return_value = [
            {"_id": "tbl_gl_accounts", "_source": {"record_type": "TABLE", "table_name": "GL_ACCOUNTS"}}
        ]
        mock_client.get_table_schema.return_value = [
            {
                "_id": "col_gl_accounts",
                "_source": {
                    "record_type": "COLUMN",
                    "table_name": "GL_ACCOUNTS",
                    "column_name": "ACCOUNT_ID",
                },
            }
        ]
        mock_client.format_search_results.return_value = "formatted"
        mock_factory.return_value = mock_client

        from universal_agent.metadata_agent.nodes import opensearch_retriever_node

        result = opensearch_retriever_node(
            {
                "search_strategy": {
                    "semantic_query": "journal lines",
                    "keywords": [],
                    "target_tables": [],
                    "record_types": ["TABLE", "COLUMN"],
                }
            },
            None,
        )

        mock_client.get_table_schema.assert_called_once_with("GL_ACCOUNTS")
        mock_client.get_table_metadata.assert_called_once_with("GL_ACCOUNTS")
        mock_client.get_relationships.assert_not_called()
        assert "GL_ACCOUNTS" in result["expanded_tables"]
        assert "[RELATIONSHIP]" in result["raw_results"]
