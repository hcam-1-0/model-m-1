from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from hcam.intelligence.integrations.canonical import stable_id
from hcam.intelligence.integrations.contracts import (
    AttemptReceiptV1,
    CandidateSetV1,
    ControlRevisionV1,
    ProviderManifestV2,
    QueryIntentV1,
    QueryJobV1,
)
from hcam.intelligence.integrations.auth import AuthenticationResolver
from hcam.intelligence.integrations.matching import build_candidate_set
from hcam.intelligence.integrations.manifests import manifest_digest
from hcam.intelligence.integrations.parser import (
    ProviderResponseError,
    ProviderTransientError,
    parse_generated_response,
)
from hcam.intelligence.integrations.persistence import (
    IntegrationRepository,
    job_contract,
)
from hcam.intelligence.integrations.policy import compile_query_plan
from hcam.intelligence.integrations.providers import ProviderRegistry
from hcam.intelligence.integrations.review import build_review_handoff
from hcam.intelligence.integrations.runtime import GeneratedIntegrationRuntime
from hcam.intelligence.integrations.secrets import NoneGeneratedSecretProvider
from hcam.intelligence.integrations.transport import (
    GeneratedTransportEnvelope,
    InProcessGeneratedTransport,
)
from hcam.intelligence.row_security import apply_department_scope
from hcam.security.auth import Principal


class IntegrationControlError(RuntimeError):
    reason_code = "reference_request_rejected"


class IntegrationDisabledError(IntegrationControlError):
    reason_code = "reference_runtime_disabled"


class IntegrationNotFoundError(IntegrationControlError):
    reason_code = "reference_resource_not_found"


class IntegrationPreconditionError(IntegrationControlError):
    reason_code = "reference_precondition_failed"


class IntegrationControlService:
    def __init__(
        self,
        session: Session,
        *,
        enabled: bool,
        manual_queries_enabled: bool = False,
        hypothesis_enrichment_enabled: bool = False,
    ) -> None:
        self.session = session
        self.enabled = enabled
        self.manual_queries_enabled = manual_queries_enabled
        self.hypothesis_enrichment_enabled = hypothesis_enrichment_enabled
        self.repository = IntegrationRepository(session)

    def _authorize(self, principal: Principal, department: str | None = None) -> None:
        if not self.enabled:
            raise IntegrationDisabledError("generated reference integrations are disabled")
        apply_department_scope(self.session, principal)
        if department is not None and not principal.can_access_department(department):
            raise IntegrationNotFoundError("reference resource was not found")

    def register_manifest(
        self, manifest: ProviderManifestV2, *, principal: Principal
    ) -> ProviderManifestV2:
        self._authorize(principal, manifest.department)
        if manifest.manifest_digest != manifest_digest(manifest):
            raise IntegrationControlError("provider manifest digest does not match")
        if self.repository.manifest(manifest.provider_version_id) is not None:
            raise IntegrationPreconditionError("provider version is already registered")
        self.repository.add_manifest(manifest)
        self.session.commit()
        return manifest

    def list_manifests(self, *, principal: Principal) -> list[ProviderManifestV2]:
        self._authorize(principal)
        return self.repository.list_manifests(principal.allowed_departments)

    def get_manifest(
        self, provider_version_id: str, *, principal: Principal
    ) -> ProviderManifestV2:
        self._authorize(principal)
        manifest = self.repository.manifest(provider_version_id)
        if manifest is None or not principal.can_access_department(manifest.department):
            raise IntegrationNotFoundError("provider version was not found")
        return manifest

    def submit_query(
        self, intent: QueryIntentV1, *, principal: Principal
    ) -> tuple[QueryJobV1, bool]:
        self._authorize(principal, intent.department)
        if intent.requested_by != principal.actor_id:
            raise IntegrationControlError("query requester does not match authenticated actor")
        if intent.lane == "manual_generated" and not self.manual_queries_enabled:
            raise IntegrationDisabledError("the generated manual query lane is disabled")
        if (
            intent.lane == "hypothesis_enrichment_generated"
            and not self.hypothesis_enrichment_enabled
        ):
            raise IntegrationDisabledError(
                "the generated hypothesis enrichment lane is disabled"
            )
        manifest = self.repository.manifest(intent.provider_version_id)
        if manifest is None or manifest.department != intent.department:
            raise IntegrationNotFoundError("provider version was not found")
        plan = compile_query_plan(
            intent,
            manifest,
            control_enabled=self.repository.controls_allow(manifest, intent),
        )
        row, reused = self.repository.add_job(intent, plan)
        self.session.commit()
        return job_contract(row), reused

    def get_job(self, job_id: str, *, principal: Principal) -> QueryJobV1:
        self._authorize(principal)
        row = self.repository.job(job_id)
        if row is None or not principal.can_access_department(row.department):
            raise IntegrationNotFoundError("query job was not found")
        return job_contract(row)

    def cancel_job(
        self,
        job_id: str,
        *,
        expected_version: int,
        principal: Principal,
    ) -> QueryJobV1:
        self._authorize(principal)
        row = self.repository.job(job_id)
        if row is None or not principal.can_access_department(row.department):
            raise IntegrationNotFoundError("query job was not found")
        try:
            self.repository.cancel_job(row, expected_version=expected_version)
            self.session.commit()
        except ValueError as exc:
            self.session.rollback()
            raise IntegrationPreconditionError(str(exc)) from exc
        return job_contract(row)

    def get_candidate_set(
        self, candidate_set_id: str, *, principal: Principal
    ) -> CandidateSetV1:
        self._authorize(principal)
        candidate_set = self.repository.candidate_set(candidate_set_id)
        if candidate_set is None or not principal.can_access_department(
            candidate_set.department
        ):
            raise IntegrationNotFoundError("candidate set was not found")
        return candidate_set

    def controls(self, *, principal: Principal) -> list[ControlRevisionV1]:
        self._authorize(principal)
        return self.repository.list_controls(principal.allowed_departments)

    def apply_control(
        self,
        *,
        department: str,
        scope: str,
        scope_key: str,
        state: str,
        expected_version: int,
        reason: str,
        principal: Principal,
        now: datetime | None = None,
    ) -> ControlRevisionV1:
        self._authorize(principal, department)
        prior = self.repository.latest_control(department, scope, scope_key)
        actual_version = prior.version if prior is not None else 0
        if actual_version != expected_version:
            raise IntegrationPreconditionError("reference control version does not match")
        revision = ControlRevisionV1(
            revision_id=stable_id(
                "rctl", department, scope, scope_key, actual_version + 1
            ),
            department=department,
            scope=scope,
            scope_key=scope_key,
            state=state,
            version=actual_version + 1,
            actor_id=principal.actor_id,
            reason=reason,
            recorded_at=now or datetime.now(UTC),
        )
        self.repository.add_control_revision(revision)
        self.session.commit()
        return revision


class GeneratedQueryWorker:
    """Synchronous generated-only worker used by bounded tests and lab orchestration."""

    def __init__(
        self,
        session: Session,
        providers: ProviderRegistry,
        *,
        enabled: bool,
        environment: str,
        worker_id: str = "generated.reference.worker",
    ) -> None:
        self.session = session
        self.repository = IntegrationRepository(session)
        self.runtime = GeneratedIntegrationRuntime(enabled=enabled, environment=environment)
        self.transport = InProcessGeneratedTransport(providers)
        self.authentication = AuthenticationResolver(NoneGeneratedSecretProvider())
        self.worker_id = worker_id

    def run_one(self, *, now: datetime | None = None) -> QueryJobV1 | None:
        self.runtime.require_enabled()
        current = now or datetime.now(UTC)
        row = self.repository.claim_next(self.worker_id, now=current)
        if row is None:
            return None
        intent = QueryIntentV1.model_validate(row.intent_payload)
        manifest = self._manifest(row.provider_version_id)
        if not self.repository.controls_allow(manifest, intent):
            self.repository.add_attempt(
                AttemptReceiptV1(
                    attempt_id=stable_id("ratt", row.job_id, row.attempt_count),
                    job_id=row.job_id,
                    outcome="revoked",
                    reason_code="query.revoked",
                    recorded_at=current,
                ),
                department=row.department,
            )
            self.repository.quarantine_job(
                row,
                worker_id=self.worker_id,
                now=current,
            )
            self.session.commit()
            return job_contract(row)
        if not self.repository.circuit_allows(
            manifest.provider_version_id, manifest.department
        ):
            self.repository.quarantine_job(
                row,
                worker_id=self.worker_id,
                reason_code="query.circuit_open",
                now=current,
            )
            self.session.commit()
            return job_contract(row)
        plan = compile_query_plan(
            intent,
            manifest,
            control_enabled=True,
        )
        try:
            self.authentication.resolve(manifest.auth_profile)
            payload = self.transport.execute(
                GeneratedTransportEnvelope(plan=plan, parameters=dict(intent.parameters))
            )
            records, normalized_digest, _completeness = parse_generated_response(
                payload, allowed_fields=list(plan.requested_fields)
            )
            candidate_set = build_candidate_set(
                query_id=intent.query_id,
                department=intent.department,
                query_fields=dict(intent.parameters),
                records=records,
                minimum_evidence=min(2, len(intent.parameters)),
            )
            handoff = build_review_handoff(candidate_set, now=current)
            self.repository.add_candidate_set(candidate_set, now=current)
            self.repository.add_review_handoff(handoff)
            self.repository.add_attempt(
                AttemptReceiptV1(
                    attempt_id=stable_id("ratt", row.job_id, row.attempt_count),
                    job_id=row.job_id,
                    outcome="succeeded",
                    reason_code="query.succeeded",
                    normalized_digest=normalized_digest,
                    recorded_at=current,
                ),
                department=row.department,
            )
            self.repository.complete_job(
                row,
                worker_id=self.worker_id,
                result_digest=candidate_set.candidate_set_digest,
                now=current,
            )
            self.repository.record_circuit_outcome(
                provider_version_id=manifest.provider_version_id,
                department=manifest.department,
                succeeded=True,
                now=current,
            )
        except ProviderResponseError as exc:
            transient = isinstance(exc, ProviderTransientError)
            self.repository.add_attempt(
                AttemptReceiptV1(
                    attempt_id=stable_id("ratt", row.job_id, row.attempt_count),
                    job_id=row.job_id,
                    outcome="transient_failure" if transient else "permanent_failure",
                    reason_code=exc.reason_code,
                    recorded_at=current,
                ),
                department=row.department,
            )
            self.repository.fail_job(
                row,
                worker_id=self.worker_id,
                transient=transient,
                reason_code=exc.reason_code,
                now=current,
            )
            self.repository.record_circuit_outcome(
                provider_version_id=manifest.provider_version_id,
                department=manifest.department,
                succeeded=False,
                now=current,
            )
        self.session.commit()
        return job_contract(row)

    def _manifest(self, provider_version_id: str) -> ProviderManifestV2:
        manifest = self.repository.manifest(provider_version_id)
        if manifest is None:
            raise IntegrationNotFoundError("provider version was not found")
        return manifest
