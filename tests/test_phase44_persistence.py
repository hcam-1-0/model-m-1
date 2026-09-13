from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select

from hcam.database import Database
from hcam.intelligence.integrations.catalogue import build_catalogue_snapshot
from hcam.intelligence.integrations.generated_provider import StaticGeneratedProvider
from hcam.intelligence.integrations.persistence import (
    IntegrationRepository,
    ReferenceCandidateSet,
    ReferenceCatalogueRecord,
    ReferenceCatalogueSnapshot,
    ReferenceCircuitState,
    ReferenceIntegrationOutbox,
    ReferenceQueryAttempt,
    ReferenceReviewHandoff,
)
from hcam.intelligence.integrations.providers import ProviderRegistry
from hcam.intelligence.integrations.service import (
    GeneratedQueryWorker,
    IntegrationControlService,
)
from hcam.security.auth import PLATFORM_ADMIN, Principal
from tests.test_phase44_contracts import NOW, intent, manifest


def principal(actor: str = "generated-admin") -> Principal:
    return Principal(
        actor_id=actor,
        roles=frozenset({PLATFORM_ADMIN}),
        departments=frozenset({"*"}),
        authentication_method="generated-test",
    )


def database(tmp_path) -> Database:
    result = Database(
        f"sqlite:///{(tmp_path / 'phase44.db').as_posix()}",
        allow_unversioned_schema=True,
    )
    result.create_schema()
    return result


def test_persistence_deduplicates_catalogue_and_keeps_normalized_records(
    tmp_path,
) -> None:
    db = database(tmp_path)
    provider = manifest()
    records = [{"record_key": "gen_record_001", "category": "gen_category_a"}]
    try:
        with db.session_factory.begin() as session:
            repository = IntegrationRepository(session)
            repository.add_manifest(provider, now=NOW)
            first = build_catalogue_snapshot(
                provider_version_id=provider.provider_version_id,
                department=provider.department,
                records=records,
                observed_at=NOW,
            )
            assert repository.add_snapshot(first)[1] is True
            refreshed = build_catalogue_snapshot(
                provider_version_id=provider.provider_version_id,
                department=provider.department,
                records=records,
                observed_at=NOW + timedelta(hours=1),
                first_observed_at=NOW,
            )
            assert repository.add_snapshot(refreshed)[1] is False
        with db.session_factory() as session:
            assert (
                session.scalar(
                    select(func.count(ReferenceCatalogueSnapshot.snapshot_id))
                )
                == 1
            )
            assert (
                session.scalar(select(func.count(ReferenceCatalogueRecord.row_id))) == 1
            )
            snapshot = session.scalar(select(ReferenceCatalogueSnapshot))
            assert snapshot is not None
            assert snapshot.raw_response_retained is False
            assert snapshot.last_observed_at == NOW + timedelta(hours=1)
    finally:
        db.dispose()


def test_generated_worker_persists_attempt_candidate_review_and_no_raw_response(
    tmp_path,
) -> None:
    db = database(tmp_path)
    provider = manifest()
    query = intent(provider)
    providers = ProviderRegistry()
    providers.register(
        StaticGeneratedProvider(
            provider.provider_version_id,
            [
                {
                    "record_key": "gen_record_001",
                    "category": "gen_category_a",
                    "region": "gen_region_west",
                }
            ],
        )
    )
    try:
        with db.session_factory() as session:
            service = IntegrationControlService(
                session, enabled=True, manual_queries_enabled=True
            )
            service.register_manifest(provider, principal=principal())
            job, reused = service.submit_query(query, principal=principal())
            assert reused is False and job.state == "queued"
        with db.session_factory() as session:
            result = GeneratedQueryWorker(
                session,
                providers,
                enabled=True,
                environment="test",
            ).run_one(now=job.created_at + timedelta(seconds=1))
            assert result is not None and result.state == "succeeded"
        with db.session_factory() as session:
            attempt = session.scalar(select(ReferenceQueryAttempt))
            candidate = session.scalar(select(ReferenceCandidateSet))
            review = session.scalar(select(ReferenceReviewHandoff))
            assert attempt is not None and attempt.raw_response_retained is False
            assert (
                candidate is not None and candidate.identity_state == "not_established"
            )
            assert candidate.mandatory_review is True and candidate.operational is False
            assert review is not None and review.authority_class == "mandatory_review"
            outbox_payloads = list(
                session.scalars(select(ReferenceIntegrationOutbox.payload))
            )
            serialized = str(outbox_payloads).lower()
            for prohibited in ("gen_record_001", "gen_category_a", "raw_response"):
                assert prohibited not in serialized
    finally:
        db.dispose()


def test_persistent_worker_retries_transient_failures_then_stops_at_bound(
    tmp_path,
) -> None:
    db = database(tmp_path)
    provider = manifest()
    providers = ProviderRegistry()
    providers.register(
        StaticGeneratedProvider(provider.provider_version_id, [], fault="transient")
    )
    try:
        with db.session_factory() as session:
            service = IntegrationControlService(
                session, enabled=True, manual_queries_enabled=True
            )
            service.register_manifest(provider, principal=principal())
            queued, _ = service.submit_query(intent(provider), principal=principal())
        for attempt_number in range(1, 4):
            with db.session_factory() as session:
                result = GeneratedQueryWorker(
                    session, providers, enabled=True, environment="test"
                ).run_one(
                    now=queued.created_at + timedelta(seconds=attempt_number)
                )
                assert result is not None
                assert result.state == ("queued" if attempt_number < 3 else "failed")
        with db.session_factory() as session:
            assert (
                session.scalar(select(func.count(ReferenceQueryAttempt.attempt_id)))
                == 3
            )
            circuit = session.scalar(select(ReferenceCircuitState))
            assert circuit is not None
            assert circuit.state == "open"
            assert circuit.failure_count == 3
        with db.session_factory() as session:
            second = intent(provider, delivery="generated.delivery.002")
            second = type(second).model_validate(
                {
                    **second.model_dump(mode="json"),
                    "parameters": {
                        "record_key": "gen_record_002",
                        "category": "gen_category_b",
                    },
                }
            )
            service = IntegrationControlService(
                session, enabled=True, manual_queries_enabled=True
            )
            queued, reused = service.submit_query(second, principal=principal())
            assert reused is False and queued.state == "queued"
        with db.session_factory() as session:
            quarantined = GeneratedQueryWorker(
                session, providers, enabled=True, environment="test"
            ).run_one(now=queued.created_at + timedelta(seconds=4))
            assert quarantined is not None
            assert quarantined.state == "quarantined"
            assert quarantined.reason_code == "query.circuit_open"
            assert (
                session.scalar(select(func.count(ReferenceQueryAttempt.attempt_id)))
                == 3
            )
    finally:
        db.dispose()


def test_queued_job_is_quarantined_when_provider_control_is_revoked(tmp_path) -> None:
    db = database(tmp_path)
    provider = manifest()
    providers = ProviderRegistry()
    providers.register(StaticGeneratedProvider(provider.provider_version_id, []))
    try:
        with db.session_factory() as session:
            service = IntegrationControlService(
                session, enabled=True, manual_queries_enabled=True
            )
            service.register_manifest(provider, principal=principal())
            queued, reused = service.submit_query(
                intent(provider), principal=principal()
            )
            assert reused is False and queued.state == "queued"
            revision = service.apply_control(
                department=provider.department,
                scope="provider",
                scope_key=provider.provider_version_id,
                state="revoked",
                expected_version=0,
                reason="Generated provider is revoked before execution",
                principal=principal(),
                now=NOW,
            )
            assert revision.version == 1 and revision.state == "revoked"
        with db.session_factory() as session:
            quarantined = GeneratedQueryWorker(
                session, providers, enabled=True, environment="test"
            ).run_one(now=queued.created_at + timedelta(seconds=1))
            assert quarantined is not None
            assert quarantined.state == "quarantined"
            assert quarantined.reason_code == "query.revoked"
            attempt = session.scalar(select(ReferenceQueryAttempt))
            assert attempt is not None
            assert attempt.outcome == "revoked"
            assert attempt.raw_response_retained is False
    finally:
        db.dispose()
