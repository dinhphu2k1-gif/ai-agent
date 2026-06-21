"""Chat persistence abstractions."""

from chat.repositories.channel_repository import (
    ChannelRepository,
    InMemoryChannelRepository,
)
from chat.repositories.message_repository import (
    InMemoryMessageRepository,
    MessageRepository,
    MessagePage,
)

__all__ = [
    "ChannelRepository",
    "InMemoryChannelRepository",
    "MessagePage",
    "MessageRepository",
    "InMemoryMessageRepository",
]
