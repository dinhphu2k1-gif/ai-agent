from __future__ import annotations

from typing import TypeVar

from fastapi.responses import JSONResponse

from app.schemas.admin_contract import ApiErrorData, ApiResponse

T = TypeVar("T")


def ok(data: T | None = None, *, message: str = "OK") -> ApiResponse[T]:
    return ApiResponse(success=True, message=message, data=data)


def fail(
    message: str,
    *,
    code: str,
    field: str | None = None,
) -> ApiResponse[ApiErrorData]:
    return ApiResponse(
        success=False,
        message=message,
        data=ApiErrorData(code=code, field=field),
    )


def not_found(message: str = "Not found") -> JSONResponse:
    body = fail(message, code="NOT_FOUND")
    return JSONResponse(status_code=404, content=body.model_dump())


def conflict(message: str, *, code: str) -> JSONResponse:
    body = fail(message, code=code)
    return JSONResponse(status_code=409, content=body.model_dump())


def forbidden(message: str, *, code: str) -> JSONResponse:
    body = fail(message, code=code)
    return JSONResponse(status_code=403, content=body.model_dump())


def grant_validation_error(message: str, *, code: str, status: int = 400) -> JSONResponse:
    body = fail(message, code=code)
    return JSONResponse(status_code=status, content=body.model_dump())
