from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from hcam.analytics.contracts import (
    AnalyticEventCreatedV1,
    AnalyticEventPayloadV1,
    AnalyticsAssignmentV1,
    DeploymentTargetV1,
    ModelDeploymentChangedV1,
    ModelDeploymentPayloadV1,
    NormalizedBoundingBox,
    ObjectClassification,
    ObservationCreatedV1,
    ObservationPayloadV1,
    ObservationQuality,
    ProcessingLineage,
    RuntimeReference,
    SourceFrame,
    TrackPayloadV1,
    TrackLifecyclePayloadV2,
    TrackLifecycleV2,
    TrackUpdatedV1,
    VersionedArtifact,
    VersionedConfiguration,
)
from hcam.analytics.geometry import (
    GeometryDefinitionV1,
    GeometryScheduleV1,
    LineGeometryV1,
    NormalizedPoint,
    WeeklyWindowV1,
    ZoneGeometryV1,
)
from hcam.analytics.runtime import (
    RuntimeAdapterDescriptorV1,
    RuntimeBatchRequestV1,
    RuntimeBatchRequestV2,
    RuntimeInputDescriptorV1,
    UnavailableAnalyticsRuntimeAdapter,
)
from hcam.analytics.spatial.contracts import GeometryRuleV1, RuleGraphV1, RuleNodeV1
from hcam.analytics.taxonomy import TaxonomyClassV1, TaxonomyManifestV1


STREAM_ID = "str_11111111111111111111111111111111"
CAMERA_ID = "synthetic:cctv-001"
TAXONOMY_VERSION = "hcam.objects.synthetic.v1"
PIPELINE = VersionedArtifact(
    id="fixture-tier-a-contract",
    version=f"sha256:{'1' * 64}",
)
MODEL = VersionedArtifact(
    id="fixture-detector",
    version=f"sha256:{'2' * 64}",
)
TRACKER = VersionedArtifact(
    id="fixture-tracker",
    version=f"sha256:{'3' * 64}",
)
LINEAGE = ProcessingLineage(
    code_version=f"sha256:{'4' * 64}",
    pipeline=PIPELINE,
    preprocessing_version=f"sha256:{'5' * 64}",
    postprocessing_version=f"sha256:{'6' * 64}",
    taxonomy_version=TAXONOMY_VERSION,
    policy_version=f"sha256:{'7' * 64}",
    runtime=RuntimeReference(name="contract-only-runtime", version="0.0.0+fixture"),
    configuration_digest=f"sha256:{'8' * 64}",
)
OBSERVED_AT = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
PROCESSED_AT = datetime(2026, 8, 24, 12, 0, 0, 50_000, tzinfo=UTC)


def golden_contract_fixtures() -> dict[str, BaseModel]:
    assignment = AnalyticsAssignmentV1(
        assignment_id="ana_11111111111111111111111111111111",
        department="phase3-lab",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        capability="object_detection",
        desired_state="enabled",
        version=1,
        pipeline=PIPELINE,
        models=[MODEL],
        taxonomy_version=TAXONOMY_VERSION,
        policy_version=f"sha256:{'7' * 64}",
        configuration_digest=f"sha256:{'8' * 64}",
        minimum_confidence=0.5,
        sampling_fps=5.0,
        maximum_queue_age_ms=2_000,
        geometry_refs=[],
        retention_class="derived.analytics.standard",
        actor_id="phase3-owner",
        reason="Start deterministic P3.0 contract validation",
        approval_record_id="D-P3.0-001",
        updated_at=OBSERVED_AT,
    )
    observation = ObservationCreatedV1(
        event_id="evt_11111111111111111111111111111111",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        partition_key=STREAM_ID,
        occurred_at=PROCESSED_AT,
        payload=ObservationPayloadV1(
            observation_id="obs_11111111111111111111111111111111",
            stream_id=STREAM_ID,
            camera_id=CAMERA_ID,
            observed_at=OBSERVED_AT,
            processed_at=PROCESSED_AT,
            source=SourceFrame(
                sequence=1,
                width=1_920,
                height=1_080,
                timestamp_source="generated",
                timestamp_confidence=1.0,
            ),
            lineage=LINEAGE,
            model=MODEL,
            **{"class": ObjectClassification(id="vehicle.car", confidence=0.91)},
            bbox=NormalizedBoundingBox(x=0.22, y=0.35, width=0.18, height=0.24),
            quality=ObservationQuality(
                blur_score=0.08,
                occlusion="partial",
                truncated=False,
            ),
            retention_class="derived.analytics.standard",
            review_state="unreviewed",
        ),
    )
    track = TrackUpdatedV1(
        event_id="evt_22222222222222222222222222222222",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        partition_key=STREAM_ID,
        occurred_at=PROCESSED_AT,
        payload=TrackPayloadV1(
            track_id="trk_11111111111111111111111111111111",
            tracker_epoch="epoch_11111111111111111111111111111111",
            stream_id=STREAM_ID,
            camera_id=CAMERA_ID,
            state="updated",
            observed_at=OBSERVED_AT,
            class_id="vehicle.car",
            latest_observation_id="obs_11111111111111111111111111111111",
            age_frames=31,
            visible_frames=26,
            tracker=TRACKER,
            pipeline=PIPELINE,
            configuration_digest=f"sha256:{'9' * 64}",
        ),
    )
    track_lifecycle = TrackLifecycleV2(
        event_id="evt_55555555555555555555555555555555",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        partition_key=STREAM_ID,
        occurred_at=PROCESSED_AT,
        payload=TrackLifecyclePayloadV2(
            track_id="trk_11111111111111111111111111111111",
            tracker_epoch="epoch_11111111111111111111111111111111",
            stream_id=STREAM_ID,
            camera_id=CAMERA_ID,
            state="updated",
            reason="recovered",
            first_observed_at=OBSERVED_AT - timedelta(seconds=3),
            first_sequence=7,
            observed_at=PROCESSED_AT,
            source_sequence=10,
            last_visible_at=PROCESSED_AT,
            last_visible_sequence=10,
            latest_observation_id="obs_11111111111111111111111111111111",
            class_id="vehicle.car",
            bbox=NormalizedBoundingBox(x=0.22, y=0.35, width=0.18, height=0.24),
            confidence=0.91,
            age_frames=4,
            visible_frames=3,
            missed_frames=0,
            tracker=TRACKER,
            lineage=LINEAGE,
            retention_class="derived.analytics.standard",
        ),
    )
    analytic_event = AnalyticEventCreatedV1(
        event_id="evt_33333333333333333333333333333333",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        partition_key=STREAM_ID,
        occurred_at=PROCESSED_AT,
        payload=AnalyticEventPayloadV1(
            analytic_event_id="aevt_11111111111111111111111111111111",
            stream_id=STREAM_ID,
            camera_id=CAMERA_ID,
            event_kind="zone.entry",
            observed_at=OBSERVED_AT,
            track_refs=[
                "epoch_11111111111111111111111111111111:"
                "trk_11111111111111111111111111111111"
            ],
            observation_refs=[],
            rule=VersionedConfiguration(id="loading-zone-entry", version=1),
            geometry_ref=VersionedConfiguration(id="zone-7", version=2),
            lineage=LINEAGE,
            confidence=0.88,
            review_state="unreviewed",
            alert_state="not_evaluated",
        ),
    )
    deployment = ModelDeploymentChangedV1(
        event_id="evt_44444444444444444444444444444444",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        partition_key=STREAM_ID,
        occurred_at=OBSERVED_AT,
        payload=ModelDeploymentPayloadV1(
            assignment_id="ana_11111111111111111111111111111111",
            department="phase3-lab",
            stream_id=STREAM_ID,
            camera_id=CAMERA_ID,
            capability="object_detection",
            previous=None,
            current=DeploymentTargetV1(
                pipeline=PIPELINE,
                models=[MODEL],
                configuration_digest=f"sha256:{'8' * 64}",
            ),
            lifecycle_state="pending",
            reason_code="assignment_approved",
            actor_id="phase3-owner",
            change_reason="Start approved generated-fixture assignment",
            approval_record_id="D-P3.0-001",
            effective_at=OBSERVED_AT,
        ),
    )
    taxonomy = TaxonomyManifestV1(
        taxonomy_version=TAXONOMY_VERSION,
        artifact_digest=f"sha256:{'a' * 64}",
        status="draft",
        intended_use="Generated metadata contract validation only",
        classes=[
            TaxonomyClassV1(
                id="object.entity",
                display_name="Entity",
                purpose="Root for generated object-class fixtures",
            ),
            TaxonomyClassV1(
                id="object.person",
                display_name="Person",
                parent_id="object.entity",
                purpose="Anonymous person bounding-box fixture",
            ),
            TaxonomyClassV1(
                id="object.vehicle",
                display_name="Vehicle",
                parent_id="object.entity",
                purpose="Generic vehicle bounding-box fixture",
            ),
            TaxonomyClassV1(
                id="vehicle.car",
                display_name="Car",
                parent_id="object.vehicle",
                purpose="Passenger-car bounding-box fixture",
            ),
        ],
        unknown_class_policy="reject",
        prohibited_uses=[
            "autonomous_enforcement",
            "biometric_identification",
            "cross_camera_identity",
            "person_reidentification",
            "sensitive_trait_inference",
        ],
        owner_id="phase3-owner",
        independent_reviewer_id=None,
        approval_record_id=None,
        created_at=OBSERVED_AT,
        updated_at=OBSERVED_AT,
    )
    line_geometry = GeometryDefinitionV1(
        geometry_id="line-1",
        version=1,
        department="phase3-lab",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        status="draft",
        shape=LineGeometryV1(
            start=NormalizedPoint(x=0.2, y=0.5),
            end=NormalizedPoint(x=0.8, y=0.5),
            crossing_direction="both",
        ),
        schedule=GeometryScheduleV1(
            mode="weekly",
            timezone="Asia/Kolkata",
            windows=[
                WeeklyWindowV1(
                    days=["monday", "tuesday", "wednesday", "thursday", "friday"],
                    start_minute=480,
                    end_minute=1_080,
                )
            ],
        ),
        intended_use="Generated line-crossing contract validation",
        policy_version=f"sha256:{'7' * 64}",
        owner_id="phase3-owner",
        created_at=OBSERVED_AT,
        updated_at=OBSERVED_AT,
    )
    zone_geometry = GeometryDefinitionV1(
        geometry_id="zone-1",
        version=1,
        department="phase3-lab",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        status="draft",
        shape=ZoneGeometryV1(
            vertices=[
                NormalizedPoint(x=0.2, y=0.2),
                NormalizedPoint(x=0.8, y=0.2),
                NormalizedPoint(x=0.8, y=0.8),
                NormalizedPoint(x=0.2, y=0.8),
            ],
        ),
        intended_use="Generated zone contract validation",
        policy_version=f"sha256:{'7' * 64}",
        owner_id="phase3-owner",
        created_at=OBSERVED_AT,
        updated_at=OBSERVED_AT,
    )
    geometry_rule = GeometryRuleV1(
        rule_id="line-crossing-vehicle",
        version=1,
        status="draft",
        department="phase3-lab",
        assignment_id="ana_11111111111111111111111111111111",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        geometry_id=line_geometry.geometry_id,
        geometry_version=line_geometry.version,
        event_kind="hcam.analytics.line.crossing.v1",
        class_filter=["vehicle.car"],
        line_direction="both",
        deadband=0.01,
        rearm_distance=0.04,
        cel_condition="confidence >= 0.5 && class_id == 'vehicle.car'",
        graph=RuleGraphV1(
            nodes=[
                RuleNodeV1(
                    node_id="crossing",
                    kind="spatial",
                    signal="line_crossing",
                )
            ],
            output_node_id="crossing",
        ),
        configuration_digest=f"sha256:{'c' * 64}",
        retention_class="derived.analytics.standard",
        owner_id="phase3-owner",
        effective_from=OBSERVED_AT,
        created_at=OBSERVED_AT,
        updated_at=OBSERVED_AT,
    )
    runtime_adapter = RuntimeAdapterDescriptorV1(
        adapter_id="contract-only-runtime",
        adapter_version=f"sha256:{'b' * 64}",
        supported_capabilities=["object_detection"],
        maximum_batch_size=4,
        configured=False,
    )
    runtime_request = RuntimeBatchRequestV1(
        request_id="run_11111111111111111111111111111111",
        assignment_id="ana_11111111111111111111111111111111",
        capability="object_detection",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        deadline_at=OBSERVED_AT + timedelta(seconds=5),
        inputs=[
            RuntimeInputDescriptorV1(
                input_id="input_11111111111111111111111111111111",
                lease_id="lease_11111111111111111111111111111111",
                stream_id=STREAM_ID,
                camera_id=CAMERA_ID,
                source=SourceFrame(
                    sequence=1,
                    width=1_920,
                    height=1_080,
                    timestamp_source="generated",
                    timestamp_confidence=1.0,
                ),
                observed_at=OBSERVED_AT,
                issued_at=OBSERVED_AT,
                expires_at=OBSERVED_AT + timedelta(seconds=30),
                pixel_format="rgb8",
            )
        ],
    )
    runtime_result = UnavailableAnalyticsRuntimeAdapter(runtime_adapter).infer(
        runtime_request
    )
    runtime_request_v2 = RuntimeBatchRequestV2(
        **runtime_request.model_dump(exclude={"contract_type"}),
        minimum_confidence=0.5,
    )
    return {
        "assignment-v1.json": assignment,
        "observation-created-v1.json": observation,
        "track-updated-v1.json": track,
        "track-lifecycle-v2.json": track_lifecycle,
        "analytic-event-created-v1.json": analytic_event,
        "model-deployment-changed-v1.json": deployment,
        "taxonomy-draft-v1.json": taxonomy,
        "geometry-line-draft-v1.json": line_geometry,
        "geometry-zone-draft-v1.json": zone_geometry,
        "geometry-rule-draft-v1.json": geometry_rule,
        "runtime-adapter-unconfigured-v1.json": runtime_adapter,
        "runtime-request-v1.json": runtime_request,
        "runtime-request-v2.json": runtime_request_v2,
        "runtime-result-unconfigured-v1.json": runtime_result,
    }
