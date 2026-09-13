from __future__ import annotations

from hcam.intelligence.integrations.canonical import digest, stable_id
from hcam.intelligence.integrations.contracts import QueryJobV1, WorkflowExecutionV1


class GeneratedWorkflowExecutor:
    def __init__(self) -> None:
        self._executions: dict[str, WorkflowExecutionV1] = {}

    def execute(
        self,
        job: QueryJobV1,
        *,
        outcome: str = "accepted",
    ) -> WorkflowExecutionV1:
        execution_id = stable_id("wexec", job.job_id, job.attempt_count)
        if execution_id in self._executions:
            prior = self._executions[execution_id]
            return WorkflowExecutionV1.model_validate(
                prior.model_copy(
                    update={
                        "outcome": "duplicate",
                        "reason_code": "workflow.duplicate",
                    }
                ).model_dump(mode="json")
            )
        if outcome not in {"accepted", "timeout", "cancelled", "revoked", "late"}:
            raise ValueError("workflow outcome is not allowlisted")
        material = {
            "job_id": job.job_id,
            "attempt_count": job.attempt_count,
            "outcome": outcome,
        }
        execution = WorkflowExecutionV1(
            execution_id=execution_id,
            job_id=job.job_id,
            adapter_kind="generated_simulator",
            outcome=outcome,
            reason_code=f"workflow.{outcome}",
            result_digest=digest(material) if outcome == "accepted" else None,
        )
        self._executions[execution_id] = execution
        return execution


class DisabledWorkflowDispatchAdapter:
    def execute(self, job: QueryJobV1) -> WorkflowExecutionV1:
        return WorkflowExecutionV1(
            execution_id=stable_id("wexec", job.job_id, "disabled"),
            job_id=job.job_id,
            adapter_kind="future_disabled",
            outcome="disabled",
            reason_code="workflow.adapter_disabled",
        )
