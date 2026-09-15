from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select

from hcam.database import CURRENT_SCHEMA_REVISION, Database
from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.contracts import (
    CorrelationIngressEventV1,
    CorrelationProfileV1,
)
from hcam.intelligence.correlation.persistence import (
    CorrelationPersistence,
    CorrelationPersistenceError,
)
from hcam.intelligence.correlation.hypotheses import revise_hypothesis_state
from hcam.intelligence.correlation.runtime import run_generated_batch
from hcam.intelligence.models import (
    CorrelationEventReceipt,
    CorrelationHypothesis,
    CorrelationHypothesisRevision,
    CorrelationLaneResult,
    CorrelationRun,
    CorrelationWindowEvent,
    HypothesisEvidenceReference,
)


P41_TABLES = {
    "correlation_event_receipts",
    "correlation_partition_checkpoints",
    "correlation_window_events",
    "correlation_lane_results",
    "correlation_hypothesis_revisions",
}
P42_TABLES = {
    "intelligence_rule_compilations",
    "intelligence_rule_scope_members",
    "intelligence_rule_schedules",
    "intelligence_rule_lifecycle_events",
    "intelligence_rule_state_checkpoints",
    "intelligence_rule_evaluation_revisions",
    "intelligence_rule_shadow_comparisons",
}
P43_TABLES = {
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
}
BASE = datetime(2026, 1, 1, tzinfo=UTC)


def _config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _batch():
    selected = CorrelationProfileV1(
        profile_id="persistence-profile",
        profile_version=canonical_sha256({"profile": "persistence"}),
        allowed_event_types=["hcam.analytics.observation.created.v1"],
        subject_kind="vehicle",
        partition_dimensions=["generated_reference"],
        window_seconds=10,
        allowed_lateness_seconds=1,
        minimum_supporting_events=2,
        maximum_events_per_window=100,
        maximum_active_windows=8,
    )

    def event(identifier: int, seconds: int) -> CorrelationIngressEventV1:
        instant = BASE + timedelta(seconds=seconds)
        return CorrelationIngressEventV1(
            event_id=f"persistence-event-{identifier}",
            event_type="hcam.analytics.observation.created.v1",
            schema_version=1,
            department="generated-lab",
            stream_id="str_" + "5" * 32,
            camera_id="cam-5",
            profile_id=selected.profile_id,
            subject_kind="vehicle",
            signals={
                "object_class": "car",
                "confidence": 0.9,
                "generated_reference": "vehicle-a",
                "source_sequence": identifier,
            },
            chronology={
                "occurred_at": instant,
                "observed_at": instant,
                "received_at": instant,
                "recorded_at": instant,
            },
        )

    return run_generated_batch(
        [event(1, 1), event(2, 2), event(3, 20)],
        selected,
    )


def test_phase41_migration_upgrade_downgrade_upgrade_cycle(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'phase41.db').as_posix()}"
    config = _config(database_url)
    command.upgrade(config, "0013_correlation_foundation")
    database = Database(database_url)
    try:
        inspector = inspect(database.engine)
        assert P41_TABLES.issubset(inspector.get_table_names())
        assert P42_TABLES.isdisjoint(inspector.get_table_names())
        assert P43_TABLES.isdisjoint(inspector.get_table_names())
        assert {
            "profile_id",
            "profile_version",
            "result_digest",
            "replay_binding",
            "accepted_count",
        }.issubset(
            column["name"] for column in inspector.get_columns("correlation_runs")
        )
        command.upgrade(config, "0014_rule_authoring_evaluation")
        assert P42_TABLES.issubset(inspect(database.engine).get_table_names())
        assert P43_TABLES.isdisjoint(inspect(database.engine).get_table_names())
        command.upgrade(config, "0018_operations_security_scale")
        database.check_ready()
        assert CURRENT_SCHEMA_REVISION == "0018_operations_security_scale"
        assert P42_TABLES.issubset(inspect(database.engine).get_table_names())
        assert P43_TABLES.issubset(inspect(database.engine).get_table_names())
        command.check(config)
        database.dispose()
        command.downgrade(config, "0013_correlation_foundation")
        downgraded = Database(database_url, allow_unversioned_schema=True)
        downgraded_tables = inspect(downgraded.engine).get_table_names()
        assert P41_TABLES.issubset(downgraded_tables)
        assert P42_TABLES.isdisjoint(downgraded_tables)
        assert P43_TABLES.isdisjoint(downgraded_tables)
        assert "profile_id" in {
            column["name"]
            for column in inspect(downgraded.engine).get_columns("correlation_runs")
        }
        downgraded.dispose()
        command.upgrade(config, "0014_rule_authoring_evaluation")
        assert P43_TABLES.isdisjoint(inspect(downgraded.engine).get_table_names())
        command.upgrade(config, "0018_operations_security_scale")
        command.check(config)
        final = Database(database_url)
        final.check_ready()
        assert P41_TABLES | P42_TABLES <= set(inspect(final.engine).get_table_names())
        assert P43_TABLES.issubset(inspect(final.engine).get_table_names())
        final.dispose()
    finally:
        database.dispose()


def test_generated_batch_persists_atomically_and_is_idempotent(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'persistence.db').as_posix()}"
    command.upgrade(_config(database_url), "head")
    database = Database(database_url)
    batch = _batch()
    try:
        with database.session_factory() as session:
            first = CorrelationPersistence(session).store_batch(batch)
        with database.session_factory() as session:
            second = CorrelationPersistence(session).store_batch(batch)
            assert first.inserted and not second.inserted
            assert session.scalar(select(func.count()).select_from(CorrelationRun)) == 1
            assert (
                session.scalar(
                    select(func.count()).select_from(CorrelationEventReceipt)
                )
                == 3
            )
            assert (
                session.scalar(select(func.count()).select_from(CorrelationHypothesis))
                == 2
            )
            assert (
                session.scalar(select(func.count()).select_from(CorrelationWindowEvent))
                == 3
            )
            assert (
                session.scalar(select(func.count()).select_from(CorrelationLaneResult))
                == 10
            )
            assert (
                session.scalar(
                    select(func.count()).select_from(CorrelationHypothesisRevision)
                )
                == 2
            )
            row = session.scalar(
                select(CorrelationHypothesis).order_by(CorrelationHypothesis.created_at)
            )
            assert row is not None
            assert row.authority_class == "mandatory_review"
            assert not row.operational
            assert row.generated_only
            run = session.get(CorrelationRun, batch.run_id)
            assert run is not None
            assert run.replay_binding == batch.replay_binding.model_dump(mode="json")
            revision_rows = session.scalars(
                select(CorrelationHypothesisRevision).order_by(
                    CorrelationHypothesisRevision.hypothesis_id
                )
            ).all()
            assert all(
                canonical_sha256(row.snapshot) == row.snapshot_digest
                for row in revision_rows
            )
    finally:
        database.dispose()


def test_stored_run_digest_conflict_fails_closed(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'digest-conflict.db').as_posix()}"
    command.upgrade(_config(database_url), "head")
    database = Database(database_url)
    batch = _batch()
    try:
        with database.session_factory() as session:
            CorrelationPersistence(session).store_batch(batch)
        with database.session_factory.begin() as session:
            row = session.get(CorrelationRun, batch.run_id)
            assert row is not None
            row.result_digest = canonical_sha256({"conflict": True})
        with database.session_factory() as session:
            with pytest.raises(
                CorrelationPersistenceError, match="digest does not match"
            ):
                CorrelationPersistence(session).store_batch(batch)
    finally:
        database.dispose()


def test_hypothesis_revisions_append_without_rewriting_evidence(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'revisions.db').as_posix()}"
    command.upgrade(_config(database_url), "head")
    database = Database(database_url)
    batch = _batch()
    original = batch.hypotheses[0]
    revised, revision = revise_hypothesis_state(
        original,
        new_state="corrected",
        reason_code="generated_correction",
        recorded_at=BASE + timedelta(seconds=30),
    )
    try:
        with database.session_factory() as session:
            CorrelationPersistence(session).store_batch(batch)
        with database.session_factory() as session:
            inserted = CorrelationPersistence(session).append_revision(
                revised, revision
            )
        with database.session_factory() as session:
            persistence = CorrelationPersistence(session)
            assert not persistence.append_revision(revised, revision)
        with database.session_factory() as session:
            row = session.get(CorrelationHypothesis, original.hypothesis_id)
            assert row is not None
            assert row.revision == 2
            assert row.state == "corrected"
            assert row.content_digest == revision.snapshot_digest
            assert session.scalar(
                select(func.count())
                .select_from(HypothesisEvidenceReference)
                .where(
                    HypothesisEvidenceReference.hypothesis_id == original.hypothesis_id
                )
            ) == len(original.evidence)
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(CorrelationHypothesisRevision)
                    .where(
                        CorrelationHypothesisRevision.hypothesis_id
                        == original.hypothesis_id
                    )
                )
                == 2
            )
            stored_revisions = session.scalars(
                select(CorrelationHypothesisRevision)
                .where(
                    CorrelationHypothesisRevision.hypothesis_id
                    == original.hypothesis_id
                )
                .order_by(CorrelationHypothesisRevision.revision)
            ).all()
            assert [item.snapshot["revision"] for item in stored_revisions] == [1, 2]
            assert all(
                canonical_sha256(item.snapshot) == item.snapshot_digest
                for item in stored_revisions
            )
            assert inserted
        invalid = revision.model_copy(
            update={"snapshot_digest": canonical_sha256({"bad": 1})}
        )
        with database.session_factory() as session:
            with pytest.raises(
                CorrelationPersistenceError, match="digest does not match"
            ):
                CorrelationPersistence(session).append_revision(revised, invalid)
    finally:
        database.dispose()


def test_hypothesis_revision_validation_is_fail_closed(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'revision-validation.db').as_posix()}"
    command.upgrade(_config(database_url), "head")
    database = Database(database_url)
    batch = _batch()
    original = batch.hypotheses[0]
    revised, revision = revise_hypothesis_state(
        original,
        new_state="corrected",
        reason_code="generated_correction",
        recorded_at=BASE + timedelta(seconds=30),
    )
    try:
        with database.session_factory() as session:
            persistence = CorrelationPersistence(session)
            with pytest.raises(CorrelationPersistenceError, match="another hypothesis"):
                persistence.append_revision(
                    revised,
                    revision.model_copy(update={"hypothesis_id": "hyp_" + "f" * 32}),
                )
            with pytest.raises(
                CorrelationPersistenceError, match="number does not match"
            ):
                persistence.append_revision(
                    revised,
                    revision.model_copy(update={"revision": revised.revision + 1}),
                )
            with pytest.raises(
                CorrelationPersistenceError, match="state does not match"
            ):
                persistence.append_revision(
                    revised,
                    revision.model_copy(update={"new_state": "expired"}),
                )
            with pytest.raises(CorrelationPersistenceError, match="does not exist"):
                persistence.append_revision(revised, revision)
    finally:
        database.dispose()


def test_generated_worker_claim_is_leased_and_sqlite_is_single_worker(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite:///{(tmp_path / 'worker.db').as_posix()}"
    command.upgrade(_config(database_url), "head")
    database = Database(database_url)
    now = datetime.now(UTC)
    try:
        with database.session_factory() as session:
            session.add(
                CorrelationRun(
                    run_id="crun_" + "a" * 32,
                    department="generated-lab",
                    status="queued",
                    execution_scope="generated_event_correlation",
                    reason_code="generated_queued",
                    generated_only=True,
                    attempt_count=0,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()
        with database.session_factory() as session:
            persistence = CorrelationPersistence(session)
            with pytest.raises(CorrelationPersistenceError, match="one worker"):
                persistence.claim_next_run(
                    worker_id="generated-worker-1",
                    now=now,
                    sqlite_worker_count=2,
                )
            with pytest.raises(CorrelationPersistenceError, match="identifier"):
                persistence.claim_next_run(worker_id="", now=now)
            with pytest.raises(CorrelationPersistenceError, match="lease"):
                persistence.claim_next_run(
                    worker_id="generated-worker-1",
                    now=now,
                    lease_seconds=91,
                )
            claimed = persistence.claim_next_run(
                worker_id="generated-worker-1",
                now=now,
            )
            assert claimed is not None
            assert claimed.status == "running"
            assert claimed.attempt_count == 1
            assert claimed.lease_until == now + timedelta(seconds=30)
            assert (
                persistence.claim_next_run(
                    worker_id="generated-worker-2",
                    now=now,
                )
                is None
            )
            recovered = persistence.claim_next_run(
                worker_id="generated-worker-2",
                now=now + timedelta(seconds=31),
            )
            assert recovered is not None
            assert recovered.attempt_count == 2
    finally:
        database.dispose()
