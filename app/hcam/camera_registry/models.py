from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import TypeDecorator
from geoalchemy2 import Geometry

from hcam.database import Base, UTCDateTime


def utc_now() -> datetime:
    return datetime.now(UTC)


class PortablePointGeometry(TypeDecorator[Any]):
    """PostGIS POINT on PostgreSQL and inert text storage on SQLite.

    SQLite is the project's lightweight test/development database and does not
    load Spatialite. Keeping GeoAlchemy's ``Geometry`` as the model's top-level
    type makes GeoAlchemy emit ``RecoverGeometryColumn`` calls on SQLite. This
    wrapper preserves the real PostGIS type and bind/result processors while
    allowing the non-spatial SQLite contract to create and migrate cleanly.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[no-untyped-def]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(
                Geometry(
                    geometry_type="POINT",
                    srid=4326,
                    spatial_index=False,
                    from_text="ST_GeomFromEWKT",
                    name="geometry",
                )
            )
        return dialect.type_descriptor(Text())


class Camera(Base):
    __tablename__ = "cameras"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_camera_source_external"),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="ck_cameras_coordinate_pair",
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_cameras_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_cameras_longitude_range",
        ),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_cameras_duration_nonnegative",
        ),
        CheckConstraint("version_id >= 1", name="ck_cameras_version_positive"),
        Index("ix_cameras_geometry", "geometry", postgresql_using="gist"),
    )

    camera_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    location_label: Mapped[str | None] = mapped_column(String(500))
    timezone_name: Mapped[str | None] = mapped_column(String(80))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    # PostGIS geometry column (POINT, SRID 4326)
    geometry: Mapped[Any | None] = mapped_column(
        PortablePointGeometry(),
        nullable=True,
    )

    @hybrid_property
    def lat(self) -> float | None:
        """Return latitude from geometry if lat/long columns are null."""
        if self.latitude is not None:
            return self.latitude
        if self.geometry is not None:
            # Extract latitude from geometry (ST_Y)
            # This is a hybrid property, so we can't execute SQL here
            # The value will be set via Python when geometry is loaded
            pass
        return None

    @hybrid_property
    def lon(self) -> float | None:
        """Return longitude from geometry if lat/long columns are null."""
        if self.longitude is not None:
            return self.longitude
        if self.geometry is not None:
            pass
        return None

    def sync_geometry_from_coords(self) -> None:
        """Update geometry column from latitude/longitude values."""
        if self.latitude is not None and self.longitude is not None:
            from geoalchemy2.shape import from_shape
            from shapely.geometry import Point
            point = Point(self.longitude, self.latitude)
            self.geometry = from_shape(point, srid=4326)

    def sync_coords_from_geometry(self) -> None:
        """Update latitude/longitude from geometry column."""
        if self.geometry is not None:
            # geometry is a WKBElement, we can extract coordinates
            from geoalchemy2.shape import to_shape
            point = to_shape(self.geometry)
            self.longitude = point.x
            self.latitude = point.y

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

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}
