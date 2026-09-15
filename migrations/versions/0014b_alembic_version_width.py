"""Widen Alembic's revision marker before long historical revisions.

Revision ID: 0014b_alembic_version_width
Revises: 0014_rule_authoring_evaluation
Create Date: 2026-09-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0014b_alembic_version_width"
down_revision: str | None = "0014_rule_authoring_evaluation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Allow Alembic to persist every reviewed revision identifier safely."""
    with op.batch_alter_table("alembic_version") as batch:
        batch.alter_column(
            "version_num",
            existing_type=sa.String(length=32),
            type_=sa.String(length=128),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Restore the historical width only before any long revision can exist."""
    with op.batch_alter_table("alembic_version") as batch:
        batch.alter_column(
            "version_num",
            existing_type=sa.String(length=128),
            type_=sa.String(length=32),
            existing_nullable=False,
        )
