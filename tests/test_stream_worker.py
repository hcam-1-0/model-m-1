from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select

from hcam.camera_registry.models import Camera
from hcam.streams.models import (
    StreamEndpoint,
    StreamEventOutbox,
    StreamHealthCurrent,
    StreamProbeRun,
)
from hcam.streams.probe import ProbeResult, ProbeToolError
from hcam.streams.worker import (
    StreamHealthWorker,
    StreamWorkerLeaseError,
    _float_media,
    _integer_media,
    _text_media,
    transition_health,
)


@dataclass
class Clock:
    current: datetime

    def __call__(self) -> datetime:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += timedelta(seconds=seconds)


class ResultAdapter:
    def __init__(self, *results: ProbeResult) -> None:
        self.results = list(results)

    def probe(self, _endpoint: StreamEndpoint) -> ProbeResult:
        return self.results.pop(0)


class FailingToolAdapter:
    def probe(self, _endpoint: StreamEndpoint) -> ProbeResult:
        raise ProbeToolError("tool unavailable")


def _primary_stream_id(imported_app) -> str:
    with imported_app.state.database.session_factory() as session:
        return session.scalar(
            select(StreamEndpoint.stream_id).where(StreamEndpoint.is_primary.is_(True))
        )


def test_health_hysteresis_records_events_and_updates_camera_projection(
    imported_app,
) -> None:
    clock = Clock(datetime(2026, 8, 18, 10, 0, tzinfo=UTC))
    worker = StreamHealthWorker(
        imported_app.state.database.session_factory,
        ResultAdapter(
            ProbeResult(
                "success",
                None,
                12.5,
                {"codec": "h264", "container": "rtsp", "width": 640, "height": 360},
            ),
            ProbeResult(
                "success",
                None,
                10.0,
                {"codec": "h264", "container": "rtsp", "width": 640, "height": 360},
            ),
        ),
        worker_id="worker-test",
        clock=clock,
    )
    stream_id = _primary_stream_id(imported_app)
    with imported_app.state.database.session_factory.begin() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        assert endpoint is not None
        endpoint.probe_due_at = clock.current

    assert worker.run_once() is True
    clock.advance(11)
    assert worker.run_once() is True

    with imported_app.state.database.session_factory() as session:
        health = session.get(StreamHealthCurrent, stream_id)
        endpoint = session.get(StreamEndpoint, stream_id)
        assert health is not None
        assert endpoint is not None
        assert health.state == "healthy"
        assert health.consecutive_successes == 2
        assert endpoint.probe_due_at == clock.current + timedelta(seconds=30)
        assert endpoint.lease_owner is None
        assert session.scalar(
            select(func.count()).select_from(StreamProbeRun).where(
                StreamProbeRun.stream_id == stream_id
            )
        ) == 2
        assert session.scalar(
            select(func.count()).select_from(StreamEventOutbox).where(
                StreamEventOutbox.stream_id == stream_id
            )
        ) == 2
        camera = session.get(Camera, endpoint.camera_id)
        assert camera is not None
        assert camera.reachability == "healthy"
        assert camera.codec == "h264"


def test_three_transient_failures_move_stream_offline_with_backoff(imported_app) -> None:
    clock = Clock(datetime(2026, 8, 18, 11, 0, tzinfo=UTC))
    worker = StreamHealthWorker(
        imported_app.state.database.session_factory,
        ResultAdapter(
            *[ProbeResult("failure", "unreachable", 50.0) for _ in range(4)]
        ),
        worker_id="worker-failure-test",
        clock=clock,
    )
    stream_id = _primary_stream_id(imported_app)
    with imported_app.state.database.session_factory.begin() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        assert endpoint is not None
        endpoint.probe_due_at = clock.current

    for delay in (11, 11, 11, 21):
        assert worker.run_once() is True
        clock.advance(delay)

    with imported_app.state.database.session_factory() as session:
        health = session.get(StreamHealthCurrent, stream_id)
        endpoint = session.get(StreamEndpoint, stream_id)
        assert health is not None
        assert endpoint is not None
        assert health.state == "offline"
        assert health.consecutive_failures == 4
        assert endpoint.probe_due_at == clock.current - timedelta(seconds=1)


@pytest.mark.parametrize("reason", ["network_policy_denied", "onvif_redirect_denied"])
def test_terminal_failure_is_immediate_and_scheduled_at_five_minutes(
    reason: str,
) -> None:
    current = StreamHealthCurrent(
        stream_id="str_" + "a" * 32,
        state="unknown",
        consecutive_successes=0,
        consecutive_failures=0,
    )

    transition = transition_health(current, ProbeResult("failure", reason, 0.0))

    assert transition.state == "misconfigured"
    assert transition.next_probe_delay == timedelta(minutes=5)


def test_tool_failure_releases_lease_and_remains_a_runtime_error(imported_app) -> None:
    clock = Clock(datetime(2026, 8, 18, 12, 0, tzinfo=UTC))
    worker = StreamHealthWorker(
        imported_app.state.database.session_factory,
        FailingToolAdapter(),
        worker_id="worker-tool-test",
        clock=clock,
    )
    stream_id = _primary_stream_id(imported_app)
    with imported_app.state.database.session_factory.begin() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        assert endpoint is not None
        endpoint.probe_due_at = clock.current

    try:
        worker.run_once()
    except ProbeToolError:
        pass
    else:
        raise AssertionError("ProbeToolError was not raised")

    with imported_app.state.database.session_factory() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        assert endpoint is not None
        assert endpoint.lease_owner is None
        assert endpoint.probe_due_at == clock.current + timedelta(seconds=10)


def test_worker_returns_false_without_due_stream(imported_app) -> None:
    clock = Clock(datetime(2026, 8, 18, 13, 0, tzinfo=UTC))
    worker = StreamHealthWorker(
        imported_app.state.database.session_factory,
        ResultAdapter(ProbeResult("success", None, 1.0)),
        worker_id="worker-idle",
        clock=clock,
    )
    with imported_app.state.database.session_factory.begin() as session:
        for endpoint in session.scalars(select(StreamEndpoint)):
            endpoint.probe_due_at = clock.current + timedelta(hours=1)
    assert worker.run_once() is False


def test_worker_detects_lost_lease_and_purges_expired_history(imported_app) -> None:
    clock = Clock(datetime(2026, 8, 18, 14, 0, tzinfo=UTC))
    worker = StreamHealthWorker(
        imported_app.state.database.session_factory,
        ResultAdapter(
            ProbeResult(
                "success",
                None,
                2.0,
                {
                    "codec": 123,
                    "container": "rtsp",
                    "width": True,
                    "height": 720,
                    "frame_rate": "invalid",
                },
            )
        ),
        worker_id="worker-retention",
        clock=clock,
    )
    stream_id = _primary_stream_id(imported_app)
    with imported_app.state.database.session_factory.begin() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        assert endpoint is not None
        endpoint.probe_due_at = clock.current
        session.add(
            StreamProbeRun(
                probe_id="prb_" + "a" * 32,
                stream_id=stream_id,
                worker_id="old-worker",
                started_at=clock.current - timedelta(days=8, seconds=1),
                finished_at=clock.current - timedelta(days=8),
                outcome="failure",
                reason_code="unreachable",
                latency_ms=1.0,
                media={},
            )
        )

    assert worker.run_once() is True
    with imported_app.state.database.session_factory() as session:
        assert session.get(StreamProbeRun, "prb_" + "a" * 32) is None
        health = session.get(StreamHealthCurrent, stream_id)
        assert health is not None
        assert health.codec is None
        assert health.container == "rtsp"
        assert health.width is None
        assert health.height == 720
        assert health.frame_rate is None

    with imported_app.state.database.session_factory.begin() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        assert endpoint is not None
        endpoint.lease_owner = "different-worker"
    with pytest.raises(StreamWorkerLeaseError, match="lost"):
        worker._load_claimed(stream_id)


def test_worker_health_helpers_and_backoff_are_bounded() -> None:
    current = StreamHealthCurrent(
        stream_id="str_" + "b" * 32,
        state="healthy",
        consecutive_successes=5,
        consecutive_failures=20,
    )
    success = transition_health(current, ProbeResult("success", None, 1.0))
    assert success.state == "healthy"
    assert success.next_probe_delay == timedelta(seconds=30)
    offline = transition_health(
        current, ProbeResult("failure", "unreachable", 1.0)
    )
    assert offline.state == "offline"
    assert offline.next_probe_delay == timedelta(seconds=300)
    assert _text_media({"codec": 1}, "codec") is None
    assert _integer_media({"width": True}, "width") is None
    assert _float_media({"rate": True}, "rate") is None
    assert _float_media({"rate": 25}, "rate") == 25.0


def test_worker_run_touches_heartbeat_and_sleeps_when_idle(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    heartbeat = tmp_path / "worker.ready"
    worker = object.__new__(StreamHealthWorker)
    outcomes = iter([False])
    object.__setattr__(worker, "run_once", lambda: next(outcomes))
    slept: list[float] = []
    monkeypatch.setattr("hcam.streams.worker.sleep", slept.append)
    with pytest.raises(StopIteration):
        worker.run(poll_seconds=0.25, heartbeat_file=heartbeat)
    assert heartbeat.is_file()
    assert slept == [0.25]
