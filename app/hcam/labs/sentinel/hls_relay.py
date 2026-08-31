from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit, urlunsplit

import httpx

from hcam.labs.sentinel.models import CatalogEndpoint, ExactNetworkPolicy


class HlsRelayError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class HlsRelayTicket:
    session_id: str
    bearer_token: str
    whep_url: str
    expires_at: str


@dataclass(slots=True)
class _Relay:
    process: asyncio.subprocess.Process
    token_digest: bytes
    path: str
    expires_at: datetime


class SentinelHlsRelay:
    """Ephemeral HLS stream-copy relay for networks that block WHEP port 8889."""

    def __init__(
        self,
        network_policy: ExactNetworkPolicy,
        *,
        mediamtx_api_url: str,
        publish_base_url: str,
        public_whep_base_url: str,
        ttl_seconds: int = 60,
        startup_timeout_seconds: float = 35,
        ffmpeg: str = "ffmpeg",
    ) -> None:
        if not 10 <= ttl_seconds <= 300:
            raise ValueError("relay lifetime must be between 10 and 300 seconds")
        self.network_policy = network_policy
        self.mediamtx_api_url = mediamtx_api_url.rstrip("/")
        self.publish_base_url = publish_base_url.rstrip("/")
        self.public_whep_base_url = public_whep_base_url.rstrip("/")
        self.ttl_seconds = ttl_seconds
        self.startup_timeout_seconds = startup_timeout_seconds
        self.ffmpeg = ffmpeg
        self._relays: dict[str, _Relay] = {}
        self._lock = asyncio.Lock()

    async def issue(self, endpoint: CatalogEndpoint, *, limit: int) -> HlsRelayTicket:
        if not 1 <= limit <= 8:
            raise HlsRelayError("hls_relay_limit_invalid")
        trusted = self.network_policy.validate(
            endpoint.locator, origin=endpoint.locator, role="fallback"
        )
        if trusted.protocol not in {"http", "https"}:
            raise HlsRelayError("hls_relay_transport_invalid")
        input_url = self._cookie_check_url(trusted.locator)
        await self.cleanup_expired()
        async with self._lock:
            if len(self._relays) >= limit:
                raise HlsRelayError("hls_relay_limit_reached")
        session_id = secrets.token_hex(16)
        token = secrets.token_urlsafe(32)
        path = f"hcam-sentinel/{session_id}"
        environment = {
            key: value
            for key, value in os.environ.items()
            if key.lower()
            not in {
                "all_proxy",
                "http_proxy",
                "https_proxy",
                "no_proxy",
            }
        }
        try:
            process = await asyncio.create_subprocess_exec(
                self.ffmpeg,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-rw_timeout",
                "15000000",
                "-reconnect",
                "1",
                "-reconnect_streamed",
                "1",
                "-reconnect_delay_max",
                "2",
                "-http_persistent",
                "0",
                "-i",
                input_url,
                "-map",
                "0:v:0",
                "-an",
                "-c:v",
                "copy",
                "-f",
                "rtsp",
                "-rtsp_transport",
                "tcp",
                f"{self.publish_base_url}/{session_id}",
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                env=environment,
            )
        except OSError as exc:
            raise HlsRelayError("hls_relay_ffmpeg_unavailable") from exc
        expires_at = datetime.now(UTC) + timedelta(
            seconds=self.startup_timeout_seconds + self.ttl_seconds
        )
        relay = _Relay(
            process=process,
            token_digest=self._token_digest(token),
            path=path,
            expires_at=expires_at,
        )
        async with self._lock:
            if len(self._relays) >= limit:
                await self._stop_process(process)
                raise HlsRelayError("hls_relay_limit_reached")
            self._relays[session_id] = relay
        try:
            await self._wait_ready(relay)
        except HlsRelayError:
            async with self._lock:
                self._relays.pop(session_id, None)
            await self._stop_process(process)
            raise
        expires_at = datetime.now(UTC) + timedelta(seconds=self.ttl_seconds)
        relay.expires_at = expires_at
        return HlsRelayTicket(
            session_id=session_id,
            bearer_token=token,
            whep_url=f"{self.public_whep_base_url}/{session_id}/whep",
            expires_at=expires_at.isoformat().replace("+00:00", "Z"),
        )

    async def delete(self, session_id: str, bearer_token: str) -> None:
        async with self._lock:
            relay = self._authorized_relay(session_id, bearer_token)
            self._relays.pop(session_id, None)
        await self._stop_process(relay.process)

    async def cleanup_expired(self) -> int:
        now = datetime.now(UTC)
        async with self._lock:
            expired = [
                session_id
                for session_id, relay in self._relays.items()
                if relay.expires_at <= now or relay.process.returncode is not None
            ]
            relays = [self._relays.pop(session_id) for session_id in expired]
        for relay in relays:
            await self._stop_process(relay.process)
        return len(relays)

    async def close(self) -> None:
        async with self._lock:
            relays = list(self._relays.values())
            self._relays.clear()
        for relay in relays:
            await self._stop_process(relay.process)

    def _authorized_relay(self, session_id: str, token: str) -> _Relay:
        relay = self._relays.get(session_id)
        if relay is None or relay.expires_at <= datetime.now(UTC):
            self._relays.pop(session_id, None)
            raise HlsRelayError("hls_relay_not_found")
        if not hmac.compare_digest(relay.token_digest, self._token_digest(token)):
            raise HlsRelayError("hls_relay_unauthorized")
        return relay

    async def _wait_ready(self, relay: _Relay) -> None:
        deadline = asyncio.get_running_loop().time() + self.startup_timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            if relay.process.returncode is not None:
                raise HlsRelayError("hls_relay_process_failed")
            try:
                async with httpx.AsyncClient(
                    timeout=3, follow_redirects=False, trust_env=False
                ) as client:
                    response = await client.get(
                        f"{self.mediamtx_api_url}/v3/paths/list"
                    )
                if response.status_code == 200 and len(response.content) <= 1024 * 1024:
                    document = response.json()
                    items = document.get("items", [])
                    if any(
                        isinstance(item, dict)
                        and item.get("name") == relay.path
                        and item.get("ready") is True
                        for item in items
                    ):
                        return
            except (httpx.HTTPError, ValueError):
                pass
            await asyncio.sleep(0.25)
        raise HlsRelayError("hls_relay_startup_timeout")

    @staticmethod
    async def _stop_process(process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except TimeoutError:
            process.kill()
            await process.wait()

    @staticmethod
    def _token_digest(token: str) -> bytes:
        return hashlib.sha256(token.encode("utf-8")).digest()

    @staticmethod
    def _cookie_check_url(locator: str) -> str:
        """Use the Sentinel gateway's fixed, non-secret HLS bootstrap query."""
        parsed = urlsplit(locator)
        if parsed.query or parsed.fragment or not parsed.path.endswith(".m3u8"):
            raise HlsRelayError("hls_relay_locator_invalid")
        return urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, "cookieCheck=1", "")
        )
