"""Add indexed WGS84 camera geometry synchronized from coordinates.

Revision ID: 0008_postgis_gis
Revises: 0007_onvif_operations
Create Date: 2026-08-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0008_postgis_gis"
down_revision: str | None = "0007_onvif_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        op.add_column("cameras", sa.Column("geometry", sa.LargeBinary(), nullable=True))
        op.create_index("ix_cameras_geometry", "cameras", ["geometry"])
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("ALTER TABLE cameras ADD COLUMN geometry geometry(Point,4326)")
    op.execute(
        """
        UPDATE cameras
        SET geometry = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE FUNCTION hcam_sync_camera_geometry() RETURNS trigger AS $$
        BEGIN
            NEW.geometry := CASE
                WHEN NEW.latitude IS NULL OR NEW.longitude IS NULL THEN NULL
                ELSE ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)
            END;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_hcam_sync_camera_geometry
        BEFORE INSERT OR UPDATE OF latitude, longitude ON cameras
        FOR EACH ROW EXECUTE FUNCTION hcam_sync_camera_geometry()
        """
    )
    op.create_index(
        "ix_cameras_geometry",
        "cameras",
        ["geometry"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_index(
            "ix_cameras_geometry",
            table_name="cameras",
            postgresql_using="gist",
        )
        op.execute("DROP TRIGGER trg_hcam_sync_camera_geometry ON cameras")
        op.execute("DROP FUNCTION hcam_sync_camera_geometry()")
    op.drop_column("cameras", "geometry")
