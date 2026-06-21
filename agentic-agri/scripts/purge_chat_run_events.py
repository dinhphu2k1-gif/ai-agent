#!/usr/bin/env python3
"""Purge chat_run_events older than CHAT_RUN_EVENTS_RETENTION_DAYS."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from chat.repositories.run_event_repository import PostgresRunEventRepository
from chat.settings import get_chat_settings


def main() -> int:
    settings = get_chat_settings()
    if not settings.database_url:
        print("CHAT_DATABASE_URL is required", file=sys.stderr)
        return 1
    days = settings.run_events_retention_days
    repo = PostgresRunEventRepository()
    deleted = repo.delete_older_than_days(days)
    print(f"Deleted {deleted} run event(s) older than {days} day(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
