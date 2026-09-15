from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import Field, field_validator, model_validator

from hcam.intelligence.contracts import ActorId, ContractModel, Department, Digest, StableName
from hcam.intelligence.integrations.bounds import (
    MAX_CANDIDATES,
    MAX_JOB_ATTEMPTS,
    MAX_MANIFEST_OPERATIONS,
    MAX_REQUEST_FIELDS,
    MAX_RESPONSE_FIELDS,
    MAX_SIGNALS_PER_CANDIDATE,
    validate_safe_document,
)


ProviderId = Annotated[str, Field(pattern=r"^prov_[0-9a-f]{32}$")]
ProviderVersionId = Annotated[str, Field(pattern=r"^pver_[0-9a-f]{32}$")]
QueryId = Annotated[str, Field(pattern=r"^qry_[0-9a-f]{32}$")]
JobId = Annotated[str, Field(pattern=r"^rjob_[0-9a-f]{32}$")]
AttemptId = Annotated[str, Field(pattern=r"^ratt_[0-9a-f]{32}$")]
SnapshotId = Annotated[str, Field(pattern=r"^rcat_[0-9a-f]{32}$")]
CandidateSetId = Annotated[str, Field(pattern=r"^cset_[0-9a-f]{32}$")]
CandidateId = Annotated[str, Field(pattern=r"^cand_[0-9a-f]{32}$")]
ControlRevisionId = Annotated[str, Field(pattern=r"^rctl_[0-9a-f]{32}$")]
ReviewHandoffId = Annotated[str, Field(pattern=r"^rrev_[0-9a-f]{32}$")]
HypothesisEvidenceRevisionId = Annotated[
    str, Field(pattern=r"^rhev_[0-9a-f]{32}$")
]
ReasonCode = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
FieldName = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.]{0,63}$")]
GeneratedValue = Annotated[str, Field(pattern=r"^gen_[a-z0-9][a-z0-9._-]{0,126}$")]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return value.astimezone(UTC)


class AuthProfileV1(ContractModel):
    profile_id: StableName
    mode: Literal[
        "none_generated",
        "secret_lease",
        "database_envelope_disabled",
        "extension_disabled",
    ]
    secret_ref: Annotated[str, Field(pattern=r"^secret_ref_[0-9a-f]{32}$")] | None = None
    extension_id: StableName | None = None
    enabled: bool = False

    @model_validator(mode="after")
    def mode_is_consistent(self) -> AuthProfileV1:
        if self.mode == "none_generated":
            if self.secret_ref is not None or self.extension_id is not None:
                raise ValueError("generated authentication cannot reference secrets")
        elif self.secret_ref is None:
            raise ValueError("non-generated authentication requires an opaque secret reference")
        if self.mode == "extension_disabled" and self.extension_id is None:
            raise ValueError("extension authentication requires an extension identifier")
        if self.mode != "extension_disabled" and self.extension_id is not None:
            raise ValueError("only extension authentication may name an extension")
        if self.enabled and self.mode != "none_generated":
            raise ValueError("non-generated authentication is disabled in P4.4")
        return self


class DestinationPolicyV1(ContractModel):
    destination_id: StableName
    transport: Literal["in_process_generated"] = "in_process_generated"
    service_identity: Literal["generated.reference.local"] = "generated.reference.local"
    route_id: StableName
    redirects_allowed: Literal[False] = False
    environment_proxies_allowed: Literal[False] = False
    network_allowed: Literal[False] = False


class ProviderOperationV1(ContractModel):
    operation_id: StableName
    action: Literal["catalogue.read_generated", "query.read_generated"]
    request_fields: Annotated[list[FieldName], Field(max_length=MAX_REQUEST_FIELDS)]
    response_fields: Annotated[
        list[FieldName], Field(min_length=1, max_length=MAX_RESPONSE_FIELDS)
    ]
    idempotent: Literal[True] = True
    page_size_maximum: Annotated[int, Field(ge=1, le=200)] = 50

    @field_validator("request_fields", "response_fields")
    @classmethod
    def fields_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("operation fields must be unique")
        for field_name in value:
            validate_safe_document({field_name: "gen_value"})
        return value


class ProviderManifestV2(ContractModel):
    contract_type: Literal["hcam.reference.provider-manifest.v2"] = (
        "hcam.reference.provider-manifest.v2"
    )
    provider_id: ProviderId
    provider_version_id: ProviderVersionId
    provider_key: StableName
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    department: Department
    status: Literal[
        "validated_generated", "approved_disabled", "suspended", "revoked", "retired"
    ]
    adapter_kind: Literal["generated_static"] = "generated_static"
    auth_profile: AuthProfileV1
    destination: DestinationPolicyV1
    purposes: Annotated[list[ReasonCode], Field(min_length=1, max_length=32)]
    operations: Annotated[
        list[ProviderOperationV1], Field(min_length=1, max_length=MAX_MANIFEST_OPERATIONS)
    ]
    manifest_digest: Digest
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def manifest_is_consistent(self) -> ProviderManifestV2:
        operation_ids = [item.operation_id for item in self.operations]
        if len(operation_ids) != len(set(operation_ids)):
            raise ValueError("provider operation identifiers must be unique")
        if len(self.purposes) != len(set(self.purposes)):
            raise ValueError("provider purposes must be unique")
        if self.status == "validated_generated" and not self.auth_profile.enabled:
            raise ValueError("validated generated providers require generated authentication")
        return self


class QueryIntentV1(ContractModel):
    contract_type: Literal["hcam.reference.query-intent.v1"] = (
        "hcam.reference.query-intent.v1"
    )
    query_id: QueryId
    delivery_id: StableName
    provider_version_id: ProviderVersionId
    operation_id: StableName
    department: Department
    purpose_code: ReasonCode
    requested_fields: Annotated[
        list[FieldName], Field(min_length=1, max_length=MAX_REQUEST_FIELDS)
    ]
    parameters: Annotated[dict[FieldName, GeneratedValue], Field(max_length=MAX_REQUEST_FIELDS)]
    lane: Literal["manual_generated", "hypothesis_enrichment_generated"]
    hypothesis_id: Annotated[str, Field(pattern=r"^hyp_[0-9a-f]{32}$")] | None = None
    requested_by: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    requested_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    _requested_at_utc = field_validator("requested_at")(_utc)

    @model_validator(mode="after")
    def intent_is_consistent(self) -> QueryIntentV1:
        if len(self.requested_fields) != len(set(self.requested_fields)):
            raise ValueError("requested fields must be unique")
        if self.lane == "hypothesis_enrichment_generated" and self.hypothesis_id is None:
            raise ValueError("hypothesis enrichment requires a hypothesis identifier")
        if self.lane == "manual_generated" and self.hypothesis_id is not None:
            raise ValueError("manual queries cannot bind a hypothesis")
        validate_safe_document(self.parameters)
        return self


class CompiledQueryPlanV1(ContractModel):
    contract_type: Literal["hcam.reference.compiled-query-plan.v1"] = (
        "hcam.reference.compiled-query-plan.v1"
    )
    query_id: QueryId
    provider_id: ProviderId
    provider_version_id: ProviderVersionId
    operation_id: StableName
    department: Department
    purpose_code: ReasonCode
    requested_fields: Annotated[
        list[FieldName], Field(min_length=1, max_length=MAX_REQUEST_FIELDS)
    ]
    parameter_digest: Digest
    adapter_kind: Literal["generated_static"] = "generated_static"
    auth_profile_id: StableName
    destination_id: StableName
    semantic_key: Digest
    delivery_key: Digest
    plan_digest: Digest
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class CatalogueRecordV1(ContractModel):
    record_id: Annotated[str, Field(pattern=r"^grec_[0-9a-f]{32}$")]
    fields: Annotated[dict[FieldName, GeneratedValue], Field(min_length=1, max_length=MAX_RESPONSE_FIELDS)]
    record_digest: Digest

    @field_validator("fields")
    @classmethod
    def fields_are_safe(cls, value: dict[str, str]) -> dict[str, str]:
        validate_safe_document(value)
        return value


class CatalogueSnapshotV1(ContractModel):
    contract_type: Literal["hcam.reference.catalogue-snapshot.v1"] = (
        "hcam.reference.catalogue-snapshot.v1"
    )
    snapshot_id: SnapshotId
    provider_version_id: ProviderVersionId
    department: Department
    records: Annotated[list[CatalogueRecordV1], Field(max_length=2048)]
    fingerprint: Digest
    completeness: Literal["complete", "partial"]
    first_observed_at: datetime
    last_observed_at: datetime
    observed_at: datetime
    stale_at: datetime
    generated_only: Literal[True] = True
    raw_response_retained: Literal[False] = False

    _first_observed_at_utc = field_validator("first_observed_at")(_utc)
    _last_observed_at_utc = field_validator("last_observed_at")(_utc)
    _observed_at_utc = field_validator("observed_at")(_utc)
    _stale_at_utc = field_validator("stale_at")(_utc)

    @model_validator(mode="after")
    def chronology_is_valid(self) -> CatalogueSnapshotV1:
        if not (
            self.first_observed_at
            <= self.last_observed_at
            <= self.observed_at
            < self.stale_at
        ):
            raise ValueError("catalogue stale time must follow observation time")
        ids = [item.record_id for item in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("catalogue record identifiers must be unique")
        return self


class QueryJobV1(ContractModel):
    contract_type: Literal["hcam.reference.query-job.v1"] = "hcam.reference.query-job.v1"
    job_id: JobId
    query_id: QueryId
    department: Department
    state: Literal["queued", "leased", "succeeded", "failed", "cancelled", "quarantined"]
    attempt_count: Annotated[int, Field(ge=0, le=MAX_JOB_ATTEMPTS)] = 0
    lease_owner: StableName | None = None
    lease_until: datetime | None = None
    reason_code: ReasonCode
    plan_digest: Digest
    semantic_key: Digest
    delivery_key: Digest
    result_digest: Digest | None = None
    created_at: datetime
    updated_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    _created_at_utc = field_validator("created_at")(_utc)
    _updated_at_utc = field_validator("updated_at")(_utc)

    @model_validator(mode="after")
    def lease_is_consistent(self) -> QueryJobV1:
        leased = self.state == "leased"
        if leased != (self.lease_owner is not None and self.lease_until is not None):
            raise ValueError("job lease fields are inconsistent")
        if self.updated_at < self.created_at:
            raise ValueError("job update cannot precede creation")
        return self


class AttemptReceiptV1(ContractModel):
    attempt_id: AttemptId
    job_id: JobId
    outcome: Literal["succeeded", "transient_failure", "permanent_failure", "revoked", "stale"]
    reason_code: ReasonCode
    normalized_digest: Digest | None = None
    raw_response_retained: Literal[False] = False
    recorded_at: datetime
    _recorded_at_utc = field_validator("recorded_at")(_utc)


class FieldEvidenceV1(ContractModel):
    field: FieldName
    comparator_version: StableName
    state: Literal[
        "exact", "normalized", "approximate", "missing", "stale", "invalid", "contradicts"
    ]
    score: Annotated[float, Field(ge=0, le=1)]
    query_value_digest: Digest
    candidate_value_digest: Digest | None = None


class CandidateV1(ContractModel):
    candidate_id: CandidateId
    rank: Annotated[int, Field(ge=1, le=MAX_CANDIDATES)]
    evidence: Annotated[
        list[FieldEvidenceV1], Field(min_length=1, max_length=MAX_SIGNALS_PER_CANDIDATE)
    ]
    aggregate_score: Annotated[float, Field(ge=0, le=1)]
    contradiction_count: Annotated[int, Field(ge=0, le=MAX_SIGNALS_PER_CANDIDATE)]
    identity_state: Literal["not_established"] = "not_established"


class CandidateSetV1(ContractModel):
    contract_type: Literal["hcam.reference.candidate-set.v1"] = (
        "hcam.reference.candidate-set.v1"
    )
    candidate_set_id: CandidateSetId
    query_id: QueryId
    department: Department
    outcome: Literal["candidates", "no_match", "ambiguous", "abstain"]
    reason_codes: Annotated[list[ReasonCode], Field(min_length=1, max_length=16)]
    candidates: Annotated[list[CandidateV1], Field(max_length=MAX_CANDIDATES)]
    candidate_set_digest: Digest
    identity_state: Literal["not_established"] = "not_established"
    mandatory_review: Literal[True] = True
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def candidates_are_consistent(self) -> CandidateSetV1:
        ranks = [item.rank for item in self.candidates]
        if ranks != list(range(1, len(ranks) + 1)):
            raise ValueError("candidate ranks must be contiguous")
        if self.outcome != "candidates" and self.candidates:
            raise ValueError("non-candidate outcome cannot expose candidates")
        return self


class ReviewHandoffV1(ContractModel):
    contract_type: Literal["hcam.reference.review-handoff.v1"] = (
        "hcam.reference.review-handoff.v1"
    )
    handoff_id: ReviewHandoffId
    candidate_set_id: CandidateSetId
    department: Department
    authority_class: Literal["mandatory_review"] = "mandatory_review"
    state: Literal["pending_review"] = "pending_review"
    limitations: Annotated[list[ReasonCode], Field(min_length=1, max_length=16)]
    evidence_digest: Digest
    created_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False
    _created_at_utc = field_validator("created_at")(_utc)


class HypothesisEvidenceRevisionV1(ContractModel):
    contract_type: Literal["hcam.reference.hypothesis-evidence-revision.v1"] = (
        "hcam.reference.hypothesis-evidence-revision.v1"
    )
    revision_id: HypothesisEvidenceRevisionId
    hypothesis_id: Annotated[str, Field(pattern=r"^hyp_[0-9a-f]{32}$")]
    candidate_set_id: CandidateSetId
    department: Department
    role: Literal[
        "supports", "contradicts", "missing", "stale", "supersedes", "retracts"
    ]
    source_digest: Digest
    revision: Annotated[int, Field(ge=1, le=2_147_483_647)]
    supersedes_revision_id: HypothesisEvidenceRevisionId | None = None
    identity_state: Literal["not_established"] = "not_established"
    recorded_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    _recorded_at_utc = field_validator("recorded_at")(_utc)

    @model_validator(mode="after")
    def correction_reference_is_consistent(self) -> HypothesisEvidenceRevisionV1:
        correction = self.role in {"supersedes", "retracts"}
        if correction != (self.supersedes_revision_id is not None):
            raise ValueError("correction evidence requires exactly one prior revision")
        return self


class ControlRevisionV1(ContractModel):
    revision_id: ControlRevisionId
    department: Department
    scope: Literal["organization", "department", "provider", "operation", "purpose", "auth_profile"]
    scope_key: StableName
    state: Literal["enabled_generated", "suspended", "revoked"]
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    actor_id: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    recorded_at: datetime
    generated_only: Literal[True] = True
    _recorded_at_utc = field_validator("recorded_at")(_utc)


class WorkflowExecutionV1(ContractModel):
    execution_id: Annotated[str, Field(pattern=r"^wexec_[0-9a-f]{32}$")]
    job_id: JobId
    adapter_kind: Literal["generated_simulator", "future_disabled"]
    outcome: Literal["accepted", "duplicate", "timeout", "cancelled", "revoked", "late", "disabled"]
    reason_code: ReasonCode
    result_digest: Digest | None = None
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class GeneratedProviderPayload(ContractModel):
    records: Annotated[list[dict[str, Any]], Field(max_length=MAX_CANDIDATES)]
    completeness: Literal["complete", "partial"] = "complete"
    fault: Literal["none", "transient", "permanent", "oversized", "malformed", "revoked", "slow"] = "none"

    @field_validator("records")
    @classmethod
    def records_are_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validate_safe_document(value)
        return value
