from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.arbitration import arbitrate_lane_results
from hcam.intelligence.correlation.contracts import (
    CorrelationIngressEventV1,
    CorrelationProfileV1,
    LaneResultV1,
)
from hcam.intelligence.correlation.hypotheses import revise_hypothesis_state
from hcam.intelligence.correlation.lanes import lane_capabilities
from hcam.intelligence.correlation.runtime import run_generated_batch


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "contracts" / "phase-4" / "p4-1" / "fixtures"
BASE = datetime(2026, 1, 1, tzinfo=UTC)


def _profile() -> CorrelationProfileV1:
    material = {
        "profile_id": "generated-vehicle-correlation",
        "allowed_event_types": ["hcam.analytics.observation.created.v1"],
        "subject_kind": "vehicle",
        "partition_dimensions": ["generated_reference"],
        "window_kind": "tumbling",
        "window_seconds": 10,
        "allowed_lateness_seconds": 2,
        "future_clock_skew_seconds": 5,
        "minimum_supporting_events": 2,
        "maximum_contradictions": 0,
        "maximum_events_per_window": 100,
        "maximum_active_windows": 8,
    }
    return CorrelationProfileV1(
        **material,
        profile_version=canonical_sha256(material),
    )


def _event(
    identifier: int,
    seconds: int,
    *,
    event_id: str | None = None,
    signal_kind: str = "observation",
    confidence: float = 0.9,
    source_sequence: int | None = None,
) -> CorrelationIngressEventV1:
    instant = BASE + timedelta(seconds=seconds)
    return CorrelationIngressEventV1(
        event_id=event_id or f"generated-event-{identifier}",
        event_type="hcam.analytics.observation.created.v1",
        schema_version=1,
        department="generated-lab",
        stream_id="str_" + "7" * 32,
        camera_id="generated-camera-07",
        profile_id=_profile().profile_id,
        subject_kind="vehicle",
        signals={
            "object_class": "car",
            "signal_kind": signal_kind,
            "confidence": confidence,
            "generated_reference": "generated-vehicle-a",
            "source_sequence": identifier if source_sequence is None else source_sequence,
        },
        chronology={
            "occurred_at": instant,
            "observed_at": instant,
            "received_at": instant,
            "recorded_at": instant,
        },
    )


def _fixture_documents() -> dict[str, dict[str, Any]]:
    profile = _profile()
    sequence_events = [_event(1, 1), _event(2, 2), _event(3, 20)]
    sequence_result = run_generated_batch(sequence_events, profile)

    first = _event(10, 1, event_id="generated-shared-event")
    duplicate = first.model_copy(deep=True)
    conflict = _event(
        11,
        2,
        event_id="generated-shared-event",
        confidence=0.4,
    )
    duplicate_result = run_generated_batch([first, duplicate, conflict], profile)

    late_events = [
        _event(20, 20, source_sequence=1),
        _event(21, 18, source_sequence=4),
        _event(22, 10, source_sequence=5),
    ]
    late_result = run_generated_batch(late_events, profile)

    generated_optional = LaneResultV1(
        lane="probabilistic",
        status="completed",
        score=0.25,
        uncertainty=0.15,
        abstained=False,
        lineage_digest=canonical_sha256({"fixture": "probabilistic-r1"}),
        generated_fixture_result=True,
    )
    deterministic = sequence_result.hypotheses[0].lane_results[0]
    arbitration = arbitrate_lane_results([deterministic, generated_optional])

    original = sequence_result.hypotheses[0]
    corrected, correction = revise_hypothesis_state(
        original,
        new_state="corrected",
        reason_code="generated_correction",
        recorded_at=BASE + timedelta(seconds=30),
    )
    retracted, retraction = revise_hypothesis_state(
        corrected,
        new_state="retracted",
        reason_code="generated_retraction",
        recorded_at=BASE + timedelta(seconds=40),
    )

    return {
        "generated-event-sequence-v1.json": {
            "schema_version": "hcam.phase4.p4_1.generated-event-sequence.v1",
            "profile": profile.model_dump(mode="json"),
            "events": [item.model_dump(mode="json") for item in sequence_events],
            "expected": sequence_result.model_dump(mode="json"),
        },
        "generated-duplicate-conflict-v1.json": {
            "schema_version": "hcam.phase4.p4_1.generated-duplicate-conflict.v1",
            "events": [
                first.model_dump(mode="json"),
                duplicate.model_dump(mode="json"),
                conflict.model_dump(mode="json"),
            ],
            "receipts": [
                item.model_dump(mode="json") for item in duplicate_result.receipts
            ],
        },
        "generated-late-gap-v1.json": {
            "schema_version": "hcam.phase4.p4_1.generated-late-gap.v1",
            "events": [item.model_dump(mode="json") for item in late_events],
            "receipts": [item.model_dump(mode="json") for item in late_result.receipts],
            "checkpoints": [
                item.model_dump(mode="json") for item in late_result.checkpoints
            ],
        },
        "generated-lane-results-v1.json": {
            "schema_version": "hcam.phase4.p4_1.generated-lane-results.v1",
            "capabilities": [
                item.model_dump(mode="json") for item in lane_capabilities()
            ],
            "generated_optional_input": generated_optional.model_dump(mode="json"),
            "arbitration": arbitration.model_dump(mode="json"),
        },
        "generated-hypothesis-graph-v1.json": {
            "schema_version": "hcam.phase4.p4_1.generated-hypothesis-graph.v1",
            "hypothesis_id": original.hypothesis_id,
            "graph": original.graph.model_dump(mode="json"),
            "graph_digest": original.graph_digest,
            "flat_projection": original.flat_projection.model_dump(mode="json"),
        },
        "generated-hypothesis-revisions-v1.json": {
            "schema_version": "hcam.phase4.p4_1.generated-hypothesis-revisions.v1",
            "revisions": [
                correction.model_dump(mode="json"),
                retraction.model_dump(mode="json"),
            ],
            "final_hypothesis": retracted.model_dump(mode="json"),
        },
    }


def _encoded(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("ascii")


def write_fixtures() -> int:
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    for name, document in _fixture_documents().items():
        (FIXTURE_ROOT / name).write_bytes(_encoded(document))
    print(f"wrote {len(_fixture_documents())} generated-only fixtures")
    return 0


def check_fixtures() -> int:
    expected = _fixture_documents()
    mismatches = [
        name
        for name, document in expected.items()
        if not (FIXTURE_ROOT / name).is_file()
        or (FIXTURE_ROOT / name).read_bytes() != _encoded(document)
    ]
    if mismatches:
        print("generated fixtures are missing or stale")
        return 1
    print(f"validated {len(expected)} generated-only fixtures")
    return 0


def run_fixture() -> int:
    document = _fixture_documents()["generated-event-sequence-v1.json"]
    result = document["expected"]
    summary = {
        "input_count": result["input_count"],
        "accepted_count": result["accepted_count"],
        "hypothesis_states": [item["state"] for item in result["hypotheses"]],
        "generated_only": result["generated_only"],
        "operational": result["operational"],
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or validate repository-owned P4.1 event fixtures."
    )
    parser.add_argument("command", choices=("write", "check", "run"))
    args = parser.parse_args()
    if args.command == "write":
        return write_fixtures()
    if args.command == "check":
        return check_fixtures()
    return run_fixture()


if __name__ == "__main__":
    raise SystemExit(main())
