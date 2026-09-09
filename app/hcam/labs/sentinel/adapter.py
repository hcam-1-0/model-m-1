from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

import httpx

from hcam.labs.sentinel.models import (
    CatalogValidationError,
    ExactNetworkPolicy,
    NormalizedCatalog,
    normalize_catalog_document,
)
from hcam.labs.sentinel.secrets import (
    CatalogSecretProvider,
    SecretResolutionError,
    UnconfiguredSecretProvider,
)
from hcam.labs.sentinel.store import CatalogStore, CatalogStoreError


class CatalogAdapterError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class RefreshResult:
    refresh_id: str
    status: str
    snapshot_id: str | None
    fingerprint: str | None
    record_count: int
    warning_count: int
    unchanged: bool
    reconciliation: dict[str, object] | None


class SentinelCatalogAdapter:
    """Bounded read-only catalogue client for Phase 2.5 Sentinel sources."""

    def __init__(
        self,
        store: CatalogStore,
        network_policy: ExactNetworkPolicy,
        *,
        secret_provider: CatalogSecretProvider | None = None,
        max_response_bytes: int = 1024 * 1024,
        max_records: int = 500,
        timeout_seconds: float = 20,
        transport: httpx.AsyncBaseTransport | None = None,
        verify: bool | str = True,
        retry_delays: tuple[float, ...] = (0.0, 0.05, 0.2),
        candidate_health_resolver: Callable[
            [NormalizedCatalog], Awaitable[Mapping[str, bool]]
        ]
        | None = None,
    ) -> None:
        if not 1024 <= max_response_bytes <= 16 * 1024 * 1024:
            raise ValueError("max_response_bytes is outside the accepted lab range")
        if not 1 <= max_records <= 500:
            raise ValueError("max_records is outside the accepted Phase 2.5 range")
        if not 0 < timeout_seconds <= 60:
            raise ValueError("timeout_seconds is outside the accepted lab range")
        if not 1 <= len(retry_delays) <= 3 or any(
            delay < 0 or delay > 120 for delay in retry_delays
        ):
            raise ValueError("retry schedule is outside the accepted lab range")
        self.store = store
        self.network_policy = network_policy
        self.secret_provider = secret_provider or UnconfiguredSecretProvider()
        self.max_response_bytes = max_response_bytes
        self.max_records = max_records
        self.timeout_seconds = timeout_seconds
        self.transport = transport
        self.verify = verify
        self.retry_delays = retry_delays
        self.candidate_health_resolver = candidate_health_resolver

    async def refresh(
        self,
        source_id: str,
        *,
        requester: str,
        reason: str,
        candidate_health: Mapping[str, bool] | None = None,
    ) -> RefreshResult:
        source = self.store.get_source_config(source_id)
        if source is None:
            raise CatalogAdapterError("source_not_found")
        if not source.enabled:
            raise CatalogAdapterError("source_disabled")
        locator = self.network_policy.validate(
            source.catalog_locator,
            origin=source.catalog_locator,
            role="fallback",
        ).locator
        if not locator.startswith(("http://", "https://")):
            raise CatalogAdapterError("catalog_scheme_not_allowed")
        refresh_id = self.store.begin_refresh(
            source_id, requester=requester, reason=reason
        )
        try:
            headers, auth = self._authentication(source.auth_mode, source.secret_ref)
            if source.etag:
                headers["If-None-Match"] = source.etag
            response_status, payload, etag = await self._request(locator, headers, auth)
            if response_status == 304:
                summary = self.store.summary(source_id)
                latest = summary["latest_snapshot"]
                snapshot_id = (
                    latest["snapshot_id"] if isinstance(latest, dict) else None
                )
                count = int(summary["counts"]["total"])  # type: ignore[index]
                self.store.complete_refresh(
                    refresh_id,
                    snapshot_id=snapshot_id,
                    response_bytes=0,
                    record_count=count,
                    etag=etag,
                    unchanged=True,
                )
                return RefreshResult(
                    refresh_id, "succeeded", snapshot_id, None, count, 0, True, None
                )
            try:
                document: Any = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CatalogAdapterError("invalid_catalog_json") from exc
            catalog = normalize_catalog_document(
                document,
                origin=locator,
                network_policy=self.network_policy,
                max_records=self.max_records,
            )
            if not catalog.cameras:
                # A valid empty upstream inventory is observable, but never deletes
                # the last known-good catalogue merely because it is temporarily empty.
                summary = self.store.summary(source_id)
                latest = summary["latest_snapshot"]
                snapshot_id = (
                    str(latest["snapshot_id"])
                    if isinstance(latest, dict) and latest.get("snapshot_id")
                    else None
                )
                self.store.complete_refresh(
                    refresh_id,
                    snapshot_id=snapshot_id,
                    response_bytes=len(payload),
                    record_count=0,
                    etag=etag,
                )
                return RefreshResult(
                    refresh_id, "succeeded", snapshot_id, None, 0, 0, False, None
                )
            if candidate_health is None and self.candidate_health_resolver is not None:
                try:
                    candidate_health = await self.candidate_health_resolver(catalog)
                except CatalogAdapterError:
                    raise
                except Exception as exc:
                    raise CatalogAdapterError("candidate_health_unavailable") from exc
            reconciliation = self.store.apply_snapshot(
                source_id,
                catalog,
                candidate_health=candidate_health,
            )
            snapshot_id = str(reconciliation["snapshot_id"])
            self.store.complete_refresh(
                refresh_id,
                snapshot_id=snapshot_id,
                response_bytes=len(payload),
                record_count=len(catalog.cameras),
                etag=etag,
            )
            return RefreshResult(
                refresh_id=refresh_id,
                status="succeeded",
                snapshot_id=snapshot_id,
                fingerprint=catalog.fingerprint,
                record_count=len(catalog.cameras),
                warning_count=catalog.warning_count,
                unchanged=False,
                reconciliation=reconciliation,
            )
        except (
            CatalogAdapterError,
            CatalogValidationError,
            CatalogStoreError,
            SecretResolutionError,
        ) as exc:
            code = getattr(exc, "code", "catalog_refresh_failed")
            try:
                self.store.fail_refresh(refresh_id, code)
            except CatalogStoreError:
                pass
            if isinstance(exc, CatalogAdapterError):
                raise
            raise CatalogAdapterError(code) from exc

    def _authentication(
        self, auth_mode: str, secret_ref: str | None
    ) -> tuple[dict[str, str], httpx.Auth | None]:
        headers = {"Accept": "application/json", "User-Agent": "hcam-phase2-5-lab/1"}
        if auth_mode == "none":
            return headers, None
        if not secret_ref:
            raise CatalogAdapterError("secret_ref_required")
        credential = self.secret_provider.resolve(secret_ref, auth_mode)  # type: ignore[arg-type]
        if auth_mode == "bearer" and credential.bearer_token:
            headers["Authorization"] = f"Bearer {credential.bearer_token}"
            return headers, None
        if auth_mode == "basic" and credential.username and credential.password:
            return headers, httpx.BasicAuth(credential.username, credential.password)
        raise CatalogAdapterError("secret_document_invalid")

    async def _request(
        self,
        locator: str,
        headers: dict[str, str],
        auth: httpx.Auth | None,
    ) -> tuple[int, bytes, str | None]:
        last_code = "catalog_transport_failed"
        for attempt, delay in enumerate(self.retry_delays, start=1):
            if delay:
                await asyncio.sleep(delay)
            try:
                timeout = httpx.Timeout(self.timeout_seconds)
                async with httpx.AsyncClient(
                    follow_redirects=False,
                    trust_env=False,
                    timeout=timeout,
                    transport=self.transport,
                    verify=self.verify,
                ) as client:
                    async with client.stream(
                        "GET", locator, headers=headers, auth=auth
                    ) as response:
                        if response.status_code == 304:
                            return 304, b"", self._etag(response.headers.get("etag"))
                        if 300 <= response.status_code < 400:
                            raise CatalogAdapterError("catalog_redirect_denied")
                        if response.status_code in {401, 403}:
                            raise CatalogAdapterError("catalog_authorization_failed")
                        if response.status_code == 429:
                            last_code = "catalog_rate_limited"
                            if attempt < len(self.retry_delays):
                                continue
                            raise CatalogAdapterError(last_code)
                        if response.status_code >= 500:
                            last_code = "catalog_upstream_failed"
                            if attempt < len(self.retry_delays):
                                continue
                            raise CatalogAdapterError(last_code)
                        if response.status_code != 200:
                            raise CatalogAdapterError("catalog_http_status_rejected")
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > self.max_response_bytes:
                                raise CatalogAdapterError("catalog_response_too_large")
                        return (
                            200,
                            bytes(body),
                            self._etag(response.headers.get("etag")),
                        )
            except CatalogAdapterError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError):
                last_code = "catalog_transport_failed"
                if attempt >= len(self.retry_delays):
                    raise CatalogAdapterError(last_code) from None
        raise CatalogAdapterError(last_code)

    @staticmethod
    def _etag(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if (
            not stripped
            or len(stripped) > 256
            or any(ord(character) < 32 for character in stripped)
        ):
            raise CatalogAdapterError("invalid_catalog_etag")
        return stripped
