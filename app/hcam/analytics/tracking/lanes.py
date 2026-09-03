from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from threading import Condition
from time import monotonic

from hcam.analytics.tracking.types import TrackingResourceError


class GeneratedTrackingLaneStore:
    """Bounded process-local serialization for generated stream lanes."""

    def __init__(
        self,
        *,
        maximum_active_lanes: int = 32,
        maximum_queued_per_stream: int = 64,
        maximum_queue_age_ms: int = 1_000,
    ) -> None:
        if not 1 <= maximum_active_lanes <= 32:
            raise ValueError("generated tracking active-lane limit is invalid")
        if not 1 <= maximum_queued_per_stream <= 64:
            raise ValueError("generated tracking queue limit is invalid")
        if not 1 <= maximum_queue_age_ms <= 1_000:
            raise ValueError("generated tracking queue age is invalid")
        self.maximum_active_lanes = maximum_active_lanes
        self.maximum_queued_per_stream = maximum_queued_per_stream
        self.maximum_queue_age_ms = maximum_queue_age_ms
        self._condition = Condition()
        self._active: set[str] = set()
        self._waiting: dict[str, int] = defaultdict(int)

    @contextmanager
    def lease(self, stream_id: str) -> Iterator[None]:
        deadline = monotonic() + self.maximum_queue_age_ms / 1_000
        with self._condition:
            if self._waiting[stream_id] >= self.maximum_queued_per_stream:
                raise TrackingResourceError("generated tracker queue limit exceeded")
            self._waiting[stream_id] += 1
            try:
                while (
                    stream_id in self._active
                    or len(self._active) >= self.maximum_active_lanes
                ):
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        raise TrackingResourceError(
                            "generated tracker queue age exceeded"
                        )
                    self._condition.wait(timeout=remaining)
                self._active.add(stream_id)
            finally:
                self._waiting[stream_id] -= 1
                if self._waiting[stream_id] == 0:
                    del self._waiting[stream_id]
        try:
            yield
        finally:
            with self._condition:
                self._active.discard(stream_id)
                self._condition.notify_all()

    @property
    def active_lanes(self) -> int:
        with self._condition:
            return len(self._active)

    @property
    def queued_batches(self) -> int:
        with self._condition:
            return sum(self._waiting.values())
