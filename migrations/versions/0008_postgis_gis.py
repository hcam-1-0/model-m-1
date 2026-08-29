"""Add PostGIS extension and geometry column for GIS queries.

Revision ID: 0008_postgis_gis
Revises: 0007_onvif_operations
Create Date: 2026-08-23
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


revision: str = "0008_postgis_gis"
down_revision: str | None = "0007_onvif_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect_name = op.get_bind().dialect.name
    if dialect_name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        geometry_type: sa.types.TypeEngine = Geometry(
            geometry_type="POINT",
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        )
    else:
        # SQLite remains a non-spatial development/test fallback. It retains
        # the schema column without requiring Spatialite functions.
        geometry_type = sa.Text()

    op.add_column(
        "cameras",
        sa.Column("geometry", geometry_type, nullable=True),
    )

    if dialect_name == "postgresql":
        op.create_index(
            "ix_cameras_geometry",
            "cameras",
            ["geometry"],
            postgresql_using="gist",
        )
        op.execute("""
            UPDATE cameras
            SET geometry = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """)
    else:
        op.create_index("ix_cameras_geometry", "cameras", ["geometry"])


def downgrade() -> None:
    dialect_name = op.get_bind().dialect.name
    if dialect_name == "postgresql":
        op.drop_index(
            "ix_cameras_geometry",
            table_name="cameras",
            postgresql_using="gist",
        )
    else:
        op.drop_index("ix_cameras_geometry", table_name="cameras")

    # Drop geometry column
    op.drop_column("cameras", "geometry")

    # Note: We don't drop PostGIS extension as other tables might use it
