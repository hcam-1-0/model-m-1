"""Add the generated-only Phase 4.2 rule authoring and evaluation stores.

Revision ID: 0014_rule_authoring_evaluation
Revises: 0013_correlation_foundation
Create Date: 2026-09-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0014_rule_authoring_evaluation"
down_revision: str | None = "0013_correlation_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_TABLES = (
    "intelligence_rule_compilations",
    "intelligence_rule_scope_members",
    "intelligence_rule_schedules",
    "intelligence_rule_lifecycle_events",
    "intelligence_rule_state_checkpoints",
    "intelligence_rule_evaluation_revisions",
    "intelligence_rule_shadow_comparisons",
)
LEGACY_NAMING_CONVENTION = {
    "uq": "uq_%(table_name)s_%(column_0_name)s",
}


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
    dialect = op.get_bind().dialect.name
    legacy_rule_id_unique = (
        "intelligence_rules_rule_id_key"
        if dialect == "postgresql"
        else "uq_intelligence_rules_rule_id"
    )
    with op.batch_alter_table(
        "intelligence_rules",
        naming_convention=LEGACY_NAMING_CONVENTION,
    ) as batch:
        batch.drop_constraint(legacy_rule_id_unique, type_="unique")
        batch.drop_constraint("ck_intelligence_rule_status", type_="check")
        batch.create_check_constraint(
            "ck_intelligence_rule_status",
            "status IN ('draft', 'validated', 'approved', 'shadow', 'suspended', 'retired')",
        )
        batch.add_column(sa.Column("authoring_digest", sa.String(71), nullable=True))
        batch.add_column(sa.Column("semantic_digest", sa.String(71), nullable=True))
        batch.add_column(sa.Column("compilation_id", sa.String(37), nullable=True))
        batch.add_column(sa.Column("schedule_digest", sa.String(71), nullable=True))

    op.create_table(
        "intelligence_rule_compilations",
        sa.Column("compilation_id", sa.String(37), primary_key=True),
        sa.Column(
            "rule_record_id",
            sa.String(37),
            sa.ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("rule_key", sa.String(128), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("authoring_digest", sa.String(71), nullable=False),
        sa.Column("semantic_digest", sa.String(71), nullable=False),
        sa.Column("ast_digest", sa.String(71), nullable=False),
        sa.Column("schedule_digest", sa.String(71), nullable=True),
        sa.Column("canonical_ast", sa.JSON(), nullable=False),
        sa.Column("canonical_bytes", sa.Text(), nullable=False),
        sa.Column("cel_compilations", sa.JSON(), nullable=False),
        sa.Column("diagnostic_map", sa.JSON(), nullable=False),
        sa.Column("static_cost", sa.Integer(), nullable=False),
        sa.Column(
            "generated_only", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "operational", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "rule_version >= 1", name="ck_rule_compilation_rule_version"
        ),
        sa.CheckConstraint("status = 'compiled'", name="ck_rule_compilation_status"),
        sa.CheckConstraint(
            "generated_only = true", name="ck_rule_compilation_generated"
        ),
        sa.CheckConstraint(
            "operational = false", name="ck_rule_compilation_nonoperational"
        ),
        sa.CheckConstraint(
            "static_cost >= 1 AND static_cost <= 10000", name="ck_rule_compilation_cost"
        ),
        sa.UniqueConstraint(
            "rule_record_id", "ast_digest", name="uq_rule_compilation_record_ast"
        ),
    )
    op.create_index(
        "ix_rule_compilation_scope",
        "intelligence_rule_compilations",
        ["department", "rule_record_id", "created_at"],
    )

    op.create_table(
        "intelligence_rule_scope_members",
        sa.Column("scope_member_id", sa.String(37), primary_key=True),
        sa.Column(
            "rule_record_id",
            sa.String(37),
            sa.ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column(
            "stream_id",
            sa.String(64),
            sa.ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "camera_id",
            sa.String(160),
            sa.ForeignKey("cameras.camera_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "generated_only", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("generated_only = true", name="ck_rule_scope_generated"),
        sa.UniqueConstraint("rule_record_id", "stream_id", name="uq_rule_scope_stream"),
    )
    op.create_index(
        "ix_rule_scope_member_scope",
        "intelligence_rule_scope_members",
        ["department", "rule_record_id"],
    )

    op.create_table(
        "intelligence_rule_schedules",
        sa.Column("schedule_record_id", sa.String(37), primary_key=True),
        sa.Column(
            "rule_record_id",
            sa.String(37),
            sa.ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("schedule_digest", sa.String(71), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column(
            "generated_only", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("generated_only = true", name="ck_rule_schedule_generated"),
        sa.UniqueConstraint("rule_record_id", name="uq_rule_schedule_record"),
    )
    op.create_index(
        "ix_rule_schedule_scope",
        "intelligence_rule_schedules",
        ["department", "rule_record_id"],
    )

    op.create_table(
        "intelligence_rule_lifecycle_events",
        sa.Column("event_id", sa.String(37), primary_key=True),
        sa.Column(
            "rule_record_id",
            sa.String(37),
            sa.ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("from_status", sa.String(16), nullable=False),
        sa.Column("to_status", sa.String(16), nullable=False),
        sa.Column("actor_id", sa.String(160), nullable=False),
        sa.Column("reason_code", sa.String(128), nullable=False),
        sa.Column("compilation_digest", sa.String(71), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "generated_only", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "operational", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.CheckConstraint(
            "from_status IN ('draft', 'validated', 'approved', 'shadow', 'suspended', 'retired')",
            name="ck_rule_lifecycle_from_status",
        ),
        sa.CheckConstraint(
            "to_status IN ('draft', 'validated', 'approved', 'shadow', 'suspended', 'retired')",
            name="ck_rule_lifecycle_to_status",
        ),
        sa.CheckConstraint("generated_only = true", name="ck_rule_lifecycle_generated"),
        sa.CheckConstraint(
            "operational = false", name="ck_rule_lifecycle_nonoperational"
        ),
    )
    op.create_index(
        "ix_rule_lifecycle_scope",
        "intelligence_rule_lifecycle_events",
        ["department", "rule_record_id", "occurred_at"],
    )

    op.create_table(
        "intelligence_rule_state_checkpoints",
        sa.Column("checkpoint_id", sa.String(37), primary_key=True),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "compilation_id",
            sa.String(37),
            sa.ForeignKey(
                "intelligence_rule_compilations.compilation_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("partition_digest", sa.String(71), nullable=False),
        sa.Column("watermark_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state_generation", sa.Integer(), nullable=False),
        sa.Column("active_keys", sa.Integer(), nullable=False),
        sa.Column("state_digest", sa.String(71), nullable=False),
        sa.Column("state_payload", sa.JSON(), nullable=False),
        sa.Column("closed_reason", sa.String(128), nullable=True),
        sa.Column(
            "generated_only", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_id >= 1", name="ck_rule_checkpoint_version"),
        sa.CheckConstraint(
            "state_generation >= 1", name="ck_rule_checkpoint_generation"
        ),
        sa.CheckConstraint(
            "active_keys >= 0 AND active_keys <= 16384", name="ck_rule_checkpoint_keys"
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_rule_checkpoint_generated"
        ),
        sa.UniqueConstraint(
            "compilation_id", "partition_digest", name="uq_rule_checkpoint_partition"
        ),
    )
    op.create_index(
        "ix_rule_checkpoint_scope",
        "intelligence_rule_state_checkpoints",
        ["department", "compilation_id", "watermark_at"],
    )

    op.create_table(
        "intelligence_rule_evaluation_revisions",
        sa.Column("revision_id", sa.String(37), primary_key=True),
        sa.Column("evaluation_id", sa.String(37), nullable=False),
        sa.Column(
            "rule_record_id",
            sa.String(37),
            sa.ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "compilation_id",
            sa.String(37),
            sa.ForeignKey(
                "intelligence_rule_compilations.compilation_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("partition_digest", sa.String(71), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("reason_code", sa.String(128), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("snapshot_digest", sa.String(71), nullable=False),
        sa.Column("idempotency_key", sa.String(71), nullable=False, unique=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "generated_only", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "operational", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.CheckConstraint("revision >= 1", name="ck_rule_evaluation_revision"),
        sa.CheckConstraint(
            "state IN ('pending', 'matched', 'not_matched', 'suppressed', 'abstained')",
            name="ck_rule_evaluation_state",
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_rule_evaluation_generated"
        ),
        sa.CheckConstraint(
            "operational = false", name="ck_rule_evaluation_nonoperational"
        ),
        sa.UniqueConstraint(
            "evaluation_id", "revision", name="uq_rule_evaluation_revision"
        ),
    )
    op.create_index(
        "ix_rule_evaluation_scope",
        "intelligence_rule_evaluation_revisions",
        ["department", "rule_record_id", "recorded_at"],
    )

    op.create_table(
        "intelligence_rule_shadow_comparisons",
        sa.Column("comparison_id", sa.String(37), primary_key=True),
        sa.Column(
            "rule_record_id",
            sa.String(37),
            sa.ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("candidate_compilation_id", sa.String(37), nullable=False),
        sa.Column("baseline_compilation_id", sa.String(37), nullable=False),
        sa.Column("candidate_matches", sa.Integer(), nullable=False),
        sa.Column("baseline_matches", sa.Integer(), nullable=False),
        sa.Column("disagreement_count", sa.Integer(), nullable=False),
        sa.Column("comparison_digest", sa.String(71), nullable=False),
        sa.Column(
            "generated_only", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "operational", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("candidate_matches >= 0", name="ck_rule_shadow_candidate"),
        sa.CheckConstraint("baseline_matches >= 0", name="ck_rule_shadow_baseline"),
        sa.CheckConstraint(
            "disagreement_count >= 0", name="ck_rule_shadow_disagreement"
        ),
        sa.CheckConstraint("generated_only = true", name="ck_rule_shadow_generated"),
        sa.CheckConstraint("operational = false", name="ck_rule_shadow_nonoperational"),
    )
    op.create_index(
        "ix_rule_shadow_scope",
        "intelligence_rule_shadow_comparisons",
        ["department", "rule_record_id", "created_at"],
    )

    if op.get_bind().dialect.name == "postgresql":
        for table in NEW_TABLES:
            _enable_rls(table)


def downgrade() -> None:
    for table in reversed(NEW_TABLES):
        op.drop_table(table)
    with op.batch_alter_table(
        "intelligence_rules",
        naming_convention=LEGACY_NAMING_CONVENTION,
    ) as batch:
        for column in (
            "schedule_digest",
            "compilation_id",
            "semantic_digest",
            "authoring_digest",
        ):
            batch.drop_column(column)
        batch.drop_constraint("ck_intelligence_rule_status", type_="check")
        batch.create_check_constraint(
            "ck_intelligence_rule_status",
            "status IN ('draft', 'validated', 'retired')",
        )
        batch.create_unique_constraint(
            "uq_intelligence_rules_rule_id",
            ["rule_id"],
        )
