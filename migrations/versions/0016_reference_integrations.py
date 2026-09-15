"""Add the generated-only Phase 4.4 reference integration stores.

Revision ID: 0016_reference_integrations
Revises: 0015_alert_lifecycle_orchestration
Create Date: 2026-09-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0016_reference_integrations"
down_revision: str | None = "0015_alert_lifecycle_orchestration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_TABLES = (
    "reference_provider_versions",
    "reference_catalogue_snapshots",
    "reference_catalogue_records",
    "reference_query_jobs",
    "reference_query_attempts",
    "reference_candidate_sets",
    "reference_review_handoffs",
    "reference_control_revisions",
    "reference_circuit_states",
    "reference_integration_outbox",
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


def _generated_flags(*, operational: bool = False) -> tuple[sa.Column, ...]:
    columns: tuple[sa.Column, ...] = (
        sa.Column("generated_only", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    if operational:
        columns += (
            sa.Column("operational", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    return columns


def upgrade() -> None:
    op.create_table(
        "reference_provider_versions",
        sa.Column("provider_version_id", sa.String(37), primary_key=True),
        sa.Column("provider_id", sa.String(37), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("provider_key", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("manifest_digest", sa.String(71), nullable=False, unique=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        *_generated_flags(operational=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('validated_generated', 'approved_disabled', 'suspended', "
            "'revoked', 'retired')",
            name="ck_reference_provider_version_status",
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_provider_version_generated"
        ),
        sa.CheckConstraint(
            "operational = false", name="ck_reference_provider_version_nonoperational"
        ),
        sa.UniqueConstraint(
            "department", "provider_id", "version", name="uq_reference_provider_version"
        ),
    )
    op.create_index(
        "ix_reference_provider_version_scope",
        "reference_provider_versions",
        ["department", "status", "updated_at"],
    )

    op.create_table(
        "reference_catalogue_snapshots",
        sa.Column("snapshot_id", sa.String(37), primary_key=True),
        sa.Column(
            "provider_version_id",
            sa.String(37),
            sa.ForeignKey(
                "reference_provider_versions.provider_version_id", ondelete="RESTRICT"
            ),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("fingerprint", sa.String(71), nullable=False),
        sa.Column("completeness", sa.String(16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stale_at", sa.DateTime(timezone=True), nullable=False),
        *_generated_flags(),
        sa.Column(
            "raw_response_retained",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.CheckConstraint(
            "completeness IN ('complete', 'partial')",
            name="ck_reference_catalogue_completeness",
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_catalogue_generated"
        ),
        sa.CheckConstraint(
            "raw_response_retained = false", name="ck_reference_catalogue_no_raw"
        ),
        sa.UniqueConstraint(
            "provider_version_id",
            "fingerprint",
            name="uq_reference_catalogue_fingerprint",
        ),
    )
    op.create_index(
        "ix_reference_catalogue_scope",
        "reference_catalogue_snapshots",
        ["department", "provider_version_id", "last_observed_at"],
    )

    op.create_table(
        "reference_catalogue_records",
        sa.Column("row_id", sa.String(37), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(37),
            sa.ForeignKey(
                "reference_catalogue_snapshots.snapshot_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("record_id", sa.String(37), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("record_digest", sa.String(71), nullable=False),
        sa.Column("fields", sa.JSON(), nullable=False),
        *_generated_flags(),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_catalogue_record_generated"
        ),
        sa.UniqueConstraint(
            "snapshot_id", "record_id", name="uq_reference_catalogue_record"
        ),
    )
    op.create_index(
        "ix_reference_catalogue_record_scope",
        "reference_catalogue_records",
        ["department", "snapshot_id"],
    )

    op.create_table(
        "reference_query_jobs",
        sa.Column("job_id", sa.String(37), primary_key=True),
        sa.Column("query_id", sa.String(36), nullable=False),
        sa.Column(
            "provider_version_id",
            sa.String(37),
            sa.ForeignKey(
                "reference_provider_versions.provider_version_id", ondelete="RESTRICT"
            ),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(128), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("plan_digest", sa.String(71), nullable=False),
        sa.Column("semantic_key", sa.String(71), nullable=False),
        sa.Column("delivery_key", sa.String(71), nullable=False),
        sa.Column("result_digest", sa.String(71), nullable=True),
        sa.Column("intent_payload", sa.JSON(), nullable=False),
        sa.Column("plan_payload", sa.JSON(), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        *_generated_flags(operational=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('queued', 'leased', 'succeeded', 'failed', 'cancelled', "
            "'quarantined')",
            name="ck_reference_query_job_state",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0 AND attempt_count <= 3",
            name="ck_reference_query_job_attempts",
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_query_job_generated"
        ),
        sa.CheckConstraint(
            "operational = false", name="ck_reference_query_job_nonoperational"
        ),
        sa.UniqueConstraint("department", "query_id", name="uq_reference_query_id"),
        sa.UniqueConstraint(
            "department", "semantic_key", name="uq_reference_query_semantic"
        ),
        sa.UniqueConstraint(
            "department", "delivery_key", name="uq_reference_query_delivery"
        ),
    )
    op.create_index(
        "ix_reference_query_job_due",
        "reference_query_jobs",
        ["department", "state", "created_at"],
    )

    op.create_table(
        "reference_query_attempts",
        sa.Column("attempt_id", sa.String(37), primary_key=True),
        sa.Column(
            "job_id",
            sa.String(37),
            sa.ForeignKey("reference_query_jobs.job_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("normalized_digest", sa.String(71), nullable=True),
        sa.Column(
            "raw_response_retained",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        *_generated_flags(),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "outcome IN ('succeeded', 'transient_failure', 'permanent_failure', "
            "'revoked', 'stale')",
            name="ck_reference_query_attempt_outcome",
        ),
        sa.CheckConstraint(
            "raw_response_retained = false", name="ck_reference_query_attempt_no_raw"
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_query_attempt_generated"
        ),
    )
    op.create_index(
        "ix_reference_query_attempt_scope",
        "reference_query_attempts",
        ["department", "job_id", "recorded_at"],
    )

    op.create_table(
        "reference_candidate_sets",
        sa.Column("candidate_set_id", sa.String(37), primary_key=True),
        sa.Column("query_id", sa.String(36), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("candidate_set_digest", sa.String(71), nullable=False),
        sa.Column("identity_state", sa.String(32), nullable=False),
        sa.Column(
            "mandatory_review", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        *_generated_flags(operational=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "identity_state = 'not_established'", name="ck_reference_candidate_identity"
        ),
        sa.CheckConstraint(
            "mandatory_review = true", name="ck_reference_candidate_review"
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_candidate_generated"
        ),
        sa.CheckConstraint(
            "operational = false", name="ck_reference_candidate_nonoperational"
        ),
    )
    op.create_index(
        "ix_reference_candidate_scope",
        "reference_candidate_sets",
        ["department", "query_id", "created_at"],
    )

    op.create_table(
        "reference_review_handoffs",
        sa.Column("handoff_id", sa.String(37), primary_key=True),
        sa.Column(
            "candidate_set_id",
            sa.String(37),
            sa.ForeignKey(
                "reference_candidate_sets.candidate_set_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("authority_class", sa.String(32), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("evidence_digest", sa.String(71), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        *_generated_flags(operational=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "authority_class = 'mandatory_review'", name="ck_reference_review_authority"
        ),
        sa.CheckConstraint("state = 'pending_review'", name="ck_reference_review_state"),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_review_generated"
        ),
        sa.CheckConstraint(
            "operational = false", name="ck_reference_review_nonoperational"
        ),
    )
    op.create_index(
        "ix_reference_review_scope",
        "reference_review_handoffs",
        ["department", "created_at"],
    )

    op.create_table(
        "reference_control_revisions",
        sa.Column("revision_id", sa.String(37), primary_key=True),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("scope", sa.String(32), nullable=False),
        sa.Column("scope_key", sa.String(128), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.String(160), nullable=False),
        sa.Column("reason", sa.String(2000), nullable=False),
        *_generated_flags(),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('enabled_generated', 'suspended', 'revoked')",
            name="ck_reference_control_state",
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_control_generated"
        ),
        sa.UniqueConstraint(
            "department",
            "scope",
            "scope_key",
            "version",
            name="uq_reference_control_version",
        ),
    )
    op.create_index(
        "ix_reference_control_scope",
        "reference_control_revisions",
        ["department", "scope", "scope_key", "version"],
    )

    op.create_table(
        "reference_circuit_states",
        sa.Column("circuit_id", sa.String(37), primary_key=True),
        sa.Column(
            "provider_version_id",
            sa.String(37),
            sa.ForeignKey(
                "reference_provider_versions.provider_version_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
        *_generated_flags(),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('closed', 'open', 'half_open', 'revoked')",
            name="ck_reference_circuit_state",
        ),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_circuit_generated"
        ),
        sa.UniqueConstraint(
            "department",
            "provider_version_id",
            name="uq_reference_circuit_provider",
        ),
    )
    op.create_index(
        "ix_reference_circuit_scope",
        "reference_circuit_states",
        ["department", "state", "updated_at"],
    )

    op.create_table(
        "reference_integration_outbox",
        sa.Column("event_id", sa.String(37), primary_key=True),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("aggregate_id", sa.String(128), nullable=False),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        *_generated_flags(operational=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "generated_only = true", name="ck_reference_outbox_generated"
        ),
        sa.CheckConstraint(
            "operational = false", name="ck_reference_outbox_nonoperational"
        ),
    )
    op.create_index(
        "ix_reference_outbox_pending",
        "reference_integration_outbox",
        ["department", "published_at", "occurred_at"],
    )

    if op.get_bind().dialect.name == "postgresql":
        for table in NEW_TABLES:
            _enable_rls(table)


def downgrade() -> None:
    for table in reversed(NEW_TABLES):
        op.drop_table(table)
