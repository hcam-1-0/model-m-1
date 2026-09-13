from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest
from sqlalchemy import delete, text

from hcam.database import Database
from hcam.intelligence.alerts.canonical import digest, stable_id
from hcam.intelligence.alerts.contracts import AlertAggregateV2
from hcam.intelligence.alerts.persistence import AlertPersistence
from hcam.intelligence.models import Alert, AlertTimerIntent
from hcam.intelligence.row_security import apply_department_scope
from hcam.security.auth import Principal


POSTGRES_TEST_URL = os.getenv("HCAM_POSTGRES_TEST_URL")
PROBE_ROLE = "hcam_p43_rls_probe"
P43_TABLES = (
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
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not POSTGRES_TEST_URL,
        reason="HCAM_POSTGRES_TEST_URL is required for PostgreSQL integration",
    ),
]


def _admin() -> Principal:
    return Principal(
        actor_id="phase43-postgres-test",
        roles=frozenset({"platform.admin"}),
        departments=frozenset({"*"}),
        authentication_method="generated-test",
    )


def _alert(index: int, now: datetime) -> Alert:
    alert_id = stable_id("alt", "phase43-postgres", index)
    semantic_key = digest({"semantic": index})
    delivery_key = digest({"delivery": index})
    aggregate = AlertAggregateV2(
        alert_id=alert_id,
        version=1,
        department="P4.3 Generated PostgreSQL",
        semantic_key=semantic_key,
        delivery_key=delivery_key,
        source_evaluation_id=stable_id("revl", "phase43-postgres", index),
        source_evaluation_revision=1,
        source_evaluation_digest=digest({"evaluation": index}),
        incident_key=f"generated.postgres.{index}",
        state="proposed",
        domain="police_intelligence",
        authority_class="mandatory_review",
        severity="high",
        priority="urgent",
        confidence=0.9,
        certainty=0.9,
        chronology_confidence=1.0,
        disposition="unreviewed",
        evidence_refs=[f"generated.postgres.evidence.{index}"],
        policy_digest=digest({"policy": index}),
        created_at=now,
        updated_at=now,
    )
    return Alert(
        alert_id=aggregate.alert_id,
        version_id=aggregate.version,
        department=aggregate.department,
        hypothesis_id=None,
        dedupe_key=semantic_key,
        semantic_key=semantic_key,
        delivery_key=delivery_key,
        source_evaluation_id=aggregate.source_evaluation_id,
        source_evaluation_revision=1,
        source_evaluation_digest=aggregate.source_evaluation_digest,
        incident_key=aggregate.incident_key,
        domain=aggregate.domain,
        state=aggregate.state,
        authority_class=aggregate.authority_class,
        operational=False,
        generated_only=True,
        severity=aggregate.severity,
        priority=aggregate.priority,
        confidence=aggregate.confidence,
        certainty=aggregate.certainty,
        chronology_confidence=aggregate.chronology_confidence,
        disposition=aggregate.disposition,
        policy_digest=aggregate.policy_digest,
        payload=aggregate.model_dump(mode="json"),
        content_digest=digest(aggregate),
        retention_class="derived.intelligence.test",
        created_at=now,
        updated_at=now,
    )


def _drop_probe_role(database: Database) -> None:
    with database.engine.begin() as connection:
        exists = connection.scalar(
            text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role)"),
            {"role": PROBE_ROLE},
        )
        if exists:
            connection.execute(text(f"DROP OWNED BY {PROBE_ROLE}"))
            connection.execute(text(f"DROP ROLE {PROBE_ROLE}"))


def test_phase43_postgres_forced_rls_and_skip_locked_timer_claims() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    principal = _admin()
    now = datetime.now(UTC)
    alert_ids = [stable_id("alt", "phase43-postgres", index) for index in (1, 2)]
    timer_ids = [stable_id("atmr", "phase43-postgres", index) for index in (1, 2)]
    try:
        database.check_ready()
        with database.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT relname, relrowsecurity, relforcerowsecurity "
                    "FROM pg_class WHERE relname = ANY(:tables)"
                ),
                {"tables": list(P43_TABLES)},
            ).all()
            policies = connection.execute(
                text(
                    "SELECT tablename, count(*) FROM pg_policies "
                    "WHERE tablename = ANY(:tables) GROUP BY tablename"
                ),
                {"tables": list(P43_TABLES)},
            ).all()
        assert {row[0]: row[1:] for row in rows} == {
            table: (True, True) for table in P43_TABLES
        }
        assert {row[0]: row[1] for row in policies} == {
            table: 1 for table in P43_TABLES
        }

        with database.session_factory.begin() as session:
            apply_department_scope(session, principal)
            session.execute(delete(AlertTimerIntent).where(AlertTimerIntent.timer_id.in_(timer_ids)))
            session.execute(delete(Alert).where(Alert.alert_id.in_(alert_ids)))
            alerts = [_alert(index, now) for index in (1, 2)]
            session.add_all(alerts)
            session.flush()
            session.add_all(
                [
                    AlertTimerIntent(
                        timer_id=timer_id,
                        alert_id=alert.alert_id,
                        department=alert.department,
                        timer_kind="review_sla",
                        due_at=now,
                        state="pending",
                        attempt_count=0,
                        lease_owner=None,
                        lease_until=None,
                        expected_alert_version=1,
                        payload_digest=digest({"timer": timer_id}),
                        generated_only=True,
                        operational=False,
                        created_at=now,
                        updated_at=now,
                    )
                    for timer_id, alert in zip(timer_ids, alerts, strict=True)
                ]
            )

        barrier = Barrier(2)

        def claim(worker_id: str) -> str:
            with database.session_factory.begin() as session:
                apply_department_scope(session, principal)
                barrier.wait(timeout=10)
                rows = AlertPersistence(session, enabled=True).claim_due_timers(
                    worker_id=worker_id,
                    now=now + timedelta(seconds=1),
                    limit=1,
                    worker_count=2,
                )
                assert len(rows) == 1
                return rows[0].timer_id

        with ThreadPoolExecutor(max_workers=2) as executor:
            claimed = set(executor.map(claim, ("worker-one", "worker-two")))
        assert claimed == set(timer_ids)

        _drop_probe_role(database)
        with database.engine.begin() as connection:
            connection.execute(text(f"CREATE ROLE {PROBE_ROLE} NOLOGIN"))
            connection.execute(text(f"GRANT USAGE ON SCHEMA public TO {PROBE_ROLE}"))
            connection.execute(text(f"GRANT SELECT ON alert_timer_intents TO {PROBE_ROLE}"))
            connection.execute(text(f"SET LOCAL ROLE {PROBE_ROLE}"))
            connection.execute(text("SELECT set_config('hcam.is_platform_admin', 'false', true)"))
            connection.execute(
                text(
                    "SELECT set_config('hcam.allowed_departments', "
                    "'Different Department', true)"
                )
            )
            assert connection.scalar(
                text(
                    "SELECT count(*) FROM alert_timer_intents "
                    "WHERE timer_id = ANY(:timer_ids)"
                ),
                {"timer_ids": timer_ids},
            ) == 0
            connection.execute(text("RESET ROLE"))
    finally:
        with database.session_factory.begin() as session:
            apply_department_scope(session, principal)
            session.execute(delete(AlertTimerIntent).where(AlertTimerIntent.timer_id.in_(timer_ids)))
            session.execute(delete(Alert).where(Alert.alert_id.in_(alert_ids)))
        _drop_probe_role(database)
        database.dispose()
