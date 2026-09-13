"""Add the generated-only Phase 4.3 alert lifecycle stores.

Revision ID: 0015_alert_lifecycle_orchestration
Revises: 0014_rule_authoring_evaluation
Create Date: 2026-09-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0015_alert_lifecycle_orchestration"
down_revision: str | None = "0014_rule_authoring_evaluation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_TABLES = (
    "alert_command_receipts",
    "alert_lifecycle_events",
    "alert_review_quorum_policies",
    "alert_review_decisions",
    "alert_assignment_events",
    "alert_suppression_events",
    "alert_merge_relations",
    "alert_budget_policies",
    "alert_budget_counters",
    "alert_timer_intents",
    "alert_workflow_executions",
)
LEGACY_NAMING_CONVENTION = {"uq": "uq_%(table_name)s_%(column_0_name)s"}


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


def _generated_flags() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("operational", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def upgrade() -> None:
    with op.batch_alter_table("alerts", naming_convention=LEGACY_NAMING_CONVENTION) as batch:
        batch.drop_constraint("ck_alert_state", type_="check")
        batch.drop_constraint("ck_alert_authority", type_="check")
        batch.create_check_constraint(
            "ck_alert_state",
            "state IN ('proposed', 'queued_review', 'under_review', 'accepted', "
            "'rejected', 'resolved', 'corrected', 'suppressed', 'merged')",
        )
        batch.create_check_constraint(
            "ck_alert_authority",
            "authority_class IN ('mandatory_review', 'bounded_automation')",
        )
        batch.alter_column(
            "hypothesis_id",
            existing_type=sa.String(36),
            nullable=True,
        )
        batch.add_column(sa.Column("semantic_key", sa.String(71), nullable=True))
        batch.add_column(sa.Column("delivery_key", sa.String(71), nullable=True))
        batch.add_column(sa.Column("source_evaluation_id", sa.String(37), nullable=True))
        batch.add_column(sa.Column("source_evaluation_revision", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("source_evaluation_digest", sa.String(71), nullable=True))
        batch.add_column(sa.Column("incident_key", sa.String(128), nullable=True))
        batch.add_column(
            sa.Column(
                "domain",
                sa.String(32),
                nullable=False,
                server_default="police_intelligence",
            )
        )
        batch.add_column(sa.Column("certainty", sa.Float(), nullable=True))
        batch.add_column(sa.Column("chronology_confidence", sa.Float(), nullable=True))
        batch.add_column(sa.Column("assigned_to", sa.String(160), nullable=True))
        batch.add_column(sa.Column("suppression_code", sa.String(128), nullable=True))
        batch.add_column(sa.Column("merged_into", sa.String(36), nullable=True))
        batch.add_column(sa.Column("policy_digest", sa.String(71), nullable=True))
        batch.create_check_constraint(
            "ck_alert_domain", "domain IN ('police_intelligence', 'system_health')"
        )
        batch.create_check_constraint(
            "ck_alert_police_review",
            "domain != 'police_intelligence' OR authority_class = 'mandatory_review'",
        )
        batch.create_check_constraint(
            "ck_alert_certainty", "certainty IS NULL OR (certainty >= 0 AND certainty <= 1)"
        )
        batch.create_check_constraint(
            "ck_alert_chronology_confidence",
            "chronology_confidence IS NULL OR "
            "(chronology_confidence >= 0 AND chronology_confidence <= 1)",
        )
        batch.create_unique_constraint(
            "uq_alert_semantic_key", ["department", "semantic_key"]
        )
        batch.create_unique_constraint(
            "uq_alert_delivery_key", ["department", "delivery_key"]
        )

    op.create_table(
        "alert_command_receipts",
        sa.Column("receipt_id", sa.String(37), primary_key=True),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("delivery_key", sa.String(71), nullable=False),
        sa.Column("semantic_key", sa.String(71), nullable=False),
        sa.Column("occurrence_digest", sa.String(71), nullable=False),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.alert_id", ondelete="SET NULL")),
        sa.Column("disposition", sa.String(16), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "disposition IN ('accepted', 'duplicate', 'conflict')",
            name="ck_alert_command_receipt_disposition",
        ),
        sa.CheckConstraint("generated_only = true", name="ck_alert_command_receipt_generated"),
        sa.UniqueConstraint("department", "delivery_key", name="uq_alert_command_delivery"),
    )
    op.create_index("ix_alert_command_scope", "alert_command_receipts", ["department", "recorded_at"])

    op.create_table(
        "alert_lifecycle_events",
        sa.Column("event_id", sa.String(37), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("previous_state", sa.String(24), nullable=False),
        sa.Column("new_state", sa.String(24), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(160), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_digest", sa.String(71), nullable=True),
        *_generated_flags(),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("sequence >= 1", name="ck_alert_lifecycle_sequence"),
        sa.CheckConstraint("generated_only = true", name="ck_alert_lifecycle_generated"),
        sa.CheckConstraint("operational = false", name="ck_alert_lifecycle_nonoperational"),
        sa.UniqueConstraint("alert_id", "sequence", name="uq_alert_lifecycle_sequence"),
    )
    op.create_index("ix_alert_lifecycle_scope", "alert_lifecycle_events", ["department", "alert_id", "recorded_at"])

    op.create_table(
        "alert_review_quorum_policies",
        sa.Column("policy_id", sa.String(128), primary_key=True),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("policy_key", sa.String(128), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("workflow_class", sa.String(32), nullable=False),
        sa.Column("required_distinct_reviewers", sa.Integer(), nullable=False),
        sa.Column("permitted_roles", sa.JSON(), nullable=False),
        sa.Column("evidence_digest", sa.String(71), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("workflow_class IN ('ordinary', 'generated_high_impact')", name="ck_alert_quorum_workflow_class"),
        sa.CheckConstraint("required_distinct_reviewers >= 1 AND required_distinct_reviewers <= 5", name="ck_alert_quorum_bound"),
        sa.CheckConstraint("generated_only = true", name="ck_alert_quorum_generated"),
        sa.UniqueConstraint("department", "policy_key", "policy_version", name="uq_alert_quorum_version"),
    )
    op.create_index("ix_alert_quorum_scope", "alert_review_quorum_policies", ["department", "effective_at"])

    op.create_table(
        "alert_review_decisions",
        sa.Column("decision_id", sa.String(37), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", sa.String(128), sa.ForeignKey("alert_review_quorum_policies.policy_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.String(160), nullable=False),
        sa.Column("reviewer_role", sa.String(128), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("evidence_digest", sa.String(71), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("supersedes_decision_id", sa.String(37), nullable=True),
        *_generated_flags(),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("decision IN ('approve', 'deny', 'request_information', 'correct')", name="ck_alert_review_decision"),
        sa.CheckConstraint("generated_only = true", name="ck_alert_review_generated"),
        sa.CheckConstraint("operational = false", name="ck_alert_review_nonoperational"),
    )
    op.create_index("ix_alert_review_scope", "alert_review_decisions", ["department", "alert_id", "recorded_at"])

    op.create_table(
        "alert_assignment_events",
        sa.Column("assignment_id", sa.String(37), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("assignee_id", sa.String(160), nullable=False),
        sa.Column("actor_id", sa.String(160), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("generated_only = true", name="ck_alert_assignment_generated"),
    )
    op.create_index("ix_alert_assignment_scope", "alert_assignment_events", ["department", "alert_id", "recorded_at"])

    op.create_table(
        "alert_suppression_events",
        sa.Column("suppression_id", sa.String(37), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("reason_code", sa.String(128), nullable=False),
        sa.Column("collapse_key", sa.String(71), nullable=True),
        sa.Column("represented_alerts", sa.Integer(), nullable=False),
        sa.Column("suppressed_alerts", sa.Integer(), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("represented_alerts >= 1 AND suppressed_alerts >= 0", name="ck_alert_suppression_counts"),
        sa.CheckConstraint("generated_only = true", name="ck_alert_suppression_generated"),
    )
    op.create_index("ix_alert_suppression_scope", "alert_suppression_events", ["department", "alert_id", "recorded_at"])

    op.create_table(
        "alert_merge_relations",
        sa.Column("relation_id", sa.String(37), primary_key=True),
        sa.Column("source_alert_id", sa.String(36), sa.ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_alert_id", sa.String(36), sa.ForeignKey("alerts.alert_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("actor_id", sa.String(160), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("source_alert_id != target_alert_id", name="ck_alert_merge_self"),
        sa.CheckConstraint("generated_only = true", name="ck_alert_merge_generated"),
        sa.UniqueConstraint("source_alert_id", name="uq_alert_merge_source"),
    )
    op.create_index("ix_alert_merge_scope", "alert_merge_relations", ["department", "target_alert_id", "recorded_at"])

    op.create_table(
        "alert_budget_policies",
        sa.Column("policy_id", sa.String(128), primary_key=True),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("policy_key", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("limits", sa.JSON(), nullable=False),
        sa.Column("policy_digest", sa.String(71), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_alert_budget_policy_version"),
        sa.CheckConstraint("generated_only = true", name="ck_alert_budget_policy_generated"),
        sa.UniqueConstraint("department", "policy_key", "version", name="uq_alert_budget_policy_version"),
    )
    op.create_index("ix_alert_budget_policy_scope", "alert_budget_policies", ["department", "created_at"])

    op.create_table(
        "alert_budget_counters",
        sa.Column("counter_id", sa.String(37), primary_key=True),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("scope", sa.String(32), nullable=False),
        sa.Column("scope_key", sa.String(128), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_count", sa.Integer(), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("observed_count >= 0", name="ck_alert_budget_count"),
        sa.CheckConstraint("generated_only = true", name="ck_alert_budget_counter_generated"),
        sa.UniqueConstraint("department", "scope", "scope_key", "window_started_at", name="uq_alert_budget_counter_window"),
    )
    op.create_index("ix_alert_budget_counter_scope", "alert_budget_counters", ["department", "window_started_at"])

    op.create_table(
        "alert_timer_intents",
        sa.Column("timer_id", sa.String(37), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("timer_kind", sa.String(32), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(128), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_alert_version", sa.Integer(), nullable=False),
        sa.Column("payload_digest", sa.String(71), nullable=False),
        *_generated_flags(),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("state IN ('pending', 'leased', 'completed', 'failed', 'cancelled')", name="ck_alert_timer_state"),
        sa.CheckConstraint("attempt_count >= 0 AND attempt_count <= 3", name="ck_alert_timer_attempts"),
        sa.CheckConstraint("generated_only = true", name="ck_alert_timer_generated"),
        sa.CheckConstraint("operational = false", name="ck_alert_timer_nonoperational"),
        sa.UniqueConstraint("alert_id", "timer_kind", "due_at", name="uq_alert_timer_intent"),
    )
    op.create_index("ix_alert_timer_due", "alert_timer_intents", ["department", "state", "due_at"])

    op.create_table(
        "alert_workflow_executions",
        sa.Column("execution_id", sa.String(37), primary_key=True),
        sa.Column("timer_id", sa.String(37), sa.ForeignKey("alert_timer_intents.timer_id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("adapter_kind", sa.String(32), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("reason_code", sa.String(128), nullable=False),
        *_generated_flags(),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("adapter_kind IN ('local_bounded', 'generated_simulator', 'future_disabled')", name="ck_alert_workflow_adapter"),
        sa.CheckConstraint("outcome IN ('applied', 'stale', 'rejected', 'adapter_disabled')", name="ck_alert_workflow_outcome"),
        sa.CheckConstraint("generated_only = true", name="ck_alert_workflow_generated"),
        sa.CheckConstraint("operational = false", name="ck_alert_workflow_nonoperational"),
    )
    op.create_index("ix_alert_workflow_scope", "alert_workflow_executions", ["department", "timer_id", "recorded_at"])

    if op.get_bind().dialect.name == "postgresql":
        for table in NEW_TABLES:
            _enable_rls(table)


def downgrade() -> None:
    for table in reversed(NEW_TABLES):
        op.drop_table(table)
    op.execute(
        "DELETE FROM alert_revisions WHERE alert_id IN "
        "(SELECT alert_id FROM alerts WHERE source_evaluation_id IS NOT NULL)"
    )
    op.execute("DELETE FROM alerts WHERE source_evaluation_id IS NOT NULL")
    with op.batch_alter_table("alerts", naming_convention=LEGACY_NAMING_CONVENTION) as batch:
        batch.drop_constraint("uq_alert_delivery_key", type_="unique")
        batch.drop_constraint("uq_alert_semantic_key", type_="unique")
        batch.drop_constraint("ck_alert_chronology_confidence", type_="check")
        batch.drop_constraint("ck_alert_certainty", type_="check")
        batch.drop_constraint("ck_alert_police_review", type_="check")
        batch.drop_constraint("ck_alert_domain", type_="check")
        batch.drop_constraint("ck_alert_state", type_="check")
        batch.drop_constraint("ck_alert_authority", type_="check")
        for column in (
            "policy_digest",
            "merged_into",
            "suppression_code",
            "assigned_to",
            "chronology_confidence",
            "certainty",
            "domain",
            "incident_key",
            "source_evaluation_digest",
            "source_evaluation_revision",
            "source_evaluation_id",
            "delivery_key",
            "semantic_key",
        ):
            batch.drop_column(column)
        batch.create_check_constraint("ck_alert_state", "state = 'proposed'")
        batch.create_check_constraint(
            "ck_alert_authority", "authority_class = 'mandatory_review'"
        )
        batch.alter_column(
            "hypothesis_id",
            existing_type=sa.String(36),
            nullable=False,
        )
