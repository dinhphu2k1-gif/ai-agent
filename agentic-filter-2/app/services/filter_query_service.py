from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.cache.redis_client import UserContextCache
from app.connectors.postgres import PostgresSqlExecutor
from app.core.config import Settings
from app.core.errors import ErrorCode
from app.query.analyzer import UnsupportedQueryError, parse_select_query
from app.query.postgres_rewriter import inject_row_filter_predicate
from app.repositories.resource_repo import ResourceRepository
from app.schemas.runtime import FilterQueryRequest, FilterQueryResponse, QueryPolicyOut
from app.services.audit_service import (
    record_runtime_access,
    record_runtime_access_for_http_error,
)
from app.services.authorization_service import (
    resolve_access,
    resolve_column_masks_for_resource,
)
from app.services.masking_service import apply_column_masks_to_rows, jsonable_row
from app.services.permission_resolver import ColumnMaskPolicy, DecisionType
from app.services.row_filter_service import combine_row_filters
from app.services.user_context_service import UserContext


class FilterQueryHttpError(Exception):
    def __init__(self, status_code: int, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def _dedupe_filters(exprs: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for e in exprs:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def run_filter_query(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    settings: Settings,
    body: FilterQueryRequest,
    executor: PostgresSqlExecutor,
    *,
    request_id: str | None = None,
) -> FilterQueryResponse:
    audit_action = "POSTGRES_FILTER_QUERY"
    resource_id_for_audit: uuid.UUID | None = None
    try:
        if body.backend != "postgres":
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                "Only backend=postgres is supported in this MVP",
            )
        if body.parameters:
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                "Non-empty parameters are not supported in this MVP",
            )

        try:
            parsed = parse_select_query(body.query)
        except UnsupportedQueryError as e:
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                str(e),
            ) from e

        rr = ResourceRepository(session)
        db_id = rr.find_database_resource_id_by_name(body.database)
        if db_id is None:
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                f"Unknown database '{body.database}' in resource catalog",
            )
        sch_id = rr.find_schema_resource_id(db_id, parsed.schema_name)
        if sch_id is None:
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                f"Unknown schema '{parsed.schema_name}'",
            )
        tbl_id = rr.find_table_resource_id(sch_id, parsed.table_name)
        if tbl_id is None:
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                f"Unknown table '{parsed.table_name}'",
            )
        resource_id_for_audit = tbl_id

        col_ids: dict[str, uuid.UUID] = {}
        for c in parsed.columns:
            cid = rr.find_column_resource_id(tbl_id, c)
            if cid is None:
                raise FilterQueryHttpError(
                    422,
                    ErrorCode.UNSUPPORTED_QUERY,
                    f"Unknown column '{c}'",
                )
            col_ids[c] = cid

        ttl = settings.permission_snapshot_ttl_seconds

        def _resolve(rid: uuid.UUID):
            return resolve_access(session, user_ctx, rid, "SELECT", cache, ttl)

        dec_table = _resolve(tbl_id)
        if dec_table.decision == DecisionType.DENY:
            raise FilterQueryHttpError(
                403,
                ErrorCode.FORBIDDEN,
                "SELECT denied on table",
            )

        row_exprs: list[str] = list(dec_table.row_filter_exprs)
        masks_by_column: dict[str, ColumnMaskPolicy] = {}

        for col_name, cid in col_ids.items():
            dec_col = _resolve(cid)
            if dec_col.decision == DecisionType.DENY:
                raise FilterQueryHttpError(
                    403,
                    ErrorCode.FORBIDDEN,
                    f"SELECT denied on column '{col_name}'",
                )
            row_exprs.extend(dec_col.row_filter_exprs)
            runtime_masks = resolve_column_masks_for_resource(
                session, user_ctx, cid, cache, ttl
            )
            if runtime_masks:
                masks_by_column[col_name] = runtime_masks[0]
            elif dec_col.column_masks:
                masks_by_column[col_name] = dec_col.column_masks[0]

        combined = combine_row_filters(_dedupe_filters(row_exprs))
        sql_to_run = parsed.original_sql
        if combined:
            sql_to_run = inject_row_filter_predicate(parsed.original_sql, combined)

        try:
            keys, rows = executor.execute_select(sql_to_run, {})
        except Exception as e:
            raise FilterQueryHttpError(
                502,
                ErrorCode.BAD_GATEWAY,
                f"Data source error: {type(e).__name__}",
            ) from e

        masked_cols = list(masks_by_column.keys())
        rows_mut = [dict(r) for r in rows]
        apply_column_masks_to_rows(
            rows_mut,
            list(keys),
            parsed.columns,
            masks_by_column,
            hash_salt=settings.masking_hash_salt,
        )
        out_rows = [jsonable_row(r) for r in rows_mut]

        has_rf = bool(combined)
        has_mk = bool(masked_cols)
        if has_rf and has_mk:
            decision_label = "ALLOW_WITH_FILTER_AND_MASK"
        elif has_rf:
            decision_label = "ALLOW_WITH_FILTER"
        elif has_mk:
            decision_label = "ALLOW_WITH_MASK"
        else:
            decision_label = "ALLOW"

        resp = FilterQueryResponse(
            request_id=body.request_id,
            backend="postgres",
            columns=list(keys),
            rows=out_rows,
            policy=QueryPolicyOut(
                decision=decision_label,
                masked_columns=masked_cols,
                row_filters_applied=1 if combined else 0,
            ),
        )
        record_runtime_access(
            session,
            user_id=user_ctx.user_id,
            resource_id=resource_id_for_audit,
            action=audit_action,
            result="allow",
            decision=resp.policy.decision,
            request_id=request_id or body.request_id,
        )
        return resp
    except FilterQueryHttpError as e:
        record_runtime_access_for_http_error(
            session,
            user_id=user_ctx.user_id,
            resource_id=resource_id_for_audit,
            action=audit_action,
            status_code=e.status_code,
            code=e.code,
            request_id=request_id or body.request_id,
        )
        raise
