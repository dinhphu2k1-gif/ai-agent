"""MVP permission snapshot invalidation (architecture §10): bump monotonic version."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Iterable

from app.cache.keys import permission_snapshot_key, user_context_key
from app.cache.redis_client import UserContextCache

_lock = threading.Lock()
_permission_version: int = 1


def bump_permission_version() -> int:
    """Increment global permission config version after policy-affecting writes."""
    global _permission_version
    with _lock:
        _permission_version += 1
        return _permission_version


def get_permission_version() -> int:
    return _permission_version


def invalidate_cache_for_users(
    user_ids: Iterable[uuid.UUID],
    cache: UserContextCache | None,
) -> None:
    """Drop per-user membership/snapshot keys after policy or membership mutations."""
    if cache is None:
        return
    for user_id in user_ids:
        cache.delete(user_context_key(user_id))
        cache.delete(permission_snapshot_key(user_id))
