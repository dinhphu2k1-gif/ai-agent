"""OpenSearch query bodies and catalog resolution for metadata_agent hits.

Query shapes ported from ``agentic-agri`` ``OpenSearchClient`` (BM25 fields, term filters).
kNN hybrid leg requires an embedding service — when unavailable, hybrid falls back to
the same BM25 bool as keyword (see ``build_hybrid_search_body``).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.resource_repo import ResourceRepository

_RECORD_TABLE = "TABLE"
_RECORD_COLUMN = "COLUMN"
_RECORD_RELATIONSHIP = "RELATIONSHIP"

# Align with agentic-agri OpenSearchClient.search_by_keyword / hybrid multi_match
_KEYWORD_FIELDS = [
    "business_name^3",
    "description^2",
    "business_rules",
    "table_purpose",
    "relationship_name^2",
]

_SOURCE_EXCLUDES = {"excludes": ["description_vector"]}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _record_type(source: dict[str, Any]) -> str:
    return _norm(source.get("record_type")).upper()


def _database_name(source: dict[str, Any]) -> str:
    return _norm(source.get("database_name") or source.get("db_name"))


def build_keyword_search_body(
    query: str,
    size: int,
    *,
    record_type: str | None = None,
    table_name: str | None = None,
) -> dict[str, Any]:
    """BM25 keyword search (agentic-agri ``search_by_keyword``)."""
    q = query.strip()
    must_clauses: list[dict[str, Any]] = [
        {
            "multi_match": {
                "query": q,
                "fields": _KEYWORD_FIELDS,
            }
        }
    ]
    if record_type:
        must_clauses.append({"term": {"record_type": record_type.strip().upper()}})
    if table_name:
        must_clauses.append({"term": {"table_name": table_name.strip()}})

    return {
        "size": size,
        "_source": _SOURCE_EXCLUDES,
        "query": {"bool": {"must": must_clauses}},
    }


def build_hybrid_search_body(
    query: str,
    size: int,
    *,
    hybrid_enabled: bool,
    query_vector: list[float] | None = None,
    record_type: str | None = None,
    table_name: str | None = None,
) -> dict[str, Any]:
    """
    Hybrid search: kNN on ``description_vector`` + BM25 (agentic-agri ``hybrid_search``).

    When ``hybrid_enabled`` is false or ``query_vector`` is missing, falls back to keyword.
    """
    if not hybrid_enabled or not query_vector:
        return build_keyword_search_body(
            query, size, record_type=record_type, table_name=table_name
        )

    q = query.strip()
    should_clauses: list[dict[str, Any]] = [
        {
            "knn": {
                "description_vector": {
                    "vector": query_vector,
                    "k": size,
                }
            }
        },
        {
            "multi_match": {
                "query": q,
                "fields": _KEYWORD_FIELDS,
                "boost": 0.3,
            }
        },
    ]
    bool_query: dict[str, Any] = {"should": should_clauses}
    filter_clauses: list[dict[str, Any]] = []
    if record_type:
        filter_clauses.append({"term": {"record_type": record_type.strip().upper()}})
    if table_name:
        filter_clauses.append({"term": {"table_name": table_name.strip()}})
    if filter_clauses:
        bool_query["filter"] = filter_clauses

    return {
        "size": size,
        "_source": _SOURCE_EXCLUDES,
        "query": {"bool": bool_query},
    }


def build_table_lookup_body(table_name: str, size: int) -> dict[str, Any]:
    """TABLE-level metadata (agentic-agri ``get_table_metadata``)."""
    name = table_name.strip()
    return {
        "size": min(size, 10) if size > 10 else size,
        "_source": _SOURCE_EXCLUDES,
        "query": {
            "bool": {
                "must": [
                    {"term": {"record_type": _RECORD_TABLE}},
                    {"term": {"table_name": name}},
                ]
            }
        },
    }


def build_columns_lookup_body(table_name: str, size: int) -> dict[str, Any]:
    """COLUMN records for a table (agentic-agri ``get_table_schema``)."""
    name = table_name.strip()
    return {
        "size": min(size, 100),
        "_source": _SOURCE_EXCLUDES,
        "sort": [{"column_name": {"order": "asc"}}],
        "query": {
            "bool": {
                "must": [
                    {"term": {"record_type": _RECORD_COLUMN}},
                    {"term": {"table_name": name}},
                ]
            }
        },
    }


def build_relationships_body(table_names: list[str], size: int) -> dict[str, Any]:
    """RELATIONSHIP by ``related_tables`` (agentic-agri ``get_relationships``)."""
    names = [n.strip() for n in table_names if n and n.strip()]
    bool_query: dict[str, Any] = {
        "must": [{"term": {"record_type": _RECORD_RELATIONSHIP}}],
    }
    if names:
        bool_query["should"] = [{"terms": {"related_tables": names}}]
        bool_query["minimum_should_match"] = 1

    return {
        "size": size,
        "_source": _SOURCE_EXCLUDES,
        "query": {"bool": bool_query},
    }


def resolve_metadata_hit_to_resource_id(
    session: Session, hit: dict[str, Any]
) -> uuid.UUID | None:
    source = hit.get("_source")
    if not isinstance(source, dict):
        return None
    rt = _record_type(source)
    if rt == _RECORD_RELATIONSHIP:
        return None
    if rt not in (_RECORD_TABLE, _RECORD_COLUMN):
        return None

    db_name = _database_name(source)
    schema_name = _norm(source.get("schema_name"))
    table_name = _norm(source.get("table_name"))
    if not db_name or not schema_name or not table_name:
        return None

    rr = ResourceRepository(session)
    db_id = rr.find_database_resource_id_by_name(db_name)
    if db_id is None:
        return None
    schema_id = rr.find_schema_resource_id(db_id, schema_name)
    if schema_id is None:
        return None
    table_id = rr.find_table_resource_id(schema_id, table_name)
    if table_id is None:
        return None
    if rt == _RECORD_TABLE:
        return table_id

    column_name = _norm(source.get("column_name"))
    if not column_name:
        return None
    return rr.find_column_resource_id(table_id, column_name)


def hit_display_key(hit: dict[str, Any]) -> str | None:
    source = hit.get("_source")
    if not isinstance(source, dict):
        return None
    rt = _record_type(source)
    schema = _norm(source.get("schema_name"))
    table = _norm(source.get("table_name"))
    if rt == _RECORD_TABLE:
        if schema and table:
            return f"{schema}.{table}"
        return table or None
    if rt == _RECORD_COLUMN:
        col = _norm(source.get("column_name"))
        if schema and table and col:
            return f"{schema}.{table}.{col}"
        if table and col:
            return f"{table}.{col}"
        return col or None
    if rt == _RECORD_RELATIONSHIP:
        name = _norm(source.get("relationship_name"))
        if name:
            return name
        related = source.get("related_tables") or []
        if isinstance(related, str):
            related = [related]
        parts = [str(t).strip() for t in related if str(t).strip()]
        if parts:
            return "↔".join(parts[:5])
    return None
