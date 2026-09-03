"""Merge the camera GIS and Phase 3 analytics migration lines.

Revision ID: 0012_merge_camera_gis
Revises: 0011_geometry_events, 0008_postgis_gis
Create Date: 2026-09-03
"""

from __future__ import annotations

from collections.abc import Sequence


revision: str = "0012_merge_camera_gis"
down_revision: tuple[str, str] = ("0011_geometry_events", "0008_postgis_gis")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
