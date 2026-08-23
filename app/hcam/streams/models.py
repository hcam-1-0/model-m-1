from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    Boolean,
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


STREAM_STATES = (
    "unknown",
    "healthy",
    "degraded",
    "offline",
    "unauthorized",
    "misconfigured",
    "unsupported",
)


class StreamEndpoint(Base):
    __tablename__ = "stream_endpoints"
    __table_args__ = (
        UniqueConstraint("camera_id", "name", name="uq_stream_camera_name"),
        CheckConstraint("version_id >= 1", name="ck_stream_version_positive"),
        CheckConstraint(
            "transport IN ('tcp', 'udp', 'auto')",
            name="ck_stream_transport",
        ),
        CheckConstraint(
            "onvif_auth_mode IN ('none', 'wsse_password_digest', "
            "'http_digest', 'wsse_and_http_digest')",
            name="ck_stream_onvif_auth_mode",
        ),
        CheckConstraint(
            "onvif_max_velocity > 0 AND onvif_max_velocity <= 1",
            name="ck_stream_onvif_max_velocity",
        ),
        CheckConstraint(
            "onvif_max_move_seconds >= 0.1 AND onvif_max_move_seconds <= 10",
            name="ck_stream_onvif_max_move_seconds",
        ),
        Index(
            "uq_stream_primary_camera",
            "camera_id",
            unique=True,
            sqlite_where=text("is_primary = 1"),
            postgresql_where=text("is_primary"),
        ),
    )

    stream_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    camera_id: Mapped[str] = mapped_column(
        ForeignKey("cameras.camera_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    adapter_kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    protocol: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    locator: Mapped[str] = mapped_column(Text, nullable=False)
    secret_ref: Mapped[str | None] = mapped_column(String(255))
    management_locator: Mapped[str | None] = mapped_column(Text)
    onvif_auth_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="none", server_default="none"
    )
    capability_refresh_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    capability_due_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime(), index=True
    )
    onvif_control_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    onvif_max_velocity: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5, server_default=text("0.5")
    )
    onvif_max_move_seconds: Mapped[float] = mapped_column(
        Float, nullable=False, default=2.0, server_default=text("2.0")
    )
    transport: Mapped[str] = mapped_column(
        String(16), nullable=False, default="tcp", server_default="tcp"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true"), index=True
    )
    probe_due_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), index=True)
    lease_owner: Mapped[str | None] = mapped_column(String(160))
    lease_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), index=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, onupdate=utc_now
    )

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}


class StreamHealthCurrent(Base):
    __tablename__ = "stream_health_current"
    __table_args__ = (
        CheckConstraint(
            "state IN ('unknown', 'healthy', 'degraded', 'offline', "
            "'unauthorized', 'misconfigured', 'unsupported')",
            name="ck_stream_health_state",
        ),
        CheckConstraint(
            "consecutive_successes >= 0 AND consecutive_failures >= 0",
            name="ck_stream_health_counts_nonnegative",
        ),
        CheckConstraint(
            "probe_latency_ms IS NULL OR probe_latency_ms >= 0",
            name="ck_stream_health_latency_nonnegative",
        ),
    )

    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"), primary_key=True
    )
    state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unknown", server_default="unknown", index=True
    )
    reason_code: Mapped[str | None] = mapped_column(String(64))
    observed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), index=True)
    consecutive_successes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    probe_latency_ms: Mapped[float | None] = mapped_column(Float)
    codec: Mapped[str | None] = mapped_column(String(80))
    container: Mapped[str | None] = mapped_column(String(80))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    frame_rate: Mapped[float | None] = mapped_column(Float)
    last_success_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    last_failure_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, onupdate=utc_now
    )


class StreamProbeRun(Base):
    __tablename__ = "stream_probe_runs"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('success', 'failure')", name="ck_stream_probe_outcome"
        ),
        CheckConstraint("latency_ms >= 0", name="ck_stream_probe_latency_nonnegative"),
    )

    probe_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    worker_id: Mapped[str] = mapped_column(String(160), nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, index=True)
    finished_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    reason_code: Mapped[str | None] = mapped_column(String(64))
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    media: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class StreamEventOutbox(Base):
    __tablename__ = "stream_event_outbox"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    camera_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), index=True)


class PlaybackSession(Base):
    __tablename__ = "playback_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    token_jti_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, index=True
    )


class StreamCapabilitySnapshot(Base):
    __tablename__ = "stream_capability_snapshots"
    __table_args__ = (
        CheckConstraint(
            "source IN ('device_and_media', 'media_only')",
            name="ck_stream_capability_snapshot_source",
        ),
        CheckConstraint(
            "completeness IN ('complete', 'partial')",
            name="ck_stream_capability_snapshot_completeness",
        ),
        Index(
            "ix_stream_capability_snapshot_latest",
            "stream_id",
            "last_observed_at",
        ),
    )

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    completeness: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    first_observed_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, index=True
    )
    last_observed_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )


class StreamCapabilityRefresh(Base):
    __tablename__ = "stream_capability_refreshes"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_stream_capability_refresh_status",
        ),
        CheckConstraint(
            "source IN ('manual', 'scheduled')",
            name="ck_stream_capability_refresh_source",
        ),
        CheckConstraint(
            "attempt_count >= 0 AND max_attempts >= 1",
            name="ck_stream_capability_refresh_attempts",
        ),
        CheckConstraint(
            "duration_ms IS NULL OR duration_ms >= 0",
            name="ck_stream_capability_refresh_duration",
        ),
        CheckConstraint(
            "result_completeness IS NULL OR "
            "result_completeness IN ('complete', 'partial')",
            name="ck_stream_capability_refresh_completeness",
        ),
        Index(
            "uq_stream_capability_refresh_active",
            "stream_id",
            unique=True,
            sqlite_where=text("status IN ('queued', 'running')"),
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
        Index(
            "ix_stream_capability_refresh_claim",
            "status",
            "next_attempt_at",
            "priority",
        ),
    )

    refresh_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    requested_by: Mapped[str | None] = mapped_column(String(160), index=True)
    request_id: Mapped[str | None] = mapped_column(String(160))
    audit_reason: Mapped[str] = mapped_column(String(500), nullable=False)
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default=text("3")
    )
    next_attempt_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, index=True
    )
    lease_owner: Mapped[str | None] = mapped_column(String(160))
    lease_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), index=True)
    reason_code: Mapped[str | None] = mapped_column(String(64))
    duration_ms: Mapped[float | None] = mapped_column(Float)
    result_completeness: Mapped[str | None] = mapped_column(String(16))
    snapshot_id: Mapped[str | None] = mapped_column(
        ForeignKey("stream_capability_snapshots.snapshot_id", ondelete="SET NULL"),
        index=True,
    )
    queued_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), index=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, onupdate=utc_now
    )


class OnvifControlLease(Base):
    __tablename__ = "onvif_control_leases"

    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"), primary_key=True
    )
    lease_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    acquired_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, index=True
    )


class OnvifOperationRun(Base):
    __tablename__ = "onvif_operation_runs"
    __table_args__ = (
        CheckConstraint(
            "operation_type IN ('imaging_inspect', 'event_pull', "
            "'ptz_stop', 'ptz_continuous', 'ptz_relative', "
            "'ptz_absolute', 'ptz_goto_preset', 'ws_discovery', "
            "'capability_discover_sync')",
            name="ck_onvif_operation_type",
        ),
        CheckConstraint(
            "outcome IN ('pending', 'success', 'failure')",
            name="ck_onvif_operation_outcome",
        ),
        CheckConstraint(
            "(outcome = 'pending' AND finished_at IS NULL AND duration_ms IS NULL) "
            "OR (outcome IN ('success', 'failure') AND finished_at IS NOT NULL "
            "AND duration_ms >= 0)",
            name="ck_onvif_operation_lifecycle",
        ),
    )

    operation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stream_id: Mapped[str | None] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    operation_type: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True
    )
    outcome: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    reason_code: Mapped[str | None] = mapped_column(String(64))
    parameters: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    audit_reason: Mapped[str] = mapped_column(String(500), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(160))
    requested_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    duration_ms: Mapped[float | None] = mapped_column(Float)
