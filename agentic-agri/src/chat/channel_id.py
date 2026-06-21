"""Generate URL-safe channel ids from titles."""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable


def generate_channel_id(title: str, *, exists: Callable[[str], bool]) -> str:
    """Slugify title and append random suffix; retry on collision."""
    base = re.sub(r"[^a-z0-9]+", "-", title.lower().strip())
    base = base.strip("-")[:40] or "channel"
    for _ in range(8):
        candidate = f"{base}-{secrets.token_hex(2)}"
        if not exists(candidate):
            return candidate
    return f"{base}-{secrets.token_hex(4)}"
