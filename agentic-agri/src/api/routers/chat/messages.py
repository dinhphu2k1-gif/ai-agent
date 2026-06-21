"""GET/POST /api/v1/chat/channels/{channelId}/messages"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse

from api.deps import ChatContainer, get_chat_container
from api.errors import RunInProgressApiError, ValidationFailedError
from api.schemas.chat import Message, PostMessageRequest, StartRunResponse
from api.schemas.common import ApiResponse, PageableResponse
from chat.services.run_service import RunInProgressError

router = APIRouter(tags=["chat-messages"])


@router.get("/messages/{message_id}", response_model=ApiResponse[Message])
async def get_message_by_id(
    message_id: str,
    request: Request,
    container: ChatContainer = Depends(get_chat_container),
) -> ApiResponse[Message]:
    user_id = getattr(request.state, "user_id", "dev-user")
    message = container.message_service.get_message(message_id, user_id)
    return ApiResponse(success=True, message="", data=message)


def _accepts_event_stream(accept: str | None) -> bool:
    if not accept:
        return True
    lowered = accept.lower()
    return "text/event-stream" in lowered or "*/*" in lowered


@router.get(
    "/channels/{channel_id}/messages",
    response_model=PageableResponse[Message],
)
async def list_channel_messages(
    channel_id: str,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize"),
    container: ChatContainer = Depends(get_chat_container),
) -> PageableResponse[Message]:
    user_id = getattr(request.state, "user_id", "dev-user")
    return container.message_service.list_messages(
        channel_id, page=page, page_size=page_size, user_id=user_id
    )


@router.post(
    "/channels/{channel_id}/messages",
    response_model=ApiResponse[StartRunResponse],
    status_code=202,
    responses={200: {"description": "SSE stream when Accept includes text/event-stream"}},
)
async def post_channel_message(
    channel_id: str,
    body: PostMessageRequest,
    request: Request,
    accept: str | None = Header(None, alias="Accept"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    respond_async: bool = Query(False, alias="async"),
    container: ChatContainer = Depends(get_chat_container),
):
    user_id = getattr(request.state, "user_id", "dev-user")

    if respond_async or not _accepts_event_stream(accept):
        try:
            container.post_message_validator.validate(channel_id, user_id, body)
            container.run_service.check_can_start(
                channel_id,
                user_id,
                idempotency_key=idempotency_key,
            )
            data = await container.run_service.prepare_run(
                channel_id,
                user_id,
                body,
                idempotency_key=idempotency_key,
            )
            return ApiResponse(success=True, message="", data=data)
        except ValidationFailedError:
            raise
        except RunInProgressError as exc:
            raise RunInProgressApiError(
                "A run is already in progress for this channel",
                run_id=exc.run_id,
                channel_id=exc.channel_id,
            ) from exc

    try:
        container.post_message_validator.validate(channel_id, user_id, body)
        container.run_service.check_can_start(
            channel_id,
            user_id,
            idempotency_key=idempotency_key,
        )

        async def event_generator():
            async for frame in container.run_service.stream_message(
                channel_id,
                user_id,
                body,
                idempotency_key=idempotency_key,
            ):
                yield frame

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except ValidationFailedError:
        raise
    except RunInProgressError as exc:
        raise RunInProgressApiError(
            "A run is already in progress for this channel",
            run_id=exc.run_id,
            channel_id=exc.channel_id,
        ) from exc
