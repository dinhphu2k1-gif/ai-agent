"""Shared column mask algorithms (preview API + runtime PDP)."""

from __future__ import annotations

import hashlib
import re
from typing import Any


def apply_partial_mask(pattern: str, sample: str) -> str:
    """FE §4.2: prefix from sample, middle X run → *, trailing X run = suffix length."""
    xs = [i for i, c in enumerate(pattern) if c in ("X", "x")]
    if not xs or not sample:
        return sample

    first_x = xs[0]
    prefix_out: list[str] = []
    si = 0
    for ch in pattern[:first_x]:
        if ch.isalnum():
            if si < len(sample):
                prefix_out.append(sample[si])
                si += 1
            else:
                prefix_out.append(ch)

    suffix_len = 0
    for ch in reversed(pattern):
        if ch in ("X", "x"):
            suffix_len += 1
        else:
            break

    mask_count = sum(1 for c in pattern if c in ("X", "x")) - suffix_len
    if mask_count < 0:
        mask_count = 0

    if si + mask_count + suffix_len > len(sample):
        masked = "*" * len(sample)
        return "".join(prefix_out) + masked[len(prefix_out) :]

    masked_mid = "*" * mask_count
    suffix = sample[-suffix_len:] if suffix_len else ""
    return "".join(prefix_out) + masked_mid + suffix


def hash_mask_digest(sample: str, hash_salt: str) -> str:
    return hashlib.sha256(f"{hash_salt}:{sample}".encode()).hexdigest()[:12]


def mask_value(
    value: Any,
    mask_type: str,
    pattern: str | None,
    *,
    hash_salt: str,
    for_preview: bool = False,
) -> Any:
    """Apply mask; NULLIFY returns None at runtime and ``\"null\"`` string in preview."""
    if value is None:
        return "null" if for_preview else None
    s = str(value)
    mt = (mask_type or "PARTIAL").strip().upper()
    if mt == "FULL":
        return "*" * max(len(s), 1)
    if mt == "NULLIFY":
        return "null" if for_preview else None
    if mt == "PARTIAL":
        pat = (pattern or "").strip()
        if not pat:
            return s
        return apply_partial_mask(pat, s)
    if mt == "CUSTOM":
        return (s[:1] + "***") if s else ""
    if mt == "HASH":
        return hash_mask_digest(s, hash_salt)
    return value


def normalize_row_filter_expression(expression: str) -> str:
    return re.sub(r"\s+", " ", (expression or "").strip()).strip()
