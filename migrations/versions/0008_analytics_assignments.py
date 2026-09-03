"""Add activation-blocked Phase 3 analytics assignments.

Revision ID: 0008_analytics_assignments
Revises: 0007_onvif_operations
Create Date: 2026-08-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0008_analytics_assignments"
down_revision: str | None = "0007_onvif_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analytics_assignments",
        sa.Column("assignment_id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=False),
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("camera_id", sa.String(length=160), nullable=False),
        sa.Column("capability", sa.String(length=128), nullable=False),
        sa.Column("desired_state", sa.String(length=16), server_default="paused", nullable=False),
        sa.Column("lifecycle_state", sa.String(length=16), server_default="blocked", nullable=False),
        sa.Column(
            "reason_code",
            sa.String(length=64),
            server_default="owner_gates_pending",
            nullable=False,
        ),
        sa.Column("pipeline_id", sa.String(length=128), nullable=False),
        sa.Column("pipeline_version", sa.String(length=71), nullable=False),
        sa.Column("models", sa.JSON(), nullable=False),
        sa.Column("taxonomy_version", sa.String(length=128), nullable=False),
        sa.Column("policy_version", sa.String(length=71), nullable=False),
        sa.Column("configuration_digest", sa.String(length=71), nullable=False),
        sa.Column("minimum_confidence", sa.Float(), nullable=False),
        sa.Column("sampling_fps", sa.Float(), nullable=False),
        sa.Column("maximum_queue_age_ms", sa.Integer(), nullable=False),
        sa.Column("geometry_refs", sa.JSON(), nullable=False),
        sa.Column("retention_class", sa.String(length=64), nullable=False),
        sa.Column("last_actor_id", sa.String(length=160), nullable=False),
        sa.Column("last_change_reason", sa.Text(), nullable=False),
        sa.Column("approval_record_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "version_id >= 1",
            name="ck_analytics_assignment_version_positive",
        ),
        sa.CheckConstraint(
            "desired_state = 'paused'",
            name="ck_analytics_assignment_p3_desired_state",
        ),
        sa.CheckConstraint(
            "lifecycle_state = 'blocked'",
            name="ck_analytics_assignment_p3_lifecycle_state",
        ),
        sa.CheckConstraint(
            "reason_code = 'owner_gates_pending'",
            name="ck_analytics_assignment_p3_reason_code",
        ),
        sa.CheckConstraint(
            "minimum_confidence >= 0 AND minimum_confidence <= 1",
            name="ck_analytics_assignment_confidence",
        ),
        sa.CheckConstraint(
            "sampling_fps > 0 AND sampling_fps <= 60",
            name="ck_analytics_assignment_sampling_fps",
        ),
        sa.CheckConstraint(
            "maximum_queue_age_ms >= 50 AND maximum_queue_age_ms <= 60000",
            name="ck_analytics_assignment_queue_age",
        ),
        sa.CheckConstraint(
            "retention_class IN ('derived.analytics.standard', "
            "'derived.analytics.restricted')",
            name="ck_analytics_assignment_retention_class",
        ),
        sa.ForeignKeyConstraint(
            ["stream_id"], ["stream_endpoints.stream_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"], ["cameras.camera_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("assignment_id"),
        sa.UniqueConstraint(
            "stream_id",
            "capability",
            name="uq_analytics_assignment_stream_capability",
        ),
    )
    for column in (
        "department",
        "stream_id",
        "camera_id",
        "capability",
        "last_actor_id",
        "created_at",
        "updated_at",
    ):
        op.create_index(
            f"ix_analytics_assignments_{column}",
            "analytics_assignments",
            [column],
        )
    op.create_index(
        "ix_analytics_assignment_department_state",
        "analytics_assignments",
        ["department", "lifecycle_state"],
    )

    op.create_table(
        "analytics_assignment_revisions",
        sa.Column("assignment_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("actor_id", sa.String(length=160), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_analytics_assignment_revision_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["analytics_assignments.assignment_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("assignment_id", "version"),
    )
    op.create_index(
        "ix_analytics_assignment_revisions_actor_id",
        "analytics_assignment_revisions",
        ["actor_id"],
    )
    op.create_index(
        "ix_analytics_assignment_revisions_recorded_at",
        "analytics_assignment_revisions",
        ["recorded_at"],
    )
    op.create_index(
        "ix_analytics_assignment_revision_recorded",
        "analytics_assignment_revisions",
        ["assignment_id", "recorded_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analytics_assignment_revision_recorded",
        table_name="analytics_assignment_revisions",
    )
    op.drop_index(
        "ix_analytics_assignment_revisions_recorded_at",
        table_name="analytics_assignment_revisions",
    )
    op.drop_index(
        "ix_analytics_assignment_revisions_actor_id",
        table_name="analytics_assignment_revisions",
    )
    op.drop_table("analytics_assignment_revisions")

    op.drop_index(
        "ix_analytics_assignment_department_state",
        table_name="analytics_assignments",
    )
    for column in reversed(
        (
            "department",
            "stream_id",
            "camera_id",
            "capability",
            "last_actor_id",
            "created_at",
            "updated_at",
        )
    ):
        op.drop_index(
            f"ix_analytics_assignments_{column}",
            table_name="analytics_assignments",
        )
    op.drop_table("analytics_assignments")
