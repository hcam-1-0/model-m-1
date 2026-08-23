"""Add short-lived playback session records.

Revision ID: 0005_playback_sessions
Revises: 0004_stream_management
Create Date: 2026-08-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0005_playback_sessions"
down_revision: str | None = "0004_stream_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "playback_sessions",
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("stream_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=160), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("token_jti_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["stream_id"], ["stream_endpoints.stream_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("session_id"),
        sa.UniqueConstraint("token_jti_hash"),
    )
    op.create_index(
        "ix_playback_sessions_stream_id", "playback_sessions", ["stream_id"]
    )
    op.create_index(
        "ix_playback_sessions_actor_id", "playback_sessions", ["actor_id"]
    )
    op.create_index(
        "ix_playback_sessions_created_at", "playback_sessions", ["created_at"]
    )
    op.create_index(
        "ix_playback_sessions_expires_at", "playback_sessions", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_playback_sessions_expires_at", table_name="playback_sessions")
    op.drop_index("ix_playback_sessions_created_at", table_name="playback_sessions")
    op.drop_index("ix_playback_sessions_actor_id", table_name="playback_sessions")
    op.drop_index("ix_playback_sessions_stream_id", table_name="playback_sessions")
    op.drop_table("playback_sessions")
