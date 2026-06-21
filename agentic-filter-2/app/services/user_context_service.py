from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.cache.keys import user_context_key
from app.cache.redis_client import UserContextCache
from app.core.config import Settings
from app.iam.schemas import IamUserClaims
from app.repositories.identity_repo import IdentityRepository

_CACHE_PAYLOAD_VERSION = 1


class TrustedUserContextError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class UserContext:
    user_id: uuid.UUID
    username: str
    email: str
    is_active: bool
    group_ids: list[uuid.UUID]
    direct_role_ids: list[uuid.UUID]
    inherited_role_ids: list[uuid.UUID]


def build_user_context(
    session: Session,
    claims: IamUserClaims,
    cache: UserContextCache,
    ttl_seconds: int,
) -> UserContext:
    """Merge IAM claims with Permission DB membership; cache membership under §3.3 key."""
    ir = IdentityRepository(session)
    local = ir.get_user(claims.user_id)
    iam_active = claims.is_active
    db_active = True if local is None else bool(local.is_active)
    is_active = iam_active and db_active

    key = user_context_key(claims.user_id)
    raw = cache.get(key)
    if raw:
        try:
            data = json.loads(raw.decode("utf-8"))
            if data.get("v") == _CACHE_PAYLOAD_VERSION:
                return UserContext(
                    user_id=claims.user_id,
                    username=claims.username,
                    email=claims.email,
                    is_active=is_active,
                    group_ids=[uuid.UUID(x) for x in data["group_ids"]],
                    direct_role_ids=[uuid.UUID(x) for x in data["direct_role_ids"]],
                    inherited_role_ids=[uuid.UUID(x) for x in data["inherited_role_ids"]],
                )
        except (KeyError, ValueError, TypeError):
            pass

    groups = ir.list_groups_for_user(claims.user_id)
    direct_roles = ir.list_roles_for_user(claims.user_id)
    inherited_roles = ir.list_roles_inherited_via_groups(claims.user_id)

    payload = {
        "v": _CACHE_PAYLOAD_VERSION,
        "group_ids": [str(g.id) for g in groups],
        "direct_role_ids": [str(r.id) for r in direct_roles],
        "inherited_role_ids": [str(r.id) for r in inherited_roles],
    }
    cache.setex(key, ttl_seconds, json.dumps(payload).encode("utf-8"))

    return UserContext(
        user_id=claims.user_id,
        username=claims.username,
        email=claims.email,
        is_active=is_active,
        group_ids=[g.id for g in groups],
        direct_role_ids=[r.id for r in direct_roles],
        inherited_role_ids=[r.id for r in inherited_roles],
    )


def build_user_context_from_trusted_user_id(
    session: Session,
    cache: UserContextCache,
    user_id: str,
    settings: Settings,
) -> UserContext:
    """Metadata routes: trusted userId in body (no Bearer)."""
    raw = user_id.strip()
    if not raw:
        raise TrustedUserContextError(400, "VALIDATION_ERROR", "userId is required")

    ir = IdentityRepository(session)
    row = None
    try:
        uid = uuid.UUID(raw)
    except ValueError:
        row = ir.get_user_by_username(raw)
    else:
        row = ir.get_user(uid)

    if row is None:
        raise TrustedUserContextError(400, "USER_NOT_FOUND", f"User not found: {raw}")
    if not row.is_active:
        raise TrustedUserContextError(403, "FORBIDDEN", "User is inactive")

    claims = IamUserClaims(
        user_id=row.id,
        username=row.username,
        email=row.email,
        is_active=True,
    )
    return build_user_context(
        session, claims, cache, settings.user_context_ttl_seconds
    )
