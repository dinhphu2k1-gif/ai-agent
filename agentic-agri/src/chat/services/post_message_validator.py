"""Business validation for POST /messages beyond Pydantic shape checks."""

from __future__ import annotations

from api.errors import ValidationFailedError
from api.schemas.chat import PostMessageRequest
from chat.repositories.message_repository import MessageRepository
class PostMessageValidator:
    def __init__(self, message_repository: MessageRepository) -> None:
        self._messages = message_repository

    def validate(self, channel_id: str, user_id: str, body: PostMessageRequest) -> None:
        if body.type == "text":
            content = (body.content or "").strip()
            if not content:
                raise ValidationFailedError("content must be non-empty for type text")

        if body.type == "action":
            if not body.action_id or not body.label:
                raise ValidationFailedError(
                    "actionId and label are required for type action"
                )
            self._validate_action_reply(channel_id, user_id, body)

        if body.reply_to_message_id:
            self._validate_reply_target(channel_id, user_id, body.reply_to_message_id)

    def _validate_reply_target(
        self, channel_id: str, user_id: str, reply_id: str
    ) -> None:
        page = self._messages.list_by_channel(
            channel_id, page=1, page_size=200, user_id=user_id
        )
        if page is None:
            raise ValidationFailedError("replyToMessageId references unknown context")
        known = {message.id for message in page.items}
        if reply_id not in known:
            raise ValidationFailedError(
                f"replyToMessageId not found in channel history: {reply_id}"
            )

    def _validate_action_reply(
        self, channel_id: str, user_id: str, body: PostMessageRequest
    ) -> None:
        page = self._messages.list_by_channel(
            channel_id, page=1, page_size=50, user_id=user_id
        )
        if page is None:
            raise ValidationFailedError("No channel history for action reply")

        pending = [
            message
            for message in page.items
            if message.sender == "action_prompt" and message.prompt_data
        ]
        if not pending:
            raise ValidationFailedError("No pending action prompt for this action")

        prompt = pending[-1].prompt_data
        if prompt is None:
            raise ValidationFailedError("Invalid pending prompt state")

        allowed_ids = {option.action_id for option in prompt.options}
        if body.action_id not in allowed_ids:
            raise ValidationFailedError(
                f"actionId {body.action_id!r} does not match pending prompt options"
            )
