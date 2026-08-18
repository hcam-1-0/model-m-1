from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

import pytest

from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEventOutbox
from hcam.streams.outbox import (
    LoggingStreamEventSink,
    StreamEventDeliveryError,
    StreamEventOutboxDispatcher,
)


NOW = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)


class RecordingSink:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def publish(self, event: dict[str, object]) -> None:
        self.events.append(event)


def _add_event(app, event_id: str = "evt_test") -> None:
    with app.state.database.session_factory() as session:
        seed_synthetic_lab(session, count=1)
    with app.state.database.session_factory.begin() as session:
        session.add(
            StreamEventOutbox(
                event_id=event_id,
                event_type="hcam.stream.health.changed.v1",
                schema_version=1,
                stream_id=synthetic_stream_id(1),
                camera_id="phase2:cctv-001",
                occurred_at=NOW,
                payload={"state": "healthy"},
            )
        )


def test_dispatcher_delivers_and_marks_event_after_sink_success(app) -> None:
    _add_event(app)
    sink = RecordingSink()
    dispatcher = StreamEventOutboxDispatcher(
        app.state.database.session_factory,
        sink,
        clock=lambda: NOW,
    )

    assert dispatcher.run_once() is True
    assert dispatcher.run_once() is False
    assert sink.events[0]["event_id"] == "evt_test"
    assert sink.events[0]["payload"] == {"state": "healthy"}
    with app.state.database.session_factory() as session:
        stored = session.get(StreamEventOutbox, "evt_test")
        assert stored is not None
        assert stored.published_at == NOW


def test_dispatcher_rolls_back_when_sink_fails(app) -> None:
    _add_event(app, "evt_failure")

    class FailingSink:
        def publish(self, event: dict[str, object]) -> None:
            raise OSError("sink unavailable")

    dispatcher = StreamEventOutboxDispatcher(
        app.state.database.session_factory,
        FailingSink(),
        clock=lambda: NOW,
    )

    with pytest.raises(StreamEventDeliveryError, match="rejected delivery"):
        dispatcher.run_once()
    with app.state.database.session_factory() as session:
        stored = session.get(StreamEventOutbox, "evt_failure")
        assert stored is not None
        assert stored.published_at is None


def test_logging_sink_emits_metadata_only_json(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="hcam.stream_event_dispatcher"):
        LoggingStreamEventSink().publish({"event_id": "evt_log", "state": "healthy"})

    assert '"event_id":"evt_log"' in caplog.text
    assert "locator" not in caplog.text


def test_dispatcher_run_updates_heartbeat_and_sleeps_when_idle(
    app,
    tmp_path: Path,
    monkeypatch,
) -> None:
    dispatcher = StreamEventOutboxDispatcher(
        app.state.database.session_factory,
        RecordingSink(),
    )
    outcomes = iter([False])
    heartbeat = tmp_path / "dispatcher-heartbeat"
    slept: list[float] = []

    monkeypatch.setattr(dispatcher, "run_once", lambda: next(outcomes))
    monkeypatch.setattr("hcam.streams.outbox.sleep", lambda value: slept.append(value))

    with pytest.raises(StopIteration):
        dispatcher.run(poll_seconds=0.25, heartbeat_file=heartbeat)

    assert heartbeat.is_file()
    assert slept == [0.25]
