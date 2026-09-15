from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hcam.intelligence.alerts.contracts import (
    AlertAggregateV2,
    AlertLifecycleCommandV1,
    ProposedAlertCommandV1,
)
from hcam.intelligence.alerts.identity import derive_alert_identity
from hcam.intelligence.alerts.lifecycle import AlertTransitionDenied, apply_transition
from tests.test_phase43_contracts import DIGEST, proposal


def aggregate() -> AlertAggregateV2:
    source = ProposedAlertCommandV1.model_validate(proposal())
    identity = derive_alert_identity(source)
    return AlertAggregateV2(
        alert_id=identity.alert_id,
        version=1,
        department=source.department,
        semantic_key=identity.semantic_key,
        delivery_key=identity.delivery_key,
        source_evaluation_id=source.evaluation_id,
        source_evaluation_revision=1,
        source_evaluation_digest=source.evaluation_digest,
        incident_key=source.incident_key,
        state="proposed",
        domain=source.domain,
        authority_class=source.authority_class,
        severity=source.severity,
        priority=source.priority,
        confidence=source.confidence,
        certainty=source.certainty,
        chronology_confidence=source.chronology_confidence,
        disposition="unreviewed",
        evidence_refs=source.evidence_refs,
        policy_digest=DIGEST,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def command(action: str, version: int, **values) -> AlertLifecycleCommandV1:
    return AlertLifecycleCommandV1(
        command_id=f"generated.command.{version}.{action}",
        action=action,
        expected_version=version,
        actor_id="generated-reviewer",
        reason="Generated lifecycle decision",
        **values,
    )


def test_complete_review_lifecycle_is_deterministic() -> None:
    item = aggregate()
    for index, (action, state) in enumerate(
        (("queue_review", "queued_review"), ("start_review", "under_review"), ("accept", "accepted"), ("resolve", "resolved")),
        start=1,
    ):
        item, event = apply_transition(
            item,
            command(action, item.version),
            now=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=index),
        )
        assert item.state == state and event.sequence == item.version
    assert item.disposition == "approved"


def test_stale_invalid_and_unbounded_reason_transitions_fail_closed() -> None:
    item = aggregate()
    with pytest.raises(AlertTransitionDenied):
        apply_transition(item, command("resolve", 1), now=datetime.now(UTC))
    with pytest.raises(AlertTransitionDenied):
        apply_transition(item, command("queue_review", 2), now=datetime.now(UTC))
    with pytest.raises(ValueError):
        apply_transition(
            item,
            command("queue_review", 1).model_copy(update={"reason": " short"}),
            now=datetime.now(UTC),
        )


@pytest.mark.parametrize(
    ("start_state", "start_version", "action", "expected_state", "disposition"),
    [
        ("under_review", 3, "reject", "rejected", "denied"),
        ("under_review", 3, "request_information", "queued_review", "needs_information"),
        ("accepted", 4, "correct", "corrected", "corrected"),
    ],
)
def test_review_dispositions_remain_separate_from_lifecycle_state(
    start_state: str,
    start_version: int,
    action: str,
    expected_state: str,
    disposition: str,
) -> None:
    item = aggregate().model_copy(update={"state": start_state, "version": start_version})
    updated, _ = apply_transition(
        item,
        command(action, start_version),
        now=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
    )
    assert updated.state == expected_state
    assert updated.disposition == disposition
