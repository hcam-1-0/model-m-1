"""Add PostGIS extension and geometry column for GIS queries.

Revision ID: 0008_postgis_gis
Revises: 0007_onvif_operations
Create Date: 2026-08-23
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography, Geometry


revision: str = "0008_postgis_gis"
down_revision: str | None = "0007_onvif_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Add geometry column (POINT, SRID 4326) to cameras table
    op.add_column(
        "cameras",
        sa.Column(
            "geometry",
            Geometry(geometry_type="POINT", srid=4326, from_text="ST_GeomFromEWKT", name="geometry"),
            nullable=True,
        ),
    )

    # Create GIST spatial index for fast spatial queries
    op.create_index(
        "ix_cameras_geometry",
        "cameras",
        ["geometry"],
        postgresql_using="gist",
    )

    # Backfill geometry from existing latitude/longitude columns
    op.execute("""
        UPDATE cameras
        SET geometry = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)


def downgrade() -> None:
    # Drop spatial index
    op.drop_index("ix_cameras_geometry", table_name="cameras", postgresql_using="gist")

    # Drop geometry column
    op.drop_column("cameras", "geometry")

    # Note: We don't drop PostGIS extension as other tables might use it