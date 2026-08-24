from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
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


class AnalyticsAssignment(Base):
    __tablename__ = "analytics_assignments"
    __table_args__ = (
        UniqueConstraint(
            "stream_id",
            "capability",
            name="uq_analytics_assignment_stream_capability",
        ),
        CheckConstraint(
            "version_id >= 1",
            name="ck_analytics_assignment_version_positive",
        ),
        CheckConstraint(
            "desired_state = 'paused'",
            name="ck_analytics_assignment_p3_desired_state",
        ),
        CheckConstraint(
            "lifecycle_state = 'blocked'",
            name="ck_analytics_assignment_p3_lifecycle_state",
        ),
        CheckConstraint(
            "reason_code = 'owner_gates_pending'",
            name="ck_analytics_assignment_p3_reason_code",
        ),
        CheckConstraint(
            "minimum_confidence >= 0 AND minimum_confidence <= 1",
            name="ck_analytics_assignment_confidence",
        ),
        CheckConstraint(
            "sampling_fps > 0 AND sampling_fps <= 60",
            name="ck_analytics_assignment_sampling_fps",
        ),
        CheckConstraint(
            "maximum_queue_age_ms >= 50 AND maximum_queue_age_ms <= 60000",
            name="ck_analytics_assignment_queue_age",
        ),
        CheckConstraint(
            "retention_class IN ('derived.analytics.standard', "
            "'derived.analytics.restricted')",
            name="ck_analytics_assignment_retention_class",
        ),
        Index(
            "ix_analytics_assignment_department_state",
            "department",
            "lifecycle_state",
        ),
    )

    assignment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    camera_id: Mapped[str] = mapped_column(
        ForeignKey("cameras.camera_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capability: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    desired_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="paused", server_default="paused"
    )
    lifecycle_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="blocked", server_default="blocked"
    )
    reason_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="owner_gates_pending",
        server_default="owner_gates_pending",
    )
    pipeline_id: Mapped[str] = mapped_column(String(128), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(71), nullable=False)
    models: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    taxonomy_version: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(71), nullable=False)
    configuration_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    minimum_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    sampling_fps: Mapped[float] = mapped_column(Float, nullable=False)
    maximum_queue_age_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    geometry_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    last_actor_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    last_change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    approval_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, onupdate=utc_now, index=True
    )

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}


class AnalyticsAssignmentRevision(Base):
    __tablename__ = "analytics_assignment_revisions"
    __table_args__ = (
        CheckConstraint(
            "version >= 1",
            name="ck_analytics_assignment_revision_version_positive",
        ),
        Index(
            "ix_analytics_assignment_revision_recorded",
            "assignment_id",
            "recorded_at",
        ),
    )

    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("analytics_assignments.assignment_id", ondelete="CASCADE"),
        primary_key=True,
    )
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, index=True
    )
