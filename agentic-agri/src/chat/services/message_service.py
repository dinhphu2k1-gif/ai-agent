"""Message history service."""

from __future__ import annotations

from api.errors import ChannelNotFoundError, MessageNotFoundError
from api.schemas.chat import Message
from api.schemas.common import PageableResponse
from chat.repositories.message_repository import MessageRepository
from chat.services.attachment_service import AttachmentService
from chat.services.channel_access_service import ChannelAccessService


class MessageService:
    def __init__(
        self,
        message_repository: MessageRepository,
        channel_access: ChannelAccessService,
        attachment_service: AttachmentService | None = None,
    ) -> None:
        self._message_repository = message_repository
        self._channel_access = channel_access
        self._attachment_service = attachment_service

    def list_messages(
        self,
        channel_id: str,
        page: int = 1,
        page_size: int = 50,
        user_id: str | None = None,
    ) -> PageableResponse[Message]:
        if not user_id:
            user_id = "dev-user"
        self._channel_access.authorize_participant(channel_id, user_id)

        result = self._message_repository.list_by_channel(
            channel_id, page=page, page_size=page_size, user_id=user_id
        )
        if result is None:
            raise ChannelNotFoundError(f"Channel not found: {channel_id}")

        return PageableResponse[Message](
            success=True,
            message="",
            data=result.items,
            current_page=result.page,
            total_items=result.total_items,
            total_pages=result.total_pages,
        )

    def get_message(self, message_id: str, user_id: str) -> Message:
        if not user_id:
            user_id = "dev-user"
        message = self._message_repository.get_by_id(message_id, user_id)
        if message is None:
            raise MessageNotFoundError(f"Message not found: {message_id}")
        if self._attachment_service:
            attachments = self._attachment_service.metadata_for_message(message_id)
            if attachments:
                return message.model_copy(update={"attachments": attachments})
        return message
