"""Add generated-only Phase 4.0 intelligence control-plane stores.

Revision ID: 0012_intelligence_control_plane
Revises: 0012_merge_camera_gis
Create Date: 2026-09-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0012_intelligence_control_plane"
down_revision: str | None = "0012_merge_camera_gis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _scope_columns() -> list[sa.Column]:
    return [sa.Column("department", sa.String(120), nullable=False)]


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
    op.create_table(
        "intelligence_rules",
        sa.Column("rule_record_id", sa.String(37), primary_key=True),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        *_scope_columns(),
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
        sa.Column("rule_id", sa.String(38), nullable=False, unique=True),
        sa.Column("rule_key", sa.String(128), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("authority_class", sa.String(32), nullable=False),
        sa.Column("operational", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("canonical_json", sa.Text(), nullable=False),
        sa.Column("configuration_digest", sa.String(71), nullable=False),
        sa.Column("static_cost", sa.Integer(), nullable=False),
        sa.Column("intended_use", sa.Text(), nullable=False),
        sa.Column("policy_version", sa.String(71), nullable=False),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.Column("owner_id", sa.String(160), nullable=False),
        sa.Column("last_change_reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_id >= 1", name="ck_intelligence_rule_version"),
        sa.CheckConstraint("rule_version >= 1", name="ck_intelligence_rule_rule_version"),
        sa.CheckConstraint(
            "status IN ('draft', 'validated', 'retired')",
            name="ck_intelligence_rule_status",
        ),
        sa.CheckConstraint(
            "authority_class = 'mandatory_review'",
            name="ck_intelligence_rule_authority",
        ),
        sa.CheckConstraint(
            "operational = false", name="ck_intelligence_rule_nonoperational"
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_intelligence_rule_generated"
        ),
        sa.CheckConstraint(
            "static_cost >= 1 AND static_cost <= 320",
            name="ck_intelligence_rule_static_cost",
        ),
        sa.CheckConstraint(
            "length(configuration_digest) = 71",
            name="ck_intelligence_rule_digest",
        ),
        sa.UniqueConstraint(
            "department",
            "rule_key",
            "rule_version",
            name="uq_intelligence_rule_department_key_version",
        ),
    )
    op.create_index(
        "ix_intelligence_rule_scope",
        "intelligence_rules",
        ["department", "stream_id", "status"],
    )

    op.create_table(
        "correlation_runs",
        sa.Column("run_id", sa.String(37), primary_key=True),
        *_scope_columns(),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("execution_scope", sa.String(32), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("watermark_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status = 'blocked'", name="ck_correlation_run_status"),
        sa.CheckConstraint(
            "execution_scope = 'contract_only'", name="ck_correlation_run_scope"
        ),
        sa.CheckConstraint(
            "reason_code = 'p4_0_runtime_disabled'", name="ck_correlation_run_reason"
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_correlation_run_generated"
        ),
    )
    op.create_index(
        "ix_correlation_run_scope", "correlation_runs", ["department", "created_at"]
    )

    op.create_table(
        "correlation_hypotheses",
        sa.Column("hypothesis_id", sa.String(36), primary_key=True),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        *_scope_columns(),
        sa.Column(
            "run_id",
            sa.String(37),
            sa.ForeignKey("correlation_runs.run_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("hypothesis_key", sa.String(71), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("subject_kind", sa.String(32), nullable=False),
        sa.Column("authority_class", sa.String(32), nullable=False),
        sa.Column("operational", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("uncertainty", sa.Float(), nullable=False),
        sa.Column("abstained", sa.Boolean(), nullable=False),
        sa.Column("contradiction_count", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("canonical_json", sa.Text(), nullable=False),
        sa.Column("content_digest", sa.String(71), nullable=False),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_id >= 1", name="ck_correlation_hypothesis_version"),
        sa.CheckConstraint(
            "state IN ('proposed', 'abstained', 'retracted', 'corrected')",
            name="ck_correlation_hypothesis_state",
        ),
        sa.CheckConstraint(
            "authority_class = 'mandatory_review'",
            name="ck_correlation_hypothesis_authority",
        ),
        sa.CheckConstraint(
            "operational = false", name="ck_correlation_hypothesis_nonoperational"
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_correlation_hypothesis_generated"
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1 AND uncertainty >= 0 AND uncertainty <= 1",
            name="ck_correlation_hypothesis_scores",
        ),
        sa.CheckConstraint(
            "contradiction_count >= 0 AND contradiction_count <= 256",
            name="ck_correlation_hypothesis_contradictions",
        ),
        sa.UniqueConstraint(
            "department", "hypothesis_key", name="uq_correlation_hypothesis_key"
        ),
    )
    op.create_index(
        "ix_correlation_hypothesis_scope",
        "correlation_hypotheses",
        ["department", "state", "created_at"],
    )

    op.create_table(
        "hypothesis_evidence_refs",
        sa.Column("evidence_id", sa.String(37), primary_key=True),
        sa.Column(
            "hypothesis_id",
            sa.String(36),
            sa.ForeignKey("correlation_hypotheses.hypothesis_id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_scope_columns(),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_ref", sa.String(36), nullable=False),
        sa.Column("source_digest", sa.String(71), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('supports', 'contradicts', 'missing', 'stale', 'supersedes', 'retracts')",
            name="ck_hypothesis_evidence_role",
        ),
        sa.CheckConstraint("sequence >= 0", name="ck_hypothesis_evidence_sequence"),
        sa.UniqueConstraint(
            "hypothesis_id", "evidence_id", name="uq_hypothesis_evidence_reference"
        ),
    )
    op.create_index(
        "ix_hypothesis_evidence_scope",
        "hypothesis_evidence_refs",
        ["department", "hypothesis_id", "sequence"],
    )

    op.create_table(
        "reference_providers",
        sa.Column("provider_id", sa.String(37), primary_key=True),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        *_scope_columns(),
        sa.Column("provider_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("provider_kind", sa.String(32), nullable=False),
        sa.Column("transport_state", sa.String(16), nullable=False),
        sa.Column("credential_state", sa.String(16), nullable=False),
        sa.Column("policy_ref", sa.String(36), nullable=False),
        sa.Column("destination_policy_ref", sa.String(36), nullable=False),
        sa.Column("allowed_fields", sa.JSON(), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("configuration_digest", sa.String(71), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("owner_id", sa.String(160), nullable=False),
        sa.Column("last_change_reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_id >= 1", name="ck_reference_provider_version"),
        sa.CheckConstraint("status = 'disabled'", name="ck_reference_provider_status"),
        sa.CheckConstraint("enabled = false", name="ck_reference_provider_disabled"),
        sa.CheckConstraint(
            "provider_kind = 'generated_fixture'", name="ck_reference_provider_kind"
        ),
        sa.CheckConstraint(
            "transport_state = 'absent'", name="ck_reference_provider_transport"
        ),
        sa.CheckConstraint(
            "credential_state = 'none'", name="ck_reference_provider_credentials"
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_provider_generated"
        ),
        sa.UniqueConstraint(
            "department", "provider_key", name="uq_reference_provider_department_key"
        ),
    )
    op.create_index(
        "ix_reference_provider_scope", "reference_providers", ["department", "status"]
    )

    op.create_table(
        "reference_queries",
        sa.Column("query_id", sa.String(36), primary_key=True),
        sa.Column(
            "provider_id",
            sa.String(37),
            sa.ForeignKey("reference_providers.provider_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *_scope_columns(),
        sa.Column("purpose_code", sa.String(64), nullable=False),
        sa.Column("requested_fields", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("requested_by", sa.String(160), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status = 'blocked'", name="ck_reference_query_status"),
        sa.CheckConstraint(
            "reason_code = 'provider_disabled'", name="ck_reference_query_reason"
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_query_generated"
        ),
    )
    op.create_index(
        "ix_reference_query_scope", "reference_queries", ["department", "requested_at"]
    )

    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.String(36), primary_key=True),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        *_scope_columns(),
        sa.Column(
            "hypothesis_id",
            sa.String(36),
            sa.ForeignKey("correlation_hypotheses.hypothesis_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("dedupe_key", sa.String(71), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("authority_class", sa.String(32), nullable=False),
        sa.Column("operational", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("disposition", sa.String(16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("content_digest", sa.String(71), nullable=False),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_id >= 1", name="ck_alert_version"),
        sa.CheckConstraint("state = 'proposed'", name="ck_alert_state"),
        sa.CheckConstraint(
            "authority_class = 'mandatory_review'", name="ck_alert_authority"
        ),
        sa.CheckConstraint("operational = false", name="ck_alert_nonoperational"),
        sa.CheckConstraint("generated_only = true", name="ck_alert_generated"),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_alert_confidence"
        ),
        sa.UniqueConstraint("department", "dedupe_key", name="uq_alert_dedupe_key"),
    )
    op.create_index("ix_alert_scope", "alerts", ["department", "state", "created_at"])

    op.create_table(
        "alert_revisions",
        sa.Column("revision_id", sa.String(37), primary_key=True),
        sa.Column(
            "alert_id",
            sa.String(36),
            sa.ForeignKey("alerts.alert_id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_scope_columns(),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("previous_state", sa.String(16), nullable=False),
        sa.Column("new_state", sa.String(16), nullable=False),
        sa.Column("actor_id", sa.String(160), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("content_digest", sa.String(71), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision >= 1", name="ck_alert_revision_positive"),
        sa.UniqueConstraint("alert_id", "revision", name="uq_alert_revision"),
    )
    op.create_index(
        "ix_alert_revision_scope",
        "alert_revisions",
        ["department", "alert_id", "recorded_at"],
    )

    op.create_table(
        "investigation_timelines",
        sa.Column("timeline_id", sa.String(36), primary_key=True),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        *_scope_columns(),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("title_code", sa.String(64), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("owner_id", sa.String(160), nullable=False),
        sa.Column("last_change_reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_id >= 1", name="ck_investigation_timeline_version"),
        sa.CheckConstraint(
            "status IN ('draft', 'closed')", name="ck_investigation_timeline_status"
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_investigation_timeline_generated"
        ),
    )
    op.create_index(
        "ix_investigation_timeline_scope",
        "investigation_timelines",
        ["department", "status", "updated_at"],
    )

    op.create_table(
        "timeline_entries",
        sa.Column("entry_id", sa.String(37), primary_key=True),
        sa.Column(
            "timeline_id",
            sa.String(36),
            sa.ForeignKey("investigation_timelines.timeline_id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_scope_columns(),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("entry_type", sa.String(32), nullable=False),
        sa.Column("source_ref", sa.String(36), nullable=False),
        sa.Column("source_digest", sa.String(71), nullable=False),
        sa.Column("summary_code", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("content_digest", sa.String(71), nullable=False),
        sa.Column("actor_id", sa.String(160), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("retention_class", sa.String(64), nullable=False),
        sa.CheckConstraint("sequence >= 1", name="ck_timeline_entry_sequence"),
        sa.CheckConstraint(
            "entry_type IN ('source_fact', 'system_hypothesis', "
            "'operator_observation', 'review_decision', 'correction')",
            name="ck_timeline_entry_type",
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_timeline_entry_generated"
        ),
        sa.UniqueConstraint("timeline_id", "sequence", name="uq_timeline_entry_sequence"),
    )
    op.create_index(
        "ix_timeline_entry_scope",
        "timeline_entries",
        ["department", "timeline_id", "sequence"],
    )

    if op.get_bind().dialect.name == "postgresql":
        for table in (
            "intelligence_rules",
            "correlation_runs",
            "correlation_hypotheses",
            "hypothesis_evidence_refs",
            "reference_providers",
            "reference_queries",
            "alerts",
            "alert_revisions",
            "investigation_timelines",
            "timeline_entries",
        ):
            _enable_rls(table)


def downgrade() -> None:
    op.drop_table("timeline_entries")
    op.drop_table("investigation_timelines")
    op.drop_table("alert_revisions")
    op.drop_table("alerts")
    op.drop_table("reference_queries")
    op.drop_table("reference_providers")
    op.drop_table("hypothesis_evidence_refs")
    op.drop_table("correlation_hypotheses")
    op.drop_table("correlation_runs")
    op.drop_table("intelligence_rules")
