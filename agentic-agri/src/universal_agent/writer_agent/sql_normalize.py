"""Normalize LLM-generated SQL before execution."""

from __future__ import annotations

import re

from universal_agent.utils import strip_markdown_json

_TRAILING_LIMIT = re.compile(
    r"\s+LIMIT\s+\d+(?:\s+OFFSET\s+\d+)?\s*$",
    re.IGNORECASE,
)
_TRAILING_FETCH_FIRST = re.compile(
    r"\s+FETCH\s+FIRST\s+\d+\s+ROWS\s+ONLY\s*$",
    re.IGNORECASE,
)
_TRAILING_OFFSET = re.compile(
    r"\s+OFFSET\s+\d+\s*$",
    re.IGNORECASE,
)


def clean_llm_sql(sql_text: str) -> str:
    """Strip markdown fences and language hints from model output."""
    normalized = sql_text.strip()
    fenced_match = re.match(
        r"^```[a-zA-Z0-9_-]*\s*\n(?P<body>[\s\S]*?)\n```$",
        normalized,
    )
    if fenced_match:
        normalized = fenced_match.group("body").strip()
    else:
        normalized = strip_markdown_json(normalized).strip()

    normalized = re.sub(
        r"^(sql|postgresql|oracle)\s*\n",
        "",
        normalized,
        flags=re.IGNORECASE,
    )
    return normalized.strip().rstrip(";").strip()


def strip_trailing_limit(sql_text: str) -> str:
    """Remove outer row-limit clause so executor can apply its own LIMIT."""
    normalized = sql_text.strip()
    changed = True
    while changed:
        changed = False
        for pattern in (_TRAILING_LIMIT, _TRAILING_FETCH_FIRST, _TRAILING_OFFSET):
            updated = pattern.sub("", normalized)
            if updated != normalized:
                normalized = updated.strip()
                changed = True
    return normalized.strip()


def prepare_sql_for_filter_service(sql_text: str) -> str:
    """Prepare SQL for filter-service /execute (limit applied via request body)."""
    return strip_trailing_limit(clean_llm_sql(sql_text))
