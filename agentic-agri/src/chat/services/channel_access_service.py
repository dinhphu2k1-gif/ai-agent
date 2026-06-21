"""Authorize channel access before read/write operations."""

from __future__ import annotations

from api.errors import ChannelForbiddenError, ChannelNotFoundError
from chat.constants import SEED_CHANNEL_IDS
from chat.repositories.channel_member_repository import ChannelMemberRepository
from chat.repositories.channel_repository import ChannelRepository
from chat.settings import ChatSettings, get_chat_settings


class ChannelAccessService:
    def __init__(
        self,
        channel_repository: ChannelRepository,
        member_repository: ChannelMemberRepository,
        chat_settings: ChatSettings | None = None,
    ) -> None:
        self._channels = channel_repository
        self._members = member_repository
        self._settings = chat_settings or get_chat_settings()

    def authorize_participant(self, channel_id: str, user_id: str) -> None:
        if not self._channels.exists(channel_id):
            raise ChannelNotFoundError(f"Channel not found: {channel_id}")

        if not self._settings.enforce_channel_acl:
            return

        if not self._members.has_participant_access(channel_id, user_id):
            raise ChannelForbiddenError(
                f"Access denied for channel: {channel_id}"
            )

    def authorize_delete(self, channel_id: str, user_id: str) -> None:
        if not self._channels.exists(channel_id):
            raise ChannelNotFoundError(f"Channel not found: {channel_id}")

        if channel_id in SEED_CHANNEL_IDS:
            raise ChannelForbiddenError(
                f"Cannot delete system channel: {channel_id}"
            )

        if self._settings.enforce_channel_acl:
            if not self._members.has_admin_access(channel_id, user_id):
                raise ChannelForbiddenError(
                    f"Access denied for channel: {channel_id}"
                )
