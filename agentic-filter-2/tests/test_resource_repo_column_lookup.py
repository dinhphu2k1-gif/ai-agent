"""Column catalog lookup for SQL execute (case sensitivity)."""

from __future__ import annotations

import uuid

from app.repositories.resource_repo import ResourceRepository


def test_find_column_resource_id_case_insensitive(db_session) -> None:
    rr = ResourceRepository(db_session)
    db_res = rr.create_resource("DATABASE")
    rr.create_database(db_res.id, "test_db_ci", None)
    sch_res = rr.create_resource("SCHEMA")
    rr.create_schema(sch_res.id, db_res.id, "public")
    tbl_res = rr.create_resource("TABLE")
    rr.create_table(tbl_res.id, sch_res.id, "demo_t")

    col_res = rr.create_resource("COLUMN")
    rr.create_column(col_res.id, tbl_res.id, "full_name", "text")
    db_session.flush()

    found = rr.find_column_resource_id(tbl_res.id, "FULL_NAME")
    assert found == col_res.id
