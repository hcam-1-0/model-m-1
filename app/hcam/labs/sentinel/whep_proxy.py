from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urljoin

import httpx

from hcam.labs.sentinel.models import (
    CatalogEndpoint,
    CatalogValidationError,
    ExactNetworkPolicy,
)


class WhepProxyError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class WhepTicket:
    session_id: str
    bearer_token: str
    expires_at: str


@dataclass(slots=True)
class _Session:
    endpoint: CatalogEndpoint
    token_digest: bytes
    expires_at: datetime
    external_resource: str | None = None
    negotiating: bool = False


class SentinelWhepProxy:
    """Bounded signaling proxy; WebRTC media never passes through H-CAM."""

    def __init__(
        self,
        network_policy: ExactNetworkPolicy,
        *,
        ttl_seconds: int = 60,
        timeout_seconds: float = 15,
        max_offer_bytes: int = 64 * 1024,
        max_answer_bytes: int = 256 * 1024,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not 10 <= ttl_seconds <= 300:
            raise ValueError("WHEP ticket lifetime must be between 10 and 300 seconds")
        self.network_policy = network_policy
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds
        self.max_offer_bytes = max_offer_bytes
        self.max_answer_bytes = max_answer_bytes
        self.transport = transport
        self._sessions: dict[str, _Session] = {}
        self._lock = asyncio.Lock()

    async def issue(self, endpoint: CatalogEndpoint, *, limit: int) -> WhepTicket:
        if not 1 <= limit <= 8:
            raise WhepProxyError("whep_session_limit_invalid")
        validated = self.network_policy.validate(
            endpoint.locator, origin=endpoint.locator, role="preview"
        )
        await self.cleanup_expired()
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_urlsafe(18)
        expires_at = datetime.now(UTC) + timedelta(seconds=self.ttl_seconds)
        async with self._lock:
            if len(self._sessions) >= limit:
                raise WhepProxyError("whep_session_limit_reached")
            self._sessions[session_id] = _Session(
                endpoint=validated,
                token_digest=self._token_digest(token),
                expires_at=expires_at,
            )
        return WhepTicket(
            session_id=session_id,
            bearer_token=token,
            expires_at=expires_at.isoformat().replace("+00:00", "Z"),
        )

    async def negotiate(
        self, session_id: str, bearer_token: str, offer: bytes
    ) -> tuple[bytes, str]:
        if not offer or len(offer) > self.max_offer_bytes:
            raise WhepProxyError("whep_offer_rejected")
        async with self._lock:
            session = self._authorized_session(session_id, bearer_token)
            if session.negotiating or session.external_resource is not None:
                raise WhepProxyError("whep_session_already_used")
            session.negotiating = True
            endpoint = session.endpoint.locator
        try:
            answer, location = await self._post_offer(endpoint, offer)
        except Exception:
            async with self._lock:
                self._sessions.pop(session_id, None)
            raise
        async with self._lock:
            current = self._sessions.get(session_id)
            if current is None:
                await self._delete_external(location)
                raise WhepProxyError("whep_session_expired")
            current.external_resource = location
            current.negotiating = False
        return answer, location

    async def delete(self, session_id: str, bearer_token: str) -> None:
        async with self._lock:
            session = self._authorized_session(session_id, bearer_token)
            self._sessions.pop(session_id, None)
        if session.external_resource is not None:
            await self._delete_external(session.external_resource)

    async def cleanup_expired(self) -> int:
        now = datetime.now(UTC)
        async with self._lock:
            expired = [
                session_id
                for session_id, session in self._sessions.items()
                if session.expires_at <= now
            ]
            sessions = [self._sessions.pop(session_id) for session_id in expired]
        for session in sessions:
            if session.external_resource is not None:
                await self._delete_external(session.external_resource)
        return len(sessions)

    async def close(self) -> None:
        async with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            if session.external_resource is not None:
                await self._delete_external(session.external_resource)

    def _authorized_session(self, session_id: str, token: str) -> _Session:
        session = self._sessions.get(session_id)
        if session is None or session.expires_at <= datetime.now(UTC):
            self._sessions.pop(session_id, None)
            raise WhepProxyError("whep_session_not_found")
        if not hmac.compare_digest(session.token_digest, self._token_digest(token)):
            raise WhepProxyError("whep_session_unauthorized")
        return session

    async def _post_offer(self, endpoint: str, offer: bytes) -> tuple[bytes, str]:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=False,
                trust_env=False,
                transport=self.transport,
            ) as client:
                async with client.stream(
                    "POST",
                    endpoint,
                    headers={
                        "Accept": "application/sdp",
                        "Content-Type": "application/sdp",
                        "User-Agent": "hcam-phase2-5-sentinel-lab/1",
                    },
                    content=offer,
                ) as response:
                    if response.status_code not in {200, 201}:
                        raise WhepProxyError("whep_upstream_rejected")
                    if response.headers.get("content-type", "").split(";", 1)[
                        0
                    ].strip().lower() != "application/sdp":
                        raise WhepProxyError("whep_answer_content_type_invalid")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > self.max_answer_bytes:
                            raise WhepProxyError("whep_answer_too_large")
                    location = response.headers.get("location")
        except WhepProxyError:
            raise
        except httpx.TimeoutException as exc:
            raise WhepProxyError("whep_upstream_timeout") from exc
        except httpx.NetworkError as exc:
            raise WhepProxyError("whep_upstream_failed") from exc
        if not location:
            raise WhepProxyError("whep_resource_missing")
        absolute_location = urljoin(endpoint, location)
        try:
            trusted = self.network_policy.validate(
                absolute_location, origin=endpoint, role="preview"
            )
        except CatalogValidationError as exc:
            raise WhepProxyError("whep_resource_untrusted") from exc
        return bytes(body), trusted.locator

    async def _delete_external(self, locator: str) -> None:
        try:
            trusted = self.network_policy.validate(
                locator, origin=locator, role="preview"
            )
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=False,
                trust_env=False,
                transport=self.transport,
            ) as client:
                response = await client.delete(
                    trusted.locator,
                    headers={"User-Agent": "hcam-phase2-5-sentinel-lab/1"},
                )
                if not 200 <= response.status_code < 300:
                    raise WhepProxyError("whep_cleanup_failed")
        except WhepProxyError:
            raise
        except (CatalogValidationError, httpx.HTTPError) as exc:
            raise WhepProxyError("whep_cleanup_failed") from exc

    @staticmethod
    def _token_digest(token: str) -> bytes:
        return hashlib.sha256(token.encode("utf-8")).digest()
