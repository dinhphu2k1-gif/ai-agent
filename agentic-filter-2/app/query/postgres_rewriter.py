from __future__ import annotations

import sqlglot
from sqlglot import exp


def inject_row_filter_predicate(sql: str, combined_predicate: str) -> str:
    """Append trusted admin predicate with AND, or add WHERE (§11.1)."""
    ast = sqlglot.parse_one(sql, read="postgres")
    dummy = sqlglot.parse_one(
        f"SELECT 1 WHERE ({combined_predicate})", read="postgres"
    )
    extra = dummy.find(exp.Where)
    if extra is None:
        raise ValueError("invalid predicate")
    extra_cond = extra.this
    current = ast.args.get("where")
    if current:
        merged = exp.And(this=current.this, expression=extra_cond)
        ast.set("where", exp.Where(this=merged))
    else:
        ast.set("where", exp.Where(this=extra_cond))
    return ast.sql(dialect="postgres")
