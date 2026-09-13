from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError

from hcam.database import Database
from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.contracts import ReferenceProviderV1
from hcam.intelligence.models import ReferenceProvider
from hcam.intelligence.row_security import apply_department_scope
from hcam.security.auth import Principal


POSTGRES_TEST_URL = os.getenv("HCAM_POSTGRES_TEST_URL")
PROBE_ROLE = "hcam_p40_rls_probe"
PROVIDER_IDS = ("prov_" + "a" * 32, "prov_" + "b" * 32)
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not POSTGRES_TEST_URL,
        reason="HCAM_POSTGRES_TEST_URL is required for PostgreSQL integration",
    ),
]


def _principal(department: str = "*") -> Principal:
    return Principal(
        actor_id="phase40-postgres-test",
        roles=frozenset({"platform.admin"}),
        departments=frozenset({department}),
        authentication_method="generated-test",
    )


def _provider(provider_id: str, department: str, key: str) -> ReferenceProvider:
    now = datetime.now(UTC)
    contract = ReferenceProviderV1(
        provider_id=provider_id,
        provider_key=key,
        version=1,
        department=department,
        policy_ref="ref_" + "a" * 32,
        destination_policy_ref="ref_" + "b" * 32,
        allowed_fields=["record.external_id"],
        owner_id="phase40-postgres-test",
        created_at=now,
        updated_at=now,
    )
    document = contract.model_dump(mode="json")
    return ReferenceProvider(
        provider_id=provider_id,
        department=department,
        provider_key=key,
        status="disabled",
        enabled=False,
        provider_kind="generated_fixture",
        transport_state="absent",
        credential_state="none",
        policy_ref=contract.policy_ref,
        destination_policy_ref=contract.destination_policy_ref,
        allowed_fields=contract.allowed_fields,
        definition=document,
        configuration_digest=canonical_sha256(document),
        generated_only=True,
        owner_id=contract.owner_id,
        last_change_reason="Validate generated PostgreSQL row security",
        created_at=now,
        updated_at=now,
    )


def test_phase40_forced_rls_department_isolation_and_constraints() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    try:
        database.check_ready()
        with database.engine.connect() as connection:
            rls = connection.execute(
                text(
                    "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                    "WHERE relname = 'reference_providers'"
                )
            ).one()
            policy_count = connection.scalar(
                text(
                    "SELECT count(*) FROM pg_policies "
                    "WHERE tablename = 'reference_providers' "
                    "AND policyname = 'reference_providers_department_scope'"
                )
            )
        assert rls == (True, True)
        assert policy_count == 1

        with database.session_factory.begin() as session:
            apply_department_scope(session, _principal())
            session.execute(
                delete(ReferenceProvider).where(
                    ReferenceProvider.provider_id.in_(PROVIDER_IDS)
                )
            )
            session.add_all(
                [
                    _provider(PROVIDER_IDS[0], "Engineering Lab", "p40.rls.lab"),
                    _provider(PROVIDER_IDS[1], "Another Department", "p40.rls.other"),
                ]
            )

        with database.engine.begin() as connection:
            is_superuser = bool(
                connection.scalar(
                    text(
                        "SELECT rolsuper FROM pg_roles WHERE rolname = current_user"
                    )
                )
            )
            if is_superuser:
                connection.execute(text(f"DROP ROLE IF EXISTS {PROBE_ROLE}"))
                connection.execute(text(f"CREATE ROLE {PROBE_ROLE} NOLOGIN"))
                connection.execute(text(f"GRANT USAGE ON SCHEMA public TO {PROBE_ROLE}"))
                connection.execute(
                    text(f"GRANT SELECT ON reference_providers TO {PROBE_ROLE}")
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
                select(ReferenceProvider.provider_id).where(
                    ReferenceProvider.provider_id.in_(PROVIDER_IDS)
                )
            ).scalars().all()
            if is_superuser:
                connection.execute(text("RESET ROLE"))
        assert visible == [PROVIDER_IDS[0]]

        with database.session_factory() as session:
            apply_department_scope(session, _principal())
            with pytest.raises(IntegrityError):
                session.execute(
                    text(
                        "UPDATE reference_providers SET enabled = true "
                        "WHERE provider_id = :provider_id"
                    ),
                    {"provider_id": PROVIDER_IDS[0]},
                )
                session.commit()
            session.rollback()
    finally:
        with database.engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM reference_providers "
                    "WHERE provider_id IN (:first, :second)"
                ),
                {"first": PROVIDER_IDS[0], "second": PROVIDER_IDS[1]},
            )
            is_superuser = bool(
                connection.scalar(
                    text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
                )
            )
            if is_superuser:
                connection.execute(text(f"DROP ROLE IF EXISTS {PROBE_ROLE}"))
        database.dispose()
