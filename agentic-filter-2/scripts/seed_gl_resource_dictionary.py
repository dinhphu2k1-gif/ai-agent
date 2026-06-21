#!/usr/bin/env python3
"""Seed Filter Service catalog + DESCRIBE permissions for metadata_agent integration tests.

Luồng (hai nguồn, tránh lệch tên):
  1. **Dictionary** — ``agentic-agri/scripts/seed_data_dictionary.py``: nguồn chuẩn cho
     ``database_name`` / ``schema_name`` / ``table_name`` / ``column_name`` ghi vào catalog.
  2. **OpenSearch** — scroll index ``data_dictionary``: đối chiếu cùng khóa logic
     (``TABLE|COREDB|GL|GL_ACCOUNTS``, ``COLUMN|...``). Chỉ seed catalog khi hai nguồn khớp
     (mặc định ``STRICT_OPENSEARCH_RECONCILE=true``).
  3. Ghi PostgreSQL: DATABASE ``COREDB`` → SCHEMA → TABLE → COLUMN.
  4. Gán DESCRIBE + user tích hợp; xuất manifest (catalog id ↔ OpenSearch ``_id`` + báo cáo reconcile).

Chạy (sau ``agentic-agri`` ``seed_data_dictionary_1.py`` trên OpenSearch):

  pip install -e ".[dev]"
  python scripts/seed_gl_resource_dictionary.py

Biến môi trường:
  AGRI_DATA_DICTIONARY_SCRIPT       — ``seed_data_dictionary.py`` (nguồn tên resource)
  AGRI_DATA_DICTIONARY_V1_SCRIPT     — ``seed_data_dictionary_1.py`` (UUID id, tuỳ chọn)
  STRICT_OPENSEARCH_RECONCILE       — ``true`` (mặc định): fail nếu TABLE/COLUMN dictionary thiếu trên OS
  SKIP_OPENSEARCH_FETCH=true          — chỉ dictionary, bỏ qua đối chiếu OpenSearch (dev)
  METADATA_INTEGRATION_MANIFEST     — JSON đầu ra (mặc định scripts/gl_metadata_integration_manifest.json)
  METADATA_SEED_DESCRIBE_USER_ID    — UUID user nhận DESCRIBE
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEFAULT_AGRI_DICTIONARY_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "agentic-agri"
    / "scripts"
    / "seed_data_dictionary.py"
)
DEFAULT_AGRI_V1_SCRIPT = DEFAULT_AGRI_DICTIONARY_SCRIPT.parent / "seed_data_dictionary_1.py"
DEFAULT_MANIFEST = ROOT / "scripts" / "gl_metadata_integration_manifest.json"

DATABASE_NAME = "COREDB"
DATABASE_DESCRIPTION = (
    "Core Banking System — General Ledger (GL) & Customer Information (CIF). "
    "Metadata seeded for metadata_agent ↔ filter-service integration."
)

_CATALOG_SEED_TYPES = frozenset({"TABLE", "COLUMN"})


@dataclass(frozen=True)
class ReconcileReport:
    """Kết quả đối chiếu dictionary ↔ OpenSearch trước khi ghi catalog."""

    dictionary_table_keys: int
    dictionary_column_keys: int
    opensearch_table_keys: int
    opensearch_column_keys: int
    aligned_table_keys: int
    aligned_column_keys: int
    missing_in_opensearch: tuple[str, ...] = ()
    extra_in_opensearch: tuple[str, ...] = ()
    identifier_mismatches: tuple[str, ...] = ()
    strict: bool = True
    skipped_opensearch: bool = False

    @property
    def passed(self) -> bool:
        if self.skipped_opensearch:
            return True
        if self.identifier_mismatches:
            return False
        if self.strict and self.missing_in_opensearch:
            return False
        return True


def _resolve_agri_dictionary_script_path() -> Path:
    """Path to ``seed_data_dictionary.py`` — nguồn tên schema/table/column."""
    raw = os.environ.get("AGRI_DATA_DICTIONARY_SCRIPT", "").strip()
    if raw:
        return Path(raw)
    legacy_v1 = os.environ.get("AGRI_DATA_DICTIONARY_V1_SCRIPT", "").strip()
    if legacy_v1:
        p = Path(legacy_v1)
        sibling = p.parent / "seed_data_dictionary.py"
        if p.name == "seed_data_dictionary_1.py" and sibling.is_file():
            return sibling
        if p.name == "seed_data_dictionary.py":
            return p
    return DEFAULT_AGRI_DICTIONARY_SCRIPT


def _resolve_agri_v1_script_path(dictionary_path: Path) -> Path | None:
    raw = os.environ.get("AGRI_DATA_DICTIONARY_V1_SCRIPT", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_file() else None
    sibling = dictionary_path.parent / "seed_data_dictionary_1.py"
    return sibling if sibling.is_file() else None


def _load_module_from_path(path: Path, module_name: str) -> Any:
    if not path.is_file():
        raise FileNotFoundError(f"agentic-agri script not found: {path}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def normalize_dictionary_record(rec: dict[str, Any]) -> dict[str, Any]:
    """Strip identifier fields so catalog keys match OpenSearch ``_source``."""
    row = dict(rec)
    db = row.get("database_name")
    if db is not None:
        row["database_name"] = str(db).strip() or DATABASE_NAME
    for field in ("schema_name", "table_name", "column_name"):
        value = row.get(field)
        if value is not None and str(value).strip():
            row[field] = str(value).strip()
    return row


def load_all_records_from_agri(
    dictionary_path: Path | None = None,
    *,
    assign_uuids: bool = True,
) -> list[dict[str, Any]]:
    """Load ``ALL_RECORDS`` from ``seed_data_dictionary.py`` (source of resource names).

    UUID ``id`` (OpenSearch v1) comes from ``seed_data_dictionary_1.prepare_records_with_ids``
    when ``assign_uuids`` is true and the v1 helper script exists beside the dictionary file.
    """
    dict_path = dictionary_path or _resolve_agri_dictionary_script_path()
    base_mod = _load_module_from_path(dict_path, "agri_seed_data_dictionary")
    records_raw = getattr(base_mod, "ALL_RECORDS", None)
    if not isinstance(records_raw, (list, tuple)):
        raise RuntimeError(f"{dict_path} missing ALL_RECORDS list/tuple")
    records = [normalize_dictionary_record(dict(r)) for r in records_raw]

    if assign_uuids:
        v1_path = _resolve_agri_v1_script_path(dict_path)
        if v1_path is not None:
            v1_mod = _load_module_from_path(v1_path, "agri_seed_data_dictionary_v1")
            prepare = getattr(v1_mod, "prepare_records_with_ids", None)
            if prepare is None:
                raise RuntimeError(f"{v1_path} missing prepare_records_with_ids")
            records = [normalize_dictionary_record(dict(r)) for r in prepare(records)]
    return records


def load_all_records_from_agri_v1(script_path: Path | None = None) -> list[dict[str, Any]]:
    """Backward-compatible alias — prefer ``load_all_records_from_agri``."""
    if script_path is not None:
        if script_path.name == "seed_data_dictionary_1.py":
            dict_path = script_path.parent / "seed_data_dictionary.py"
            if not dict_path.is_file():
                dict_path = script_path
        else:
            dict_path = script_path
        return load_all_records_from_agri(dict_path)
    return load_all_records_from_agri()


def record_catalog_key(rec: dict[str, Any]) -> str | None:
    """Stable key to match agri record ↔ OpenSearch ``_source``."""
    rt = str(rec.get("record_type") or "").strip().upper()
    db = str(rec.get("database_name") or DATABASE_NAME).strip()
    schema = str(rec.get("schema_name") or "").strip()
    table = str(rec.get("table_name") or "").strip()

    if rt == "COLUMN":
        col = str(rec.get("column_name") or "").strip()
        if schema and table and col:
            return f"COLUMN|{db}|{schema}|{table}|{col}"
        return None
    if rt == "TABLE":
        if schema and table:
            return f"TABLE|{db}|{schema}|{table}"
        return None
    if rt == "RELATIONSHIP":
        name = str(rec.get("relationship_name") or "").strip()
        related = rec.get("related_tables") or []
        if isinstance(related, str):
            related = [related]
        parts = ",".join(sorted(str(t).strip() for t in related if str(t).strip()))
        return f"RELATIONSHIP|{db}|{name}|{parts}"
    return None


def _record_type(rec: dict[str, Any]) -> str:
    return str(rec.get("record_type") or "").strip().upper()


def _catalog_seed_keys(records: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    """TABLE/COLUMN catalog keys present in dictionary (used for catalog seed + reconcile)."""
    table_keys: set[str] = set()
    column_keys: set[str] = set()
    for rec in records:
        rt = _record_type(rec)
        if rt not in _CATALOG_SEED_TYPES:
            continue
        key = record_catalog_key(rec)
        if not key:
            continue
        if rt == "TABLE":
            table_keys.add(key)
        else:
            column_keys.add(key)
    return table_keys, column_keys


def _identifier_snapshot(rec: dict[str, Any]) -> dict[str, str]:
    rt = _record_type(rec)
    out = {
        "database_name": str(rec.get("database_name") or DATABASE_NAME).strip(),
        "schema_name": str(rec.get("schema_name") or "").strip(),
        "table_name": str(rec.get("table_name") or "").strip(),
    }
    if rt == "COLUMN":
        out["column_name"] = str(rec.get("column_name") or "").strip()
    return out


def _identifiers_match(file_rec: dict[str, Any], os_source: dict[str, Any]) -> bool:
    file_ids = _identifier_snapshot(normalize_dictionary_record(file_rec))
    os_ids = _identifier_snapshot(normalize_dictionary_record(os_source))
    return file_ids == os_ids


def fetch_opensearch_records(
    *,
    base_url: str,
    index: str,
    auth: tuple[str, str] | None,
    timeout_seconds: float = 60.0,
    page_size: int = 500,
    verify: bool = True,
) -> dict[str, dict[str, Any]]:
    """Scroll index; return catalog_key → ``{"id": _id, "source": _source}``."""
    mapping: dict[str, dict[str, Any]] = {}
    scroll_id: str | None = None
    scroll_ttl = "2m"

    with httpx.Client(
        base_url=base_url.rstrip("/"),
        auth=auth,
        timeout=httpx.Timeout(timeout_seconds),
        verify=verify,
    ) as client:
        def _consume(hits: list[dict[str, Any]]) -> None:
            for hit in hits:
                source = hit.get("_source")
                if not isinstance(source, dict):
                    continue
                key = record_catalog_key(source)
                if key is None:
                    continue
                doc_id = str(hit.get("_id", "")).strip()
                if not doc_id:
                    continue
                mapping[key] = {"id": doc_id, "source": normalize_dictionary_record(source)}

        body: dict[str, Any] = {
            "size": page_size,
            "query": {"match_all": {}},
        }
        resp = client.post(f"/{index.strip('/')}/_search?scroll={scroll_ttl}", json=body)
        resp.raise_for_status()
        data = resp.json()
        scroll_id = data.get("_scroll_id")
        hits = data.get("hits", {}).get("hits", [])
        if isinstance(hits, list):
            _consume(hits)

        while scroll_id and hits:
            resp = client.post(
                "/_search/scroll",
                json={"scroll": scroll_ttl, "scroll_id": scroll_id},
            )
            resp.raise_for_status()
            data = resp.json()
            scroll_id = data.get("_scroll_id")
            hits = data.get("hits", {}).get("hits", [])
            if not hits:
                break
            if isinstance(hits, list):
                _consume(hits)

        if scroll_id:
            try:
                client.request(
                    "DELETE",
                    "/_search/scroll",
                    json={"scroll_id": scroll_id},
                )
            except httpx.HTTPError:
                pass

    return mapping


def fetch_opensearch_id_map(
    *,
    base_url: str,
    index: str,
    auth: tuple[str, str] | None,
    timeout_seconds: float = 60.0,
    page_size: int = 500,
    verify: bool = True,
) -> dict[str, str]:
    """Backward-compatible: catalog_key → document ``_id``."""
    records = fetch_opensearch_records(
        base_url=base_url,
        index=index,
        auth=auth,
        timeout_seconds=timeout_seconds,
        page_size=page_size,
        verify=verify,
    )
    return {key: str(entry["id"]) for key, entry in records.items()}


def reconcile_dictionary_with_opensearch(
    dictionary_records: list[dict[str, Any]],
    os_by_key: dict[str, dict[str, Any]],
    *,
    strict: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, str], ReconcileReport]:
    """Đối chiếu dictionary (nguồn tên catalog) với OpenSearch (nguồn runtime metadata).

    Catalog PostgreSQL luôn lấy tên từ ``dictionary_records``. OpenSearch dùng để:
    - gán ``opensearch_id`` / ``id`` cho manifest và metadata API;
    - phát hiện thiếu / thừa / lệch identifier trước khi ghi DB.
    """
    dict_table_keys, dict_column_keys = _catalog_seed_keys(dictionary_records)
    os_table_keys = {
        k for k, v in os_by_key.items() if _record_type(v["source"]) == "TABLE"
    }
    os_column_keys = {
        k for k, v in os_by_key.items() if _record_type(v["source"]) == "COLUMN"
    }
    catalog_keys = dict_table_keys | dict_column_keys

    missing_in_os = sorted(catalog_keys - set(os_by_key))
    extra_in_os = sorted(
        (os_table_keys | os_column_keys) - catalog_keys
    )
    identifier_mismatches: list[str] = []
    os_id_by_key: dict[str, str] = {}

    dict_by_key: dict[str, dict[str, Any]] = {}
    for rec in dictionary_records:
        key = record_catalog_key(rec)
        if key and _record_type(rec) in _CATALOG_SEED_TYPES:
            dict_by_key[key] = rec

    aligned: list[dict[str, Any]] = []
    for rec in dictionary_records:
        row = dict(rec)
        key = record_catalog_key(row)
        if key and key in os_by_key:
            os_entry = os_by_key[key]
            os_id = str(os_entry["id"])
            os_id_by_key[key] = os_id
            if key in dict_by_key and not _identifiers_match(dict_by_key[key], os_entry["source"]):
                identifier_mismatches.append(key)
            file_id = str(row.get("id") or "").strip()
            if file_id and file_id != os_id:
                row["_file_id_before_os"] = file_id
            row["id"] = os_id
            row["opensearch_id"] = os_id
        elif key and str(row.get("id") or "").strip():
            fid = str(row["id"]).strip()
            row["opensearch_id"] = fid
            if key in catalog_keys:
                os_id_by_key.setdefault(key, fid)
        aligned.append(row)

    report = ReconcileReport(
        dictionary_table_keys=len(dict_table_keys),
        dictionary_column_keys=len(dict_column_keys),
        opensearch_table_keys=len(os_table_keys),
        opensearch_column_keys=len(os_column_keys),
        aligned_table_keys=len(dict_table_keys & os_table_keys),
        aligned_column_keys=len(dict_column_keys & os_column_keys),
        missing_in_opensearch=tuple(missing_in_os),
        extra_in_opensearch=tuple(extra_in_os),
        identifier_mismatches=tuple(identifier_mismatches),
        strict=strict,
        skipped_opensearch=False,
    )
    return aligned, os_id_by_key, report


def reconcile_dictionary_only(
    dictionary_records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str], ReconcileReport]:
    """Dev mode: không có OpenSearch — catalog chỉ từ dictionary."""
    dict_table_keys, dict_column_keys = _catalog_seed_keys(dictionary_records)
    os_id_by_key: dict[str, str] = {}
    aligned: list[dict[str, Any]] = []
    for rec in dictionary_records:
        row = dict(rec)
        key = record_catalog_key(row)
        fid = str(row.get("id") or "").strip()
        if fid and key:
            row["opensearch_id"] = fid
            os_id_by_key[key] = fid
        aligned.append(row)
    report = ReconcileReport(
        dictionary_table_keys=len(dict_table_keys),
        dictionary_column_keys=len(dict_column_keys),
        opensearch_table_keys=0,
        opensearch_column_keys=0,
        aligned_table_keys=0,
        aligned_column_keys=0,
        strict=False,
        skipped_opensearch=True,
    )
    return aligned, os_id_by_key, report


def format_reconcile_report(report: ReconcileReport) -> list[str]:
    lines = [
        f"  dictionary: TABLE={report.dictionary_table_keys} COLUMN={report.dictionary_column_keys}",
        f"  opensearch: TABLE={report.opensearch_table_keys} COLUMN={report.opensearch_column_keys}",
        f"  aligned: TABLE={report.aligned_table_keys} COLUMN={report.aligned_column_keys}",
    ]
    if report.skipped_opensearch:
        lines.append("  reconcile: skipped (dictionary-only mode)")
        return lines
    if report.missing_in_opensearch:
        lines.append(f"  missing_in_opensearch ({len(report.missing_in_opensearch)}):")
        for key in report.missing_in_opensearch[:8]:
            lines.append(f"    - {key}")
        if len(report.missing_in_opensearch) > 8:
            lines.append(f"    ... +{len(report.missing_in_opensearch) - 8} more")
    if report.extra_in_opensearch:
        lines.append(f"  extra_in_opensearch ({len(report.extra_in_opensearch)}):")
        for key in report.extra_in_opensearch[:5]:
            lines.append(f"    - {key}")
        if len(report.extra_in_opensearch) > 5:
            lines.append(f"    ... +{len(report.extra_in_opensearch) - 5} more")
    if report.identifier_mismatches:
        lines.append(f"  identifier_mismatches ({len(report.identifier_mismatches)}):")
        for key in report.identifier_mismatches[:5]:
            lines.append(f"    - {key}")
    lines.append(f"  reconcile passed: {report.passed}")
    return lines


def align_records_with_opensearch(
    records: list[dict[str, Any]],
    os_id_by_key: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Legacy helper — prefer ``reconcile_dictionary_with_opensearch``."""
    warnings: list[str] = []
    aligned: list[dict[str, Any]] = []
    for rec in records:
        row = dict(rec)
        key = record_catalog_key(row)
        os_id = os_id_by_key.get(key) if key else None
        file_id = str(row.get("id") or "").strip()
        if os_id:
            if file_id and file_id != os_id:
                warnings.append(
                    f"id mismatch key={key}: file={file_id[:36]} os={os_id[:36]}"
                )
            row["id"] = os_id
            row["opensearch_id"] = os_id
        elif file_id:
            row["opensearch_id"] = file_id
        aligned.append(row)
    return aligned, warnings


def seed_gl_resource_dictionary(
    session: Session,
    records: list[dict[str, Any]],
    *,
    database_name: str = DATABASE_NAME,
    database_description: str = DATABASE_DESCRIPTION,
) -> dict[str, Any]:
    """Insert or update COREDB resource tree from agri metadata (TABLE + COLUMN)."""
    from app.repositories.resource_repo import ResourceRepository

    rr = ResourceRepository(session)
    stats: dict[str, Any] = {
        "schemas": 0,
        "tables": 0,
        "columns_created": 0,
        "columns_updated": 0,
        "table_resource_ids": [],
    }
    table_rid_by_key: dict[tuple[str, str], uuid.UUID] = {}

    def _ensure_db() -> uuid.UUID:
        rid = rr.find_database_resource_id_by_name(database_name)
        if rid is not None:
            db = rr.get_database(rid)
            if db is not None and database_description and db.description != database_description:
                db.description = database_description
            return rid
        res = rr.create_resource("DATABASE")
        rr.create_database(res.id, database_name, database_description)
        return res.id

    def _ensure_schema(db_rid: uuid.UUID, name: str) -> uuid.UUID:
        rid = rr.find_schema_resource_id(db_rid, name)
        if rid is not None:
            return rid
        res = rr.create_resource("SCHEMA")
        stats["schemas"] += 1
        return rr.create_schema(res.id, db_rid, name).resource_id

    def _ensure_table(schema_rid: uuid.UUID, name: str) -> uuid.UUID:
        rid = rr.find_table_resource_id(schema_rid, name)
        if rid is not None:
            return rid
        res = rr.create_resource("TABLE")
        stats["tables"] += 1
        return rr.create_table(res.id, schema_rid, name).resource_id

    def _ensure_column(
        table_rid: uuid.UUID,
        name: str,
        data_type: str,
        *,
        is_primary_key: bool | None,
        is_foreign_key: bool | None,
    ) -> uuid.UUID:
        col_rid = rr.find_column_resource_id(table_rid, name)
        if col_rid is None:
            res = rr.create_resource("COLUMN")
            rr.create_column(
                res.id,
                table_rid,
                name,
                data_type,
                is_primary_key=is_primary_key,
                is_foreign_key=is_foreign_key,
            )
            stats["columns_created"] += 1
            return res.id
        col = rr.get_column(col_rid)
        if col is not None:
            changed = False
            if col.data_type != data_type:
                col.data_type = data_type
                changed = True
            if col.is_primary_key != is_primary_key:
                col.is_primary_key = is_primary_key
                changed = True
            if col.is_foreign_key != is_foreign_key:
                col.is_foreign_key = is_foreign_key
                changed = True
            if changed:
                stats["columns_updated"] += 1
        return col_rid

    db_rid = _ensure_db()

    for rec in records:
        if str(rec.get("record_type") or "").upper() != "TABLE":
            continue
        schema = str(rec.get("schema_name") or "").strip()
        table = str(rec.get("table_name") or "").strip()
        if not schema or not table:
            continue
        schema_rid = _ensure_schema(db_rid, schema)
        table_rid = _ensure_table(schema_rid, table)
        table_rid_by_key[(schema, table)] = table_rid

    by_schema_table: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        if str(rec.get("record_type") or "").upper() != "COLUMN":
            continue
        schema = str(rec.get("schema_name") or "").strip()
        table = str(rec.get("table_name") or "").strip()
        column = str(rec.get("column_name") or "").strip()
        if not schema or not table or not column:
            continue
        by_schema_table[(schema, table)].append(rec)

    column_resource_ids: dict[str, uuid.UUID] = {}

    for (schema_name, table_name), cols in sorted(by_schema_table.items()):
        schema_rid = _ensure_schema(db_rid, schema_name)
        table_rid = table_rid_by_key.get((schema_name, table_name))
        if table_rid is None:
            table_rid = _ensure_table(schema_rid, table_name)
            table_rid_by_key[(schema_name, table_name)] = table_rid
        for rec in sorted(cols, key=lambda r: str(r.get("column_name", ""))):
            col_rid = _ensure_column(
                table_rid,
                str(rec["column_name"]),
                str(rec.get("data_type") or "text"),
                is_primary_key=bool(rec["is_primary_key"])
                if rec.get("is_primary_key") is not None
                else None,
                is_foreign_key=bool(rec["is_foreign_key"])
                if rec.get("is_foreign_key") is not None
                else None,
            )
            key = record_catalog_key(rec)
            if key:
                column_resource_ids[key] = col_rid

    stats["table_resource_ids"] = sorted(
        table_rid_by_key.values(),
        key=lambda x: str(x),
    )
    stats["table_rid_by_key"] = table_rid_by_key
    stats["column_resource_ids"] = column_resource_ids
    session.flush()
    return stats


def seed_describe_permissions_for_tables(
    session: Session,
    user_id: uuid.UUID,
    table_resource_ids: list[uuid.UUID],
) -> int:
    """Idempotent DESCRIBE ALLOW on each table for integration tests."""
    from app.models.identity import UserPermission
    from app.models.permission import Permission
    from app.repositories.identity_repo import IdentityRepository
    from app.repositories.permission_repo import PermissionRepository

    pr = PermissionRepository(session)
    ir = IdentityRepository(session)
    describe = pr.get_permission_type_by_name("DESCRIBE")
    if describe is None:
        raise RuntimeError("Permission type DESCRIBE not in database — run seed_demo_data first")

    existing_perm_ids = set(
        session.scalars(
            select(Permission.id)
            .join(UserPermission, UserPermission.permission_id == Permission.id)
            .where(
                UserPermission.user_id == user_id,
                Permission.permission_type_id == describe.id,
            )
        ).all()
    )
    existing_resources = set()
    if existing_perm_ids:
        existing_resources = set(
            session.scalars(
                select(Permission.resource_id).where(
                    Permission.id.in_(existing_perm_ids)
                )
            ).all()
        )

    created = 0
    for table_rid in table_resource_ids:
        if table_rid in existing_resources:
            continue
        perm = pr.create_permission(
            resource_id=table_rid,
            permission_type_id=describe.id,
            effect="ALLOW",
        )
        ir.add_user_permission(user_id, perm.id)
        created += 1
    session.flush()
    return created


def build_integration_manifest(
    records: list[dict[str, Any]],
    stats: dict[str, Any],
    *,
    opensearch_index: str,
    os_id_by_key: dict[str, str],
    describe_user_id: uuid.UUID,
    describe_grants: int,
    reconcile: ReconcileReport | None = None,
    dictionary_path: str | None = None,
) -> dict[str, Any]:
    """JSON artifact for manual / automated metadata API tests."""
    table_rid_by_key: dict[tuple[str, str], uuid.UUID] = stats.get("table_rid_by_key", {})
    column_resource_ids: dict[str, uuid.UUID] = stats.get("column_resource_ids", {})

    tables_out: list[dict[str, Any]] = []
    for (schema, table), table_rid in sorted(table_rid_by_key.items()):
        tbl_key = f"TABLE|{DATABASE_NAME}|{schema}|{table}"
        columns_out: list[dict[str, Any]] = []
        for rec in records:
            if str(rec.get("record_type") or "").upper() != "COLUMN":
                continue
            if rec.get("schema_name") != schema or rec.get("table_name") != table:
                continue
            col = str(rec.get("column_name") or "")
            ckey = f"COLUMN|{DATABASE_NAME}|{schema}|{table}|{col}"
            columns_out.append(
                {
                    "column_name": col,
                    "catalog_resource_id": str(column_resource_ids.get(ckey, "")),
                    "opensearch_id": os_id_by_key.get(ckey) or rec.get("opensearch_id"),
                    "catalog_key": ckey,
                }
            )
        tables_out.append(
            {
                "schema_name": schema,
                "table_name": table,
                "catalog_resource_id": str(table_rid),
                "opensearch_id": os_id_by_key.get(tbl_key),
                "catalog_key": tbl_key,
                "columns_sample": columns_out[:5],
                "column_count": len(columns_out),
            }
        )

    relationships: list[dict[str, Any]] = []
    for rec in records:
        if str(rec.get("record_type") or "").upper() != "RELATIONSHIP":
            continue
        key = record_catalog_key(rec)
        if not key:
            continue
        relationships.append(
            {
                "relationship_name": rec.get("relationship_name"),
                "opensearch_id": os_id_by_key.get(key) or rec.get("opensearch_id"),
                "catalog_key": key,
            }
        )

    manifest: dict[str, Any] = {
        "database_name": DATABASE_NAME,
        "opensearch_index": opensearch_index,
        "describe_user_id": str(describe_user_id),
        "describe_permissions_created": describe_grants,
        "opensearch_documents_mapped": len(os_id_by_key),
        "tables": tables_out,
        "relationships": relationships,
        "sample_metadata_requests": {
            "keyword_search_demo_user": {
                "method": "POST",
                "path": "/api/v1/metadata/keyword-search",
                "body": {
                    "userId": "demo_user",
                    "query": "journal",
                    "size": 10,
                },
            },
            "keyword_search_agri_agent": {
                "method": "POST",
                "path": "/api/v1/metadata/keyword-search",
                "body": {
                    "userId": "agri_agent",
                    "query": "journal",
                    "size": 10,
                },
            },
            "table_lookup": {
                "method": "GET",
                "path": "/api/v1/metadata/tables/GL_JOURNAL_HEADERS",
                "query": {"userId": "agri_agent", "size": 5},
            },
        },
    }
    if dictionary_path:
        manifest["dictionary_source"] = dictionary_path
    if reconcile is not None:
        manifest["reconcile"] = {
            "passed": reconcile.passed,
            "strict": reconcile.strict,
            "skipped_opensearch": reconcile.skipped_opensearch,
            "dictionary_table_keys": reconcile.dictionary_table_keys,
            "dictionary_column_keys": reconcile.dictionary_column_keys,
            "opensearch_table_keys": reconcile.opensearch_table_keys,
            "opensearch_column_keys": reconcile.opensearch_column_keys,
            "aligned_table_keys": reconcile.aligned_table_keys,
            "aligned_column_keys": reconcile.aligned_column_keys,
            "missing_in_opensearch": list(reconcile.missing_in_opensearch),
            "extra_in_opensearch": list(reconcile.extra_in_opensearch),
            "identifier_mismatches": list(reconcile.identifier_mismatches),
        }
    return manifest


def _ensure_permission_types(session: Session) -> None:
    from app.models.permission import PermissionType

    for name in ("SELECT", "USAGE", "INSERT", "UPDATE", "DELETE", "DESCRIBE"):
        if session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).first() is None:
            session.add(PermissionType(name=name))
    session.flush()


def _ensure_demo_user(session: Session, user_id: uuid.UUID) -> None:
    from app.models.identity import User

    row = session.get(User, user_id)
    if row is None:
        session.add(
            User(
                id=user_id,
                username="demo_user",
                email="demo@example.com",
                is_active=True,
            )
        )
    else:
        row.username = "demo_user"
        row.email = "demo@example.com"
        row.is_active = True
    session.flush()


def main() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError

    from app.core.config import Settings

    from scripts.demo_constants import DEMO_USER_ID

    agri_path = _resolve_agri_dictionary_script_path()
    print(f"Loading ALL_RECORDS from: {agri_path}")
    records = load_all_records_from_agri(agri_path)
    n_col = sum(1 for r in records if r.get("record_type") == "COLUMN")
    n_tbl = sum(1 for r in records if r.get("record_type") == "TABLE")
    n_rel = sum(1 for r in records if r.get("record_type") == "RELATIONSHIP")
    print(f"  records: {len(records)} (COLUMN={n_col} TABLE={n_tbl} RELATIONSHIP={n_rel})")

    settings = Settings()
    strict_reconcile = os.environ.get("STRICT_OPENSEARCH_RECONCILE", "true").strip().lower() not in (
        "0",
        "false",
        "no",
    )
    skip_os = os.environ.get("SKIP_OPENSEARCH_FETCH", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    reconcile: ReconcileReport
    os_id_by_key: dict[str, str] = {}

    if skip_os:
        print("  OpenSearch: skipped (SKIP_OPENSEARCH_FETCH)")
        records, os_id_by_key, reconcile = reconcile_dictionary_only(records)
    else:
        os_base = settings.opensearch_effective_base_url
        if not os_base:
            print(
                "\n[seed_gl_resource_dictionary] OpenSearch not configured.\n"
                "  Set OPENSEARCH_HOST/PORT or OPENSEARCH_BASE_URL in .env\n"
                "  Or set SKIP_OPENSEARCH_FETCH=true to seed catalog only.\n",
                file=sys.stderr,
            )
            raise SystemExit(1)
        print(f"  OpenSearch: {os_base} index={settings.opensearch_index}")
        try:
            os_by_key = fetch_opensearch_records(
                base_url=os_base,
                index=settings.opensearch_index,
                auth=settings.opensearch_auth,
                timeout_seconds=settings.opensearch_timeout_seconds,
                verify=settings.opensearch_verify_certs,
            )
        except httpx.HTTPError as exc:
            print(
                f"\n[seed_gl_resource_dictionary] OpenSearch request failed: {exc}\n"
                "  Ensure index exists (run agentic-agri seed_data_dictionary_1.py).\n",
                file=sys.stderr,
            )
            raise SystemExit(1) from exc
        print(f"  OpenSearch documents mapped: {len(os_by_key)}")
        records, os_id_by_key, reconcile = reconcile_dictionary_with_opensearch(
            records,
            os_by_key,
            strict=strict_reconcile,
        )

    print("  Reconcile (dictionary ↔ OpenSearch):")
    for line in format_reconcile_report(reconcile):
        print(line)

    if not reconcile.passed:
        print(
            "\n[seed_gl_resource_dictionary] Reconcile failed — catalog not seeded.\n"
            "  Fix agentic-agri dictionary / re-index OpenSearch, or set STRICT_OPENSEARCH_RECONCILE=false.\n",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if reconcile.extra_in_opensearch:
        print(
            f"  note: {len(reconcile.extra_in_opensearch)} TABLE/COLUMN keys in OpenSearch "
            "not in dictionary (ignored for catalog seed)"
        )

    describe_user = uuid.UUID(
        os.environ.get("METADATA_SEED_DESCRIBE_USER_ID", str(DEMO_USER_ID))
    )
    manifest_path = Path(
        os.environ.get("METADATA_INTEGRATION_MANIFEST", str(DEFAULT_MANIFEST))
    )

    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    try:
        try:
            _ensure_permission_types(session)
            _ensure_demo_user(session, describe_user)
            stats = seed_gl_resource_dictionary(session, records)
            describe_grants = seed_describe_permissions_for_tables(
                session,
                describe_user,
                stats["table_resource_ids"],
            )
            manifest = build_integration_manifest(
                records,
                stats,
                opensearch_index=settings.opensearch_index,
                os_id_by_key=os_id_by_key,
                describe_user_id=describe_user,
                describe_grants=describe_grants,
                reconcile=reconcile,
                dictionary_path=str(agri_path),
            )
            from scripts.seed_agri_integration_user import seed_agri_integration_user

            agri_user = seed_agri_integration_user(session)
            manifest["agri_integration_user"] = {
                "userId": agri_user["username"],
                "user_id": str(agri_user["user_id"]),
                "group": agri_user["group_name"],
                "role": agri_user["role_name"],
                "permissions_allow": agri_user["permissions"],
            }
            session.commit()
        except OperationalError as exc:
            print(
                "\n[seed_gl_resource_dictionary] PostgreSQL connection failed.\n"
                "  Start Postgres (e.g. docker compose up -d postgres) and set DATABASE_URL.\n"
                f"  URL: {settings.database_url}\n",
                file=sys.stderr,
            )
            raise SystemExit(1) from exc
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    schemas = {r["schema_name"] for r in records if r.get("schema_name")}
    tables = {
        r["table_name"]
        for r in records
        if r.get("record_type") == "COLUMN" and r.get("table_name")
    }
    print("--- Metadata integration seed OK ---")
    print(f"DATABASE={DATABASE_NAME}")
    print(f"schemas={sorted(schemas)}")
    print(f"tables={len(tables)}")
    print(
        "catalog_writes: "
        f"schemas+={stats['schemas']} tables+={stats['tables']} "
        f"columns+={stats['columns_created']} columns_updated={stats['columns_updated']}"
    )
    print(f"DESCRIBE grants created for demo_user: {describe_grants}")
    agri = manifest.get("agri_integration_user", {})
    if agri:
        print(
            f"Agri user: userId={agri.get('userId')} role={agri.get('role')} "
            f"permissions={agri.get('permissions_allow')}"
        )
    print(f"Manifest: {manifest_path}")
    print("Test agri: POST /api/v1/metadata/keyword-search  body.userId=agri_agent")


if __name__ == "__main__":
    main()
