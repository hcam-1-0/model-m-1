from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import datetime
from typing import cast

from pydantic import ValidationError

from hcam.analytics.contracts import ObservationCreatedV1, TrackLifecycleV2
from hcam.intelligence.canonical import canonical_json_bytes, canonical_sha256
from hcam.intelligence.correlation.bounds import MAX_EVENT_ENVELOPE_BYTES
from hcam.intelligence.correlation.contracts import (
    CorrelationIngressEventV1,
    CorrelationProfileV1,
    CorrelationReceiptV1,
    Phase3SpatialEventPayloadV1,
)
from hcam.intelligence.guardrails import validate_intelligence_document


class CorrelationIngressError(ValueError):
    """Raised for an invalid generated correlation input boundary."""


def _identifier(prefix: str, material: str) -> str:
    return prefix + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _subject_kind(class_id: str) -> str:
    if class_id.startswith("vehicle."):
        return "vehicle"
    if class_id.startswith("person."):
        return "anonymous_person"
    return "object"


def _require_resolved_scope(
    *,
    stream_id: str,
    camera_id: str,
    resolved_stream_id: str,
    resolved_camera_id: str,
    resolved_department: str | None,
) -> str:
    if stream_id != resolved_stream_id or camera_id != resolved_camera_id:
        raise CorrelationIngressError("outbox event does not match resolved camera stream")
    if resolved_department is None:
        raise CorrelationIngressError("camera department is not resolved")
    return resolved_department


def project_stream_event_outbox(
    *,
    event_id: str,
    event_type: str,
    schema_version: int,
    stream_id: str,
    camera_id: str,
    occurred_at: datetime,
    payload: Mapping[str, object],
    resolved_stream_id: str,
    resolved_camera_id: str,
    resolved_department: str | None,
    profile_id: str,
    source_generated_only: bool,
) -> CorrelationIngressEventV1:
    """Project one generated outbox row without mutating its publication state."""

    if not source_generated_only:
        raise CorrelationIngressError("only generated Phase 3 events may be projected")
    source = {
        "event_id": event_id,
        "event_type": event_type,
        "schema_version": schema_version,
        "stream_id": stream_id,
        "camera_id": camera_id,
        "occurred_at": occurred_at.isoformat(),
        "payload": dict(payload),
    }
    canonical_json_bytes(source, maximum_bytes=MAX_EVENT_ENVELOPE_BYTES)
    department = _require_resolved_scope(
        stream_id=stream_id,
        camera_id=camera_id,
        resolved_stream_id=resolved_stream_id,
        resolved_camera_id=resolved_camera_id,
        resolved_department=resolved_department,
    )
    envelope = {
        **source,
        "partition_key": stream_id,
    }
    try:
        if event_type == "hcam.analytics.observation.created.v1" and schema_version == 1:
            phase3 = ObservationCreatedV1.model_validate(envelope)
            if phase3.payload.source.timestamp_source != "generated":
                raise CorrelationIngressError("observation source is not generated")
            observed_at = phase3.payload.observed_at
            if occurred_at < observed_at:
                raise CorrelationIngressError("outbox occurrence precedes observation")
            return CorrelationIngressEventV1(
                event_id=event_id,
                event_type=event_type,
                schema_version=schema_version,
                department=department,
                stream_id=stream_id,
                camera_id=camera_id,
                profile_id=profile_id,
                subject_kind=cast(str, _subject_kind(phase3.payload.classification.id)),
                signals={
                    "object_class": phase3.payload.classification.id,
                    "confidence": phase3.payload.classification.confidence,
                    "source_sequence": phase3.payload.source.sequence,
                },
                chronology={
                    "occurred_at": observed_at,
                    "observed_at": observed_at,
                    "received_at": occurred_at,
                    "recorded_at": occurred_at,
                },
            )
        if event_type == "hcam.analytics.track.lifecycle.v2" and schema_version == 2:
            phase3 = TrackLifecycleV2.model_validate(envelope)
            observed_at = phase3.payload.observed_at
            if occurred_at < observed_at:
                raise CorrelationIngressError("outbox occurrence precedes track observation")
            return CorrelationIngressEventV1(
                event_id=event_id,
                event_type=event_type,
                schema_version=schema_version,
                department=department,
                stream_id=stream_id,
                camera_id=camera_id,
                profile_id=profile_id,
                subject_kind=cast(str, _subject_kind(phase3.payload.class_id)),
                signals={
                    "object_class": phase3.payload.class_id,
                    "confidence": phase3.payload.confidence,
                    "local_track_id": phase3.payload.track_id,
                    "tracker_epoch": phase3.payload.tracker_epoch,
                    "source_sequence": phase3.payload.source_sequence,
                },
                chronology={
                    "occurred_at": observed_at,
                    "observed_at": observed_at,
                    "received_at": occurred_at,
                    "recorded_at": occurred_at,
                },
            )
        if event_type.startswith("hcam.analytics.") and schema_version == 1:
            phase3_spatial = Phase3SpatialEventPayloadV1.model_validate(payload)
            if phase3_spatial.event_kind != event_type:
                raise CorrelationIngressError("spatial payload type does not match outbox event")
            if phase3_spatial.event_id != event_id:
                raise CorrelationIngressError("spatial payload identifier does not match outbox event")
            if phase3_spatial.department != department:
                raise CorrelationIngressError("spatial payload crosses department scope")
            if (
                phase3_spatial.stream_id != stream_id
                or phase3_spatial.camera_id != camera_id
            ):
                raise CorrelationIngressError("spatial payload crosses camera stream scope")
            if phase3_spatial.occurred_at != occurred_at:
                raise CorrelationIngressError("spatial payload time does not match outbox event")
            return CorrelationIngressEventV1(
                event_id=event_id,
                event_type=event_type,
                schema_version=schema_version,
                department=department,
                stream_id=stream_id,
                camera_id=camera_id,
                profile_id=profile_id,
                subject_kind="event_group",
                signals={
                    "object_class": event_type,
                    "confidence": phase3_spatial.confidence,
                    "direction": phase3_spatial.direction,
                    "location_relation": phase3_spatial.geometry.id,
                    "local_track_id": phase3_spatial.track_id,
                    "tracker_epoch": (
                        phase3_spatial.epoch_id
                        if phase3_spatial.track_id is not None
                        else None
                    ),
                    "generated_reference": phase3_spatial.state_cycle_id,
                    "source_sequence": phase3_spatial.source_sequence,
                },
                chronology={
                    "occurred_at": occurred_at,
                    "observed_at": occurred_at,
                    "received_at": occurred_at,
                    "recorded_at": occurred_at,
                },
            )
    except ValidationError as exc:
        raise CorrelationIngressError("outbox event failed its closed Phase 3 schema") from exc
    raise CorrelationIngressError("outbox event type or schema is not supported")


def event_digest(event: CorrelationIngressEventV1) -> str:
    validate_intelligence_document(event)
    return canonical_sha256(event)


def partition_digest(
    event: CorrelationIngressEventV1,
    profile: CorrelationProfileV1,
) -> str:
    values: dict[str, str] = {
        "department": event.department,
        "profile": profile.profile_id,
    }
    for dimension in profile.partition_dimensions:
        if dimension == "camera":
            values[dimension] = event.camera_id
        elif dimension == "stream":
            values[dimension] = event.stream_id
        elif dimension == "object_class":
            values[dimension] = event.signals.object_class
        elif dimension == "direction":
            values[dimension] = event.signals.direction or "unknown"
        elif dimension == "location_relation":
            values[dimension] = event.signals.location_relation or "unknown"
        elif dimension == "track_local":
            if event.signals.local_track_id is None or event.signals.tracker_epoch is None:
                raise CorrelationIngressError("track-local partition requires tracker epoch")
            values[dimension] = (
                f"{event.stream_id}:{event.signals.tracker_epoch}:"
                f"{event.signals.local_track_id}"
            )
        elif dimension == "generated_reference":
            if event.signals.generated_reference is None:
                raise CorrelationIngressError("generated reference partition is missing")
            values[dimension] = event.signals.generated_reference
    return canonical_sha256(values)


def classify_ingress(
    event: CorrelationIngressEventV1,
    profile: CorrelationProfileV1,
    seen_event_digests: Mapping[str, str],
    *,
    receipt_sequence: int,
    processing_time: datetime | None = None,
) -> CorrelationReceiptV1:
    digest = event_digest(event)
    receipt_id = _identifier("crec_", f"{event.event_id}:{digest}:{receipt_sequence}")
    common = {
        "receipt_id": receipt_id,
        "event_id": event.event_id,
        "event_digest": digest,
        "department": event.department,
        "receipt_sequence": receipt_sequence,
        "occurred_at": event.chronology.occurred_at,
        "recorded_at": event.chronology.recorded_at,
    }
    previous = seen_event_digests.get(event.event_id)
    if previous is not None:
        if previous == digest:
            return CorrelationReceiptV1(
                **common,
                partition_digest=None,
                disposition="duplicate",
                reason_code="duplicate_same_digest",
                accepted=False,
            )
        return CorrelationReceiptV1(
            **common,
            partition_digest=None,
            disposition="conflict",
            reason_code="event_id_digest_conflict",
            accepted=False,
        )
    if event.profile_id != profile.profile_id:
        return CorrelationReceiptV1(
            **common,
            partition_digest=None,
            disposition="policy_rejected",
            reason_code="profile_mismatch",
            accepted=False,
        )
    if event.event_type not in profile.allowed_event_types:
        return CorrelationReceiptV1(
            **common,
            partition_digest=None,
            disposition="policy_rejected",
            reason_code="event_type_not_allowed",
            accepted=False,
        )
    if event.subject_kind != profile.subject_kind:
        return CorrelationReceiptV1(
            **common,
            partition_digest=None,
            disposition="policy_rejected",
            reason_code="subject_kind_mismatch",
            accepted=False,
        )
    effective_processing_time = processing_time or event.chronology.recorded_at
    skew = event.chronology.occurred_at - effective_processing_time
    if skew.total_seconds() > profile.future_clock_skew_seconds:
        return CorrelationReceiptV1(
            **common,
            partition_digest=None,
            disposition="future_rejected",
            reason_code="future_clock_skew",
            accepted=False,
        )
    try:
        partition = partition_digest(event, profile)
    except CorrelationIngressError:
        return CorrelationReceiptV1(
            **common,
            partition_digest=None,
            disposition="policy_rejected",
            reason_code="partition_key_incomplete",
            accepted=False,
        )
    return CorrelationReceiptV1(
        **common,
        partition_digest=partition,
        disposition="accepted",
        reason_code="accepted",
        accepted=True,
    )
