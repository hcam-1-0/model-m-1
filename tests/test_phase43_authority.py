from __future__ import annotations

import pytest

from hcam.intelligence.alerts.authority import (
    AuthorityDenied,
    authorize_action,
    validate_proposal_authority,
    validate_system_health_action,
)
from hcam.intelligence.alerts.contracts import (
    ProposedAlertCommandV1,
    SystemHealthActionV1,
)
from tests.test_phase43_contracts import proposal


def test_police_intelligence_allows_review_routing_but_denies_automation() -> None:
    command = ProposedAlertCommandV1.model_validate(proposal())
    authorize_action(command, "queue_review")
    with pytest.raises(AuthorityDenied):
        authorize_action(command, "resolve_synthetic_health")


def test_system_health_has_only_three_bounded_generated_actions() -> None:
    value = {**proposal(), "domain": "system_health", "authority_class": "bounded_automation"}
    command = ProposedAlertCommandV1.model_validate(value)
    for action in ("route", "suppress_duplicate", "resolve_synthetic_health"):
        authorize_action(command, action)
    with pytest.raises(AuthorityDenied):
        authorize_action(command, "dispatch")


def test_authority_guards_fail_closed_even_for_unvalidated_internal_objects() -> None:
    police = ProposedAlertCommandV1.model_validate(proposal())
    invalid_police = police.model_copy(update={"authority_class": "bounded_automation"})
    with pytest.raises(AuthorityDenied, match="cannot use automation"):
        validate_proposal_authority(invalid_police)
    invalid_domain = police.model_copy(update={"domain": "unknown"})
    with pytest.raises(AuthorityDenied, match="do not match"):
        validate_proposal_authority(invalid_domain)

    health = ProposedAlertCommandV1.model_validate(
        {**proposal(), "domain": "system_health", "authority_class": "bounded_automation"}
    )
    action = SystemHealthActionV1(
        alert_id="alt_" + "f" * 32,
        action="route",
        policy_digest=health.evaluation_digest,
    )
    validate_system_health_action(health, action)
    with pytest.raises(AuthorityDenied, match="cannot consume"):
        validate_system_health_action(police, action)
    with pytest.raises(AuthorityDenied, match="not allowlisted"):
        validate_system_health_action(
            health, action.model_copy(update={"action": "dispatch"})
        )
