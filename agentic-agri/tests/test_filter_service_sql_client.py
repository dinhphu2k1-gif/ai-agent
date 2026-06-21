"""Unit tests for filter-service SQL client and execution factory."""

from unittest.mock import MagicMock, patch

from universal_agent.writer_agent.db_executor_client import PostgresExecutorClient
from universal_agent.writer_agent.filter_service_sql_client import FilterServiceSqlClient
from universal_agent.writer_agent.sql_execution_client import (
    _PostgresWrapper,
    create_sql_execution_client,
)


class TestFilterServiceSqlClient:
    def _mock_response(self, payload: dict, status_code: int = 200) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = payload
        resp.text = str(payload)
        return resp

    @patch("universal_agent.writer_agent.filter_service_sql_client.httpx.Client")
    def test_execute_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = self._mock_response(
            {
                "success": True,
                "data": {
                    "executedSql": "SELECT 1 LIMIT 100",
                    "columns": ["x"],
                    "rows": [[1]],
                    "rowCount": 1,
                },
            }
        )

        client = FilterServiceSqlClient("user-1", "user-1:ch1", base_url="http://fs")
        scope = {"source": "metadata_agent", "tables": [{"name": "GL_ACCOUNTS"}]}
        result = client.execute_query("SELECT 1", scope)

        assert result.success
        assert result.columns == ["x"]
        assert result.row_count == 1
        body = mock_client.post.call_args.kwargs["json"]
        assert body["queryScope"] == scope
        assert body["userId"] == "user-1"

    @patch("universal_agent.writer_agent.filter_service_sql_client.httpx.Client")
    def test_strips_trailing_limit_before_post(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = self._mock_response(
            {
                "success": True,
                "data": {
                    "executedSql": "SELECT 1 LIMIT 100",
                    "columns": ["x"],
                    "rows": [[1]],
                    "rowCount": 1,
                },
            }
        )

        client = FilterServiceSqlClient("user-1", base_url="http://fs")
        scope = {"source": "metadata_agent", "tables": [{"name": "GL_ACCOUNTS"}]}
        client.execute_query("SELECT 1 LIMIT 50", scope, limit=100)

        body = mock_client.post.call_args.kwargs["json"]
        assert body["sql"] == "SELECT 1"
        assert body["limit"] == 100

    @patch("universal_agent.writer_agent.filter_service_sql_client.httpx.Client")
    def test_execute_forbidden_not_repairable(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = self._mock_response(
            {
                "success": False,
                "error": {"code": "FORBIDDEN", "message": "No SELECT on CIF_SSN"},
            }
        )

        client = FilterServiceSqlClient("user-1", base_url="http://fs")
        scope = {"source": "metadata_agent", "tables": [{"name": "CIF_SSN"}]}
        result = client.execute_query("SELECT * FROM cif_ssn", scope)

        assert not result.success
        assert result.error_code == "FORBIDDEN"
        assert result.repairable is False

    def test_missing_query_scope_returns_validation_error(self):
        client = FilterServiceSqlClient("user-1", base_url="http://fs")
        result = client.execute_query("SELECT 1", {"source": "metadata_agent", "tables": []})
        assert not result.success
        assert result.error_code == "VALIDATION_ERROR"


class TestCreateSqlExecutionClient:
    def test_returns_postgres_when_disabled(self, monkeypatch):
        monkeypatch.setenv("SQL_USE_FILTER_SERVICE", "false")
        client = create_sql_execution_client("u1", "u1:ch1")
        assert isinstance(client, _PostgresWrapper)

    def test_returns_filter_client_when_enabled(self, monkeypatch):
        monkeypatch.setenv("SQL_USE_FILTER_SERVICE", "true")
        monkeypatch.setenv("FILTER_SERVICE_BASE_URL", "http://localhost:8000")
        client = create_sql_execution_client("analyst-gl", "analyst-gl:demo")
        assert isinstance(client, FilterServiceSqlClient)
