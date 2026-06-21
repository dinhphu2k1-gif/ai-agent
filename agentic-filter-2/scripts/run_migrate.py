#!/usr/bin/env python3
"""Apply Alembic migrations using DATABASE_URL from repo ``.env``.

Không cần ``set`` / ``$env:`` trên CMD hay PowerShell. Chạy từ thư mục gốc repo:

  python scripts/run_migrate.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))

    from alembic import command
    from alembic.config import Config
    from sqlalchemy.exc import OperationalError

    from app.core.config import Settings

    settings = Settings()
    cfg = Config(str(ROOT / "alembic.ini"))

    print(f"DATABASE_URL (from .env): {settings.database_url}")
    print("Running: alembic upgrade head")

    try:
        command.upgrade(cfg, "head")
    except OperationalError as exc:
        print(
            "\n[run_migrate] PostgreSQL connection failed.\n"
            "  1. docker compose up -d postgres\n"
            "  2. Kiểm tra DATABASE_URL trong .env (mặc định cổng host 5433)\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    print("OK — schema at head.")


if __name__ == "__main__":
    main()
