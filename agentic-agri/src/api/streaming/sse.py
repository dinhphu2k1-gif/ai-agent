"""Server-Sent Events formatting (spec §5.1)."""

from __future__ import annotations

import json


def format_sse(event: str, data: dict, event_id: str | None = None) -> str:
    """Return one SSE frame: optional id, event name, single-line JSON data, blank line."""
    lines: list[str] = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    lines.append(f"data: {payload}")
    lines.append("")
    return "\n".join(lines) + "\n"


def format_sse_comment(text: str = "ping") -> str:
    """SSE comment line for keep-alive (proxies may ignore)."""
    return f": {text}\n\n"
