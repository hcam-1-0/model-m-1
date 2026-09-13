from __future__ import annotations

from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from hcam.operations.platform.bounds import bounded_text, validate_generated_document
from hcam.operations.platform.canonical import digest, stable_id
from hcam.operations.platform.contracts import (
    CapacityRunV1,
    CircuitStateV1,
    DegradationDecisionV1,
    ErrorBudgetStateV1,
    KillSwitchRevisionV1,
    RecoverySimulationResultV1,
    ServiceObjectiveV1,
    SupplyChainInventoryV1,
    WorkerJobV1,
)
from hcam.operations.platform.models import (
    PlatformCapacityRecord,
    PlatformCircuitRecord,
    PlatformDegradationRecord,
    PlatformErrorBudgetRecord,
    PlatformKillSwitchRecord,
    PlatformOutboxRecord,
    PlatformRecoveryRecord,
    PlatformSecurityEvidenceRecord,
    PlatformServiceObjectiveRecord,
    PlatformSupplyChainRecord,
)


RecordT = TypeVar("RecordT")


class PlatformRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_objective(self, objective: ServiceObjectiveV1, *, at: datetime) -> None:
        payload = objective.model_dump(mode="json")
        self.session.add(
            PlatformServiceObjectiveRecord(
                objective_id=objective.objective_id,
                department=objective.department,
                service_class=objective.service_class,
                target_state=objective.target_state,
                revision=objective.revision,
                content_digest=digest(payload),
                payload=payload,
                created_at=at,
                updated_at=at,
            )
        )

    def save_budget(self, department: str, budget: ErrorBudgetStateV1, *, at: datetime) -> None:
        payload = budget.model_dump(mode="json")
        content_digest = digest(payload)
        self.session.add(
            PlatformErrorBudgetRecord(
                budget_id=stable_id("ref", department, budget.objective_id, content_digest),
                objective_id=budget.objective_id,
                department=department,
                status=budget.status,
                content_digest=content_digest,
                payload=payload,
                observed_at=at,
            )
        )

    def save_degradation(self, department: str, item: DegradationDecisionV1, *, revision: int, at: datetime) -> None:
        payload = item.model_dump(mode="json")
        content_digest = digest(payload)
        self.session.add(
            PlatformDegradationRecord(
                degradation_id=stable_id("ref", department, revision, content_digest),
                department=department,
                state=item.state,
                revision=revision,
                content_digest=content_digest,
                payload=payload,
                recorded_at=at,
            )
        )

    def save_circuit(self, department: str, item: CircuitStateV1) -> None:
        payload = item.model_dump(mode="json")
        self.session.add(
            PlatformCircuitRecord(
                circuit_id=stable_id("ref", department, item.dependency_class),
                department=department,
                dependency_class=item.dependency_class,
                state=item.state,
                content_digest=digest(payload),
                payload=payload,
                updated_at=item.updated_at,
            )
        )

    def save_control(self, item: KillSwitchRevisionV1) -> None:
        payload = item.model_dump(mode="json")
        self.session.add(
            PlatformKillSwitchRecord(
                record_id=stable_id("ref", item.switch_id, item.revision),
                switch_id=item.switch_id,
                department=item.department,
                scope=item.scope,
                scope_key=item.scope_key,
                state=item.state,
                revision=item.revision,
                actor_id=item.actor_id,
                reason_code=item.reason_code,
                content_digest=digest(payload),
                payload=payload,
                recorded_at=item.recorded_at,
            )
        )

    def save_recovery(self, department: str, item: RecoverySimulationResultV1, *, at: datetime) -> None:
        payload = item.model_dump(mode="json")
        content_digest = digest(payload)
        self.session.add(
            PlatformRecoveryRecord(
                result_id=stable_id("ref", department, item.plan_id, content_digest),
                plan_id=item.plan_id,
                department=department,
                outcome=item.outcome,
                content_digest=content_digest,
                payload=payload,
                recorded_at=at,
            )
        )

    def save_capacity(self, department: str, item: CapacityRunV1, *, at: datetime) -> None:
        payload = item.model_dump(mode="json")
        self.session.add(
            PlatformCapacityRecord(
                run_id=item.run_id,
                department=department,
                profile_id=item.profile_id,
                scale=item.scale,
                mode=item.mode,
                status=item.status,
                content_digest=digest(payload),
                payload=payload,
                recorded_at=at,
            )
        )

    def save_supply_chain(self, department: str, item: SupplyChainInventoryV1) -> None:
        payload = item.model_dump(mode="json")
        self.session.add(
            PlatformSupplyChainRecord(
                inventory_id=item.inventory_id,
                department=department,
                freshness=item.freshness,
                source_digest=item.source_digest,
                content_digest=digest(payload),
                payload=payload,
                observed_at=item.observed_at,
            )
        )

    def save_security_evidence(
        self,
        *,
        department: str,
        evidence_type: str,
        outcome: str,
        payload: dict[str, Any],
        at: datetime,
    ) -> None:
        bounded_text(evidence_type, maximum=96)
        bounded_text(outcome, maximum=24)
        validate_generated_document(payload)
        content_digest = digest(payload)
        self.session.add(
            PlatformSecurityEvidenceRecord(
                evidence_id=stable_id("ref", department, evidence_type, at.isoformat(), content_digest),
                department=department,
                evidence_type=evidence_type,
                outcome=outcome,
                content_digest=content_digest,
                payload=payload,
                recorded_at=at,
            )
        )

    def enqueue_outbox(
        self,
        job: WorkerJobV1,
        *,
        event_type: str,
        payload: dict[str, Any],
        available_at: datetime,
    ) -> None:
        bounded_text(event_type, maximum=96)
        validate_generated_document(payload)
        self.session.add(
            PlatformOutboxRecord(
                event_id=job.job_id,
                department=job.department,
                event_type=event_type,
                state=job.state,
                attempt_count=job.attempt_count,
                lease_owner=job.lease_owner,
                lease_until=job.lease_until,
                idempotency_key=job.idempotency_key,
                payload=payload,
                available_at=available_at,
                created_at=job.updated_at,
            )
        )

    def latest_payloads(
        self,
        model: type[RecordT],
        *,
        departments: frozenset[str] | None,
        order_by,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        statement: Select[tuple[RecordT]] = select(model)
        if departments is not None:
            if not departments:
                return []
            statement = statement.where(model.department.in_(departments))
        rows = self.session.scalars(statement.order_by(order_by.desc()).limit(min(max(limit, 1), 200)))
        return [dict(row.payload) for row in rows]
