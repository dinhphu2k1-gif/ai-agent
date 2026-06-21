"""HTTP OpenSearch _search executor (§3.6)."""

from __future__ import annotations

from typing import Any

import httpx


class OpenSearchExecutor:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 30.0,
        auth: tuple[str, str] | None = None,
        verify: bool = True,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._client = httpx.Client(
            base_url=self._base,
            timeout=httpx.Timeout(timeout_seconds),
            auth=auth,
            verify=verify,
        )

    def close(self) -> None:
        self._client.close()

    def search(self, index: str, body: dict[str, Any]) -> dict[str, Any]:
        path = f"/{index.strip('/')}/_search"
        resp = self._client.post(path, json=body)
        resp.raise_for_status()
        return resp.json()
