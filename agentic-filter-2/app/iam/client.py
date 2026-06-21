from __future__ import annotations

import time
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.iam.schemas import IamUserClaims

__all__ = ["IamInvalidTokenError", "IamUnavailableError", "IamHttpClient", "IamUserClaims"]


class IamInvalidTokenError(Exception):
    """IAM rejected the token (caller maps to HTTP 401)."""


class IamUnavailableError(Exception):
    """IAM unreachable or error (caller maps to HTTP 502/504)."""


class _OptionalCircuitBreaker:
    """After N consecutive failures, open for cooldown seconds."""

    def __init__(self, *, failure_threshold: int = 5, cooldown_seconds: float = 30.0) -> None:
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._failures = 0
        self._open_until: float = 0.0

    def allow(self) -> bool:
        return time.monotonic() >= self._open_until

    def record_success(self) -> None:
        self._failures = 0
        self._open_until = 0.0

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._failure_threshold:
            self._open_until = time.monotonic() + self._cooldown_seconds
            self._failures = 0


class IamHttpClient:
    """Synchronous IAM validate client (httpx); safe to call from threadpool in async routes."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.Client | None = None,
        circuit_breaker: _OptionalCircuitBreaker | None = None,
    ) -> None:
        self._settings = settings
        self._owns_client = client is None
        timeout = httpx.Timeout(settings.iam_timeout_seconds)
        self._client = client or httpx.Client(
            base_url=str(settings.iam_base_url).rstrip("/"),
            timeout=timeout,
            follow_redirects=False,
        )
        self._path = settings.iam_token_validate_path
        self._max_retries = max(0, settings.iam_max_retries)
        self._breaker: _OptionalCircuitBreaker | None = circuit_breaker
        if settings.iam_circuit_breaker_enabled:
            self._breaker = self._breaker or _OptionalCircuitBreaker()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def validate_bearer_token(self, access_token: str) -> IamUserClaims:
        if self._breaker is not None and not self._breaker.allow():
            raise IamUnavailableError("IAM circuit breaker open")

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                claims = self._do_validate(access_token)
                if self._breaker is not None:
                    self._breaker.record_success()
                return claims
            except IamInvalidTokenError:
                raise
            except IamUnavailableError as e:
                last_error = e
                if attempt >= self._max_retries:
                    break
            except httpx.TimeoutException as e:
                last_error = e
                if attempt >= self._max_retries:
                    break
            except (httpx.ConnectError, httpx.NetworkError) as e:
                last_error = e
                if attempt >= self._max_retries:
                    break
            except httpx.RequestError as e:
                last_error = e
                if attempt >= self._max_retries:
                    break

        if self._breaker is not None:
            self._breaker.record_failure()
        if isinstance(last_error, httpx.TimeoutException):
            raise IamUnavailableError("IAM request timed out") from last_error
        if last_error is not None:
            raise IamUnavailableError("IAM request failed") from last_error
        raise IamUnavailableError("IAM request failed")

    def _do_validate(self, access_token: str) -> IamUserClaims:
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = self._client.get(self._path, headers=headers)
        except httpx.TimeoutException:
            raise
        except (httpx.ConnectError, httpx.NetworkError) as e:
            raise IamUnavailableError("IAM network error") from e
        except httpx.RequestError as e:
            raise IamUnavailableError("IAM transport error") from e

        if response.status_code in (401, 403):
            raise IamInvalidTokenError("IAM rejected token")
        if response.status_code >= 500:
            raise IamUnavailableError(f"IAM status {response.status_code}")
        if response.status_code >= 400:
            raise IamUnavailableError(f"IAM unexpected status {response.status_code}")

        try:
            payload: dict[str, Any] = response.json()
        except ValueError as e:
            raise IamUnavailableError("IAM returned non-JSON body") from e

        try:
            return IamUserClaims.model_validate(payload)
        except ValidationError as e:
            raise IamInvalidTokenError("IAM payload invalid") from e
