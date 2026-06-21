"""Epic 2: repository CRUD smoke (SQLite in-memory)."""

from sqlalchemy import select

from app.models.permission import PermissionType
from app.repositories import (
    AuditRepository,
    IdentityRepository,
    PermissionRepository,
    ResourceRepository,
)


def test_resource_tree_create_and_list(db_session):
    rr = ResourceRepository(db_session)
    r_db = rr.create_resource("DATABASE")
    rr.create_database(r_db.id, "appdb", "main db")
    r_sc = rr.create_resource("SCHEMA")
    rr.create_schema(r_sc.id, r_db.id, "public")
    assert rr.get_database(r_db.id).name == "appdb"
    assert len(rr.list_schemas_for_database(r_db.id)) == 1


def test_user_crud(db_session):
    ir = IdentityRepository(db_session)
    u = ir.create_user("alice", "a@example.com")
    assert ir.get_user(u.id).username == "alice"
    ir.update_user_email(u.id, "b@example.com")
    assert ir.get_user(u.id).email == "b@example.com"
    assert ir.delete_user(u.id) is True
    assert ir.get_user(u.id) is None


def test_permission_crud_with_select_type(db_session):
    db_session.add(PermissionType(name="SELECT"))
    db_session.flush()

    rr = ResourceRepository(db_session)
    r_db = rr.create_resource("DATABASE")
    rr.create_database(r_db.id, "db", None)
    r_sch = rr.create_resource("SCHEMA")
    rr.create_schema(r_sch.id, r_db.id, "public")
    r_tbl = rr.create_resource("TABLE")
    rr.create_table(r_tbl.id, r_sch.id, "orders")

    pt = db_session.scalars(select(PermissionType).where(PermissionType.name == "SELECT")).one()
    pr = PermissionRepository(db_session)
    perm = pr.create_permission(
        resource_id=r_tbl.id, permission_type_id=pt.id, effect="ALLOW"
    )
    assert pr.get_permission(perm.id).effect == "ALLOW"
    pr.update_permission_effect(perm.id, "DENY")
    assert pr.get_permission(perm.id).effect == "DENY"
    assert pr.delete_permission(perm.id) is True


def test_audit_repos(db_session):
    ar = AuditRepository(db_session)
    log = ar.create_access_log(
        user_id=None, resource_id=None, action="SELECT", result="ALLOW"
    )
    assert ar.get_access_log(log.id).action == "SELECT"
    pcl = ar.create_permission_change_log(
        permission_id=None,
        changed_by="admin",
        change_type="CREATE",
        detail={"x": 1},
    )
    assert ar.get_permission_change_log(pcl.id).detail == {"x": 1}
