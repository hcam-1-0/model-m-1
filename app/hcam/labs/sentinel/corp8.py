"""Authenticated, zero-retention CORP8 Camera Grid catalogue support.

The public catalogue intentionally contains only camera identities.  Transport
locators are derived from the documented, allowlisted CORP8 contract rather
than accepted from untrusted catalogue data.  Credentials are used only while
creating a short-lived upstream web session and are never persisted.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

import httpx

from hcam.labs.sentinel.adapter import CatalogAdapterError, SentinelCatalogAdapter
from hcam.labs.sentinel.models import (
    CatalogValidationError,
    ExactNetworkPolicy,
    NormalizedCatalog,
    normalize_catalog_document,
)

_CAMERA_ID = re.compile(r"^cam(?:0[1-9]|[12][0-9]|30)$")
_MAX_SECRET_BYTES = 1024
_RECONNECT_DELAYS_SECONDS = (2, 4, 8, 16, 30)


@dataclass(frozen=True, slots=True)
class Corp8StreamPolicy:
    """Documented live-stream rules, independent of frame arrival timing."""

    rtsp_transport: str = "tcp"
    timing_source: str = "pts"
    reconnect_delays_seconds: tuple[int, ...] = _RECONNECT_DELAYS_SECONDS
    recording_permitted: bool = False
    download_permitted: bool = False

    def reconnect_delay(self, attempt: int) -> int:
        if attempt < 1:
            raise ValueError("reconnect attempt must be positive")
        return self.reconnect_delays_seconds[
            min(attempt - 1, len(self.reconnect_delays_seconds) - 1)
        ]


@dataclass(frozen=True, slots=True)
class PtsObservation:
    delta_ms: float | None
    discontinuity: bool


class Corp8PtsClock:
    """PTS-only timing state for live processing; arrival time is ignored."""

    def __init__(self) -> None:
        self._previous_pts_ms: float | None = None

    def observe(self, pts_ms: float) -> PtsObservation:
        if not isinstance(pts_ms, (int, float)) or pts_ms < 0:
            raise CatalogAdapterError("corp8_pts_invalid")
        current = float(pts_ms)
        previous = self._previous_pts_ms
        self._previous_pts_ms = current
        if previous is None:
            return PtsObservation(delta_ms=None, discontinuity=False)
        if current <= previous:
            # Treat a timestamp reset/regression as a hard scene boundary so
            # downstream state can reset instead of inventing elapsed time.
            return PtsObservation(delta_ms=None, discontinuity=True)
        return PtsObservation(delta_ms=current - previous, discontinuity=False)

    def reset_for_scene_cut(self) -> None:
        """Discard long-lived timing state after a known loop scene cut."""
        self._previous_pts_ms = None


def _read_secret(path: Path | None) -> str:
    if path is None:
        raise CatalogAdapterError("corp8_credentials_unconfigured")
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > _MAX_SECRET_BYTES:
            raise OSError("invalid secret file")
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise CatalogAdapterError("corp8_credentials_unavailable") from exc
    if not value or "\x00" in value:
        raise CatalogAdapterError("corp8_credentials_invalid")
    return value


def corp8_whep_auth(
    *, email_file: Path | None, password_file: Path | None
) -> httpx.BasicAuth:
    """Resolve short-lived upstream WHEP authentication without persistence."""
    return httpx.BasicAuth(
        username=_read_secret(email_file), password=_read_secret(password_file)
    )


def corp8_rtsp_locator(
    locator: str, *, email_file: Path | None, password_file: Path | None
) -> str:
    """Create a private RTSP/TCP locator only for a backend media client.

    The caller must never store or serialize this value.  HTTP Basic auth is
    used for WHEP; RTSP clients require the documented URL-userinfo form.
    """
    parsed = urlsplit(locator)
    if (
        parsed.scheme != "rtsp"
        or parsed.hostname != "103.250.160.189"
        or parsed.port != 8554
        or not parsed.path.startswith("/stream/cam")
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise CatalogAdapterError("corp8_rtsp_locator_invalid")
    email = quote(_read_secret(email_file), safe="")
    password = quote(_read_secret(password_file), safe="")
    return urlunsplit(
        ("rtsp", f"{email}:{password}@103.250.160.189:8554", parsed.path, "", "")
    )


def normalize_corp8_catalog_document(
    document: object,
    *,
    origin: str,
    network_policy: ExactNetworkPolicy,
    max_records: int = 50,
) -> NormalizedCatalog:
    """Normalize CORP8's minimal ``[{id, name}]`` catalogue safely."""
    if not isinstance(document, list):
        raise CatalogValidationError("corp8_catalog_root_invalid")
    if len(document) > max_records:
        raise CatalogValidationError("catalog_record_limit_exceeded")
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or parsed.hostname != "cctv.corp8.cloud" or parsed.path != "/cameras.json":
        raise CatalogValidationError("corp8_catalog_origin_invalid")
    cameras: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in document:
        if not isinstance(item, dict) or set(item) - {"id", "name"}:
            raise CatalogValidationError("corp8_camera_record_invalid")
        camera_id = item.get("id")
        name = item.get("name")
        if not isinstance(camera_id, str) or _CAMERA_ID.fullmatch(camera_id) is None:
            raise CatalogValidationError("corp8_camera_id_invalid")
        if camera_id in seen:
            raise CatalogValidationError("duplicate_camera_id")
        if not isinstance(name, str) or not name.strip() or len(name) > 240:
            raise CatalogValidationError("invalid_camera_name")
        seen.add(camera_id)
        cameras.append(
            {
                "id": camera_id,
                "name": name.strip(),
                "live": True,
                "rtsp_url": f"rtsp://103.250.160.189:8554/stream/{camera_id}",
                "webrtc_url": f"http://103.250.160.189:8889/stream/{camera_id}/whep",
                "hls_live_url": f"https://cctv.corp8.cloud/{camera_id}/index.m3u8",
            }
        )
    return normalize_catalog_document(
        {"cameras": cameras},
        origin=origin,
        network_policy=network_policy,
        max_records=max_records,
    )


class Corp8CatalogAdapter(SentinelCatalogAdapter):
    """Catalogue adapter which establishes an in-memory CORP8 web session."""

    def __init__(
        self,
        *args: Any,
        login_url: str = "https://cctv.corp8.cloud/auth/login",
        email_file: Path | None = None,
        password_file: Path | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("document_normalizer", normalize_corp8_catalog_document)
        super().__init__(*args, **kwargs)
        self.login_url = login_url
        self.email_file = email_file
        self.password_file = password_file

    async def _request(
        self, locator: str, headers: dict[str, str], auth: httpx.Auth | None
    ) -> tuple[int, bytes, str | None]:
        del auth
        email = _read_secret(self.email_file)
        password = _read_secret(self.password_file)
        login = urlsplit(self.login_url)
        if (
            login.scheme != "https"
            or login.hostname != "cctv.corp8.cloud"
            or login.port not in {None, 443}
            or login.path != "/auth/login"
            or login.query
            or login.fragment
            or login.username
            or login.password
        ):
            raise CatalogAdapterError("corp8_login_url_invalid")
        timeout = httpx.Timeout(self.timeout_seconds)
        try:
            async with httpx.AsyncClient(
                follow_redirects=False,
                trust_env=False,
                timeout=timeout,
                transport=self.transport,
                verify=self.verify,
            ) as client:
                # Mirror the provider's ordinary browser form flow.  Loading
                # the page first permits provider-owned bootstrap cookies, but
                # nothing from this in-memory cookie jar is ever persisted or
                # sent to the dashboard client.
                login_page = await client.get(
                    self.login_url,
                    headers={"User-Agent": headers["User-Agent"]},
                )
                if login_page.status_code != 200:
                    raise CatalogAdapterError("corp8_login_page_unavailable")
                login = await client.post(
                    self.login_url,
                    data={"email": email, "password": password},
                    headers={
                        "User-Agent": headers["User-Agent"],
                        "Origin": "https://cctv.corp8.cloud",
                        "Referer": self.login_url,
                    },
                )
                if login.status_code in {401, 403}:
                    raise CatalogAdapterError("catalog_authorization_failed")
                if login.status_code not in {200, 302, 303}:
                    raise CatalogAdapterError("corp8_login_failed")
                redirect = login.headers.get("location")
                if redirect is not None and redirect not in {"/", "/auth/login"}:
                    raise CatalogAdapterError("corp8_login_redirect_denied")
                if login.status_code == 200 and not client.cookies:
                    # A standard form login returns a successful page status
                    # even for invalid credentials.  Do not mistake that HTML
                    # response for an authenticated server-side session.
                    raise CatalogAdapterError("catalog_authorization_failed")
                async with client.stream("GET", locator, headers=headers) as response:
                    if 300 <= response.status_code < 400:
                        raise CatalogAdapterError("catalog_redirect_denied")
                    if response.status_code in {401, 403}:
                        raise CatalogAdapterError("catalog_authorization_failed")
                    if response.status_code != 200:
                        raise CatalogAdapterError("catalog_http_status_rejected")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > self.max_response_bytes:
                            raise CatalogAdapterError("catalog_response_too_large")
                    return 200, bytes(body), self._etag(response.headers.get("etag"))
        except CatalogAdapterError:
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise CatalogAdapterError("catalog_transport_failed") from exc
