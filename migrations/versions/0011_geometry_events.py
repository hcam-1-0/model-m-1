"""Add generated-only P3.4 geometry and event primitives.

Revision ID: 0011_geometry_events
Revises: 0010_generated_tracking
Create Date: 2026-08-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from hcam.analytics.spatial.sql_types import image_geometry_type


revision: str = "0011_geometry_events"
down_revision: str | None = "0010_generated_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RETENTION = "'derived.analytics.standard', 'derived.analytics.restricted'"


def upgrade() -> None:
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"
    if is_postgresql:
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "analytics_geometries",
        sa.Column("geometry_record_id", sa.String(37), primary_key=True),
        sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
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
        sa.Column("geometry_id", sa.String(128), nullable=False),
        sa.Column("geometry_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("shape", sa.JSON(), nullable=False),
        sa.Column("schedule", sa.JSON(), nullable=False),
        sa.Column("canonical_json", sa.Text(), nullable=False),
        sa.Column("canonical_wkb", sa.LargeBinary(), nullable=False),
        sa.Column("spatial_geometry", image_geometry_type(), nullable=False),
        sa.Column("configuration_digest", sa.String(71), nullable=False),
        sa.Column("wkb_sha256", sa.String(64), nullable=False),
        sa.Column("shapely_version", sa.String(32), nullable=False),
        sa.Column("geos_version", sa.String(32), nullable=False),
        sa.Column("intended_use", sa.Text(), nullable=False),
        sa.Column("policy_version", sa.String(71), nullable=False),
        sa.Column("owner_id", sa.String(160), nullable=False),
        sa.Column("approval_record_id", sa.String(128), nullable=True),
        sa.Column("last_change_reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "record_version >= 1", name="ck_analytics_geometry_record_version"
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'retired')",
            name="ck_analytics_geometry_status",
        ),
        sa.CheckConstraint(
            "kind IN ('line', 'zone')", name="ck_analytics_geometry_kind"
        ),
        sa.CheckConstraint(
            "length(configuration_digest) = 71",
            name="ck_analytics_geometry_digest",
        ),
        sa.UniqueConstraint(
            "department",
            "geometry_id",
            "geometry_version",
            name="uq_analytics_geometry_department_version",
        ),
    )
    _indexes(
        "analytics_geometries",
        "department",
        "stream_id",
        "camera_id",
        "geometry_id",
        "configuration_digest",
        "owner_id",
        "created_at",
        "updated_at",
    )
    op.create_index(
        "ix_analytics_geometry_scope_status",
        "analytics_geometries",
        ["department", "stream_id", "status"],
    )
    if is_postgresql:
        op.create_check_constraint(
            "ck_analytics_geometry_postgis_valid",
            "analytics_geometries",
            "ST_IsValid(spatial_geometry) AND ST_SRID(spatial_geometry) = 0 "
            "AND ST_NDims(spatial_geometry) = 2 "
            "AND GeometryType(spatial_geometry) IN ('LINESTRING', 'POLYGON')",
        )
        op.create_check_constraint(
            "ck_analytics_geometry_postgis_wkb",
            "analytics_geometries",
            "ST_AsBinary(spatial_geometry) = canonical_wkb",
        )
        op.create_index(
            "ix_analytics_geometry_spatial_gist",
            "analytics_geometries",
            ["spatial_geometry"],
            postgresql_using="gist",
        )

    op.create_table(
        "analytics_geometry_rules",
        sa.Column("rule_record_id", sa.String(37), primary_key=True),
        sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "geometry_record_id",
            sa.String(37),
            sa.ForeignKey(
                "analytics_geometries.geometry_record_id", ondelete="RESTRICT"
            ),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column(
            "assignment_id",
            sa.String(64),
            sa.ForeignKey("analytics_assignments.assignment_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stream_id", sa.String(64), nullable=False),
        sa.Column("camera_id", sa.String(160), nullable=False),
        sa.Column("rule_id", sa.String(128), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("event_kind", sa.String(128), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("visual_graph", sa.JSON(), nullable=False),
        sa.Column("checked_cel", sa.LargeBinary(), nullable=False),
        sa.Column("checked_cel_digest", sa.String(71), nullable=False),
        sa.Column("configuration_digest", sa.String(71), nullable=False),
        sa.Column("static_cost", sa.Integer(), nullable=False),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.Column("owner_id", sa.String(160), nullable=False),
        sa.Column("approval_record_id", sa.String(128), nullable=True),
        sa.Column("last_change_reason", sa.Text(), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "record_version >= 1", name="ck_analytics_geometry_rule_record_version"
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'retired')",
            name="ck_analytics_geometry_rule_status",
        ),
        sa.CheckConstraint(
            "static_cost >= 1 AND static_cost <= 320",
            name="ck_analytics_geometry_rule_static_cost",
        ),
        sa.CheckConstraint(
            f"retention_class IN ({RETENTION})",
            name="ck_analytics_geometry_rule_retention",
        ),
        sa.UniqueConstraint(
            "department",
            "rule_id",
            "rule_version",
            name="uq_analytics_geometry_rule_department_version",
        ),
    )
    _indexes(
        "analytics_geometry_rules",
        "geometry_record_id",
        "department",
        "assignment_id",
        "stream_id",
        "camera_id",
        "rule_id",
        "event_kind",
        "configuration_digest",
        "owner_id",
        "created_at",
        "updated_at",
    )
    op.create_index(
        "ix_analytics_geometry_rule_scope_status",
        "analytics_geometry_rules",
        ["department", "assignment_id", "stream_id", "status"],
    )

    op.create_table(
        "analytics_geometry_evaluator_runs",
        sa.Column("run_id", sa.String(37), primary_key=True),
        sa.Column(
            "assignment_id",
            sa.String(64),
            sa.ForeignKey("analytics_assignments.assignment_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("stream_id", sa.String(64), nullable=False),
        sa.Column("camera_id", sa.String(160), nullable=False),
        sa.Column("epoch_id", sa.String(38), nullable=False),
        sa.Column("execution_scope", sa.String(32), nullable=False),
        sa.Column("scenario_id", sa.String(64), nullable=False),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("input_sha256", sa.String(64), nullable=False),
        sa.Column("configuration_digest", sa.String(71), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("close_reason", sa.String(64), nullable=True),
        sa.Column("input_count", sa.Integer(), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("late_count", sa.Integer(), nullable=False),
        sa.Column("maximum_buffer_depth", sa.Integer(), nullable=False),
        sa.Column("maximum_candidate_count", sa.Integer(), nullable=False),
        sa.Column("maximum_state_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "execution_scope = 'generated_only'",
            name="ck_analytics_geometry_run_scope",
        ),
        sa.CheckConstraint(
            "status IN ('succeeded', 'failed')",
            name="ck_analytics_geometry_run_status",
        ),
        sa.CheckConstraint(
            "close_reason IS NULL OR close_reason IN ('completed', "
            "'sequence_conflict', 'reorder_buffer_overflow', 'candidate_limit', "
            "'state_limit', 'scope_mismatch', 'timezone_unavailable', "
            "'persistence_conflict')",
            name="ck_analytics_geometry_run_close_reason",
        ),
        sa.CheckConstraint(
            f"retention_class IN ({RETENTION})",
            name="ck_analytics_geometry_run_retention",
        ),
        sa.UniqueConstraint(
            "assignment_id",
            "scenario_id",
            "seed",
            "input_sha256",
            "configuration_digest",
            name="uq_analytics_geometry_run_input",
        ),
    )
    _indexes(
        "analytics_geometry_evaluator_runs",
        "assignment_id",
        "department",
        "stream_id",
        "camera_id",
        "epoch_id",
        "scenario_id",
        "completed_at",
    )
    op.create_index(
        "ix_analytics_geometry_run_scope_completed",
        "analytics_geometry_evaluator_runs",
        ["department", "stream_id", "completed_at"],
    )

    op.create_table(
        "analytics_track_rule_states",
        sa.Column("state_id", sa.String(37), primary_key=True),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "evaluator_run_id",
            sa.String(37),
            sa.ForeignKey(
                "analytics_geometry_evaluator_runs.run_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column(
            "rule_record_id",
            sa.String(37),
            sa.ForeignKey(
                "analytics_geometry_rules.rule_record_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("stream_id", sa.String(64), nullable=False),
        sa.Column("epoch_id", sa.String(38), nullable=False),
        sa.Column("track_id", sa.String(36), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "version_id >= 1", name="ck_analytics_track_rule_state_version"
        ),
        sa.UniqueConstraint(
            "evaluator_run_id",
            "rule_record_id",
            "track_id",
            name="uq_analytics_track_rule_state_scope",
        ),
    )
    _indexes(
        "analytics_track_rule_states",
        "evaluator_run_id",
        "rule_record_id",
        "department",
        "stream_id",
        "epoch_id",
        "track_id",
    )
    op.create_index(
        "ix_analytics_track_rule_state_scope",
        "analytics_track_rule_states",
        ["department", "stream_id", "updated_at"],
    )

    op.create_table(
        "analytics_events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column(
            "evaluator_run_id",
            sa.String(37),
            sa.ForeignKey(
                "analytics_geometry_evaluator_runs.run_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column(
            "rule_record_id",
            sa.String(37),
            sa.ForeignKey(
                "analytics_geometry_rules.rule_record_id", ondelete="RESTRICT"
            ),
            nullable=False,
        ),
        sa.Column(
            "geometry_record_id",
            sa.String(37),
            sa.ForeignKey(
                "analytics_geometries.geometry_record_id", ondelete="RESTRICT"
            ),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("assignment_id", sa.String(36), nullable=False),
        sa.Column("stream_id", sa.String(64), nullable=False),
        sa.Column("camera_id", sa.String(160), nullable=False),
        sa.Column("epoch_id", sa.String(38), nullable=False),
        sa.Column("track_id", sa.String(36), nullable=True),
        sa.Column("lifecycle_id", sa.String(36), nullable=False),
        sa.Column("source_sequence", sa.BigInteger(), nullable=False),
        sa.Column("event_kind", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.Column("alert_state", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "alert_state = 'not_evaluated'",
            name="ck_analytics_event_alert_state",
        ),
        sa.CheckConstraint(
            f"retention_class IN ({RETENTION})",
            name="ck_analytics_event_retention",
        ),
    )
    _indexes(
        "analytics_events",
        "evaluator_run_id",
        "rule_record_id",
        "geometry_record_id",
        "department",
        "assignment_id",
        "stream_id",
        "camera_id",
        "epoch_id",
        "track_id",
        "event_kind",
        "occurred_at",
    )
    op.create_index(
        "ix_analytics_event_scope_occurred",
        "analytics_events",
        ["department", "stream_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_table("analytics_events")
    op.drop_table("analytics_track_rule_states")
    op.drop_table("analytics_geometry_evaluator_runs")
    op.drop_table("analytics_geometry_rules")
    op.drop_table("analytics_geometries")


def _indexes(table: str, *columns: str) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])
