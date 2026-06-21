"""
Build queryScope payload for filter-service SQL execution from metadata retrieval output.
"""

from __future__ import annotations

from typing import Any

from .sql_normalize import clean_llm_sql


def _parse_table_line(line: str) -> str | None:
    if not line.startswith("[TABLE] "):
        return None
    payload = line[len("[TABLE] ") :].strip()
    if not payload:
        return None
    # "[TABLE] CIF_CUSTOMERS — Customers"
    name = payload.split("—", 1)[0].strip().split()[0].upper()
    return name or None


def _parse_column_line(line: str) -> tuple[str, str] | None:
    if not line.startswith("[COLUMN] "):
        return None
    payload = line[len("[COLUMN] ") :].strip()
    if "." not in payload:
        return None
    table_part, column_part = payload.split(".", 1)
    table = table_part.strip().upper()
    column = column_part.split()[0].strip().lower()
    if not table or not column:
        return None
    return table, column


def _tables_from_raw_results(raw_results: str) -> list[str]:
    seen: set[str] = set()
    tables: list[str] = []
    for line in (raw_results or "").splitlines():
        name = _parse_table_line(line.strip())
        if name and name not in seen:
            seen.add(name)
            tables.append(name)
    for line in (raw_results or "").splitlines():
        parsed = _parse_column_line(line.strip())
        if not parsed:
            continue
        name = parsed[0]
        if name not in seen:
            seen.add(name)
            tables.append(name)
    return tables


def _catalog_from_metadata(
    *,
    raw_hits: list[dict[str, Any]] | None = None,
    raw_results: str | None = None,
    scope_tables: list[dict[str, Any]] | None = None,
) -> list[str]:
    seen: set[str] = set()
    catalog: list[str] = []

    def _add(name: str) -> None:
        normalized = str(name).upper().strip()
        if not normalized or normalized == "_RELATIONSHIP" or normalized in seen:
            return
        seen.add(normalized)
        catalog.append(normalized)

    if scope_tables:
        for entry in scope_tables:
            if isinstance(entry, dict) and entry.get("name"):
                _add(str(entry["name"]))

    if raw_hits:
        for hit in raw_hits:
            src = hit.get("_source") or hit.get("source") or {}
            if isinstance(src, dict) and src.get("table_name"):
                _add(str(src["table_name"]))

    for name in _tables_from_raw_results(raw_results or ""):
        _add(name)

    return sorted(catalog, key=len, reverse=True)


def _tables_mentioned_in_text(text: str, known_tables: list[str]) -> list[str]:
    """Return known catalog tables that appear as whole identifiers in text."""
    if not text or not known_tables:
        return []

    upper_text = text.upper()
    seen: set[str] = set()
    found: list[str] = []
    for name in known_tables:
        normalized = name.upper()
        if normalized in seen:
            continue
        if _text_contains_identifier(upper_text, normalized):
            seen.add(normalized)
            found.append(normalized)
    return found


def _text_contains_identifier(text: str, identifier: str) -> bool:
    if not identifier:
        return False
    start = 0
    id_len = len(identifier)
    while start < len(text):
        pos = text.find(identifier, start)
        if pos == -1:
            return False
        if _is_identifier_boundary(text, pos, id_len):
            return True
        start = pos + 1
    return False


def _is_identifier_boundary(text: str, start: int, length: int) -> bool:
    if start > 0:
        prev = text[start - 1]
        if prev.isalnum() or prev == "_":
            return False
    end = start + length
    if end < len(text):
        nxt = text[end]
        if nxt.isalnum() or nxt == "_":
            return False
    return True


def _infer_schema_from_table(table_name: str) -> str | None:
    upper = table_name.upper()
    if upper.startswith("GL_"):
        return "GL"
    if upper.startswith("CIF_"):
        return "CIF"
    return None


def _schemas_from_hits(hits: list[dict[str, Any]]) -> dict[str, str]:
    by_table: dict[str, str] = {}
    for hit in hits:
        src = hit.get("_source") or hit.get("source") or {}
        if not isinstance(src, dict):
            continue
        table = str(src.get("table_name", "")).upper().strip()
        schema = str(src.get("schema_name", "")).strip()
        if table and schema and table not in by_table:
            by_table[table] = schema
    return by_table


def _resolve_table_schema(
    table_name: str,
    schemas_by_table: dict[str, str],
    *,
    default_schema: str | None = None,
) -> str | None:
    normalized = table_name.upper()
    return (
        schemas_by_table.get(normalized)
        or _infer_schema_from_table(normalized)
        or default_schema
    )


def _columns_from_raw_results(raw_results: str) -> dict[str, list[str]]:
    by_table: dict[str, list[str]] = {}
    for line in (raw_results or "").splitlines():
        parsed = _parse_column_line(line.strip())
        if not parsed:
            continue
        table, column = parsed
        cols = by_table.setdefault(table, [])
        if column not in cols:
            cols.append(column)
    return by_table


def _columns_from_hits(hits: list[dict[str, Any]]) -> dict[str, list[str]]:
    by_table: dict[str, list[str]] = {}
    for hit in hits:
        src = hit.get("_source") or hit.get("source") or {}
        if not isinstance(src, dict):
            continue
        if src.get("record_type") != "COLUMN":
            continue
        table = str(src.get("table_name", "")).upper()
        column = str(src.get("column_name", "")).lower()
        if not table or not column:
            continue
        cols = by_table.setdefault(table, [])
        if column not in cols:
            cols.append(column)
    return by_table


def build_query_scope(
    table_names: list[str],
    *,
    raw_hits: list[dict[str, Any]] | None = None,
    raw_results: str | None = None,
    default_schema: str | None = None,
    source: str = "metadata_agent",
) -> dict[str, Any]:
    """
    Map metadata retriever output to filter-service queryScope.

    Table names come from expanded_tables / list_tables and structured metadata
    lines ([TABLE], [COLUMN]). Schema comes from metadata hits or table prefix.
    """
    columns_by_table: dict[str, list[str]] = {}
    schemas_by_table: dict[str, str] = {}
    if raw_hits:
        columns_by_table = _columns_from_hits(raw_hits)
        schemas_by_table = _schemas_from_hits(raw_hits)
    elif raw_results:
        columns_by_table = _columns_from_raw_results(raw_results)

    resolved_names = list(table_names)
    if not resolved_names and raw_results:
        resolved_names = _tables_from_raw_results(raw_results)
    if not resolved_names and columns_by_table:
        resolved_names = list(columns_by_table.keys())

    seen: set[str] = set()
    tables: list[dict[str, Any]] = []
    for name in resolved_names:
        normalized = str(name).upper().strip()
        if not normalized or normalized == "_RELATIONSHIP" or normalized in seen:
            continue
        seen.add(normalized)
        entry: dict[str, Any] = {"name": normalized}
        schema = _resolve_table_schema(
            normalized, schemas_by_table, default_schema=default_schema
        )
        if schema:
            entry["schema"] = schema
        cols = columns_by_table.get(normalized)
        if cols:
            entry["columns"] = cols
        tables.append(entry)

    return {"source": source, "tables": tables}


def resolve_query_scope(
    query_scope: dict[str, Any] | None,
    *,
    metadata_context: str | None = None,
    raw_results: str | None = None,
    raw_hits: list[dict[str, Any]] | None = None,
    default_schema: str | None = None,
) -> dict[str, Any] | None:
    """Return queryScope with non-empty tables, rebuilding from metadata when needed."""
    if query_scope and query_scope.get("tables"):
        return _ensure_table_schemas(query_scope, default_schema=default_schema)

    raw = raw_results or ""
    if not raw and metadata_context and ("[TABLE]" in metadata_context or "[COLUMN]" in metadata_context):
        raw = metadata_context

    if raw or raw_hits:
        rebuilt = build_query_scope(
            [],
            raw_results=raw or None,
            raw_hits=raw_hits,
            default_schema=default_schema,
        )
        if rebuilt.get("tables"):
            return rebuilt

    catalog = _catalog_from_metadata(raw_hits=raw_hits, raw_results=raw)
    if metadata_context and catalog:
        names = _tables_mentioned_in_text(metadata_context, catalog)
        if names:
            rebuilt = build_query_scope(names, default_schema=default_schema)
            if rebuilt.get("tables"):
                return rebuilt

    return query_scope


def extract_tables_from_sql(sql_text: str, known_tables: list[str]) -> list[str]:
    """
    Return catalog tables referenced in SQL (whole-identifier match only).

    Uses the metadata table whitelist so column names like CIF_NUMBER are never
    mistaken for tables.
    """
    if not known_tables:
        return []

    sql_upper = clean_llm_sql(sql_text).upper()
    catalog = sorted({name.upper() for name in known_tables}, key=len, reverse=True)
    seen: set[str] = set()
    found: list[str] = []
    for name in catalog:
        if name in seen:
            continue
        if _text_contains_identifier(sql_upper, name):
            seen.add(name)
            found.append(name)
    return found


def narrow_query_scope_to_sql(
    query_scope: dict[str, Any] | None,
    sql_text: str,
) -> dict[str, Any] | None:
    """
    Restrict queryScope to tables actually referenced in the SQL.

    Metadata retrieval often expands many related tables via Neo4j; filter-service
    checks permissions on every table listed in queryScope, not only parsed SQL refs.
    """
    if not query_scope or not query_scope.get("tables"):
        return query_scope

    scope_tables = [
        entry
        for entry in query_scope["tables"]
        if isinstance(entry, dict) and entry.get("name")
    ]
    catalog = [str(entry["name"]).upper() for entry in scope_tables]
    referenced = extract_tables_from_sql(sql_text, catalog)
    if not referenced:
        return query_scope

    scope_by_name = {str(entry["name"]).upper(): entry for entry in scope_tables}
    referenced_set = set(referenced)

    narrowed: list[dict[str, Any]] = []
    for name in catalog:
        if name not in referenced_set:
            continue
        narrowed.append(dict(scope_by_name[name]))

    if not narrowed:
        return query_scope

    return {
        **query_scope,
        "source": "sql_parser",
        "tables": narrowed,
    }


def _ensure_table_schemas(
    query_scope: dict[str, Any],
    *,
    default_schema: str | None = None,
) -> dict[str, Any]:
    """Fill or correct schema on tables already present (e.g. stale public default)."""
    tables = query_scope.get("tables") or []
    if not tables:
        return query_scope

    updated: list[dict[str, Any]] = []
    changed = False
    for table in tables:
        if not isinstance(table, dict):
            updated.append(table)
            continue
        entry = dict(table)
        name = str(entry.get("name", "")).upper()
        current = str(entry.get("schema", "")).strip()
        inferred = _resolve_table_schema(name, {}, default_schema=default_schema)
        if inferred and (not current or current == "public"):
            if entry.get("schema") != inferred:
                entry["schema"] = inferred
                changed = True
        updated.append(entry)

    if not changed:
        return query_scope
    return {**query_scope, "tables": updated}
