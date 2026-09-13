from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hcam.intelligence.integrations.bounds import JOB_LEASE_SECONDS, MAX_JOB_ATTEMPTS
from hcam.intelligence.integrations.canonical import stable_id
from hcam.intelligence.integrations.contracts import CompiledQueryPlanV1, QueryJobV1


class JobStateError(RuntimeError):
    reason_code = "query_job_state_denied"


class JobQueue:
    def __init__(self) -> None:
        self._jobs: dict[str, QueryJobV1] = {}
        self._semantic_jobs: dict[str, str] = {}
        self._deliveries: dict[str, str] = {}

    def submit(
        self,
        plan: CompiledQueryPlanV1,
        *,
        now: datetime | None = None,
    ) -> tuple[QueryJobV1, bool]:
        current = now or datetime.now(UTC)
        if plan.delivery_key in self._deliveries:
            job = self._jobs[self._deliveries[plan.delivery_key]]
            if job.semantic_key != plan.semantic_key:
                raise JobStateError("delivery identity contains different material")
            return job, True
        if plan.semantic_key in self._semantic_jobs:
            job = self._jobs[self._semantic_jobs[plan.semantic_key]]
            self._deliveries[plan.delivery_key] = job.job_id
            return job, True
        job_id = stable_id("rjob", plan.department, plan.semantic_key)
        job = QueryJobV1(
            job_id=job_id,
            query_id=plan.query_id,
            department=plan.department,
            state="queued",
            reason_code="query.queued",
            plan_digest=plan.plan_digest,
            semantic_key=plan.semantic_key,
            delivery_key=plan.delivery_key,
            created_at=current,
            updated_at=current,
        )
        self._jobs[job_id] = job
        self._semantic_jobs[plan.semantic_key] = job_id
        self._deliveries[plan.delivery_key] = job_id
        return job, False

    def claim(
        self,
        worker_id: str,
        *,
        now: datetime | None = None,
    ) -> QueryJobV1 | None:
        current = now or datetime.now(UTC)
        eligible = []
        for job in self._jobs.values():
            if job.state == "queued" or (
                job.state == "leased"
                and job.lease_until is not None
                and job.lease_until <= current
            ):
                eligible.append(job)
        if not eligible:
            return None
        prior = sorted(eligible, key=lambda item: (item.created_at, item.job_id))[0]
        claimed = prior.model_copy(
            update={
                "state": "leased",
                "attempt_count": prior.attempt_count + 1,
                "lease_owner": worker_id,
                "lease_until": current + timedelta(seconds=JOB_LEASE_SECONDS),
                "reason_code": "query.leased",
                "updated_at": current,
            }
        )
        claimed = QueryJobV1.model_validate(claimed.model_dump(mode="json"))
        self._jobs[claimed.job_id] = claimed
        return claimed

    def complete(
        self,
        job_id: str,
        worker_id: str,
        result_digest: str,
        *,
        now: datetime | None = None,
    ) -> QueryJobV1:
        job = self._leased(job_id, worker_id)
        updated = job.model_copy(
            update={
                "state": "succeeded",
                "lease_owner": None,
                "lease_until": None,
                "reason_code": "query.succeeded",
                "result_digest": result_digest,
                "updated_at": now or datetime.now(UTC),
            }
        )
        return self._store(updated)

    def fail(
        self,
        job_id: str,
        worker_id: str,
        *,
        transient: bool,
        reason_code: str,
        now: datetime | None = None,
    ) -> QueryJobV1:
        job = self._leased(job_id, worker_id)
        retry = transient and job.attempt_count < MAX_JOB_ATTEMPTS
        updated = job.model_copy(
            update={
                "state": "queued" if retry else "failed",
                "lease_owner": None,
                "lease_until": None,
                "reason_code": "query.retry_queued" if retry else reason_code,
                "updated_at": now or datetime.now(UTC),
            }
        )
        return self._store(updated)

    def cancel(self, job_id: str, *, now: datetime | None = None) -> QueryJobV1:
        job = self.get(job_id)
        if job.state not in {"queued", "leased"}:
            raise JobStateError("only active jobs can be cancelled")
        return self._store(
            job.model_copy(
                update={
                    "state": "cancelled",
                    "lease_owner": None,
                    "lease_until": None,
                    "reason_code": "query.cancelled",
                    "updated_at": now or datetime.now(UTC),
                }
            )
        )

    def quarantine(self, job_id: str, *, now: datetime | None = None) -> QueryJobV1:
        job = self.get(job_id)
        if job.state in {"succeeded", "failed", "cancelled", "quarantined"}:
            raise JobStateError("terminal jobs cannot be quarantined again")
        return self._store(
            job.model_copy(
                update={
                    "state": "quarantined",
                    "lease_owner": None,
                    "lease_until": None,
                    "reason_code": "query.revoked",
                    "updated_at": now or datetime.now(UTC),
                }
            )
        )

    def get(self, job_id: str) -> QueryJobV1:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise JobStateError("query job was not found") from exc

    def list(self, *, department: str | None = None) -> list[QueryJobV1]:
        values = self._jobs.values()
        if department is not None:
            values = (item for item in values if item.department == department)
        return sorted(values, key=lambda item: (item.created_at, item.job_id))

    def _leased(self, job_id: str, worker_id: str) -> QueryJobV1:
        job = self.get(job_id)
        if job.state != "leased" or job.lease_owner != worker_id:
            raise JobStateError("worker does not own the active lease")
        return job

    def _store(self, candidate: QueryJobV1) -> QueryJobV1:
        validated = QueryJobV1.model_validate(candidate.model_dump(mode="json"))
        self._jobs[validated.job_id] = validated
        return validated
