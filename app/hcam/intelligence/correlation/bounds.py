from __future__ import annotations

from dataclasses import dataclass


MAX_EVENT_ENVELOPE_BYTES = 65_536
MAX_CORRELATION_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_EVENTS_PER_BATCH = 1_000
MAX_ACTIVE_PARTITIONS = 128
MAX_ACTIVE_WINDOWS_PER_PARTITION = 256
MAX_EVENTS_PER_WINDOW = 4_096
MIN_WINDOW_SECONDS = 1
MAX_WINDOW_SECONDS = 900
MAX_ALLOWED_LATENESS_SECONDS = 300
MAX_FUTURE_CLOCK_SKEW_SECONDS = 30
MAX_WORKER_LEASE_SECONDS = 90
MAX_RETRY_ATTEMPTS = 3
MAX_EVIDENCE_REFS = 256
MAX_GRAPH_NODES = 1_024
MAX_GRAPH_EDGES = 4_096


class CorrelationLimitError(ValueError):
    """Raised when a correlation request exceeds a declared hard limit."""


@dataclass(frozen=True, slots=True)
class CorrelationBounds:
    events_per_batch: int = 100
    active_partitions: int = 32
    active_windows_per_partition: int = 32
    events_per_window: int = MAX_EVENTS_PER_WINDOW
    worker_lease_seconds: int = 30
    retry_attempts: int = 1

    def __post_init__(self) -> None:
        values = (
            ("events_per_batch", self.events_per_batch, 1, MAX_EVENTS_PER_BATCH),
            ("active_partitions", self.active_partitions, 1, MAX_ACTIVE_PARTITIONS),
            (
                "active_windows_per_partition",
                self.active_windows_per_partition,
                1,
                MAX_ACTIVE_WINDOWS_PER_PARTITION,
            ),
            ("events_per_window", self.events_per_window, 1, MAX_EVENTS_PER_WINDOW),
            ("worker_lease_seconds", self.worker_lease_seconds, 1, MAX_WORKER_LEASE_SECONDS),
            ("retry_attempts", self.retry_attempts, 1, MAX_RETRY_ATTEMPTS),
        )
        for name, value, minimum, maximum in values:
            if not minimum <= value <= maximum:
                raise CorrelationLimitError(f"{name} is outside the declared bounds")
