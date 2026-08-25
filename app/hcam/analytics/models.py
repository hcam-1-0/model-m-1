from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from hcam.camera_registry.models import utc_now
from hcam.database import Base, UTCDateTime


class AnalyticsAssignment(Base):
    __tablename__ = "analytics_assignments"
    __table_args__ = (
        UniqueConstraint(
            "stream_id",
            "capability",
            name="uq_analytics_assignment_stream_capability",
        ),
        CheckConstraint(
            "version_id >= 1",
            name="ck_analytics_assignment_version_positive",
        ),
        CheckConstraint(
            "desired_state IN ('paused', 'enabled')",
            name="ck_analytics_assignment_p3_desired_state",
        ),
        CheckConstraint(
            "lifecycle_state IN ('blocked', 'paused', 'running', 'degraded', 'failed')",
            name="ck_analytics_assignment_p3_lifecycle_state",
        ),
        CheckConstraint(
            "reason_code IN ('owner_gates_pending', 'manual_pause', "
            "'generated_runtime_active', 'runtime_degraded', 'runtime_failed')",
            name="ck_analytics_assignment_p3_reason_code",
        ),
        CheckConstraint(
            "execution_scope = 'generated_only'",
            name="ck_analytics_assignment_execution_scope",
        ),
        CheckConstraint(
            "(desired_state = 'paused' AND lifecycle_state = 'blocked' AND "
            "reason_code = 'owner_gates_pending') OR "
            "(desired_state = 'paused' AND lifecycle_state = 'paused' AND "
            "reason_code = 'manual_pause') OR "
            "(desired_state = 'enabled' AND lifecycle_state = 'running' AND "
            "reason_code = 'generated_runtime_active') OR "
            "(desired_state = 'enabled' AND lifecycle_state = 'degraded' AND "
            "reason_code = 'runtime_degraded') OR "
            "(desired_state = 'enabled' AND lifecycle_state = 'failed' AND "
            "reason_code = 'runtime_failed')",
            name="ck_analytics_assignment_state_consistency",
        ),
        CheckConstraint(
            "minimum_confidence >= 0 AND minimum_confidence <= 1",
            name="ck_analytics_assignment_confidence",
        ),
        CheckConstraint(
            "sampling_fps > 0 AND sampling_fps <= 60",
            name="ck_analytics_assignment_sampling_fps",
        ),
        CheckConstraint(
            "maximum_queue_age_ms >= 50 AND maximum_queue_age_ms <= 60000",
            name="ck_analytics_assignment_queue_age",
        ),
        CheckConstraint(
            "retention_class IN ('derived.analytics.standard', "
            "'derived.analytics.restricted')",
            name="ck_analytics_assignment_retention_class",
        ),
        Index(
            "ix_analytics_assignment_department_state",
            "department",
            "lifecycle_state",
        ),
    )

    assignment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    camera_id: Mapped[str] = mapped_column(
        ForeignKey("cameras.camera_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capability: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    desired_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="paused", server_default="paused"
    )
    lifecycle_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="blocked", server_default="blocked"
    )
    reason_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="owner_gates_pending",
        server_default="owner_gates_pending",
    )
    execution_scope: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="generated_only",
        server_default="generated_only",
    )
    pipeline_id: Mapped[str] = mapped_column(String(128), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(71), nullable=False)
    models: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    taxonomy_version: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(71), nullable=False)
    configuration_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    minimum_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    sampling_fps: Mapped[float] = mapped_column(Float, nullable=False)
    maximum_queue_age_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    geometry_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    last_actor_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    last_change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    approval_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, onupdate=utc_now, index=True
    )

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}


class AnalyticsAssignmentRevision(Base):
    __tablename__ = "analytics_assignment_revisions"
    __table_args__ = (
        CheckConstraint(
            "version >= 1",
            name="ck_analytics_assignment_revision_version_positive",
        ),
        Index(
            "ix_analytics_assignment_revision_recorded",
            "assignment_id",
            "recorded_at",
        ),
    )

    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_assignments.assignment_id", ondelete="CASCADE"),
        primary_key=True,
    )
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, index=True
    )


class AnalyticsGeneratedRun(Base):
    __tablename__ = "analytics_generated_runs"
    __table_args__ = (
        CheckConstraint(
            "assignment_version >= 1",
            name="ck_analytics_generated_run_assignment_version",
        ),
        CheckConstraint(
            "source_sequence >= 0",
            name="ck_analytics_generated_run_sequence",
        ),
        CheckConstraint(
            "seed >= 0 AND seed <= 4294967295",
            name="ck_analytics_generated_run_seed",
        ),
        CheckConstraint(
            "generator_id = 'hcam.det-r0.generated-frame' AND "
            "generator_version = "
            "'sha256:910d7083976055269029733d90f70cafc0f3fe3046716c2c9d683732fc181f64'",
            name="ck_analytics_generated_run_generator",
        ),
        CheckConstraint(
            "length(input_sha256) = 64 AND lower(input_sha256) = input_sha256",
            name="ck_analytics_generated_run_input_digest",
        ),
        CheckConstraint(
            "status IN ('succeeded', 'degraded', 'failed')",
            name="ck_analytics_generated_run_status",
        ),
        CheckConstraint(
            "(status = 'succeeded' AND failure_code IS NULL) OR "
            "(status IN ('degraded', 'failed') AND failure_code IS NOT NULL)",
            name="ck_analytics_generated_run_failure_consistency",
        ),
        CheckConstraint(
            "candidate_count >= 0 AND candidate_count <= 300",
            name="ck_analytics_generated_run_candidate_count",
        ),
        CheckConstraint(
            "duration_ms >= 0 AND duration_ms <= 60000",
            name="ck_analytics_generated_run_duration",
        ),
        CheckConstraint(
            "retention_class IN ('derived.analytics.standard', "
            "'derived.analytics.restricted')",
            name="ck_analytics_generated_run_retention_class",
        ),
        UniqueConstraint(
            "assignment_id",
            "assignment_version",
            "source_sequence",
            "input_sha256",
            name="uq_analytics_generated_run_input",
        ),
        Index(
            "ix_analytics_generated_run_department_completed",
            "department",
            "completed_at",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_assignments.assignment_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_version: Mapped[int] = mapped_column(Integer, nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    camera_id: Mapped[str] = mapped_column(
        ForeignKey("cameras.camera_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    generator_id: Mapped[str] = mapped_column(String(128), nullable=False)
    generator_version: Mapped[str] = mapped_column(String(71), nullable=False)
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    input_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, index=True
    )


class AnalyticsObservation(Base):
    __tablename__ = "analytics_observations"
    __table_args__ = (
        CheckConstraint(
            "candidate_index >= 0 AND candidate_index < 300",
            name="ck_analytics_observation_candidate_index",
        ),
        CheckConstraint(
            "class_id IN ('object.person', 'vehicle.bicycle', 'vehicle.car', "
            "'vehicle.motorcycle', 'vehicle.bus', 'vehicle.truck', "
            "'object.unknown')",
            name="ck_analytics_observation_tier_a_class",
        ),
        CheckConstraint(
            "model_id = 'DET-R0-ONNX-UPSTREAM-0.1.1RC0' AND model_version = "
            "'sha256:427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7'",
            name="ck_analytics_observation_model",
        ),
        CheckConstraint(
            "source_width = 416 AND source_height = 416",
            name="ck_analytics_observation_source_shape",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_analytics_observation_confidence",
        ),
        CheckConstraint(
            "bbox_x >= 0 AND bbox_x <= 1 AND bbox_y >= 0 AND bbox_y <= 1 AND "
            "bbox_width > 0 AND bbox_width <= 1 AND bbox_height > 0 AND "
            "bbox_height <= 1 AND bbox_x + bbox_width <= 1 AND "
            "bbox_y + bbox_height <= 1",
            name="ck_analytics_observation_bbox",
        ),
        CheckConstraint(
            "retention_class IN ('derived.analytics.standard', "
            "'derived.analytics.restricted')",
            name="ck_analytics_observation_retention_class",
        ),
        UniqueConstraint(
            "event_id",
            name="uq_analytics_observations_event_id",
        ),
        UniqueConstraint(
            "run_id",
            "candidate_index",
            name="uq_analytics_observation_run_candidate",
        ),
        Index(
            "ix_analytics_observation_department_created",
            "department",
            "created_at",
        ),
    )

    observation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_generated_runs.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_assignments.assignment_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_index: Mapped[int] = mapped_column(Integer, nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stream_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    camera_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    source_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_width: Mapped[int] = mapped_column(Integer, nullable=False)
    source_height: Mapped[int] = mapped_column(Integer, nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(71), nullable=False)
    class_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_x: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_width: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_height: Mapped[float] = mapped_column(Float, nullable=False)
    lineage: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, index=True
    )


class AnalyticsTrackingRun(Base):
    __tablename__ = "analytics_tracking_runs"
    __table_args__ = (
        CheckConstraint(
            "assignment_version >= 1",
            name="ck_analytics_tracking_run_assignment_version",
        ),
        CheckConstraint(
            "seed >= 0 AND seed <= 4294967295",
            name="ck_analytics_tracking_run_seed",
        ),
        CheckConstraint(
            "scenario_id IN ('single-object', 'two-crossing', 'short-occlusion', "
            "'long-occlusion', 'all-tier-a', 'discontinuity', 'overload')",
            name="ck_analytics_tracking_run_scenario",
        ),
        CheckConstraint(
            "status IN ('succeeded', 'failed')",
            name="ck_analytics_tracking_run_status",
        ),
        CheckConstraint(
            "(status = 'succeeded' AND failure_code IS NULL) OR "
            "(status = 'failed' AND failure_code = 'resource_exhausted')",
            name="ck_analytics_tracking_run_failure_consistency",
        ),
        CheckConstraint(
            "frame_count >= 0 AND frame_count <= 10000",
            name="ck_analytics_tracking_run_frame_count",
        ),
        CheckConstraint(
            "transition_count >= 0 AND transition_count <= 1000000",
            name="ck_analytics_tracking_run_transition_count",
        ),
        CheckConstraint(
            "duration_ms >= 0 AND duration_ms <= 60000",
            name="ck_analytics_tracking_run_duration",
        ),
        CheckConstraint(
            "length(input_sha256) = 64 AND lower(input_sha256) = input_sha256",
            name="ck_analytics_tracking_run_input_digest",
        ),
        CheckConstraint(
            "retention_class IN ('derived.analytics.standard', "
            "'derived.analytics.restricted')",
            name="ck_analytics_tracking_run_retention_class",
        ),
        UniqueConstraint(
            "assignment_id",
            "scenario_id",
            "seed",
            "input_sha256",
            "configuration_digest",
            name="uq_analytics_tracking_run_input",
        ),
        Index(
            "ix_analytics_tracking_run_department_completed",
            "department",
            "completed_at",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    assignment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analytics_assignments.assignment_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_version: Mapped[int] = mapped_column(Integer, nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    camera_id: Mapped[str] = mapped_column(
        ForeignKey("cameras.camera_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scenario_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    input_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    generator_id: Mapped[str] = mapped_column(String(128), nullable=False)
    generator_version: Mapped[str] = mapped_column(String(71), nullable=False)
    tracker_id: Mapped[str] = mapped_column(String(128), nullable=False)
    tracker_version: Mapped[str] = mapped_column(String(71), nullable=False)
    pipeline_id: Mapped[str] = mapped_column(String(128), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(71), nullable=False)
    configuration_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frame_count: Mapped[int] = mapped_column(Integer, nullable=False)
    transition_count: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, index=True
    )


class AnalyticsTrackerEpoch(Base):
    __tablename__ = "analytics_tracker_epochs"
    __table_args__ = (
        CheckConstraint(
            "start_sequence >= 0 AND (end_sequence IS NULL OR end_sequence >= 0)",
            name="ck_analytics_tracker_epoch_sequence",
        ),
        CheckConstraint(
            "end_reason IS NULL OR end_reason IN ('explicit_reset', 'sequence_gap', "
            "'sequence_regression', 'timestamp_regression', "
            "'configuration_change', 'source_change', 'worker_restart', "
            "'resource_exhausted')",
            name="ck_analytics_tracker_epoch_end_reason",
        ),
        CheckConstraint(
            "(ended_at IS NULL AND end_sequence IS NULL AND end_reason IS NULL) OR "
            "(ended_at IS NOT NULL AND end_sequence IS NOT NULL AND "
            "end_reason IS NOT NULL)",
            name="ck_analytics_tracker_epoch_end_consistency",
        ),
        UniqueConstraint(
            "run_id",
            "epoch_index",
            name="uq_analytics_tracker_epoch_run_index",
        ),
        Index(
            "ix_analytics_tracker_epoch_scope",
            "department",
            "stream_id",
            "started_at",
        ),
    )

    epoch_id: Mapped[str] = mapped_column(String(38), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_tracking_runs.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stream_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    camera_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    epoch_index: Mapped[int] = mapped_column(Integer, nullable=False)
    tracker_id: Mapped[str] = mapped_column(String(128), nullable=False)
    tracker_version: Mapped[str] = mapped_column(String(71), nullable=False)
    configuration_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    start_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    end_sequence: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    end_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AnalyticsTrack(Base):
    __tablename__ = "analytics_tracks"
    __table_args__ = (
        CheckConstraint(
            "class_id IN ('object.person', 'vehicle.bicycle', 'vehicle.car', "
            "'vehicle.motorcycle', 'vehicle.bus', 'vehicle.truck', "
            "'object.unknown')",
            name="ck_analytics_track_tier_a_class",
        ),
        CheckConstraint(
            "state IN ('started', 'updated', 'lost', 'ended')",
            name="ck_analytics_track_state",
        ),
        CheckConstraint(
            "local_track_number >= 1 AND age_frames >= 1 AND visible_frames >= 1 "
            "AND visible_frames <= age_frames AND missed_frames >= 0",
            name="ck_analytics_track_counters",
        ),
        CheckConstraint(
            "first_sequence >= 0 AND latest_sequence >= 0 AND "
            "last_visible_sequence >= 0",
            name="ck_analytics_track_sequences",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_analytics_track_confidence",
        ),
        CheckConstraint(
            "bbox_x >= 0 AND bbox_x <= 1 AND bbox_y >= 0 AND bbox_y <= 1 AND "
            "bbox_width > 0 AND bbox_width <= 1 AND bbox_height > 0 AND "
            "bbox_height <= 1 AND bbox_x + bbox_width <= 1 AND "
            "bbox_y + bbox_height <= 1",
            name="ck_analytics_track_bbox",
        ),
        CheckConstraint(
            "retention_class IN ('derived.analytics.standard', "
            "'derived.analytics.restricted')",
            name="ck_analytics_track_retention_class",
        ),
        UniqueConstraint(
            "epoch_id",
            "local_track_number",
            name="uq_analytics_track_epoch_local_number",
        ),
        Index(
            "ix_analytics_track_scope_state",
            "department",
            "stream_id",
            "state",
        ),
    )

    track_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    epoch_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_tracker_epochs.epoch_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_tracking_runs.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stream_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    camera_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    local_track_number: Mapped[int] = mapped_column(Integer, nullable=False)
    class_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    first_observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    first_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    latest_observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    latest_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_visible_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    last_visible_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    latest_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    bbox_x: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_width: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_height: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    age_frames: Mapped[int] = mapped_column(Integer, nullable=False)
    visible_frames: Mapped[int] = mapped_column(Integer, nullable=False)
    missed_frames: Mapped[int] = mapped_column(Integer, nullable=False)
    tracker_id: Mapped[str] = mapped_column(String(128), nullable=False)
    tracker_version: Mapped[str] = mapped_column(String(71), nullable=False)
    pipeline_id: Mapped[str] = mapped_column(String(128), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(71), nullable=False)
    taxonomy_version: Mapped[str] = mapped_column(String(128), nullable=False)
    configuration_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class AnalyticsTrackLifecycle(Base):
    __tablename__ = "analytics_track_lifecycle"
    __table_args__ = (
        CheckConstraint(
            "transition_index >= 0",
            name="ck_analytics_track_lifecycle_index",
        ),
        CheckConstraint(
            "state IN ('started', 'updated', 'lost', 'ended')",
            name="ck_analytics_track_lifecycle_state",
        ),
        CheckConstraint(
            "reason IN ('confirmed', 'matched', 'recovered', "
            "'temporarily_unmatched', 'lost_timeout', 'explicit_reset', "
            "'sequence_gap', 'sequence_regression', 'timestamp_regression', "
            "'configuration_change', 'source_change', 'worker_restart', "
            "'resource_exhausted')",
            name="ck_analytics_track_lifecycle_reason",
        ),
        UniqueConstraint(
            "event_id",
            name="uq_analytics_track_lifecycle_event",
        ),
        UniqueConstraint(
            "run_id",
            "transition_index",
            name="uq_analytics_track_lifecycle_run_index",
        ),
        Index(
            "ix_analytics_track_lifecycle_scope",
            "department",
            "stream_id",
            "occurred_at",
        ),
    )

    lifecycle_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_tracking_runs.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    epoch_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_tracker_epochs.epoch_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    track_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_tracks.track_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stream_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    camera_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    transition_index: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    source_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    latest_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
