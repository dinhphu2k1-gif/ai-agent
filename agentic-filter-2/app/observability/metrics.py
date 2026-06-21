"""In-process counters for runtime (§13 MVP)."""

from __future__ import annotations

import threading
from typing import Any

_lock = threading.Lock()
_counts: dict[str, float] = {
    "runtime_requests": 0.0,
    "runtime_denies": 0.0,
    "masking_calls": 0.0,
    "masking_ms_total": 0.0,
}


def inc_runtime_request() -> None:
    with _lock:
        _counts["runtime_requests"] += 1.0


def inc_runtime_deny() -> None:
    with _lock:
        _counts["runtime_denies"] += 1.0


def record_masking_duration_ms(ms: float) -> None:
    with _lock:
        _counts["masking_calls"] += 1.0
        _counts["masking_ms_total"] += max(0.0, ms)


def metrics_snapshot() -> dict[str, Any]:
    with _lock:
        return dict(_counts)


def reset_metrics_for_tests() -> None:
    with _lock:
        for k in _counts:
            _counts[k] = 0.0
