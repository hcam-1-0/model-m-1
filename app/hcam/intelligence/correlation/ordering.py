from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from hcam.intelligence.correlation.bounds import CorrelationLimitError
from hcam.intelligence.correlation.contracts import (
    CorrelationIngressEventV1,
    CorrelationProfileV1,
    CorrelationReceiptV1,
    CorrelationWindowV1,
    PartitionCheckpointV1,
)


def _identifier(prefix: str, material: str) -> str:
    return prefix + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _floor_time(value: datetime, seconds: int) -> datetime:
    epoch_seconds = int(value.timestamp())
    return datetime.fromtimestamp(epoch_seconds - epoch_seconds % seconds, tz=UTC)


def classify_partition_order(
    events: list[CorrelationIngressEventV1],
    receipts: list[CorrelationReceiptV1],
    profile: CorrelationProfileV1,
) -> tuple[list[CorrelationReceiptV1], list[PartitionCheckpointV1]]:
    by_event: dict[str, CorrelationIngressEventV1] = {}
    for event in events:
        by_event.setdefault(event.event_id, event)
    grouped: dict[str, list[CorrelationReceiptV1]] = defaultdict(list)
    for receipt in receipts:
        if receipt.accepted and receipt.partition_digest is not None:
            grouped[receipt.partition_digest].append(receipt)

    updated = {item.receipt_id: item for item in receipts}
    checkpoints: list[PartitionCheckpointV1] = []
    for partition, partition_receipts in sorted(grouped.items()):
        maximum: datetime | None = None
        watermark: datetime | None = None
        last_source_sequence: int | None = None
        for receipt in sorted(partition_receipts, key=lambda item: item.receipt_sequence):
            event = by_event[receipt.event_id]
            occurred = event.chronology.occurred_at
            prior_maximum = maximum
            prior_watermark = watermark
            disposition = receipt.disposition
            reason = receipt.reason_code
            if prior_watermark is not None and occurred < prior_watermark:
                disposition = "late_rejected"
                reason = "event_behind_watermark"
            elif prior_maximum is not None and occurred < prior_maximum:
                disposition = "late_accepted"
                reason = "out_of_order_within_lateness"
            source_sequence = event.signals.source_sequence
            if (
                disposition != "late_rejected"
                and source_sequence is not None
                and last_source_sequence is not None
                and source_sequence > last_source_sequence + 1
            ):
                disposition = "gap_accepted"
                reason = "source_sequence_gap"
            if disposition == "late_rejected":
                updated[receipt.receipt_id] = receipt.model_copy(
                    update={
                        "partition_digest": None,
                        "disposition": disposition,
                        "reason_code": reason,
                        "accepted": False,
                    }
                )
                continue
            maximum = occurred if maximum is None else max(maximum, occurred)
            watermark = maximum - timedelta(seconds=profile.allowed_lateness_seconds)
            if source_sequence is not None:
                last_source_sequence = (
                    source_sequence
                    if last_source_sequence is None
                    else max(last_source_sequence, source_sequence)
                )
            updated[receipt.receipt_id] = receipt.model_copy(
                update={"disposition": disposition, "reason_code": reason}
            )
        accepted_partition = [
            item
            for item in updated.values()
            if item.partition_digest == partition and item.accepted
        ]
        if maximum is not None and watermark is not None and accepted_partition:
            checkpoints.append(
                PartitionCheckpointV1(
                    department=accepted_partition[0].department,
                    profile_id=profile.profile_id,
                    partition_digest=partition,
                    version=1,
                    receipt_sequence=max(
                        item.receipt_sequence for item in accepted_partition
                    ),
                    last_source_sequence=last_source_sequence,
                    maximum_occurred_at=maximum,
                    watermark_at=watermark,
                    active_window_count=0,
                )
            )
    return (
        [updated[item.receipt_id] for item in receipts],
        checkpoints,
    )


def build_windows(
    events: list[CorrelationIngressEventV1],
    receipts: list[CorrelationReceiptV1],
    checkpoints: list[PartitionCheckpointV1],
    profile: CorrelationProfileV1,
) -> tuple[list[CorrelationWindowV1], list[PartitionCheckpointV1]]:
    by_event: dict[str, CorrelationIngressEventV1] = {}
    for event in events:
        by_event.setdefault(event.event_id, event)
    by_checkpoint = {item.partition_digest: item for item in checkpoints}
    grouped: dict[str, list[CorrelationIngressEventV1]] = defaultdict(list)
    for receipt in receipts:
        if receipt.accepted and receipt.partition_digest is not None:
            grouped[receipt.partition_digest].append(by_event[receipt.event_id])

    windows: list[CorrelationWindowV1] = []
    updated_checkpoints: list[PartitionCheckpointV1] = []
    for partition, partition_events in sorted(grouped.items()):
        sorted_events = sorted(
            partition_events,
            key=lambda item: (item.chronology.occurred_at, item.event_id),
        )
        buckets: list[tuple[datetime, datetime, list[CorrelationIngressEventV1]]] = []
        if profile.window_kind == "session":
            gap = timedelta(seconds=profile.session_gap_seconds or profile.window_seconds)
            current: list[CorrelationIngressEventV1] = []
            for event in sorted_events:
                if current and event.chronology.occurred_at - current[-1].chronology.occurred_at > gap:
                    start = current[0].chronology.occurred_at
                    buckets.append((start, current[-1].chronology.occurred_at + gap, current))
                    current = []
                current.append(event)
            if current:
                start = current[0].chronology.occurred_at
                buckets.append((start, current[-1].chronology.occurred_at + gap, current))
        else:
            mapped: dict[datetime, list[CorrelationIngressEventV1]] = defaultdict(list)
            for event in sorted_events:
                mapped[_floor_time(event.chronology.occurred_at, profile.window_seconds)].append(event)
            for start, bucket_events in sorted(mapped.items()):
                buckets.append(
                    (start, start + timedelta(seconds=profile.window_seconds), bucket_events)
                )
        if len(buckets) > profile.maximum_active_windows:
            raise CorrelationLimitError("active window capacity exceeded")
        checkpoint = by_checkpoint[partition]
        for start, end, bucket_events in buckets:
            if len(bucket_events) > profile.maximum_events_per_window:
                raise CorrelationLimitError("event window capacity exceeded")
            window_id = _identifier(
                "cwin_",
                f"{profile.profile_version}:{partition}:{start.isoformat()}:{end.isoformat()}",
            )
            completeness = "complete" if checkpoint.watermark_at >= end else "open"
            windows.append(
                CorrelationWindowV1(
                    window_id=window_id,
                    department=checkpoint.department,
                    profile_id=profile.profile_id,
                    partition_digest=partition,
                    window_kind=profile.window_kind,
                    window_start=start,
                    window_end=end,
                    watermark_at=checkpoint.watermark_at,
                    completeness=completeness,
                    event_ids=[item.event_id for item in bucket_events],
                )
            )
        updated_checkpoints.append(
            checkpoint.model_copy(update={"active_window_count": len(buckets)})
        )
    return windows, updated_checkpoints
