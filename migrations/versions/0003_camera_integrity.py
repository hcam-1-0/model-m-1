"""Add camera registry integrity constraints.

Revision ID: 0003_camera_integrity
Revises: 0002_camera_version
Create Date: 2026-08-18
"""

from collections.abc import Sequence

from alembic import op


revision: str = "0003_camera_integrity"
down_revision: str | None = "0002_camera_version"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("cameras") as batch_op:
        batch_op.create_check_constraint(
            "ck_cameras_coordinate_pair",
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL)",
        )
        batch_op.create_check_constraint(
            "ck_cameras_latitude_range",
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
        )
        batch_op.create_check_constraint(
            "ck_cameras_longitude_range",
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
        )
        batch_op.create_check_constraint(
            "ck_cameras_duration_nonnegative",
            "duration_seconds IS NULL OR duration_seconds >= 0",
        )
        batch_op.create_check_constraint(
            "ck_cameras_version_positive",
            "version_id >= 1",
        )


def downgrade() -> None:
    with op.batch_alter_table("cameras") as batch_op:
        batch_op.drop_constraint(
            "ck_cameras_version_positive",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_cameras_duration_nonnegative",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_cameras_longitude_range",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_cameras_latitude_range",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_cameras_coordinate_pair",
            type_="check",
        )
