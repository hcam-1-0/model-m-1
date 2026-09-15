from datetime import UTC, datetime

import pytest

from hcam.database import Database
from hcam.operations.platform.budgets import calculate_error_budget
from hcam.operations.platform.capacity import simulate_capacity
from hcam.operations.platform.canonical import digest
from hcam.operations.platform.contracts import (
    BurnWindowV1,
    CapabilityProfileV1,
    CircuitStateV1,
    KillSwitchRevisionV1,
    RecoveryAssetV1,
    RecoveryPlanV1,
    ServiceObjectiveV1,
    SupplyChainComponentV1,
    SupplyChainInventoryV1,
    WorkerJobV1,
)
from hcam.operations.platform.degradation import decide_degradation
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
from hcam.operations.platform.objectives import health_projection
from hcam.operations.platform.persistence import PlatformRepository
from hcam.operations.platform.recovery import simulate_recovery


NOW = datetime(2026, 9, 5, tzinfo=UTC)


def _objective() -> ServiceObjectiveV1:
    return ServiceObjectiveV1(
        objective_id="ref_" + "1" * 32,
        department="Generated Department",
        service_class="api",
        indicator="request:success",
        target_state="provisional",
        target_ratio=0.99,
        windows=[BurnWindowV1(window_seconds=300, good=99, valid=100, bad=1, unknown=0)],
        revision=1,
    )


def test_platform_repository_persists_generated_objective_and_budget(tmp_path) -> None:
    database = Database(f"sqlite:///{(tmp_path / 'platform.db').as_posix()}", allow_unversioned_schema=True)
    database.create_schema()
    try:
        objective = _objective()
        with database.session_factory() as session:
            repository = PlatformRepository(session)
            repository.save_objective(objective, at=NOW)
            repository.save_budget(objective.department, calculate_error_budget(objective), at=NOW)
            session.commit()
        with database.session_factory() as session:
            objectives = PlatformRepository(session).latest_payloads(
                PlatformServiceObjectiveRecord,
                departments=frozenset({"Generated Department"}),
                order_by=PlatformServiceObjectiveRecord.updated_at,
            )
            budgets = PlatformRepository(session).latest_payloads(
                PlatformErrorBudgetRecord,
                departments=frozenset({"Generated Department"}),
                order_by=PlatformErrorBudgetRecord.observed_at,
            )
            assert objectives == [objective.model_dump(mode="json")]
            assert budgets[0]["objective_id"] == objective.objective_id
            assert PlatformRepository(session).latest_payloads(
                PlatformServiceObjectiveRecord,
                departments=frozenset({"Other Department"}),
                order_by=PlatformServiceObjectiveRecord.updated_at,
            ) == []
    finally:
        database.dispose()


def test_platform_persistence_digest_is_stable() -> None:
    assert digest(_objective()) == digest(_objective())


def _profile() -> CapabilityProfileV1:
    return CapabilityProfileV1(
        profile_id="ref_" + "2" * 32,
        profile_class="developer_laptop",
        state="declared",
        cpu_units=4,
        memory_mib=8192,
        accelerator_units=0,
        capabilities=frozenset({"cpu:generic"}),
        profile_digest=digest({"profile": "generated"}),
    )


def test_repository_persists_every_generated_platform_store(tmp_path) -> None:
    database = Database(
        f"sqlite:///{(tmp_path / 'all-platform.db').as_posix()}",
        allow_unversioned_schema=True,
    )
    database.create_schema()
    objective = _objective()
    recovery_plan = RecoveryPlanV1(
        plan_id="ref_" + "3" * 32,
        department=objective.department,
        revision=1,
        assets=[
            RecoveryAssetV1(
                asset_ref="ref_" + "4" * 32,
                asset_class="configuration",
                recovery_tier="metadata",
                dependencies=[],
            )
        ],
    )
    inventory = SupplyChainInventoryV1(
        inventory_id="ref_" + "5" * 32,
        observed_at=NOW,
        freshness="unknown",
        components=[
            SupplyChainComponentV1(
                component_ref="ref_" + "6" * 32,
                name="generated-component",
                version="generated-v1",
                source="fixture",
                digest="sha256:" + "7" * 64,
                license_state="unknown",
                vulnerability_state="not_observed",
                provenance_state="not_observed",
            )
        ],
        source_digest="sha256:" + "8" * 64,
    )
    job = WorkerJobV1(
        job_id="ref_" + "9" * 32,
        department=objective.department,
        worker_class="telemetry",
        state="queued",
        attempt_count=0,
        idempotency_key="sha256:" + "a" * 64,
        payload_digest="sha256:" + "b" * 64,
        reason_code="worker.queued",
        updated_at=NOW,
    )
    try:
        with database.session_factory() as session:
            repository = PlatformRepository(session)
            budget = calculate_error_budget(objective)
            repository.save_degradation(
                objective.department,
                decide_degradation(
                    budget,
                    health_projection(objective),
                    optional_lanes=["generated:optional"],
                ),
                revision=1,
                at=NOW,
            )
            repository.save_circuit(
                objective.department,
                CircuitStateV1(
                    dependency_class="generated:database",
                    state="closed",
                    consecutive_failures=0,
                    probe_remaining=0,
                    updated_at=NOW,
                ),
            )
            repository.save_control(
                KillSwitchRevisionV1(
                    switch_id="ref_" + "c" * 32,
                    department=objective.department,
                    scope="department",
                    scope_key="generated:department",
                    state="deny",
                    revision=1,
                    actor_id="generated:owner",
                    reason_code="control.generated",
                    recorded_at=NOW,
                )
            )
            repository.save_recovery(
                objective.department,
                simulate_recovery(recovery_plan),
                at=NOW,
            )
            repository.save_capacity(
                objective.department,
                simulate_capacity(_profile(), scale="C1", mode="balanced"),
                at=NOW,
            )
            repository.save_supply_chain(objective.department, inventory)
            repository.save_security_evidence(
                department=objective.department,
                evidence_type="generated:authorization",
                outcome="accepted",
                payload={"result": "generated"},
                at=NOW,
            )
            repository.enqueue_outbox(
                job,
                event_type="hcam.platform.generated.v1",
                payload={"event": "generated"},
                available_at=NOW,
            )
            session.commit()
        with database.session_factory() as session:
            for model in (
                PlatformDegradationRecord,
                PlatformCircuitRecord,
                PlatformKillSwitchRecord,
                PlatformRecoveryRecord,
                PlatformCapacityRecord,
                PlatformSupplyChainRecord,
                PlatformSecurityEvidenceRecord,
                PlatformOutboxRecord,
            ):
                assert session.query(model).count() == 1
    finally:
        database.dispose()


def test_repository_rejects_prohibited_security_and_outbox_payloads(tmp_path) -> None:
    database = Database(
        f"sqlite:///{(tmp_path / 'bounded.db').as_posix()}",
        allow_unversioned_schema=True,
    )
    database.create_schema()
    try:
        with database.session_factory() as session:
            repository = PlatformRepository(session)
            with pytest.raises(ValueError):
                repository.save_security_evidence(
                    department="Generated Department",
                    evidence_type="generated:authorization",
                    outcome="denied",
                    payload={"secret": "prohibited"},
                    at=NOW,
                )
    finally:
        database.dispose()
