from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.engine import Connection

from hcam.database import Database
from hcam.intelligence.correlation.persistence import CorrelationPersistence
from hcam.intelligence.models import CorrelationPartitionCheckpoint, CorrelationRun
from hcam.intelligence.row_security import apply_department_scope
from hcam.security.auth import Principal


POSTGRES_TEST_URL = os.getenv("HCAM_POSTGRES_TEST_URL")
PROBE_ROLE = "hcam_p41_rls_probe"
CHECKPOINT_IDS = ("ckp_" + "a" * 32, "ckp_" + "b" * 32)
RUN_IDS = ("crun_" + "a" * 32, "crun_" + "b" * 32)
P41_TABLES = (
    "correlation_event_receipts",
    "correlation_partition_checkpoints",
    "correlation_window_events",
    "correlation_lane_results",
    "correlation_hypothesis_revisions",
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
        actor_id="phase41-postgres-test",
        roles=frozenset({"platform.admin"}),
        departments=frozenset({"*"}),
        authentication_method="generated-test",
    )


def _drop_probe_role(connection: Connection) -> None:
    exists = connection.scalar(
        text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role)"),
        {"role": PROBE_ROLE},
    )
    if exists:
        connection.execute(text(f"DROP OWNED BY {PROBE_ROLE}"))
        connection.execute(text(f"DROP ROLE {PROBE_ROLE}"))


def test_phase41_postgis_forced_rls_and_department_isolation() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    now = datetime.now(UTC)
    try:
        database.check_ready()
        with database.engine.connect() as connection:
            assert str(connection.scalar(text("SELECT postgis_lib_version()"))).startswith("3.")
            rows = connection.execute(
                text(
                    "SELECT relname, relrowsecurity, relforcerowsecurity "
                    "FROM pg_class WHERE relname = ANY(:tables)"
                ),
                {"tables": list(P41_TABLES)},
            ).all()
            policies = connection.execute(
                text(
                    "SELECT tablename, count(*) FROM pg_policies "
                    "WHERE tablename = ANY(:tables) GROUP BY tablename"
                ),
                {"tables": list(P41_TABLES)},
            ).all()
        assert {row[0]: row[1:] for row in rows} == {
            table: (True, True) for table in P41_TABLES
        }
        assert {row[0]: row[1] for row in policies} == {
            table: 1 for table in P41_TABLES
        }

        with database.session_factory.begin() as session:
            apply_department_scope(session, _admin())
            session.execute(
                delete(CorrelationPartitionCheckpoint).where(
                    CorrelationPartitionCheckpoint.checkpoint_id.in_(CHECKPOINT_IDS)
                )
            )
            session.add_all(
                [
                    CorrelationPartitionCheckpoint(
                        checkpoint_id=CHECKPOINT_IDS[0],
                        department="Engineering Lab",
                        profile_id="generated-p41-rls",
                        partition_digest="sha256:" + "a" * 64,
                        receipt_sequence=1,
                        last_source_sequence=1,
                        maximum_occurred_at=now,
                        watermark_at=now,
                        active_window_count=1,
                        generated_only=True,
                        updated_at=now,
                    ),
                    CorrelationPartitionCheckpoint(
                        checkpoint_id=CHECKPOINT_IDS[1],
                        department="Another Department",
                        profile_id="generated-p41-rls",
                        partition_digest="sha256:" + "b" * 64,
                        receipt_sequence=1,
                        last_source_sequence=1,
                        maximum_occurred_at=now,
                        watermark_at=now,
                        active_window_count=1,
                        generated_only=True,
                        updated_at=now,
                    ),
                ]
            )

        with database.engine.begin() as connection:
            _drop_probe_role(connection)
            connection.execute(text(f"CREATE ROLE {PROBE_ROLE} NOLOGIN"))
            connection.execute(text(f"GRANT USAGE ON SCHEMA public TO {PROBE_ROLE}"))
            connection.execute(
                text(f"GRANT SELECT ON correlation_partition_checkpoints TO {PROBE_ROLE}")
            )
            connection.execute(text(f"SET LOCAL ROLE {PROBE_ROLE}"))
            connection.execute(
                text("SELECT set_config('hcam.is_platform_admin', 'false', true)")
            )
            connection.execute(
                text(
                    "SELECT set_config('hcam.allowed_departments', "
                    "'Engineering Lab', true)"
                )
            )
            visible = connection.execute(
                select(CorrelationPartitionCheckpoint.checkpoint_id).where(
                    CorrelationPartitionCheckpoint.checkpoint_id.in_(CHECKPOINT_IDS)
                )
            ).scalars().all()
            connection.execute(text("RESET ROLE"))
        assert visible == [CHECKPOINT_IDS[0]]
    finally:
        with database.engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM correlation_partition_checkpoints "
                    "WHERE checkpoint_id = ANY(:ids)"
                ),
                {"ids": list(CHECKPOINT_IDS)},
            )
            _drop_probe_role(connection)
        database.dispose()


def test_phase41_skip_locked_claims_an_unlocked_generated_run() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    now = datetime.now(UTC)
    try:
        with database.session_factory.begin() as session:
            apply_department_scope(session, _admin())
            session.execute(delete(CorrelationRun).where(CorrelationRun.run_id.in_(RUN_IDS)))
            session.add_all(
                [
                    CorrelationRun(
                        run_id=RUN_IDS[0],
                        department="Engineering Lab",
                        status="queued",
                        execution_scope="generated_event_correlation",
                        reason_code="generated_queued",
                        generated_only=True,
                        attempt_count=0,
                        created_at=now,
                        updated_at=now,
                    ),
                    CorrelationRun(
                        run_id=RUN_IDS[1],
                        department="Engineering Lab",
                        status="queued",
                        execution_scope="generated_event_correlation",
                        reason_code="generated_queued",
                        generated_only=True,
                        attempt_count=0,
                        created_at=now + timedelta(milliseconds=1),
                        updated_at=now,
                    ),
                ]
            )

        with database.engine.connect() as locking_connection:
            transaction = locking_connection.begin()
            locking_connection.execute(
                text("SELECT run_id FROM correlation_runs WHERE run_id = :id FOR UPDATE"),
                {"id": RUN_IDS[0]},
            ).one()
            with database.session_factory() as session:
                apply_department_scope(session, _admin())
                claimed = CorrelationPersistence(session).claim_next_run(
                    worker_id="generated-postgres-worker",
                    now=now,
                )
                assert claimed is not None
                assert claimed.run_id == RUN_IDS[1]
                assert claimed.attempt_count == 1
            transaction.rollback()
    finally:
        with database.engine.begin() as connection:
            connection.execute(
                text("DELETE FROM correlation_runs WHERE run_id = ANY(:ids)"),
                {"ids": list(RUN_IDS)},
            )
        database.dispose()
