from __future__ import annotations

from collections.abc import Sequence

from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.contracts import (
    CorrelationIngressEventV1,
    CorrelationProfileV1,
    CorrelationWindowV1,
    LaneResultV1,
)
from hcam.intelligence.correlation.lanes import DETERMINISTIC_LANE_VERSION


def evaluate_deterministic_lane(
    window: CorrelationWindowV1,
    events: Sequence[CorrelationIngressEventV1],
    profile: CorrelationProfileV1,
) -> LaneResultV1:
    event_ids = set(window.event_ids)
    selected = sorted(
        (item for item in events if item.event_id in event_ids),
        key=lambda item: (item.chronology.occurred_at, item.event_id),
    )
    if len(selected) != len(event_ids):
        return LaneResultV1(
            lane="deterministic_cpu",
            status="failed",
            abstained=True,
            failure_code="invalid_generated_input",
            lineage_digest=DETERMINISTIC_LANE_VERSION,
        )
    supporting = [item for item in selected if item.signals.signal_kind == "observation"]
    contradictions = [
        item for item in selected if item.signals.signal_kind == "contradiction"
    ]
    missing = [item for item in selected if item.signals.signal_kind == "absence"]
    stale = [item for item in selected if item.signals.signal_kind == "stale"]
    denominator = len(supporting) + len(contradictions) + len(missing) + len(stale)
    score = 0.0 if denominator == 0 else len(supporting) / denominator
    evidence_ids = [item.event_id for item in selected]
    policy_veto = len(contradictions) > profile.maximum_contradictions
    insufficient = len(supporting) < profile.minimum_supporting_events
    incomplete = window.completeness != "complete"
    abstained = policy_veto or insufficient or incomplete
    failure_code = None
    if policy_veto:
        failure_code = "policy_veto"
    elif insufficient or incomplete:
        failure_code = "insufficient_evidence"
    if abstained:
        return LaneResultV1(
            lane="deterministic_cpu",
            status="completed",
            score=score,
            uncertainty=1.0,
            abstained=True,
            evidence_ids=evidence_ids,
            contradiction_count=len(contradictions),
            lineage_digest=canonical_sha256(
                {
                    "implementation": DETERMINISTIC_LANE_VERSION,
                    "profile": profile.profile_version,
                    "window": window.window_id,
                    "reason": failure_code,
                }
            ),
        )
    uncertainty = max(0.0, min(1.0, 1.0 - score))
    return LaneResultV1(
        lane="deterministic_cpu",
        status="completed",
        score=score,
        uncertainty=uncertainty,
        abstained=False,
        evidence_ids=evidence_ids,
        contradiction_count=len(contradictions),
        lineage_digest=canonical_sha256(
            {
                "implementation": DETERMINISTIC_LANE_VERSION,
                "profile": profile.profile_version,
                "window": window.window_id,
                "evidence": evidence_ids,
            }
        ),
    )
