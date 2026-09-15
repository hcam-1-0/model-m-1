from __future__ import annotations

from typing import Protocol

from hcam.intelligence.alerts.contracts import (
    LabEvaluationIngressV1,
    WorkflowExecutionRequestV1,
    WorkflowExecutionResultV1,
)


class WorkflowExecutionAdapter(Protocol):
    def execute(self, request: WorkflowExecutionRequestV1) -> WorkflowExecutionResultV1: ...


class GeneratedWorkflowExecutor:
    def execute(self, request: WorkflowExecutionRequestV1) -> WorkflowExecutionResultV1:
        if request.adapter_kind not in {"local_bounded", "generated_simulator"}:
            return WorkflowExecutionResultV1(
                execution_id=request.execution_id,
                outcome="adapter_disabled",
                reason_code="future_adapter_disabled",
            )
        return WorkflowExecutionResultV1(
            execution_id=request.execution_id,
            outcome="applied",
            reason_code="generated_execution_applied",
        )


class DisabledWorkflowAdapter:
    def execute(self, request: WorkflowExecutionRequestV1) -> WorkflowExecutionResultV1:
        return WorkflowExecutionResultV1(
            execution_id=request.execution_id,
            outcome="adapter_disabled",
            reason_code="external_workflow_adapter_disabled",
        )


class LabEvaluationIngressAdapter(Protocol):
    def normalize(self, value: LabEvaluationIngressV1) -> LabEvaluationIngressV1: ...


class GeneratedLabEvaluationIngressAdapter:
    def normalize(self, value: LabEvaluationIngressV1) -> LabEvaluationIngressV1:
        return LabEvaluationIngressV1.model_validate(value.model_dump(mode="json"))
