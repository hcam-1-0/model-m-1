from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hcam.intelligence.alerts.contracts import (
    LabEvaluationIngressV1,
    ProposedAlertCommandV1,
    ReviewQuorumPolicyV1,
)


DIGEST = "sha256:" + "a" * 64


def proposal() -> dict[str, object]:
    return {
        "delivery_id": "generated.delivery.1",
        "evaluation_id": "revl_" + "1" * 32,
        "evaluation_revision": 1,
        "evaluation_digest": DIGEST,
        "rule_record_id": "irlr_" + "2" * 32,
        "compilation_id": "rcmp_" + "3" * 32,
        "department": "generated-lab",
        "partition_digest": "sha256:" + "b" * 64,
        "occurred_at": datetime(2026, 1, 1, tzinfo=UTC),
        "evidence_refs": ["generated.evidence.1"],
        "incident_key": "generated.incident.1",
        "severity": "high",
        "priority": "urgent",
        "confidence": 0.8,
        "certainty": 0.7,
        "chronology_confidence": 0.9,
    }


def test_proposal_contract_is_strict_generated_and_nonoperational() -> None:
    item = ProposedAlertCommandV1.model_validate(proposal())
    assert item.generated_only is True and item.operational is False
    assert item.authority_class == "mandatory_review"
    invalid = deepcopy(proposal())
    invalid["authority_class"] = "bounded_automation"
    with pytest.raises(ValidationError):
        ProposedAlertCommandV1.model_validate(invalid)
    invalid = deepcopy(proposal())
    invalid["unexpected"] = "denied"
    with pytest.raises(ValidationError):
        ProposedAlertCommandV1.model_validate(invalid)


def test_system_health_and_lab_contracts_are_separately_typed() -> None:
    health = proposal()
    health.update({"domain": "system_health", "authority_class": "bounded_automation"})
    assert ProposedAlertCommandV1.model_validate(health).domain == "system_health"
    lab = LabEvaluationIngressV1(
        fixture_id="generated.lab.1",
        adapter_profile="lab1highadapter",
        camera_slot=50,
        media_profile="high",
        availability="available",
        sample_epoch=1,
        metadata_digest=DIGEST,
    )
    assert lab.network_locator is None and lab.media_payload is None
    with pytest.raises(ValidationError):
        LabEvaluationIngressV1.model_validate(
            {**lab.model_dump(), "network_locator": "https://example.invalid"}
        )


def test_quorum_contract_bounds_ordinary_and_high_impact_policies() -> None:
    base = {
        "policy_id": "generated.policy.1",
        "policy_version": 1,
        "department": "generated-lab",
        "permitted_roles": ["intelligence.reviewer"],
        "evidence_digest": DIGEST,
        "effective_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    assert ReviewQuorumPolicyV1(**base, workflow_class="ordinary").required_distinct_reviewers == 1
    assert ReviewQuorumPolicyV1(
        **base, workflow_class="generated_high_impact", required_distinct_reviewers=5
    ).required_distinct_reviewers == 5
    with pytest.raises(ValidationError):
        ReviewQuorumPolicyV1(
            **base, workflow_class="ordinary", required_distinct_reviewers=2
        )
