"""Neo4j table expansion for the metadata retriever."""

from __future__ import annotations

from ..config import (
    METADATA_NEO4J_ENABLED,
    METADATA_NEO4J_MAX_HOPS,
    METADATA_NEO4J_MAX_TABLES,
)


def expand_tables_from_neo4j(seed_tables: list[str]) -> tuple[list[str], str]:
    """
    Expand seed tables using Neo4j and return formatted join context.

    Returns (expanded_table_names, neo4j_join_text). On failure, returns seeds only.
    """
    seeds = [t for t in dict.fromkeys(seed_tables) if t and t != "_RELATIONSHIP"]
    if not METADATA_NEO4J_ENABLED or not seeds:
        return seeds, ""

    from ..sql_writer_agent.neo4j_client import Neo4jRelationshipClient

    client = Neo4jRelationshipClient()
    try:
        expanded = client.collect_related_tables(
            seeds,
            max_hops=METADATA_NEO4J_MAX_HOPS,
            max_tables=METADATA_NEO4J_MAX_TABLES,
        )
        join_text = client.format_relationships_for_metadata(
            expanded,
            max_hops=METADATA_NEO4J_MAX_HOPS,
        )
        return expanded, join_text
    except Exception as exc:
        print(f"⚠️ [Retriever] Neo4j expansion lỗi: {exc}")
        return seeds, ""
    finally:
        client.close()
