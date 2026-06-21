from __future__ import annotations

from collections.abc import Sequence


def combine_row_filters(exprs: Sequence[str]) -> str | None:
    """Combine row predicates with AND (architecture §7.3)."""
    cleaned = [e.strip() for e in exprs if e and e.strip()]
    if not cleaned:
        return None
    return " AND ".join(f"({e})" for e in cleaned)
