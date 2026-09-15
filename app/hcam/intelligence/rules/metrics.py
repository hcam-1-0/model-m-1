from __future__ import annotations

from collections import Counter


_ALLOWED_STAGES = {"compile", "evaluate", "persist", "lifecycle"}
_ALLOWED_OUTCOMES = {"succeeded", "failed", "pending", "suppressed", "abstained"}


class RuleMetrics:
    """In-memory low-cardinality metric recorder for the generated boundary."""

    def __init__(self) -> None:
        self.outcomes: Counter[tuple[str, str]] = Counter()

    def record(self, stage: str, outcome: str) -> None:
        if stage not in _ALLOWED_STAGES or outcome not in _ALLOWED_OUTCOMES:
            raise ValueError("rule metric label is not allowlisted")
        self.outcomes[(stage, outcome)] += 1
