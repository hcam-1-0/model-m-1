from __future__ import annotations

import hashlib
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from datetime import timedelta

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from hcam.intelligence.canonical import canonical_json, canonical_sha256
from hcam.intelligence.correlation.bounds import MAX_CORRELATION_DOCUMENT_BYTES
from hcam.intelligence.correlation.contracts import (
    CorrelationBatchResultV1,
    CorrelationHypothesisV2,
    HypothesisRevisionV1,
)
from hcam.intelligence.guardrails import validate_intelligence_document
from hcam.intelligence.models import (
    CorrelationEventReceipt,
    CorrelationHypothesis,
    CorrelationHypothesisRevision,
    CorrelationLaneResult,
    CorrelationPartitionCheckpoint,
    CorrelationRun,
    CorrelationWindowEvent,
    HypothesisEvidenceReference,
)


class CorrelationPersistenceError(RuntimeError):
    """Raised when a generated correlation batch cannot be stored atomically."""


@dataclass(frozen=True, slots=True)
class CorrelationPersistenceResult:
    run_id: str
    inserted: bool
    hypothesis_count: int


def _identifier(prefix: str, material: str) -> str:
    return prefix + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


class CorrelationPersistence:
    def __init__(self, session: Session) -> None:
        self.session = session

    def store_batch(self, result: CorrelationBatchResultV1) -> CorrelationPersistenceResult:
        departments = {item.department for item in result.receipts}
        departments.update(item.department for item in result.hypotheses)
        departments.update(item.department for item in result.checkpoints)
        if len(departments) != 1:
            raise CorrelationPersistenceError(
                "a correlation batch must contain exactly one department"
            )
        department = next(iter(departments))
        try:
            with self.session.begin():
                existing = self.session.get(CorrelationRun, result.run_id)
                if existing is not None:
                    if existing.result_digest != result.result_digest:
                        raise CorrelationPersistenceError(
                            "stored correlation run digest does not match"
                        )
                    return CorrelationPersistenceResult(
                        run_id=result.run_id,
                        inserted=False,
                        hypothesis_count=len(result.hypotheses),
                    )
                now = datetime.now(UTC)
                watermark = max(
                    (item.watermark_at for item in result.checkpoints),
                    default=None,
                )
                self.session.add(
                    CorrelationRun(
                        run_id=result.run_id,
                        department=department,
                        status="succeeded",
                        execution_scope="generated_event_correlation",
                        reason_code="generated_completed",
                        generated_only=True,
                        profile_id=result.profile_id,
                        profile_version=(
                            result.hypotheses[0].profile_version
                            if result.hypotheses
                            else None
                        ),
                        result_digest=result.result_digest,
                        replay_binding=result.replay_binding.model_dump(mode="json"),
                        input_count=result.input_count,
                        accepted_count=result.accepted_count,
                        duplicate_count=result.duplicate_count,
                        rejected_count=result.rejected_count,
                        attempt_count=0,
                        watermark_at=watermark,
                        created_at=now,
                        updated_at=now,
                    )
                )
                self.session.flush()
                self._store_receipts(result)
                self._store_checkpoints(result, now)
                self._store_hypotheses(result, now)
                self.session.flush()
            return CorrelationPersistenceResult(
                run_id=result.run_id,
                inserted=True,
                hypothesis_count=len(result.hypotheses),
            )
        except IntegrityError as exc:
            raise CorrelationPersistenceError(
                "correlation batch violated a persistence invariant"
            ) from exc

    def claim_next_run(
        self,
        *,
        worker_id: str,
        now: datetime,
        lease_seconds: int = 30,
        sqlite_worker_count: int = 1,
    ) -> CorrelationRun | None:
        if not worker_id or len(worker_id) > 128:
            raise CorrelationPersistenceError("worker identifier is invalid")
        dialect = self.session.get_bind().dialect.name
        if dialect == "sqlite" and sqlite_worker_count != 1:
            raise CorrelationPersistenceError("SQLite correlation requires one worker")
        if not 1 <= lease_seconds <= 90:
            raise CorrelationPersistenceError("worker lease is outside the declared bounds")
        statement = (
            select(CorrelationRun)
            .where(
                or_(
                    CorrelationRun.status == "queued",
                    (
                        (CorrelationRun.status == "running")
                        & (CorrelationRun.lease_until < now)
                    ),
                ),
                CorrelationRun.attempt_count < 3,
            )
            .order_by(CorrelationRun.created_at.asc(), CorrelationRun.run_id.asc())
            .limit(1)
        )
        if dialect == "postgresql":
            statement = statement.with_for_update(skip_locked=True)
        transaction = nullcontext() if self.session.in_transaction() else self.session.begin()
        with transaction:
            row = self.session.scalar(statement)
            if row is None:
                return None
            row.status = "running"
            row.reason_code = "generated_lease_acquired"
            row.attempt_count += 1
            row.lease_owner = worker_id
            row.lease_until = now + timedelta(seconds=lease_seconds)
            row.updated_at = now
            self.session.flush()
            return row

    def append_revision(
        self,
        revised: CorrelationHypothesisV2,
        revision: HypothesisRevisionV1,
    ) -> bool:
        """Append one generated revision and advance its rebuildable current projection."""

        validate_intelligence_document(
            revised,
            maximum_bytes=MAX_CORRELATION_DOCUMENT_BYTES,
        )
        expected_digest = canonical_sha256(
            revised,
            maximum_bytes=MAX_CORRELATION_DOCUMENT_BYTES,
        )
        if revision.hypothesis_id != revised.hypothesis_id:
            raise CorrelationPersistenceError("revision references another hypothesis")
        if revision.revision != revised.revision:
            raise CorrelationPersistenceError("revision number does not match its snapshot")
        if revision.new_state != revised.state:
            raise CorrelationPersistenceError("revision state does not match its snapshot")
        if revision.snapshot_digest != expected_digest:
            raise CorrelationPersistenceError("revision snapshot digest does not match")
        try:
            with self.session.begin():
                statement = select(CorrelationHypothesis).where(
                    CorrelationHypothesis.hypothesis_id == revised.hypothesis_id
                )
                if self.session.get_bind().dialect.name == "postgresql":
                    statement = statement.with_for_update()
                row = self.session.scalar(statement)
                if row is None:
                    raise CorrelationPersistenceError("revision hypothesis does not exist")
                existing = self.session.get(
                    CorrelationHypothesisRevision,
                    revision.revision_id,
                )
                if existing is not None:
                    if (
                        existing.snapshot_digest == revision.snapshot_digest
                        and row.revision == revised.revision
                        and row.content_digest == expected_digest
                    ):
                        return False
                    raise CorrelationPersistenceError("revision identifier conflicts")
                if row.department != revised.department:
                    raise CorrelationPersistenceError("revision crosses department scope")
                if row.revision != revised.revision - 1:
                    raise CorrelationPersistenceError("revision sequence is not contiguous")
                if row.state != revision.previous_state:
                    raise CorrelationPersistenceError("revision previous state does not match")

                row.revision = revised.revision
                row.state = revised.state
                row.abstained = revised.abstained
                row.abstention_reason = revised.abstention_reason
                row.payload = revised.model_dump(mode="json")
                row.canonical_json = canonical_json(
                    revised,
                    maximum_bytes=MAX_CORRELATION_DOCUMENT_BYTES,
                )
                row.content_digest = expected_digest
                row.graph_digest = revised.graph_digest
                row.projection = revised.flat_projection.model_dump(mode="json")
                row.updated_at = revision.recorded_at
                self.session.add(
                    CorrelationHypothesisRevision(
                        revision_id=revision.revision_id,
                        hypothesis_id=revision.hypothesis_id,
                        department=revised.department,
                        revision=revision.revision,
                        previous_state=revision.previous_state,
                        new_state=revision.new_state,
                        reason_code=revision.reason_code,
                        snapshot=revised.model_dump(mode="json"),
                        snapshot_digest=revision.snapshot_digest,
                        recorded_at=revision.recorded_at,
                        generated_only=True,
                        operational=False,
                    )
                )
                self.session.flush()
            return True
        except IntegrityError as exc:
            raise CorrelationPersistenceError(
                "hypothesis revision violated a persistence invariant"
            ) from exc

    def _store_receipts(self, result: CorrelationBatchResultV1) -> None:
        for item in result.receipts:
            self.session.add(
                CorrelationEventReceipt(
                    receipt_id=item.receipt_id,
                    run_id=result.run_id,
                    department=item.department,
                    event_id=item.event_id,
                    event_digest=item.event_digest,
                    partition_digest=item.partition_digest,
                    disposition=item.disposition,
                    reason_code=item.reason_code,
                    accepted=item.accepted,
                    receipt_sequence=item.receipt_sequence,
                    occurred_at=item.occurred_at,
                    recorded_at=item.recorded_at,
                    generated_only=True,
                )
            )

    def _store_checkpoints(
        self,
        result: CorrelationBatchResultV1,
        now: datetime,
    ) -> None:
        for item in result.checkpoints:
            statement = select(CorrelationPartitionCheckpoint).where(
                CorrelationPartitionCheckpoint.department == item.department,
                CorrelationPartitionCheckpoint.profile_id == item.profile_id,
                CorrelationPartitionCheckpoint.partition_digest
                == item.partition_digest,
            )
            row = self.session.scalar(statement)
            if row is None:
                self.session.add(
                    CorrelationPartitionCheckpoint(
                        checkpoint_id=_identifier(
                            "ckp_",
                            f"{item.department}:{item.profile_id}:{item.partition_digest}",
                        ),
                        department=item.department,
                        profile_id=item.profile_id,
                        partition_digest=item.partition_digest,
                        receipt_sequence=item.receipt_sequence,
                        last_source_sequence=item.last_source_sequence,
                        maximum_occurred_at=item.maximum_occurred_at,
                        watermark_at=item.watermark_at,
                        active_window_count=item.active_window_count,
                        generated_only=True,
                        updated_at=now,
                    )
                )
                continue
            if item.watermark_at < row.watermark_at:
                raise CorrelationPersistenceError(
                    "correlation checkpoint cannot move backward"
                )
            row.receipt_sequence = max(
                row.receipt_sequence + 1,
                item.receipt_sequence,
            )
            row.last_source_sequence = item.last_source_sequence
            row.maximum_occurred_at = item.maximum_occurred_at
            row.watermark_at = item.watermark_at
            row.active_window_count = item.active_window_count
            row.updated_at = now

    def _store_hypotheses(
        self,
        result: CorrelationBatchResultV1,
        now: datetime,
    ) -> None:
        windows = {item.window_id: item for item in result.windows}
        for window in result.windows:
            for sequence, event_id in enumerate(window.event_ids):
                self.session.add(
                    CorrelationWindowEvent(
                        membership_id=_identifier(
                            "winm_", f"{result.run_id}:{window.window_id}:{event_id}"
                        ),
                        run_id=result.run_id,
                        department=window.department,
                        window_id=window.window_id,
                        event_id=event_id,
                        sequence=sequence,
                        window_payload=window.model_dump(mode="json"),
                        generated_only=True,
                    )
                )
        for hypothesis in result.hypotheses:
            validate_intelligence_document(
                hypothesis,
                maximum_bytes=MAX_CORRELATION_DOCUMENT_BYTES,
            )
            payload = hypothesis.model_dump(mode="json")
            content_digest = canonical_sha256(
                hypothesis,
                maximum_bytes=MAX_CORRELATION_DOCUMENT_BYTES,
            )
            self.session.add(
                CorrelationHypothesis(
                    hypothesis_id=hypothesis.hypothesis_id,
                    department=hypothesis.department,
                    run_id=result.run_id,
                    hypothesis_key=hypothesis.hypothesis_key,
                    profile_id=hypothesis.profile_id,
                    profile_version=hypothesis.profile_version,
                    partition_digest=hypothesis.partition_digest,
                    revision=hypothesis.revision,
                    state=hypothesis.state,
                    subject_kind=hypothesis.subject_kind,
                    authority_class="mandatory_review",
                    operational=False,
                    generated_only=True,
                    confidence=hypothesis.confidence,
                    uncertainty=hypothesis.uncertainty,
                    abstained=hypothesis.abstained,
                    abstention_reason=hypothesis.abstention_reason,
                    contradiction_count=hypothesis.contradiction_count,
                    payload=payload,
                    canonical_json=canonical_json(
                        hypothesis,
                        maximum_bytes=MAX_CORRELATION_DOCUMENT_BYTES,
                    ),
                    content_digest=content_digest,
                    graph_digest=hypothesis.graph_digest,
                    arbitration_digest=hypothesis.arbitration_digest,
                    projection=hypothesis.flat_projection.model_dump(mode="json"),
                    retention_class=hypothesis.retention_class,
                    created_at=now,
                    updated_at=now,
                )
            )
            self.session.flush()
            for evidence in hypothesis.evidence:
                self.session.add(
                    HypothesisEvidenceReference(
                        evidence_id=evidence.evidence_id,
                        hypothesis_id=hypothesis.hypothesis_id,
                        department=hypothesis.department,
                        role=evidence.role,
                        source_type="generated_event",
                        source_ref=evidence.event_id,
                        source_digest=evidence.source_digest,
                        sequence=evidence.sequence,
                        payload={"chronology": evidence.chronology.model_dump(mode="json")},
                        occurred_at=evidence.chronology.occurred_at,
                        created_at=now,
                    )
                )
            for lane in hypothesis.lane_results:
                self.session.add(
                    CorrelationLaneResult(
                        lane_result_id=_identifier(
                            "lres_", f"{hypothesis.hypothesis_id}:{lane.lane}"
                        ),
                        hypothesis_id=hypothesis.hypothesis_id,
                        department=hypothesis.department,
                        lane=lane.lane,
                        status=lane.status,
                        payload=lane.model_dump(mode="json"),
                        lineage_digest=lane.lineage_digest,
                        generated_fixture_result=lane.generated_fixture_result,
                        generated_only=True,
                        operational=False,
                    )
                )
            revision = HypothesisRevisionV1(
                revision_id=_identifier(
                    "hrev_", f"{hypothesis.hypothesis_id}:{hypothesis.revision}"
                ),
                hypothesis_id=hypothesis.hypothesis_id,
                revision=hypothesis.revision,
                previous_state="none",
                new_state=hypothesis.state,
                reason_code="generated_initial_projection",
                snapshot_digest=content_digest,
                recorded_at=hypothesis.chronology.recorded_at,
            )
            self.session.add(
                CorrelationHypothesisRevision(
                    revision_id=revision.revision_id,
                    hypothesis_id=hypothesis.hypothesis_id,
                    department=hypothesis.department,
                    revision=hypothesis.revision,
                    previous_state=revision.previous_state,
                    new_state=revision.new_state,
                    reason_code=revision.reason_code,
                    snapshot=payload,
                    snapshot_digest=revision.snapshot_digest,
                    recorded_at=hypothesis.chronology.recorded_at,
                    generated_only=True,
                    operational=False,
                )
            )
            if hypothesis.window.window_id not in windows:
                raise CorrelationPersistenceError(
                    "hypothesis references an unknown correlation window"
                )
