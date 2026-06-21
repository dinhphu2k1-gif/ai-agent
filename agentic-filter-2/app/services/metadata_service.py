"""Metadata discovery: OpenSearch upstream + DESCRIBE filter (metadata_agent integration)."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.cache.redis_client import UserContextCache
from app.connectors.opensearch import OpenSearchExecutor
from app.core.config import Settings
from app.query.metadata_dictionary import (
    build_columns_lookup_body,
    build_hybrid_search_body,
    build_keyword_search_body,
    build_relationships_body,
    build_table_lookup_body,
    hit_display_key,
    resolve_metadata_hit_to_resource_id,
)
from app.schemas.metadata_contract import (
    MetadataApiResponse,
    MetadataDebugOut,
    MetadataFilteredOut,
    MetadataFormatDataOut,
    MetadataFormatResultsRequest,
    MetadataHybridSearchRequest,
    MetadataKeywordSearchRequest,
    MetadataRelationshipsRequest,
    MetadataSearchDataOut,
    MetadataWarningOut,
)
from app.services.authorization_service import resolve_access
from app.services.metadata_embedding import MetadataEmbeddingError, MetadataEmbeddingService
from app.services.permission_resolver import DecisionType
from app.services.user_context_service import UserContext

logger = logging.getLogger(__name__)

_FILTERED_SAMPLE_LIMIT = 20
_RECORD_RELATIONSHIP = "RELATIONSHIP"


class MetadataHttpError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def _record_type(source: dict[str, Any]) -> str:
    return str(source.get("record_type") or "").strip().upper()


def _filter_hits(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    settings: Settings,
    hits: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], MetadataFilteredOut, list[MetadataWarningOut]]:
    ttl = settings.permission_snapshot_ttl_seconds
    kept: list[dict[str, Any]] = []
    removed_tables: list[str] = []
    removed_columns: list[str] = []
    removed_relationships: list[str] = []
    dropped = 0

    for hit in hits:
        source = hit.get("_source")
        if not isinstance(source, dict):
            dropped += 1
            continue
        if _record_type(source) == _RECORD_RELATIONSHIP:
            kept.append(hit)
            continue

        rid = resolve_metadata_hit_to_resource_id(session, hit)
        label = hit_display_key(hit)
        if rid is None:
            # No catalog row — not a DESCRIBE denial; omit from removed* samples.
            dropped += 1
            continue

        decision = resolve_access(session, user_ctx, rid, "DESCRIBE", cache, ttl)
        if decision.decision == DecisionType.DENY:
            dropped += 1
            rt = _record_type(source)
            if label:
                if rt == "TABLE" and len(removed_tables) < _FILTERED_SAMPLE_LIMIT:
                    removed_tables.append(label)
                elif rt == "COLUMN" and len(removed_columns) < _FILTERED_SAMPLE_LIMIT:
                    removed_columns.append(label)
            continue
        kept.append(hit)

    filtered = MetadataFilteredOut(
        removedTables=removed_tables,
        removedColumns=removed_columns,
        removedRelationships=removed_relationships,
    )
    warnings: list[MetadataWarningOut] = []
    if dropped:
        warnings.append(
            MetadataWarningOut(
                code="ACCESS_FILTERED",
                message="Một số resource không đủ quyền đã bị loại bỏ khỏi kết quả.",
                details={"count": dropped},
            )
        )
    return kept, filtered, warnings


def _search_and_filter(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    settings: Settings,
    executor: OpenSearchExecutor,
    body: dict[str, Any],
    *,
    query_mode: str,
    hybrid_leg: str | None = None,
) -> MetadataSearchDataOut:
    index = settings.opensearch_index
    t0 = time.perf_counter()
    try:
        raw = executor.search(index, body)
    except httpx.TimeoutException as e:
        raise MetadataHttpError(504, "TIMEOUT", "OpenSearch request timed out") from e
    except httpx.HTTPError as e:
        raise MetadataHttpError(502, "UPSTREAM_ERROR", "OpenSearch request failed") from e

    hits_raw = raw.get("hits", {}).get("hits", [])
    if not isinstance(hits_raw, list):
        hits_raw = []
    kept, filtered, warnings = _filter_hits(
        session, user_ctx, cache, settings, hits_raw
    )
    took_ms = int((time.perf_counter() - t0) * 1000)
    lst_kept = [hit.get('_source', {}).get('table_name', None) for hit in kept]
    print(f"kept: {lst_kept}")
    print(f"filtered: {filtered}")
    print(f"warnings: {warnings}")
    return MetadataSearchDataOut(
        hits=kept,
        filtered=filtered,
        warnings=warnings,
        debug=MetadataDebugOut(
            tookMs=took_ms,
            queryMode=query_mode,
            index=index,
            hybridLeg=hybrid_leg,
        ),
    )


def run_metadata_hybrid_search(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    settings: Settings,
    body: MetadataHybridSearchRequest,
    executor: OpenSearchExecutor,
    embedder: MetadataEmbeddingService | None,
) -> MetadataApiResponse:
    query_vector: list[float] | None = None
    hybrid_leg = "keyword_fallback"

    if settings.metadata_hybrid_enabled:
        if embedder is None:
            raise MetadataHttpError(
                503,
                "EMBEDDING_UNAVAILABLE",
                "Metadata embedding service is not configured",
            )
        try:
            query_vector = embedder.encode_query(body.query)
            hybrid_leg = "knn_bm25"
        except MetadataEmbeddingError as e:
            raise MetadataHttpError(
                503,
                "EMBEDDING_UNAVAILABLE",
                str(e),
            ) from e

    os_body = build_hybrid_search_body(
        body.query,
        body.size,
        hybrid_enabled=settings.metadata_hybrid_enabled,
        query_vector=query_vector,
        record_type=body.record_type,
        table_name=body.table_name,
    )
    data = _search_and_filter(
        session,
        user_ctx,
        cache,
        settings,
        executor,
        os_body,
        query_mode="hybrid",
        hybrid_leg=hybrid_leg,
    )
    return MetadataApiResponse(success=True, data=data)


def run_metadata_keyword_search(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    settings: Settings,
    body: MetadataKeywordSearchRequest,
    executor: OpenSearchExecutor,
) -> MetadataApiResponse:
    os_body = build_keyword_search_body(
        body.query,
        body.size,
        record_type=body.record_type,
        table_name=body.table_name,
    )
    data = _search_and_filter(
        session,
        user_ctx,
        cache,
        settings,
        executor,
        os_body,
        query_mode="keyword",
    )
    return MetadataApiResponse(success=True, data=data)


def run_metadata_table(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    settings: Settings,
    table_name: str,
    *,
    size: int,
    executor: OpenSearchExecutor,
) -> MetadataApiResponse:
    os_body = build_table_lookup_body(table_name, size)
    data = _search_and_filter(
        session,
        user_ctx,
        cache,
        settings,
        executor,
        os_body,
        query_mode="table",
    )
    return MetadataApiResponse(success=True, data=data)


def run_metadata_table_columns(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    settings: Settings,
    table_name: str,
    *,
    size: int,
    executor: OpenSearchExecutor,
) -> MetadataApiResponse:
    os_body = build_columns_lookup_body(table_name, size)
    data = _search_and_filter(
        session,
        user_ctx,
        cache,
        settings,
        executor,
        os_body,
        query_mode="columns",
    )
    return MetadataApiResponse(success=True, data=data)


def run_metadata_relationships(
    session: Session,
    user_ctx: UserContext,
    cache: UserContextCache,
    settings: Settings,
    body: MetadataRelationshipsRequest,
    executor: OpenSearchExecutor,
) -> MetadataApiResponse:
    os_body = build_relationships_body(body.table_names, body.size)
    data = _search_and_filter(
        session,
        user_ctx,
        cache,
        settings,
        executor,
        os_body,
        query_mode="relationships",
    )
    return MetadataApiResponse(success=True, data=data)


def _format_hits(hits: list[dict[str, Any]]) -> str:
    """Format hits for LLM consumption (agentic-agri ``format_search_results``)."""
    if not hits:
        return "Không tìm thấy kết quả nào trong Data Dictionary."

    sections: list[str] = []
    for hit in hits:
        source = hit.get("_source")
        if not isinstance(source, dict):
            continue
        rt = _record_type(source)

        if rt == "TABLE":
            section = (
                f"[TABLE] {source.get('table_name', '')} — {source.get('business_name', '')}\n"
                f"  Mô tả: {source.get('description', '')}\n"
                f"  Mục đích: {source.get('table_purpose', '')}\n"
                f"  Primary Key: {source.get('primary_key_columns', '')}\n"
                f"  Natural Key: {source.get('natural_key', '')}\n"
                f"  Bảng liên quan: {', '.join(source.get('related_tables') or [])}\n"
                f"  Ước tính rows: {source.get('estimated_row_count', '')}\n"
                f"  Quy tắc: {source.get('business_rules', '') or 'N/A'}"
            )
        elif rt == "RELATIONSHIP":
            related = source.get("related_tables") or []
            if isinstance(related, str):
                related = [related]
            section = (
                f"[RELATIONSHIP] {source.get('relationship_name', '')}\n"
                f"  Mô tả: {source.get('description', '')}\n"
                f"  Join Path: {source.get('join_path', '')}\n"
                f"  Sample SQL: {source.get('sample_sql', '')}\n"
                f"  Bảng liên quan: {', '.join(related)}"
            )
        else:
            fk_info = ""
            if source.get("is_foreign_key"):
                fk_info = (
                    f" → FK({source.get('references_table', '')}."
                    f"{source.get('references_column', '')})"
                )
            pk_info = " [PK]" if source.get("is_primary_key") else ""
            section = (
                f"[COLUMN] {source.get('table_name', '')}.{source.get('column_name', '')}"
                f"{pk_info}{fk_info}\n"
                f"  Kiểu: {source.get('data_type', '')}\n"
                f"  Tên nghiệp vụ: {source.get('business_name', '')}\n"
                f"  Mô tả: {source.get('description', '')}\n"
                f"  Allowed values: {source.get('allowed_values', '') or 'N/A'}\n"
                f"  Quy tắc: {source.get('business_rules', '') or 'N/A'}"
            )
        sections.append(section)

    return "\n\n".join(sections)


def run_metadata_format_results(
    body: MetadataFormatResultsRequest,
) -> MetadataApiResponse:
    return MetadataApiResponse(
        success=True,
        data=MetadataFormatDataOut(rawResults=_format_hits(body.hits)),
    )
