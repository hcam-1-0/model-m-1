from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from hcam.database import Base, UTCDateTime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Camera(Base):
    __tablename__ = "cameras"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_camera_source_external"),
    )

    camera_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    location_label: Mapped[str | None] = mapped_column(String(500))
    timezone_name: Mapped[str | None] = mapped_column(String(80))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    department: Mapped[str | None] = mapped_column(String(120), index=True)
    ownership: Mapped[str | None] = mapped_column(String(120))
    camera_type: Mapped[str | None] = mapped_column(String(80), index=True)
    connectivity_status: Mapped[str | None] = mapped_column(String(80))
    storage_status: Mapped[str | None] = mapped_column(String(80))
    health_status: Mapped[str | None] = mapped_column(String(80), index=True)
    maintenance_status: Mapped[str | None] = mapped_column(String(80))

    metadata_status: Mapped[str | None] = mapped_column(String(80))
    operational_status: Mapped[str | None] = mapped_column(String(80), index=True)

    stream_path: Mapped[str | None] = mapped_column(Text)
    hls_path: Mapped[str | None] = mapped_column(Text)
    selected_url: Mapped[str | None] = mapped_column(Text)
    delivery_type: Mapped[str | None] = mapped_column(String(80))
    codec: Mapped[str | None] = mapped_column(String(80))
    container: Mapped[str | None] = mapped_column(String(80))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    reachability: Mapped[str | None] = mapped_column(String(80))
    last_checked_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    source_schema: Mapped[str] = mapped_column(String(120), nullable=False)
    source_generated_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    imported_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now, onupdate=utc_now
    )
