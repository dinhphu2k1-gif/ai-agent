"""GET /api/v1/chat/runs/{runId}/stream — SSE reconnect (P1b)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from api.deps import ChatContainer, get_chat_container
from chat.services.run_service import RunNotFoundError

router = APIRouter(tags=["chat-runs"])


def _parse_last_event_id(
    query_value: int | None,
    header_value: str | None,
) -> int:
    if query_value is not None:
        return max(0, query_value)
    if header_value:
        stripped = header_value.strip()
        if stripped.isdigit():
            return int(stripped)
    return 0


@router.get("/runs/{run_id}/stream")
async def reconnect_run_stream(
    run_id: str,
    request: Request,
    last_event_id: int | None = Query(None, alias="lastEventId"),
    last_event_header: str | None = Header(None, alias="Last-Event-ID"),
    container: ChatContainer = Depends(get_chat_container),
) -> StreamingResponse:
    cursor = _parse_last_event_id(last_event_id, last_event_header)

    try:

        user_id = getattr(request.state, "user_id", "dev-user")

        async def event_generator():
            async for frame in container.run_service.stream_run_by_id(
                run_id, user_id, cursor
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
    except RunNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": str(exc),
                "data": None,
            },
        ) from exc
