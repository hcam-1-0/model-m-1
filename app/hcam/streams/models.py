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
