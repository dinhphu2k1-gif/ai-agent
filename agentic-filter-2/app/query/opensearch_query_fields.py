"""Collect OpenSearch field names referenced in a query clause (MVP shallow walk)."""

from __future__ import annotations

from typing import Any


def collect_fields_from_query_clause(node: Any, *, depth: int = 0) -> set[str]:
    """Known DSL shapes only; unknown keys are recursed shallowly."""
    if depth > 48:
        return set()
    fields: set[str] = set()
    if isinstance(node, dict):
        for k, v in node.items():
            lk = str(k).lower()
            if lk in ("match", "match_phrase", "term", "prefix", "wildcard", "regexp"):
                if isinstance(v, dict):
                    fields.update(str(f) for f in v.keys())
            elif lk == "range" and isinstance(v, dict):
                fields.update(str(f) for f in v.keys())
            elif lk == "multi_match" and isinstance(v, dict):
                for f in v.get("fields") or []:
                    if isinstance(f, str):
                        fields.add(f.split("^")[0])
            elif lk == "bool" and isinstance(v, dict):
                for sub in ("must", "filter", "should", "must_not"):
                    if sub in v and isinstance(v[sub], list):
                        for item in v[sub]:
                            fields |= collect_fields_from_query_clause(item, depth=depth + 1)
            elif lk == "nested" and isinstance(v, dict) and "query" in v:
                fields |= collect_fields_from_query_clause(v["query"], depth=depth + 1)
            elif lk == "query_string" and isinstance(v, dict):
                # cannot resolve fields reliably
                pass
            else:
                fields |= collect_fields_from_query_clause(v, depth=depth + 1)
    elif isinstance(node, list):
        for item in node:
            fields |= collect_fields_from_query_clause(item, depth=depth + 1)
    return fields


def collect_fields_from_post_filter_clause(node: Any) -> set[str]:
    return collect_fields_from_query_clause(node)
