"""Add optimistic concurrency version to cameras.

Revision ID: 0002_camera_version
Revises: 0001_camera_registry
Create Date: 2026-08-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_camera_version"
down_revision: str | None = "0001_camera_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("cameras") as batch_op:
        batch_op.add_column(
            sa.Column(
                "version_id",
                sa.Integer(),
                server_default=sa.text("1"),
                nullable=False,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("cameras") as batch_op:
        batch_op.drop_column("version_id")
