"""Add generated-only anonymous stream-local tracking metadata.

Revision ID: 0010_generated_tracking
Revises: 0009_generated_analytics
Create Date: 2026-08-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0010_generated_tracking"
down_revision: str | None = "0009_generated_analytics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TIER_A = (
    "'object.person', 'vehicle.bicycle', 'vehicle.car', "
    "'vehicle.motorcycle', 'vehicle.bus', 'vehicle.truck', 'object.unknown'"
)
RETENTION = "'derived.analytics.standard', 'derived.analytics.restricted'"
RESET_REASONS = (
    "'explicit_reset', 'sequence_gap', 'sequence_regression', "
    "'timestamp_regression', 'configuration_change', 'source_change', "
    "'worker_restart', 'resource_exhausted'"
)
TRANSITION_REASONS = (
    "'confirmed', 'matched', 'recovered', 'temporarily_unmatched', "
    "'lost_timeout', " + RESET_REASONS
)


def upgrade() -> None:
    op.create_table(
        "analytics_tracking_runs",
        sa.Column("run_id", sa.String(37), primary_key=True),
        sa.Column(
            "assignment_id",
            sa.String(36),
            sa.ForeignKey("analytics_assignments.assignment_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assignment_version", sa.Integer(), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column(
            "stream_id",
            sa.String(64),
            sa.ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "camera_id",
            sa.String(160),
            sa.ForeignKey("cameras.camera_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scenario_id", sa.String(32), nullable=False),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("input_sha256", sa.String(64), nullable=False),
        sa.Column("generator_id", sa.String(128), nullable=False),
        sa.Column("generator_version", sa.String(71), nullable=False),
        sa.Column("tracker_id", sa.String(128), nullable=False),
        sa.Column("tracker_version", sa.String(71), nullable=False),
        sa.Column("pipeline_id", sa.String(128), nullable=False),
        sa.Column("pipeline_version", sa.String(71), nullable=False),
        sa.Column("configuration_digest", sa.String(71), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("failure_code", sa.String(64), nullable=True),
        sa.Column("frame_count", sa.Integer(), nullable=False),
        sa.Column("transition_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "assignment_version >= 1",
            name="ck_analytics_tracking_run_assignment_version",
        ),
        sa.CheckConstraint(
            "seed >= 0 AND seed <= 4294967295",
            name="ck_analytics_tracking_run_seed",
        ),
        sa.CheckConstraint(
            "scenario_id IN ('single-object', 'two-crossing', 'short-occlusion', "
            "'long-occlusion', 'all-tier-a', 'discontinuity', 'overload')",
            name="ck_analytics_tracking_run_scenario",
        ),
        sa.CheckConstraint(
            "status IN ('succeeded', 'failed')",
            name="ck_analytics_tracking_run_status",
        ),
        sa.CheckConstraint(
            "(status = 'succeeded' AND failure_code IS NULL) OR "
            "(status = 'failed' AND failure_code = 'resource_exhausted')",
            name="ck_analytics_tracking_run_failure_consistency",
        ),
        sa.CheckConstraint(
            "frame_count >= 0 AND frame_count <= 10000",
            name="ck_analytics_tracking_run_frame_count",
        ),
        sa.CheckConstraint(
            "transition_count >= 0 AND transition_count <= 1000000",
            name="ck_analytics_tracking_run_transition_count",
        ),
        sa.CheckConstraint(
            "duration_ms >= 0 AND duration_ms <= 60000",
            name="ck_analytics_tracking_run_duration",
        ),
        sa.CheckConstraint(
            "length(input_sha256) = 64 AND lower(input_sha256) = input_sha256",
            name="ck_analytics_tracking_run_input_digest",
        ),
        sa.CheckConstraint(
            f"retention_class IN ({RETENTION})",
            name="ck_analytics_tracking_run_retention_class",
        ),
        sa.UniqueConstraint(
            "assignment_id",
            "scenario_id",
            "seed",
            "input_sha256",
            "configuration_digest",
            name="uq_analytics_tracking_run_input",
        ),
    )
    _indexes(
        "analytics_tracking_runs",
        "assignment_id",
        "department",
        "stream_id",
        "camera_id",
        "scenario_id",
        "completed_at",
    )
    op.create_index(
        "ix_analytics_tracking_run_department_completed",
        "analytics_tracking_runs",
        ["department", "completed_at"],
    )

    op.create_table(
        "analytics_tracker_epochs",
        sa.Column("epoch_id", sa.String(38), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(37),
            sa.ForeignKey("analytics_tracking_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assignment_id", sa.String(36), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("stream_id", sa.String(64), nullable=False),
        sa.Column("camera_id", sa.String(160), nullable=False),
        sa.Column("epoch_index", sa.Integer(), nullable=False),
        sa.Column("tracker_id", sa.String(128), nullable=False),
        sa.Column("tracker_version", sa.String(71), nullable=False),
        sa.Column("configuration_digest", sa.String(71), nullable=False),
        sa.Column("start_sequence", sa.BigInteger(), nullable=False),
        sa.Column("end_sequence", sa.BigInteger(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_reason", sa.String(64), nullable=True),
        sa.CheckConstraint(
            "start_sequence >= 0 AND (end_sequence IS NULL OR end_sequence >= 0)",
            name="ck_analytics_tracker_epoch_sequence",
        ),
        sa.CheckConstraint(
            f"end_reason IS NULL OR end_reason IN ({RESET_REASONS})",
            name="ck_analytics_tracker_epoch_end_reason",
        ),
        sa.CheckConstraint(
            "(ended_at IS NULL AND end_sequence IS NULL AND end_reason IS NULL) OR "
            "(ended_at IS NOT NULL AND end_sequence IS NOT NULL AND "
            "end_reason IS NOT NULL)",
            name="ck_analytics_tracker_epoch_end_consistency",
        ),
        sa.UniqueConstraint(
            "run_id", "epoch_index", name="uq_analytics_tracker_epoch_run_index"
        ),
    )
    _indexes(
        "analytics_tracker_epochs",
        "run_id",
        "assignment_id",
        "department",
        "stream_id",
        "camera_id",
    )
    op.create_index(
        "ix_analytics_tracker_epoch_scope",
        "analytics_tracker_epochs",
        ["department", "stream_id", "started_at"],
    )

    op.create_table(
        "analytics_tracks",
        sa.Column("track_id", sa.String(36), primary_key=True),
        sa.Column(
            "epoch_id",
            sa.String(38),
            sa.ForeignKey("analytics_tracker_epochs.epoch_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "run_id",
            sa.String(37),
            sa.ForeignKey("analytics_tracking_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assignment_id", sa.String(36), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("stream_id", sa.String(64), nullable=False),
        sa.Column("camera_id", sa.String(160), nullable=False),
        sa.Column("local_track_number", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.String(128), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_sequence", sa.BigInteger(), nullable=False),
        sa.Column("latest_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latest_sequence", sa.BigInteger(), nullable=False),
        sa.Column("last_visible_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_visible_sequence", sa.BigInteger(), nullable=False),
        sa.Column("latest_observation_id", sa.String(36), nullable=False),
        sa.Column("bbox_x", sa.Float(), nullable=False),
        sa.Column("bbox_y", sa.Float(), nullable=False),
        sa.Column("bbox_width", sa.Float(), nullable=False),
        sa.Column("bbox_height", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("age_frames", sa.Integer(), nullable=False),
        sa.Column("visible_frames", sa.Integer(), nullable=False),
        sa.Column("missed_frames", sa.Integer(), nullable=False),
        sa.Column("tracker_id", sa.String(128), nullable=False),
        sa.Column("tracker_version", sa.String(71), nullable=False),
        sa.Column("pipeline_id", sa.String(128), nullable=False),
        sa.Column("pipeline_version", sa.String(71), nullable=False),
        sa.Column("taxonomy_version", sa.String(128), nullable=False),
        sa.Column("configuration_digest", sa.String(71), nullable=False),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"class_id IN ({TIER_A})",
            name="ck_analytics_track_tier_a_class",
        ),
        sa.CheckConstraint(
            "state IN ('started', 'updated', 'lost', 'ended')",
            name="ck_analytics_track_state",
        ),
        sa.CheckConstraint(
            "local_track_number >= 1 AND age_frames >= 1 AND visible_frames >= 1 "
            "AND visible_frames <= age_frames AND missed_frames >= 0",
            name="ck_analytics_track_counters",
        ),
        sa.CheckConstraint(
            "first_sequence >= 0 AND latest_sequence >= 0 AND "
            "last_visible_sequence >= 0",
            name="ck_analytics_track_sequences",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_analytics_track_confidence",
        ),
        sa.CheckConstraint(
            "bbox_x >= 0 AND bbox_x <= 1 AND bbox_y >= 0 AND bbox_y <= 1 AND "
            "bbox_width > 0 AND bbox_width <= 1 AND bbox_height > 0 AND "
            "bbox_height <= 1 AND bbox_x + bbox_width <= 1 AND "
            "bbox_y + bbox_height <= 1",
            name="ck_analytics_track_bbox",
        ),
        sa.CheckConstraint(
            f"retention_class IN ({RETENTION})",
            name="ck_analytics_track_retention_class",
        ),
        sa.UniqueConstraint(
            "epoch_id",
            "local_track_number",
            name="uq_analytics_track_epoch_local_number",
        ),
    )
    _indexes(
        "analytics_tracks",
        "epoch_id",
        "run_id",
        "assignment_id",
        "department",
        "stream_id",
        "camera_id",
        "class_id",
        "state",
    )
    op.create_index(
        "ix_analytics_track_scope_state",
        "analytics_tracks",
        ["department", "stream_id", "state"],
    )

    op.create_table(
        "analytics_track_lifecycle",
        sa.Column("lifecycle_id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False),
        sa.Column(
            "run_id",
            sa.String(37),
            sa.ForeignKey("analytics_tracking_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "epoch_id",
            sa.String(38),
            sa.ForeignKey("analytics_tracker_epochs.epoch_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "track_id",
            sa.String(36),
            sa.ForeignKey("analytics_tracks.track_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assignment_id", sa.String(36), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("stream_id", sa.String(64), nullable=False),
        sa.Column("camera_id", sa.String(160), nullable=False),
        sa.Column("transition_index", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_sequence", sa.BigInteger(), nullable=False),
        sa.Column("latest_observation_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "transition_index >= 0",
            name="ck_analytics_track_lifecycle_index",
        ),
        sa.CheckConstraint(
            "state IN ('started', 'updated', 'lost', 'ended')",
            name="ck_analytics_track_lifecycle_state",
        ),
        sa.CheckConstraint(
            f"reason IN ({TRANSITION_REASONS})",
            name="ck_analytics_track_lifecycle_reason",
        ),
        sa.UniqueConstraint(
            "event_id", name="uq_analytics_track_lifecycle_event"
        ),
        sa.UniqueConstraint(
            "run_id",
            "transition_index",
            name="uq_analytics_track_lifecycle_run_index",
        ),
    )
    _indexes(
        "analytics_track_lifecycle",
        "run_id",
        "epoch_id",
        "track_id",
        "assignment_id",
        "department",
        "stream_id",
        "camera_id",
    )
    op.create_index(
        "ix_analytics_track_lifecycle_scope",
        "analytics_track_lifecycle",
        ["department", "stream_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_table("analytics_track_lifecycle")
    op.drop_table("analytics_tracks")
    op.drop_table("analytics_tracker_epochs")
    op.drop_table("analytics_tracking_runs")


def _indexes(table: str, *columns: str) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])
