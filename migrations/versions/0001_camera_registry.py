"""Create camera registry and audit foundation.

Revision ID: 0001_camera_registry
Revises:
Create Date: 2026-08-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_camera_registry"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=160), nullable=True),
        sa.Column("action", sa.String(length=160), nullable=False),
        sa.Column("target_type", sa.String(length=120), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_occurred_at", "audit_events", ["occurred_at"])

    op.create_table(
        "cameras",
        sa.Column("camera_id", sa.String(length=160), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("location_label", sa.String(length=500), nullable=True),
        sa.Column("timezone_name", sa.String(length=80), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("ownership", sa.String(length=120), nullable=True),
        sa.Column("camera_type", sa.String(length=80), nullable=True),
        sa.Column("connectivity_status", sa.String(length=80), nullable=True),
        sa.Column("storage_status", sa.String(length=80), nullable=True),
        sa.Column("health_status", sa.String(length=80), nullable=True),
        sa.Column("maintenance_status", sa.String(length=80), nullable=True),
        sa.Column("metadata_status", sa.String(length=80), nullable=True),
        sa.Column("operational_status", sa.String(length=80), nullable=True),
        sa.Column("stream_path", sa.Text(), nullable=True),
        sa.Column("hls_path", sa.Text(), nullable=True),
        sa.Column("selected_url", sa.Text(), nullable=True),
        sa.Column("delivery_type", sa.String(length=80), nullable=True),
        sa.Column("codec", sa.String(length=80), nullable=True),
        sa.Column("container", sa.String(length=80), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("reachability", sa.String(length=80), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_schema", sa.String(length=120), nullable=False),
        sa.Column("source_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("camera_id"),
        sa.UniqueConstraint(
            "source_id", "external_id", name="uq_camera_source_external"
        ),
    )
    op.create_index("ix_cameras_camera_type", "cameras", ["camera_type"])
    op.create_index("ix_cameras_department", "cameras", ["department"])
    op.create_index("ix_cameras_health_status", "cameras", ["health_status"])
    op.create_index("ix_cameras_operational_status", "cameras", ["operational_status"])
    op.create_index("ix_cameras_source_id", "cameras", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_cameras_source_id", table_name="cameras")
    op.drop_index("ix_cameras_operational_status", table_name="cameras")
    op.drop_index("ix_cameras_health_status", table_name="cameras")
    op.drop_index("ix_cameras_department", table_name="cameras")
    op.drop_index("ix_cameras_camera_type", table_name="cameras")
    op.drop_table("cameras")
    op.drop_index("ix_audit_events_occurred_at", table_name="audit_events")
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_table("audit_events")
