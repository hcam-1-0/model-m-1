from __future__ import annotations

from datetime import datetime, timedelta

from hcam.operations.platform.contracts import FailureV1, WorkerJobV1
from hcam.operations.platform.failures import may_retry


class WorkerStateError(RuntimeError):
    pass


def claim(job: WorkerJobV1, *, owner: str, now: datetime) -> WorkerJobV1:
    if job.state != "queued":
        raise WorkerStateError("only queued work can be claimed")
    return job.model_copy(
        update={
            "state": "leased",
            "lease_owner": owner,
            "lease_until": now + timedelta(seconds=90),
            "updated_at": now,
            "reason_code": "worker.claimed",
        }
    )


def heartbeat(job: WorkerJobV1, *, owner: str, now: datetime) -> WorkerJobV1:
    _require_live_lease(job, owner=owner, now=now)
    return job.model_copy(update={"lease_until": now + timedelta(seconds=90), "updated_at": now})


def complete(job: WorkerJobV1, *, owner: str, now: datetime) -> WorkerJobV1:
    _require_live_lease(job, owner=owner, now=now)
    return job.model_copy(
        update={
            "state": "succeeded",
            "lease_owner": None,
            "lease_until": None,
            "updated_at": now,
            "reason_code": "worker.completed",
        }
    )


def fail(job: WorkerJobV1, record: FailureV1, *, owner: str, now: datetime) -> WorkerJobV1:
    _require_live_lease(job, owner=owner, now=now)
    attempts = job.attempt_count + 1
    retry = may_retry(record, attempt_count=attempts)
    return job.model_copy(
        update={
            "state": "queued" if retry else ("dead_letter" if attempts >= 3 else "failed"),
            "attempt_count": attempts,
            "lease_owner": None,
            "lease_until": None,
            "updated_at": now,
            "reason_code": record.code,
        }
    )


def recover_abandoned(job: WorkerJobV1, *, now: datetime) -> WorkerJobV1:
    if job.state != "leased" or job.lease_until is None or job.lease_until > now:
        raise WorkerStateError("job lease is not abandoned")
    state = "dead_letter" if job.attempt_count >= 3 else "queued"
    return job.model_copy(
        update={
            "state": state,
            "lease_owner": None,
            "lease_until": None,
            "updated_at": now,
            "reason_code": "worker.lease_recovered",
        }
    )


def retry_delay_seconds(job_id: str, attempt_count: int) -> int:
    if not 1 <= attempt_count <= 3:
        raise ValueError("attempt count must be between one and three")
    bases = (30, 120, 300)
    jitter = sum(job_id.encode("ascii")) % 17
    return bases[attempt_count - 1] + jitter


def _require_live_lease(job: WorkerJobV1, *, owner: str, now: datetime) -> None:
    if job.state != "leased" or job.lease_owner != owner:
        raise WorkerStateError("worker does not own the lease")
    if job.lease_until is None or job.lease_until <= now:
        raise WorkerStateError("worker lease was lost")
