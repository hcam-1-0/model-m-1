"""Add Phase 2 stream management foundation.

Revision ID: 0004_stream_management
Revises: 0003_camera_integrity
Create Date: 2026-08-18
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from urllib.parse import urlsplit

import sqlalchemy as sa
from alembic import op


revision: str = "0004_stream_management"
down_revision: str | None = "0003_camera_integrity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _legacy_stream_id(camera_id: str) -> str:
    digest = hashlib.sha256(camera_id.encode("utf-8")).hexdigest()[:32]
    return f"str_{digest}"


def _legacy_protocol(locator: str, delivery: str | None) -> str:
    scheme = urlsplit(locator).scheme.lower()
    if delivery == "hls" and scheme in {"http", "https"}:
        return "hls"
    if scheme in {"rtsp", "rtsps", "http", "https"}:
        return scheme
    return "http"


def upgrade() -> None:
    op.create_table(
        "stream_endpoints",
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("camera_id", sa.String(length=160), nullable=False),
        sa.Column("version_id", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("adapter_kind", sa.String(length=32), nullable=False),
        sa.Column("protocol", sa.String(length=16), nullable=False),
        sa.Column("locator", sa.Text(), nullable=False),
        sa.Column("secret_ref", sa.String(length=255), nullable=True),
        sa.Column("transport", sa.String(length=16), server_default="tcp", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("probe_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_owner", sa.String(length=160), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_id >= 1", name="ck_stream_version_positive"),
        sa.CheckConstraint(
            "transport IN ('tcp', 'udp', 'auto')", name="ck_stream_transport"
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"], ["cameras.camera_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("stream_id"),
        sa.UniqueConstraint("camera_id", "name", name="uq_stream_camera_name"),
    )
    op.create_index("ix_stream_endpoints_camera_id", "stream_endpoints", ["camera_id"])
    op.create_index("ix_stream_endpoints_adapter_kind", "stream_endpoints", ["adapter_kind"])
    op.create_index("ix_stream_endpoints_protocol", "stream_endpoints", ["protocol"])
    op.create_index("ix_stream_endpoints_enabled", "stream_endpoints", ["enabled"])
    op.create_index("ix_stream_endpoints_probe_due_at", "stream_endpoints", ["probe_due_at"])
    op.create_index("ix_stream_endpoints_lease_until", "stream_endpoints", ["lease_until"])
    op.create_index(
        "uq_stream_primary_camera",
        "stream_endpoints",
        ["camera_id"],
        unique=True,
        sqlite_where=sa.text("is_primary = 1"),
        postgresql_where=sa.text("is_primary"),
    )

    op.create_table(
        "stream_health_current",
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), server_default="unknown", nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_successes", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("consecutive_failures", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("probe_latency_ms", sa.Float(), nullable=True),
        sa.Column("codec", sa.String(length=80), nullable=True),
        sa.Column("container", sa.String(length=80), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("frame_rate", sa.Float(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('unknown', 'healthy', 'degraded', 'offline', "
            "'unauthorized', 'misconfigured', 'unsupported')",
            name="ck_stream_health_state",
        ),
        sa.CheckConstraint(
            "consecutive_successes >= 0 AND consecutive_failures >= 0",
            name="ck_stream_health_counts_nonnegative",
        ),
        sa.CheckConstraint(
            "probe_latency_ms IS NULL OR probe_latency_ms >= 0",
            name="ck_stream_health_latency_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["stream_id"], ["stream_endpoints.stream_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("stream_id"),
    )
    op.create_index("ix_stream_health_current_state", "stream_health_current", ["state"])
    op.create_index(
        "ix_stream_health_current_observed_at", "stream_health_current", ["observed_at"]
    )

    op.create_table(
        "stream_probe_runs",
        sa.Column("probe_id", sa.String(length=64), nullable=False),
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("worker_id", sa.String(length=160), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("media", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            "outcome IN ('success', 'failure')", name="ck_stream_probe_outcome"
        ),
        sa.CheckConstraint("latency_ms >= 0", name="ck_stream_probe_latency_nonnegative"),
        sa.ForeignKeyConstraint(
            ["stream_id"], ["stream_endpoints.stream_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("probe_id"),
    )
    op.create_index("ix_stream_probe_runs_stream_id", "stream_probe_runs", ["stream_id"])
    op.create_index("ix_stream_probe_runs_started_at", "stream_probe_runs", ["started_at"])
    op.create_index("ix_stream_probe_runs_outcome", "stream_probe_runs", ["outcome"])

    op.create_table(
        "stream_event_outbox",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("camera_id", sa.String(length=160), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["stream_id"], ["stream_endpoints.stream_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_stream_event_outbox_event_type", "stream_event_outbox", ["event_type"])
    op.create_index("ix_stream_event_outbox_stream_id", "stream_event_outbox", ["stream_id"])
    op.create_index("ix_stream_event_outbox_camera_id", "stream_event_outbox", ["camera_id"])
    op.create_index("ix_stream_event_outbox_occurred_at", "stream_event_outbox", ["occurred_at"])
    op.create_index("ix_stream_event_outbox_published_at", "stream_event_outbox", ["published_at"])

    connection = op.get_bind()
    cameras = sa.table(
        "cameras",
        sa.column("camera_id", sa.String),
        sa.column("stream_path", sa.Text),
        sa.column("hls_path", sa.Text),
        sa.column("selected_url", sa.Text),
        sa.column("delivery_type", sa.String),
        sa.column("codec", sa.String),
        sa.column("container", sa.String),
        sa.column("reachability", sa.String),
        sa.column("last_checked_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    endpoints = sa.table(
        "stream_endpoints",
        sa.column("stream_id", sa.String),
        sa.column("camera_id", sa.String),
        sa.column("version_id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("adapter_kind", sa.String),
        sa.column("protocol", sa.String),
        sa.column("locator", sa.Text),
        sa.column("secret_ref", sa.String),
        sa.column("transport", sa.String),
        sa.column("is_primary", sa.Boolean),
        sa.column("enabled", sa.Boolean),
        sa.column("probe_due_at", sa.DateTime(timezone=True)),
        sa.column("lease_owner", sa.String),
        sa.column("lease_until", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    health = sa.table(
        "stream_health_current",
        sa.column("stream_id", sa.String),
        sa.column("state", sa.String),
        sa.column("reason_code", sa.String),
        sa.column("observed_at", sa.DateTime(timezone=True)),
        sa.column("consecutive_successes", sa.Integer),
        sa.column("consecutive_failures", sa.Integer),
        sa.column("probe_latency_ms", sa.Float),
        sa.column("codec", sa.String),
        sa.column("container", sa.String),
        sa.column("width", sa.Integer),
        sa.column("height", sa.Integer),
        sa.column("frame_rate", sa.Float),
        sa.column("last_success_at", sa.DateTime(timezone=True)),
        sa.column("last_failure_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    for row in connection.execute(sa.select(cameras)).mappings():
        locator = row["selected_url"] or row["hls_path"] or row["stream_path"]
        if not locator:
            continue
        stream_id = _legacy_stream_id(row["camera_id"])
        connection.execute(
            endpoints.insert().values(
                stream_id=stream_id,
                camera_id=row["camera_id"],
                version_id=1,
                name="primary",
                adapter_kind="legacy",
                protocol=_legacy_protocol(locator, row["delivery_type"]),
                locator=locator,
                secret_ref=None,
                transport="tcp",
                is_primary=True,
                enabled=True,
                probe_due_at=row["updated_at"],
                lease_owner=None,
                lease_until=None,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        )
        state = row["reachability"]
        if state not in {
            "unknown",
            "healthy",
            "degraded",
            "offline",
            "unauthorized",
            "misconfigured",
            "unsupported",
        }:
            state = "unknown"
        connection.execute(
            health.insert().values(
                stream_id=stream_id,
                state=state or "unknown",
                reason_code=None,
                observed_at=row["last_checked_at"],
                consecutive_successes=0,
                consecutive_failures=0,
                probe_latency_ms=None,
                codec=row["codec"],
                container=row["container"],
                width=None,
                height=None,
                frame_rate=None,
                last_success_at=None,
                last_failure_at=None,
                updated_at=row["updated_at"],
            )
        )


def downgrade() -> None:
    op.drop_index("ix_stream_event_outbox_published_at", table_name="stream_event_outbox")
    op.drop_index("ix_stream_event_outbox_occurred_at", table_name="stream_event_outbox")
    op.drop_index("ix_stream_event_outbox_camera_id", table_name="stream_event_outbox")
    op.drop_index("ix_stream_event_outbox_stream_id", table_name="stream_event_outbox")
    op.drop_index("ix_stream_event_outbox_event_type", table_name="stream_event_outbox")
    op.drop_table("stream_event_outbox")
    op.drop_index("ix_stream_probe_runs_outcome", table_name="stream_probe_runs")
    op.drop_index("ix_stream_probe_runs_started_at", table_name="stream_probe_runs")
    op.drop_index("ix_stream_probe_runs_stream_id", table_name="stream_probe_runs")
    op.drop_table("stream_probe_runs")
    op.drop_index("ix_stream_health_current_observed_at", table_name="stream_health_current")
    op.drop_index("ix_stream_health_current_state", table_name="stream_health_current")
    op.drop_table("stream_health_current")
    op.drop_index("uq_stream_primary_camera", table_name="stream_endpoints")
    op.drop_index("ix_stream_endpoints_lease_until", table_name="stream_endpoints")
    op.drop_index("ix_stream_endpoints_probe_due_at", table_name="stream_endpoints")
    op.drop_index("ix_stream_endpoints_enabled", table_name="stream_endpoints")
    op.drop_index("ix_stream_endpoints_protocol", table_name="stream_endpoints")
    op.drop_index("ix_stream_endpoints_adapter_kind", table_name="stream_endpoints")
    op.drop_index("ix_stream_endpoints_camera_id", table_name="stream_endpoints")
    op.drop_table("stream_endpoints")
