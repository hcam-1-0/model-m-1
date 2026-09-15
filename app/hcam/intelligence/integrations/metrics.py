from __future__ import annotations

from collections import Counter


_OPERATIONS = frozenset({"manifest", "catalogue", "query", "job", "match", "review", "control", "workflow"})
_OUTCOMES = frozenset({"created", "duplicate", "changed", "unchanged", "succeeded", "failed", "denied", "abstained", "revoked"})


class IntegrationMetrics:
    def __init__(self) -> None:
        self._counts: Counter[tuple[str, str]] = Counter()

    def record(self, operation: str, outcome: str) -> None:
        if operation not in _OPERATIONS:
            raise ValueError("metric operation is not allowlisted")
        if outcome not in _OUTCOMES:
            raise ValueError("metric outcome is not allowlisted")
        self._counts[(operation, outcome)] += 1

    def snapshot(self) -> dict[str, int]:
        return {
            f"{operation}:{outcome}": value
            for (operation, outcome), value in sorted(self._counts.items())
        }
