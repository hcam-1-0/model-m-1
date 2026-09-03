"""Add generated-only analytics execution metadata.

Revision ID: 0009_generated_analytics
Revises: 0008_analytics_assignments
Create Date: 2026-08-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0009_generated_analytics"
down_revision: str | None = "0008_analytics_assignments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _replace_assignment_constraints_for_generated_scope() -> None:
    with op.batch_alter_table("analytics_assignments") as batch_op:
        batch_op.add_column(
            sa.Column(
                "execution_scope",
                sa.String(length=32),
                server_default="generated_only",
                nullable=False,
            )
        )
        for name in (
            "ck_analytics_assignment_p3_desired_state",
            "ck_analytics_assignment_p3_lifecycle_state",
            "ck_analytics_assignment_p3_reason_code",
        ):
            batch_op.drop_constraint(name, type_="check")
        batch_op.create_check_constraint(
            "ck_analytics_assignment_p3_desired_state",
            "desired_state IN ('paused', 'enabled')",
        )
        batch_op.create_check_constraint(
            "ck_analytics_assignment_p3_lifecycle_state",
            "lifecycle_state IN ('blocked', 'paused', 'running', 'degraded', 'failed')",
        )
        batch_op.create_check_constraint(
            "ck_analytics_assignment_p3_reason_code",
            "reason_code IN ('owner_gates_pending', 'manual_pause', "
            "'generated_runtime_active', 'runtime_degraded', 'runtime_failed')",
        )
        batch_op.create_check_constraint(
            "ck_analytics_assignment_execution_scope",
            "execution_scope = 'generated_only'",
        )
        batch_op.create_check_constraint(
            "ck_analytics_assignment_state_consistency",
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
        )


def upgrade() -> None:
    _replace_assignment_constraints_for_generated_scope()

    op.create_table(
        "analytics_generated_runs",
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("assignment_id", sa.String(length=64), nullable=False),
        sa.Column("assignment_version", sa.Integer(), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=False),
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("camera_id", sa.String(length=160), nullable=False),
        sa.Column("source_sequence", sa.BigInteger(), nullable=False),
        sa.Column("source_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generator_id", sa.String(length=128), nullable=False),
        sa.Column("generator_version", sa.String(length=71), nullable=False),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("input_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("retention_class", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "assignment_version >= 1",
            name="ck_analytics_generated_run_assignment_version",
        ),
        sa.CheckConstraint(
            "source_sequence >= 0",
            name="ck_analytics_generated_run_sequence",
        ),
        sa.CheckConstraint(
            "seed >= 0 AND seed <= 4294967295",
            name="ck_analytics_generated_run_seed",
        ),
        sa.CheckConstraint(
            "generator_id = 'hcam.det-r0.generated-frame' AND "
            "generator_version = "
            "'sha256:910d7083976055269029733d90f70cafc0f3fe3046716c2c9d683732fc181f64'",
            name="ck_analytics_generated_run_generator",
        ),
        sa.CheckConstraint(
            "length(input_sha256) = 64 AND lower(input_sha256) = input_sha256",
            name="ck_analytics_generated_run_input_digest",
        ),
        sa.CheckConstraint(
            "status IN ('succeeded', 'degraded', 'failed')",
            name="ck_analytics_generated_run_status",
        ),
        sa.CheckConstraint(
            "(status = 'succeeded' AND failure_code IS NULL) OR "
            "(status IN ('degraded', 'failed') AND failure_code IS NOT NULL)",
            name="ck_analytics_generated_run_failure_consistency",
        ),
        sa.CheckConstraint(
            "candidate_count >= 0 AND candidate_count <= 300",
            name="ck_analytics_generated_run_candidate_count",
        ),
        sa.CheckConstraint(
            "duration_ms >= 0 AND duration_ms <= 60000",
            name="ck_analytics_generated_run_duration",
        ),
        sa.CheckConstraint(
            "retention_class IN ('derived.analytics.standard', "
            "'derived.analytics.restricted')",
            name="ck_analytics_generated_run_retention_class",
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["analytics_assignments.assignment_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["stream_id"], ["stream_endpoints.stream_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"], ["cameras.camera_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("run_id"),
        sa.UniqueConstraint(
            "assignment_id",
            "assignment_version",
            "source_sequence",
            "input_sha256",
            name="uq_analytics_generated_run_input",
        ),
    )
    for column in (
        "assignment_id",
        "department",
        "stream_id",
        "camera_id",
        "completed_at",
    ):
        op.create_index(
            f"ix_analytics_generated_runs_{column}",
            "analytics_generated_runs",
            [column],
        )
    op.create_index(
        "ix_analytics_generated_run_department_completed",
        "analytics_generated_runs",
        ["department", "completed_at"],
    )

    op.create_table(
        "analytics_observations",
        sa.Column("observation_id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("assignment_id", sa.String(length=64), nullable=False),
        sa.Column("candidate_index", sa.Integer(), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=False),
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("camera_id", sa.String(length=160), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_sequence", sa.BigInteger(), nullable=False),
        sa.Column("source_width", sa.Integer(), nullable=False),
        sa.Column("source_height", sa.Integer(), nullable=False),
        sa.Column("model_id", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=71), nullable=False),
        sa.Column("class_id", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("bbox_x", sa.Float(), nullable=False),
        sa.Column("bbox_y", sa.Float(), nullable=False),
        sa.Column("bbox_width", sa.Float(), nullable=False),
        sa.Column("bbox_height", sa.Float(), nullable=False),
        sa.Column("lineage", sa.JSON(), nullable=False),
        sa.Column("retention_class", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "candidate_index >= 0 AND candidate_index < 300",
            name="ck_analytics_observation_candidate_index",
        ),
        sa.CheckConstraint(
            "class_id IN ('object.person', 'vehicle.bicycle', 'vehicle.car', "
            "'vehicle.motorcycle', 'vehicle.bus', 'vehicle.truck', "
            "'object.unknown')",
            name="ck_analytics_observation_tier_a_class",
        ),
        sa.CheckConstraint(
            "model_id = 'DET-R0-ONNX-UPSTREAM-0.1.1RC0' AND model_version = "
            "'sha256:427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7'",
            name="ck_analytics_observation_model",
        ),
        sa.CheckConstraint(
            "source_width = 416 AND source_height = 416",
            name="ck_analytics_observation_source_shape",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_analytics_observation_confidence",
        ),
        sa.CheckConstraint(
            "bbox_x >= 0 AND bbox_x <= 1 AND bbox_y >= 0 AND bbox_y <= 1 AND "
            "bbox_width > 0 AND bbox_width <= 1 AND bbox_height > 0 AND "
            "bbox_height <= 1 AND bbox_x + bbox_width <= 1 AND "
            "bbox_y + bbox_height <= 1",
            name="ck_analytics_observation_bbox",
        ),
        sa.CheckConstraint(
            "retention_class IN ('derived.analytics.standard', "
            "'derived.analytics.restricted')",
            name="ck_analytics_observation_retention_class",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["analytics_generated_runs.run_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["analytics_assignments.assignment_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("observation_id"),
        sa.UniqueConstraint(
            "event_id",
            name="uq_analytics_observations_event_id",
        ),
        sa.UniqueConstraint(
            "run_id",
            "candidate_index",
            name="uq_analytics_observation_run_candidate",
        ),
    )
    for column in (
        "run_id",
        "assignment_id",
        "department",
        "stream_id",
        "camera_id",
        "class_id",
        "created_at",
    ):
        op.create_index(
            f"ix_analytics_observations_{column}",
            "analytics_observations",
            [column],
        )
    op.create_index(
        "ix_analytics_observation_department_created",
        "analytics_observations",
        ["department", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analytics_observation_department_created",
        table_name="analytics_observations",
    )
    for column in reversed(
        (
            "run_id",
            "assignment_id",
            "department",
            "stream_id",
            "camera_id",
            "class_id",
            "created_at",
        )
    ):
        op.drop_index(
            f"ix_analytics_observations_{column}",
            table_name="analytics_observations",
        )
    op.drop_table("analytics_observations")

    op.drop_index(
        "ix_analytics_generated_run_department_completed",
        table_name="analytics_generated_runs",
    )
    for column in reversed(
        (
            "assignment_id",
            "department",
            "stream_id",
            "camera_id",
            "completed_at",
        )
    ):
        op.drop_index(
            f"ix_analytics_generated_runs_{column}",
            table_name="analytics_generated_runs",
        )
    op.drop_table("analytics_generated_runs")

    op.execute(
        sa.text(
            "UPDATE analytics_assignments SET desired_state = 'paused', "
            "lifecycle_state = 'blocked', reason_code = 'owner_gates_pending'"
        )
    )
    with op.batch_alter_table("analytics_assignments") as batch_op:
        for name in (
            "ck_analytics_assignment_state_consistency",
            "ck_analytics_assignment_execution_scope",
            "ck_analytics_assignment_p3_desired_state",
            "ck_analytics_assignment_p3_lifecycle_state",
            "ck_analytics_assignment_p3_reason_code",
        ):
            batch_op.drop_constraint(name, type_="check")
        batch_op.create_check_constraint(
            "ck_analytics_assignment_p3_desired_state",
            "desired_state = 'paused'",
        )
        batch_op.create_check_constraint(
            "ck_analytics_assignment_p3_lifecycle_state",
            "lifecycle_state = 'blocked'",
        )
        batch_op.create_check_constraint(
            "ck_analytics_assignment_p3_reason_code",
            "reason_code = 'owner_gates_pending'",
        )
        batch_op.drop_column("execution_scope")
