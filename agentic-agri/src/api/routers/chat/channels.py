"""GET/POST/DELETE /api/v1/chat/channels"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from api.deps import ChatContainer, get_chat_container
from api.schemas.chat import Channel, CreateChannelRequest
from api.schemas.common import ApiResponse

router = APIRouter(tags=["chat-channels"])


@router.get("/channels", response_model=ApiResponse[list[Channel]])
async def list_channels(
    request: Request,
    container: ChatContainer = Depends(get_chat_container),
) -> ApiResponse[list[Channel]]:
    user_id = getattr(request.state, "user_id", "dev-user")
    channels = container.channel_service.list_channels(user_id)
    return ApiResponse(success=True, message="", data=channels)


@router.post(
    "/channels",
    response_model=ApiResponse[Channel],
    status_code=status.HTTP_201_CREATED,
)
async def create_channel(
    body: CreateChannelRequest,
    request: Request,
    container: ChatContainer = Depends(get_chat_container),
) -> ApiResponse[Channel]:
    user_id = getattr(request.state, "user_id", "dev-user")
    channel = container.channel_service.create_channel(user_id, body)
    return ApiResponse(success=True, message="", data=channel)


@router.delete(
    "/channels/{channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_channel(
    channel_id: str,
    request: Request,
    container: ChatContainer = Depends(get_chat_container),
) -> Response:
    user_id = getattr(request.state, "user_id", "dev-user")
    container.channel_service.delete_channel(channel_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
