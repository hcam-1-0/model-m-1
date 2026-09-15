from __future__ import annotations

from collections import Counter


ALLOWED_OUTCOMES = frozenset(
    {"created", "duplicate", "conflict", "transitioned", "denied", "stale", "collapsed"}
)


class AlertMetrics:
    def __init__(self) -> None:
        self._counts: Counter[tuple[str, str]] = Counter()

    def record(self, operation: str, outcome: str) -> None:
        if outcome not in ALLOWED_OUTCOMES:
            raise ValueError("metric outcome is not allowlisted")
        if operation not in {"proposal", "lifecycle", "review", "budget", "timer", "adapter"}:
            raise ValueError("metric operation is not allowlisted")
        self._counts[(operation, outcome)] += 1

    def snapshot(self) -> dict[str, int]:
        return {
            f"{operation}:{outcome}": count
            for (operation, outcome), count in sorted(self._counts.items())
        }
