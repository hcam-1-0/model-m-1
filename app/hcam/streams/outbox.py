from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import sleep
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from hcam.streams.models import StreamEventOutbox


_LOGGER = logging.getLogger("hcam.stream_event_dispatcher")


def utc_now() -> datetime:
    return datetime.now(UTC)


class StreamEventSink(Protocol):
    def publish(self, event: dict[str, object]) -> None: ...


class StreamEventDeliveryError(RuntimeError):
    pass


class LoggingStreamEventSink:
    """Metadata-only validation sink; production deployments supply an event bus."""

    def publish(self, event: dict[str, object]) -> None:
        _LOGGER.info(json.dumps(event, separators=(",", ":"), sort_keys=True))


class StreamEventOutboxDispatcher:
    """Deliver one event transactionally with at-least-once sink semantics."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        sink: StreamEventSink,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.session_factory = session_factory
        self.sink = sink
        self.clock = clock

    def run_once(self) -> bool:
        with self.session_factory() as session, session.begin():
            query = (
                select(StreamEventOutbox)
                .where(StreamEventOutbox.published_at.is_(None))
                .order_by(StreamEventOutbox.occurred_at, StreamEventOutbox.event_id)
                .limit(1)
            )
            if session.bind is not None and session.bind.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
            event = session.scalar(query)
            if event is None:
                return False
            document: dict[str, object] = {
                "event": "stream.outbox.delivered",
                "event_id": event.event_id,
                "event_type": event.event_type,
                "schema_version": event.schema_version,
                "stream_id": event.stream_id,
                "camera_id": event.camera_id,
                "occurred_at": event.occurred_at.isoformat(),
                "payload": event.payload,
            }
            try:
                self.sink.publish(document)
            except Exception as exc:
                raise StreamEventDeliveryError("stream event sink rejected delivery") from exc
            event.published_at = self.clock()
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
