"""Add controlled ONVIF operations and audit evidence.

Revision ID: 0007_onvif_operations
Revises: 0006_onvif_capability_management
Create Date: 2026-08-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0007_onvif_operations"
down_revision: str | None = "0006_onvif_capability_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "stream_endpoints",
        sa.Column(
            "onvif_control_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "stream_endpoints",
        sa.Column(
            "onvif_max_velocity",
            sa.Float(),
            server_default=sa.text("0.5"),
            nullable=False,
        ),
    )
    op.add_column(
        "stream_endpoints",
        sa.Column(
            "onvif_max_move_seconds",
            sa.Float(),
            server_default=sa.text("2.0"),
            nullable=False,
        ),
    )
    with op.batch_alter_table("stream_endpoints") as batch_op:
        batch_op.create_check_constraint(
            "ck_stream_onvif_max_velocity",
            "onvif_max_velocity > 0 AND onvif_max_velocity <= 1",
        )
        batch_op.create_check_constraint(
            "ck_stream_onvif_max_move_seconds",
            "onvif_max_move_seconds >= 0.1 AND onvif_max_move_seconds <= 10",
        )

    op.create_table(
        "onvif_control_leases",
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("lease_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=160), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["stream_id"], ["stream_endpoints.stream_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("stream_id"),
        sa.UniqueConstraint("lease_id"),
    )
    op.create_index(
        "ix_onvif_control_leases_actor_id",
        "onvif_control_leases",
        ["actor_id"],
    )
    op.create_index(
        "ix_onvif_control_leases_expires_at",
        "onvif_control_leases",
        ["expires_at"],
    )

    op.create_table(
        "onvif_operation_runs",
        sa.Column("operation_id", sa.String(length=64), nullable=False),
        sa.Column("stream_id", sa.String(length=64)),
        sa.Column("actor_id", sa.String(length=160), nullable=False),
        sa.Column("operation_type", sa.String(length=40), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=64)),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("audit_reason", sa.String(length=500), nullable=False),
        sa.Column("request_id", sa.String(length=160)),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Float()),
        sa.CheckConstraint(
            "operation_type IN ('imaging_inspect', 'event_pull', "
            "'ptz_stop', 'ptz_continuous', 'ptz_relative', "
            "'ptz_absolute', 'ptz_goto_preset', 'ws_discovery', "
            "'capability_discover_sync')",
            name="ck_onvif_operation_type",
        ),
        sa.CheckConstraint(
            "outcome IN ('pending', 'success', 'failure')",
            name="ck_onvif_operation_outcome",
        ),
        sa.CheckConstraint(
            "(outcome = 'pending' AND finished_at IS NULL AND duration_ms IS NULL) "
            "OR (outcome IN ('success', 'failure') AND finished_at IS NOT NULL "
            "AND duration_ms >= 0)",
            name="ck_onvif_operation_lifecycle",
        ),
        sa.ForeignKeyConstraint(
            ["stream_id"], ["stream_endpoints.stream_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("operation_id"),
    )
    for column in (
        "stream_id",
        "actor_id",
        "operation_type",
        "outcome",
        "requested_at",
    ):
        op.create_index(
            f"ix_onvif_operation_runs_{column}",
            "onvif_operation_runs",
            [column],
        )


def downgrade() -> None:
    for column in reversed(
        ("stream_id", "actor_id", "operation_type", "outcome", "requested_at")
    ):
        op.drop_index(
            f"ix_onvif_operation_runs_{column}",
            table_name="onvif_operation_runs",
        )
    op.drop_table("onvif_operation_runs")
    op.drop_index(
        "ix_onvif_control_leases_expires_at",
        table_name="onvif_control_leases",
    )
    op.drop_index(
        "ix_onvif_control_leases_actor_id",
        table_name="onvif_control_leases",
    )
    op.drop_table("onvif_control_leases")
    with op.batch_alter_table("stream_endpoints") as batch_op:
        batch_op.drop_constraint(
            "ck_stream_onvif_max_move_seconds", type_="check"
        )
        batch_op.drop_constraint(
            "ck_stream_onvif_max_velocity", type_="check"
        )
    op.drop_column("stream_endpoints", "onvif_max_move_seconds")
    op.drop_column("stream_endpoints", "onvif_max_velocity")
    op.drop_column("stream_endpoints", "onvif_control_enabled")
