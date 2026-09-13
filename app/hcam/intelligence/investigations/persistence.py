from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column

from hcam.database import Base, UTCDateTime
from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.contracts import (
    CorrectionCommandV1,
    DeletionReceiptV1,
    EvidenceReferenceV2,
    ExportManifestV1,
    HoldOverlayV1,
    ImpactRecordV1,
    IntegrityAssessmentV1,
    InvestigationTimelineV2,
    ProvenanceBundleV1,
    RelationshipRevisionV1,
    RetentionEvaluationV1,
    ReviewDecisionV1,
    TimelineCreateCommandV2,
    TimelineEntryV2,
)
from hcam.intelligence.investigations.review import latest_review


def _now() -> datetime:
    return datetime.now(UTC)


class InvestigationTimelineRecord(Base):
    __tablename__ = "investigation_timelines_v2"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_investigation_timeline_revision"),
        CheckConstraint("entry_count >= 0", name="ck_investigation_timeline_entry_count"),
        CheckConstraint("generated_only = true", name="ck_investigation_timeline_generated"),
        CheckConstraint("operational = false", name="ck_investigation_timeline_nonoperational"),
        Index("ix_investigation_timeline_v2_scope", "department", "updated_at"),
    )

    timeline_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose_code: Mapped[str] = mapped_column(String(96), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(16), nullable=False)
    disposition: Mapped[str] = mapped_column(String(24), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_count: Mapped[int] = mapped_column(Integer, nullable=False)
    canonical_timeline_id: Mapped[str] = mapped_column(String(37), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __mapper_args__ = {"version_id_col": version_id}


class InvestigationTimelineRevision(Base):
    __tablename__ = "investigation_timeline_revisions"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_investigation_revision_number"),
        CheckConstraint("generated_only = true", name="ck_investigation_revision_generated"),
        CheckConstraint("operational = false", name="ck_investigation_revision_nonoperational"),
        UniqueConstraint("timeline_id", "revision", name="uq_investigation_timeline_revision"),
        UniqueConstraint("timeline_id", "content_digest", name="uq_investigation_revision_digest"),
        Index("ix_investigation_revision_scope", "department", "timeline_id", "revision"),
    )

    revision_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(16), nullable=False)
    disposition: Mapped[str] = mapped_column(String(24), nullable=False)
    entry_count: Mapped[int] = mapped_column(Integer, nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationTimelineEntryRecord(Base):
    __tablename__ = "investigation_timeline_entries_v2"
    __table_args__ = (
        CheckConstraint("sequence >= 1", name="ck_investigation_entry_sequence"),
        CheckConstraint("aggregate_revision >= 1", name="ck_investigation_entry_revision"),
        CheckConstraint("generated_only = true", name="ck_investigation_entry_generated"),
        CheckConstraint("operational = false", name="ck_investigation_entry_nonoperational"),
        UniqueConstraint("timeline_id", "sequence", name="uq_investigation_entry_sequence"),
        UniqueConstraint("department", "semantic_key", name="uq_investigation_entry_semantic"),
        UniqueConstraint("department", "delivery_key", name="uq_investigation_entry_delivery"),
        Index("ix_investigation_entry_scope", "department", "timeline_id", "sequence"),
    )

    entry_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    family: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    aggregate_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    semantic_key: Mapped[str] = mapped_column(String(71), nullable=False)
    delivery_key: Mapped[str] = mapped_column(String(71), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationEvidenceReferenceRecord(Base):
    __tablename__ = "investigation_evidence_references"
    __table_args__ = (
        CheckConstraint("source_payload_retained = false", name="ck_investigation_evidence_no_payload"),
        CheckConstraint("locator_retained = false", name="ck_investigation_evidence_no_locator"),
        CheckConstraint("generated_only = true", name="ck_investigation_evidence_generated"),
        UniqueConstraint(
            "department",
            "source_system_ref",
            "source_object_ref",
            "source_version",
            "content_digest",
            name="uq_investigation_evidence_identity",
        ),
        Index("ix_investigation_evidence_scope", "department", "timeline_id", "registered_at"),
    )

    reference_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    source_system_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    source_object_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    source_version: Mapped[str] = mapped_column(String(128), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    canonicalization_profile: Mapped[str] = mapped_column(String(128), nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    source_payload_retained: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    locator_retained: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    registered_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationIntegrityAssessmentRecord(Base):
    __tablename__ = "investigation_integrity_assessments"
    __table_args__ = (
        CheckConstraint("source_payload_retained = false", name="ck_investigation_integrity_no_payload"),
        CheckConstraint("generated_only = true", name="ck_investigation_integrity_generated"),
        Index("ix_investigation_integrity_scope", "department", "reference_id", "assessed_at"),
    )

    assessment_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    reference_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_evidence_references.reference_id", ondelete="RESTRICT"), nullable=False
    )
    timeline_id: Mapped[str] = mapped_column(String(37), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    expected_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    observed_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    reason_code: Mapped[str] = mapped_column(String(96), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    source_payload_retained: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    assessed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationProvenanceBundleRecord(Base):
    __tablename__ = "investigation_provenance_bundles"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_investigation_provenance_generated"),
        UniqueConstraint("timeline_id", "bundle_digest", name="uq_investigation_provenance_digest"),
        Index("ix_investigation_provenance_scope", "department", "timeline_id", "recorded_at"),
    )

    bundle_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    bundle_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    completeness: Mapped[str] = mapped_column(String(16), nullable=False)
    node_count: Mapped[int] = mapped_column(Integer, nullable=False)
    edge_count: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationCorrectionRecord(Base):
    __tablename__ = "investigation_corrections"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_investigation_correction_generated"),
        CheckConstraint("operational = false", name="ck_investigation_correction_nonoperational"),
        UniqueConstraint("department", "delivery_id", name="uq_investigation_correction_delivery"),
        Index("ix_investigation_correction_scope", "department", "timeline_id", "recorded_at"),
    )

    correction_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    target_type: Mapped[str] = mapped_column(String(24), nullable=False)
    target_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    target_version: Mapped[int] = mapped_column(Integer, nullable=False)
    replacement_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)
    delivery_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationCorrectionImpactRecord(Base):
    __tablename__ = "investigation_correction_impacts"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_investigation_impact_generated"),
        UniqueConstraint("correction_id", "target_type", "target_ref", name="uq_investigation_impact_target"),
        Index("ix_investigation_impact_scope", "department", "correction_id", "state"),
    )

    impact_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    correction_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_corrections.correction_id", ondelete="RESTRICT"), nullable=False
    )
    timeline_id: Mapped[str] = mapped_column(String(37), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    target_type: Mapped[str] = mapped_column(String(24), nullable=False)
    target_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(96), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationReviewRecord(Base):
    __tablename__ = "investigation_reviews"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_investigation_review_revision"),
        CheckConstraint("generated_only = true", name="ck_investigation_review_generated"),
        CheckConstraint("operational = false", name="ck_investigation_review_nonoperational"),
        UniqueConstraint("timeline_id", "target_ref", "revision", name="uq_investigation_review_revision"),
        Index("ix_investigation_review_scope", "department", "timeline_id", "recorded_at"),
    )

    review_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    target_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    disposition: Mapped[str] = mapped_column(String(24), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    supersedes_review_id: Mapped[str | None] = mapped_column(String(37), nullable=True)
    evidence_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationRelationshipRecord(Base):
    __tablename__ = "investigation_relationships"
    __table_args__ = (
        CheckConstraint("source_timeline_id != target_timeline_id", name="ck_investigation_relationship_self"),
        CheckConstraint("generated_only = true", name="ck_investigation_relationship_generated"),
        UniqueConstraint("source_timeline_id", "target_timeline_id", "kind", "revision", name="uq_investigation_relationship_revision"),
        Index("ix_investigation_relationship_scope", "department", "source_timeline_id", "recorded_at"),
    )

    relationship_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    source_timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"), nullable=False
    )
    target_timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationHoldOverlayRecord(Base):
    __tablename__ = "investigation_hold_overlays"
    __table_args__ = (
        CheckConstraint("grants_access = false", name="ck_investigation_hold_no_access"),
        CheckConstraint("effective_runtime_action = false", name="ck_investigation_hold_no_action"),
        CheckConstraint("generated_only = true", name="ck_investigation_hold_generated"),
        UniqueConstraint("hold_ref", "revision", name="uq_investigation_hold_revision"),
        Index("ix_investigation_hold_scope", "department", "timeline_id", "recorded_at"),
    )

    row_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    hold_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    grants_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    effective_runtime_action: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationRetentionEvaluationRecord(Base):
    __tablename__ = "investigation_retention_evaluations"
    __table_args__ = (
        CheckConstraint("advisory_only = true", name="ck_investigation_retention_advisory"),
        CheckConstraint("legal_period_selected = false", name="ck_investigation_retention_no_period"),
        CheckConstraint("generated_only = true", name="ck_investigation_retention_generated"),
        Index("ix_investigation_retention_scope", "department", "timeline_id", "evaluated_at"),
    )

    evaluation_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    policy_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    advisory_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    legal_period_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    evaluated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationDeletionReceiptRecord(Base):
    __tablename__ = "investigation_deletion_receipts"
    __table_args__ = (
        CheckConstraint("universal_deletion_proven = false", name="ck_investigation_deletion_no_universal"),
        CheckConstraint("external_action_executed = false", name="ck_investigation_deletion_no_action"),
        CheckConstraint("generated_only = true", name="ck_investigation_deletion_generated"),
        UniqueConstraint("intent_id", "target_ref", name="uq_investigation_deletion_target"),
        Index("ix_investigation_deletion_scope", "department", "timeline_id", "recorded_at"),
    )

    receipt_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    intent_id: Mapped[str] = mapped_column(String(37), nullable=False)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    target_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    outcome: Mapped[str] = mapped_column(String(24), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    universal_deletion_proven: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    external_action_executed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationExportManifestRecord(Base):
    __tablename__ = "investigation_export_manifests"
    __table_args__ = (
        CheckConstraint("source_payload_included = false", name="ck_investigation_export_no_payload"),
        CheckConstraint("generated_only = true", name="ck_investigation_export_generated"),
        CheckConstraint("operational = false", name="ck_investigation_export_nonoperational"),
        UniqueConstraint("timeline_id", "manifest_digest", name="uq_investigation_export_digest"),
        Index("ix_investigation_export_scope", "department", "timeline_id", "prepared_at"),
    )

    manifest_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_timelines_v2.timeline_id", ondelete="RESTRICT"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    purpose_code: Mapped[str] = mapped_column(String(96), nullable=False)
    recipient_class: Mapped[str] = mapped_column(String(32), nullable=False)
    completeness: Mapped[str] = mapped_column(String(16), nullable=False)
    manifest_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    source_payload_included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prepared_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationImpactJobRecord(Base):
    __tablename__ = "investigation_impact_jobs"
    __table_args__ = (
        CheckConstraint("attempt_count >= 0 AND attempt_count <= 3", name="ck_investigation_job_attempts"),
        CheckConstraint("generated_only = true", name="ck_investigation_job_generated"),
        CheckConstraint("operational = false", name="ck_investigation_job_nonoperational"),
        UniqueConstraint("correction_id", name="uq_investigation_job_correction"),
        Index("ix_investigation_job_due", "department", "state", "updated_at"),
    )

    job_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    correction_id: Mapped[str] = mapped_column(
        ForeignKey("investigation_corrections.correction_id", ondelete="RESTRICT"), nullable=False
    )
    timeline_id: Mapped[str] = mapped_column(String(37), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    reason_code: Mapped[str] = mapped_column(String(96), nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __mapper_args__ = {"version_id_col": version_id}


class InvestigationCommandReceipt(Base):
    __tablename__ = "investigation_command_receipts"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_investigation_receipt_generated"),
        UniqueConstraint("department", "delivery_id", name="uq_investigation_command_delivery"),
        Index("ix_investigation_receipt_scope", "department", "timeline_id", "recorded_at"),
    )

    receipt_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    timeline_id: Mapped[str] = mapped_column(String(37), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    delivery_id: Mapped[str] = mapped_column(String(128), nullable=False)
    command_type: Mapped[str] = mapped_column(String(64), nullable=False)
    command_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    response_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InvestigationOutbox(Base):
    __tablename__ = "investigation_outbox"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_investigation_outbox_generated"),
        CheckConstraint("operational = false", name="ck_investigation_outbox_nonoperational"),
        Index("ix_investigation_outbox_pending", "department", "published_at", "occurred_at"),
    )

    event_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


class InvestigationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def timeline(self, timeline_id: str) -> InvestigationTimelineRecord | None:
        return self.session.get(InvestigationTimelineRecord, timeline_id)

    def timelines(self, departments: frozenset[str] | None) -> list[InvestigationTimelineV2]:
        statement = select(InvestigationTimelineRecord).order_by(
            InvestigationTimelineRecord.updated_at.desc(),
            InvestigationTimelineRecord.timeline_id,
        )
        if departments is not None:
            statement = statement.where(InvestigationTimelineRecord.department.in_(departments))
        return [timeline_contract(row) for row in self.session.scalars(statement)]

    def create_timeline(
        self, command: TimelineCreateCommandV2
    ) -> tuple[InvestigationTimelineV2, bool]:
        command_digest = digest(command)
        receipt = self._receipt(command.department, command.delivery_id)
        if receipt is not None:
            if receipt.command_digest != command_digest:
                raise ValueError("delivery identifier is bound to different command material")
            row = self.timeline(receipt.response_ref)
            if row is None:
                raise ValueError("command receipt references a missing timeline")
            return timeline_contract(row), True
        if self.timeline(command.timeline_id) is not None:
            raise ValueError("timeline identifier already exists")
        content_digest = digest(
            {
                "timeline_id": command.timeline_id,
                "department": command.department,
                "title": command.title,
                "purpose_code": command.purpose_code,
                "lifecycle": "open",
                "disposition": "unreviewed",
                "revision": 1,
                "entry_count": 0,
            }
        )
        row = InvestigationTimelineRecord(
            timeline_id=command.timeline_id,
            department=command.department,
            title=command.title,
            purpose_code=command.purpose_code,
            lifecycle="open",
            disposition="unreviewed",
            revision=1,
            entry_count=0,
            canonical_timeline_id=command.timeline_id,
            content_digest=content_digest,
            created_at=command.requested_at,
            updated_at=command.requested_at,
        )
        self.session.add(row)
        self.session.flush()
        contract = timeline_contract(row)
        self._add_revision(contract, command.actor_id, command.reason)
        self._add_receipt(
            timeline_id=command.timeline_id,
            department=command.department,
            delivery_id=command.delivery_id,
            command_type="timeline.create",
            command_digest=command_digest,
            response_ref=command.timeline_id,
            recorded_at=command.requested_at,
        )
        self._outbox(
            "hcam.investigation.timeline.created.v1",
            command.timeline_id,
            command.department,
            {"revision": 1, "generated_only": True},
            command.requested_at,
        )
        self.session.flush()
        return contract, False

    def append_entry(
        self,
        entry: TimelineEntryV2,
        *,
        expected_revision: int,
    ) -> tuple[InvestigationTimelineV2, bool]:
        row = self.timeline(entry.timeline_id)
        if row is None or row.department != entry.department:
            raise KeyError("timeline was not found")
        duplicate = self.session.scalar(
            select(InvestigationTimelineEntryRecord).where(
                InvestigationTimelineEntryRecord.department == entry.department,
                InvestigationTimelineEntryRecord.delivery_key == entry.delivery_key,
            )
        )
        if duplicate is not None:
            if duplicate.content_digest != entry.content_digest:
                raise ValueError("delivery key is bound to different entry material")
            return timeline_contract(row), True
        if row.revision != expected_revision:
            raise ValueError("timeline revision does not match")
        if entry.sequence != row.entry_count + 1 or entry.aggregate_revision != row.revision + 1:
            raise ValueError("entry sequence or aggregate revision is not next")
        self.session.add(
            InvestigationTimelineEntryRecord(
                entry_id=entry.entry_id,
                timeline_id=entry.timeline_id,
                department=entry.department,
                family=entry.family,
                subject_ref=entry.subject_ref,
                sequence=entry.sequence,
                aggregate_revision=entry.aggregate_revision,
                semantic_key=entry.semantic_key,
                delivery_key=entry.delivery_key,
                content_digest=entry.content_digest,
                payload=entry.model_dump(mode="json"),
                actor_id=entry.actor_id,
                reason=entry.reason,
                recorded_at=entry.temporal.recorded_at,
            )
        )
        row.revision = entry.aggregate_revision
        row.entry_count = entry.sequence
        row.updated_at = entry.temporal.recorded_at
        row.content_digest = digest(
            {
                "prior": row.content_digest,
                "entry": entry.content_digest,
                "revision": row.revision,
            }
        )
        contract = timeline_contract(row)
        self._add_revision(contract, entry.actor_id, entry.reason)
        self._outbox(
            "hcam.investigation.timeline.entry-appended.v1",
            entry.timeline_id,
            entry.department,
            {"entry_id": entry.entry_id, "revision": row.revision},
            entry.temporal.recorded_at,
        )
        self.session.flush()
        return contract, False

    def update_timeline_state(
        self,
        timeline_id: str,
        department: str,
        *,
        expected_revision: int,
        actor_id: str,
        reason: str,
        recorded_at: datetime,
        lifecycle: str | None = None,
        disposition: str | None = None,
        canonical_timeline_id: str | None = None,
    ) -> InvestigationTimelineV2:
        row = self.timeline(timeline_id)
        if row is None or row.department != department:
            raise KeyError("timeline was not found")
        if row.revision != expected_revision:
            raise ValueError("timeline revision does not match")
        if lifecycle is not None:
            row.lifecycle = lifecycle
        if disposition is not None:
            row.disposition = disposition
        if canonical_timeline_id is not None:
            row.canonical_timeline_id = canonical_timeline_id
        row.revision += 1
        row.updated_at = recorded_at
        row.content_digest = digest(
            {
                "prior": row.content_digest,
                "lifecycle": row.lifecycle,
                "disposition": row.disposition,
                "canonical_timeline_id": row.canonical_timeline_id,
                "revision": row.revision,
            }
        )
        contract = timeline_contract(row)
        self._add_revision(contract, actor_id, reason)
        self._outbox(
            "hcam.investigation.timeline.state-revised.v1",
            timeline_id,
            department,
            {
                "revision": row.revision,
                "lifecycle": row.lifecycle,
                "disposition": row.disposition,
            },
            recorded_at,
        )
        self.session.flush()
        return contract

    def entries(self, timeline_id: str) -> list[TimelineEntryV2]:
        rows = self.session.scalars(
            select(InvestigationTimelineEntryRecord)
            .where(InvestigationTimelineEntryRecord.timeline_id == timeline_id)
            .order_by(InvestigationTimelineEntryRecord.sequence)
        )
        return [TimelineEntryV2.model_validate(row.payload) for row in rows]

    def add_evidence(self, reference: EvidenceReferenceV2) -> tuple[EvidenceReferenceV2, bool]:
        existing = self.session.get(InvestigationEvidenceReferenceRecord, reference.reference_id)
        if existing is not None:
            stored = EvidenceReferenceV2.model_validate(existing.payload)
            if stored != reference:
                raise ValueError("evidence reference identifier collision")
            return stored, True
        self._require_timeline_scope(reference.timeline_id, reference.department)
        self.session.add(
            InvestigationEvidenceReferenceRecord(
                reference_id=reference.reference_id,
                timeline_id=reference.timeline_id,
                department=reference.department,
                source_system_ref=reference.source_system_ref,
                source_object_ref=reference.source_object_ref,
                source_version=reference.source_version,
                content_digest=reference.content_digest,
                canonicalization_profile=reference.canonicalization_profile,
                classification=reference.classification,
                source_payload_retained=False,
                locator_retained=False,
                payload=reference.model_dump(mode="json"),
                registered_at=reference.registered_at,
            )
        )
        self._outbox(
            "hcam.investigation.evidence.reference-registered.v1",
            reference.reference_id,
            reference.department,
            {"timeline_id": reference.timeline_id},
            reference.registered_at,
        )
        self.session.flush()
        return reference, False

    def evidence(self, reference_id: str) -> EvidenceReferenceV2 | None:
        row = self.session.get(InvestigationEvidenceReferenceRecord, reference_id)
        return EvidenceReferenceV2.model_validate(row.payload) if row is not None else None

    def evidence_for_timeline(self, timeline_id: str) -> list[EvidenceReferenceV2]:
        rows = self.session.scalars(
            select(InvestigationEvidenceReferenceRecord)
            .where(InvestigationEvidenceReferenceRecord.timeline_id == timeline_id)
            .order_by(InvestigationEvidenceReferenceRecord.registered_at)
        )
        return [EvidenceReferenceV2.model_validate(row.payload) for row in rows]

    def add_integrity(self, assessment: IntegrityAssessmentV1) -> IntegrityAssessmentV1:
        existing = self.session.get(
            InvestigationIntegrityAssessmentRecord, assessment.assessment_id
        )
        if existing is not None:
            stored = IntegrityAssessmentV1.model_validate(existing.payload)
            if stored != assessment:
                raise ValueError("integrity assessment identifier collision")
            return stored
        reference = self.evidence(assessment.reference_id)
        if reference is None or reference.timeline_id != assessment.timeline_id or reference.department != assessment.department:
            raise ValueError("integrity assessment scope does not match evidence")
        self.session.add(
            InvestigationIntegrityAssessmentRecord(
                assessment_id=assessment.assessment_id,
                reference_id=assessment.reference_id,
                timeline_id=assessment.timeline_id,
                department=assessment.department,
                state=assessment.state,
                expected_digest=assessment.expected_digest,
                observed_digest=assessment.observed_digest,
                reason_code=assessment.reason_code,
                payload=assessment.model_dump(mode="json"),
                source_payload_retained=False,
                assessed_at=assessment.assessed_at,
            )
        )
        self.session.flush()
        return assessment

    def add_provenance(
        self, bundle: ProvenanceBundleV1, *, recorded_at: datetime
    ) -> ProvenanceBundleV1:
        existing = self.session.get(InvestigationProvenanceBundleRecord, bundle.bundle_id)
        if existing is not None:
            stored = ProvenanceBundleV1.model_validate(existing.payload)
            if stored != bundle or existing.recorded_at != recorded_at:
                raise ValueError("provenance bundle identifier collision")
            return stored
        self._require_timeline_scope(bundle.timeline_id, bundle.department)
        self.session.add(
            InvestigationProvenanceBundleRecord(
                bundle_id=bundle.bundle_id,
                timeline_id=bundle.timeline_id,
                department=bundle.department,
                bundle_digest=bundle.bundle_digest,
                completeness=bundle.completeness,
                node_count=len(bundle.nodes),
                edge_count=len(bundle.edges),
                payload=bundle.model_dump(mode="json"),
                recorded_at=recorded_at,
            )
        )
        self.session.flush()
        return bundle

    def add_correction(
        self, correction: CorrectionCommandV1, impacts: list[ImpactRecordV1]
    ) -> tuple[CorrectionCommandV1, bool]:
        existing = self.session.get(InvestigationCorrectionRecord, correction.correction_id)
        if existing is None:
            existing = self.session.scalar(
                select(InvestigationCorrectionRecord).where(
                    InvestigationCorrectionRecord.department == correction.department,
                    InvestigationCorrectionRecord.delivery_id == correction.delivery_id,
                )
            )
        if existing is not None:
            stored = CorrectionCommandV1.model_validate(existing.payload)
            if stored != correction:
                raise ValueError("correction identity is bound to different command material")
            return stored, True
        self._require_timeline_scope(correction.timeline_id, correction.department)
        self.session.add(
            InvestigationCorrectionRecord(
                correction_id=correction.correction_id,
                timeline_id=correction.timeline_id,
                department=correction.department,
                kind=correction.kind,
                target_type=correction.target_type,
                target_ref=correction.target_ref,
                target_version=correction.target_version,
                replacement_ref=correction.replacement_ref,
                delivery_id=correction.delivery_id,
                payload=correction.model_dump(mode="json"),
                recorded_at=correction.recorded_at,
            )
        )
        self.session.flush()
        for impact in impacts:
            self.session.add(
                InvestigationCorrectionImpactRecord(
                    impact_id=impact.impact_id,
                    correction_id=impact.correction_id,
                    timeline_id=impact.timeline_id,
                    department=impact.department,
                    target_type=impact.target_type,
                    target_ref=impact.target_ref,
                    state=impact.state,
                    reason_code=impact.reason_code,
                    recorded_at=impact.recorded_at,
                )
            )
        self.session.add(
            InvestigationImpactJobRecord(
                job_id=stable_id("ijob", correction.correction_id),
                correction_id=correction.correction_id,
                timeline_id=correction.timeline_id,
                department=correction.department,
                state="queued",
                attempt_count=0,
                reason_code="impact.queued",
                created_at=correction.recorded_at,
                updated_at=correction.recorded_at,
            )
        )
        self._outbox(
            "hcam.investigation.correction.recorded.v1",
            correction.correction_id,
            correction.department,
            {"timeline_id": correction.timeline_id, "impact_count": len(impacts)},
            correction.recorded_at,
        )
        self.session.flush()
        return correction, False

    def add_review(self, review: ReviewDecisionV1) -> tuple[ReviewDecisionV1, bool]:
        self._require_timeline_scope(review.timeline_id, review.department)
        existing = self.session.get(InvestigationReviewRecord, review.review_id)
        if existing is not None:
            stored = ReviewDecisionV1.model_validate(existing.payload)
            if stored != review:
                raise ValueError("review identifier collision")
            return stored, True
        history = [
            ReviewDecisionV1.model_validate(row.payload)
            for row in self.session.scalars(
                select(InvestigationReviewRecord)
                .where(
                    InvestigationReviewRecord.timeline_id == review.timeline_id,
                    InvestigationReviewRecord.target_ref == review.target_ref,
                )
                .order_by(InvestigationReviewRecord.revision)
            )
        ]
        latest_review([*history, review])
        self.session.add(
            InvestigationReviewRecord(
                review_id=review.review_id,
                timeline_id=review.timeline_id,
                department=review.department,
                target_ref=review.target_ref,
                decision=review.decision,
                disposition=review.disposition,
                revision=review.revision,
                supersedes_review_id=review.supersedes_review_id,
                evidence_digest=review.evidence_digest,
                payload=review.model_dump(mode="json"),
                recorded_at=review.recorded_at,
            )
        )
        self.session.flush()
        return review, False

    def add_relationship(
        self, relation: RelationshipRevisionV1
    ) -> tuple[RelationshipRevisionV1, bool]:
        self._require_timeline_scope(relation.source_timeline_id, relation.department)
        self._require_timeline_scope(relation.target_timeline_id, relation.department)
        existing = self.session.get(
            InvestigationRelationshipRecord, relation.relationship_id
        )
        if existing is not None:
            stored = RelationshipRevisionV1.model_validate(existing.payload)
            if stored != relation:
                raise ValueError("relationship identifier collision")
            return stored, True
        prior_revisions = list(
            self.session.scalars(
                select(InvestigationRelationshipRecord).where(
                    InvestigationRelationshipRecord.source_timeline_id
                    == relation.source_timeline_id,
                    InvestigationRelationshipRecord.target_timeline_id
                    == relation.target_timeline_id,
                    InvestigationRelationshipRecord.kind == relation.kind,
                )
            )
        )
        expected_revision = max((row.revision for row in prior_revisions), default=0) + 1
        if relation.revision != expected_revision:
            raise ValueError("relationship revision is not next")
        self.session.add(
            InvestigationRelationshipRecord(
                relationship_id=relation.relationship_id,
                department=relation.department,
                source_timeline_id=relation.source_timeline_id,
                target_timeline_id=relation.target_timeline_id,
                kind=relation.kind,
                revision=relation.revision,
                active=relation.active,
                payload=relation.model_dump(mode="json"),
                recorded_at=relation.recorded_at,
            )
        )
        if relation.kind == "merged_into" and relation.active:
            row = self.timeline(relation.source_timeline_id)
            if row is not None:
                row.canonical_timeline_id = relation.target_timeline_id
                row.updated_at = relation.recorded_at
        elif relation.kind == "merged_into":
            row = self.timeline(relation.source_timeline_id)
            if row is not None and row.canonical_timeline_id == relation.target_timeline_id:
                row.canonical_timeline_id = relation.source_timeline_id
                row.updated_at = relation.recorded_at
        self.session.flush()
        return relation, False

    def relationships(self, department: str) -> list[RelationshipRevisionV1]:
        rows = self.session.scalars(
            select(InvestigationRelationshipRecord)
            .where(InvestigationRelationshipRecord.department == department)
            .order_by(InvestigationRelationshipRecord.recorded_at)
        )
        return [RelationshipRevisionV1.model_validate(row.payload) for row in rows]

    def add_hold(self, hold: HoldOverlayV1) -> HoldOverlayV1:
        self._require_timeline_scope(hold.timeline_id, hold.department)
        row_id = stable_id("ihld", hold.hold_ref, hold.revision)
        existing = self.session.get(InvestigationHoldOverlayRecord, row_id)
        if existing is not None:
            stored = HoldOverlayV1.model_validate(existing.payload)
            if stored != hold:
                raise ValueError("hold revision identifier collision")
            return stored
        prior_revisions = list(
            self.session.scalars(
                select(InvestigationHoldOverlayRecord)
                .where(InvestigationHoldOverlayRecord.hold_ref == hold.hold_ref)
                .order_by(InvestigationHoldOverlayRecord.revision)
            )
        )
        if hold.revision != len(prior_revisions) + 1:
            raise ValueError("hold revision is not next")
        if prior_revisions:
            previous = HoldOverlayV1.model_validate(prior_revisions[-1].payload)
            if (
                previous.timeline_id != hold.timeline_id
                or previous.department != hold.department
                or previous.scope_digest != hold.scope_digest
                or previous.authority_ref != hold.authority_ref
            ):
                raise ValueError("hold identity or scope cannot change between revisions")
        self.session.add(
            InvestigationHoldOverlayRecord(
                row_id=row_id,
                hold_ref=hold.hold_ref,
                timeline_id=hold.timeline_id,
                department=hold.department,
                state=hold.state,
                revision=hold.revision,
                grants_access=False,
                effective_runtime_action=False,
                payload=hold.model_dump(mode="json"),
                recorded_at=hold.recorded_at,
            )
        )
        self.session.flush()
        return hold

    def holds(self, timeline_id: str) -> list[HoldOverlayV1]:
        rows = self.session.scalars(
            select(InvestigationHoldOverlayRecord)
            .where(InvestigationHoldOverlayRecord.timeline_id == timeline_id)
            .order_by(InvestigationHoldOverlayRecord.recorded_at)
        )
        return [HoldOverlayV1.model_validate(row.payload) for row in rows]

    def add_retention(self, evaluation: RetentionEvaluationV1) -> RetentionEvaluationV1:
        self._require_timeline_scope(evaluation.timeline_id, evaluation.department)
        existing = self.session.get(
            InvestigationRetentionEvaluationRecord, evaluation.evaluation_id
        )
        if existing is not None:
            stored = RetentionEvaluationV1.model_validate(existing.payload)
            if stored != evaluation:
                raise ValueError("retention evaluation identifier collision")
            return stored
        self.session.add(
            InvestigationRetentionEvaluationRecord(
                evaluation_id=evaluation.evaluation_id,
                timeline_id=evaluation.timeline_id,
                department=evaluation.department,
                policy_ref=evaluation.policy.policy_ref,
                outcome=evaluation.outcome,
                payload=evaluation.model_dump(mode="json"),
                advisory_only=True,
                legal_period_selected=False,
                evaluated_at=evaluation.evaluated_at,
            )
        )
        self.session.flush()
        return evaluation

    def retention(self, evaluation_id: str) -> RetentionEvaluationV1 | None:
        row = self.session.get(InvestigationRetentionEvaluationRecord, evaluation_id)
        return RetentionEvaluationV1.model_validate(row.payload) if row is not None else None

    def add_deletion_receipts(self, receipts: list[DeletionReceiptV1]) -> list[DeletionReceiptV1]:
        stored_receipts: list[DeletionReceiptV1] = []
        for receipt in receipts:
            existing = self.session.get(
                InvestigationDeletionReceiptRecord, receipt.receipt_id
            )
            if existing is not None:
                stored = DeletionReceiptV1.model_validate(existing.payload)
                if stored != receipt:
                    raise ValueError("deletion receipt identifier collision")
                stored_receipts.append(stored)
                continue
            self.session.add(
                InvestigationDeletionReceiptRecord(
                    receipt_id=receipt.receipt_id,
                    intent_id=receipt.intent_id,
                    timeline_id=receipt.timeline_id,
                    department=receipt.department,
                    target_ref=receipt.target_ref,
                    outcome=receipt.outcome,
                    payload=receipt.model_dump(mode="json"),
                    universal_deletion_proven=False,
                    external_action_executed=False,
                    recorded_at=receipt.recorded_at,
                )
            )
            stored_receipts.append(receipt)
        self.session.flush()
        return stored_receipts

    def add_export(self, manifest: ExportManifestV1) -> ExportManifestV1:
        self._require_timeline_scope(manifest.timeline_id, manifest.department)
        existing = self.session.get(InvestigationExportManifestRecord, manifest.manifest_id)
        if existing is not None:
            stored = ExportManifestV1.model_validate(existing.payload)
            if stored != manifest:
                raise ValueError("export manifest identifier collision")
            return stored
        self.session.add(
            InvestigationExportManifestRecord(
                manifest_id=manifest.manifest_id,
                timeline_id=manifest.timeline_id,
                department=manifest.department,
                purpose_code=manifest.purpose_code,
                recipient_class=manifest.recipient_class,
                completeness=manifest.completeness,
                manifest_digest=manifest.manifest_digest,
                payload=manifest.model_dump(mode="json"),
                source_payload_included=False,
                prepared_at=manifest.prepared_at,
            )
        )
        self.session.flush()
        return manifest

    def claim_impact_job(
        self, worker_id: str, *, now: datetime | None = None
    ) -> InvestigationImpactJobRecord | None:
        current = now or _now()
        statement = (
            select(InvestigationImpactJobRecord)
            .where(
                (InvestigationImpactJobRecord.state == "queued")
                | (
                    (InvestigationImpactJobRecord.state == "leased")
                    & (InvestigationImpactJobRecord.lease_until <= current)
                )
            )
            .order_by(InvestigationImpactJobRecord.created_at)
            .limit(1)
        )
        if self.session.get_bind().dialect.name == "postgresql":
            statement = statement.with_for_update(skip_locked=True)
        row = self.session.scalar(statement)
        if row is None:
            return None
        row.state = "leased"
        row.attempt_count += 1
        row.lease_owner = worker_id
        row.lease_until = current + timedelta(seconds=90)
        row.reason_code = "impact.leased"
        row.updated_at = current
        self.session.flush()
        return row

    def complete_impact_job(
        self,
        row: InvestigationImpactJobRecord,
        *,
        worker_id: str,
        now: datetime | None = None,
    ) -> None:
        if row.state != "leased" or row.lease_owner != worker_id:
            raise ValueError("worker does not own the impact-job lease")
        current = now or _now()
        impacts = list(
            self.session.scalars(
                select(InvestigationCorrectionImpactRecord).where(
                    InvestigationCorrectionImpactRecord.correction_id == row.correction_id
                )
            )
        )
        for impact in impacts:
            impact.state = "applied"
            impact.reason_code = "correction.impact_applied"
        row.state = "succeeded"
        row.reason_code = "impact.complete"
        row.lease_owner = None
        row.lease_until = None
        row.updated_at = current
        self._outbox(
            "hcam.investigation.correction.propagated.v1",
            row.correction_id,
            row.department,
            {"impact_count": len(impacts), "state": "complete"},
            current,
        )
        self.session.flush()

    def _require_timeline_scope(self, timeline_id: str, department: str) -> None:
        row = self.timeline(timeline_id)
        if row is None or row.department != department:
            raise KeyError("timeline was not found")

    def _receipt(self, department: str, delivery_id: str) -> InvestigationCommandReceipt | None:
        return self.session.scalar(
            select(InvestigationCommandReceipt).where(
                InvestigationCommandReceipt.department == department,
                InvestigationCommandReceipt.delivery_id == delivery_id,
            )
        )

    def _add_receipt(
        self,
        *,
        timeline_id: str,
        department: str,
        delivery_id: str,
        command_type: str,
        command_digest: str,
        response_ref: str,
        recorded_at: datetime,
    ) -> None:
        self.session.add(
            InvestigationCommandReceipt(
                receipt_id=stable_id("icmd", department, delivery_id),
                timeline_id=timeline_id,
                department=department,
                delivery_id=delivery_id,
                command_type=command_type,
                command_digest=command_digest,
                response_ref=response_ref,
                recorded_at=recorded_at,
            )
        )

    def _add_revision(
        self, timeline: InvestigationTimelineV2, actor_id: str, reason: str
    ) -> None:
        self.session.add(
            InvestigationTimelineRevision(
                revision_id=stable_id("itvr", timeline.timeline_id, timeline.revision),
                timeline_id=timeline.timeline_id,
                department=timeline.department,
                revision=timeline.revision,
                lifecycle=timeline.lifecycle,
                disposition=timeline.disposition,
                entry_count=timeline.entry_count,
                content_digest=timeline.content_digest,
                payload=timeline.model_dump(mode="json"),
                actor_id=actor_id,
                reason=reason,
                recorded_at=timeline.updated_at,
            )
        )

    def _outbox(
        self,
        event_type: str,
        aggregate_id: str,
        department: str,
        payload: dict[str, Any],
        occurred_at: datetime,
    ) -> None:
        self.session.add(
            InvestigationOutbox(
                event_id=stable_id(
                    "iout",
                    event_type,
                    aggregate_id,
                    occurred_at.isoformat(),
                    digest(payload),
                ),
                event_type=event_type,
                aggregate_id=aggregate_id,
                department=department,
                payload=payload,
                occurred_at=occurred_at,
            )
        )


def timeline_contract(row: InvestigationTimelineRecord) -> InvestigationTimelineV2:
    return InvestigationTimelineV2(
        timeline_id=row.timeline_id,
        department=row.department,
        title=row.title,
        purpose_code=row.purpose_code,
        lifecycle=row.lifecycle,
        disposition=row.disposition,
        revision=row.revision,
        entry_count=row.entry_count,
        canonical_timeline_id=row.canonical_timeline_id,
        content_digest=row.content_digest,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
