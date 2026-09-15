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
from hcam.intelligence.integrations.canonical import stable_id
from hcam.intelligence.integrations.contracts import (
    AttemptReceiptV1,
    CandidateSetV1,
    CatalogueSnapshotV1,
    CompiledQueryPlanV1,
    ControlRevisionV1,
    ProviderManifestV2,
    QueryIntentV1,
    QueryJobV1,
    ReviewHandoffV1,
)


def _now() -> datetime:
    return datetime.now(UTC)


class ReferenceProviderVersion(Base):
    __tablename__ = "reference_provider_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('validated_generated', 'approved_disabled', 'suspended', 'revoked', 'retired')",
            name="ck_reference_provider_version_status",
        ),
        CheckConstraint("generated_only = true", name="ck_reference_provider_version_generated"),
        CheckConstraint("operational = false", name="ck_reference_provider_version_nonoperational"),
        UniqueConstraint("department", "provider_id", "version", name="uq_reference_provider_version"),
        Index("ix_reference_provider_version_scope", "department", "status", "updated_at"),
    )

    provider_version_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(37), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_key: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    manifest_digest: Mapped[str] = mapped_column(String(71), nullable=False, unique=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=_now)

    __mapper_args__ = {"version_id_col": version_id}


class ReferenceCatalogueSnapshot(Base):
    __tablename__ = "reference_catalogue_snapshots"
    __table_args__ = (
        CheckConstraint("completeness IN ('complete', 'partial')", name="ck_reference_catalogue_completeness"),
        CheckConstraint("generated_only = true", name="ck_reference_catalogue_generated"),
        CheckConstraint("raw_response_retained = false", name="ck_reference_catalogue_no_raw"),
        UniqueConstraint("provider_version_id", "fingerprint", name="uq_reference_catalogue_fingerprint"),
        Index("ix_reference_catalogue_scope", "department", "provider_version_id", "last_observed_at"),
    )

    snapshot_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    provider_version_id: Mapped[str] = mapped_column(
        ForeignKey("reference_provider_versions.provider_version_id", ondelete="RESTRICT"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(71), nullable=False)
    completeness: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    first_observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    last_observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    stale_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    raw_response_retained: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ReferenceCatalogueRecord(Base):
    __tablename__ = "reference_catalogue_records"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_reference_catalogue_record_generated"),
        UniqueConstraint("snapshot_id", "record_id", name="uq_reference_catalogue_record"),
        Index("ix_reference_catalogue_record_scope", "department", "snapshot_id"),
    )

    row_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("reference_catalogue_snapshots.snapshot_id", ondelete="CASCADE"),
        nullable=False,
    )
    record_id: Mapped[str] = mapped_column(String(37), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    record_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    fields: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ReferenceQueryJob(Base):
    __tablename__ = "reference_query_jobs"
    __table_args__ = (
        CheckConstraint(
            "state IN ('queued', 'leased', 'succeeded', 'failed', 'cancelled', 'quarantined')",
            name="ck_reference_query_job_state",
        ),
        CheckConstraint("attempt_count >= 0 AND attempt_count <= 3", name="ck_reference_query_job_attempts"),
        CheckConstraint("generated_only = true", name="ck_reference_query_job_generated"),
        CheckConstraint("operational = false", name="ck_reference_query_job_nonoperational"),
        UniqueConstraint("department", "query_id", name="uq_reference_query_id"),
        UniqueConstraint("department", "semantic_key", name="uq_reference_query_semantic"),
        UniqueConstraint("department", "delivery_key", name="uq_reference_query_delivery"),
        Index("ix_reference_query_job_due", "department", "state", "created_at"),
    )

    job_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    query_id: Mapped[str] = mapped_column(String(36), nullable=False)
    provider_version_id: Mapped[str] = mapped_column(
        ForeignKey("reference_provider_versions.provider_version_id", ondelete="RESTRICT"),
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    semantic_key: Mapped[str] = mapped_column(String(71), nullable=False)
    delivery_key: Mapped[str] = mapped_column(String(71), nullable=False)
    result_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    intent_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    plan_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __mapper_args__ = {"version_id_col": version_id}


class ReferenceQueryAttempt(Base):
    __tablename__ = "reference_query_attempts"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('succeeded', 'transient_failure', 'permanent_failure', 'revoked', 'stale')",
            name="ck_reference_query_attempt_outcome",
        ),
        CheckConstraint("raw_response_retained = false", name="ck_reference_query_attempt_no_raw"),
        CheckConstraint("generated_only = true", name="ck_reference_query_attempt_generated"),
        Index("ix_reference_query_attempt_scope", "department", "job_id", "recorded_at"),
    )

    attempt_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("reference_query_jobs.job_id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_digest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    raw_response_retained: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class ReferenceCandidateSet(Base):
    __tablename__ = "reference_candidate_sets"
    __table_args__ = (
        CheckConstraint("identity_state = 'not_established'", name="ck_reference_candidate_identity"),
        CheckConstraint("mandatory_review = true", name="ck_reference_candidate_review"),
        CheckConstraint("generated_only = true", name="ck_reference_candidate_generated"),
        CheckConstraint("operational = false", name="ck_reference_candidate_nonoperational"),
        Index("ix_reference_candidate_scope", "department", "query_id", "created_at"),
    )

    candidate_set_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    query_id: Mapped[str] = mapped_column(String(36), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    candidate_set_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    identity_state: Mapped[str] = mapped_column(String(32), nullable=False)
    mandatory_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=_now)


class ReferenceReviewHandoff(Base):
    __tablename__ = "reference_review_handoffs"
    __table_args__ = (
        CheckConstraint("authority_class = 'mandatory_review'", name="ck_reference_review_authority"),
        CheckConstraint("state = 'pending_review'", name="ck_reference_review_state"),
        CheckConstraint("generated_only = true", name="ck_reference_review_generated"),
        CheckConstraint("operational = false", name="ck_reference_review_nonoperational"),
        Index("ix_reference_review_scope", "department", "created_at"),
    )

    handoff_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    candidate_set_id: Mapped[str] = mapped_column(
        ForeignKey("reference_candidate_sets.candidate_set_id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    authority_class: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class ReferenceControlRevision(Base):
    __tablename__ = "reference_control_revisions"
    __table_args__ = (
        CheckConstraint("state IN ('enabled_generated', 'suspended', 'revoked')", name="ck_reference_control_state"),
        CheckConstraint("generated_only = true", name="ck_reference_control_generated"),
        UniqueConstraint("department", "scope", "scope_key", "version", name="uq_reference_control_version"),
        Index("ix_reference_control_scope", "department", "scope", "scope_key", "version"),
    )

    revision_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class ReferenceCircuitState(Base):
    __tablename__ = "reference_circuit_states"
    __table_args__ = (
        CheckConstraint("state IN ('closed', 'open', 'half_open', 'revoked')", name="ck_reference_circuit_state"),
        CheckConstraint("generated_only = true", name="ck_reference_circuit_generated"),
        UniqueConstraint("department", "provider_version_id", name="uq_reference_circuit_provider"),
        Index("ix_reference_circuit_scope", "department", "state", "updated_at"),
    )

    circuit_id: Mapped[str] = mapped_column(String(37), primary_key=True)
    provider_version_id: Mapped[str] = mapped_column(
        ForeignKey("reference_provider_versions.provider_version_id", ondelete="CASCADE"), nullable=False
    )
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    generated_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=_now)

    __mapper_args__ = {"version_id_col": version_id}


class ReferenceIntegrationOutbox(Base):
    __tablename__ = "reference_integration_outbox"
    __table_args__ = (
        CheckConstraint("generated_only = true", name="ck_reference_outbox_generated"),
        CheckConstraint("operational = false", name="ck_reference_outbox_nonoperational"),
        Index("ix_reference_outbox_pending", "department", "published_at", "occurred_at"),
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


def job_contract(row: ReferenceQueryJob) -> QueryJobV1:
    return QueryJobV1(
        job_id=row.job_id,
        query_id=row.query_id,
        department=row.department,
        state=row.state,
        attempt_count=row.attempt_count,
        lease_owner=row.lease_owner,
        lease_until=row.lease_until,
        reason_code=row.reason_code,
        plan_digest=row.plan_digest,
        semantic_key=row.semantic_key,
        delivery_key=row.delivery_key,
        result_digest=row.result_digest,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class IntegrationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_manifest(self, manifest: ProviderManifestV2, *, now: datetime | None = None) -> ReferenceProviderVersion:
        current = now or _now()
        row = ReferenceProviderVersion(
            provider_version_id=manifest.provider_version_id,
            provider_id=manifest.provider_id,
            department=manifest.department,
            provider_key=manifest.provider_key,
            version=manifest.version,
            status=manifest.status,
            manifest_digest=manifest.manifest_digest,
            payload=manifest.model_dump(mode="json"),
            created_at=current,
            updated_at=current,
        )
        self.session.add(row)
        self._outbox("hcam.reference.provider.created.v1", row.provider_version_id, row.department, {"manifest_digest": row.manifest_digest}, current)
        self.session.flush()
        return row

    def manifest(self, provider_version_id: str) -> ProviderManifestV2 | None:
        row = self.session.get(ReferenceProviderVersion, provider_version_id)
        return ProviderManifestV2.model_validate(row.payload) if row is not None else None

    def list_manifests(self, departments: frozenset[str] | None) -> list[ProviderManifestV2]:
        statement = select(ReferenceProviderVersion).order_by(
            ReferenceProviderVersion.department,
            ReferenceProviderVersion.provider_key,
            ReferenceProviderVersion.version,
        )
        if departments is not None:
            statement = statement.where(ReferenceProviderVersion.department.in_(departments))
        return [
            ProviderManifestV2.model_validate(row.payload)
            for row in self.session.scalars(statement)
        ]

    def add_snapshot(self, snapshot: CatalogueSnapshotV1) -> tuple[ReferenceCatalogueSnapshot, bool]:
        existing = self.session.scalar(
            select(ReferenceCatalogueSnapshot).where(
                ReferenceCatalogueSnapshot.provider_version_id == snapshot.provider_version_id,
                ReferenceCatalogueSnapshot.fingerprint == snapshot.fingerprint,
            )
        )
        if existing is not None:
            existing.last_observed_at = snapshot.last_observed_at
            existing.observed_at = snapshot.observed_at
            existing.stale_at = snapshot.stale_at
            self.session.flush()
            return existing, False
        row = ReferenceCatalogueSnapshot(
            snapshot_id=snapshot.snapshot_id,
            provider_version_id=snapshot.provider_version_id,
            department=snapshot.department,
            fingerprint=snapshot.fingerprint,
            completeness=snapshot.completeness,
            payload=snapshot.model_dump(mode="json", exclude={"records"}),
            first_observed_at=snapshot.first_observed_at,
            last_observed_at=snapshot.last_observed_at,
            observed_at=snapshot.observed_at,
            stale_at=snapshot.stale_at,
        )
        self.session.add(row)
        self.session.flush()
        for record in snapshot.records:
            self.session.add(
                ReferenceCatalogueRecord(
                    row_id=stable_id("grec", snapshot.snapshot_id, record.record_id),
                    snapshot_id=snapshot.snapshot_id,
                    record_id=record.record_id,
                    department=snapshot.department,
                    record_digest=record.record_digest,
                    fields=record.fields,
                )
            )
        self._outbox("hcam.reference.catalogue.changed.v1", snapshot.snapshot_id, snapshot.department, {"fingerprint": snapshot.fingerprint}, snapshot.observed_at)
        self.session.flush()
        return row, True

    def add_job(self, intent: QueryIntentV1, plan: CompiledQueryPlanV1, *, now: datetime | None = None) -> tuple[ReferenceQueryJob, bool]:
        existing = self.session.scalar(
            select(ReferenceQueryJob).where(
                ReferenceQueryJob.department == intent.department,
                ReferenceQueryJob.delivery_key == plan.delivery_key,
            )
        )
        if existing is not None:
            if existing.semantic_key != plan.semantic_key:
                raise ValueError("delivery identity contains different material")
            return existing, True
        semantic = self.session.scalar(
            select(ReferenceQueryJob).where(
                ReferenceQueryJob.department == intent.department,
                ReferenceQueryJob.semantic_key == plan.semantic_key,
            )
        )
        if semantic is not None:
            return semantic, True
        current = now or _now()
        row = ReferenceQueryJob(
            job_id=stable_id("rjob", intent.department, plan.semantic_key),
            query_id=intent.query_id,
            provider_version_id=plan.provider_version_id,
            department=intent.department,
            state="queued",
            attempt_count=0,
            reason_code="query.queued",
            plan_digest=plan.plan_digest,
            semantic_key=plan.semantic_key,
            delivery_key=plan.delivery_key,
            intent_payload=intent.model_dump(mode="json"),
            plan_payload=plan.model_dump(mode="json"),
            created_at=current,
            updated_at=current,
        )
        self.session.add(row)
        self._outbox("hcam.reference.query.queued.v1", row.job_id, row.department, {"plan_digest": row.plan_digest}, current)
        self.session.flush()
        return row, False

    def job(self, job_id: str) -> ReferenceQueryJob | None:
        return self.session.get(ReferenceQueryJob, job_id)

    def candidate_set(self, candidate_set_id: str) -> CandidateSetV1 | None:
        row = self.session.get(ReferenceCandidateSet, candidate_set_id)
        return CandidateSetV1.model_validate(row.payload) if row is not None else None

    def candidate_set_for_query(self, query_id: str) -> CandidateSetV1 | None:
        row = self.session.scalar(
            select(ReferenceCandidateSet)
            .where(ReferenceCandidateSet.query_id == query_id)
            .order_by(ReferenceCandidateSet.created_at.desc())
            .limit(1)
        )
        return CandidateSetV1.model_validate(row.payload) if row is not None else None

    def latest_control(
        self, department: str, scope: str, scope_key: str
    ) -> ControlRevisionV1 | None:
        row = self.session.scalar(
            select(ReferenceControlRevision)
            .where(
                ReferenceControlRevision.department == department,
                ReferenceControlRevision.scope == scope,
                ReferenceControlRevision.scope_key == scope_key,
            )
            .order_by(ReferenceControlRevision.version.desc())
            .limit(1)
        )
        return _control_contract(row) if row is not None else None

    def list_controls(
        self, departments: frozenset[str] | None
    ) -> list[ControlRevisionV1]:
        statement = select(ReferenceControlRevision).order_by(
            ReferenceControlRevision.department,
            ReferenceControlRevision.scope,
            ReferenceControlRevision.scope_key,
            ReferenceControlRevision.version,
        )
        if departments is not None:
            statement = statement.where(ReferenceControlRevision.department.in_(departments))
        return [_control_contract(row) for row in self.session.scalars(statement)]

    def controls_allow(self, manifest: ProviderManifestV2, intent: QueryIntentV1) -> bool:
        checks = (
            ("organization", "generated.reference"),
            ("department", manifest.department),
            ("provider", manifest.provider_version_id),
            ("operation", intent.operation_id),
            ("purpose", intent.purpose_code),
            ("auth_profile", manifest.auth_profile.profile_id),
        )
        return all(
            (revision := self.latest_control(manifest.department, scope, scope_key))
            is None
            or revision.state == "enabled_generated"
            for scope, scope_key in checks
        )

    def circuit_allows(self, provider_version_id: str, department: str) -> bool:
        row = self.session.scalar(
            select(ReferenceCircuitState).where(
                ReferenceCircuitState.provider_version_id == provider_version_id,
                ReferenceCircuitState.department == department,
            )
        )
        return row is None or row.state in {"closed", "half_open"}

    def record_circuit_outcome(
        self,
        *,
        provider_version_id: str,
        department: str,
        succeeded: bool,
        revoked: bool = False,
        now: datetime | None = None,
    ) -> ReferenceCircuitState:
        current = now or _now()
        row = self.session.scalar(
            select(ReferenceCircuitState).where(
                ReferenceCircuitState.provider_version_id == provider_version_id,
                ReferenceCircuitState.department == department,
            )
        )
        if row is None:
            row = ReferenceCircuitState(
                circuit_id=stable_id("rcir", department, provider_version_id),
                provider_version_id=provider_version_id,
                department=department,
                state="closed",
                failure_count=0,
                updated_at=current,
            )
            self.session.add(row)
        if revoked:
            row.state = "revoked"
        elif succeeded:
            row.state = "closed"
            row.failure_count = 0
        else:
            row.failure_count += 1
            row.state = "open" if row.failure_count >= 3 else "closed"
        row.updated_at = current
        self._outbox(
            "hcam.reference.circuit.changed.v1",
            row.circuit_id,
            department,
            {"state": row.state, "failure_count": row.failure_count},
            current,
        )
        self.session.flush()
        return row

    def claim_next(self, worker_id: str, *, concurrent_workers: bool = False, now: datetime | None = None) -> ReferenceQueryJob | None:
        if self.session.bind is not None and self.session.bind.dialect.name == "sqlite" and concurrent_workers:
            raise RuntimeError("SQLite reference integration workers must run singly")
        current = now or _now()
        statement = (
            select(ReferenceQueryJob)
            .where(
                (ReferenceQueryJob.state == "queued")
                | ((ReferenceQueryJob.state == "leased") & (ReferenceQueryJob.lease_until <= current))
            )
            .order_by(ReferenceQueryJob.created_at, ReferenceQueryJob.job_id)
            .limit(1)
        )
        if self.session.bind is not None and self.session.bind.dialect.name == "postgresql":
            statement = statement.with_for_update(skip_locked=True)
        row = self.session.scalar(statement)
        if row is None:
            return None
        row.state = "leased"
        row.attempt_count += 1
        row.lease_owner = worker_id
        row.lease_until = current + timedelta(seconds=90)
        row.reason_code = "query.leased"
        row.updated_at = current
        self.session.flush()
        return row

    def complete_job(self, row: ReferenceQueryJob, *, worker_id: str, result_digest: str, now: datetime | None = None) -> None:
        if row.state != "leased" or row.lease_owner != worker_id:
            raise ValueError("worker does not own the query lease")
        current = now or _now()
        row.state = "succeeded"
        row.reason_code = "query.succeeded"
        row.result_digest = result_digest
        row.lease_owner = None
        row.lease_until = None
        row.updated_at = current
        self._outbox("hcam.reference.query.completed.v1", row.job_id, row.department, {"result_digest": result_digest}, current)
        self.session.flush()

    def fail_job(
        self,
        row: ReferenceQueryJob,
        *,
        worker_id: str,
        transient: bool,
        reason_code: str,
        now: datetime | None = None,
    ) -> None:
        if row.state != "leased" or row.lease_owner != worker_id:
            raise ValueError("worker does not own the query lease")
        current = now or _now()
        retry = transient and row.attempt_count < 3
        row.state = "queued" if retry else "failed"
        row.reason_code = "query.retry_queued" if retry else reason_code
        row.lease_owner = None
        row.lease_until = None
        row.updated_at = current
        event = "hcam.reference.query.retry.v1" if retry else "hcam.reference.query.failed.v1"
        self._outbox(
            event,
            row.job_id,
            row.department,
            {"attempt_count": row.attempt_count, "reason_code": row.reason_code},
            current,
        )
        self.session.flush()

    def quarantine_job(
        self,
        row: ReferenceQueryJob,
        *,
        worker_id: str,
        reason_code: str = "query.revoked",
        now: datetime | None = None,
    ) -> None:
        if row.state != "leased" or row.lease_owner != worker_id:
            raise ValueError("worker does not own the query lease")
        current = now or _now()
        row.state = "quarantined"
        row.reason_code = reason_code
        row.lease_owner = None
        row.lease_until = None
        row.updated_at = current
        self._outbox(
            "hcam.reference.query.quarantined.v1",
            row.job_id,
            row.department,
            {"reason_code": reason_code},
            current,
        )
        self.session.flush()

    def add_attempt(
        self, receipt: AttemptReceiptV1, *, department: str
    ) -> ReferenceQueryAttempt:
        row = ReferenceQueryAttempt(
            attempt_id=receipt.attempt_id,
            job_id=receipt.job_id,
            department=department,
            attempt_number=self.session.scalar(
                select(ReferenceQueryJob.attempt_count).where(
                    ReferenceQueryJob.job_id == receipt.job_id
                )
            ),
            outcome=receipt.outcome,
            reason_code=receipt.reason_code,
            normalized_digest=receipt.normalized_digest,
            raw_response_retained=False,
            generated_only=True,
            recorded_at=receipt.recorded_at,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def cancel_job(
        self,
        row: ReferenceQueryJob,
        *,
        expected_version: int,
        now: datetime | None = None,
    ) -> None:
        if row.version_id != expected_version:
            raise ValueError("query job version does not match")
        if row.state not in {"queued", "leased"}:
            raise ValueError("only active query jobs can be cancelled")
        row.state = "cancelled"
        row.reason_code = "query.cancelled"
        row.lease_owner = None
        row.lease_until = None
        row.updated_at = now or _now()
        self._outbox(
            "hcam.reference.query.cancelled.v1",
            row.job_id,
            row.department,
            {"version": row.version_id + 1},
            row.updated_at,
        )
        self.session.flush()

    def add_candidate_set(self, candidate_set: CandidateSetV1, *, now: datetime | None = None) -> ReferenceCandidateSet:
        row = ReferenceCandidateSet(
            candidate_set_id=candidate_set.candidate_set_id,
            query_id=candidate_set.query_id,
            department=candidate_set.department,
            outcome=candidate_set.outcome,
            candidate_set_digest=candidate_set.candidate_set_digest,
            identity_state=candidate_set.identity_state,
            mandatory_review=candidate_set.mandatory_review,
            payload=candidate_set.model_dump(mode="json"),
            created_at=now or _now(),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def add_review_handoff(self, handoff: ReviewHandoffV1) -> ReferenceReviewHandoff:
        row = ReferenceReviewHandoff(
            handoff_id=handoff.handoff_id,
            candidate_set_id=handoff.candidate_set_id,
            department=handoff.department,
            authority_class=handoff.authority_class,
            state=handoff.state,
            evidence_digest=handoff.evidence_digest,
            payload=handoff.model_dump(mode="json"),
            created_at=handoff.created_at,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def add_control_revision(self, revision: ControlRevisionV1) -> ReferenceControlRevision:
        row = ReferenceControlRevision(**revision.model_dump(mode="python"))
        self.session.add(row)
        self._outbox("hcam.reference.control.changed.v1", revision.revision_id, revision.department, {"scope": revision.scope, "state": revision.state, "version": revision.version}, revision.recorded_at)
        self.session.flush()
        return row

    def _outbox(self, event_type: str, aggregate_id: str, department: str, payload: dict[str, Any], occurred_at: datetime) -> None:
        self.session.add(
            ReferenceIntegrationOutbox(
                event_id=stable_id("rout", event_type, aggregate_id, occurred_at.isoformat()),
                event_type=event_type,
                aggregate_id=aggregate_id,
                department=department,
                payload=payload,
                occurred_at=occurred_at,
            )
        )


def _control_contract(row: ReferenceControlRevision) -> ControlRevisionV1:
    return ControlRevisionV1(
        revision_id=row.revision_id,
        department=row.department,
        scope=row.scope,
        scope_key=row.scope_key,
        state=row.state,
        version=row.version,
        actor_id=row.actor_id,
        reason=row.reason,
        recorded_at=row.recorded_at,
    )
