from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import datetime

from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.bounds import MAX_CORRELATION_DOCUMENT_BYTES
from hcam.intelligence.correlation.contracts import (
    ArbitrationResultV1,
    CorrelationChronologyV1,
    CorrelationEvidenceV1,
    CorrelationFlatProjectionV1,
    CorrelationGraphEdgeV1,
    CorrelationGraphNodeV1,
    CorrelationGraphV1,
    CorrelationHypothesisV2,
    CorrelationIngressEventV1,
    CorrelationProfileV1,
    CorrelationWindowV1,
    HypothesisRevisionV1,
)


def _identifier(prefix: str, material: str) -> str:
    return prefix + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _evidence_role(event: CorrelationIngressEventV1) -> str:
    return {
        "observation": "supports",
        "contradiction": "contradicts",
        "absence": "missing",
        "stale": "stale",
        "correction": "supersedes",
        "retraction": "retracts",
    }[event.signals.signal_kind]


def build_hypothesis(
    run_id: str,
    window: CorrelationWindowV1,
    events: Sequence[CorrelationIngressEventV1],
    profile: CorrelationProfileV1,
    arbitration: ArbitrationResultV1,
) -> CorrelationHypothesisV2:
    selected = sorted(
        (item for item in events if item.event_id in set(window.event_ids)),
        key=lambda item: (item.chronology.occurred_at, item.event_id),
    )
    hypothesis_key = canonical_sha256(
        {
            "department": window.department,
            "profile": profile.profile_version,
            "partition": window.partition_digest,
            "window_start": window.window_start.isoformat(),
            "window_end": window.window_end.isoformat(),
        }
    )
    hypothesis_id = _identifier("hyp_", hypothesis_key)
    evidence: list[CorrelationEvidenceV1] = []
    nodes = [
        CorrelationGraphNodeV1(
            node_id="hypothesis",
            kind="hypothesis",
            reference_id=hypothesis_id,
            reference_digest=hypothesis_key,
        )
    ]
    edges: list[CorrelationGraphEdgeV1] = []
    for sequence, event in enumerate(selected):
        digest = canonical_sha256(event)
        evidence_id = _identifier("evid_", f"{hypothesis_key}:{event.event_id}")
        role = _evidence_role(event)
        evidence.append(
            CorrelationEvidenceV1(
                evidence_id=evidence_id,
                event_id=event.event_id,
                role=role,
                source_digest=digest,
                sequence=sequence,
                chronology=event.chronology,
            )
        )
        node_id = _identifier("event_", event.event_id)
        nodes.append(
            CorrelationGraphNodeV1(
                node_id=node_id,
                kind="event",
                reference_id=event.event_id,
                reference_digest=digest,
            )
        )
        edges.append(
            CorrelationGraphEdgeV1(
                edge_id=_identifier("edge_", f"{hypothesis_id}:{event.event_id}:{role}"),
                source_node_id=node_id,
                target_node_id="hypothesis",
                role=role,
            )
        )
    for lane in arbitration.lane_results:
        node_id = _identifier("lane_", lane.lane)
        nodes.append(
            CorrelationGraphNodeV1(
                node_id=node_id,
                kind="lane",
                reference_id=lane.lane,
                reference_digest=lane.lineage_digest,
            )
        )
    graph = CorrelationGraphV1(nodes=nodes, edges=edges)
    graph_digest = canonical_sha256(
        graph,
        maximum_bytes=MAX_CORRELATION_DOCUMENT_BYTES,
    )
    supporting = sum(item.role == "supports" for item in evidence)
    contradictions = sum(item.role == "contradicts" for item in evidence)
    missing = sum(item.role == "missing" for item in evidence)
    summary = "hypothesis.abstained" if arbitration.abstained else "hypothesis.proposed"
    projection_material = {
        "hypothesis_id": hypothesis_id,
        "graph_digest": graph_digest,
        "event_count": len(selected),
        "supporting_evidence_count": supporting,
        "contradiction_count": contradictions,
        "missing_evidence_count": missing,
        "summary_code": summary,
    }
    projection = CorrelationFlatProjectionV1(
        **projection_material,
        projection_digest=canonical_sha256(projection_material),
    )
    first = selected[0].chronology
    chronology = CorrelationChronologyV1(
        occurred_at=first.occurred_at,
        observed_at=max(item.chronology.observed_at for item in selected),
        received_at=max(item.chronology.received_at for item in selected),
        recorded_at=max(item.chronology.recorded_at for item in selected),
        corrected_at=max(
            (item.chronology.corrected_at for item in selected if item.chronology.corrected_at),
            default=None,
        ),
    )
    return CorrelationHypothesisV2(
        hypothesis_id=hypothesis_id,
        revision=1,
        run_id=run_id,
        department=window.department,
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        partition_digest=window.partition_digest,
        hypothesis_key=hypothesis_key,
        subject_kind=profile.subject_kind,
        state=arbitration.state,
        confidence=arbitration.confidence,
        uncertainty=arbitration.uncertainty,
        abstained=arbitration.abstained,
        abstention_reason=(arbitration.reason_codes[0] if arbitration.abstained else None),
        contradiction_count=contradictions,
        window=window,
        lane_results=arbitration.lane_results,
        evidence=evidence,
        graph=graph,
        graph_digest=graph_digest,
        flat_projection=projection,
        arbitration_digest=arbitration.arbitration_digest,
        chronology=chronology,
    )


def revise_hypothesis_state(
    hypothesis: CorrelationHypothesisV2,
    *,
    new_state: str,
    reason_code: str,
    recorded_at: datetime,
) -> tuple[CorrelationHypothesisV2, HypothesisRevisionV1]:
    allowed = {
        "proposed": {"expired", "superseded", "retracted", "corrected"},
        "abstained": {"expired", "superseded", "retracted", "corrected"},
        "corrected": {"superseded", "retracted", "corrected"},
    }
    if new_state not in allowed.get(hypothesis.state, set()):
        raise ValueError("hypothesis state transition is not allowed")
    if recorded_at < hypothesis.chronology.recorded_at:
        raise ValueError("hypothesis revision cannot precede the current revision")
    revision_number = hypothesis.revision + 1
    constraint_digest = canonical_sha256(
        {
            "hypothesis_id": hypothesis.hypothesis_id,
            "revision": revision_number,
            "state": new_state,
            "reason_code": reason_code,
        }
    )
    node_id = f"revision_{revision_number}"
    role = {
        "expired": "stale",
        "superseded": "supersedes",
        "corrected": "supersedes",
        "retracted": "retracts",
    }[new_state]
    graph = CorrelationGraphV1(
        nodes=[
            *hypothesis.graph.nodes,
            CorrelationGraphNodeV1(
                node_id=node_id,
                kind="constraint",
                reference_id=reason_code,
                reference_digest=constraint_digest,
            ),
        ],
        edges=[
            *hypothesis.graph.edges,
            CorrelationGraphEdgeV1(
                edge_id=_identifier(
                    "edge_",
                    f"{hypothesis.hypothesis_id}:{revision_number}:{new_state}",
                ),
                source_node_id=node_id,
                target_node_id="hypothesis",
                role=role,
            ),
        ],
    )
    graph_digest = canonical_sha256(
        graph,
        maximum_bytes=MAX_CORRELATION_DOCUMENT_BYTES,
    )
    projection_material = hypothesis.flat_projection.model_dump(
        mode="json",
        exclude={"projection_digest", "graph_digest"},
    )
    projection_material["graph_digest"] = graph_digest
    projection = CorrelationFlatProjectionV1(
        **projection_material,
        projection_digest=canonical_sha256(projection_material),
    )
    chronology = hypothesis.chronology.model_copy(
        update={"recorded_at": recorded_at, "corrected_at": recorded_at}
    )
    revised = hypothesis.model_copy(
        update={
            "revision": revision_number,
            "state": new_state,
            "abstained": False,
            "abstention_reason": None,
            "graph": graph,
            "graph_digest": graph_digest,
            "flat_projection": projection,
            "chronology": chronology,
        }
    )
    revised = CorrelationHypothesisV2.model_validate(revised.model_dump(mode="json"))
    snapshot_digest = canonical_sha256(
        revised,
        maximum_bytes=MAX_CORRELATION_DOCUMENT_BYTES,
    )
    revision = HypothesisRevisionV1(
        revision_id=_identifier(
            "hrev_", f"{hypothesis.hypothesis_id}:{revision_number}"
        ),
        hypothesis_id=hypothesis.hypothesis_id,
        revision=revision_number,
        previous_state=hypothesis.state,
        new_state=new_state,
        reason_code=reason_code,
        snapshot_digest=snapshot_digest,
        recorded_at=recorded_at,
    )
    return revised, revision
