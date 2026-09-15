from __future__ import annotations

from collections import Counter


_OPERATIONS = frozenset(
    {
        "timeline",
        "entry",
        "evidence",
        "integrity",
        "provenance",
        "correction",
        "review",
        "relationship",
        "retention",
        "deletion",
        "export",
        "job",
    }
)
_OUTCOMES = frozenset(
    {"created", "duplicate", "succeeded", "partial", "blocked", "failed", "denied"}
)


class InvestigationMetrics:
    def __init__(self) -> None:
        self._counts: Counter[tuple[str, str]] = Counter()

    def record(self, operation: str, outcome: str) -> None:
        if operation not in _OPERATIONS or outcome not in _OUTCOMES:
            raise ValueError("metric labels are not allowlisted")
        self._counts[(operation, outcome)] += 1

    def snapshot(self) -> dict[str, int]:
        return {
            f"{operation}:{outcome}": count
            for (operation, outcome), count in sorted(self._counts.items())
        }
