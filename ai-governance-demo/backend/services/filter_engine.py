"""Filter Engine — Core governance logic.

Handles:
1. resolve_access: Walk up the resource tree (COLUMN→TABLE→SCHEMA→DATABASE) to find permissions
2. inject_row_filter: Rewrite SQL to add WHERE clause
3. apply_column_masks: Mask sensitive values in result rows
"""
from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.resource import Resource, Database, Schema, Table, ColumnResource
from models.identity import User, UserRole
from models.permission import Permission, RowFilter, ColumnMask


# ─── Data Types ───────────────────────────────────────────

@dataclass
class AccessDecision:
    decision: str  # "ALLOW" | "DENY" | "NO_RULE"
    row_filters: list[str] = field(default_factory=list)
    column_masks: list[dict] = field(default_factory=list)


@dataclass
class FilteredResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    original_sql: str
    rewritten_sql: str
    policy: dict


@dataclass
class ParsedSQL:
    schema_name: str
    table_name: str
    columns: list[str]
    original_sql: str


# ─── SQL Parser (simple regex-based) ─────────────────────

def parse_simple_select(sql: str) -> ParsedSQL:
    """Parse a simple SELECT ... FROM schema.table statement."""
    sql_clean = sql.strip().rstrip(";")

    # Extract columns
    col_match = re.search(r"SELECT\s+(.+?)\s+FROM", sql_clean, re.IGNORECASE | re.DOTALL)
    if not col_match:
        raise ValueError(f"Cannot parse SQL: {sql}")

    col_str = col_match.group(1).strip()
    if col_str == "*":
        columns = ["*"]
    else:
        columns = [c.strip().split(".")[-1] for c in col_str.split(",")]

    # Extract schema.table
    from_match = re.search(r"FROM\s+([\w.]+)", sql_clean, re.IGNORECASE)
    if not from_match:
        raise ValueError(f"Cannot find FROM clause in: {sql}")

    table_ref = from_match.group(1)
    parts = table_ref.split(".")
    if len(parts) == 2:
        schema_name, table_name = parts
    else:
        schema_name = "public"
        table_name = parts[0]

    return ParsedSQL(
        schema_name=schema_name,
        table_name=table_name,
        columns=columns,
        original_sql=sql_clean,
    )


# ─── Resource Lookup ─────────────────────────────────────

def find_resource_chain(db: Session, schema_name: str, table_name: str) -> dict:
    """Find resource IDs for the full chain: DATABASE → SCHEMA → TABLE."""
    # Find schema
    schema_row = db.execute(
        select(Schema).where(Schema.name == schema_name)
    ).scalar_one_or_none()
    if not schema_row:
        raise ValueError(f"Schema '{schema_name}' not found in resource catalog")

    # Find table
    table_row = db.execute(
        select(Table).where(Table.schema_id == schema_row.resource_id, Table.name == table_name)
    ).scalar_one_or_none()
    if not table_row:
        raise ValueError(f"Table '{table_name}' not found in schema '{schema_name}'")

    # Find database
    db_row = db.execute(
        select(Database).where(Database.resource_id == schema_row.database_id)
    ).scalar_one_or_none()

    return {
        "database_id": db_row.resource_id if db_row else None,
        "schema_id": schema_row.resource_id,
        "table_id": table_row.resource_id,
    }


def find_column_resource_id(db: Session, table_id: uuid.UUID, col_name: str) -> uuid.UUID | None:
    """Find the resource_id for a specific column."""
    col = db.execute(
        select(ColumnResource).where(
            ColumnResource.table_id == table_id,
            ColumnResource.name == col_name,
        )
    ).scalar_one_or_none()
    return col.resource_id if col else None


def get_all_columns_for_table(db: Session, table_id: uuid.UUID) -> list[str]:
    """Get all column names for a table."""
    cols = db.execute(
        select(ColumnResource.name).where(ColumnResource.table_id == table_id)
    ).scalars().all()
    return list(cols)


# ─── Permission Resolution ───────────────────────────────

def _get_user_role_ids(db: Session, user_id: uuid.UUID) -> list[uuid.UUID]:
    """Get all role IDs assigned to a user."""
    role_ids = db.execute(
        select(UserRole.role_id).where(UserRole.user_id == user_id)
    ).scalars().all()
    return list(role_ids)


def _find_permissions(db: Session, role_ids: list[uuid.UUID], resource_id: uuid.UUID) -> list[Permission]:
    """Find all permissions for given roles on a specific resource."""
    if not role_ids:
        return []
    perms = db.execute(
        select(Permission).where(
            Permission.role_id.in_(role_ids),
            Permission.resource_id == resource_id,
            Permission.action == "SELECT",
        )
    ).scalars().all()
    return list(perms)


def resolve_access(db: Session, user: User, resource_id: uuid.UUID, resource_chain: dict) -> AccessDecision:
    """
    Walk up the resource tree to resolve access.
    Priority: COLUMN → TABLE → SCHEMA → DATABASE.
    DENY at any level wins immediately.
    """
    role_ids = _get_user_role_ids(db, user.id)
    if not role_ids:
        return AccessDecision(decision="DENY")

    # Check levels from most specific to least specific
    check_order = [
        resource_id,
        resource_chain.get("table_id"),
        resource_chain.get("schema_id"),
        resource_chain.get("database_id"),
    ]

    for rid in check_order:
        if rid is None:
            continue
        perms = _find_permissions(db, role_ids, rid)
        for perm in perms:
            if perm.effect == "DENY":
                return AccessDecision(decision="DENY")

        for perm in perms:
            if perm.effect == "ALLOW":
                # Collect row filters and column masks for this permission
                row_filters = []
                col_masks = []
                rf = db.execute(
                    select(RowFilter).where(RowFilter.permission_id == perm.id)
                ).scalar_one_or_none()
                if rf:
                    row_filters.append(rf.condition_expr)

                cm = db.execute(
                    select(ColumnMask).where(ColumnMask.permission_id == perm.id)
                ).scalar_one_or_none()
                if cm:
                    col_masks.append({
                        "mask_type": cm.mask_type,
                        "mask_pattern": cm.mask_pattern,
                    })

                return AccessDecision(
                    decision="ALLOW",
                    row_filters=row_filters,
                    column_masks=col_masks,
                )

    # Default: DENY
    return AccessDecision(decision="DENY")


# ─── SQL Rewrite ──────────────────────────────────────────

def inject_row_filters(sql: str, filters: list[str], user: User) -> str:
    """Inject row filter expressions into the SQL WHERE clause."""
    if not filters:
        return sql

    # Substitute {user.branch_code} with actual value
    substituted = []
    for f in filters:
        expr = f.replace("{user.branch_code}", f"'{user.branch_code}'" if user.branch_code else "'*'")
        substituted.append(expr)

    filter_clause = " AND ".join(substituted)

    # Check if SQL already has WHERE
    if re.search(r"\bWHERE\b", sql, re.IGNORECASE):
        sql = re.sub(
            r"\bWHERE\b",
            f"WHERE ({filter_clause}) AND",
            sql,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        # Insert WHERE before ORDER BY, LIMIT, GROUP BY, or at end
        insert_point = len(sql)
        for kw in (r"\bORDER\s+BY\b", r"\bGROUP\s+BY\b", r"\bLIMIT\b", r"\bHAVING\b"):
            m = re.search(kw, sql, re.IGNORECASE)
            if m and m.start() < insert_point:
                insert_point = m.start()

        sql = sql[:insert_point].rstrip() + f" WHERE {filter_clause} " + sql[insert_point:]

    return sql.strip()


# ─── Column Masking ───────────────────────────────────────

def _mask_partial(value: str, pattern: str | None) -> str:
    """Apply partial masking. Keeps first 3 and last 2 chars, masks middle."""
    if not value or len(value) < 6:
        return "***"
    return value[:3] + "***" + value[-2:]


def _mask_hash(value: str) -> str:
    """Return a SHA-256 hash (first 12 hex chars)."""
    if not value:
        return "***"
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def _mask_redact(value: str) -> str:
    """Full redaction."""
    return "***"


def apply_column_masks(rows: list[dict], masks_by_column: dict[str, dict]) -> list[dict]:
    """Apply column masking to result rows in-place."""
    for row in rows:
        for col_name, mask_info in masks_by_column.items():
            if col_name not in row:
                continue
            raw = str(row[col_name]) if row[col_name] is not None else ""
            mask_type = mask_info["mask_type"]
            if mask_type == "PARTIAL":
                row[col_name] = _mask_partial(raw, mask_info.get("mask_pattern"))
            elif mask_type == "HASH":
                row[col_name] = _mask_hash(raw)
            elif mask_type == "REDACT":
                row[col_name] = _mask_redact(raw)
    return rows


# ─── Main Entry Point ────────────────────────────────────

def filter_and_execute(sql: str, user: User, db: Session) -> FilteredResult:
    """
    Full governance pipeline:
    1. Parse SQL → extract table + columns
    2. Resolve access for table and each column
    3. Inject row filters
    4. Execute SQL
    5. Apply column masks
    """
    parsed = parse_simple_select(sql)

    # Find resource chain
    chain = find_resource_chain(db, parsed.schema_name, parsed.table_name)
    table_id = chain["table_id"]

    # Check table-level access
    table_decision = resolve_access(db, user, table_id, chain)
    if table_decision.decision == "DENY":
        raise PermissionError(f"Quyền truy cập bị từ chối trên bảng {parsed.schema_name}.{parsed.table_name}")

    # Resolve columns — expand * if needed
    if parsed.columns == ["*"]:
        parsed.columns = get_all_columns_for_table(db, table_id)

    # Check column-level access + collect masks
    all_row_filters = list(table_decision.row_filters)
    masks_by_column: dict[str, dict] = {}
    allowed_columns: list[str] = []

    for col_name in parsed.columns:
        col_rid = find_column_resource_id(db, table_id, col_name)
        if col_rid is None:
            # Column not in catalog — allow by default (pass-through)
            allowed_columns.append(col_name)
            continue

        col_decision = resolve_access(db, user, col_rid, chain)
        if col_decision.decision == "DENY":
            continue  # Skip denied columns silently
        allowed_columns.append(col_name)
        all_row_filters.extend(col_decision.row_filters)
        if col_decision.column_masks:
            masks_by_column[col_name] = col_decision.column_masks[0]

    if not allowed_columns:
        raise PermissionError("Không có cột nào được phép truy cập")

    # Rewrite SQL with allowed columns
    col_str = ", ".join(f"{parsed.schema_name}.{parsed.table_name}.{c}" for c in allowed_columns)
    rewritten = f"SELECT {col_str} FROM {parsed.schema_name}.{parsed.table_name}"

    # Add existing WHERE/ORDER BY from original
    after_from = re.search(r"FROM\s+[\w.]+\s*(.*)", parsed.original_sql, re.IGNORECASE | re.DOTALL)
    if after_from and after_from.group(1).strip():
        rewritten += " " + after_from.group(1).strip()

    # Inject row filters
    unique_filters = list(dict.fromkeys(all_row_filters))
    rewritten = inject_row_filters(rewritten, unique_filters, user)

    # Execute
    from sqlalchemy import text
    result = db.execute(text(rewritten))
    keys = list(result.keys())
    raw_rows = [dict(zip(keys, row)) for row in result.fetchall()]

    # Clean up column names (remove schema.table prefix)
    clean_rows = []
    for row in raw_rows:
        clean = {}
        for k, v in row.items():
            clean_key = k.split(".")[-1] if "." in k else k
            clean[clean_key] = v
        clean_rows.append(clean)

    # Apply masks
    if masks_by_column:
        apply_column_masks(clean_rows, masks_by_column)

    # Build policy summary
    has_filter = bool(unique_filters)
    has_mask = bool(masks_by_column)
    if has_filter and has_mask:
        decision_label = "ALLOW_WITH_FILTER_AND_MASK"
    elif has_filter:
        decision_label = "ALLOW_WITH_FILTER"
    elif has_mask:
        decision_label = "ALLOW_WITH_MASK"
    else:
        decision_label = "ALLOW"

    policy = {
        "decision": decision_label,
        "row_filters_applied": unique_filters,
        "masked_columns": list(masks_by_column.keys()),
        "denied_columns": [c for c in parsed.columns if c not in allowed_columns],
    }

    return FilteredResult(
        columns=[c.split(".")[-1] for c in allowed_columns],
        rows=clean_rows,
        original_sql=parsed.original_sql,
        rewritten_sql=rewritten,
        policy=policy,
    )
