"""Add authenticated ONVIF capability management.

Revision ID: 0006_onvif_capability_management
Revises: 0005_playback_sessions
Create Date: 2026-08-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0006_onvif_capability_management"
down_revision: str | None = "0005_playback_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("stream_endpoints", sa.Column("management_locator", sa.Text()))
    op.add_column(
        "stream_endpoints",
        sa.Column(
            "onvif_auth_mode",
            sa.String(length=32),
            server_default="none",
            nullable=False,
        ),
    )
    op.add_column(
        "stream_endpoints",
        sa.Column(
            "capability_refresh_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "stream_endpoints",
        sa.Column("capability_due_at", sa.DateTime(timezone=True)),
    )
    with op.batch_alter_table("stream_endpoints") as batch_op:
        batch_op.create_check_constraint(
            "ck_stream_onvif_auth_mode",
            "onvif_auth_mode IN ('none', 'wsse_password_digest', "
            "'http_digest', 'wsse_and_http_digest')",
        )
    op.create_index(
        "ix_stream_endpoints_capability_due_at",
        "stream_endpoints",
        ["capability_due_at"],
    )

    op.create_table(
        "stream_capability_snapshots",
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("completeness", sa.String(length=16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source IN ('device_and_media', 'media_only')",
            name="ck_stream_capability_snapshot_source",
        ),
        sa.CheckConstraint(
            "completeness IN ('complete', 'partial')",
            name="ck_stream_capability_snapshot_completeness",
        ),
        sa.ForeignKeyConstraint(
            ["stream_id"], ["stream_endpoints.stream_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("snapshot_id"),
    )
    op.create_index(
        "ix_stream_capability_snapshots_stream_id",
        "stream_capability_snapshots",
        ["stream_id"],
    )
    op.create_index(
        "ix_stream_capability_snapshots_fingerprint",
        "stream_capability_snapshots",
        ["fingerprint"],
    )
    op.create_index(
        "ix_stream_capability_snapshots_first_observed_at",
        "stream_capability_snapshots",
        ["first_observed_at"],
    )
    op.create_index(
        "ix_stream_capability_snapshots_last_observed_at",
        "stream_capability_snapshots",
        ["last_observed_at"],
    )
    op.create_index(
        "ix_stream_capability_snapshot_latest",
        "stream_capability_snapshots",
        ["stream_id", "last_observed_at"],
    )

    op.create_table(
        "stream_capability_refreshes",
        sa.Column("refresh_id", sa.String(length=64), nullable=False),
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("requested_by", sa.String(length=160)),
        sa.Column("request_id", sa.String(length=160)),
        sa.Column("audit_reason", sa.String(length=500), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_owner", sa.String(length=160)),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("reason_code", sa.String(length=64)),
        sa.Column("duration_ms", sa.Float()),
        sa.Column("result_completeness", sa.String(length=16)),
        sa.Column("snapshot_id", sa.String(length=64)),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_stream_capability_refresh_status",
        ),
        sa.CheckConstraint(
            "source IN ('manual', 'scheduled')",
            name="ck_stream_capability_refresh_source",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0 AND max_attempts >= 1",
            name="ck_stream_capability_refresh_attempts",
        ),
        sa.CheckConstraint(
            "duration_ms IS NULL OR duration_ms >= 0",
            name="ck_stream_capability_refresh_duration",
        ),
        sa.CheckConstraint(
            "result_completeness IS NULL OR result_completeness IN ('complete', 'partial')",
            name="ck_stream_capability_refresh_completeness",
        ),
        sa.ForeignKeyConstraint(
            ["stream_id"], ["stream_endpoints.stream_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["stream_capability_snapshots.snapshot_id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("refresh_id"),
    )
    for column in (
        "stream_id",
        "status",
        "source",
        "requested_by",
        "next_attempt_at",
        "lease_until",
        "snapshot_id",
        "queued_at",
        "finished_at",
    ):
        op.create_index(
            f"ix_stream_capability_refreshes_{column}",
            "stream_capability_refreshes",
            [column],
        )
    op.create_index(
        "uq_stream_capability_refresh_active",
        "stream_capability_refreshes",
        ["stream_id"],
        unique=True,
        sqlite_where=sa.text("status IN ('queued', 'running')"),
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )
    op.create_index(
        "ix_stream_capability_refresh_claim",
        "stream_capability_refreshes",
        ["status", "next_attempt_at", "priority"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_stream_capability_refresh_claim",
        table_name="stream_capability_refreshes",
    )
    op.drop_index(
        "uq_stream_capability_refresh_active",
        table_name="stream_capability_refreshes",
    )
    for column in reversed(
        (
            "stream_id",
            "status",
            "source",
            "requested_by",
            "next_attempt_at",
            "lease_until",
            "snapshot_id",
            "queued_at",
            "finished_at",
        )
    ):
        op.drop_index(
            f"ix_stream_capability_refreshes_{column}",
            table_name="stream_capability_refreshes",
        )
    op.drop_table("stream_capability_refreshes")
    op.drop_index(
        "ix_stream_capability_snapshot_latest",
        table_name="stream_capability_snapshots",
    )
    op.drop_index(
        "ix_stream_capability_snapshots_last_observed_at",
        table_name="stream_capability_snapshots",
    )
    op.drop_index(
        "ix_stream_capability_snapshots_first_observed_at",
        table_name="stream_capability_snapshots",
    )
    op.drop_index(
        "ix_stream_capability_snapshots_fingerprint",
        table_name="stream_capability_snapshots",
    )
    op.drop_index(
        "ix_stream_capability_snapshots_stream_id",
        table_name="stream_capability_snapshots",
    )
    op.drop_table("stream_capability_snapshots")
    op.drop_index(
        "ix_stream_endpoints_capability_due_at", table_name="stream_endpoints"
    )
    with op.batch_alter_table("stream_endpoints") as batch_op:
        batch_op.drop_constraint(
            "ck_stream_onvif_auth_mode",
            type_="check",
        )
    op.drop_column("stream_endpoints", "capability_due_at")
    op.drop_column("stream_endpoints", "capability_refresh_enabled")
    op.drop_column("stream_endpoints", "onvif_auth_mode")
    op.drop_column("stream_endpoints", "management_locator")
