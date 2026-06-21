"""HTTP error model aligned with architecture_plan §12 (subset for Epic 1)."""

from enum import StrEnum
from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    BAD_REQUEST = "bad_request"
    UNSUPPORTED_QUERY = "unsupported_query"
    BAD_GATEWAY = "bad_gateway"
    GATEWAY_TIMEOUT = "gateway_timeout"
    INTERNAL = "internal_error"


class ErrorBody(BaseModel):
    code: str = Field(..., description="Stable machine-readable code")
    message: str = Field(..., description="Human-readable message")
    detail: dict[str, Any] | None = None


def error_response(
    *,
    status_code: int,
    code: ErrorCode,
    message: str,
    detail: dict[str, Any] | None = None,
) -> JSONResponse:
    body = ErrorBody(code=code.value, message=message, detail=detail).model_dump(
        exclude_none=True
    )
    return JSONResponse(status_code=status_code, content=body)
