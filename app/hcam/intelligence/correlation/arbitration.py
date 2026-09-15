from __future__ import annotations

from collections.abc import Sequence
from statistics import fmean, pstdev

from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.contracts import ArbitrationResultV1, LaneResultV1


class CorrelationArbitrationError(ValueError):
    """Raised when lane results violate the AMEC arbitration boundary."""


def arbitrate_lane_results(results: Sequence[LaneResultV1]) -> ArbitrationResultV1:
    ordered = sorted(results, key=lambda item: item.lane)
    if len({item.lane for item in ordered}) != len(ordered):
        raise CorrelationArbitrationError("lane results must be unique")
    deterministic = [item for item in ordered if item.lane == "deterministic_cpu"]
    if len(deterministic) != 1:
        raise CorrelationArbitrationError("exactly one deterministic lane is required")
    primary = deterministic[0]
    if primary.status != "completed" or primary.score is None or primary.uncertainty is None:
        state = "abstained"
        confidence = 0.0
        uncertainty = 1.0
        reasons = ["deterministic_lane_unavailable"]
    elif primary.abstained:
        state = "abstained"
        confidence = primary.score
        uncertainty = 1.0
        reasons = [
            "deterministic_policy_veto"
            if primary.contradiction_count
            else "insufficient_deterministic_evidence"
        ]
    else:
        completed = [
            item
            for item in ordered
            if item.status == "completed" and item.score is not None
        ]
        scores = [item.score for item in completed if item.score is not None]
        disagreement = pstdev(scores) if len(scores) > 1 else 0.0
        confidence = fmean(scores)
        uncertainty = max(
            primary.uncertainty,
            disagreement,
            *(item.uncertainty or 0.0 for item in completed),
        )
        confidence = max(0.0, min(1.0, confidence))
        uncertainty = max(0.0, min(1.0, uncertainty))
        state = "proposed"
        reasons = ["deterministic_evidence_satisfied"]
        if disagreement:
            reasons.append("lane_disagreement_preserved")
    material = {
        "state": state,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "reasons": reasons,
        "lanes": [item.model_dump(mode="json") for item in ordered],
    }
    return ArbitrationResultV1(
        state=state,
        confidence=confidence,
        uncertainty=uncertainty,
        abstained=state == "abstained",
        reason_codes=reasons,
        lane_results=ordered,
        contradiction_count=sum(item.contradiction_count for item in deterministic),
        arbitration_digest=canonical_sha256(material),
    )
