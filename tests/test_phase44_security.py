from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from hcam.intelligence.integrations.auth import (
    AuthenticationPolicyError,
    AuthenticationResolver,
)
from hcam.intelligence.integrations.bounds import BoundsError, validate_safe_document
from hcam.intelligence.integrations.canonical import (
    CanonicalizationError,
    canonical_bytes,
)
from hcam.intelligence.integrations.contracts import (
    AuthProfileV1,
    CandidateSetV1,
    CatalogueSnapshotV1,
    DestinationPolicyV1,
    GeneratedProviderPayload,
    ProviderOperationV1,
    QueryJobV1,
)
from hcam.intelligence.integrations.destinations import (
    DestinationPolicyError,
    compile_destination,
)
from hcam.intelligence.integrations.generated_provider import StaticGeneratedProvider
from hcam.intelligence.integrations.jobs import JobQueue, JobStateError
from hcam.intelligence.integrations.manifests import ManifestError, ManifestRegistry
from hcam.intelligence.integrations.metrics import IntegrationMetrics
from hcam.intelligence.integrations.parser import (
    ProviderResponseError,
    parse_generated_response,
)
from hcam.intelligence.integrations.policy import PolicyDeniedError, compile_query_plan
from hcam.intelligence.integrations.runtime import GeneratedIntegrationRuntime
from hcam.intelligence.integrations.secrets import SecretLease
from hcam.security.auth import (
    AUTHENTICATION_ROLES,
    KNOWN_ROLES,
    REFERENCE_INTEGRATION_ROLES,
)
from hcam.settings import Settings
from tests.test_phase44_api import application, headers
from tests.test_phase44_contracts import NOW, intent, manifest


def test_generated_reference_integration_is_production_forbidden() -> None:
    with pytest.raises(ValueError, match="forbidden in production"):
        Settings(
            database_url="postgresql+psycopg://generated:generated@127.0.0.1/generated",
            environment="production",
            intelligence_generated_reference_integrations_enabled=True,
        )


def test_reference_roles_are_additive_to_the_historical_core_registry() -> None:
    assert REFERENCE_INTEGRATION_ROLES
    assert REFERENCE_INTEGRATION_ROLES.isdisjoint(KNOWN_ROLES)
    assert AUTHENTICATION_ROLES == KNOWN_ROLES | REFERENCE_INTEGRATION_ROLES


def test_api_enforces_exact_capability_and_department_scope(tmp_path) -> None:
    app = application(tmp_path)
    provider = manifest()
    try:
        with TestClient(app) as client:
            denied = client.post(
                "/reference-integrations/providers",
                json=provider.model_dump(mode="json"),
                headers=headers("reference.provider.read"),
            )
            assert denied.status_code == 403
            created = client.post(
                "/reference-integrations/providers",
                json=provider.model_dump(mode="json"),
                headers=headers("reference.provider.create_generated"),
            )
            assert created.status_code == 201
            hidden = client.get(
                f"/reference-integrations/providers/{provider.provider_version_id}",
                headers=headers(
                    "reference.provider.read", department="Generated-Department-2"
                ),
            )
            assert hidden.status_code == 404
            listed = client.get(
                "/reference-integrations/providers",
                headers=headers(
                    "reference.provider.read", department="Generated-Department-2"
                ),
            )
            assert listed.status_code == 200 and listed.json()["total"] == 0
    finally:
        app.state.database.dispose()


@pytest.mark.parametrize(
    "document",
    [
        {"private_key": "gen_value"},
        {1: "gen_value"},
        {"value": "x" * 4097},
        list(range(2049)),
        {f"field_{index}": index for index in range(129)},
        {"value": b"generated"},
    ],
)
def test_document_bounds_reject_sensitive_and_unbounded_values(
    document: object,
) -> None:
    with pytest.raises(BoundsError):
        validate_safe_document(document)
    with pytest.raises(CanonicalizationError):
        canonical_bytes({"value": "x" * 100}, maximum_bytes=4)


def test_contract_cross_field_guards_fail_closed() -> None:
    provider = manifest()
    with pytest.raises(ValidationError):
        provider.model_copy(
            update={"operations": [provider.operations[0], provider.operations[0]]}
        ).model_validate(
            provider.model_copy(
                update={"operations": [provider.operations[0], provider.operations[0]]}
            ).model_dump(mode="json")
        )
    with pytest.raises(ValidationError):
        ProviderOperationV1(
            operation_id="generated.duplicate.fields.v1",
            action="query.read_generated",
            request_fields=["record_key", "record_key"],
            response_fields=["region"],
        )
    with pytest.raises(ValidationError):
        intent(provider).model_copy(
            update={"requested_fields": ["region", "region"]}
        ).model_validate(
            intent(provider)
            .model_copy(update={"requested_fields": ["region", "region"]})
            .model_dump(mode="json")
        )
    with pytest.raises(ValidationError):
        intent(provider).model_copy(
            update={"lane": "hypothesis_enrichment_generated"}
        ).model_validate(
            intent(provider)
            .model_copy(update={"lane": "hypothesis_enrichment_generated"})
            .model_dump(mode="json")
        )
    with pytest.raises(ValidationError):
        CatalogueSnapshotV1(
            snapshot_id="rcat_" + "1" * 32,
            provider_version_id=provider.provider_version_id,
            department=provider.department,
            records=[],
            fingerprint="sha256:" + "1" * 64,
            completeness="complete",
            first_observed_at=NOW,
            last_observed_at=NOW,
            observed_at=NOW,
            stale_at=NOW - timedelta(seconds=1),
        )
    with pytest.raises(ValidationError):
        QueryJobV1(
            job_id="rjob_" + "1" * 32,
            query_id="qry_" + "1" * 32,
            department=provider.department,
            state="leased",
            reason_code="query.leased",
            plan_digest="sha256:" + "1" * 64,
            semantic_key="sha256:" + "2" * 64,
            delivery_key="sha256:" + "3" * 64,
            created_at=NOW,
            updated_at=NOW,
        )
    with pytest.raises(ValidationError):
        CandidateSetV1(
            candidate_set_id="cset_" + "1" * 32,
            query_id="qry_" + "1" * 32,
            department=provider.department,
            outcome="no_match",
            reason_codes=["candidate.no_match"],
            candidates=[],
            candidate_set_digest="sha256:" + "1" * 64,
            unexpected=True,
        )


def test_auth_destination_runtime_and_metrics_reject_unapproved_surfaces() -> None:
    profile = AuthProfileV1(
        profile_id="generated.auth.none.v1", mode="none_generated", enabled=True
    )

    class UnsafeSecretProvider:
        def resolve(self, profile: AuthProfileV1) -> SecretLease:
            return SecretLease(
                lease_id="generated.lease",
                profile_id=profile.profile_id,
                mode=profile.mode,
                contains_secret=True,
            )

    with pytest.raises(AuthenticationPolicyError):
        AuthenticationResolver(UnsafeSecretProvider()).resolve(profile)
    unsafe_destination = DestinationPolicyV1.model_construct(
        destination_id="generated.destination.invalid.v1",
        route_id="generated.route.invalid.v1",
        transport="in_process_generated",
        network_allowed=True,
        redirects_allowed=False,
        environment_proxies_allowed=False,
        service_identity="generated.reference.local",
    )
    with pytest.raises(DestinationPolicyError):
        compile_destination(unsafe_destination)
    with pytest.raises(ValueError):
        GeneratedIntegrationRuntime(enabled=True, environment="production")
    with pytest.raises(RuntimeError):
        GeneratedIntegrationRuntime().require_enabled()
    metrics = IntegrationMetrics()
    metrics.record("query", "succeeded")
    assert metrics.snapshot() == {"query:succeeded": 1}
    with pytest.raises(ValueError):
        metrics.record("camera", "succeeded")
    with pytest.raises(ValueError):
        metrics.record("query", "dispatched")


def test_manifest_policy_provider_parser_and_job_negative_paths() -> None:
    provider = manifest()
    query = intent(provider)
    plan = compile_query_plan(query, provider, control_enabled=True)
    with pytest.raises(ManifestError):
        ManifestRegistry().get(provider.provider_version_id)
    bad_digest = provider.model_copy(update={"manifest_digest": "sha256:" + "1" * 64})
    with pytest.raises(PolicyDeniedError):
        compile_query_plan(query, bad_digest, control_enabled=True)
    with pytest.raises(PolicyDeniedError):
        compile_query_plan(
            query.model_copy(update={"purpose_code": "generated.denied"}),
            provider,
            control_enabled=True,
        )
    with pytest.raises(PolicyDeniedError):
        compile_query_plan(
            query.model_copy(update={"operation_id": "generated.missing.v1"}),
            provider,
            control_enabled=True,
        )
    with pytest.raises(PolicyDeniedError):
        compile_query_plan(
            query.model_copy(update={"requested_fields": ["not_allowlisted"]}),
            provider,
            control_enabled=True,
        )
    with pytest.raises(PolicyDeniedError):
        compile_query_plan(
            query.model_copy(update={"parameters": {"unknown": "gen_value"}}),
            provider,
            control_enabled=True,
        )
    wrong_plan = plan.model_copy(update={"provider_version_id": "pver_" + "f" * 32})
    with pytest.raises(ValueError):
        StaticGeneratedProvider(provider.provider_version_id, []).execute(
            wrong_plan, dict(query.parameters)
        )
    with pytest.raises(ProviderResponseError):
        parse_generated_response(
            GeneratedProviderPayload(records=[], fault="permanent"),
            allowed_fields=["record_key"],
        )
    queue = JobQueue()
    with pytest.raises(JobStateError):
        queue.get("rjob_" + "f" * 32)
    first, _ = queue.submit(plan, now=NOW)
    collision = plan.model_copy(
        update={"semantic_key": "sha256:" + "9" * 64, "query_id": "qry_" + "9" * 32}
    )
    with pytest.raises(JobStateError):
        queue.submit(collision, now=NOW)
    assert queue.list(department="Generated-Department-9") == []
    assert queue.claim("generated.worker", now=NOW) is not None
    failed = queue.fail(
        first.job_id,
        "generated.worker",
        transient=False,
        reason_code="provider.permanent",
        now=NOW,
    )
    assert failed.state == "failed"


def test_api_problem_paths_are_sanitized_and_controls_are_versioned(tmp_path) -> None:
    app = application(tmp_path)
    provider = manifest()
    try:
        with TestClient(app) as client:
            health = client.get(
                "/reference-integrations/health",
                headers=headers("reference.provider.read"),
            )
            assert health.status_code == 200
            assert health.json()["network_allowed"] is False
            missing = client.get(
                "/reference-integrations/providers/pver_" + "f" * 32,
                headers=headers("reference.provider.read"),
            )
            assert missing.status_code == 404
            invalid_etag = client.post(
                "/reference-integrations/controls",
                json={
                    "department": provider.department,
                    "scope": "organization",
                    "scope_key": "generated.reference",
                    "state": "enabled_generated",
                },
                headers=headers("reference.control.manage_generated"),
            )
            assert invalid_etag.status_code == 428
            created = client.post(
                "/reference-integrations/controls",
                json={
                    "department": provider.department,
                    "scope": "organization",
                    "scope_key": "generated.reference",
                    "state": "enabled_generated",
                },
                headers={
                    **headers("reference.control.manage_generated"),
                    "If-Match": '"0"',
                },
            )
            assert created.status_code == 200
            stale = client.post(
                "/reference-integrations/controls",
                json={
                    "department": provider.department,
                    "scope": "organization",
                    "scope_key": "generated.reference",
                    "state": "revoked",
                },
                headers={
                    **headers("reference.control.manage_generated"),
                    "If-Match": '"0"',
                },
            )
            assert stale.status_code == 412
            listed = client.get(
                "/reference-integrations/controls",
                headers=headers("reference.control.read"),
            )
            assert listed.status_code == 200 and listed.json()["total"] == 1
            candidate = client.get(
                "/reference-integrations/candidate-sets/cset_" + "f" * 32,
                headers=headers("reference.candidate.read"),
            )
            assert candidate.status_code == 404
    finally:
        app.state.database.dispose()
