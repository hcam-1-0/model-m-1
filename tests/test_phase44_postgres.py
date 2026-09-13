from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest
from sqlalchemy import text

from hcam.database import Database
from hcam.intelligence.integrations.persistence import IntegrationRepository
from hcam.intelligence.integrations.service import IntegrationControlService
from hcam.intelligence.row_security import (
    REFERENCE_INTEGRATION_TABLES,
    apply_department_scope,
)
from hcam.security.auth import PLATFORM_ADMIN, Principal
from tests.test_phase44_contracts import intent, manifest


POSTGRES_TEST_URL = os.getenv("HCAM_POSTGRES_TEST_URL")
PROBE_ROLE = "hcam_p44_rls_probe"
DEPARTMENT = "P4.4 Generated PostgreSQL"
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not POSTGRES_TEST_URL,
        reason="HCAM_POSTGRES_TEST_URL is required for PostgreSQL integration",
    ),
]


def _admin() -> Principal:
    return Principal(
        actor_id="phase44-postgres-test",
        roles=frozenset({PLATFORM_ADMIN}),
        departments=frozenset({"*"}),
        authentication_method="generated-test",
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


def _clean_department(database: Database) -> None:
    with database.engine.begin() as connection:
        connection.execute(
            text("SELECT set_config('hcam.is_platform_admin', 'true', true)")
        )
        for table in reversed(REFERENCE_INTEGRATION_TABLES):
            connection.execute(
                text(f'DELETE FROM "{table}" WHERE department = :department'),
                {"department": DEPARTMENT},
            )


def test_phase44_postgres_rls_concurrent_claim_circuit_and_revocation() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    provider = manifest(department=DEPARTMENT)
    now = datetime.now(UTC)
    try:
        database.check_ready()
        _clean_department(database)
        with database.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT relname, relrowsecurity, relforcerowsecurity "
                    "FROM pg_class WHERE relname = ANY(:tables)"
                ),
                {"tables": list(REFERENCE_INTEGRATION_TABLES)},
            ).all()
            policies = connection.execute(
                text(
                    "SELECT tablename, count(*) FROM pg_policies "
                    "WHERE tablename = ANY(:tables) GROUP BY tablename"
                ),
                {"tables": list(REFERENCE_INTEGRATION_TABLES)},
            ).all()
        assert {row[0]: row[1:] for row in rows} == {
            table: (True, True) for table in REFERENCE_INTEGRATION_TABLES
        }
        assert {row[0]: row[1] for row in policies} == {
            table: 1 for table in REFERENCE_INTEGRATION_TABLES
        }

        with database.session_factory() as session:
            apply_department_scope(session, _admin())
            service = IntegrationControlService(
                session, enabled=True, manual_queries_enabled=True
            )
            service.register_manifest(provider, principal=_admin())
            for index in (1, 2):
                query = intent(
                    provider, delivery=f"generated.postgres.delivery.{index}"
                )
                query = type(query).model_validate(
                    {
                        **query.model_dump(mode="json"),
                        "parameters": {
                            "record_key": f"gen_postgres_record_{index}",
                            "category": f"gen_postgres_category_{index}",
                        },
                    }
                )
                queued, reused = service.submit_query(query, principal=_admin())
                assert reused is False and queued.state == "queued"

        barrier = Barrier(2)

        def claim(worker_id: str) -> str:
            with database.session_factory.begin() as session:
                apply_department_scope(session, _admin())
                barrier.wait(timeout=10)
                row = IntegrationRepository(session).claim_next(
                    worker_id,
                    concurrent_workers=True,
                    now=now + timedelta(seconds=1),
                )
                assert row is not None
                return row.job_id

        with ThreadPoolExecutor(max_workers=2) as executor:
            claimed = set(
                executor.map(claim, ("generated.worker.one", "generated.worker.two"))
            )
        assert len(claimed) == 2

        with database.session_factory.begin() as session:
            apply_department_scope(session, _admin())
            repository = IntegrationRepository(session)
            for index in range(3):
                circuit = repository.record_circuit_outcome(
                    provider_version_id=provider.provider_version_id,
                    department=provider.department,
                    succeeded=False,
                    now=now + timedelta(seconds=index + 2),
                )
            assert circuit.state == "open" and circuit.failure_count == 3
            assert not repository.circuit_allows(
                provider.provider_version_id, provider.department
            )

        with database.session_factory() as session:
            apply_department_scope(session, _admin())
            service = IntegrationControlService(session, enabled=True)
            revision = service.apply_control(
                department=provider.department,
                scope="provider",
                scope_key=provider.provider_version_id,
                state="revoked",
                expected_version=0,
                reason="Generated PostgreSQL provider revocation test",
                principal=_admin(),
                now=now + timedelta(seconds=6),
            )
            assert revision.state == "revoked" and revision.version == 1

        _drop_probe_role(database)
        with database.engine.begin() as connection:
            connection.execute(text(f"CREATE ROLE {PROBE_ROLE} NOLOGIN"))
            connection.execute(text(f"GRANT USAGE ON SCHEMA public TO {PROBE_ROLE}"))
            connection.execute(
                text(f"GRANT SELECT ON reference_query_jobs TO {PROBE_ROLE}")
            )
            connection.execute(text(f"SET LOCAL ROLE {PROBE_ROLE}"))
            connection.execute(
                text("SELECT set_config('hcam.is_platform_admin', 'false', true)")
            )
            connection.execute(
                text(
                    "SELECT set_config('hcam.allowed_departments', "
                    "'Different Department', true)"
                )
            )
            assert (
                connection.scalar(
                    text(
                        "SELECT count(*) FROM reference_query_jobs "
                        "WHERE department = :department"
                    ),
                    {"department": DEPARTMENT},
                )
                == 0
            )
            connection.execute(text("RESET ROLE"))
    finally:
        _drop_probe_role(database)
        _clean_department(database)
        database.dispose()
