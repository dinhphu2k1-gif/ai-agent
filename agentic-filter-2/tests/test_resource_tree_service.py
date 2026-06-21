"""M5: ResourceTreeService unit tests."""

from __future__ import annotations

from app.repositories.resource_repo import ResourceRepository
from app.services.resource_tree_service import ResourceTreeService, column_key_flags


def test_column_key_flags() -> None:
    assert column_key_flags("id") == (True, None)
    assert column_key_flags("event_id") == (True, None)
    assert column_key_flags("user_id") == (None, True)
    assert column_key_flags("email") == (None, None)


def test_build_fe_tree_nested_children(db_session) -> None:
    rr = ResourceRepository(db_session)
    r_db = rr.create_resource("DATABASE")
    rr.create_database(r_db.id, "analytics_db", None)
    r_sch = rr.create_resource("SCHEMA")
    rr.create_schema(r_sch.id, r_db.id, "public")
    r_tbl = rr.create_resource("TABLE")
    rr.create_table(r_tbl.id, r_sch.id, "users")
    r_col = rr.create_resource("COLUMN")
    rr.create_column(
        r_col.id,
        r_tbl.id,
        "id",
        "int",
        is_primary_key=True,
        is_foreign_key=False,
    )
    db_session.flush()

    tree = ResourceTreeService(db_session).build_fe_tree()
    assert len(tree) == 1
    assert tree[0].type == "database"
    assert tree[0].children is not None
    col = tree[0].children[0].children[0].children[0]
    assert col.type == "column"
    assert col.is_primary_key is True
    assert col.is_foreign_key is False


def test_build_fe_tree_uses_db_foreign_key_flag(db_session) -> None:
    rr = ResourceRepository(db_session)
    r_db = rr.create_resource("DATABASE")
    rr.create_database(r_db.id, "analytics_db", None)
    r_sch = rr.create_resource("SCHEMA")
    rr.create_schema(r_sch.id, r_db.id, "public")
    r_tbl = rr.create_resource("TABLE")
    rr.create_table(r_tbl.id, r_sch.id, "orders")
    r_col = rr.create_resource("COLUMN")
    rr.create_column(
        r_col.id,
        r_tbl.id,
        "user_id",
        "uuid",
        is_primary_key=False,
        is_foreign_key=True,
    )
    db_session.flush()

    tree = ResourceTreeService(db_session).build_fe_tree()
    col = tree[0].children[0].children[0].children[0]
    assert col.name == "user_id"
    assert col.is_foreign_key is True
