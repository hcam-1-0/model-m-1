from __future__ import annotations

from datetime import timedelta

from hcam.intelligence.alerts.bounds import MAX_TIMER_ATTEMPTS, TIMER_LEASE_SECONDS
from hcam.intelligence.alerts.contracts import AlertTimerIntentV1


class TimerClaimDenied(ValueError):
    pass


def claim_timer(
    timer: AlertTimerIntentV1,
    *,
    worker_id: str,
    now,
) -> AlertTimerIntentV1:
    lease_active = timer.lease_until is not None and timer.lease_until > now
    if timer.state not in {"pending", "leased"} or lease_active or timer.due_at > now:
        raise TimerClaimDenied("timer is not claimable")
    if timer.attempt_count >= MAX_TIMER_ATTEMPTS:
        raise TimerClaimDenied("timer attempts are exhausted")
    return timer.model_copy(
        update={
            "state": "leased",
            "attempt_count": timer.attempt_count + 1,
            "lease_owner": worker_id,
            "lease_until": now + timedelta(seconds=TIMER_LEASE_SECONDS),
        }
    )


def complete_timer(
    timer: AlertTimerIntentV1, *, worker_id: str, alert_version: int
) -> AlertTimerIntentV1:
    if timer.state != "leased" or timer.lease_owner != worker_id:
        raise TimerClaimDenied("timer lease does not belong to worker")
    if timer.expected_alert_version != alert_version:
        return timer.model_copy(
            update={"state": "cancelled", "lease_owner": None, "lease_until": None}
        )
    return timer.model_copy(
        update={"state": "completed", "lease_owner": None, "lease_until": None}
    )


def fail_timer(timer: AlertTimerIntentV1, *, worker_id: str) -> AlertTimerIntentV1:
    if timer.state != "leased" or timer.lease_owner != worker_id:
        raise TimerClaimDenied("timer lease does not belong to worker")
    state = "failed" if timer.attempt_count >= MAX_TIMER_ATTEMPTS else "pending"
    return timer.model_copy(
        update={"state": state, "lease_owner": None, "lease_until": None}
    )
