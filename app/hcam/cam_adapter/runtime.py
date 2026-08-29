from __future__ import annotations

import os
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from .catalog import CatalogPreview, load_catalog_preview
from .config import AdapterConfig, AdapterConfigurationError, StreamConfig
from .recorder import probe_stream_ok
from .viewer import LiveCamera, LiveViewer, LiveViewerError, WhepAnswer
from .worker import AdapterOrchestrator


class AdapterRuntimeError(RuntimeError):
    """The adapter lifecycle could not complete safely."""


@dataclass(frozen=True, slots=True)
class AdapterRuntimeStatus:
    config_loaded: bool
    config_file: str | None
    configuration_error: str | None
    running: bool
    base: str | None
    segment_time: int | None
    streams_configured: int
    streams_enabled: int
    active_workers: tuple[str, ...]
    yolo_model: str | None
    sample_interval: float | None
    catalog_configured: bool
    catalog_enabled: bool
    live_viewer_configured: bool
    live_viewer_enabled: bool
    live_viewer_camera_limit: int | None


@dataclass(frozen=True, slots=True)
class _ViewerLaunchSession:
    expires_at: float


class AdapterRuntime:
    """Owns a single in-process recorder orchestrator.

    The runtime is intentionally stopped by default.  It only loads a local JSON
    file selected through HCAM_CAM_ADAPTER_CONFIG_FILE and starts after an
    explicit platform-admin request.
    """

    def __init__(self, config_file: str | Path | None = None) -> None:
        self._config_file = Path(config_file).expanduser().resolve() if config_file else None
        self._lock = threading.RLock()
        self._config: AdapterConfig | None = None
        self._resolved_streams: list[StreamConfig] = []
        self._orchestrator: AdapterOrchestrator | None = None
        self._live_viewer: LiveViewer | None = None
        self._viewer_sessions: dict[str, _ViewerLaunchSession] = {}
        self._configuration_error: str | None = None
        self.reload()

    @classmethod
    def from_environment(cls) -> "AdapterRuntime":
        value = os.getenv("HCAM_CAM_ADAPTER_CONFIG_FILE")
        return cls(value if value and value.strip() else None)

    def reload(self) -> AdapterRuntimeStatus:
        with self._lock:
            if self.running:
                raise AdapterRuntimeError("stop the adapter before reloading its configuration")
            previous_viewer = self._live_viewer
            self._live_viewer = None
            self._viewer_sessions.clear()
            self._resolved_streams = []
            self._configuration_error = None
            if self._config_file is None:
                self._config = None
            else:
                try:
                    self._config = AdapterConfig.from_file(self._config_file)
                    if self._config.catalog is not None and self._config.catalog.viewer_enabled:
                        self._live_viewer = LiveViewer(self._config)
                except AdapterConfigurationError as exc:
                    self._config = None
                    self._configuration_error = str(exc)
        if previous_viewer is not None:
            previous_viewer.close_all()
        return self.status()

    @property
    def running(self) -> bool:
        return self._orchestrator is not None

    def _require_config(self) -> AdapterConfig:
        if self._configuration_error is not None:
            raise AdapterRuntimeError("adapter configuration is invalid")
        if self._config is None:
            raise AdapterRuntimeError("adapter configuration file is not set")
        return self._config

    def _resolve_streams(self, config: AdapterConfig) -> list[StreamConfig]:
        streams = list(config.streams)
        if config.catalog is not None and config.catalog.enabled:
            preview = load_catalog_preview(config)
            known = {stream.camera_id for stream in streams}
            streams.extend(stream for stream in preview.selected_streams if stream.camera_id not in known)
        config.assert_activatable(streams)
        return streams

    def catalog_preview(self) -> CatalogPreview:
        with self._lock:
            return load_catalog_preview(self._require_config())

    def issue_live_viewer_session(self) -> tuple[str, int]:
        with self._lock:
            viewer = self._require_live_viewer()
            self._discard_expired_viewer_sessions_locked()
            launch_token = secrets.token_urlsafe(32)
            self._viewer_sessions[launch_token] = _ViewerLaunchSession(
                expires_at=time.monotonic() + viewer.session_ttl_seconds
            )
            return launch_token, viewer.session_ttl_seconds

    def redeem_live_viewer_session(self, launch_token: str) -> tuple[str, int] | None:
        with self._lock:
            viewer = self._require_live_viewer()
            self._discard_expired_viewer_sessions_locked()
            launch = self._viewer_sessions.pop(launch_token, None)
            if launch is None:
                return None
            cookie_token = secrets.token_urlsafe(32)
            self._viewer_sessions[cookie_token] = _ViewerLaunchSession(
                expires_at=launch.expires_at
            )
            remaining = max(1, int(launch.expires_at - time.monotonic()))
            return cookie_token, min(remaining, viewer.session_ttl_seconds)

    def has_live_viewer_session(self, token: str | None) -> bool:
        if not token:
            return False
        with self._lock:
            self._discard_expired_viewer_sessions_locked()
            return token in self._viewer_sessions

    def live_cameras(self) -> tuple[LiveCamera, ...]:
        with self._lock:
            viewer = self._require_live_viewer()
        try:
            return viewer.cameras()
        except LiveViewerError as exc:
            raise AdapterRuntimeError("live camera catalogue is unavailable") from exc

    def negotiate_whep(self, camera_id: str, offer_sdp: str) -> WhepAnswer:
        with self._lock:
            viewer = self._require_live_viewer()
        try:
            return viewer.negotiate(camera_id, offer_sdp)
        except Exception as exc:
            raise AdapterRuntimeError("live playback negotiation failed") from exc

    def close_whep(self, playback_session_id: str) -> None:
        with self._lock:
            viewer = self._require_live_viewer()
        viewer.close(playback_session_id)

    def start(self) -> AdapterRuntimeStatus:
        with self._lock:
            if self.running:
                return self.status()
            config = self._require_config()
            try:
                streams = self._resolve_streams(config)
            except (AdapterConfigurationError, RuntimeError) as exc:
                raise AdapterRuntimeError("adapter source resolution failed") from exc
            active_config = config.model_copy(update={"streams": streams})
            orchestrator = AdapterOrchestrator(active_config, base=active_config.effective_base())
            try:
                orchestrator.start()
            except Exception as exc:
                orchestrator.stop()
                raise AdapterRuntimeError("adapter recorder could not be started") from exc
            self._resolved_streams = streams
            self._orchestrator = orchestrator
            return self.status()

    def stop(self) -> AdapterRuntimeStatus:
        with self._lock:
            orchestrator = self._orchestrator
            self._orchestrator = None
            self._resolved_streams = []
        if orchestrator is not None:
            orchestrator.stop()
        return self.status()

    def close(self) -> AdapterRuntimeStatus:
        snapshot = self.stop()
        with self._lock:
            viewer = self._live_viewer
            self._live_viewer = None
            self._viewer_sessions.clear()
        if viewer is not None:
            viewer.close_all()
        return snapshot

    def validate_configured_sources(self) -> list[dict[str, object]]:
        """Run ffprobe only against streams explicitly resolved by local config."""
        with self._lock:
            config = self._require_config()
            streams = self._resolved_streams or self._resolve_streams(config)
        return [
            {
                "camera_id": stream.camera_id,
                "reachable": probe_stream_ok(config.ffprobe_bin, stream.rtsp_url),
            }
            for stream in streams
            if stream.enabled
        ]

    def streams(self) -> tuple[StreamConfig, ...]:
        with self._lock:
            config = self._config
            if config is None:
                return ()
            return tuple(self._resolved_streams or config.streams)

    def _require_live_viewer(self) -> LiveViewer:
        if self._configuration_error is not None:
            raise AdapterRuntimeError("adapter configuration is invalid")
        if self._live_viewer is None:
            raise AdapterRuntimeError("live viewer is not enabled in local configuration")
        return self._live_viewer

    def _discard_expired_viewer_sessions_locked(self) -> None:
        now = time.monotonic()
        expired = [
            token
            for token, viewer_session in self._viewer_sessions.items()
            if viewer_session.expires_at <= now
        ]
        for token in expired:
            self._viewer_sessions.pop(token, None)

    def status(self) -> AdapterRuntimeStatus:
        with self._lock:
            config = self._config
            configured_streams = self._resolved_streams or (list(config.streams) if config else [])
            active_workers = (
                tuple(worker.stream.camera_id for worker in self._orchestrator.workers if worker.is_alive())
                if self._orchestrator is not None
                else ()
            )
            return AdapterRuntimeStatus(
                config_loaded=config is not None,
                config_file=self._config_file.name if self._config_file else None,
                configuration_error=self._configuration_error,
                running=self.running,
                base=str(config.effective_base()) if config else None,
                segment_time=config.segment_time_seconds if config else None,
                streams_configured=len(configured_streams),
                streams_enabled=sum(1 for stream in configured_streams if stream.enabled),
                active_workers=active_workers,
                yolo_model=config.yolo_model if config else None,
                sample_interval=config.sample_interval_seconds if config else None,
                catalog_configured=config is not None and config.catalog is not None,
                catalog_enabled=config is not None and config.catalog is not None and config.catalog.enabled,
                live_viewer_configured=config is not None and config.catalog is not None,
                live_viewer_enabled=self._live_viewer is not None,
                live_viewer_camera_limit=(
                    config.catalog.max_cameras
                    if config is not None and config.catalog is not None and config.catalog.viewer_enabled
                    else None
                ),
            )
