"""Unit tests for GL / metadata integration seed helpers."""

from __future__ import annotations

import pytest

from scripts.seed_gl_resource_dictionary import (
    align_records_with_opensearch,
    reconcile_dictionary_with_opensearch,
    record_catalog_key,
)


def _table_rec(schema: str, table: str, *, doc_id: str = "t-id") -> dict:
    return {
        "record_type": "TABLE",
        "database_name": "COREDB",
        "schema_name": schema,
        "table_name": table,
        "id": doc_id,
    }


def _column_rec(schema: str, table: str, column: str, *, doc_id: str = "c-id") -> dict:
    return {
        "record_type": "COLUMN",
        "database_name": "COREDB",
        "schema_name": schema,
        "table_name": table,
        "column_name": column,
        "id": doc_id,
    }


def test_reconcile_passes_when_dictionary_matches_opensearch() -> None:
    tbl = _table_rec("GL", "GL_ACCOUNTS", doc_id="file-t")
    col = _column_rec("GL", "GL_ACCOUNTS", "ACCOUNT_ID", doc_id="file-c")
    tkey = record_catalog_key(tbl)
    ckey = record_catalog_key(col)
    assert tkey and ckey
    os_by_key = {
        tkey: {"id": "os-t", "source": dict(tbl)},
        ckey: {"id": "os-c", "source": dict(col)},
    }
    aligned, os_map, report = reconcile_dictionary_with_opensearch(
        [tbl, col], os_by_key, strict=True
    )
    assert report.passed
    assert report.dictionary_table_keys == 1
    assert report.dictionary_column_keys == 1
    assert report.missing_in_opensearch == ()
    assert aligned[0]["id"] == "os-t"
    assert aligned[1]["id"] == "os-c"
    assert os_map[tkey] == "os-t"


def test_reconcile_strict_fails_when_dictionary_missing_in_opensearch() -> None:
    col = _column_rec("GL", "GL_ACCOUNTS", "MISSING_COL")
    ckey = record_catalog_key(col)
    assert ckey
    _, _, report = reconcile_dictionary_with_opensearch([col], {}, strict=True)
    assert not report.passed
    assert ckey in report.missing_in_opensearch


def test_reconcile_warns_extra_opensearch_keys_but_passes_non_strict() -> None:
    col = _column_rec("GL", "GL_ACCOUNTS", "ACCOUNT_ID")
    extra = _column_rec("GL", "GL_ACCOUNTS", "EXTRA_COL")
    ckey = record_catalog_key(col)
    ekey = record_catalog_key(extra)
    assert ckey and ekey
    os_by_key = {
        ckey: {"id": "os-c", "source": dict(col)},
        ekey: {"id": "os-e", "source": dict(extra)},
    }
    _, _, report = reconcile_dictionary_with_opensearch([col], os_by_key, strict=False)
    assert report.passed
    assert ekey in report.extra_in_opensearch


def test_reconcile_fails_on_identifier_mismatch() -> None:
    col = _column_rec("GL", "GL_ACCOUNTS", "ACCOUNT_ID")
    ckey = record_catalog_key(col)
    assert ckey
    os_source = dict(col)
    os_source["column_name"] = "WRONG_NAME"
    os_by_key = {ckey: {"id": "os-c", "source": os_source}}
    _, _, report = reconcile_dictionary_with_opensearch([col], os_by_key, strict=True)
    assert not report.passed
    assert ckey in report.identifier_mismatches


def test_record_catalog_key_column() -> None:
    rec = {
        "record_type": "COLUMN",
        "database_name": "COREDB",
        "schema_name": "GL",
        "table_name": "GL_ACCOUNTS",
        "column_name": "ACCOUNT_ID",
    }
    assert record_catalog_key(rec) == "COLUMN|COREDB|GL|GL_ACCOUNTS|ACCOUNT_ID"


def test_record_catalog_key_table() -> None:
    rec = {
        "record_type": "TABLE",
        "database_name": "COREDB",
        "schema_name": "GL",
        "table_name": "GL_ACCOUNTS",
    }
    assert record_catalog_key(rec) == "TABLE|COREDB|GL|GL_ACCOUNTS"


def test_record_catalog_key_relationship() -> None:
    rec = {
        "record_type": "RELATIONSHIP",
        "database_name": "COREDB",
        "relationship_name": "Journal to Lines",
        "related_tables": ["GL_JOURNAL_LINES", "GL_JOURNAL_HEADERS"],
    }
    key = record_catalog_key(rec)
    assert key is not None
    assert "RELATIONSHIP|COREDB|Journal to Lines|" in key
    assert "GL_JOURNAL_HEADERS" in key
    assert "GL_JOURNAL_LINES" in key


def test_align_records_prefers_opensearch_id() -> None:
    rec = {
        "record_type": "TABLE",
        "database_name": "COREDB",
        "schema_name": "GL",
        "table_name": "GL_ACCOUNTS",
        "id": "file-uuid",
    }
    key = record_catalog_key(rec)
    assert key is not None
    os_map = {key: "os-uuid-from-cluster"}
    aligned, warnings = align_records_with_opensearch([rec], os_map)
    assert aligned[0]["id"] == "os-uuid-from-cluster"
    assert aligned[0]["opensearch_id"] == "os-uuid-from-cluster"
    assert any("mismatch" in w for w in warnings)


def test_load_all_records_from_agri_v1() -> None:
    from pathlib import Path

    from scripts.seed_gl_resource_dictionary import (
        load_all_records_from_agri,
        load_all_records_from_agri_v1,
    )

    root = Path(__file__).resolve().parents[1]
    dictionary = root.parent / "agentic-agri" / "scripts" / "seed_data_dictionary.py"
    v1 = root.parent / "agentic-agri" / "scripts" / "seed_data_dictionary_1.py"
    if not dictionary.is_file():
        pytest.skip("agentic-agri not checked out beside filter-service")

    records = load_all_records_from_agri(dictionary)
    assert len(records) > 100
    assert all(r.get("id") for r in records[:20]) if v1.is_file() else True
    assert any(r.get("record_type") == "COLUMN" for r in records)

    expected_tables = sorted(
        {
            (str(r["schema_name"]), str(r["table_name"]))
            for r in records
            if r.get("record_type") == "COLUMN"
        }
    )
    assert expected_tables == [
        ("CIF", "CIF_ACCOUNTS"),
        ("CIF", "CIF_ADDRESSES"),
        ("CIF", "CIF_CUSTOMERS"),
        ("CIF", "CIF_IDENTIFICATIONS"),
        ("GL", "GL_ACCOUNTS"),
        ("GL", "GL_BALANCES"),
        ("GL", "GL_COST_CENTERS"),
        ("GL", "GL_JOURNAL_HEADERS"),
        ("GL", "GL_JOURNAL_LINES"),
        ("GL", "GL_PERIODS"),
    ]

    if v1.is_file():
        via_alias = load_all_records_from_agri_v1(v1)
        assert {r.get("table_name") for r in via_alias if r.get("record_type") == "COLUMN"} == {
            r.get("table_name") for r in records if r.get("record_type") == "COLUMN"
        }
