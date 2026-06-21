"""POST /api/v1/chat/channels/{channelId}/attachments"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, UploadFile

from api.deps import ChatContainer, get_chat_container
from api.schemas.chat import AttachmentUploadResponse
from api.schemas.common import ApiResponse

router = APIRouter(tags=["chat-attachments"])


@router.post(
    "/channels/{channel_id}/attachments",
    response_model=ApiResponse[AttachmentUploadResponse],
    status_code=201,
)
async def upload_channel_attachment(
    channel_id: str,
    request: Request,
    file: UploadFile = File(...),
    container: ChatContainer = Depends(get_chat_container),
) -> ApiResponse[AttachmentUploadResponse]:
    user_id = getattr(request.state, "user_id", "dev-user")
    data = await container.attachment_service.upload(channel_id, user_id, file)
    return ApiResponse(success=True, message="", data=data)
