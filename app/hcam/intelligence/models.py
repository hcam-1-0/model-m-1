from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from hcam.database import Base, UTCDateTime


def utc_now() -> datetime:
    return datetime.now(UTC)


class IntelligenceRule(Base):
    __tablename__ = "intelligence_rules"
    __table_args__ = (
        CheckConstraint("version_id >= 1", name="ck_intelligence_rule_version"),
        CheckConstraint("rule_version >= 1", name="ck_intelligence_rule_rule_version"),
        CheckConstraint(
            "status IN ('draft', 'validated', 'approved', 'shadow', 'suspended', 'retired')",
            name="ck_intelligence_rule_status",
        ),
        CheckConstraint(
            "authority_class = 'mandatory_review'",
            name="ck_intelligence_rule_authority",
        ),
        CheckConstraint(
            "operational = false", name="ck_intelligence_rule_nonoperational"
        ),
        CheckConstraint("generated_only = true", name="ck_intelligence_rule_generated"),
        CheckConstraint(
            "static_cost >= 1 AND static_cost <= 320",
            name="ck_intelligence_rule_static_cost",
        ),
        CheckConstraint(
            "length(configuration_digest) = 71",
            name="ck_intelligence_rule_digest",
        ),
        UniqueConstraint(
            "department",
            "rule_key",
            "rule_version",
            name="uq_intelligence_rule_department_key_version",
        ),
        Index("ix_intelligence_rule_scope", "department", "stream_id", "status"),
    )

    rule_record_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"), nullable=False
    )
    camera_id: Mapped[str] = mapped_column(
        ForeignKey("cameras.camera_id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[str] = mapped_column(String(38), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    authority_class: Mapped[str] = mapped_column(String(32), nullable=False)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    canonical_json: Mapped[str] = mapped_column(Text, nullable=False)
    configuration_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    static_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    intended_use: Mapped[str] = mapped_column(Text, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(71), nullable=False)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(160), nullable=False)
    last_change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    authoring_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    semantic_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    compilation_id: Mapped[str | None] = mapped_column(String(37), nullable=True)
    schedule_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}


class IntelligenceRuleCompilation(Base):
    __tablename__ = "intelligence_rule_compilations"
    __table_args__ = (
        CheckConstraint("rule_version >= 1", name="ck_rule_compilation_rule_version"),
        CheckConstraint("status = 'compiled'", name="ck_rule_compilation_status"),
        CheckConstraint("generated_only = true", name="ck_rule_compilation_generated"),
        CheckConstraint(
            "operational = false", name="ck_rule_compilation_nonoperational"
        ),
        CheckConstraint(
            "static_cost >= 1 AND static_cost <= 10000", name="ck_rule_compilation_cost"
        ),
        UniqueConstraint(
            "rule_record_id", "ast_digest", name="uq_rule_compilation_record_ast"
        ),
        Index(
            "ix_rule_compilation_scope", "department", "rule_record_id", "created_at"
        ),
    )

    compilation_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    rule_record_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="compiled")
    authoring_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    semantic_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    ast_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    schedule_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    canonical_ast: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    canonical_bytes: Mapped[str] = mapped_column(Text, nullable=False)
    cel_compilations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    diagnostic_map: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
    static_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )


class IntelligenceRuleScopeMember(Base):
    __tablename__ = "intelligence_rule_scope_members"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_rule_scope_generated"),
        UniqueConstraint("rule_record_id", "stream_id", name="uq_rule_scope_stream"),
        Index("ix_rule_scope_member_scope", "department", "rule_record_id"),
    )

    scope_member_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    rule_record_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    stream_id: Mapped[str] = mapped_column(
        ForeignKey("stream_endpoints.stream_id", ondelete="CASCADE"), nullable=False
    )
    camera_id: Mapped[str] = mapped_column(
        ForeignKey("cameras.camera_id", ondelete="CASCADE"), nullable=False
    )
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )


class IntelligenceRuleSchedule(Base):
    __tablename__ = "intelligence_rule_schedules"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_rule_schedule_generated"),
        UniqueConstraint("rule_record_id", name="uq_rule_schedule_record"),
        Index("ix_rule_schedule_scope", "department", "rule_record_id"),
    )

    schedule_record_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    rule_record_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    schedule_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )


class IntelligenceRuleLifecycleEvent(Base):
    __tablename__ = "intelligence_rule_lifecycle_events"
    __table_args__ = (
        CheckConstraint(
            "from_status IN ('draft', 'validated', 'approved', 'shadow', 'suspended', 'retired')",
            name="ck_rule_lifecycle_from_status",
        ),
        CheckConstraint(
            "to_status IN ('draft', 'validated', 'approved', 'shadow', 'suspended', 'retired')",
            name="ck_rule_lifecycle_to_status",
        ),
        CheckConstraint("generated_only = true", name="ck_rule_lifecycle_generated"),
        CheckConstraint("operational = false", name="ck_rule_lifecycle_nonoperational"),
        Index("ix_rule_lifecycle_scope", "department", "rule_record_id", "occurred_at"),
    )

    event_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    rule_record_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    from_status: Mapped[str] = mapped_column(String(16), nullable=False)
    to_status: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(128), nullable=False)
    compilation_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class IntelligenceRuleStateCheckpoint(Base):
    __tablename__ = "intelligence_rule_state_checkpoints"
    __table_args__ = (
        CheckConstraint("version_id >= 1", name="ck_rule_checkpoint_version"),
        CheckConstraint("state_generation >= 1", name="ck_rule_checkpoint_generation"),
        CheckConstraint(
            "active_keys >= 0 AND active_keys <= 16384", name="ck_rule_checkpoint_keys"
        ),
        CheckConstraint("generated_only = true", name="ck_rule_checkpoint_generated"),
        UniqueConstraint(
            "compilation_id", "partition_digest", name="uq_rule_checkpoint_partition"
        ),
        Index(
            "ix_rule_checkpoint_scope", "department", "compilation_id", "watermark_at"
        ),
    )

    checkpoint_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    compilation_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_rule_compilations.compilation_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    partition_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    watermark_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    state_generation: Mapped[int] = mapped_column(Integer, nullable=False)
    active_keys: Mapped[int] = mapped_column(Integer, nullable=False)
    state_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    state_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    closed_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}


class IntelligenceRuleEvaluationRevision(Base):
    __tablename__ = "intelligence_rule_evaluation_revisions"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_rule_evaluation_revision"),
        CheckConstraint(
            "state IN ('pending', 'matched', 'not_matched', 'suppressed', 'abstained')",
            name="ck_rule_evaluation_state",
        ),
        CheckConstraint("generated_only = true", name="ck_rule_evaluation_generated"),
        CheckConstraint(
            "operational = false", name="ck_rule_evaluation_nonoperational"
        ),
        UniqueConstraint(
            "evaluation_id", "revision", name="uq_rule_evaluation_revision"
        ),
        Index(
            "ix_rule_evaluation_scope", "department", "rule_record_id", "recorded_at"
        ),
    )

    revision_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(String(37), nullable=False)
    rule_record_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
        nullable=False,
    )
    compilation_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_rule_compilations.compilation_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    partition_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(128), nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    snapshot_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(71), nullable=False, unique=True
    )
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class IntelligenceRuleShadowComparison(Base):
    __tablename__ = "intelligence_rule_shadow_comparisons"
    __table_args__ = (
        CheckConstraint("candidate_matches >= 0", name="ck_rule_shadow_candidate"),
        CheckConstraint("baseline_matches >= 0", name="ck_rule_shadow_baseline"),
        CheckConstraint("disagreement_count >= 0", name="ck_rule_shadow_disagreement"),
        CheckConstraint("generated_only = true", name="ck_rule_shadow_generated"),
        CheckConstraint("operational = false", name="ck_rule_shadow_nonoperational"),
        Index("ix_rule_shadow_scope", "department", "rule_record_id", "created_at"),
    )

    comparison_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    rule_record_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_rules.rule_record_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    candidate_compilation_id: Mapped[str] = mapped_column(String(37), nullable=False)
    baseline_compilation_id: Mapped[str] = mapped_column(String(37), nullable=False)
    candidate_matches: Mapped[int] = mapped_column(Integer, nullable=False)
    baseline_matches: Mapped[int] = mapped_column(Integer, nullable=False)
    disagreement_count: Mapped[int] = mapped_column(Integer, nullable=False)
    comparison_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )


class CorrelationRun(Base):
    __tablename__ = "correlation_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('blocked', 'queued', 'running', 'succeeded', 'failed')",
            name="ck_correlation_run_status",
        ),
        CheckConstraint(
            "execution_scope IN ('contract_only', 'generated_event_correlation')",
            name="ck_correlation_run_scope",
        ),
        CheckConstraint(
            "reason_code IN ('p4_0_runtime_disabled', 'generated_queued', "
            "'generated_lease_acquired', 'generated_completed', 'generated_failed')",
            name="ck_correlation_run_reason",
        ),
        CheckConstraint("generated_only = true", name="ck_correlation_run_generated"),
        CheckConstraint(
            "attempt_count >= 0 AND attempt_count <= 3",
            name="ck_correlation_run_attempts",
        ),
        Index("ix_correlation_run_scope", "department", "created_at"),
    )

    run_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    execution_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    profile_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    profile_version: Mapped[str | None] = mapped_column(String(71), nullable=True)
    result_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    replay_binding: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    input_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accepted_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duplicate_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rejected_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    watermark_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )


class CorrelationHypothesis(Base):
    __tablename__ = "correlation_hypotheses"
    __table_args__ = (
        CheckConstraint("version_id >= 1", name="ck_correlation_hypothesis_version"),
        CheckConstraint(
            "state IN ('proposed', 'abstained', 'expired', 'superseded', "
            "'retracted', 'corrected')",
            name="ck_correlation_hypothesis_state",
        ),
        CheckConstraint(
            "authority_class = 'mandatory_review'",
            name="ck_correlation_hypothesis_authority",
        ),
        CheckConstraint(
            "operational = false", name="ck_correlation_hypothesis_nonoperational"
        ),
        CheckConstraint(
            "generated_only = true", name="ck_correlation_hypothesis_generated"
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1 AND uncertainty >= 0 AND uncertainty <= 1",
            name="ck_correlation_hypothesis_scores",
        ),
        CheckConstraint(
            "contradiction_count >= 0 AND contradiction_count <= 256",
            name="ck_correlation_hypothesis_contradictions",
        ),
        UniqueConstraint(
            "department", "hypothesis_key", name="uq_correlation_hypothesis_key"
        ),
        Index("ix_correlation_hypothesis_scope", "department", "state", "created_at"),
    )

    hypothesis_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("correlation_runs.run_id", ondelete="RESTRICT"), nullable=True
    )
    hypothesis_key: Mapped[str] = mapped_column(String(71), nullable=False)
    profile_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    profile_version: Mapped[str | None] = mapped_column(String(71), nullable=True)
    partition_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    subject_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    authority_class: Mapped[str] = mapped_column(String(32), nullable=False)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    uncertainty: Mapped[float] = mapped_column(Float, nullable=False)
    abstained: Mapped[bool] = mapped_column(Boolean, nullable=False)
    abstention_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contradiction_count: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    canonical_json: Mapped[str] = mapped_column(Text, nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    graph_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    arbitration_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    projection: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}


class HypothesisEvidenceReference(Base):
    __tablename__ = "hypothesis_evidence_refs"
    __table_args__ = (
        CheckConstraint(
            "role IN ('supports', 'contradicts', 'missing', 'stale', 'supersedes', 'retracts')",
            name="ck_hypothesis_evidence_role",
        ),
        CheckConstraint("sequence >= 0", name="ck_hypothesis_evidence_sequence"),
        UniqueConstraint(
            "hypothesis_id", "evidence_id", name="uq_hypothesis_evidence_reference"
        ),
        Index(
            "ix_hypothesis_evidence_scope", "department", "hypothesis_id", "sequence"
        ),
    )

    evidence_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    hypothesis_id: Mapped[str] = mapped_column(
        ForeignKey("correlation_hypotheses.hypothesis_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(160), nullable=False)
    source_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )


class CorrelationEventReceipt(Base):
    __tablename__ = "correlation_event_receipts"
    __table_args__ = (
        CheckConstraint(
            "disposition IN ('accepted', 'duplicate', 'conflict', 'late_accepted', "
            "'late_rejected', 'gap_accepted', 'future_rejected', 'policy_rejected', "
            "'capacity_rejected')",
            name="ck_correlation_receipt_disposition",
        ),
        CheckConstraint(
            "receipt_sequence >= 0", name="ck_correlation_receipt_sequence"
        ),
        CheckConstraint(
            "generated_only = true", name="ck_correlation_receipt_generated"
        ),
        UniqueConstraint(
            "run_id", "receipt_sequence", name="uq_correlation_receipt_run_sequence"
        ),
        Index(
            "ix_correlation_receipt_scope", "department", "run_id", "receipt_sequence"
        ),
    )

    receipt_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("correlation_runs.run_id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    event_id: Mapped[str] = mapped_column(String(160), nullable=False)
    event_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    partition_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    disposition: Mapped[str] = mapped_column(String(24), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    receipt_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CorrelationPartitionCheckpoint(Base):
    __tablename__ = "correlation_partition_checkpoints"
    __table_args__ = (
        CheckConstraint("version_id >= 1", name="ck_correlation_checkpoint_version"),
        CheckConstraint(
            "receipt_sequence >= 0", name="ck_correlation_checkpoint_sequence"
        ),
        CheckConstraint(
            "active_window_count >= 0 AND active_window_count <= 256",
            name="ck_correlation_checkpoint_windows",
        ),
        CheckConstraint(
            "generated_only = true", name="ck_correlation_checkpoint_generated"
        ),
        UniqueConstraint(
            "department",
            "profile_id",
            "partition_digest",
            name="uq_correlation_checkpoint_partition",
        ),
        Index(
            "ix_correlation_checkpoint_scope",
            "department",
            "profile_id",
            "watermark_at",
        ),
    )

    checkpoint_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    profile_id: Mapped[str] = mapped_column(String(128), nullable=False)
    partition_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    receipt_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_source_sequence: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    maximum_occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    watermark_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    active_window_count: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}


class CorrelationWindowEvent(Base):
    __tablename__ = "correlation_window_events"
    __table_args__ = (
        CheckConstraint("sequence >= 0", name="ck_correlation_window_event_sequence"),
        CheckConstraint(
            "generated_only = true", name="ck_correlation_window_event_generated"
        ),
        UniqueConstraint("window_id", "event_id", name="uq_correlation_window_event"),
        Index(
            "ix_correlation_window_event_scope", "department", "window_id", "sequence"
        ),
    )

    membership_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("correlation_runs.run_id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    window_id: Mapped[str] = mapped_column(String(37), nullable=False)
    event_id: Mapped[str] = mapped_column(String(160), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    window_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CorrelationLaneResult(Base):
    __tablename__ = "correlation_lane_results"
    __table_args__ = (
        CheckConstraint(
            "lane IN ('deterministic_cpu', 'probabilistic', 'temporal_graph', "
            "'model_first_shadow', 'uncertainty_ensemble')",
            name="ck_correlation_lane_name",
        ),
        CheckConstraint(
            "operational = false", name="ck_correlation_lane_nonoperational"
        ),
        CheckConstraint("generated_only = true", name="ck_correlation_lane_generated"),
        UniqueConstraint(
            "hypothesis_id", "lane", name="uq_correlation_lane_hypothesis"
        ),
        Index("ix_correlation_lane_scope", "department", "hypothesis_id", "lane"),
    )

    lane_result_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    hypothesis_id: Mapped[str] = mapped_column(
        ForeignKey("correlation_hypotheses.hypothesis_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    lane: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    lineage_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    generated_fixture_result: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CorrelationHypothesisRevision(Base):
    __tablename__ = "correlation_hypothesis_revisions"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_correlation_revision_positive"),
        CheckConstraint(
            "operational = false", name="ck_correlation_revision_nonoperational"
        ),
        CheckConstraint(
            "generated_only = true", name="ck_correlation_revision_generated"
        ),
        UniqueConstraint(
            "hypothesis_id", "revision", name="uq_correlation_hypothesis_revision"
        ),
        Index(
            "ix_correlation_revision_scope", "department", "hypothesis_id", "revision"
        ),
    )

    revision_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    hypothesis_id: Mapped[str] = mapped_column(
        ForeignKey("correlation_hypotheses.hypothesis_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_state: Mapped[str] = mapped_column(String(16), nullable=False)
    new_state: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    snapshot_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ReferenceProvider(Base):
    __tablename__ = "reference_providers"
    __table_args__ = (
        CheckConstraint("version_id >= 1", name="ck_reference_provider_version"),
        CheckConstraint("status = 'disabled'", name="ck_reference_provider_status"),
        CheckConstraint("enabled = false", name="ck_reference_provider_disabled"),
        CheckConstraint(
            "provider_kind = 'generated_fixture'", name="ck_reference_provider_kind"
        ),
        CheckConstraint(
            "transport_state = 'absent'", name="ck_reference_provider_transport"
        ),
        CheckConstraint(
            "credential_state = 'none'", name="ck_reference_provider_credentials"
        ),
        CheckConstraint(
            "generated_only = true", name="ck_reference_provider_generated"
        ),
        UniqueConstraint(
            "department", "provider_key", name="uq_reference_provider_department_key"
        ),
        Index("ix_reference_provider_scope", "department", "status"),
    )

    provider_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provider_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    transport_state: Mapped[str] = mapped_column(String(16), nullable=False)
    credential_state: Mapped[str] = mapped_column(String(16), nullable=False)
    policy_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    destination_policy_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    allowed_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    configuration_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    owner_id: Mapped[str] = mapped_column(String(160), nullable=False)
    last_change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}


class ReferenceQuery(Base):
    __tablename__ = "reference_queries"
    __table_args__ = (
        CheckConstraint("status = 'blocked'", name="ck_reference_query_status"),
        CheckConstraint(
            "reason_code = 'provider_disabled'", name="ck_reference_query_reason"
        ),
        CheckConstraint("generated_only = true", name="ck_reference_query_generated"),
        Index("ix_reference_query_scope", "department", "requested_at"),
    )

    query_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    provider_id: Mapped[str] = mapped_column(
        ForeignKey("reference_providers.provider_id", ondelete="RESTRICT"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    purpose_code: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_by: Mapped[str] = mapped_column(String(160), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requested_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint("version_id >= 1", name="ck_alert_version"),
        CheckConstraint(
            "state IN ('proposed', 'queued_review', 'under_review', 'accepted', "
            "'rejected', 'resolved', 'corrected', 'suppressed', 'merged')",
            name="ck_alert_state",
        ),
        CheckConstraint(
            "authority_class IN ('mandatory_review', 'bounded_automation')",
            name="ck_alert_authority",
        ),
        CheckConstraint(
            "domain IN ('police_intelligence', 'system_health')",
            name="ck_alert_domain",
        ),
        CheckConstraint(
            "domain != 'police_intelligence' OR authority_class = 'mandatory_review'",
            name="ck_alert_police_review",
        ),
        CheckConstraint("operational = false", name="ck_alert_nonoperational"),
        CheckConstraint("generated_only = true", name="ck_alert_generated"),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_alert_confidence"
        ),
        CheckConstraint(
            "certainty IS NULL OR (certainty >= 0 AND certainty <= 1)",
            name="ck_alert_certainty",
        ),
        CheckConstraint(
            "chronology_confidence IS NULL OR "
            "(chronology_confidence >= 0 AND chronology_confidence <= 1)",
            name="ck_alert_chronology_confidence",
        ),
        UniqueConstraint("department", "dedupe_key", name="uq_alert_dedupe_key"),
        UniqueConstraint(
            "department", "semantic_key", name="uq_alert_semantic_key"
        ),
        UniqueConstraint(
            "department", "delivery_key", name="uq_alert_delivery_key"
        ),
        Index("ix_alert_scope", "department", "state", "created_at"),
    )

    alert_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    hypothesis_id: Mapped[str | None] = mapped_column(
        ForeignKey("correlation_hypotheses.hypothesis_id", ondelete="RESTRICT"),
        nullable=True,
    )
    dedupe_key: Mapped[str] = mapped_column(String(71), nullable=False)
    semantic_key: Mapped[str | None] = mapped_column(String(71), nullable=True)
    delivery_key: Mapped[str | None] = mapped_column(String(71), nullable=True)
    source_evaluation_id: Mapped[str | None] = mapped_column(String(37), nullable=True)
    source_evaluation_revision: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    source_evaluation_digest: Mapped[str | None] = mapped_column(
        String(71), nullable=True
    )
    incident_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    domain: Mapped[str] = mapped_column(
        String(32), nullable=False, default="police_intelligence"
    )
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    authority_class: Mapped[str] = mapped_column(String(32), nullable=False)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    certainty: Mapped[float | None] = mapped_column(Float, nullable=True)
    chronology_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    disposition: Mapped[str] = mapped_column(String(16), nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(160), nullable=True)
    suppression_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    merged_into: Mapped[str | None] = mapped_column(String(36), nullable=True)
    policy_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}


class AlertRevision(Base):
    __tablename__ = "alert_revisions"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_alert_revision_positive"),
        UniqueConstraint("alert_id", "revision", name="uq_alert_revision"),
        Index("ix_alert_revision_scope", "department", "alert_id", "recorded_at"),
    )

    revision_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    alert_id: Mapped[str] = mapped_column(
        ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_state: Mapped[str] = mapped_column(String(16), nullable=False)
    new_state: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationTimeline(Base):
    __tablename__ = "investigation_timelines"
    __table_args__ = (
        CheckConstraint("version_id >= 1", name="ck_investigation_timeline_version"),
        CheckConstraint(
            "status IN ('draft', 'closed')", name="ck_investigation_timeline_status"
        ),
        CheckConstraint(
            "generated_only = true", name="ck_investigation_timeline_generated"
        ),
        Index("ix_investigation_timeline_scope", "department", "status", "updated_at"),
    )

    timeline_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    title_code: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    owner_id: Mapped[str] = mapped_column(String(160), nullable=False)
    last_change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utc_now
    )

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version_id}


class TimelineEntry(Base):
    __tablename__ = "timeline_entries"
    __table_args__ = (
        CheckConstraint("sequence >= 1", name="ck_timeline_entry_sequence"),
        CheckConstraint(
            "entry_type IN ('source_fact', 'system_hypothesis', "
            "'operator_observation', 'review_decision', 'correction')",
            name="ck_timeline_entry_type",
        ),
        CheckConstraint("generated_only = true", name="ck_timeline_entry_generated"),
        UniqueConstraint("timeline_id", "sequence", name="uq_timeline_entry_sequence"),
        Index("ix_timeline_entry_scope", "department", "timeline_id", "sequence"),
    )

    entry_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines.timeline_id", ondelete="CASCADE"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    source_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    summary_code: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)


class AlertCommandReceipt(Base):
    __tablename__ = "alert_command_receipts"
    __table_args__ = (
        CheckConstraint(
            "disposition IN ('accepted', 'duplicate', 'conflict')",
            name="ck_alert_command_receipt_disposition",
        ),
        CheckConstraint(
            "generated_only = true", name="ck_alert_command_receipt_generated"
        ),
        UniqueConstraint(
            "department", "delivery_key", name="uq_alert_command_delivery"
        ),
        Index("ix_alert_command_scope", "department", "recorded_at"),
    )

    receipt_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    delivery_key: Mapped[str] = mapped_column(String(71), nullable=False)
    semantic_key: Mapped[str] = mapped_column(String(71), nullable=False)
    occurrence_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    alert_id: Mapped[str | None] = mapped_column(
        ForeignKey("alerts.alert_id", ondelete="SET NULL"), nullable=True
    )
    disposition: Mapped[str] = mapped_column(String(16), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class AlertLifecycleRecord(Base):
    __tablename__ = "alert_lifecycle_events"
    __table_args__ = (
        CheckConstraint("sequence >= 1", name="ck_alert_lifecycle_sequence"),
        CheckConstraint(
            "generated_only = true", name="ck_alert_lifecycle_generated"
        ),
        CheckConstraint(
            "operational = false", name="ck_alert_lifecycle_nonoperational"
        ),
        UniqueConstraint("alert_id", "sequence", name="uq_alert_lifecycle_sequence"),
        Index("ix_alert_lifecycle_scope", "department", "alert_id", "recorded_at"),
    )

    event_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    alert_id: Mapped[str] = mapped_column(
        ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    previous_state: Mapped[str] = mapped_column(String(24), nullable=False)
    new_state: Mapped[str] = mapped_column(String(24), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class AlertReviewQuorumPolicy(Base):
    __tablename__ = "alert_review_quorum_policies"
    __table_args__ = (
        CheckConstraint(
            "workflow_class IN ('ordinary', 'generated_high_impact')",
            name="ck_alert_quorum_workflow_class",
        ),
        CheckConstraint(
            "required_distinct_reviewers >= 1 AND required_distinct_reviewers <= 5",
            name="ck_alert_quorum_bound",
        ),
        CheckConstraint("generated_only = true", name="ck_alert_quorum_generated"),
        UniqueConstraint(
            "department", "policy_key", "policy_version", name="uq_alert_quorum_version"
        ),
        Index("ix_alert_quorum_scope", "department", "effective_at"),
    )

    policy_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    policy_key: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_version: Mapped[int] = mapped_column(Integer, nullable=False)
    workflow_class: Mapped[str] = mapped_column(String(32), nullable=False)
    required_distinct_reviewers: Mapped[int] = mapped_column(Integer, nullable=False)
    permitted_roles: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    evidence_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AlertReviewDecision(Base):
    __tablename__ = "alert_review_decisions"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('approve', 'deny', 'request_information', 'correct')",
            name="ck_alert_review_decision",
        ),
        CheckConstraint("generated_only = true", name="ck_alert_review_generated"),
        CheckConstraint(
            "operational = false", name="ck_alert_review_nonoperational"
        ),
        Index("ix_alert_review_scope", "department", "alert_id", "recorded_at"),
    )

    decision_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    alert_id: Mapped[str] = mapped_column(
        ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False
    )
    policy_id: Mapped[str] = mapped_column(
        ForeignKey("alert_review_quorum_policies.policy_id", ondelete="RESTRICT"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    policy_version: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reviewer_role: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    supersedes_decision_id: Mapped[str | None] = mapped_column(String(37), nullable=True)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class AlertAssignmentEvent(Base):
    __tablename__ = "alert_assignment_events"
    __table_args__ = (
        CheckConstraint(
            "generated_only = true", name="ck_alert_assignment_generated"
        ),
        Index("ix_alert_assignment_scope", "department", "alert_id", "recorded_at"),
    )

    assignment_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    alert_id: Mapped[str] = mapped_column(
        ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    assignee_id: Mapped[str] = mapped_column(String(160), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class AlertSuppressionEvent(Base):
    __tablename__ = "alert_suppression_events"
    __table_args__ = (
        CheckConstraint(
            "generated_only = true", name="ck_alert_suppression_generated"
        ),
        CheckConstraint(
            "represented_alerts >= 1 AND suppressed_alerts >= 0",
            name="ck_alert_suppression_counts",
        ),
        Index("ix_alert_suppression_scope", "department", "alert_id", "recorded_at"),
    )

    suppression_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    alert_id: Mapped[str] = mapped_column(
        ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(128), nullable=False)
    collapse_key: Mapped[str | None] = mapped_column(String(71), nullable=True)
    represented_alerts: Mapped[int] = mapped_column(Integer, nullable=False)
    suppressed_alerts: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class AlertMergeRelation(Base):
    __tablename__ = "alert_merge_relations"
    __table_args__ = (
        CheckConstraint("source_alert_id != target_alert_id", name="ck_alert_merge_self"),
        CheckConstraint("generated_only = true", name="ck_alert_merge_generated"),
        UniqueConstraint("source_alert_id", name="uq_alert_merge_source"),
        Index("ix_alert_merge_scope", "department", "target_alert_id", "recorded_at"),
    )

    relation_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    source_alert_id: Mapped[str] = mapped_column(
        ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False
    )
    target_alert_id: Mapped[str] = mapped_column(
        ForeignKey("alerts.alert_id", ondelete="RESTRICT"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class AlertBudgetPolicy(Base):
    __tablename__ = "alert_budget_policies"
    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_alert_budget_policy_version"),
        CheckConstraint("generated_only = true", name="ck_alert_budget_policy_generated"),
        UniqueConstraint("department", "policy_key", "version", name="uq_alert_budget_policy_version"),
        Index("ix_alert_budget_policy_scope", "department", "created_at"),
    )

    policy_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    policy_key: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    limits: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    policy_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class AlertBudgetCounter(Base):
    __tablename__ = "alert_budget_counters"
    __table_args__ = (
        CheckConstraint("observed_count >= 0", name="ck_alert_budget_count"),
        CheckConstraint("generated_only = true", name="ck_alert_budget_counter_generated"),
        UniqueConstraint(
            "department", "scope", "scope_key", "window_started_at",
            name="uq_alert_budget_counter_window",
        ),
        Index("ix_alert_budget_counter_scope", "department", "window_started_at"),
    )

    counter_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(128), nullable=False)
    window_started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    observed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AlertTimerIntent(Base):
    __tablename__ = "alert_timer_intents"
    __table_args__ = (
        CheckConstraint(
            "state IN ('pending', 'leased', 'completed', 'failed', 'cancelled')",
            name="ck_alert_timer_state",
        ),
        CheckConstraint(
            "attempt_count >= 0 AND attempt_count <= 3", name="ck_alert_timer_attempts"
        ),
        CheckConstraint("generated_only = true", name="ck_alert_timer_generated"),
        CheckConstraint("operational = false", name="ck_alert_timer_nonoperational"),
        UniqueConstraint("alert_id", "timer_kind", "due_at", name="uq_alert_timer_intent"),
        Index("ix_alert_timer_due", "department", "state", "due_at"),
    )

    timer_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    alert_id: Mapped[str] = mapped_column(
        ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    timer_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    due_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    expected_alert_version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class AlertWorkflowExecution(Base):
    __tablename__ = "alert_workflow_executions"
    __table_args__ = (
        CheckConstraint(
            "adapter_kind IN ('local_bounded', 'generated_simulator', 'future_disabled')",
            name="ck_alert_workflow_adapter",
        ),
        CheckConstraint(
            "outcome IN ('applied', 'stale', 'rejected', 'adapter_disabled')",
            name="ck_alert_workflow_outcome",
        ),
        CheckConstraint("generated_only = true", name="ck_alert_workflow_generated"),
        CheckConstraint("operational = false", name="ck_alert_workflow_nonoperational"),
        Index("ix_alert_workflow_scope", "department", "timer_id", "recorded_at"),
    )

    execution_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timer_id: Mapped[str] = mapped_column(
        ForeignKey("alert_timer_intents.timer_id", ondelete="CASCADE"), nullable=False
    )
    alert_id: Mapped[str] = mapped_column(
        ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    adapter_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(128), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
