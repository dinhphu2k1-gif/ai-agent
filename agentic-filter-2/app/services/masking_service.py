"""Column masking after connector results (§3.7) — canonical column names only."""

from __future__ import annotations

import enum
import ipaddress
import math
import time
import uuid
from datetime import date, datetime, time as dt_time, timedelta
from decimal import Decimal
from typing import Any

from app.observability import metrics as runtime_metrics
from app.services.column_mask_engine import mask_value
from app.services.permission_resolver import ColumnMaskPolicy


def _apply_mask_value(
    value: Any,
    mask_type: str,
    pattern: str | None,
    *,
    hash_salt: str,
) -> Any:
    return mask_value(
        value,
        mask_type,
        pattern,
        hash_salt=hash_salt,
        for_preview=False,
    )


def logical_column_to_result_keys(
    logical_columns: tuple[str, ...],
    projection_keys: list[str],
    *,
    projection_output_keys: tuple[str, ...] | None = None,
) -> dict[str, str]:
    """
    Map catalog/policy column name → key present in each result row.

    Handles ``SELECT col AS alias``, and Postgres returning lowercase unquoted identifiers.
    """
    out: dict[str, str] = {}
    by_lower = {k.lower(): k for k in projection_keys}
    outputs = projection_output_keys or logical_columns
    for i, logical in enumerate(logical_columns):
        out_key = outputs[i] if i < len(outputs) else logical
        rk = by_lower.get(out_key.lower()) or by_lower.get(logical.lower())
        if rk is None and i < len(projection_keys):
            rk = projection_keys[i]
        if rk is not None:
            out[logical] = rk
    return out


def apply_column_masks_to_row(
    row: dict[str, Any],
    logical_to_result_key: dict[str, str],
    masks_by_column: dict[str | tuple[str, str], ColumnMaskPolicy],
    *,
    hash_salt: str,
    qualified_to_result_key: dict[tuple[str, str], str] | None = None,
) -> None:
    """In-place mask using **logical** column names from PDP; values read/written via mapped keys."""
    seen_result_keys: set[str] = set()
    for logical, pol in masks_by_column.items():
        rk: str | None = None
        if isinstance(logical, tuple) and qualified_to_result_key is not None:
            rk = qualified_to_result_key.get(logical)
        elif isinstance(logical, str):
            rk = logical_to_result_key.get(logical)
        if rk is None or rk in seen_result_keys:
            continue
        if rk not in row:
            continue
        seen_result_keys.add(rk)
        row[rk] = _apply_mask_value(
            row.get(rk), pol.mask_type, pol.mask_pattern, hash_salt=hash_salt
        )


def projection_table_column_to_result_keys(
    projections: tuple[tuple[str, str, str], ...],
    projection_keys: list[str],
    *,
    projection_output_keys: tuple[str, ...] | None = None,
) -> dict[tuple[str, str], str]:
    """Map (table_name, column_name) from parser → executor result dict key."""
    by_lower = {k.lower(): k for k in projection_keys}
    out: dict[tuple[str, str], str] = {}
    outputs = projection_output_keys or tuple(col for _, _, col in projections)
    for i, (out_key, tbl, col) in enumerate(projections):
        label = outputs[i] if i < len(outputs) else out_key
        rk = by_lower.get(label.lower()) or by_lower.get(col.lower()) or by_lower.get(out_key.lower())
        if rk is None and i < len(projection_keys):
            rk = projection_keys[i]
        if rk is not None:
            out[(tbl.upper(), col.upper())] = rk
    return out


def apply_column_masks_to_rows(
    rows: list[dict[str, Any]],
    projection_keys: list[str],
    logical_columns: tuple[str, ...],
    masks_by_column: dict[str | tuple[str, str], ColumnMaskPolicy],
    *,
    hash_salt: str,
    projection_output_keys: tuple[str, ...] | None = None,
    projections: tuple[tuple[str, str, str], ...] | None = None,
) -> None:
    if not rows or not masks_by_column:
        return
    t0 = time.perf_counter()
    mapping = logical_column_to_result_keys(
        logical_columns,
        projection_keys,
        projection_output_keys=projection_output_keys,
    )
    qualified_mapping: dict[tuple[str, str], str] | None = None
    if projections:
        qualified_mapping = projection_table_column_to_result_keys(
            projections,
            projection_keys,
            projection_output_keys=projection_output_keys,
        )
    for row in rows:
        apply_column_masks_to_row(
            row,
            mapping,
            masks_by_column,
            hash_salt=hash_salt,
            qualified_to_result_key=qualified_mapping,
        )
    runtime_metrics.record_masking_duration_ms((time.perf_counter() - t0) * 1000.0)


def jsonable_cell(v: Any) -> Any:
    """
    Convert a single DB/API cell to a JSON-serializable value (stdlib json / FastAPI).

    Covers common PostgreSQL/SQLAlchemy driver types: Decimal, date/time, UUID,
    bytes, JSONB nests, enums, IP addresses, and unknown scalars via str().
    """
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, dt_time):
        return v.isoformat()
    if isinstance(v, timedelta):
        return v.total_seconds()
    if isinstance(v, enum.Enum):
        return jsonable_cell(v.value)
    if isinstance(v, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
        return str(v)
    if isinstance(v, (ipaddress.IPv4Network, ipaddress.IPv6Network, ipaddress.IPv4Interface, ipaddress.IPv6Interface)):
        return str(v)
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, memoryview):
        return bytes(v).decode("utf-8", errors="replace")
    if isinstance(v, dict):
        return {str(k): jsonable_cell(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [jsonable_cell(x) for x in v]
    if isinstance(v, set):
        return [jsonable_cell(x) for x in sorted(v, key=str)]
    return str(v)


def jsonable_row(row: dict[str, Any]) -> dict[str, Any]:
    return {k: jsonable_cell(v) for k, v in row.items()}
