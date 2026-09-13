from __future__ import annotations

from datetime import UTC, datetime

from hcam.intelligence.alerts.adapters import (
    DisabledWorkflowAdapter,
    GeneratedLabEvaluationIngressAdapter,
    GeneratedWorkflowExecutor,
)
from hcam.intelligence.alerts.contracts import (
    AlertTimerIntentV1,
    LabEvaluationIngressV1,
    WorkflowExecutionRequestV1,
)
from tests.test_phase43_contracts import DIGEST


def request(kind: str) -> WorkflowExecutionRequestV1:
    timer = AlertTimerIntentV1(
        timer_id="atmr_" + "1" * 32,
        alert_id="alt_" + "2" * 32,
        department="generated-lab",
        timer_kind="review_sla",
        due_at=datetime(2026, 1, 1, tzinfo=UTC),
        state="leased",
        attempt_count=1,
        lease_owner="worker-1",
        lease_until=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        expected_alert_version=1,
        payload_digest=DIGEST,
    )
    return WorkflowExecutionRequestV1(
        execution_id="awfx_" + "3" * 32,
        timer=timer,
        adapter_kind=kind,
    )


def test_generated_and_future_workflow_adapters_are_explicit() -> None:
    assert GeneratedWorkflowExecutor().execute(request("local_bounded")).outcome == "applied"
    assert GeneratedWorkflowExecutor().execute(request("generated_simulator")).outcome == "applied"
    assert GeneratedWorkflowExecutor().execute(request("future_disabled")).outcome == "adapter_disabled"
    assert DisabledWorkflowAdapter().execute(request("local_bounded")).outcome == "adapter_disabled"


def test_lab_adapter_is_sanitized_generated_metadata_only() -> None:
    item = LabEvaluationIngressV1(
        fixture_id="generated.lab.1",
        adapter_profile="lab2lowadapter",
        camera_slot=30,
        media_profile="medium",
        availability="degraded",
        sample_epoch=1,
        metadata_digest=DIGEST,
    )
    assert GeneratedLabEvaluationIngressAdapter().normalize(item) == item
    assert item.network_locator is None and item.credential_ref is None and item.media_payload is None
