"""API error types and JSON response helpers."""

from __future__ import annotations

from typing import Any


class ChatApiError(Exception):
    status_code: int = 400
    code: str = "CHAT_ERROR"

    def __init__(self, message: str, *, data: Any = None) -> None:
        self.message = message
        self.data = data
        super().__init__(message)

    def to_detail(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "success": False,
            "code": self.code,
            "message": self.message,
            "data": self.data,
        }
        return body


class UnauthorizedError(ChatApiError):
    status_code = 401
    code = "UNAUTHORIZED"


class ChannelNotFoundError(ChatApiError):
    status_code = 404
    code = "CHANNEL_NOT_FOUND"


class MessageNotFoundError(ChatApiError):
    status_code = 404
    code = "MESSAGE_NOT_FOUND"


class ChannelForbiddenError(ChatApiError):
    status_code = 403
    code = "CHANNEL_FORBIDDEN"


class ValidationFailedError(ChatApiError):
    status_code = 400
    code = "VALIDATION_ERROR"


class RunInProgressApiError(ChatApiError):
    status_code = 409
    code = "RUN_IN_PROGRESS"

    def __init__(
        self,
        message: str,
        *,
        run_id: str,
        channel_id: str,
    ) -> None:
        super().__init__(
            message,
            data={"runId": run_id, "channelId": channel_id},
        )
        self.run_id = run_id
        self.channel_id = channel_id


class RateLimitedError(ChatApiError):
    status_code = 429
    code = "RATE_LIMITED"

    def __init__(self, message: str, *, retry_after_sec: int) -> None:
        super().__init__(message, data={"retryAfterSec": retry_after_sec})
        self.retry_after_sec = retry_after_sec
