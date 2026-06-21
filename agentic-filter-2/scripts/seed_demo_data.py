#!/usr/bin/env python3
"""Seed catalog + demo user + permissions + Postgres ``public.orders``.

Optional: nếu ``OPENSEARCH_BASE_URL`` có trong môi trường / ``.env``, tạo index OpenSearch
``customers`` (2 document, mapping ``name`` / ``tenant_id``) khớp catalog cùng tên bảng.

  pip install -e ".[dev]"
  set DATABASE_URL=postgresql+psycopg://...
  set OPENSEARCH_BASE_URL=http://127.0.0.1:9201
  python scripts/seed_demo_data.py

Idempotent: catalog không nhân đôi permission. ``public.orders`` bị **DROP** rồi tạo lại + 2 dòng mẫu.
"""
from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _db_target_summary(database_url: str) -> dict[str, object]:
    from urllib.parse import parse_qs, urlparse

    u = urlparse(database_url)
    q = parse_qs(u.query)
    dbname = (u.path or "").lstrip("/").split("?")[0] or None
    return {
        "scheme": u.scheme,
        "host": u.hostname,
        "port": u.port,
        "dbname": dbname,
        "connect_timeout": q.get("connect_timeout", [""])[0] or None,
        "sslmode": q.get("sslmode", [""])[0] or None,
    }


def _load_demo_constants():
    spec = importlib.util.spec_from_file_location(
        "demo_constants", ROOT / "scripts" / "demo_constants.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _admin_demo_id(label: str) -> uuid.UUID:
    from scripts.demo_constants import ADMIN_DEMO_NS

    return uuid.uuid5(ADMIN_DEMO_NS, label)


def seed_admin_identity_demo(session: Session) -> None:
    """Idempotent admin UI demo: 3 users, 3 roles, 3 groups + grp-de-core links (§I)."""
    from app.models.identity import Group, Role, User
    from app.models.permission import PermissionType
    from app.repositories.identity_repo import IdentityRepository

    ir = IdentityRepository(session)

    users_spec = [
        ("user-1", "john.doe", "john@example.com", "John Doe", True),
        ("user-2", "alice.smith", "alice@example.com", "Alice Smith", False),
        ("user-3", "bob.chen", "bob@example.com", "Bob Chen", True),
    ]
    user_ids: list[uuid.UUID] = []
    for key, username, email, full_name, is_active in users_spec:
        uid = _admin_demo_id(key)
        user_ids.append(uid)
        row = session.get(User, uid)
        if row is None:
            session.add(
                User(
                    id=uid,
                    username=username,
                    email=email,
                    full_name=full_name,
                    is_active=is_active,
                )
            )
        else:
            row.username = username
            row.email = email
            row.full_name = full_name
            row.is_active = is_active
    session.flush()

    roles_spec = [
        (
            "role-data-scientist-eu",
            "Data_Scientist_EU",
            "Data Pipeline Admin",
        ),
        (
            "role-marketing-analyst",
            "Marketing_Analyst",
            "Warehouse Read-Only",
        ),
        (
            "role-sysadmin-global",
            "SysAdmin_Global",
            "Platform Auditor",
        ),
    ]
    role_ids: list[uuid.UUID] = []
    for key, name, display_name in roles_spec:
        rid = _admin_demo_id(key)
        role_ids.append(rid)
        row = session.get(Role, rid)
        if row is None:
            session.add(Role(id=rid, name=name, display_name=display_name))
        else:
            row.name = name
            row.display_name = display_name
    session.flush()

    groups_spec = [
        ("grp-de-core", "Data Engineering Core", "Core data engineering team"),
        ("grp-marketing", "Marketing Analysts", None),
        ("grp-contractors", "External Contractors", None),
    ]
    group_ids: list[uuid.UUID] = []
    for key, name, description in groups_spec:
        gid = _admin_demo_id(key)
        group_ids.append(gid)
        row = session.get(Group, gid)
        if row is None:
            session.add(Group(id=gid, name=name, description=description))
        else:
            row.name = name
            row.description = description
    session.flush()

    grp_de_core = _admin_demo_id("grp-de-core")
    for rid in role_ids:
        ir.add_group_role(grp_de_core, rid)
    ir.add_user_role(user_ids[0], role_ids[0])

    for extra in ("USAGE", "INSERT", "UPDATE", "DELETE", "DESCRIBE"):
        exists = session.scalars(
            select(PermissionType.id).where(PermissionType.name == extra)
        ).first()
        if exists is None:
            session.add(PermissionType(name=extra))
    session.flush()

    seed_data_scientist_role_permissions(session)
    seed_role_catalog_permissions(session)
    seed_permission_wizard_resource_tree(session)
    seed_permission_wizard_modifier_demo(session)
    seed_grp_de_core_members(session)


def seed_permission_wizard_modifier_demo(session: Session) -> None:
    """TABLE + row_filter and COLUMN + column_mask on analytics_db tree (Phase 0.4)."""
    from app.models.permission import Permission, PermissionType
    from app.repositories.identity_repo import IdentityRepository
    from app.repositories.permission_repo import PermissionRepository
    from app.repositories.resource_repo import ResourceRepository

    rr = ResourceRepository(session)
    pr = PermissionRepository(session)
    ir = IdentityRepository(session)

    db_rid = rr.find_database_resource_id_by_name("analytics_db")
    if db_rid is None:
        return
    sch_rid = rr.find_schema_resource_id(db_rid, "public")
    if sch_rid is None:
        return
    users_tbl = rr.find_table_resource_id(sch_rid, "users")
    if users_tbl is None:
        return
    email_col = rr.find_column_resource_id(users_tbl, "email")
    if email_col is None:
        return

    select_id = session.scalars(
        select(PermissionType.id).where(PermissionType.name == "SELECT")
    ).one()
    role_id = _admin_demo_id("role-data-scientist-eu")

    specs = [
        (
            "perm-wizard-analytics-users-table",
            users_tbl,
            select_id,
            "ALLOW",
            "tenant_id = 1",
            None,
        ),
        (
            "perm-wizard-analytics-email-mask",
            email_col,
            select_id,
            "ALLOW",
            None,
            ("PARTIAL", "091-XXX-XXXX"),
        ),
    ]

    for key, resource_id, ptype_id, effect, row_expr, mask in specs:
        perm_id = _admin_demo_id(key)
        perm = session.get(Permission, perm_id)
        if perm is None:
            session.add(
                Permission(
                    id=perm_id,
                    resource_id=resource_id,
                    permission_type_id=ptype_id,
                    effect=effect,
                )
            )
        else:
            perm.resource_id = resource_id
            perm.permission_type_id = ptype_id
            perm.effect = effect
        session.flush()
        if row_expr:
            pr.upsert_row_filter(permission_id=perm_id, condition_expr=row_expr)
        if mask:
            pr.upsert_column_mask(
                permission_id=perm_id,
                mask_type=mask[0],
                mask_pattern=mask[1],
            )
        ir.add_role_permission(role_id, perm_id)
    session.flush()


def seed_grp_de_core_members(session: Session) -> None:
    """Four members on grp-de-core (contract §I grp-de-core.members)."""
    from app.models.identity import User
    from app.repositories.identity_repo import IdentityRepository

    ir = IdentityRepository(session)
    grp_de_core = _admin_demo_id("grp-de-core")
    members_spec = [
        ("member-as", "ada.smith", "ada@example.com", "Ada Smith"),
        ("member-bj", "ben.jones", "ben@example.com", "Ben Jones"),
        ("member-ec", "eva.chen", "eva@example.com", "Eva Chen"),
        ("member-jw", "jay.wu", "jay@example.com", "Jay Wu"),
    ]
    for key, username, email, full_name in members_spec:
        uid = _admin_demo_id(key)
        if session.get(User, uid) is None:
            session.add(
                User(
                    id=uid,
                    username=username,
                    email=email,
                    full_name=full_name,
                    is_active=True,
                )
            )
        ir.add_user_to_group(uid, grp_de_core)
    session.flush()


def seed_permission_wizard_resource_tree(session: Session) -> None:
    """Analytics + marketing DB tree for GET /api/v1/admin/resources/tree (§G.1)."""
    from app.repositories.resource_repo import ResourceRepository

    rr = ResourceRepository(session)

    from app.services.resource_tree_service import column_key_flags

    def _ensure_column(table_rid: uuid.UUID, name: str, dtype: str = "text") -> None:
        col_rid = rr.find_column_resource_id(table_rid, name)
        is_pk, is_fk = column_key_flags(name)
        if col_rid is not None:
            col = rr.get_column(col_rid)
            if col is not None and col.is_primary_key is None:
                col.is_primary_key = is_pk
                col.is_foreign_key = is_fk
            return
        res = rr.create_resource("COLUMN")
        rr.create_column(
            res.id,
            table_rid,
            name,
            dtype,
            is_primary_key=is_pk,
            is_foreign_key=is_fk,
        )

    def _ensure_table(schema_rid: uuid.UUID, name: str) -> uuid.UUID:
        rid = rr.find_table_resource_id(schema_rid, name)
        if rid is not None:
            return rid
        res = rr.create_resource("TABLE")
        return rr.create_table(res.id, schema_rid, name).resource_id

    def _ensure_schema(db_rid: uuid.UUID, name: str) -> uuid.UUID:
        rid = rr.find_schema_resource_id(db_rid, name)
        if rid is not None:
            return rid
        res = rr.create_resource("SCHEMA")
        return rr.create_schema(res.id, db_rid, name).resource_id

    def _ensure_db(name: str) -> uuid.UUID:
        rid = rr.find_database_resource_id_by_name(name)
        if rid is not None:
            return rid
        res = rr.create_resource("DATABASE")
        return rr.create_database(res.id, name, None).resource_id

    analytics = _ensure_db("analytics_db")
    public = _ensure_schema(analytics, "public")
    users_tbl = _ensure_table(public, "users")
    for col in ("id", "email", "created_at"):
        _ensure_column(users_tbl, col)
    events_tbl = _ensure_table(public, "events")
    for col in ("event_id", "event_type", "user_id"):
        _ensure_column(events_tbl, col)
    internal = _ensure_schema(analytics, "internal")
    _ensure_table(internal, "audit_logs")

    marketing = _ensure_db("marketing_db")
    campaigns = _ensure_schema(marketing, "campaigns")
    _ensure_table(campaigns, "ads_performance")
    session.flush()


def seed_role_catalog_permissions(session: Session) -> None:
    """Extra role permissions for effective-permissions demo (marketing + sysadmin)."""
    from app.models.identity import Role
    from app.models.permission import Permission, PermissionType
    from app.repositories.identity_repo import IdentityRepository
    from app.repositories.permission_repo import PermissionRepository
    from app.repositories.resource_repo import ResourceRepository

    ir = IdentityRepository(session)
    pr = PermissionRepository(session)
    rr = ResourceRepository(session)

    def _ptype(name: str) -> uuid.UUID:
        return session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).one()

    usage_id = _ptype("USAGE")

    def _ensure_db(name: str) -> uuid.UUID:
        rid = rr.find_database_resource_id_by_name(name)
        if rid is not None:
            return rid
        res = rr.create_resource("DATABASE")
        return rr.create_database(res.id, name, None).resource_id

    specs = [
        (
            "role-marketing-analyst",
            "Marketing_Analyst",
            "Warehouse Read-Only",
            [
                ("perm-mkt-1", "marketing_dw", usage_id, "ALLOW"),
                ("perm-mkt-2", "marketing_staging", usage_id, "ALLOW"),
                ("perm-mkt-3", "marketing_raw", usage_id, "ALLOW"),
            ],
        ),
        (
            "role-sysadmin-global",
            "SysAdmin_Global",
            "Platform Auditor",
            [
                ("perm-admin-1", "*", usage_id, "ALLOW"),
            ],
        ),
    ]

    for role_key, name, display_name, perms in specs:
        role_id = _admin_demo_id(role_key)
        if ir.get_role(role_id) is None:
            session.add(Role(id=role_id, name=name, display_name=display_name))
            session.flush()
        for perm_key, db_name, ptype_id, effect in perms:
            perm_id = _admin_demo_id(perm_key)
            db_rid = _ensure_db(db_name)
            perm = session.get(Permission, perm_id)
            if perm is None:
                session.add(
                    Permission(
                        id=perm_id,
                        resource_id=db_rid,
                        permission_type_id=ptype_id,
                        effect=effect,
                    )
                )
            else:
                perm.resource_id = db_rid
                perm.permission_type_id = ptype_id
                perm.effect = effect
            session.flush()
            ir.add_role_permission(role_id, perm_id)


def seed_data_scientist_role_permissions(session: Session) -> None:
    """Eight role permissions for role-data-scientist-eu (contract §E.6, M3.4)."""
    from app.models.identity import Role
    from app.models.permission import Permission, PermissionType
    from app.repositories.identity_repo import IdentityRepository
    from app.repositories.permission_repo import PermissionRepository
    from app.repositories.resource_repo import ResourceRepository

    role_id = _admin_demo_id("role-data-scientist-eu")
    ir = IdentityRepository(session)
    if ir.get_role(role_id) is None:
        session.add(
            Role(
                id=role_id,
                name="Data_Scientist_EU",
                display_name="Data Pipeline Admin",
            )
        )
        session.flush()
    if ir.count_permissions_for_role(role_id) >= 8:
        return

    rr = ResourceRepository(session)
    pr = PermissionRepository(session)

    def _ptype(name: str) -> uuid.UUID:
        row = session.scalars(
            select(PermissionType.id).where(PermissionType.name == name)
        ).one()
        return row

    usage_id = _ptype("USAGE")
    select_id = _ptype("SELECT")

    def _db(name: str) -> uuid.UUID:
        rid = rr.find_database_resource_id_by_name(name)
        if rid is not None:
            return rid
        res = rr.create_resource("DATABASE")
        return rr.create_database(res.id, name, None).resource_id

    def _schema(db_rid: uuid.UUID, name: str) -> uuid.UUID:
        rid = rr.find_schema_resource_id(db_rid, name)
        if rid is not None:
            return rid
        res = rr.create_resource("SCHEMA")
        return rr.create_schema(res.id, db_rid, name).resource_id

    def _table(schema_rid: uuid.UUID, name: str) -> uuid.UUID:
        rid = rr.find_table_resource_id(schema_rid, name)
        if rid is not None:
            return rid
        res = rr.create_resource("TABLE")
        return rr.create_table(res.id, schema_rid, name).resource_id

    def _column(table_rid: uuid.UUID, name: str) -> uuid.UUID:
        rid = rr.find_column_resource_id(table_rid, name)
        if rid is not None:
            return rid
        res = rr.create_resource("COLUMN")
        return rr.create_column(res.id, table_rid, name, "text").resource_id

    db_rid = _db("prod_eu_central")
    analytics = _schema(db_rid, "analytics")
    raw_events = _schema(db_rid, "raw_events")

    resources = {
        "perm-db-1": (db_rid, usage_id, "ALLOW", None, None),
        "perm-schema-1": (analytics, usage_id, "ALLOW", None, None),
        "perm-schema-2": (raw_events, usage_id, "ALLOW", None, None),
        "perm-table-1": (_table(analytics, "user_metrics_agg"), select_id, "ALLOW", None, None),
        "perm-table-2": (_table(raw_events, "pii_dump_raw"), select_id, "DENY", None, None),
        "perm-table-3": (_table(analytics, "regional_sales"), select_id, "ALLOW", "region = 'EU'", None),
        "perm-table-4": (_table(analytics, "staging_users"), select_id, "ALLOW", None, None),
        "perm-column-1": (_column(_table(analytics, "users"), "email"), select_id, "ALLOW", None, ("PARTIAL", "***@***.com")),
    }

    for key, (resource_id, ptype_id, effect, row_expr, mask) in resources.items():
        perm_id = _admin_demo_id(key)
        perm = session.get(Permission, perm_id)
        if perm is None:
            perm = Permission(
                id=perm_id,
                resource_id=resource_id,
                permission_type_id=ptype_id,
                effect=effect,
            )
            session.add(perm)
        else:
            perm.resource_id = resource_id
            perm.permission_type_id = ptype_id
            perm.effect = effect
        session.flush()
        if row_expr:
            pr.upsert_row_filter(permission_id=perm_id, condition_expr=row_expr)
        if mask:
            pr.upsert_column_mask(
                permission_id=perm_id,
                mask_type=mask[0],
                mask_pattern=mask[1],
            )
        ir.add_role_permission(role_id, perm_id)

    from app.models.identity import User

    for uid_key in ("user-1", "user-2", "user-3"):
        uid = _admin_demo_id(uid_key)
        if session.get(User, uid) is not None:
            ir.add_user_role(uid, role_id)
    session.flush()


def _physical_orders(engine) -> None:
    ddl = """
    DROP TABLE IF EXISTS public.orders CASCADE;
    CREATE TABLE public.orders (
        id integer NOT NULL PRIMARY KEY,
        name text NOT NULL,
        tenant_id integer NOT NULL
    );
    INSERT INTO public.orders (id, name, tenant_id) VALUES
        (1, 'Alice', 1),
        (2, 'Bob', 2);
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def main() -> None:
    dc = _load_demo_constants()
    from app.core.config import Settings
    from app.models.identity import User, UserPermission
    from app.models.permission import Permission, PermissionType, RowFilter
    from app.repositories.identity_repo import IdentityRepository
    from app.repositories.permission_repo import PermissionRepository
    from app.repositories.resource_repo import ResourceRepository

    from sqlalchemy.exc import OperationalError

    settings = Settings()

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session: Session = factory()
    tbl_rid = None
    cust_tbl_rid = None

    try:
        try:
            pt_id = session.scalars(
                select(PermissionType.id).where(PermissionType.name == "SELECT")
            ).one()
        except OperationalError:
            tgt = _db_target_summary(settings.database_url)
            print(
                "\n[seed_demo_data] PostgreSQL connection failed "
                f"(host={tgt.get('host')!r} port={tgt.get('port')!r} dbname={tgt.get('dbname')!r}).\n"
                "  Typical fixes:\n"
                "  - Start Postgres: docker compose up -d postgres\n"
                "  - Use the same URL as docker-compose (port 5433 on host):\n"
                "    postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db\n"
                "  - Set DATABASE_URL in .env and run this script from the repo root.\n",
                file=sys.stderr,
            )
            raise

        uid = dc.DEMO_USER_ID
        if session.get(User, uid) is None:
            session.add(
                User(
                    id=uid,
                    username="demo_user",
                    email="demo@example.com",
                    is_active=True,
                )
            )
            session.flush()
        else:
            u = session.get(User, uid)
            assert u is not None
            u.username = "demo_user"
            u.email = "demo@example.com"
            u.is_active = True

        rr = ResourceRepository(session)
        ir = IdentityRepository(session)
        pr = PermissionRepository(session)

        db_rid = rr.find_database_resource_id_by_name(dc.DATABASE_LOGICAL_NAME)
        if db_rid is None:
            r_db = rr.create_resource("DATABASE")
            rr.create_database(r_db.id, dc.DATABASE_LOGICAL_NAME, "Demo catalog")
            db_rid = r_db.id
            r_sch = rr.create_resource("SCHEMA")
            rr.create_schema(r_sch.id, db_rid, dc.SCHEMA_NAME)
            sch_rid = r_sch.id
            r_tbl = rr.create_resource("TABLE")
            rr.create_table(r_tbl.id, sch_rid, dc.TABLE_LOGICAL_NAME)
            tbl_rid = r_tbl.id
            for col_name, dtype in (("id", "int"), ("name", "text"), ("tenant_id", "int")):
                r_col = rr.create_resource("COLUMN")
                rr.create_column(r_col.id, tbl_rid, col_name, dtype)
        else:
            sch_rid = rr.find_schema_resource_id(db_rid, dc.SCHEMA_NAME)
            assert sch_rid is not None
            tbl_rid = rr.find_table_resource_id(sch_rid, dc.TABLE_LOGICAL_NAME)
            assert tbl_rid is not None

        def _perm_for_resource(resource_id) -> Permission:
            p = session.scalars(
                select(Permission).where(
                    Permission.resource_id == resource_id,
                    Permission.permission_type_id == pt_id,
                )
            ).first()
            if p is None:
                p = pr.create_permission(
                    resource_id=resource_id,
                    permission_type_id=pt_id,
                    effect="ALLOW",
                )
            return p

        def _link_user(p: Permission) -> None:
            up = session.scalars(
                select(UserPermission).where(
                    UserPermission.user_id == uid,
                    UserPermission.permission_id == p.id,
                )
            ).first()
            if up is None:
                ir.add_user_permission(uid, p.id, granted_by="seed")

        p_tbl = _perm_for_resource(tbl_rid)
        _link_user(p_tbl)
        rf = session.scalars(select(RowFilter).where(RowFilter.permission_id == p_tbl.id)).first()
        if rf is None:
            pr.create_row_filter(permission_id=p_tbl.id, condition_expr="tenant_id = 1")

        for col in ("id", "name", "tenant_id"):
            rid = rr.find_column_resource_id(tbl_rid, col)
            assert rid is not None
            p = _perm_for_resource(rid)
            _link_user(p)

        cust_tbl_rid = rr.find_table_resource_id(sch_rid, dc.OPENSEARCH_CUSTOMERS_TABLE)
        if cust_tbl_rid is None:
            r_cust = rr.create_resource("TABLE")
            rr.create_table(r_cust.id, sch_rid, dc.OPENSEARCH_CUSTOMERS_TABLE)
            cust_tbl_rid = r_cust.id
            for col_name, dtype in (("name", "text"), ("tenant_id", "int")):
                r_col = rr.create_resource("COLUMN")
                rr.create_column(r_col.id, cust_tbl_rid, col_name, dtype)
        p_cust_tbl = _perm_for_resource(cust_tbl_rid)
        _link_user(p_cust_tbl)
        rf_cust = session.scalars(
            select(RowFilter).where(RowFilter.permission_id == p_cust_tbl.id)
        ).first()
        if rf_cust is None:
            pr.create_row_filter(
                permission_id=p_cust_tbl.id, condition_expr="tenant_id = 1"
            )
        for col in ("name", "tenant_id"):
            cid = rr.find_column_resource_id(cust_tbl_rid, col)
            assert cid is not None
            p = _perm_for_resource(cid)
            _link_user(p)

        seed_admin_identity_demo(session)

        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()

    assert tbl_rid is not None
    assert cust_tbl_rid is not None
    _physical_orders(engine)
    engine.dispose()

    os_url = settings.opensearch_effective_base_url
    if os_url:
        import httpx
        from scripts.opensearch_customers_seed import (
            CUSTOMERS_INDEX,
            seed_customers_index_two_documents,
        )

        base = os_url.rstrip("/")
        with httpx.Client(
            base_url=base,
            timeout=120.0,
            auth=settings.opensearch_auth,
            verify=settings.opensearch_verify_certs,
        ) as os_client:
            seed_customers_index_two_documents(os_client)
        print(f"OpenSearch index seeded: {CUSTOMERS_INDEX} at {base}")
    else:
        print("OpenSearch: skipped (set OPENSEARCH_BASE_URL or OPENSEARCH_HOST)")

    print("--- Demo seed OK ---")
    print(f"DEMO_USER_ID={dc.DEMO_USER_ID}")
    print(f"DATABASE_LOGICAL_NAME={dc.DATABASE_LOGICAL_NAME}")
    print(f"ORDERS_TABLE_RESOURCE_ID={tbl_rid}")
    print(f"CUSTOMERS_TABLE_RESOURCE_ID={cust_tbl_rid}")
    print(f"OPENSEARCH_INDEX={dc.OPENSEARCH_CUSTOMERS_TABLE}")
    print("Row filter: tenant_id = 1 on orders + customers (Alice only in filtered results)")
    print("Physical table: public.orders (recreated)")
    print("\nOther terminal - mock IAM:")
    print("  python scripts/mock_iam_server.py")
    print("\nFull curl flow: docs/huong-dan-chay-va-curl.md")


if __name__ == "__main__":
    main()
