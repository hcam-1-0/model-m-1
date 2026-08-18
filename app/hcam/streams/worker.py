from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import sleep
from uuid import uuid4

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from hcam.camera_registry.models import Camera
from hcam.streams.models import (
    StreamEndpoint,
    StreamEventOutbox,
    StreamHealthCurrent,
    StreamProbeRun,
)
from hcam.streams.probe import ProbeResult, ProbeToolError, StreamProbeAdapter


_LOGGER = logging.getLogger("hcam.stream_worker")
_TERMINAL_STATES = {
    "unauthorized": "unauthorized",
    "credentials_unavailable": "misconfigured",
    "misconfigured": "misconfigured",
    "network_policy_denied": "misconfigured",
    "onvif_invalid_response": "misconfigured",
    "onvif_invalid_stream_uri": "misconfigured",
    "onvif_response_too_large": "misconfigured",
    "unsupported": "unsupported",
}


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class HealthTransition:
    state: str
    consecutive_successes: int
    consecutive_failures: int
    next_probe_delay: timedelta


def transition_health(
    current: StreamHealthCurrent,
    result: ProbeResult,
) -> HealthTransition:
    if result.succeeded:
        successes = current.consecutive_successes + 1
        state = "healthy" if current.state == "healthy" or successes >= 2 else "degraded"
        delay = timedelta(seconds=30 if state == "healthy" else 10)
        return HealthTransition(state, successes, 0, delay)

    failures = current.consecutive_failures + 1
    terminal_state = _TERMINAL_STATES.get(result.reason_code or "")
    if terminal_state is not None:
        return HealthTransition(terminal_state, 0, failures, timedelta(minutes=5))
    if failures < 3:
        return HealthTransition("degraded", 0, failures, timedelta(seconds=10))
    backoff_seconds = min(300, 10 * (2 ** min(failures - 3, 5)))
    return HealthTransition(
        "offline",
        0,
        failures,
        timedelta(seconds=backoff_seconds),
    )


class StreamWorkerLeaseError(RuntimeError):
    pass


class StreamHealthWorker:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        adapter: StreamProbeAdapter,
        *,
        worker_id: str,
        lease_duration: timedelta = timedelta(seconds=30),
        history_retention: timedelta = timedelta(days=7),
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.session_factory = session_factory
        self.adapter = adapter
        self.worker_id = worker_id
        self.lease_duration = lease_duration
        self.history_retention = history_retention
        self.clock = clock

    def _claim(self) -> str | None:
        now = self.clock()
        with self.session_factory() as session, session.begin():
            query = (
                select(StreamEndpoint)
                .where(
                    StreamEndpoint.enabled.is_(True),
                    or_(
                        StreamEndpoint.probe_due_at.is_(None),
                        StreamEndpoint.probe_due_at <= now,
                    ),
                    or_(
                        StreamEndpoint.lease_until.is_(None),
                        StreamEndpoint.lease_until <= now,
                    ),
                )
                .order_by(StreamEndpoint.probe_due_at, StreamEndpoint.stream_id)
                .limit(1)
            )
            if session.bind is not None and session.bind.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
            endpoint = session.scalar(query)
            if endpoint is None:
                return None
            endpoint.lease_owner = self.worker_id
            endpoint.lease_until = now + self.lease_duration
            endpoint.updated_at = now
            return endpoint.stream_id

    def _load_claimed(self, stream_id: str) -> StreamEndpoint:
        with self.session_factory() as session:
            endpoint = session.get(StreamEndpoint, stream_id)
            if endpoint is None or endpoint.lease_owner != self.worker_id:
                raise StreamWorkerLeaseError("stream probe lease was lost")
            session.expunge(endpoint)
            return endpoint

    def _release_after_tool_error(self, stream_id: str) -> None:
        now = self.clock()
        with self.session_factory() as session, session.begin():
            endpoint = session.get(StreamEndpoint, stream_id)
            if endpoint is None or endpoint.lease_owner != self.worker_id:
                return
            endpoint.lease_owner = None
            endpoint.lease_until = None
            endpoint.probe_due_at = now + timedelta(seconds=10)
            endpoint.updated_at = now

    def _record(self, stream_id: str, result: ProbeResult, started_at: datetime) -> str:
        finished_at = self.clock()
        probe_id = f"prb_{uuid4().hex}"
        with self.session_factory() as session, session.begin():
            endpoint = session.get(StreamEndpoint, stream_id)
            health = session.get(StreamHealthCurrent, stream_id)
            if (
                endpoint is None
                or health is None
                or endpoint.lease_owner != self.worker_id
            ):
                raise StreamWorkerLeaseError("stream probe lease was lost")
            previous_state = health.state
            transition = transition_health(health, result)
            health.state = transition.state
            health.reason_code = result.reason_code
            health.observed_at = finished_at
            health.consecutive_successes = transition.consecutive_successes
            health.consecutive_failures = transition.consecutive_failures
            health.probe_latency_ms = result.latency_ms
            if result.succeeded:
                health.codec = _text_media(result.media, "codec")
                health.container = _text_media(result.media, "container")
                health.width = _integer_media(result.media, "width")
                health.height = _integer_media(result.media, "height")
                health.frame_rate = _float_media(result.media, "frame_rate")
                health.last_success_at = finished_at
            else:
                health.last_failure_at = finished_at
            health.updated_at = finished_at
            endpoint.probe_due_at = finished_at + transition.next_probe_delay
            endpoint.lease_owner = None
            endpoint.lease_until = None
            endpoint.updated_at = finished_at
            session.add(
                StreamProbeRun(
                    probe_id=probe_id,
                    stream_id=stream_id,
                    worker_id=self.worker_id,
                    started_at=started_at,
                    finished_at=finished_at,
                    outcome=result.outcome,
                    reason_code=result.reason_code,
                    latency_ms=result.latency_ms,
                    media=result.media,
                )
            )
            camera = session.get(Camera, endpoint.camera_id)
            if camera is not None and endpoint.is_primary:
                camera.reachability = transition.state
                camera.last_checked_at = finished_at
                if result.succeeded:
                    camera.codec = health.codec
                    camera.container = health.container
            if previous_state != transition.state:
                session.add(
                    StreamEventOutbox(
                        event_id=f"evt_{uuid4().hex}",
                        event_type="hcam.stream.health.changed.v1",
                        schema_version=1,
                        stream_id=stream_id,
                        camera_id=endpoint.camera_id,
                        occurred_at=finished_at,
                        payload={
                            "stream_id": stream_id,
                            "camera_id": endpoint.camera_id,
                            "previous_state": previous_state,
                            "state": transition.state,
                            "reason_code": result.reason_code,
                            "observed_at": finished_at.isoformat(),
                        },
                    )
                )
            session.execute(
                delete(StreamProbeRun).where(
                    StreamProbeRun.finished_at < finished_at - self.history_retention
                )
            )
        _LOGGER.info(
            json.dumps(
                {
                    "event": "stream.probe.completed",
                    "outcome": result.outcome,
                    "reason_code": result.reason_code,
                    "stream_id": stream_id,
                    "worker_id": self.worker_id,
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return probe_id

    def run_once(self) -> bool:
        stream_id = self._claim()
        if stream_id is None:
            return False
        endpoint = self._load_claimed(stream_id)
        started_at = self.clock()
        try:
            result = self.adapter.probe(endpoint)
        except ProbeToolError:
            self._release_after_tool_error(stream_id)
            raise
        self._record(stream_id, result, started_at)
        return True

    def run(
        self,
        *,
        poll_seconds: float = 2.0,
        heartbeat_file: Path | None = None,
    ) -> None:
        while True:
            processed = self.run_once()
            if heartbeat_file is not None:
                heartbeat_file.touch()
            if not processed:
                sleep(poll_seconds)


def _text_media(media: dict[str, object], key: str) -> str | None:
    value = media.get(key)
    return value if isinstance(value, str) else None


def _integer_media(media: dict[str, object], key: str) -> int | None:
    value = media.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _float_media(media: dict[str, object], key: str) -> float | None:
    value = media.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None
