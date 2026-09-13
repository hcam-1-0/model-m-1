from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hcam.intelligence.alerts.contracts import AlertTimerIntentV1
from hcam.intelligence.alerts.timers import TimerClaimDenied, claim_timer, complete_timer, fail_timer
from tests.test_phase43_contracts import DIGEST


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def timer(**changes) -> AlertTimerIntentV1:
    values = {
        "timer_id": "atmr_" + "1" * 32,
        "alert_id": "alt_" + "2" * 32,
        "department": "generated-lab",
        "timer_kind": "review_sla",
        "due_at": NOW,
        "state": "pending",
        "attempt_count": 0,
        "expected_alert_version": 3,
        "payload_digest": DIGEST,
    }
    values.update(changes)
    return AlertTimerIntentV1(**values)


def test_timer_claim_complete_stale_and_retry_are_bounded() -> None:
    claimed = claim_timer(timer(), worker_id="worker-1", now=NOW)
    assert claimed.state == "leased" and claimed.attempt_count == 1
    assert complete_timer(claimed, worker_id="worker-1", alert_version=3).state == "completed"
    assert complete_timer(claimed, worker_id="worker-1", alert_version=4).state == "cancelled"
    assert fail_timer(claimed, worker_id="worker-1").state == "pending"
    exhausted = claim_timer(timer(attempt_count=2), worker_id="worker-1", now=NOW)
    assert fail_timer(exhausted, worker_id="worker-1").state == "failed"


def test_timer_rejects_early_active_exhausted_and_foreign_worker_claims() -> None:
    cases = (
        timer(due_at=NOW + timedelta(seconds=1)),
        timer(state="leased", lease_owner="other", lease_until=NOW + timedelta(seconds=1)),
        timer(attempt_count=3),
    )
    for item in cases:
        with pytest.raises(TimerClaimDenied):
            claim_timer(item, worker_id="worker-1", now=NOW)
    with pytest.raises(TimerClaimDenied):
        complete_timer(timer(), worker_id="worker-1", alert_version=3)
    with pytest.raises(TimerClaimDenied):
        fail_timer(timer(state="leased", lease_owner="other", lease_until=NOW), worker_id="worker-1")
