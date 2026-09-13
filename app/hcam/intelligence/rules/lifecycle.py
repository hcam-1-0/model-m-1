from __future__ import annotations

from dataclasses import dataclass


RULE_STATUSES = frozenset(
    {"draft", "validated", "approved", "shadow", "suspended", "retired"}
)
_TRANSITIONS = {
    "draft": frozenset({"validated", "retired"}),
    "validated": frozenset({"approved", "retired"}),
    "approved": frozenset({"shadow", "suspended", "retired"}),
    "shadow": frozenset({"suspended", "retired"}),
    "suspended": frozenset({"approved", "shadow", "retired"}),
    "retired": frozenset(),
}


class RuleLifecycleError(ValueError):
    """A rule lifecycle transition is prohibited or insufficiently bound."""


@dataclass(frozen=True, slots=True)
class LifecycleDecision:
    from_status: str
    to_status: str
    requires_compilation: bool
    nonoperational: bool = True


def validate_transition(
    from_status: str,
    to_status: str,
    *,
    has_compilation: bool,
) -> LifecycleDecision:
    if from_status == "active" or to_status == "active":
        raise RuleLifecycleError("active rule state is unavailable")
    if from_status not in RULE_STATUSES or to_status not in RULE_STATUSES:
        raise RuleLifecycleError("rule status is unknown")
    if to_status not in _TRANSITIONS[from_status]:
        raise RuleLifecycleError("rule lifecycle transition is not allowed")
    requires_compilation = to_status in {"validated", "approved", "shadow"}
    if requires_compilation and not has_compilation:
        raise RuleLifecycleError(
            "rule lifecycle transition requires an immutable compilation"
        )
    return LifecycleDecision(from_status, to_status, requires_compilation)


def validate_rollback_target(
    current_version: int, target_version: int, target_status: str
) -> None:
    if target_version < 1 or target_version >= current_version:
        raise RuleLifecycleError(
            "rollback must select an earlier immutable rule version"
        )
    if target_status not in {"approved", "shadow", "suspended"}:
        raise RuleLifecycleError("rollback target is not an accepted immutable version")
