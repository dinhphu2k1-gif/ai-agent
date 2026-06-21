"""Unit tests for Neo4j metadata table expansion."""

from unittest.mock import MagicMock, patch

import pytest

from universal_agent.sql_writer_agent.neo4j_client import Neo4jRelationshipClient


def _mock_session(records_by_query: list[tuple[list[dict], list[dict]]]):
    """Return a session mock that yields records in order for session.run calls."""
    session = MagicMock()
    call_idx = {"i": 0}

    def run(_query, **kwargs):
        result = MagicMock()
        idx = call_idx["i"]
        call_idx["i"] += 1
        neighbor_rows, path_rows = (
            records_by_query[idx] if idx < len(records_by_query) else ([], [])
        )

        def single():
            return path_rows[0] if path_rows else None

        result.__iter__ = lambda self: iter(neighbor_rows)
        result.single = single
        return result

    session.run = run
    return session


class TestNeo4jCollectRelatedTables:
    @patch.object(Neo4jRelationshipClient, "driver", new_callable=MagicMock)
    def test_expands_neighbors_and_path_nodes(self, mock_driver):
        mock_driver.session.return_value.__enter__.return_value = _mock_session(
            [
                (
                    [
                        {"t1": "GL_JOURNAL_LINES", "t2": "GL_ACCOUNTS"},
                        {"t1": "GL_JOURNAL_LINES", "t2": "GL_JOURNAL_HEADERS"},
                    ],
                    [{"path_nodes": ["GL_JOURNAL_LINES", "GL_ACCOUNTS"]}],
                )
            ]
        )

        client = Neo4jRelationshipClient()
        expanded = client.collect_related_tables(
            ["GL_JOURNAL_LINES"], max_hops=2, max_tables=8
        )

        assert expanded[0] == "GL_JOURNAL_LINES"
        assert "GL_ACCOUNTS" in expanded
        assert "GL_JOURNAL_HEADERS" in expanded

    @patch.object(Neo4jRelationshipClient, "driver", new_callable=MagicMock)
    def test_empty_seed_returns_empty(self, mock_driver):
        client = Neo4jRelationshipClient()
        assert client.collect_related_tables([]) == []


class TestNeo4jFormatRelationshipsForMetadata:
    @patch.object(Neo4jRelationshipClient, "get_named_paths", return_value="")
    @patch.object(
        Neo4jRelationshipClient,
        "find_join_paths",
        return_value="[PATH] GL_JOURNAL_LINES -> GL_ACCOUNTS",
    )
    @patch.object(
        Neo4jRelationshipClient,
        "get_direct_relationships",
        return_value="[FK] GL_JOURNAL_LINES.ACCOUNT_ID -> GL_ACCOUNTS.ACCOUNT_ID",
    )
    def test_formats_relationship_blocks(self, _fk, _path, _named):
        client = Neo4jRelationshipClient()
        text = client.format_relationships_for_metadata(["GL_JOURNAL_LINES"])

        assert "[RELATIONSHIP]" in text
        assert "GL_JOURNAL_LINES" in text
        assert "GL_ACCOUNTS" in text


class TestExpandTablesFromNeo4j:
    @patch("universal_agent.metadata_agent.neo4j_expansion.Neo4jRelationshipClient")
    def test_returns_expanded_tables_and_join_text(self, mock_cls):
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.collect_related_tables.return_value = [
            "GL_JOURNAL_LINES",
            "GL_ACCOUNTS",
        ]
        mock_client.format_relationships_for_metadata.return_value = (
            "[RELATIONSHIP] FK\n  Join Path: test"
        )

        from universal_agent.metadata_agent.neo4j_expansion import expand_tables_from_neo4j

        tables, join_text = expand_tables_from_neo4j(["GL_JOURNAL_LINES"])

        assert "GL_ACCOUNTS" in tables
        assert "[RELATIONSHIP]" in join_text
        mock_client.close.assert_called_once()

    @patch("universal_agent.metadata_agent.neo4j_expansion.METADATA_NEO4J_ENABLED", False)
    def test_disabled_returns_seeds_only(self):
        from universal_agent.metadata_agent.neo4j_expansion import expand_tables_from_neo4j

        tables, join_text = expand_tables_from_neo4j(["GL_JOURNAL_LINES"])
        assert tables == ["GL_JOURNAL_LINES"]
        assert join_text == ""
