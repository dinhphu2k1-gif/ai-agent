"""Diagnose why GL_ACCOUNTS metadata is visible when GL schema read is not configured."""

from __future__ import annotations

import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.cache.redis_client import MemoryUserContextCache
from app.core.config import get_settings
from app.repositories.resource_repo import ResourceRepository
from app.services.authorization_service import resolve_access
from app.services.user_context_service import build_user_context_from_trusted_user_id


def main() -> int:
    user_id = uuid.UUID("845069b7-a70f-58f5-b8df-1e0c5682f3e0")
    settings = get_settings()
    engine = create_engine(str(settings.database_url))
    cache = MemoryUserContextCache()

    with Session(engine) as session:
        user_ctx = build_user_context_from_trusted_user_id(
            session, cache, str(user_id), settings
        )
        print(f"catalog_db={settings.sql_catalog_database_name}")
        print(f"user_id={user_id}")
        print(f"roles={user_ctx.direct_role_ids} groups={user_ctx.group_ids}\n")

        rows = session.execute(
            text(
                """
                SELECT r.resource_type,
                       COALESCE(d.name, d2.name) AS db,
                       s.name AS schema,
                       t.name AS table,
                       c.name AS column,
                       pt.name AS ptype,
                       p.effect
                FROM permissions p
                JOIN permission_types pt ON pt.id = p.permission_type_id
                JOIN resources r ON r.id = p.resource_id
                LEFT JOIN databases d ON d.resource_id = p.resource_id
                LEFT JOIN schemas s ON s.resource_id = p.resource_id
                LEFT JOIN tables t ON t.resource_id = p.resource_id
                LEFT JOIN columns c ON c.resource_id = p.resource_id
                LEFT JOIN schemas s2 ON s2.resource_id = t.schema_id
                LEFT JOIN databases d2 ON d2.resource_id = s2.database_id
                WHERE p.id IN (
                    SELECT permission_id FROM user_permissions WHERE user_id = :uid
                    UNION SELECT permission_id FROM role_permissions WHERE role_id IN (
                        SELECT role_id FROM user_roles WHERE user_id = :uid
                    )
                    UNION SELECT permission_id FROM group_permissions WHERE group_id IN (
                        SELECT group_id FROM user_groups WHERE user_id = :uid
                    )
                )
                AND (
                    s.name = 'GL'
                    OR t.name = 'GL_ACCOUNTS'
                    OR d.name = :db
                )
                ORDER BY r.resource_type, pt.name
                """
            ),
            {"uid": user_id, "db": settings.sql_catalog_database_name},
        ).fetchall()

        print("=== Permissions on GL / GL_ACCOUNTS / DATABASE ===")
        if not rows:
            print("(none matched)")
        for r in rows:
            print(dict(r._mapping))

        rr = ResourceRepository(session)
        db_id = rr.find_database_resource_id_by_name(settings.sql_catalog_database_name)
        schema_id = rr.find_schema_resource_id(db_id, "GL") if db_id else None
        table_id = rr.find_table_resource_id(schema_id, "GL_ACCOUNTS") if schema_id else None
        print(f"\nresource ids: db={db_id} schema GL={schema_id} table GL_ACCOUNTS={table_id}")

        ttl = settings.permission_snapshot_ttl_seconds
        for label, rid in [("SCHEMA GL", schema_id), ("TABLE GL_ACCOUNTS", table_id)]:
            if not rid:
                continue
            ancestors = rr.get_ancestor_resource_ids(rid)
            print(f"\n{label} ancestors={ancestors}")
            for action in ("DESCRIBE", "SELECT", "USAGE"):
                dec = resolve_access(session, user_ctx, rid, action, cache, ttl)
                print(f"  {action}: {dec.decision.value} deny_reason={dec.deny_reason}")

        if table_id:
            cols = rr.list_columns_for_table(table_id)[:5]
            print("\n=== Sample column DESCRIBE decisions ===")
            for col in cols:
                dec = resolve_access(session, user_ctx, col.resource_id, "DESCRIBE", cache, ttl)
                print(f"  {col.name}: {dec.decision.value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
