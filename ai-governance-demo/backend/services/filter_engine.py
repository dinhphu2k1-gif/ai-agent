"""Filter Engine — Core governance logic.

Handles:
1. resolve_access: Walk up the resource tree (COLUMN→TABLE→SCHEMA→DATABASE) to find permissions
2. inject_row_filter: Rewrite SQL to add WHERE clause
3. apply_column_masks: Mask sensitive values in result rows
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import text

import sqlglot
import sqlglot.expressions as exp
from sqlglot.optimizer.qualify import qualify

from models.resource import Database, Schema, Table, ColumnResource
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


# ─── Resource Lookup ─────────────────────────────────────

def find_resource_chain(db: Session, schema_name: str, table_name: str) -> dict | None:
    """Find resource IDs for the full chain: DATABASE → SCHEMA → TABLE."""
    schema_row = db.execute(
        select(Schema).where(Schema.name == schema_name)
    ).scalar_one_or_none()
    if not schema_row:
        return None

    table_row = db.execute(
        select(Table).where(Table.schema_id == schema_row.resource_id, Table.name == table_name)
    ).scalar_one_or_none()
    if not table_row:
        return None

    db_row = db.execute(
        select(Database).where(Database.resource_id == schema_row.database_id)
    ).scalar_one_or_none()

    return {
        "database_id": db_row.resource_id if db_row else None,
        "schema_id": schema_row.resource_id,
        "table_id": table_row.resource_id,
    }


def find_column_resource_id(db: Session, table_id: uuid.UUID, col_name: str) -> uuid.UUID | None:
    col = db.execute(
        select(ColumnResource).where(ColumnResource.table_id == table_id, ColumnResource.name == col_name)
    ).scalar_one_or_none()
    return col.resource_id if col else None


def build_catalog_schema(db: Session) -> dict:
    """Builds the schema dictionary required by sqlglot's qualify function."""
    catalog = {}
    schemas = db.execute(select(Schema)).scalars().all()
    tables = db.execute(select(Table)).scalars().all()
    cols = db.execute(select(ColumnResource)).scalars().all()

    schema_map = {s.resource_id: s.name for s in schemas}
    table_map = {t.resource_id: t for t in tables}
    
    for t in tables:
        s_name = schema_map.get(t.schema_id, "public")
        if s_name not in catalog:
            catalog[s_name] = {}
        catalog[s_name][t.name] = {}

    for c in cols:
        t = table_map.get(c.table_id)
        if t:
            s_name = schema_map.get(t.schema_id, "public")
            catalog[s_name][t.name][c.name] = "VARCHAR"

    return catalog


# ─── Permission Resolution ───────────────────────────────

def _get_user_role_ids(db: Session, user_id: uuid.UUID) -> list[uuid.UUID]:
    role_ids = db.execute(
        select(UserRole.role_id).where(UserRole.user_id == user_id)
    ).scalars().all()
    return list(role_ids)


def _find_permissions(db: Session, role_ids: list[uuid.UUID], resource_id: uuid.UUID) -> list[Permission]:
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

    return AccessDecision(decision="DENY")


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
    Full governance pipeline using SQLGlot AST parsing:
    1. Parse SQL into AST and qualify all columns.
    2. Check table-level access. Apply row filters by converting tables to subqueries.
    3. Check column-level access. Replace denied columns with NULL in the AST.
    4. Collect column masks for the root SELECT.
    5. Execute rewritten SQL and apply masks to the results.
    """
    try:
        ast = sqlglot.parse_one(sql, read="postgres")
    except Exception as e:
        raise ValueError(f"Không thể phân tích cú pháp SQL: {e}")

    catalog_schema = build_catalog_schema(db)
    try:
        ast = qualify(ast, schema=catalog_schema, dialect="postgres")
    except Exception as e:
        # Fallback if qualify fails (e.g. unknown functions)
        pass

    all_row_filters = []
    masks_by_column = {}
    denied_columns = []
    alias_to_table_chain = {}
    
    # Process Tables
    for table in ast.find_all(exp.Table):
        db_name = table.db or "public"
        table_name = table.name
        
        chain = find_resource_chain(db, db_name, table_name)
        if not chain:
            continue
            
        table_id = chain["table_id"]
        alias_to_table_chain[table.alias_or_name] = chain
        
        table_decision = resolve_access(db, user, table_id, chain)
        if table_decision.decision == "DENY":
            raise PermissionError(f"Quyền truy cập bị từ chối trên bảng {db_name}.{table_name}")
            
        if table_decision.row_filters:
            substituted = []
            for f in table_decision.row_filters:
                expr = f.replace("{user.branch_code}", f"'{user.branch_code}'" if user.branch_code else "'*'")
                substituted.append(expr)
            filter_expr = " AND ".join(substituted)
            all_row_filters.extend(table_decision.row_filters)
            
            subq_sql = f"(SELECT * FROM {db_name}.{table_name} WHERE {filter_expr})"
            subq = sqlglot.parse_one(subq_sql, read="postgres")
            subq_with_alias = exp.alias_(subq, table.alias_or_name)
            table.replace(subq_with_alias)

    # Process Columns Level Security
    # Replace denied columns with NULL everywhere in the query
    for col_node in list(ast.find_all(exp.Column)):
        col_name = col_node.name
        table_alias = col_node.table
        chain = alias_to_table_chain.get(table_alias)
        if not chain: continue
        
        col_rid = find_column_resource_id(db, chain["table_id"], col_name)
        if not col_rid: continue
        
        col_decision = resolve_access(db, user, col_rid, chain)
        if col_decision.decision == "DENY":
            if col_name not in denied_columns:
                denied_columns.append(col_name)
            col_node.replace(sqlglot.parse_one("NULL", read="postgres"))

    # Collect Masks for Output Columns
    if isinstance(ast, exp.Select):
        for select_expr in ast.expressions:
            col_node = select_expr.this if isinstance(select_expr, exp.Alias) else select_expr
            if isinstance(col_node, exp.Column):
                col_name = col_node.name
                table_alias = col_node.table
                chain = alias_to_table_chain.get(table_alias)
                if not chain: continue
                
                col_rid = find_column_resource_id(db, chain["table_id"], col_name)
                if not col_rid: continue
                
                col_decision = resolve_access(db, user, col_rid, chain)
                if col_decision.decision == "ALLOW" and col_decision.column_masks:
                    out_name = select_expr.alias if isinstance(select_expr, exp.Alias) else col_name
                    masks_by_column[out_name] = col_decision.column_masks[0]

    # Execute
    rewritten = ast.sql(dialect="postgres")
    result = db.execute(text(rewritten))
    keys = list(result.keys())
    raw_rows = [dict(zip(keys, row)) for row in result.fetchall()]

    if masks_by_column:
        apply_column_masks(raw_rows, masks_by_column)

    unique_filters = list(dict.fromkeys(all_row_filters))
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
        "denied_columns": list(dict.fromkeys(denied_columns)),
    }

    return FilteredResult(
        columns=keys,
        rows=raw_rows,
        original_sql=sql,
        rewritten_sql=rewritten,
        policy=policy,
    )
