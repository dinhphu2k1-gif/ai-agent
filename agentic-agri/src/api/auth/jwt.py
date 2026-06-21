"""JWT validation for Chat API Bearer tokens."""

from __future__ import annotations

from dataclasses import dataclass

import jwt

from api.settings import get_api_settings


@dataclass(frozen=True)
class TokenClaims:
    user_id: str


class InvalidTokenError(Exception):
    pass


def decode_access_token(token: str) -> TokenClaims:
    settings = get_api_settings()
    if not settings.jwt_secret:
        raise InvalidTokenError("JWT secret is not configured")

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid or expired token") from exc

    sub = payload.get("sub")
    if not sub or not str(sub).strip():
        raise InvalidTokenError("Token missing sub claim")

    return TokenClaims(user_id=str(sub).strip())


def encode_access_token(user_id: str, *, expires_minutes: int = 60) -> str:
    """Issue HS256 JWT for tests and local dev (requires CHAT_JWT_SECRET)."""
    import time

    settings = get_api_settings()
    if not settings.jwt_secret:
        raise InvalidTokenError("JWT secret is not configured")

    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + expires_minutes * 60,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
