"""PostgreSQL connection pool for chat persistence."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2 import pool
from psycopg2.extensions import connection as PgConnection

from chat.settings import get_chat_settings

_pool: pool.ThreadedConnectionPool | None = None


def get_connection_pool() -> pool.ThreadedConnectionPool:
    global _pool
    settings = get_chat_settings()
    if not settings.database_url:
        raise RuntimeError("CHAT_DATABASE_URL is not configured")
    if _pool is None:
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.database_url,
        )
    return _pool


def close_connection_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def borrow_connection() -> Generator[PgConnection, None, None]:
    pg_pool = get_connection_pool()
    conn = pg_pool.getconn()
    try:
        yield conn
    finally:
        pg_pool.putconn(conn)


@contextmanager
def transaction() -> Generator[PgConnection, None, None]:
    with borrow_connection() as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def run_migration_sql(sql_path: str) -> None:
    """Execute a migration file (used by seed script / ops)."""
    with open(sql_path, encoding="utf-8") as handle:
        sql = handle.read()
    with borrow_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
