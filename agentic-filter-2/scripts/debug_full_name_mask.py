"""Diagnose why FULL_NAME column mask may not apply on /sql/execute."""

from __future__ import annotations

import sys
import uuid

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.cache.redis_client import MemoryUserContextCache
from app.core.config import get_settings
from app.repositories.resource_repo import ResourceRepository
from app.services.authorization_service import (
    resolve_access,
    resolve_column_masks_for_resource,
)
from app.services.permission_resolver import DecisionType
from app.services.sql_execute_service import _first_column_mask
from app.services.user_context_service import build_user_context_from_trusted_user_id


def main() -> int:
    user_id = sys.argv[1] if len(sys.argv) > 1 else "845069b7-a70f-58f5-b8df-1e0c5682f3e0"
    settings = get_settings()
    engine = create_engine(str(settings.database_url))
    cache = MemoryUserContextCache()

    with Session(engine) as session:
        print(f"catalog_db={settings.sql_catalog_database_name}")
        print(f"user_id={user_id}\n")

        rows = session.execute(
            text(
                """
                SELECT c.resource_id, c.name, t.name AS table_name, s.name AS schema_name, d.name AS db_name
                FROM columns c
                JOIN tables t ON t.resource_id = c.table_id
                JOIN schemas s ON s.resource_id = t.schema_id
                JOIN databases d ON d.resource_id = s.database_id
                WHERE upper(t.name) = 'CIF_CUSTOMERS'
                  AND upper(c.name) LIKE '%FULL%'
                """
            )
        ).fetchall()
        print("=== CIF_CUSTOMERS FULL* columns ===")
        for r in rows:
            print(dict(r._mapping))
        if not rows:
            print("NO COLUMN — catalog missing FULL_NAME/full_name on CIF_CUSTOMERS")
            return 1

        col_rid = rows[0].resource_id
        col_name = rows[0].name

        perms = session.execute(
            text(
                """
                SELECT p.id, p.effect, pt.name AS ptype, cm.mask_type
                FROM permissions p
                JOIN permission_types pt ON pt.id = p.permission_type_id
                LEFT JOIN column_masks cm ON cm.permission_id = p.id
                WHERE p.resource_id = :rid
                """
            ),
            {"rid": col_rid},
        ).fetchall()
        print("\n=== All permissions on column resource ===")
        for p in perms:
            print(dict(p._mapping))

        uid = uuid.UUID(user_id)
        user_perms = session.execute(
            text(
                """
                WITH user_perms AS (
                    SELECT permission_id FROM user_permissions WHERE user_id = :uid
                    UNION
                    SELECT gp.permission_id FROM group_permissions gp
                    JOIN user_groups ug ON ug.group_id = gp.group_id WHERE ug.user_id = :uid
                    UNION
                    SELECT rp.permission_id FROM role_permissions rp
                    JOIN user_roles ur ON ur.role_id = rp.role_id WHERE ur.user_id = :uid
                    UNION
                    SELECT rp.permission_id FROM role_permissions rp
                    JOIN group_roles gr ON gr.role_id = rp.role_id
                    JOIN user_groups ug ON ug.group_id = gr.group_id WHERE ug.user_id = :uid
                )
                SELECT p.id, p.resource_id, p.effect, pt.name, cm.mask_type
                FROM user_perms up
                JOIN permissions p ON p.id = up.permission_id
                JOIN permission_types pt ON pt.id = p.permission_type_id
                LEFT JOIN column_masks cm ON cm.permission_id = p.id
                WHERE p.resource_id = :col_rid
                """
            ),
            {"uid": uid, "col_rid": col_rid},
        ).fetchall()
        print("\n=== User bundle rows targeting column resource ===")
        for b in user_perms:
            print(dict(b._mapping))

        try:
            uc = build_user_context_from_trusted_user_id(
                session, cache, user_id, settings
            )
        except Exception as e:
            print(f"\nUser context error: {e}")
            return 1

        rr = ResourceRepository(session)
        db_id = rr.find_database_resource_id_by_name(settings.sql_catalog_database_name)
        print(f"\ndb_id for {settings.sql_catalog_database_name}: {db_id}")

        sch_id = rr.find_schema_resource_id(db_id, "CIF") if db_id else None
        tbl_id = rr.find_table_resource_id(sch_id, "CIF_CUSTOMERS") if sch_id else None
        cid_exact = rr.find_column_resource_id(tbl_id, "FULL_NAME") if tbl_id else None
        cid_parser = rr.find_column_resource_id(tbl_id, col_name) if tbl_id else None
        print(f"tbl_id={tbl_id}")
        print(f"find_column FULL_NAME -> {cid_exact}")
        print(f"find_column {col_name!r} -> {cid_parser}")

        ttl = settings.permission_snapshot_ttl_seconds
        for label, cid in [("FULL_NAME", cid_exact), ("catalog", cid_parser)]:
            if cid is None:
                continue
            dec = resolve_access(session, uc, cid, "SELECT", cache, ttl)
            ancestors = rr.get_ancestor_resource_ids(cid)
            tbl_dec = (
                resolve_access(session, uc, tbl_id, "SELECT", cache, ttl)
                if tbl_id
                else None
            )
            runtime_masks = resolve_column_masks_for_resource(
                session, uc, cid, cache, ttl
            )
            mask = runtime_masks[0] if runtime_masks else (
                _first_column_mask(dec, tbl_dec) if tbl_dec else None
            )
            print(f"\n=== PDP {label} ({cid}) ===")
            print(f"  decision={dec.decision}")
            print(f"  SELECT column_masks={len(dec.column_masks)}")
            print(f"  runtime_masks (SELECT+DESCRIBE)={len(runtime_masks)}")
            if runtime_masks:
                print(f"  mask_type={runtime_masks[0].mask_type}")
            print(f"  ancestors={ancestors}")
            if tbl_dec:
                print(f"  table_masks={len(tbl_dec.column_masks)}")
            print(f"  effective mask -> {mask}")

        return 0


if __name__ == "__main__":
    raise SystemExit(main())
