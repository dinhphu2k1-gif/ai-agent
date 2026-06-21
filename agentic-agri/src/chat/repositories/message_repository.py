"""Message history repository."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import math

from api.schemas.chat import Message
from chat.fixtures.seed_data import MESSAGES_BY_CHANNEL
from chat.repositories.channel_repository import ChannelRepository


@dataclass(frozen=True)
class MessagePage:
    items: list[Message]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class MessageRepository(ABC):
    @abstractmethod
    def list_by_channel(
        self,
        channel_id: str,
        page: int,
        page_size: int,
        user_id: str | None = None,
    ) -> MessagePage | None:
        """Return a page of messages, or None if channel does not exist."""

    @abstractmethod
    def channel_exists(self, channel_id: str) -> bool:
        """Return True if channel_id is known."""

    @abstractmethod
    def append_message(self, channel_id: str, message: Message) -> Message | None:
        """Append a message; return None if channel does not exist."""

    @abstractmethod
    def resolve_pending_action_prompts(self, channel_id: str) -> int:
        """Remove action_prompt messages (D2). Returns count removed."""

    @abstractmethod
    def get_by_id(self, message_id: str, user_id: str) -> Message | None:
        """Return message if visible to user (via thread channel membership)."""


class InMemoryMessageRepository(MessageRepository):
    def __init__(
        self,
        messages_by_channel: dict[str, list[Message]] | None = None,
        channel_repository: ChannelRepository | None = None,
    ) -> None:
        self._messages_by_channel = {
            channel_id: list(messages)
            for channel_id, messages in (
                messages_by_channel
                if messages_by_channel is not None
                else MESSAGES_BY_CHANNEL
            ).items()
        }
        self._channel_repository = channel_repository

    def channel_exists(self, channel_id: str) -> bool:
        if self._channel_repository is not None:
            return self._channel_repository.exists(channel_id)
        return channel_id in self._messages_by_channel

    def list_by_channel(
        self,
        channel_id: str,
        page: int,
        page_size: int,
        user_id: str | None = None,
    ) -> MessagePage | None:
        if not self.channel_exists(channel_id):
            return None

        messages = self._messages_by_channel.get(channel_id, [])
        total_items = len(messages)
        if page_size < 1:
            page_size = 50
        if page < 1:
            page = 1

        total_pages = (
            math.ceil(total_items / page_size) if total_items > 0 else 0
        )
        start = (page - 1) * page_size
        end = start + page_size
        items = messages[start:end]

        return MessagePage(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def _ensure_channel_list(self, channel_id: str) -> list[Message] | None:
        if not self.channel_exists(channel_id):
            return None
        if channel_id not in self._messages_by_channel:
            self._messages_by_channel[channel_id] = []
        return self._messages_by_channel[channel_id]

    def append_message(self, channel_id: str, message: Message) -> Message | None:
        messages = self._ensure_channel_list(channel_id)
        if messages is None:
            return None
        messages.append(message)
        return message

    def resolve_pending_action_prompts(self, channel_id: str) -> int:
        messages = self._messages_by_channel.get(channel_id)
        if not messages:
            return 0
        before = len(messages)
        self._messages_by_channel[channel_id] = [
            message for message in messages if message.sender != "action_prompt"
        ]
        return before - len(self._messages_by_channel[channel_id])

    def get_by_id(self, message_id: str, user_id: str) -> Message | None:
        _ = user_id
        for messages in self._messages_by_channel.values():
            for message in messages:
                if message.id == message_id:
                    return message
        return None
