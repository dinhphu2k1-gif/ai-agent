"""Convert simple SQL-like row filter strings to OpenSearch bool.filter clauses (MVP)."""

from __future__ import annotations

import re
from typing import Any


class UnsupportedRowFilterExprError(ValueError):
    pass


_AND_SPLIT = re.compile(r"\s+AND\s+", re.IGNORECASE)
_EQ = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$")


def _parse_literal(raw: str) -> Any:
    s = raw.strip()
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    return s


def row_filter_expr_to_term_clauses(expr: str) -> list[dict[str, Any]]:
    """
    Each segment: ``col = value`` (optional parens). Combined ``a = 1 AND b = 2`` supported.
    """
    e = expr.strip()
    if not e:
        return []
    parts = _AND_SPLIT.split(e)
    out: list[dict[str, Any]] = []
    for part in parts:
        p = part.strip()
        while p.startswith("(") and p.endswith(")"):
            p = p[1:-1].strip()
        m = _EQ.match(p)
        if not m:
            raise UnsupportedRowFilterExprError(part)
        field, rhs = m.group(1), m.group(2)
        value = _parse_literal(rhs)
        out.append({"term": {field: value}})
    return out


def row_filter_exprs_to_term_clauses(exprs: list[str]) -> list[dict[str, Any]]:
    clauses: list[dict[str, Any]] = []
    for ex in exprs:
        if not ex or not ex.strip():
            continue
        clauses.extend(row_filter_expr_to_term_clauses(ex))
    return clauses
