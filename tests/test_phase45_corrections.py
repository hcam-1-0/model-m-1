from __future__ import annotations

from datetime import timedelta

import pytest

from hcam.intelligence.investigations.canonical import stable_id
from hcam.intelligence.investigations.contracts import CorrectionCommandV1
from hcam.intelligence.investigations.corrections import build_impact_set, propagation_state
from hcam.intelligence.investigations.jobs import ImpactJobState, claim, complete, fail
from hcam.intelligence.investigations.metrics import InvestigationMetrics


def test_correction_impact_closure_is_deterministic_and_bounded(p45_context: dict) -> None:
    target = stable_id("ref", "target")
    dependent = stable_id("ref", "dependent")
    export = stable_id("ref", "export")
    correction = CorrectionCommandV1(
        correction_id=stable_id("icor", target),
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        kind="retraction",
        target_type="entry",
        target_ref=target,
        target_version=1,
        actor_id=p45_context["actor"],
        reason=p45_context["reason"],
        delivery_id="generated.correction.1",
        recorded_at=p45_context["now"],
    )
    result = build_impact_set(
        correction,
        {target: [("hypothesis", dependent)], dependent: [("export", export)]},
        recorded_at=p45_context["now"],
    )
    assert [item.target_ref for item in result.impacts] == [dependent, export]
    assert result.propagation_state == "pending"
    assert propagation_state([]) == "complete"
    assert propagation_state(result.impacts) == "pending"
    assert propagation_state(
        [item.model_copy(update={"state": "blocked"}) for item in result.impacts]
    ) == "blocked"
    assert propagation_state(
        [item.model_copy(update={"state": "failed"}) for item in result.impacts]
    ) == "failed"
    assert propagation_state(
        [
            result.impacts[0].model_copy(update={"state": "applied"}),
            result.impacts[1].model_copy(update={"state": "blocked"}),
        ]
    ) == "partial"


def test_impact_job_retry_recovery_dead_letter_and_lease_ownership(p45_context: dict) -> None:
    job = ImpactJobState()
    leased = claim(job, worker_id="generated.worker", now=p45_context["now"])
    assert complete(leased, worker_id="generated.worker").state == "succeeded"
    retry = fail(leased, worker_id="generated.worker", transient=True)
    assert retry.state == "queued"
    expired = leased.__class__(
        state="leased",
        attempt_count=2,
        lease_owner="generated.old",
        lease_until=p45_context["now"] - timedelta(seconds=1),
        reason_code="impact.leased",
    )
    recovered = claim(expired, worker_id="generated.new", now=p45_context["now"])
    assert fail(recovered, worker_id="generated.new", transient=True).state == "dead_letter"
    assert fail(leased, worker_id="generated.worker", transient=False).state == "failed"
    with pytest.raises(ValueError, match="does not own"):
        complete(leased, worker_id="generated.other")
    with pytest.raises(ValueError, match="not claimable"):
        claim(leased, worker_id="generated.other", now=p45_context["now"])


def test_metrics_use_only_allowlisted_low_cardinality_labels() -> None:
    metrics = InvestigationMetrics()
    metrics.record("timeline", "created")
    assert metrics.snapshot() == {"timeline:created": 1}
    with pytest.raises(ValueError, match="allowlisted"):
        metrics.record("inv_sensitive_identifier", "created")
