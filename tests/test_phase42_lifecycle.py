from __future__ import annotations

import pytest

from hcam.intelligence.rules.lifecycle import (
    RULE_STATUSES,
    RuleLifecycleError,
    validate_rollback_target,
    validate_transition,
)


def test_lifecycle_happy_path_is_nonoperational() -> None:
    path = ["draft", "validated", "approved", "shadow", "suspended", "retired"]
    for current, target in zip(path, path[1:], strict=False):
        decision = validate_transition(current, target, has_compilation=True)
        assert decision.nonoperational is True
    assert "active" not in RULE_STATUSES


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("draft", "approved"),
        ("validated", "shadow"),
        ("shadow", "approved"),
        ("retired", "draft"),
        ("approved", "active"),
        ("active", "retired"),
    ],
)
def test_lifecycle_rejects_skips_reactivation_and_active(
    current: str, target: str
) -> None:
    with pytest.raises(RuleLifecycleError):
        validate_transition(current, target, has_compilation=True)


def test_compilation_is_required_and_rollback_selects_prior_immutable_version() -> None:
    with pytest.raises(RuleLifecycleError, match="compilation"):
        validate_transition("draft", "validated", has_compilation=False)
    validate_rollback_target(4, 2, "approved")
    with pytest.raises(RuleLifecycleError):
        validate_rollback_target(4, 4, "approved")
    with pytest.raises(RuleLifecycleError):
        validate_rollback_target(4, 2, "draft")
