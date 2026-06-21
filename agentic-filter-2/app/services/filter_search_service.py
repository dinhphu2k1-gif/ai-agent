"""OpenSearch runtime: PDP, rewrite query, execute _search (Epic 7 MVP)."""

from __future__ import annotations

import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.cache.redis_client import UserContextCache
from app.connectors.opensearch import OpenSearchExecutor
from app.core.config import Settings
from app.core.errors import ErrorCode
from app.observability import metrics as runtime_metrics
from app.query.opensearch_query_fields import (
    collect_fields_from_post_filter_clause,
    collect_fields_from_query_clause,
)
from app.query.opensearch_rewriter import build_search_body
from app.query.opensearch_row_filter import (
    UnsupportedRowFilterExprError,
    row_filter_exprs_to_term_clauses,
)
from app.query.resource_resolver import (
    AmbiguousOpenSearchIndexError,
    UnknownOpenSearchIndexError,
    resolve_opensearch_index_to_table_resource_id,
)
from app.repositories.resource_repo import ResourceRepository
from app.schemas.runtime import FilterSearchRequest, FilterSearchResponse, QueryPolicyOut
from app.services.audit_service import (
    record_runtime_access,
    record_runtime_access_for_http_error,
)
from app.services.authorization_service import (
    resolve_access,
    resolve_column_masks_for_resource,
)
from app.services.filter_query_service import FilterQueryHttpError
from app.services.masking_service import apply_column_masks_to_row
from app.services.permission_resolver import ColumnMaskPolicy, DecisionType
from app.services.row_filter_service import combine_row_filters
from app.services.user_context_service import UserContext


def _dedupe_filters(exprs: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for e in exprs:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def _normalize_source_for_opensearch(
    source: Any,
    allowed_field_names: set[str],
    *,
    strict_includes: bool,
) -> Any | None:
    """
    strict_includes: if client passed explicit includes, deny when any field not allowed.
    Returns None to omit _source key (OpenSearch default).
    """
    if source is None:
        return {"includes": sorted(allowed_field_names)}
    if source is False:
        return False
    if source is True:
        return {"includes": sorted(allowed_field_names)}
    if isinstance(source, str):
        if source == "false":
            return False
        if source == "true":
            return {"includes": sorted(allowed_field_names)}
        raise FilterQueryHttpError(
            422,
            ErrorCode.UNSUPPORTED_QUERY,
            "Unsupported _source string in MVP",
        )
    if isinstance(source, dict):
        inc = source.get("includes")
        exc = source.get("excludes")
        if inc is not None:
            if not isinstance(inc, list):
                raise FilterQueryHttpError(
                    422,
                    ErrorCode.UNSUPPORTED_QUERY,
                    "_source.includes must be a list",
                )
            names = {str(x) for x in inc}
            if strict_includes:
                bad = names - allowed_field_names
                if bad:
                    raise FilterQueryHttpError(
                        403,
                        ErrorCode.FORBIDDEN,
                        f"SELECT denied or unknown fields in _source.includes: {sorted(bad)}",
                    )
            return {"includes": sorted(names & allowed_field_names)}
        if exc is not None:
            if not isinstance(exc, list):
                raise FilterQueryHttpError(
                    422,
                    ErrorCode.UNSUPPORTED_QUERY,
                    "_source.excludes must be a list",
                )
            ex_set = {str(x) for x in exc}
            effective = allowed_field_names - ex_set
            return {"includes": sorted(effective)}
        return {"includes": sorted(allowed_field_names)}
    raise FilterQueryHttpError(
        422,
        ErrorCode.UNSUPPORTED_QUERY,
        "Unsupported _source shape in MVP",
    )


def run_filter_search(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    settings: Settings,
    body: FilterSearchRequest,
    executor: OpenSearchExecutor,
    *,
    request_id: str | None = None,
) -> FilterSearchResponse:
    audit_action = "OPENSEARCH_FILTER_SEARCH"
    resource_id_for_audit: uuid.UUID | None = None
    try:
        if body.backend != "opensearch":
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                "Only backend=opensearch is supported for this endpoint",
            )

        try:
            tbl_id = resolve_opensearch_index_to_table_resource_id(session, body.index)
        except UnknownOpenSearchIndexError as e:
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                str(e),
            ) from e
        except AmbiguousOpenSearchIndexError as e:
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                str(e),
            ) from e
        resource_id_for_audit = tbl_id

        rr = ResourceRepository(session)
        cols = rr.list_columns_for_table(tbl_id)
        col_by_name: dict[str, uuid.UUID] = {c.name: c.resource_id for c in cols}
        ttl = settings.permission_snapshot_ttl_seconds

        def _resolve(rid: uuid.UUID):
            return resolve_access(session, user_ctx, rid, "SELECT", cache, ttl)

        dec_table = _resolve(tbl_id)
        if dec_table.decision == DecisionType.DENY:
            raise FilterQueryHttpError(
                403,
                ErrorCode.FORBIDDEN,
                "SELECT denied on index/table",
            )

        row_exprs: list[str] = list(dec_table.row_filter_exprs)
        allowed_field_names: set[str] = set()
        masks_by_column: dict[str, ColumnMaskPolicy] = {}

        for col in cols:
            dec_col = _resolve(col.resource_id)
            if dec_col.decision == DecisionType.DENY:
                continue
            allowed_field_names.add(col.name)
            row_exprs.extend(dec_col.row_filter_exprs)
            runtime_masks = resolve_column_masks_for_resource(
                session, user_ctx, col.resource_id, cache, ttl
            )
            if runtime_masks:
                masks_by_column[col.name] = runtime_masks[0]
            elif dec_col.column_masks:
                masks_by_column[col.name] = dec_col.column_masks[0]

        if not allowed_field_names:
            raise FilterQueryHttpError(
                403,
                ErrorCode.FORBIDDEN,
                "No readable fields for this index",
            )

        q_fields = collect_fields_from_query_clause(body.query)
        if body.post_filter is not None:
            q_fields |= collect_fields_from_post_filter_clause(body.post_filter)

        for fname in q_fields:
            cid = col_by_name.get(fname)
            if cid is None:
                raise FilterQueryHttpError(
                    422,
                    ErrorCode.UNSUPPORTED_QUERY,
                    f"Unknown query field '{fname}' for index '{body.index}'",
                )
            dec = _resolve(cid)
            if dec.decision == DecisionType.DENY:
                raise FilterQueryHttpError(
                    403,
                    ErrorCode.FORBIDDEN,
                    f"SELECT denied on field '{fname}'",
                )

        combined_sql = combine_row_filters(_dedupe_filters(row_exprs))
        try:
            policy_filters = (
                row_filter_exprs_to_term_clauses([combined_sql])
                if combined_sql
                else []
            )
        except UnsupportedRowFilterExprError as e:
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                f"Unsupported row filter for OpenSearch: {e}",
            ) from e

        explicit_includes = (
            isinstance(body.source, dict) and body.source.get("includes") is not None
        ) or (isinstance(body.source, dict) and body.source.get("excludes") is not None)
        source_out = _normalize_source_for_opensearch(
            body.source,
            allowed_field_names,
            strict_includes=bool(explicit_includes),
        )

        try:
            search_body = build_search_body(
                query_clause=body.query,
                policy_filters=policy_filters,
                post_filter_clause=body.post_filter,
                source=source_out,
                size=body.size,
                from_=body.from_,
                sort=body.sort,
            )
        except ValueError as e:
            raise FilterQueryHttpError(
                422,
                ErrorCode.UNSUPPORTED_QUERY,
                str(e),
            ) from e

        try:
            raw = executor.search(body.index, search_body)
        except Exception as e:
            raise FilterQueryHttpError(
                502,
                ErrorCode.BAD_GATEWAY,
                f"OpenSearch error: {type(e).__name__}",
            ) from e

        hits = raw.get("hits", {})
        inner = hits.get("hits", []) if isinstance(hits, dict) else []
        if masks_by_column and inner:
            t0 = time.perf_counter()
            identity = {c: c for c in masks_by_column}
            for hit in inner:
                src = hit.get("_source")
                if isinstance(src, dict):
                    apply_column_masks_to_row(
                        src,
                        identity,
                        masks_by_column,
                        hash_salt=settings.masking_hash_salt,
                    )
            runtime_metrics.record_masking_duration_ms((time.perf_counter() - t0) * 1000.0)

        has_rf = bool(policy_filters)
        masked_cols = list(masks_by_column.keys())
        has_mk = bool(masked_cols)
        if has_rf and has_mk:
            decision_label = "ALLOW_WITH_FILTER_AND_MASK"
        elif has_rf:
            decision_label = "ALLOW_WITH_FILTER"
        elif has_mk:
            decision_label = "ALLOW_WITH_MASK"
        else:
            decision_label = "ALLOW"

        resp = FilterSearchResponse(
            request_id=body.request_id,
            backend="opensearch",
            hits=hits if isinstance(hits, dict) else {"hits": []},
            policy=QueryPolicyOut(
                decision=decision_label,
                masked_columns=masked_cols,
                row_filters_applied=1 if has_rf else 0,
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
