from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from hcam.intelligence.investigations.bounds import JOB_LEASE_SECONDS, MAX_JOB_ATTEMPTS


@dataclass(frozen=True, slots=True)
class ImpactJobState:
    state: str = "queued"
    attempt_count: int = 0
    lease_owner: str | None = None
    lease_until: datetime | None = None
    reason_code: str = "impact.queued"


def claim(job: ImpactJobState, *, worker_id: str, now: datetime) -> ImpactJobState:
    recoverable = job.state == "leased" and job.lease_until is not None and job.lease_until <= now
    if job.state != "queued" and not recoverable:
        raise ValueError("impact job is not claimable")
    return replace(
        job,
        state="leased",
        attempt_count=job.attempt_count + 1,
        lease_owner=worker_id,
        lease_until=now + timedelta(seconds=JOB_LEASE_SECONDS),
        reason_code="impact.leased",
    )


def complete(job: ImpactJobState, *, worker_id: str) -> ImpactJobState:
    _require_lease(job, worker_id)
    return replace(
        job,
        state="succeeded",
        lease_owner=None,
        lease_until=None,
        reason_code="impact.complete",
    )


def fail(
    job: ImpactJobState,
    *,
    worker_id: str,
    transient: bool,
) -> ImpactJobState:
    _require_lease(job, worker_id)
    retry = transient and job.attempt_count < MAX_JOB_ATTEMPTS
    return replace(
        job,
        state="queued" if retry else ("dead_letter" if transient else "failed"),
        lease_owner=None,
        lease_until=None,
        reason_code="impact.retry_queued" if retry else "impact.failed",
    )


def _require_lease(job: ImpactJobState, worker_id: str) -> None:
    if job.state != "leased" or job.lease_owner != worker_id:
        raise ValueError("worker does not own the impact-job lease")
