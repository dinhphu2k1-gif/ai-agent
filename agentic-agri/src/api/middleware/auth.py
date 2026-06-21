"""Bearer JWT auth for /api/v1/chat routes."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from api.auth.jwt import InvalidTokenError, decode_access_token
from api.errors import UnauthorizedError
from api.settings import get_api_settings

CHAT_API_PREFIX = "/api/v1/chat"
DEFAULT_USER_ID = "dev-user"


class ChatAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not request.url.path.startswith(CHAT_API_PREFIX):
            return await call_next(request)

        settings = get_api_settings()
        auth_header = request.headers.get("Authorization", "")

        if settings.require_auth:
            if not auth_header.startswith("Bearer ") or not auth_header[7:].strip():
                return _unauthorized_response("Missing or invalid Authorization header")
            token = auth_header[7:].strip()
            try:
                claims = decode_access_token(token)
            except InvalidTokenError as exc:
                return _unauthorized_response(str(exc))
            request.state.user_id = claims.user_id
            return await call_next(request)

        request.state.user_id = DEFAULT_USER_ID
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token and settings.jwt_secret:
                try:
                    request.state.user_id = decode_access_token(token).user_id
                except InvalidTokenError:
                    pass
            elif token and not settings.jwt_secret:
                request.state.user_id = token

        if (
            not settings.require_auth
            and settings.allow_test_user_header
        ):
            override = request.headers.get("X-Metadata-Test-User", "").strip()
            if override:
                request.state.user_id = override

        return await call_next(request)


def _unauthorized_response(message: str) -> JSONResponse:
    err = UnauthorizedError(message)
    return JSONResponse(status_code=err.status_code, content=err.to_detail())
