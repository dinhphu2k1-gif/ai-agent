"""Postgres channel catalog."""

from __future__ import annotations

from api.schemas.chat import Channel
from chat.db import transaction
from chat.repositories.channel_repository import ChannelRepository


def _row_to_channel(row: tuple) -> Channel:
    return Channel(id=row[0], title=row[1], icon=row[2], category=row[3])


class PostgresChannelRepository(ChannelRepository):
    def list_all(self) -> list[Channel]:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, icon, category
                    FROM chat.chat_channels
                    WHERE is_active = TRUE
                    ORDER BY sort_order, id
                    """
                )
                rows = cur.fetchall()
        return [_row_to_channel(row) for row in rows]

    def list_for_user(self, user_id: str, channel_ids: list[str]) -> list[Channel]:
        _ = user_id
        if not channel_ids:
            return []
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, icon, category
                    FROM chat.chat_channels
                    WHERE is_active = TRUE AND id = ANY(%s)
                    ORDER BY sort_order, id
                    """,
                    (channel_ids,),
                )
                rows = cur.fetchall()
        return [_row_to_channel(row) for row in rows]

    def exists(self, channel_id: str) -> bool:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM chat.chat_channels
                    WHERE id = %s AND is_active = TRUE
                    """,
                    (channel_id,),
                )
                return cur.fetchone() is not None

    def create(self, channel: Channel) -> Channel:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(MAX(sort_order), 0) + 10
                    FROM chat.chat_channels
                    """
                )
                sort_order = cur.fetchone()[0]
                cur.execute(
                    """
                    INSERT INTO chat.chat_channels (
                        id, title, icon, category, sort_order, is_active
                    )
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    """,
                    (
                        channel.id,
                        channel.title,
                        channel.icon,
                        channel.category,
                        sort_order,
                    ),
                )
        return channel

    def soft_delete(self, channel_id: str) -> bool:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat.chat_channels
                    SET is_active = FALSE, updated_at = now()
                    WHERE id = %s AND is_active = TRUE
                    """,
                    (channel_id,),
                )
                return cur.rowcount > 0
