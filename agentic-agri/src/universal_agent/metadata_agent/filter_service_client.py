"""
HTTP client for filter-service metadata API (/api/v1/metadata/*).
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

import httpx

from ..config import FILTER_SERVICE_BASE_URL, FILTER_SERVICE_TIMEOUT_SEC
from .opensearch_client import OpenSearchClient


class FilterServiceError(Exception):
    """Raised when filter-service returns success=false or HTTP error."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "UPSTREAM_ERROR",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message


class FilterServiceClient:
    """Metadata retrieval via filter-service (permission-filtered OpenSearch)."""

    _API_PREFIX = "/api/v1/metadata"

    def __init__(
        self,
        user_id: str,
        thread_id: str | None = None,
        *,
        base_url: str | None = None,
        timeout_sec: float | None = None,
    ) -> None:
        self._user_id = user_id
        self._thread_id = thread_id
        self._base_url = (base_url or FILTER_SERVICE_BASE_URL or "").rstrip("/")
        self._timeout = timeout_sec if timeout_sec is not None else FILTER_SERVICE_TIMEOUT_SEC
        if not self._base_url:
            raise ValueError("FILTER_SERVICE_BASE_URL is required for FilterServiceClient")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Request-Id": str(uuid.uuid4()),
        }

    def _user_payload(self) -> dict[str, str]:
        payload: dict[str, str] = {"userId": self._user_id}
        if self._thread_id:
            payload["threadId"] = self._thread_id
        return payload

    def _normalize_hits(self, hits: list[Any]) -> list[dict]:
        normalized: list[dict] = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            if "_source" in hit:
                normalized.append(hit)
                continue
            source = hit.get("source") or hit.get("_source") or {}
            normalized.append(
                {
                    "_id": hit.get("_id") or hit.get("id"),
                    "_score": hit.get("_score") or hit.get("score"),
                    "_source": source,
                }
            )
        return normalized

    def _parse_search_response(self, payload: dict) -> list[dict]:
        if not payload.get("success"):
            err = payload.get("error") or {}
            raise FilterServiceError(
                err.get("message") or "Filter service error",
                code=str(err.get("code") or "UPSTREAM_ERROR"),
            )
        data = payload.get("data") or {}
        hits = data.get("hits") or []
        warnings = data.get("warnings") or []
        if warnings:
            for w in warnings:
                code = w.get("code", "")
                msg = w.get("message", "")
                print(f"⚠️ [FilterService] {code}: {msg} (userId={self._user_id})")
        return self._normalize_hits(hits)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        url = f"{self._base_url}{path}"
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.request(
                        method,
                        url,
                        headers=self._headers(),
                        json=json_body,
                        params=params,
                    )
                if response.status_code in (502, 504) and attempt < 2:
                    continue
                if response.status_code >= 400:
                    try:
                        body = response.json()
                        err = body.get("error") or {}
                        raise FilterServiceError(
                            err.get("message") or response.text,
                            code=str(err.get("code") or "UPSTREAM_ERROR"),
                            status_code=response.status_code,
                        )
                    except FilterServiceError:
                        raise
                    except Exception:
                        raise FilterServiceError(
                            response.text or f"HTTP {response.status_code}",
                            status_code=response.status_code,
                        ) from None
                return response.json()
            except httpx.TimeoutException as e:
                last_exc = e
                if attempt < 2:
                    continue
                raise FilterServiceError(
                    "Filter service request timed out",
                    code="TIMEOUT",
                ) from e
            except httpx.ConnectError as e:
                raise FilterServiceError(
                    f"Cannot connect to filter-service at {url}. "
                    f"Check FILTER_SERVICE_BASE_URL (default for agentic-filter-2 is "
                    f"http://127.0.0.1:8000) and ensure the service is running: {e}",
                    code="UPSTREAM_ERROR",
                ) from e
            except httpx.HTTPError as e:
                last_exc = e
                if attempt < 2:
                    continue
                raise FilterServiceError(
                    f"Filter service request failed ({url}): {e}",
                    code="UPSTREAM_ERROR",
                ) from e
        raise FilterServiceError(
            f"Filter service request failed after retries: {last_exc}",
            code="UPSTREAM_ERROR",
        )

    def hybrid_search(
        self,
        query_text: str,
        record_type: Optional[str] = None,
        size: int = 10,
    ) -> list[dict]:
        _ = record_type
        body = {**self._user_payload(), "query": query_text, "size": size}
        payload = self._request(
            "POST", f"{self._API_PREFIX}/hybrid-search", json_body=body
        )
        return self._parse_search_response(payload)

    def search_by_keyword(
        self,
        query: str,
        record_type: Optional[str] = None,
        table_name: Optional[str] = None,
        size: int = 10,
    ) -> list[dict]:
        _ = record_type, table_name
        body = {**self._user_payload(), "query": query, "size": size}
        payload = self._request(
            "POST", f"{self._API_PREFIX}/keyword-search", json_body=body
        )
        return self._parse_search_response(payload)

    def get_table_schema(self, table_name: str) -> list[dict]:
        params = {"userId": self._user_id}
        if self._thread_id:
            params["threadId"] = self._thread_id
        payload = self._request(
            "GET",
            f"{self._API_PREFIX}/tables/{table_name}/columns",
            params=params,
        )
        return self._parse_search_response(payload)

    def get_table_metadata(self, table_name: str) -> list[dict]:
        params = {"userId": self._user_id}
        if self._thread_id:
            params["threadId"] = self._thread_id
        payload = self._request(
            "GET",
            f"{self._API_PREFIX}/tables/{table_name}",
            params=params,
        )
        return self._parse_search_response(payload)

    def get_relationships(self, table_names: list[str]) -> list[dict]:
        body = {
            **self._user_payload(),
            "tableNames": table_names,
            "size": 20,
        }
        payload = self._request(
            "POST", f"{self._API_PREFIX}/relationships", json_body=body
        )
        return self._parse_search_response(payload)

    @staticmethod
    def format_search_results(hits: list[dict]) -> str:
        return OpenSearchClient.format_search_results(hits)
