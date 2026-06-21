"""SQL parsing for runtime filter (Epic 6 MVP subset)."""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp


class UnsupportedQueryError(ValueError):
    """Query outside MVP subset (maps to HTTP 422)."""


@dataclass(frozen=True)
class ParsedSelect:
    """Single-table SELECT with explicit column list."""

    schema_name: str
    table_name: str
    columns: tuple[str, ...]
    original_sql: str


def parse_select_query(sql: str) -> ParsedSelect:
    """MVP: one SELECT, one physical table, no JOIN/CTE/subquery/GROUP BY, no SELECT *."""
    raw = sql.strip()
    if not raw:
        raise UnsupportedQueryError("empty query")
    inner = raw.rstrip(";").strip()
    if ";" in inner:
        raise UnsupportedQueryError("multi-statement not allowed")

    try:
        ast = sqlglot.parse_one(raw, read="postgres")
    except Exception as e:
        raise UnsupportedQueryError(f"parse error: {e}") from e

    if isinstance(ast, exp.Union):
        raise UnsupportedQueryError("UNION not supported")
    if not isinstance(ast, exp.Select):
        raise UnsupportedQueryError("only SELECT is supported")
    if ast.find(exp.With):
        raise UnsupportedQueryError("WITH/CTE not supported")
    if ast.find(exp.Subquery):
        raise UnsupportedQueryError("subqueries not supported")
    if ast.find(exp.Join):
        raise UnsupportedQueryError("JOIN not supported")
    if ast.find(exp.Group):
        raise UnsupportedQueryError("GROUP BY not supported")

    from_expr = ast.args.get("from_")
    if not from_expr or not isinstance(from_expr, exp.From):
        raise UnsupportedQueryError("FROM clause required")
    this = from_expr.this
    if not isinstance(this, exp.Table):
        raise UnsupportedQueryError("single base table required")
    schema = this.db or "public"
    table = this.name
    if not table:
        raise UnsupportedQueryError("invalid table reference")

    cols: list[str] = []
    for e in ast.expressions:
        if isinstance(e, exp.Star):
            raise UnsupportedQueryError("SELECT * not supported in MVP")
        inner_expr = e.this if isinstance(e, exp.Alias) else e
        if isinstance(inner_expr, exp.Column):
            cols.append(inner_expr.name)
        else:
            raise UnsupportedQueryError("only simple column projections are supported")

    if not cols:
        raise UnsupportedQueryError("no columns in projection")

    return ParsedSelect(
        schema_name=str(schema),
        table_name=str(table),
        columns=tuple(cols),
        original_sql=raw,
    )
