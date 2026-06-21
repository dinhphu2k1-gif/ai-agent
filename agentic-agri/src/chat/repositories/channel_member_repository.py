"""Channel membership (RBAC)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from chat.fixtures.seed_data import CHANNELS
from chat.db import transaction


PARTICIPANT_ROLES = frozenset({"participant", "admin"})


class ChannelMemberRepository(ABC):
    @abstractmethod
    def list_channel_ids_for_user(self, user_id: str) -> list[str]:
        """Return channel ids the user may access."""

    @abstractmethod
    def has_participant_access(self, channel_id: str, user_id: str) -> bool:
        """True if user has participant or admin role on channel."""

    @abstractmethod
    def add_member(
        self, channel_id: str, user_id: str, *, role: str = "participant"
    ) -> None:
        """Grant user access to channel."""

    @abstractmethod
    def has_admin_access(self, channel_id: str, user_id: str) -> bool:
        """True if user has admin role on channel."""


class InMemoryChannelMemberRepository(ChannelMemberRepository):
    def __init__(
        self,
        memberships: dict[str, set[str]] | None = None,
        admin_pairs: set[tuple[str, str]] | None = None,
    ) -> None:
        if memberships is not None:
            self._memberships = memberships
        else:
            all_ids = {channel.id for channel in CHANNELS}
            self._memberships = {
                "dev-user": set(all_ids),
            }
        self._admin_pairs: set[tuple[str, str]] = admin_pairs or set()

    def list_channel_ids_for_user(self, user_id: str) -> list[str]:
        return sorted(self._memberships.get(user_id, set()))

    def has_participant_access(self, channel_id: str, user_id: str) -> bool:
        return channel_id in self._memberships.get(user_id, set())

    def add_member(
        self, channel_id: str, user_id: str, *, role: str = "participant"
    ) -> None:
        if role not in PARTICIPANT_ROLES and role != "admin":
            role = "participant"
        self._memberships.setdefault(user_id, set()).add(channel_id)
        if role == "admin":
            self._admin_pairs.add((channel_id, user_id))

    def has_admin_access(self, channel_id: str, user_id: str) -> bool:
        return (channel_id, user_id) in self._admin_pairs


class PostgresChannelMemberRepository(ChannelMemberRepository):
    def list_channel_ids_for_user(self, user_id: str) -> list[str]:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT m.channel_id
                    FROM chat.chat_channel_members m
                    JOIN chat.chat_channels c ON c.id = m.channel_id
                    WHERE m.user_id = %s
                      AND m.role IN ('participant', 'admin')
                      AND c.is_active = TRUE
                    ORDER BY c.sort_order, c.id
                    """,
                    (user_id,),
                )
                return [row[0] for row in cur.fetchall()]

    def has_participant_access(self, channel_id: str, user_id: str) -> bool:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM chat.chat_channel_members
                    WHERE channel_id = %s AND user_id = %s
                      AND role IN ('participant', 'admin')
                    """,
                    (channel_id, user_id),
                )
                return cur.fetchone() is not None

    def add_member(
        self, channel_id: str, user_id: str, *, role: str = "participant"
    ) -> None:
        if role not in PARTICIPANT_ROLES and role != "admin":
            role = "participant"
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat.chat_channel_members (channel_id, user_id, role)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (channel_id, user_id) DO UPDATE
                    SET role = EXCLUDED.role
                    """,
                    (channel_id, user_id, role),
                )

    def has_admin_access(self, channel_id: str, user_id: str) -> bool:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM chat.chat_channel_members
                    WHERE channel_id = %s AND user_id = %s AND role = 'admin'
                    """,
                    (channel_id, user_id),
                )
                return cur.fetchone() is not None
