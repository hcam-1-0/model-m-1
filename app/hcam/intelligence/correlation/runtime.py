from __future__ import annotations

import hashlib
import time
from collections.abc import Mapping, Sequence
from datetime import datetime

from hcam.intelligence.canonical import canonical_json_bytes
from hcam.intelligence.correlation.arbitration import arbitrate_lane_results
from hcam.intelligence.correlation.bounds import CorrelationBounds, CorrelationLimitError
from hcam.intelligence.correlation.contracts import (
    CorrelationBatchResultV1,
    CorrelationIngressEventV1,
    CorrelationProfileV1,
    CorrelationReplayBindingV1,
    LaneResultV1,
)
from hcam.intelligence.correlation.deterministic import evaluate_deterministic_lane
from hcam.intelligence.correlation.hypotheses import build_hypothesis
from hcam.intelligence.correlation.ingress import classify_ingress, event_digest
from hcam.intelligence.correlation.lanes import unavailable_optional_results
from hcam.intelligence.correlation.metrics import CorrelationMetrics
from hcam.intelligence.correlation.ordering import build_windows, classify_partition_order


class CorrelationRuntimeError(ValueError):
    """Raised when generated correlation cannot execute inside its safe boundary."""


def _identifier(prefix: str, material: str) -> str:
    return prefix + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _stream_digest(parts: Sequence[object]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        encoded = canonical_json_bytes(part, maximum_bytes=8 * 1024 * 1024)
        digest.update(len(encoded).to_bytes(8, byteorder="big"))
        digest.update(encoded)
    return "sha256:" + digest.hexdigest()


def _validate_optional_results(
    optional_results: Mapping[str, Sequence[LaneResultV1]],
    window_ids: set[str],
) -> None:
    unknown = set(optional_results) - window_ids
    if unknown:
        raise CorrelationRuntimeError("optional result references an unknown window")
    for results in optional_results.values():
        if any(item.lane == "deterministic_cpu" for item in results):
            raise CorrelationRuntimeError("optional input cannot replace the deterministic lane")
        if len({item.lane for item in results}) != len(results):
            raise CorrelationRuntimeError("optional input repeats a lane")
        if any(item.status == "completed" and not item.generated_fixture_result for item in results):
            raise CorrelationRuntimeError("optional completed results must be generated fixtures")


def run_generated_batch(
    events: Sequence[CorrelationIngressEventV1],
    profile: CorrelationProfileV1,
    *,
    optional_results: Mapping[str, Sequence[LaneResultV1]] | None = None,
    bounds: CorrelationBounds | None = None,
    metrics: CorrelationMetrics | None = None,
    processing_time: datetime | None = None,
) -> CorrelationBatchResultV1:
    """Correlate already-structured generated events without media or model access."""

    effective_bounds = bounds or CorrelationBounds()
    started = time.perf_counter()
    if not events:
        raise CorrelationRuntimeError("a generated correlation batch cannot be empty")
    if len(events) > effective_bounds.events_per_batch:
        raise CorrelationLimitError("correlation batch capacity exceeded")
    if profile.maximum_active_windows > effective_bounds.active_windows_per_partition:
        raise CorrelationLimitError("profile active-window bound exceeds worker capacity")
    if profile.maximum_events_per_window > effective_bounds.events_per_window:
        raise CorrelationLimitError("profile event-window bound exceeds worker capacity")

    digests = [event_digest(event) for event in events]
    replay_binding = CorrelationReplayBindingV1(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_configuration_digest=_stream_digest([profile]),
        ordered_event_digests=digests,
    )
    run_material = _stream_digest([replay_binding])
    run_id = _identifier("crun_", run_material)

    seen: dict[str, str] = {}
    receipts = []
    for sequence, event in enumerate(events):
        receipt = classify_ingress(
            event,
            profile,
            seen,
            receipt_sequence=sequence,
            processing_time=processing_time,
        )
        receipts.append(receipt)
        seen.setdefault(event.event_id, digests[sequence])

    active_partitions = {
        item.partition_digest
        for item in receipts
        if item.accepted and item.partition_digest is not None
    }
    if len(active_partitions) > effective_bounds.active_partitions:
        raise CorrelationLimitError("active partition capacity exceeded")

    receipts, checkpoints = classify_partition_order(list(events), receipts, profile)
    accepted_by_id: dict[str, CorrelationIngressEventV1] = {}
    for event, receipt in zip(events, receipts, strict=True):
        if receipt.accepted:
            accepted_by_id.setdefault(event.event_id, event)
    accepted_events = list(accepted_by_id.values())
    windows, checkpoints = build_windows(accepted_events, receipts, checkpoints, profile)
    supplied = optional_results or {}
    _validate_optional_results(supplied, {item.window_id for item in windows})

    hypotheses = []
    unavailable = unavailable_optional_results()
    for window in windows:
        deterministic = evaluate_deterministic_lane(window, accepted_events, profile)
        lane_results = [deterministic, *supplied.get(window.window_id, unavailable)]
        arbitration = arbitrate_lane_results(lane_results)
        hypotheses.append(
            build_hypothesis(run_id, window, accepted_events, profile, arbitration)
        )

    accepted_count = sum(item.accepted for item in receipts)
    duplicate_count = sum(item.disposition == "duplicate" for item in receipts)
    rejected_count = len(receipts) - accepted_count - duplicate_count
    result_parts: list[object] = [
        {
            "run_id": run_id,
            "profile_id": profile.profile_id,
            "profile_version": profile.profile_version,
            "counts": [len(events), accepted_count, duplicate_count, rejected_count],
        }
    ]
    result_parts.extend(
        {
            "receipt_id": item.receipt_id,
            "event_digest": item.event_digest,
            "disposition": item.disposition,
        }
        for item in receipts
    )
    result_parts.extend(
        {
            "hypothesis_id": item.hypothesis_id,
            "graph_digest": item.graph_digest,
            "arbitration_digest": item.arbitration_digest,
        }
        for item in hypotheses
    )
    result = CorrelationBatchResultV1(
        run_id=run_id,
        profile_id=profile.profile_id,
        replay_binding=replay_binding,
        receipts=receipts,
        windows=windows,
        hypotheses=hypotheses,
        checkpoints=checkpoints,
        input_count=len(events),
        accepted_count=accepted_count,
        duplicate_count=duplicate_count,
        rejected_count=rejected_count,
        result_digest=_stream_digest(result_parts),
    )
    if metrics is not None:
        for receipt in receipts:
            metrics.record_receipt(receipt.disposition)
        for window in windows:
            metrics.record_window(window.completeness)
        for hypothesis in hypotheses:
            metrics.record_hypothesis(hypothesis.state)
        metrics.record_run("succeeded")
        metrics.observe_duration(time.perf_counter() - started)
    return result
