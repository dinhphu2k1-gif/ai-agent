"""Channel catalog repository."""

from __future__ import annotations

from abc import ABC, abstractmethod

from api.schemas.chat import Channel
from chat.fixtures.seed_data import CHANNELS


class ChannelRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Channel]:
        """Return all active channels (admin/catalog)."""

    @abstractmethod
    def list_for_user(self, user_id: str, channel_ids: list[str]) -> list[Channel]:
        """Return channels filtered to ids the user may see."""

    @abstractmethod
    def exists(self, channel_id: str) -> bool:
        """Return True if channel_id is known."""

    @abstractmethod
    def create(self, channel: Channel) -> Channel:
        """Persist a new channel."""

    @abstractmethod
    def soft_delete(self, channel_id: str) -> bool:
        """Mark channel inactive. Return False if not found or already inactive."""


class InMemoryChannelRepository(ChannelRepository):
    def __init__(self, channels: list[Channel] | None = None) -> None:
        self._channels = list(channels if channels is not None else CHANNELS)
        self._by_id = {channel.id: channel for channel in self._channels}

    def list_all(self) -> list[Channel]:
        return list(self._channels)

    def list_for_user(self, user_id: str, channel_ids: list[str]) -> list[Channel]:
        _ = user_id
        return [
            self._by_id[channel_id]
            for channel_id in channel_ids
            if channel_id in self._by_id
        ]

    def exists(self, channel_id: str) -> bool:
        return channel_id in self._by_id

    def create(self, channel: Channel) -> Channel:
        self._channels.append(channel)
        self._by_id[channel.id] = channel
        return channel

    def soft_delete(self, channel_id: str) -> bool:
        if channel_id not in self._by_id:
            return False
        del self._by_id[channel_id]
        self._channels = [c for c in self._channels if c.id != channel_id]
        return True
