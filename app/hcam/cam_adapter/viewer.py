from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx

from .catalog import CatalogLoadError, load_catalog_preview
from .config import AdapterConfig, AdapterConfigurationError, StreamConfig


_MAX_SDP_BYTES = 64 * 1024
_MAX_WHEP_ANSWER_BYTES = 128 * 1024
_WHEP_SUCCESS_CODES = frozenset({200, 201})


class LiveViewerError(RuntimeError):
    """A local live-viewer action could not be completed safely."""


@dataclass(frozen=True, slots=True)
class LiveCamera:
    camera_id: str
    location_label: str | None
    department: str | None


@dataclass(frozen=True, slots=True)
class WhepAnswer:
    answer_sdp: str
    playback_session_id: str | None


@dataclass(frozen=True, slots=True)
class _WhepPlaybackSession:
    resource_url: str
    etag: str | None
    expires_at: float


class LiveViewer:
    """A no-recording WHEP signalling client for approved catalogue entries.

    Browser media travels directly between the browser and the configured WHEP
    service. H-CAM handles only the authenticated SDP exchange and cleanup of
    the temporary WHEP resource. No frames or media files are written locally.
    """

    def __init__(self, config: AdapterConfig) -> None:
        config.assert_viewer_activatable()
        self._config = config
        self._lock = threading.RLock()
        self._playback_sessions: dict[str, _WhepPlaybackSession] = {}

    @property
    def session_ttl_seconds(self) -> int:
        assert self._config.catalog is not None
        return self._config.catalog.viewer_session_ttl_seconds

    def cameras(self) -> tuple[LiveCamera, ...]:
        try:
            preview = load_catalog_preview(self._config)
        except (AdapterConfigurationError, CatalogLoadError) as exc:
            raise LiveViewerError("live camera catalogue is unavailable") from exc
        return tuple(
            LiveCamera(
                camera_id=stream.camera_id,
                location_label=stream.location_label,
                department=stream.department,
            )
            for stream in preview.selected_streams
            if stream.enabled
        )

    def negotiate(self, camera_id: str, offer_sdp: str) -> WhepAnswer:
        self._validate_offer(offer_sdp)
        source = self._source_for_camera(camera_id)
        try:
            response = httpx.post(
                source.rtsp_url,
                content=offer_sdp.encode("utf-8"),
                headers={
                    "Accept": "application/sdp",
                    "Content-Type": "application/sdp",
                    "User-Agent": "H-CAM-Live-Viewer/1.0",
                },
                timeout=self._timeout_seconds,
                follow_redirects=False,
            )
        except httpx.HTTPError as exc:
            raise LiveViewerError("live playback negotiation failed") from exc

        if response.status_code not in _WHEP_SUCCESS_CODES:
            raise LiveViewerError("live playback negotiation was rejected")
        if len(response.content) > _MAX_WHEP_ANSWER_BYTES:
            raise LiveViewerError("live playback negotiation returned an invalid answer")
        try:
            answer_sdp = response.content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LiveViewerError("live playback negotiation returned an invalid answer") from exc
        if not answer_sdp.lstrip().startswith("v=0"):
            raise LiveViewerError("live playback negotiation returned an invalid answer")

        resource_url = self._whep_resource_url(response.headers.get("Location"), source)
        if resource_url is None:
            return WhepAnswer(answer_sdp=answer_sdp, playback_session_id=None)
        playback_session_id = secrets.token_urlsafe(24)
        with self._lock:
            self._discard_expired_locked()
            self._playback_sessions[playback_session_id] = _WhepPlaybackSession(
                resource_url=resource_url,
                etag=response.headers.get("ETag"),
                expires_at=time.monotonic() + self.session_ttl_seconds,
            )
        return WhepAnswer(answer_sdp=answer_sdp, playback_session_id=playback_session_id)

    def close(self, playback_session_id: str) -> None:
        with self._lock:
            self._discard_expired_locked()
            playback = self._playback_sessions.pop(playback_session_id, None)
        if playback is None:
            return
        headers = {"User-Agent": "H-CAM-Live-Viewer/1.0"}
        if playback.etag:
            headers["If-Match"] = playback.etag
        try:
            httpx.delete(
                playback.resource_url,
                headers=headers,
                timeout=self._timeout_seconds,
                follow_redirects=False,
            )
        except httpx.HTTPError:
            # WHEP resources expire upstream. A cleanup failure must not turn
            # into a browser error after the local media connection is closed.
            return

    def close_all(self) -> None:
        with self._lock:
            session_ids = tuple(self._playback_sessions)
        for playback_session_id in session_ids:
            self.close(playback_session_id)

    @property
    def _timeout_seconds(self) -> float:
        assert self._config.catalog is not None
        return self._config.catalog.timeout_seconds

    def _source_for_camera(self, camera_id: str) -> StreamConfig:
        for stream in load_catalog_preview(self._config).selected_streams:
            if stream.enabled and stream.camera_id == camera_id:
                return stream
        raise LiveViewerError("requested live camera is unavailable")

    @staticmethod
    def _validate_offer(offer_sdp: str) -> None:
        encoded = offer_sdp.encode("utf-8", errors="ignore")
        if not encoded or len(encoded) > _MAX_SDP_BYTES or not offer_sdp.lstrip().startswith("v=0"):
            raise LiveViewerError("live playback offer is invalid")

    def _whep_resource_url(self, location: str | None, source: StreamConfig) -> str | None:
        if not location:
            return None
        resource_url = urljoin(source.rtsp_url, location)
        parsed = urlsplit(resource_url)
        if (
            parsed.scheme.lower() != "https"
            or parsed.hostname is None
            or parsed.hostname.lower().rstrip(".") not in self._config.allowed_source_hosts
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
        ):
            raise LiveViewerError("live playback session location is unsafe")
        return resource_url

    def _discard_expired_locked(self) -> None:
        now = time.monotonic()
        expired = [
            session_id
            for session_id, playback in self._playback_sessions.items()
            if playback.expires_at <= now
        ]
        for session_id in expired:
            self._playback_sessions.pop(session_id, None)
