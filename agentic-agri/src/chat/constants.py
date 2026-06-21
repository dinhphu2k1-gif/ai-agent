"""Shared chat domain constants."""

from __future__ import annotations

from chat.fixtures.seed_data import CHANNELS

SEED_CHANNEL_IDS: frozenset[str] = frozenset(channel.id for channel in CHANNELS)

DEFAULT_CHANNEL_ICON = "forum"
DEFAULT_CHANNEL_CATEGORY = "Active Channels"
MAX_CHANNEL_TITLE_LEN = 255
