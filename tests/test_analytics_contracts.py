from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.analytics.contracts import (
    ANALYTICS_EVENT_MODELS,
    MAX_EVENT_BYTES,
    AnalyticEventPayloadV1,
    AnalyticsContractSafetyError,
    DeploymentTargetV1,
    ModelDeploymentPayloadV1,
    NormalizedBoundingBox,
    TrackPayloadV1,
    VersionedArtifact,
    VersionedConfiguration,
    analytics_contract_bundle,
    canonical_contract_json,
    parse_analytics_assignment,
    parse_analytics_event,
)
from hcam.analytics.fixtures import (
    CAMERA_ID,
    LINEAGE,
    MODEL,
    OBSERVED_AT,
    PIPELINE,
    STREAM_ID,
    TRACKER,
)
from tools import analytics_contracts


CONTRACT_ROOT = Path(__file__).parents[1] / "contracts" / "phase-3"
FIXTURE_ROOT = CONTRACT_ROOT / "fixtures"


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def test_tracked_analytics_contracts_match_current_models() -> None:
    assert analytics_contracts.check_contracts() == 0


def test_contract_writer_requires_explicit_review_acknowledgment() -> None:
    assert analytics_contracts.write_contracts(acknowledged=False) == 2


def test_contract_bundle_covers_assignment_and_four_event_types() -> None:
    bundle = analytics_contract_bundle()

    assert bundle["contract_format"] == "hcam.analytics.contract-bundle.v1"
    assert bundle["maximum_event_bytes"] == MAX_EVENT_BYTES
    assert set(bundle["events"]) == set(ANALYTICS_EVENT_MODELS)
    assert set(bundle["geometry"]) == {"definition", "line", "schedule", "zone"}
    assert set(bundle["runtime"]) == {
        "adapter",
        "request",
        "request_v2",
        "result",
    }
    assert bundle["taxonomy"]["title"] == "TaxonomyManifestV1"
    assert bundle["delivery"] == {
        "deduplication_key": "event_id",
        "ordering_scope": "stream_id",
        "partition_key": "stream_id",
        "semantics": "at_least_once",
    }
    assert "stream_url" in bundle["prohibited_fields"]
    assert "face_template" in bundle["prohibited_fields"]
    assert "owner_record" in bundle["prohibited_fields"]


def test_assignment_fixture_is_strict_and_deterministic() -> None:
    document = _fixture("assignment-v1.json")
    assignment = parse_analytics_assignment(document)

    assert assignment.stream_id == STREAM_ID
    assert assignment.models == [MODEL]
    assert canonical_contract_json(assignment) == (
        FIXTURE_ROOT / "assignment-v1.json"
    ).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "name,event_type",
    [
        (
            "observation-created-v1.json",
            "hcam.analytics.observation.created.v1",
        ),
        ("track-updated-v1.json", "hcam.analytics.track.updated.v1"),
        ("analytic-event-created-v1.json", "hcam.analytics.event.created.v1"),
        (
            "model-deployment-changed-v1.json",
            "hcam.analytics.model.deployment.changed.v1",
        ),
    ],
)
def test_event_fixtures_parse_and_serialize_deterministically(
    name: str,
    event_type: str,
) -> None:
    document = _fixture(name)
    event = parse_analytics_event(document)

    assert event.event_type == event_type
    assert event.partition_key == event.stream_id
    assert canonical_contract_json(event) == (FIXTURE_ROOT / name).read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize(
    "field",
    [
        "stream_url",
        "frame_bytes",
        "face-template",
        "embedding",
        "owner_record",
        "watchlist_match",
        "secret_ref",
        "video",
    ],
)
def test_prohibited_fields_are_rejected_before_schema_validation(field: str) -> None:
    document = _fixture("observation-created-v1.json")
    payload = document["payload"]
    assert isinstance(payload, dict)
    payload[field] = "do-not-echo"

    with pytest.raises(AnalyticsContractSafetyError) as exc_info:
        parse_analytics_event(document, forward_compatible=True)

    assert field in str(exc_info.value)
    assert "do-not-echo" not in str(exc_info.value)


@pytest.mark.parametrize(
    "sensitive_value",
    [
        "rtsp://user:password@camera.example/live",
        "https://camera.example/frame.jpg",
        "Bearer secret-value",
        "-----BEGIN PRIVATE KEY-----",
    ],
)
def test_sensitive_values_are_rejected_without_echoing_them(
    sensitive_value: str,
) -> None:
    document = _fixture("model-deployment-changed-v1.json")
    payload = document["payload"]
    assert isinstance(payload, dict)
    payload["future_note"] = sensitive_value

    with pytest.raises(AnalyticsContractSafetyError) as exc_info:
        parse_analytics_event(document, forward_compatible=True)

    assert sensitive_value not in str(exc_info.value)


def test_forward_consumer_ignores_safe_optional_fields_but_strict_producer_rejects() -> (
    None
):
    document = _fixture("observation-created-v1.json")
    payload = document["payload"]
    assert isinstance(payload, dict)
    payload["future_quality_hint"] = "generated-only"

    with pytest.raises(ValidationError):
        parse_analytics_event(document)

    parsed = parse_analytics_event(document, forward_compatible=True)
    assert "future_quality_hint" not in parsed.payload.model_dump()


def test_unknown_major_event_version_is_rejected() -> None:
    document = _fixture("observation-created-v1.json")
    document["event_type"] = "hcam.analytics.observation.created.v2"
    document["schema_version"] = 2

    with pytest.raises(ValueError, match="unsupported analytics event"):
        parse_analytics_event(document, forward_compatible=True)


def test_partition_key_must_equal_stream_id() -> None:
    document = _fixture("observation-created-v1.json")
    document["partition_key"] = "str_22222222222222222222222222222222"

    with pytest.raises(ValidationError, match="partition_key must equal stream_id"):
        parse_analytics_event(document)


@pytest.mark.parametrize("scope_field", ["stream_id", "camera_id"])
def test_payload_scope_must_match_envelope(scope_field: str) -> None:
    document = _fixture("observation-created-v1.json")
    payload = document["payload"]
    assert isinstance(payload, dict)
    payload[scope_field] = (
        "str_22222222222222222222222222222222"
        if scope_field == "stream_id"
        else "synthetic:cctv-002"
    )

    with pytest.raises(ValidationError, match=f"payload {scope_field} must match"):
        parse_analytics_event(document)


def test_timestamps_must_be_timezone_aware_utc() -> None:
    document = _fixture("observation-created-v1.json")
    document["occurred_at"] = datetime(2026, 8, 24, 12, 0).isoformat()

    with pytest.raises(ValidationError, match="timezone-aware UTC"):
        parse_analytics_event(document)


@pytest.mark.parametrize(
    "values",
    [
        {"x": 0.9, "y": 0.1, "width": 0.2, "height": 0.2},
        {"x": 0.1, "y": 0.9, "width": 0.2, "height": 0.2},
        {"x": -0.1, "y": 0.1, "width": 0.2, "height": 0.2},
        {"x": 0.1, "y": 0.1, "width": 0.0, "height": 0.2},
    ],
)
def test_normalized_bounding_box_is_bounded(values: dict[str, float]) -> None:
    with pytest.raises(ValidationError):
        NormalizedBoundingBox.model_validate(values)


def test_artifact_versions_are_immutable_digests() -> None:
    with pytest.raises(ValidationError):
        VersionedArtifact(id="det-r0", version="latest")


def test_track_visible_frames_cannot_exceed_age() -> None:
    with pytest.raises(ValidationError, match="visible_frames cannot exceed"):
        TrackPayloadV1(
            track_id="trk_11111111111111111111111111111111",
            tracker_epoch="epoch_11111111111111111111111111111111",
            stream_id=STREAM_ID,
            camera_id=CAMERA_ID,
            state="updated",
            observed_at=OBSERVED_AT,
            class_id="vehicle.car",
            latest_observation_id="obs_11111111111111111111111111111111",
            age_frames=2,
            visible_frames=3,
            tracker=TRACKER,
            pipeline=PIPELINE,
            configuration_digest=f"sha256:{'9' * 64}",
        )


def test_analytic_event_requires_local_evidence() -> None:
    with pytest.raises(ValidationError, match="local evidence reference"):
        AnalyticEventPayloadV1(
            analytic_event_id="aevt_11111111111111111111111111111111",
            stream_id=STREAM_ID,
            camera_id=CAMERA_ID,
            event_kind="zone.entry",
            observed_at=OBSERVED_AT,
            track_refs=[],
            observation_refs=[],
            rule=VersionedConfiguration(id="rule-1", version=1),
            geometry_ref=VersionedConfiguration(id="zone-1", version=1),
            lineage=LINEAGE,
            confidence=0.8,
        )


def test_phase3_analytic_event_cannot_claim_an_alert_decision() -> None:
    document = _fixture("analytic-event-created-v1.json")
    payload = document["payload"]
    assert isinstance(payload, dict)
    payload["alert_state"] = "alerted"

    with pytest.raises(ValidationError):
        parse_analytics_event(document)


def test_deployment_transition_requires_a_changed_target() -> None:
    target = DeploymentTargetV1(
        pipeline=PIPELINE,
        models=[MODEL],
        configuration_digest=f"sha256:{'8' * 64}",
    )
    common = {
        "assignment_id": "ana_11111111111111111111111111111111",
        "department": "phase3-lab",
        "stream_id": STREAM_ID,
        "camera_id": CAMERA_ID,
        "capability": "object_detection",
        "lifecycle_state": "pending",
        "reason_code": "assignment_approved",
        "actor_id": "phase3-owner",
        "change_reason": "Generated contract transition",
        "approval_record_id": "D-P3.0-001",
        "effective_at": OBSERVED_AT,
    }

    with pytest.raises(ValidationError, match="previous or current"):
        ModelDeploymentPayloadV1(previous=None, current=None, **common)
    with pytest.raises(ValidationError, match="must change the target"):
        ModelDeploymentPayloadV1(previous=target, current=target, **common)


def test_event_size_limit_applies_before_forward_fields_are_ignored() -> None:
    document = copy.deepcopy(_fixture("observation-created-v1.json"))
    payload = document["payload"]
    assert isinstance(payload, dict)
    payload["future_note"] = "x" * 1_000

    with pytest.raises(ValueError, match="maximum payload size"):
        parse_analytics_event(
            document,
            forward_compatible=True,
            max_bytes=200,
        )


def test_max_event_size_constant_is_bounded() -> None:
    assert MAX_EVENT_BYTES == 64 * 1024
