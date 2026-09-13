from __future__ import annotations

from datetime import datetime

from hcam.intelligence.alerts.bounds import bounded_reason
from hcam.intelligence.alerts.canonical import stable_id
from hcam.intelligence.alerts.contracts import (
    AlertAggregateV2,
    AlertLifecycleCommandV1,
    AlertLifecycleEventV2,
    AlertState,
)


TRANSITIONS: dict[str, dict[str, AlertState]] = {
    "proposed": {"queue_review": "queued_review", "suppress": "suppressed", "merge": "merged"},
    "queued_review": {"start_review": "under_review", "suppress": "suppressed", "merge": "merged"},
    "under_review": {
        "accept": "accepted",
        "reject": "rejected",
        "request_information": "queued_review",
        "suppress": "suppressed",
    },
    "accepted": {"resolve": "resolved", "correct": "corrected"},
    "rejected": {"correct": "corrected"},
    "resolved": {"reopen": "queued_review", "correct": "corrected"},
    "corrected": {"queue_review": "queued_review"},
    "suppressed": {"reopen": "queued_review"},
    "merged": {},
}


class AlertTransitionDenied(ValueError):
    pass


def target_state(current: AlertState, action: str) -> AlertState:
    try:
        return TRANSITIONS[current][action]
    except KeyError as exc:
        raise AlertTransitionDenied("alert lifecycle transition is not allowed") from exc


def apply_transition(
    aggregate: AlertAggregateV2,
    command: AlertLifecycleCommandV1,
    *,
    now: datetime,
) -> tuple[AlertAggregateV2, AlertLifecycleEventV2]:
    if command.expected_version != aggregate.version:
        raise AlertTransitionDenied("alert version does not match")
    bounded_reason(command.reason)
    next_state = target_state(aggregate.state, command.action)
    merged_into = command.target_alert_id if next_state == "merged" else None
    suppression_code = "manual_suppression" if next_state == "suppressed" else None
    disposition = aggregate.disposition
    if command.action == "accept":
        disposition = "approved"
    elif command.action == "reject":
        disposition = "denied"
    elif command.action == "request_information":
        disposition = "needs_information"
    elif command.action == "correct":
        disposition = "corrected"
    updated = aggregate.model_copy(
        update={
            "version": aggregate.version + 1,
            "state": next_state,
            "updated_at": now,
            "disposition": disposition,
            "merged_into": merged_into,
            "suppression_code": suppression_code,
        }
    )
    event = AlertLifecycleEventV2(
        event_id=stable_id("alfe", aggregate.alert_id, updated.version, command.command_id),
        alert_id=aggregate.alert_id,
        sequence=updated.version,
        department=aggregate.department,
        previous_state=aggregate.state,
        new_state=next_state,
        action=command.action,
        actor_id=command.actor_id,
        reason=command.reason,
        evidence_digest=command.evidence_digest,
        recorded_at=now,
    )
    return updated, event
