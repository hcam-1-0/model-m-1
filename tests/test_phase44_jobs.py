from __future__ import annotations

from datetime import timedelta

import pytest

from hcam.intelligence.integrations.jobs import JobQueue, JobStateError
from hcam.intelligence.integrations.policy import compile_query_plan
from tests.test_phase44_contracts import NOW, intent, manifest


def test_jobs_deduplicate_recover_leases_retry_and_complete() -> None:
    provider = manifest()
    plan = compile_query_plan(intent(provider), provider, control_enabled=True)
    queue = JobQueue()
    job, reused = queue.submit(plan, now=NOW)
    assert reused is False
    assert queue.submit(plan, now=NOW)[1] is True
    leased = queue.claim("generated.worker", now=NOW)
    assert leased is not None and leased.state == "leased"
    assert queue.claim("generated.worker.2", now=NOW) is None
    recovered = queue.claim("generated.worker.2", now=NOW + timedelta(seconds=91))
    assert recovered is not None and recovered.attempt_count == 2
    retried = queue.fail(
        job.job_id,
        "generated.worker.2",
        transient=True,
        reason_code="provider.transient",
        now=NOW + timedelta(seconds=92),
    )
    assert retried.state == "queued"
    final_lease = queue.claim("generated.worker.3", now=NOW + timedelta(seconds=93))
    assert final_lease is not None and final_lease.attempt_count == 3
    completed = queue.complete(
        job.job_id,
        "generated.worker.3",
        "sha256:" + "1" * 64,
        now=NOW + timedelta(seconds=94),
    )
    assert completed.state == "succeeded"


def test_job_cancellation_quarantine_and_invalid_lease_fail_closed() -> None:
    provider = manifest()
    plan = compile_query_plan(intent(provider), provider, control_enabled=True)
    queue = JobQueue()
    job, _ = queue.submit(plan, now=NOW)
    assert queue.cancel(job.job_id, now=NOW).state == "cancelled"
    with pytest.raises(JobStateError):
        queue.cancel(job.job_id, now=NOW)
    other_plan = plan.model_copy(
        update={
            "query_id": "qry_" + "2" * 32,
            "semantic_key": "sha256:" + "2" * 64,
            "delivery_key": "sha256:" + "3" * 64,
        }
    )
    other, _ = queue.submit(other_plan, now=NOW)
    assert queue.quarantine(other.job_id, now=NOW).state == "quarantined"
    with pytest.raises(JobStateError):
        queue.complete(other.job_id, "generated.worker", "sha256:" + "4" * 64)
