from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from threading import Lock
from typing import Literal


MetricOutcome = Literal[
    "accepted",
    "duplicate",
    "conflict",
    "late_accepted",
    "late_rejected",
    "gap_accepted",
    "future_rejected",
    "policy_rejected",
    "capacity_rejected",
]
HypothesisOutcome = Literal["proposed", "abstained"]
RunOutcome = Literal["succeeded", "failed", "retried", "disabled"]
WindowOutcome = Literal["open", "complete", "degraded"]


_RECEIPT_OUTCOMES = frozenset(
    {
        "accepted",
        "duplicate",
        "conflict",
        "late_accepted",
        "late_rejected",
        "gap_accepted",
        "future_rejected",
        "policy_rejected",
        "capacity_rejected",
    }
)
_HYPOTHESIS_OUTCOMES = frozenset({"proposed", "abstained"})
_RUN_OUTCOMES = frozenset({"succeeded", "failed", "retried", "disabled"})
_WINDOW_OUTCOMES = frozenset({"open", "complete", "degraded"})
_DURATION_BUCKETS = (0.01, 0.05, 0.1, 0.5, 1.0, 5.0)


@dataclass(slots=True)
class CorrelationMetrics:
    """Low-cardinality, process-local metrics for the generated P4.1 worker."""

    _values: Counter[tuple[str, str]] = field(default_factory=Counter)
    _gauges: dict[str, int] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def record_receipt(self, outcome: MetricOutcome) -> None:
        if outcome not in _RECEIPT_OUTCOMES:
            raise ValueError("unknown correlation receipt metric outcome")
        with self._lock:
            self._values[("correlation_receipts_total", outcome)] += 1

    def record_hypothesis(self, outcome: HypothesisOutcome) -> None:
        if outcome not in _HYPOTHESIS_OUTCOMES:
            raise ValueError("unknown correlation hypothesis metric outcome")
        with self._lock:
            self._values[("correlation_hypotheses_total", outcome)] += 1

    def record_run(self, outcome: RunOutcome) -> None:
        if outcome not in _RUN_OUTCOMES:
            raise ValueError("unknown correlation run metric outcome")
        with self._lock:
            self._values[("correlation_runs_total", outcome)] += 1

    def record_window(self, outcome: WindowOutcome) -> None:
        if outcome not in _WINDOW_OUTCOMES:
            raise ValueError("unknown correlation window metric outcome")
        with self._lock:
            self._values[("correlation_windows_total", outcome)] += 1

    def observe_duration(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("correlation duration cannot be negative")
        bucket = next(
            (f"le_{limit:g}" for limit in _DURATION_BUCKETS if seconds <= limit),
            "gt_5",
        )
        with self._lock:
            self._values[("correlation_duration_seconds", bucket)] += 1

    def set_queue_depth(self, depth: int) -> None:
        if depth < 0:
            raise ValueError("correlation queue depth cannot be negative")
        with self._lock:
            self._gauges["correlation_queue_depth"] = depth

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            counters = {
                f"{metric}:{outcome}": value
                for (metric, outcome), value in sorted(self._values.items())
            }
            return {**counters, **dict(sorted(self._gauges.items()))}
