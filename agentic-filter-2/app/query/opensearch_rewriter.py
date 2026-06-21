"""Merge policy row filters into OpenSearch DSL without client override (Epic 7)."""

from __future__ import annotations

import copy
from typing import Any


def _forbidden_query_subtree(node: Any, *, depth: int = 0) -> bool:
    if depth > 32:
        return True
    if isinstance(node, dict):
        for k in node:
            lk = str(k).lower()
            if lk in ("script", "scripts", "painless", "stored"):
                return True
            if _forbidden_query_subtree(node[k], depth=depth + 1):
                return True
    elif isinstance(node, list):
        for item in node:
            if _forbidden_query_subtree(item, depth=depth + 1):
                return True
    return False


def merge_policy_filters_into_clause(
    query_clause: dict[str, Any], policy_filters: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Append ``policy_filters`` to ``bool.filter`` (AND semantics). If ``query`` is not bool,
    wrap as ``bool.must`` + ``bool.filter`` so policy cannot be overridden by client ``must``.
    """
    if not policy_filters:
        return copy.deepcopy(query_clause)
    root = copy.deepcopy(query_clause)
    if "bool" in root and isinstance(root["bool"], dict):
        b = root["bool"]
        fl = b.get("filter")
        if fl is None:
            b["filter"] = list(policy_filters)
        elif isinstance(fl, list):
            b["filter"] = list(fl) + list(policy_filters)
        else:
            b["filter"] = [fl, *policy_filters]
        return root
    return {"bool": {"must": [root], "filter": list(policy_filters)}}


def build_search_body(
    *,
    query_clause: dict[str, Any],
    policy_filters: list[dict[str, Any]],
    post_filter_clause: dict[str, Any] | None,
    source: Any | None,
    size: int | None,
    from_: int | None,
    sort: Any | None,
) -> dict[str, Any]:
    if _forbidden_query_subtree(query_clause):
        msg = "Query contains unsupported script-related constructs in MVP"
        raise ValueError(msg)
    merged_query = merge_policy_filters_into_clause(query_clause, policy_filters)
    body: dict[str, Any] = {"query": merged_query}
    if post_filter_clause is not None:
        body["post_filter"] = merge_policy_filters_into_clause(
            post_filter_clause, policy_filters
        )
    if source is not None:
        body["_source"] = source
    if size is not None:
        body["size"] = size
    if from_ is not None:
        body["from"] = from_
    if sort is not None:
        body["sort"] = sort
    return body
