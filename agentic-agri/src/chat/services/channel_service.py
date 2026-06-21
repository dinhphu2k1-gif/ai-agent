"""Channel catalog service."""

from __future__ import annotations

from api.errors import ChannelNotFoundError, ValidationFailedError
from api.schemas.chat import Channel, CreateChannelRequest
from chat.channel_id import generate_channel_id
from chat.constants import (
    DEFAULT_CHANNEL_CATEGORY,
    DEFAULT_CHANNEL_ICON,
    MAX_CHANNEL_TITLE_LEN,
)
from chat.repositories.channel_member_repository import ChannelMemberRepository
from chat.repositories.channel_repository import ChannelRepository
from chat.services.channel_access_service import ChannelAccessService


class ChannelService:
    def __init__(
        self,
        channel_repository: ChannelRepository,
        member_repository: ChannelMemberRepository,
        channel_access: ChannelAccessService | None = None,
    ) -> None:
        self._channel_repository = channel_repository
        self._member_repository = member_repository
        self._channel_access = channel_access

    def list_channels(self, user_id: str) -> list[Channel]:
        channel_ids = self._member_repository.list_channel_ids_for_user(user_id)
        return self._channel_repository.list_for_user(user_id, channel_ids)

    def create_channel(
        self, user_id: str, body: CreateChannelRequest
    ) -> Channel:
        title = (body.title or "").strip()
        if not title:
            raise ValidationFailedError("title is required")
        if len(title) > MAX_CHANNEL_TITLE_LEN:
            raise ValidationFailedError(
                f"title must be at most {MAX_CHANNEL_TITLE_LEN} characters"
            )

        icon = (body.icon or "").strip() or DEFAULT_CHANNEL_ICON
        channel_id = generate_channel_id(
            title, exists=self._channel_repository.exists
        )
        channel = Channel(
            id=channel_id,
            title=title,
            icon=icon,
            category=DEFAULT_CHANNEL_CATEGORY,
        )
        self._channel_repository.create(channel)
        self._member_repository.add_member(channel_id, user_id, role="admin")
        return channel

    def delete_channel(self, channel_id: str, user_id: str) -> None:
        if self._channel_access is not None:
            self._channel_access.authorize_delete(channel_id, user_id)

        if not self._channel_repository.soft_delete(channel_id):
            raise ChannelNotFoundError(f"Channel not found: {channel_id}")
