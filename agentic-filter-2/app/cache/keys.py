from __future__ import annotations

import uuid


def user_context_key(user_id: uuid.UUID) -> str:
    """Redis key for profile + membership (architecture §3.3)."""
    return f"user_context:{user_id}"


def permission_snapshot_key(user_id: uuid.UUID) -> str:
    """Redis key for cached permission materialization (architecture §3.3)."""
    return f"permission_snapshot:{user_id}"
