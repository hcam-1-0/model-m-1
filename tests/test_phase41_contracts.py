from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.bounds import CorrelationBounds, CorrelationLimitError
from hcam.intelligence.correlation.contracts import (
    CorrelationBatchResultV1,
    CorrelationChronologyV1,
    CorrelationGraphEdgeV1,
    CorrelationGraphNodeV1,
    CorrelationGraphV1,
    CorrelationProfileV1,
    CorrelationReceiptV1,
    CorrelationReplayBindingV1,
    CorrelationSignalsV1,
    LaneCapabilityV1,
    LaneResultV1,
)


DIGEST = "sha256:" + "1" * 64
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_chronology_requires_ordered_utc_timestamps() -> None:
    with pytest.raises(ValidationError, match="not ordered"):
        CorrelationChronologyV1(
            occurred_at=NOW,
            observed_at=NOW - timedelta(seconds=1),
            received_at=NOW,
            recorded_at=NOW,
        )
    with pytest.raises(ValidationError, match="timezone-aware UTC"):
        CorrelationChronologyV1(
            occurred_at=NOW.replace(tzinfo=None),
            observed_at=NOW,
            received_at=NOW,
            recorded_at=NOW,
        )


def test_signal_track_identity_is_local_and_epoch_bound() -> None:
    with pytest.raises(ValidationError, match="track and tracker epoch"):
        CorrelationSignalsV1(
            object_class="car",
            confidence=0.8,
            local_track_id="track-1",
        )


def test_profile_rejects_duplicate_and_inconsistent_window_settings() -> None:
    common = {
        "profile_id": "vehicle-path",
        "profile_version": DIGEST,
        "allowed_event_types": ["hcam.analytics.observation.created.v1"],
        "subject_kind": "vehicle",
        "partition_dimensions": ["generated_reference"],
    }
    with pytest.raises(ValidationError, match="must be unique"):
        CorrelationProfileV1(**{**common, "partition_dimensions": ["camera", "camera"]})
    with pytest.raises(ValidationError, match="session windows require"):
        CorrelationProfileV1(**common, window_kind="session")
    with pytest.raises(ValidationError, match="only session windows"):
        CorrelationProfileV1(**common, session_gap_seconds=10)


def test_receipt_and_batch_counts_fail_closed() -> None:
    receipt = CorrelationReceiptV1(
        receipt_id="crec_" + "1" * 32,
        event_id="event-1",
        event_digest=DIGEST,
        department="generated-lab",
        partition_digest=DIGEST,
        disposition="accepted",
        reason_code="accepted",
        accepted=True,
        receipt_sequence=0,
        occurred_at=NOW,
        recorded_at=NOW,
    )
    with pytest.raises(ValidationError, match="acceptance is inconsistent"):
        CorrelationReceiptV1.model_validate(
            {**receipt.model_dump(), "accepted": False}
        )
    with pytest.raises(ValidationError, match="receipt counts"):
        CorrelationBatchResultV1(
            run_id="crun_" + "1" * 32,
            profile_id="vehicle-path",
            replay_binding=CorrelationReplayBindingV1(
                profile_id="vehicle-path",
                profile_version=DIGEST,
                profile_configuration_digest=DIGEST,
                ordered_event_digests=[DIGEST],
            ),
            receipts=[receipt],
            windows=[],
            hypotheses=[],
            checkpoints=[],
            input_count=1,
            accepted_count=0,
            duplicate_count=0,
            rejected_count=1,
            result_digest=DIGEST,
        )


def test_lane_and_graph_contracts_reject_unsafe_states() -> None:
    with pytest.raises(ValidationError, match="must remain unavailable"):
        LaneCapabilityV1(
            lane="probabilistic",
            implementation_version=DIGEST,
            execution_state="enabled_generated_only",
            resource_class="accelerator_optional",
            deterministic=False,
        )
    with pytest.raises(ValidationError, match="generated fixtures"):
        LaneResultV1(
            lane="probabilistic",
            status="completed",
            score=0.8,
            uncertainty=0.2,
            abstained=False,
            lineage_digest=DIGEST,
        )
    node = CorrelationGraphNodeV1(
        node_id="known",
        kind="event",
        reference_id="event-1",
        reference_digest=DIGEST,
    )
    edge = CorrelationGraphEdgeV1(
        edge_id="edge-1",
        source_node_id="known",
        target_node_id="missing",
        role="supports",
    )
    with pytest.raises(ValidationError, match="unknown node"):
        CorrelationGraphV1(nodes=[node], edges=[edge])


def test_correlation_bounds_are_hard_limited() -> None:
    assert CorrelationBounds().events_per_batch == 100
    with pytest.raises(CorrelationLimitError, match="outside"):
        CorrelationBounds(events_per_batch=1_001)
    assert canonical_sha256({"contract": "bounded"}).startswith("sha256:")
