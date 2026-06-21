"""OpenSearch query bodies aligned with agentic-agri OpenSearchClient."""

from __future__ import annotations

from app.query.metadata_dictionary import (
    build_columns_lookup_body,
    build_hybrid_search_body,
    build_keyword_search_body,
    build_relationships_body,
    build_table_lookup_body,
    hit_display_key,
)


def test_keyword_search_uses_agri_fields() -> None:
    body = build_keyword_search_body("loan", 5)
    mm = body["query"]["bool"]["must"][0]["multi_match"]
    assert "business_name^3" in mm["fields"]
    assert "relationship_name^2" in mm["fields"]
    assert body["_source"] == {"excludes": ["description_vector"]}


def test_relationships_query_uses_related_tables() -> None:
    body = build_relationships_body(["GL_ACCOUNT", "GL_ENTRY"], 10)
    bool_q = body["query"]["bool"]
    assert bool_q["must"] == [{"term": {"record_type": "RELATIONSHIP"}}]
    assert bool_q["should"] == [{"terms": {"related_tables": ["GL_ACCOUNT", "GL_ENTRY"]}}]
    assert bool_q["minimum_should_match"] == 1


def test_table_lookup_uses_term_not_keyword_subfield() -> None:
    body = build_table_lookup_body("users", 20)
    must = body["query"]["bool"]["must"]
    assert {"term": {"table_name": "users"}} in must
    assert {"term": {"record_type": "TABLE"}} in must


def test_columns_lookup_has_sort() -> None:
    body = build_columns_lookup_body("users", 50)
    assert body["sort"] == [{"column_name": {"order": "asc"}}]
    assert body["size"] == 50


def test_hybrid_disabled_matches_keyword_shape() -> None:
    kw = build_keyword_search_body("x", 3)
    hy = build_hybrid_search_body("x", 3, hybrid_enabled=False)
    assert kw == hy


def test_hybrid_without_vector_falls_back_to_keyword() -> None:
    hy = build_hybrid_search_body("x", 3, hybrid_enabled=True, query_vector=None)
    kw = build_keyword_search_body("x", 3)
    assert hy == kw


def test_hybrid_enabled_knn_and_bm25() -> None:
    vec = [0.1] * 1024
    body = build_hybrid_search_body(
        "ledger", 5, hybrid_enabled=True, query_vector=vec, record_type="TABLE"
    )
    should = body["query"]["bool"]["should"]
    assert "knn" in should[0]
    assert should[0]["knn"]["description_vector"]["vector"] == vec
    assert "multi_match" in should[1]
    assert body["query"]["bool"]["filter"] == [{"term": {"record_type": "TABLE"}}]


def test_hit_display_key_relationship() -> None:
    hit = {
        "_source": {
            "record_type": "RELATIONSHIP",
            "relationship_name": "a_b",
            "related_tables": ["a", "b"],
        }
    }
    assert hit_display_key(hit) == "a_b"
