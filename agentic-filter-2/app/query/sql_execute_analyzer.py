"""SQL parsing for /api/v1/sql/execute (multi-table subset)."""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp


class SqlExecuteUnsupportedQueryError(ValueError):
    """Query outside supported subset for SQL execute MVP."""


def infer_schema_from_table(table_name: str) -> str | None:
    upper = table_name.upper()
    if upper.startswith("GL_"):
        return "GL"
    if upper.startswith("CIF_"):
        return "CIF"
    return None


def resolve_table_schema(table_name: str, explicit_schema: str | None) -> str:
    if explicit_schema and explicit_schema.strip():
        return explicit_schema.strip()
    return infer_schema_from_table(table_name) or "public"


@dataclass(frozen=True)
class ParsedSqlExecute:
    schema_by_table: dict[str, str]
    tables: tuple[str, ...]
    # Simple SELECT list items only (output_key, table_name, column_name).
    projections: tuple[tuple[str, str, str], ...]
    # Base-table columns referenced anywhere (JOIN/WHERE/GROUP BY/subqueries) for PDP.
    referenced_columns: tuple[tuple[str, str], ...]  # (table_name, column_name)
    original_sql: str


def _register_table(
    node: exp.Table,
    tables: list[str],
    alias_to_table: dict[str, str],
) -> None:
    name = (node.name or "").strip()
    if not name:
        return
    up = name.upper()
    alias_to_table[up] = up
    if node.alias:
        alias_to_table[str(node.alias).strip().upper()] = up
    if up not in tables:
        tables.append(up)


def _tables_in_from(select: exp.Select) -> tuple[list[str], dict[str, str]]:
    """Tables from this SELECT's FROM + JOINs (not inside derived subqueries)."""
    tables: list[str] = []
    alias_to_table: dict[str, str] = {}
    from_ = select.args.get("from_") or select.find(exp.From)
    if from_:
        for node in from_.walk(prune=lambda n, *_: isinstance(n, exp.Subquery)):
            if isinstance(node, exp.Table):
                _register_table(node, tables, alias_to_table)
    # sqlglot puts JOIN targets in select.args["joins"], not under From.
    for join in select.args.get("joins") or []:
        if join is None:
            continue
        for node in join.walk(prune=lambda n, *_: isinstance(n, exp.Subquery)):
            if isinstance(node, exp.Table):
                _register_table(node, tables, alias_to_table)
    return tables, alias_to_table


def _collect_columns_for_select(select: exp.Select) -> tuple[tuple[str, str], ...]:
    tables, alias_to_table = _tables_in_from(select)
    if not tables:
        return ()
    base_tables = frozenset(tables)
    default_table = tables[0] if len(tables) == 1 else None
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for col in select.walk(
        prune=lambda n, *_: isinstance(n, (exp.Subquery, exp.Order))
    ):
        if not isinstance(col, exp.Column):
            continue
        cname = (col.name or "").strip().upper()
        if not cname:
            continue
        tbl_raw = (col.table or "").strip().upper()
        if tbl_raw:
            tbl_u = alias_to_table.get(tbl_raw, tbl_raw)
        elif default_table:
            tbl_u = default_table
        else:
            continue
        if tbl_u not in base_tables:
            continue
        key = (tbl_u, cname)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return tuple(out)


def _collect_referenced_columns(ast: exp.Expression) -> tuple[tuple[str, str], ...]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    selects: list[exp.Select] = []
    if isinstance(ast, exp.Select):
        selects.append(ast)
    for subq in ast.find_all(exp.Subquery):
        if isinstance(subq.this, exp.Select):
            selects.append(subq.this)
    for sel in selects:
        for ref in _collect_columns_for_select(sel):
            if ref not in seen:
                seen.add(ref)
                out.append(ref)
    return tuple(out)


def parse_sql_execute_select(sql: str) -> ParsedSqlExecute:
    raw = sql.strip()
    if not raw:
        raise SqlExecuteUnsupportedQueryError("empty query")
    inner = raw.rstrip(";").strip()
    if ";" in inner:
        raise SqlExecuteUnsupportedQueryError("multi-statement not allowed")

    try:
        ast = sqlglot.parse_one(raw, read="postgres")
    except Exception as e:
        raise SqlExecuteUnsupportedQueryError(f"parse error: {e}") from e

    if isinstance(ast, exp.Union):
        raise SqlExecuteUnsupportedQueryError("UNION not supported")
    if not isinstance(ast, exp.Select):
        raise SqlExecuteUnsupportedQueryError("only SELECT is supported")
    if ast.find(exp.With):
        raise SqlExecuteUnsupportedQueryError("WITH/CTE not supported")

    tables: list[str] = []
    schema_by_table: dict[str, str] = {}
    alias_to_table: dict[str, str] = {}
    for t in ast.find_all(exp.Table):
        name = (t.name or "").strip()
        if not name:
            continue
        up = name.upper()
        schema_raw = (t.db or "").strip() or None
        schema = resolve_table_schema(up, schema_raw)
        alias_to_table[up] = up
        if t.alias:
            alias_to_table[str(t.alias).strip().upper()] = up
        if up not in schema_by_table:
            schema_by_table[up] = schema
            tables.append(up)

    if not tables:
        raise SqlExecuteUnsupportedQueryError("FROM clause required")

    multi_table = len(tables) > 1

    # SELECT list: allow aggregates/expressions; track simple columns for masking.
    projections: list[tuple[str, str, str]] = []
    for e in ast.expressions:
        if isinstance(e, exp.Star):
            raise SqlExecuteUnsupportedQueryError("SELECT * not supported")
        out_key: str | None = None
        inner_expr = e
        if isinstance(e, exp.Alias):
            out_key = (e.alias or "").strip()
            inner_expr = e.this
        if not isinstance(inner_expr, exp.Column):
            continue
        col = (inner_expr.name or "").strip()
        tbl = (inner_expr.table or "").strip()
        if not col:
            raise SqlExecuteUnsupportedQueryError("invalid column reference")
        if multi_table and not tbl:
            raise SqlExecuteUnsupportedQueryError(
                "table-qualified columns required when multiple tables are used"
            )
        tbl_u = alias_to_table.get(tbl.upper(), tbl.upper()) if tbl else tables[0]
        key = out_key or col
        projections.append((key, tbl_u, col.upper()))

    if not ast.expressions:
        raise SqlExecuteUnsupportedQueryError("no columns in projection")

    referenced_columns = _collect_referenced_columns(ast)

    return ParsedSqlExecute(
        schema_by_table=schema_by_table,
        tables=tuple(tables),
        projections=tuple(projections),
        referenced_columns=referenced_columns,
        original_sql=raw,
    )

