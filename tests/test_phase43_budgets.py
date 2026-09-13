from __future__ import annotations

from datetime import UTC, datetime

import pytest

from hcam.intelligence.alerts.budgets import BudgetObservation, evaluate_budget
from hcam.intelligence.alerts.contracts import AlertBudgetPolicyV1, ProposedAlertCommandV1
from tests.test_phase43_contracts import DIGEST, proposal


def policy(department: str = "generated-lab") -> AlertBudgetPolicyV1:
    return AlertBudgetPolicyV1(
        policy_id="generated.budget",
        version=1,
        department=department,
        limits=[
            {"scope": "rule", "scope_key": "generated.rule", "window_seconds": 60, "limit": 2},
            {"scope": "department", "scope_key": "generated-lab", "window_seconds": 60, "limit": 5},
        ],
        policy_digest=DIGEST,
    )


def test_hierarchical_budget_admits_or_collapses_with_loss_accounting() -> None:
    command = ProposedAlertCommandV1.model_validate(proposal())
    admitted = evaluate_budget(command, policy(), [])
    assert admitted.admitted is True and admitted.represented_alerts == 1
    observations = [BudgetObservation("rule", "generated.rule", datetime.now(UTC), 4)]
    collapsed = evaluate_budget(command, policy(), observations)
    assert collapsed.admitted is False
    assert collapsed.collapse_key is not None
    assert collapsed.represented_alerts == 4
    assert collapsed.suppressed_alerts == 3
    assert collapsed == evaluate_budget(command, policy(), observations)


def test_cross_department_budget_is_denied() -> None:
    with pytest.raises(ValueError):
        evaluate_budget(ProposedAlertCommandV1.model_validate(proposal()), policy("other"), [])
