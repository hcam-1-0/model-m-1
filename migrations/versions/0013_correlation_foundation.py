"""Add the generated-only Phase 4.1 correlation foundation.

Revision ID: 0013_correlation_foundation
Revises: 0012_intelligence_control_plane
Create Date: 2026-09-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0013_correlation_foundation"
down_revision: str | None = "0012_intelligence_control_plane"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NEW_TABLES = (
    "correlation_event_receipts",
    "correlation_partition_checkpoints",
    "correlation_window_events",
    "correlation_lane_results",
    "correlation_hypothesis_revisions",
)


def _enable_rls(table: str) -> None:
    policy = f"{table}_department_scope"
    predicate = (
        "current_setting('hcam.is_platform_admin', true) = 'true' OR "
        "department = ANY(string_to_array("
        "current_setting('hcam.allowed_departments', true), E'\\x1f'))"
    )
    op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
    op.execute(
        f'CREATE POLICY "{policy}" ON "{table}" '
        f"USING ({predicate}) WITH CHECK ({predicate})"
    )


def upgrade() -> None:
    with op.batch_alter_table("correlation_runs") as batch:
        batch.drop_constraint("ck_correlation_run_status", type_="check")
        batch.drop_constraint("ck_correlation_run_scope", type_="check")
        batch.drop_constraint("ck_correlation_run_reason", type_="check")
        batch.create_check_constraint(
            "ck_correlation_run_status",
            "status IN ('blocked', 'queued', 'running', 'succeeded', 'failed')",
        )
        batch.create_check_constraint(
            "ck_correlation_run_scope",
            "execution_scope IN ('contract_only', 'generated_event_correlation')",
        )
        batch.create_check_constraint(
            "ck_correlation_run_reason",
            "reason_code IN ('p4_0_runtime_disabled', 'generated_queued', "
            "'generated_lease_acquired', 'generated_completed', 'generated_failed')",
        )
        batch.add_column(sa.Column("profile_id", sa.String(128), nullable=True))
        batch.add_column(sa.Column("profile_version", sa.String(71), nullable=True))
        batch.add_column(sa.Column("result_digest", sa.String(71), nullable=True))
        batch.add_column(sa.Column("replay_binding", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("input_count", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("accepted_count", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("duplicate_count", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("rejected_count", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch.add_column(sa.Column("lease_owner", sa.String(128), nullable=True))
        batch.add_column(
            sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True)
        )
        batch.create_check_constraint(
            "ck_correlation_run_attempts",
            "attempt_count >= 0 AND attempt_count <= 3",
        )

    with op.batch_alter_table("correlation_hypotheses") as batch:
        batch.drop_constraint("ck_correlation_hypothesis_state", type_="check")
        batch.create_check_constraint(
            "ck_correlation_hypothesis_state",
            "state IN ('proposed', 'abstained', 'expired', 'superseded', 'retracted', 'corrected')",
        )
        batch.add_column(sa.Column("profile_id", sa.String(128), nullable=True))
        batch.add_column(sa.Column("profile_version", sa.String(71), nullable=True))
        batch.add_column(sa.Column("partition_digest", sa.String(71), nullable=True))
        batch.add_column(sa.Column("revision", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("abstention_reason", sa.String(64), nullable=True))
        batch.add_column(sa.Column("graph_digest", sa.String(71), nullable=True))
        batch.add_column(sa.Column("arbitration_digest", sa.String(71), nullable=True))
        batch.add_column(sa.Column("projection", sa.JSON(), nullable=True))

    with op.batch_alter_table("hypothesis_evidence_refs") as batch:
        batch.alter_column(
            "source_ref",
            existing_type=sa.String(36),
            type_=sa.String(160),
            existing_nullable=False,
        )

    op.create_table(
        "correlation_event_receipts",
        sa.Column("receipt_id", sa.String(37), primary_key=True),
        sa.Column("run_id", sa.String(37), sa.ForeignKey("correlation_runs.run_id", ondelete="CASCADE"), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("event_id", sa.String(160), nullable=False),
        sa.Column("event_digest", sa.String(71), nullable=False),
        sa.Column("partition_digest", sa.String(71), nullable=True),
        sa.Column("disposition", sa.String(24), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("receipt_sequence", sa.BigInteger(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint(
            "disposition IN ('accepted', 'duplicate', 'conflict', 'late_accepted', "
            "'late_rejected', 'gap_accepted', 'future_rejected', 'policy_rejected', "
            "'capacity_rejected')",
            name="ck_correlation_receipt_disposition",
        ),
        sa.CheckConstraint("receipt_sequence >= 0", name="ck_correlation_receipt_sequence"),
        sa.CheckConstraint("generated_only = true", name="ck_correlation_receipt_generated"),
        sa.UniqueConstraint("run_id", "receipt_sequence", name="uq_correlation_receipt_run_sequence"),
    )
    op.create_index(
        "ix_correlation_receipt_scope",
        "correlation_event_receipts",
        ["department", "run_id", "receipt_sequence"],
    )

    op.create_table(
        "correlation_partition_checkpoints",
        sa.Column("checkpoint_id", sa.String(36), primary_key=True),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("profile_id", sa.String(128), nullable=False),
        sa.Column("partition_digest", sa.String(71), nullable=False),
        sa.Column("receipt_sequence", sa.BigInteger(), nullable=False),
        sa.Column("last_source_sequence", sa.BigInteger(), nullable=True),
        sa.Column("maximum_occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("watermark_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active_window_count", sa.Integer(), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_id >= 1", name="ck_correlation_checkpoint_version"),
        sa.CheckConstraint("receipt_sequence >= 0", name="ck_correlation_checkpoint_sequence"),
        sa.CheckConstraint("active_window_count >= 0 AND active_window_count <= 256", name="ck_correlation_checkpoint_windows"),
        sa.CheckConstraint("generated_only = true", name="ck_correlation_checkpoint_generated"),
        sa.UniqueConstraint("department", "profile_id", "partition_digest", name="uq_correlation_checkpoint_partition"),
    )
    op.create_index(
        "ix_correlation_checkpoint_scope",
        "correlation_partition_checkpoints",
        ["department", "profile_id", "watermark_at"],
    )

    op.create_table(
        "correlation_window_events",
        sa.Column("membership_id", sa.String(37), primary_key=True),
        sa.Column("run_id", sa.String(37), sa.ForeignKey("correlation_runs.run_id", ondelete="CASCADE"), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("window_id", sa.String(37), nullable=False),
        sa.Column("event_id", sa.String(160), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("window_payload", sa.JSON(), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("sequence >= 0", name="ck_correlation_window_event_sequence"),
        sa.CheckConstraint("generated_only = true", name="ck_correlation_window_event_generated"),
        sa.UniqueConstraint("window_id", "event_id", name="uq_correlation_window_event"),
    )
    op.create_index(
        "ix_correlation_window_event_scope",
        "correlation_window_events",
        ["department", "window_id", "sequence"],
    )

    op.create_table(
        "correlation_lane_results",
        sa.Column("lane_result_id", sa.String(37), primary_key=True),
        sa.Column("hypothesis_id", sa.String(36), sa.ForeignKey("correlation_hypotheses.hypothesis_id", ondelete="CASCADE"), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("lane", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("lineage_digest", sa.String(71), nullable=False),
        sa.Column("generated_fixture_result", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("operational", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint(
            "lane IN ('deterministic_cpu', 'probabilistic', 'temporal_graph', "
            "'model_first_shadow', 'uncertainty_ensemble')",
            name="ck_correlation_lane_name",
        ),
        sa.CheckConstraint("operational = false", name="ck_correlation_lane_nonoperational"),
        sa.CheckConstraint("generated_only = true", name="ck_correlation_lane_generated"),
        sa.UniqueConstraint("hypothesis_id", "lane", name="uq_correlation_lane_hypothesis"),
    )
    op.create_index(
        "ix_correlation_lane_scope",
        "correlation_lane_results",
        ["department", "hypothesis_id", "lane"],
    )

    op.create_table(
        "correlation_hypothesis_revisions",
        sa.Column("revision_id", sa.String(37), primary_key=True),
        sa.Column("hypothesis_id", sa.String(36), sa.ForeignKey("correlation_hypotheses.hypothesis_id", ondelete="CASCADE"), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("previous_state", sa.String(16), nullable=False),
        sa.Column("new_state", sa.String(16), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("snapshot_digest", sa.String(71), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("operational", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("revision >= 1", name="ck_correlation_revision_positive"),
        sa.CheckConstraint("operational = false", name="ck_correlation_revision_nonoperational"),
        sa.CheckConstraint("generated_only = true", name="ck_correlation_revision_generated"),
        sa.UniqueConstraint("hypothesis_id", "revision", name="uq_correlation_hypothesis_revision"),
    )
    op.create_index(
        "ix_correlation_revision_scope",
        "correlation_hypothesis_revisions",
        ["department", "hypothesis_id", "revision"],
    )

    if op.get_bind().dialect.name == "postgresql":
        for table in NEW_TABLES:
            _enable_rls(table)


def downgrade() -> None:
    for table in reversed(NEW_TABLES):
        op.drop_table(table)

    with op.batch_alter_table("hypothesis_evidence_refs") as batch:
        batch.alter_column(
            "source_ref",
            existing_type=sa.String(160),
            type_=sa.String(36),
            existing_nullable=False,
        )

    with op.batch_alter_table("correlation_hypotheses") as batch:
        batch.drop_constraint("ck_correlation_hypothesis_state", type_="check")
        batch.create_check_constraint(
            "ck_correlation_hypothesis_state",
            "state IN ('proposed', 'abstained', 'retracted', 'corrected')",
        )
        for column in (
            "projection",
            "arbitration_digest",
            "graph_digest",
            "abstention_reason",
            "revision",
            "partition_digest",
            "profile_version",
            "profile_id",
        ):
            batch.drop_column(column)

    with op.batch_alter_table("correlation_runs") as batch:
        batch.drop_constraint("ck_correlation_run_attempts", type_="check")
        batch.drop_constraint("ck_correlation_run_status", type_="check")
        batch.drop_constraint("ck_correlation_run_scope", type_="check")
        batch.drop_constraint("ck_correlation_run_reason", type_="check")
        batch.create_check_constraint("ck_correlation_run_status", "status = 'blocked'")
        batch.create_check_constraint("ck_correlation_run_scope", "execution_scope = 'contract_only'")
        batch.create_check_constraint("ck_correlation_run_reason", "reason_code = 'p4_0_runtime_disabled'")
        for column in (
            "lease_until",
            "lease_owner",
            "attempt_count",
            "rejected_count",
            "duplicate_count",
            "accepted_count",
            "input_count",
            "result_digest",
            "replay_binding",
            "profile_version",
            "profile_id",
        ):
            batch.drop_column(column)
