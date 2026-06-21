#!/usr/bin/env python3
"""Quick Phase 0 verification against DATABASE_URL (Postgres)."""
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from app.core.config import Settings

    settings = Settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        types = [
            r[0]
            for r in conn.execute(
                text("SELECT name FROM permission_types ORDER BY name")
            )
        ]
        print("permission_types:", types)
        assert "SELECT" in types
        assert "DESCRIBE" in types

        uq = conn.execute(
            text(
                """
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_row_filters_permission_id'
                """
            )
        ).first()
        print("uq_row_filters_permission_id:", bool(uq))
        assert uq is not None

        demos = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM permissions p
                JOIN row_filters rf ON rf.permission_id = p.id
                """
            )
        ).scalar()
        masks = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM permissions p
                JOIN column_masks cm ON cm.permission_id = p.id
                """
            )
        ).scalar()
        print("permissions_with_row_filter:", demos)
        print("permissions_with_column_mask:", masks)
        assert demos and demos > 0
        assert masks and masks > 0

        tree = conn.execute(
            text(
                """
                SELECT d.name FROM databases d
                WHERE d.name = 'analytics_db'
                """
            )
        ).first()
        print("analytics_db:", tree is not None)
        assert tree is not None

    print("Phase 0 DB verification OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
