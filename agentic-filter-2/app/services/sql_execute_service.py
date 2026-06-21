"""SQL execution API for writer agent (row filter + column masking + scope enforcement)."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError

from app.cache.redis_client import UserContextCache
from app.connectors.postgres import PostgresSqlExecutor
from app.core.config import Settings
from app.query.postgres_rewriter import inject_row_filter_predicate
from app.query.sql_execute_analyzer import (
    SqlExecuteUnsupportedQueryError,
    parse_sql_execute_select,
    resolve_table_schema,
)
from app.repositories.resource_repo import ResourceRepository
from app.schemas.sql_contract import (
    SqlExecuteDataOut,
    SqlExecuteRequest,
    SqlExecuteResponse,
    SqlFilteredOut,
    SqlScopeMatchOut,
    SqlWarningOut,
)
from app.services.authorization_service import (
    resolve_access,
    resolve_column_masks_for_resource,
)
from app.services.masking_service import apply_column_masks_to_rows, jsonable_cell
from app.services.permission_resolver import (
    ColumnMaskPolicy,
    DecisionType,
    PolicyDecision,
)
from app.services.row_filter_service import combine_row_filters
from app.services.user_context_service import UserContext

logger = logging.getLogger(__name__)


def _first_column_mask(
    dec_col: PolicyDecision, dec_tbl: PolicyDecision
) -> ColumnMaskPolicy | None:
    """Column-level mask wins; otherwise inherit table-level mask from PDP ancestors."""
    if dec_col.column_masks:
        return dec_col.column_masks[0]
    if dec_tbl.column_masks:
        return dec_tbl.column_masks[0]
    return None


class SqlExecuteHttpError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        sql_state: str | None = None,
        dialect: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.sql_state = sql_state
        self.dialect = dialect


_FENCE_RE = re.compile(r"^```[a-zA-Z0-9_-]*\s*\n(?P<body>[\s\S]*?)\n```$")
_LEADING_DIALECT_RE = re.compile(r"^(sql|postgresql|oracle)\s*\n", re.IGNORECASE)


def normalize_select_sql(sql_text: str, *, limit: int, limit_cap: int = 1000) -> str:
    raw = (sql_text or "").strip()
    if not raw:
        raise SqlExecuteHttpError(400, "VALIDATION_ERROR", "sql is required")

    m = _FENCE_RE.match(raw)
    normalized = m.group("body").strip() if m else raw
    normalized = _LEADING_DIALECT_RE.sub("", normalized).strip()
    normalized = normalized.rstrip(";").strip()
    if ";" in normalized:
        raise SqlExecuteHttpError(400, "VALIDATION_ERROR", "Chỉ cho phép một câu SQL duy nhất.")
    if not re.match(r"^SELECT\b", normalized, re.IGNORECASE):
        raise SqlExecuteHttpError(400, "VALIDATION_ERROR", "Chỉ cho phép truy vấn SELECT trong giai đoạn này.")

    # Cap limit.
    lim = min(int(limit), int(limit_cap))
    if not re.search(r"\bLIMIT\b", normalized, re.IGNORECASE):
        normalized = f"{normalized}\nLIMIT {lim}"
    return normalized


def run_sql_execute(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    settings: Settings,
    body: SqlExecuteRequest,
    executor: PostgresSqlExecutor,
) -> SqlExecuteResponse:
    # 1) normalize
    sql_norm = normalize_select_sql(body.sql, limit=body.limit, limit_cap=1000)

    # 2) parse subset
    try:
        parsed = parse_sql_execute_select(sql_norm)
    except SqlExecuteUnsupportedQueryError as e:
        raise SqlExecuteHttpError(400, "VALIDATION_ERROR", str(e)) from e

    # 3) declared scope
    declared_tables = []
    declared_set: set[tuple[str, str]] = set()
    for t in body.query_scope.tables:
        nm = t.name.strip().upper()
        sch = resolve_table_schema(nm, t.schema_name)
        declared_tables.append(nm)
        declared_set.add((sch, nm))

    # 4) strict scope match for parsed tables
    parsed_tables = list(parsed.tables)
    undeclared = []
    if body.options.strict_scope_match:
        for t in parsed_tables:
            sch = resolve_table_schema(t, parsed.schema_by_table.get(t))
            if (sch, t) not in declared_set:
                undeclared.append(t)
        if undeclared:
            raise SqlExecuteHttpError(
                403,
                "POLICY_VIOLATION",
                f"SQL references table(s) not declared in queryScope: {', '.join(undeclared)}",
                details={
                    "declaredTables": declared_tables,
                    "parsedTables": parsed_tables,
                    "undeclaredTables": undeclared,
                },
            )

    # 5) resolve catalog ids for declared scope (fail-fast select)
    rr = ResourceRepository(session)
    db_name = settings.sql_catalog_database_name
    db_id = rr.find_database_resource_id_by_name(db_name)
    if db_id is None:
        raise SqlExecuteHttpError(
            422,
            "VALIDATION_ERROR",
            f"Unknown database '{db_name}' in resource catalog",
        )

    ttl = settings.permission_snapshot_ttl_seconds

    def _resolve(rid: uuid.UUID):
        return resolve_access(session, user_ctx, rid, "SELECT", cache, ttl)

    table_id_by_name: dict[tuple[str, str], uuid.UUID] = {}
    checked_tables: list[str] = []
    for t in body.query_scope.tables:
        nm = t.name.strip().upper()
        sch = resolve_table_schema(nm, t.schema_name)
        sch_id = rr.find_schema_resource_id(db_id, sch)
        if sch_id is None:
            raise SqlExecuteHttpError(
                422,
                "VALIDATION_ERROR",
                f"Unknown schema '{sch}' in resource catalog",
            )
        tbl_id = rr.find_table_resource_id(sch_id, nm)
        if tbl_id is None:
            raise SqlExecuteHttpError(
                422,
                "VALIDATION_ERROR",
                f"Unknown table '{nm}' in resource catalog",
            )
        checked_tables.append(nm)
        table_id_by_name[(sch, nm)] = tbl_id

        dec = _resolve(tbl_id)
        if dec.decision == DecisionType.DENY:
            raise SqlExecuteHttpError(403, "FORBIDDEN", f"SELECT denied on table {nm}")

    table_decision_cache: dict[uuid.UUID, PolicyDecision] = {}

    def _table_decision(tid: uuid.UUID) -> PolicyDecision:
        if tid not in table_decision_cache:
            table_decision_cache[tid] = _resolve(tid)
        return table_decision_cache[tid]

    # 6) resolve parsed projection columns → enforce + collect policies
    row_exprs: list[str] = []
    checked_columns: list[str] = []
    masks_by_column: dict[str | tuple[str, str], ColumnMaskPolicy] = {}
    for tbl_name, col_name in parsed.referenced_columns:
        sch = resolve_table_schema(tbl_name, parsed.schema_by_table.get(tbl_name))
        tbl_id = table_id_by_name.get((sch, tbl_name))
        if tbl_id is None:
            # If strictScopeMatch=false, this would happen; still deny for safety.
            raise SqlExecuteHttpError(
                403,
                "POLICY_VIOLATION",
                f"SQL references table {tbl_name} not declared in queryScope",
            )
        cid = rr.find_column_resource_id(tbl_id, col_name)
        if cid is None:
            raise SqlExecuteHttpError(
                400,
                "VALIDATION_ERROR",
                f"Unknown column '{tbl_name}.{col_name}' in resource catalog",
            )
        col_row = rr.get_column(cid)
        catalog_col_name = col_row.name if col_row is not None else col_name
        checked_columns.append(f"{tbl_name}.{catalog_col_name}")
        dec_col = _resolve(cid)
        dec_tbl = _table_decision(tbl_id)
        if dec_col.decision == DecisionType.DENY:
            raise SqlExecuteHttpError(
                403, "FORBIDDEN", f"SELECT denied on column {tbl_name}.{col_name}"
            )
        row_exprs.extend(dec_col.row_filter_exprs)
        if body.options.apply_column_masking:
            runtime_masks = resolve_column_masks_for_resource(
                session, user_ctx, cid, cache, ttl
            )
            mask_pol = (
                runtime_masks[0]
                if runtime_masks
                else _first_column_mask(dec_col, dec_tbl)
            )
            if mask_pol is not None:
                # Qualified key for multi-table JOIN; bare name for result-key mapping.
                masks_by_column[(tbl_name, col_name)] = mask_pol
                masks_by_column[col_name] = mask_pol
                if catalog_col_name.upper() != col_name.upper():
                    masks_by_column[catalog_col_name] = mask_pol

    for tid in table_id_by_name.values():
        row_exprs.extend(_table_decision(tid).row_filter_exprs)

    combined = combine_row_filters([e for e in row_exprs if e and e.strip()])
    sql_to_run = parsed.original_sql
    applied_row_filters: list[str] = []
    if body.options.apply_row_filter and combined:
        sql_to_run = inject_row_filter_predicate(sql_to_run, combined)
        applied_row_filters.append(combined)

    # 7) execute
    try:
        keys, rows = executor.execute_select(sql_to_run, {})
    except DBAPIError as e:
        sql_state = getattr(e.orig, "pgcode", None)
        # Per contract: runtime execution errors are 200 + success:false.
        return SqlExecuteResponse(
            success=False,
            error={
                "code": "EXECUTION_ERROR",
                "message": str(e).strip(),
                "sqlState": sql_state,
                "dialect": body.dialect,
            },
        )
    except Exception as e:
        raise SqlExecuteHttpError(
            502, "UPSTREAM_ERROR", f"Data source error: {type(e).__name__}"
        ) from e

    # 8) mask post-process (logical column → actual result key from executor)
    masked_cols: list[str] = []
    rows_mut = [dict(r) for r in rows]
    if body.options.apply_column_masking and masks_by_column and rows_mut:
        logical_columns = tuple(col for _, _, col in parsed.projections)
        projection_output_keys = tuple(out for out, _, _ in parsed.projections)
        apply_column_masks_to_rows(
            rows_mut,
            list(keys),
            logical_columns,
            masks_by_column,
            hash_salt=settings.masking_hash_salt,
            projection_output_keys=projection_output_keys,
            projections=parsed.projections,
        )
        masked_cols = list(dict.fromkeys(logical_columns))

    # 9) convert rows → list[list[Any]] preserving column order (JSON-safe cells)
    out_rows = [[jsonable_cell(row.get(k)) for k in keys] for row in rows_mut]

    warnings: list[SqlWarningOut] = []
    for c in masked_cols:
        warnings.append(
            SqlWarningOut(
                code="COLUMN_MASKED",
                message="Column masked per policy",
                resource=c,
            )
        )

    scope_match = SqlScopeMatchOut(
        declaredTables=declared_tables,
        parsedTables=parsed_tables,
        undeclaredTables=undeclared,
        strictScopeMatch=body.options.strict_scope_match,
    )

    filtered = SqlFilteredOut(
        checkedTables=checked_tables,
        checkedColumns=checked_columns,
        maskedColumns=masked_cols,
        appliedRowFilters=applied_row_filters,
        scopeMatch=scope_match,
    )

    return SqlExecuteResponse(
        success=True,
        data=SqlExecuteDataOut(
            executedSql=sql_to_run,
            columns=list(keys),
            rows=out_rows,
            rowCount=len(out_rows),
            truncated=len(out_rows) >= body.limit,
            filtered=filtered,
            warnings=warnings,
        ),
    )

