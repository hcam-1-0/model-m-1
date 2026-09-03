from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from typing import Annotated, Any, ClassVar, Literal, TypeVar

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    ValidationInfo,
    field_validator,
    model_validator,
)


MAX_EVALUATION_RECORD_BYTES = 1024 * 1024
ZERO_DIGEST = f"sha256:{'0' * 64}"

Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
StableId = Annotated[
    str,
    Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"),
]
SemanticVersion = Annotated[
    str,
    Field(pattern=r"^[1-9][0-9]*\.[0-9]+\.[0-9]+(?:-[a-z0-9.-]+)?$"),
]
ClassId = Annotated[
    str,
    Field(
        min_length=3,
        max_length=128,
        pattern=r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$",
    ),
]
NonBlankText = Annotated[str, Field(min_length=1, max_length=1000)]
ShortText = Annotated[str, Field(min_length=1, max_length=256)]
MetricName = Annotated[
    str,
    Field(min_length=2, max_length=128, pattern=r"^[a-z][a-z0-9_.-]*$"),
]
SourceTier = Literal["S0", "S1", "S2", "S3", "S4", "S5"]


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be timezone-aware UTC")
    return value


UtcDateTime = Annotated[datetime, AfterValidator(_require_utc)]

_PROHIBITED_KEYS = {
    "biometric",
    "credential",
    "face_embedding",
    "face_template",
    "government_data",
    "image_bytes",
    "local_path",
    "media_bytes",
    "owner_record",
    "password",
    "person_embedding",
    "secret",
    "secret_ref",
    "stream_url",
    "token",
    "video",
    "video_bytes",
    "watchlist_match",
}
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:rtsp|rtsps)://", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|secret|token)\s*[:=]", re.IGNORECASE),
)


class EvaluationContractSafetyError(ValueError):
    """Raised without echoing sensitive values into error messages."""


class EvaluationContractModel(BaseModel):
    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )


def _scan_safe(value: object, *, key: str | None = None) -> None:
    normalized_key = key.casefold() if key else None
    if normalized_key in _PROHIBITED_KEYS:
        raise EvaluationContractSafetyError("evaluation record contains a prohibited field")
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            _scan_safe(child, key=str(child_key))
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _scan_safe(child)
        return
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise EvaluationContractSafetyError("evaluation record cannot contain binary data")
    if isinstance(value, str):
        if any(pattern.search(value) for pattern in _SENSITIVE_VALUE_PATTERNS):
            raise EvaluationContractSafetyError(
                "evaluation record contains a prohibited sensitive value"
            )
        if "\\" in value or re.match(r"^[A-Za-z]:/", value):
            raise EvaluationContractSafetyError(
                "evaluation record cannot contain a local filesystem path"
            )


def _jsonable(value: BaseModel | Mapping[str, object]) -> dict[str, object]:
    if isinstance(value, BaseModel):
        document = value.model_dump(mode="json", by_alias=True)
    else:
        document = dict(value)
    _scan_safe(document)
    return document


def canonical_evaluation_json(
    value: BaseModel | Mapping[str, object],
    *,
    max_bytes: int = MAX_EVALUATION_RECORD_BYTES,
) -> str:
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    document = _jsonable(value)
    try:
        serialized = json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("evaluation record must contain canonical JSON data") from exc
    if len(serialized.encode("utf-8")) > max_bytes:
        raise ValueError("evaluation record exceeds the maximum payload size")
    return serialized


def canonical_digest(value: BaseModel | Mapping[str, object]) -> str:
    serialized = canonical_evaluation_json(value)
    return f"sha256:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"


class DigestBoundRecord(EvaluationContractModel):
    digest_field: ClassVar[str]

    @model_validator(mode="after")
    def digest_matches_content(self, info: ValidationInfo) -> DigestBoundRecord:
        if info.context and info.context.get("skip_digest_check"):
            return self
        field = self.digest_field
        actual = getattr(self, field)
        content = self.model_dump(mode="json", by_alias=True, exclude={field})
        if actual != canonical_digest(content):
            raise ValueError("record digest does not match canonical content")
        return self


DigestRecordT = TypeVar("DigestRecordT", bound=DigestBoundRecord)


def seal_record(
    record_type: type[DigestRecordT],
    document: Mapping[str, object],
) -> DigestRecordT:
    payload = dict(document)
    payload[record_type.digest_field] = ZERO_DIGEST
    unsealed = record_type.model_validate(
        payload,
        context={"skip_digest_check": True},
    )
    normalized = unsealed.model_dump(
        mode="json",
        by_alias=True,
        exclude={record_type.digest_field},
    )
    payload = dict(normalized)
    payload[record_type.digest_field] = canonical_digest(normalized)
    return record_type.model_validate(payload)


class ApprovalRecordV1(EvaluationContractModel):
    record_id: StableId
    owner_id: StableId
    status: Literal["pending", "owner_recorded", "owner_approved"]
    decided_at: UtcDateTime | None = None
    reason: NonBlankText

    @field_validator("reason")
    @classmethod
    def reason_is_trimmed(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("reason must not have outer whitespace")
        return value

    @model_validator(mode="after")
    def decision_time_matches_status(self) -> ApprovalRecordV1:
        if self.status == "pending" and self.decided_at is not None:
            raise ValueError("pending approval cannot have a decision timestamp")
        if self.status != "pending" and self.decided_at is None:
            raise ValueError("recorded approval requires a decision timestamp")
        return self


class ResearchReferenceV1(EvaluationContractModel):
    reference_id: StableId
    url: HttpUrl
    title: ShortText
    publisher: ShortText
    accessed_on: date
    evidence_kind: Literal[
        "official_documentation",
        "official_repository",
        "official_release",
        "license_text",
        "research_paper",
    ]
    supports_claim: NonBlankText
    no_download_performed: Literal[True] = True

    @field_validator("url")
    @classmethod
    def reference_is_clean_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https" or value.username or value.password:
            raise ValueError("research references require credential-free HTTPS")
        if value.query or value.fragment:
            raise ValueError("research references cannot contain query or fragment")
        return value


class SourceEvidenceV1(EvaluationContractModel):
    source_id: StableId
    source_tier: SourceTier
    source_version: ShortText
    method: Literal[
        "deterministic_generation",
        "team_created",
        "public_research",
        "private_lab",
        "prohibited_reference",
    ]
    authorization_state: Literal[
        "authorized",
        "planning_only",
        "research_only",
        "prohibited",
    ]
    authorization_record_id: StableId | None = None
    license_id: ShortText
    allowed_uses: Annotated[list[StableId], Field(min_length=1, max_length=32)]
    prohibited_uses: Annotated[list[StableId], Field(min_length=1, max_length=32)]
    privacy_classification: Literal[
        "generated_non_personal",
        "consent_required",
        "review_required",
        "prohibited",
    ]
    no_external_input: bool
    no_download_performed: bool
    references: Annotated[list[ResearchReferenceV1], Field(max_length=16)] = Field(
        default_factory=list
    )

    @field_validator("allowed_uses", "prohibited_uses")
    @classmethod
    def usage_sets_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("source usage entries must be unique")
        return value

    @model_validator(mode="after")
    def tier_policy_is_fail_closed(self) -> SourceEvidenceV1:
        if set(self.allowed_uses) & set(self.prohibited_uses):
            raise ValueError("allowed and prohibited source uses cannot overlap")
        expected = {
            "S0": ("deterministic_generation", "authorized"),
            "S1": ("team_created", "planning_only"),
            "S2": ("public_research", "research_only"),
            "S3": ("public_research", "research_only"),
            "S4": ("private_lab", "prohibited"),
            "S5": ("prohibited_reference", "prohibited"),
        }[self.source_tier]
        if (self.method, self.authorization_state) != expected:
            raise ValueError("source tier does not match its authorization policy")
        if self.source_tier == "S0":
            if (
                not self.no_external_input
                or not self.no_download_performed
                or self.authorization_record_id != "D-P3.1-001"
                or self.references
                or self.privacy_classification != "generated_non_personal"
            ):
                raise ValueError("S0 must be generated-only under D-P3.1-001")
        elif self.source_tier in {"S2", "S3"}:
            if (
                self.no_external_input
                or not self.no_download_performed
                or not self.references
                or self.authorization_record_id is not None
            ):
                raise ValueError("research-only sources require references and no download")
        elif self.authorization_state == "prohibited":
            if self.authorization_record_id is not None or not self.no_download_performed:
                raise ValueError("prohibited sources cannot have use authorization")
        return self


class ManifestReferenceV1(EvaluationContractModel):
    record_id: StableId
    version: SemanticVersion
    digest: Digest


class RetentionPolicyV1(EvaluationContractModel):
    data_class: Literal[
        "generated.analytics.fixture",
        "generated.analytics.annotation",
        "generated.analytics.report",
        "research.metadata.only",
    ]
    maximum_retention_hours: Annotated[int, Field(ge=0, le=2_160)]
    access_roles: Annotated[list[StableId], Field(min_length=1, max_length=8)]
    export_allowed: Literal[False] = False
    training_reuse_allowed: Literal[False] = False
    deletion_proof: Literal["audited_metadata_only"] = "audited_metadata_only"


class ContentInventoryItemV1(EvaluationContractModel):
    item_id: StableId
    content_type: Literal[
        "generated_metadata",
        "programmatic_asset",
        "annotation",
        "prediction",
        "metric_report",
        "research_record",
    ]
    artifact_name: Annotated[
        str,
        Field(pattern=r"^[a-z0-9][a-z0-9_.-]{2,127}$"),
    ]
    digest: Digest
    count: Annotated[int, Field(ge=1, le=10_000_000)]
    split: Literal["train", "validation", "test", "none"]
    sequence_id: StableId | None = None
    group_key: StableId | None = None
    class_ids: Annotated[list[ClassId], Field(max_length=128)] = Field(
        default_factory=list
    )
    slices: Annotated[list[StableId], Field(max_length=128)] = Field(
        default_factory=list
    )


class SplitPolicyV1(EvaluationContractModel):
    method: Literal["grouped_immutable"] = "grouped_immutable"
    allowed_splits: Annotated[
        list[Literal["train", "validation", "test"]],
        Field(min_length=3, max_length=3),
    ]
    required_group_keys: Annotated[list[StableId], Field(min_length=1, max_length=16)]
    final_test_frozen: bool
    final_test_access_count: Annotated[int, Field(ge=0, le=1_000_000)]
    exact_duplicate_count: Annotated[int, Field(ge=0, le=1_000_000)]
    cross_split_group_count: Annotated[int, Field(ge=0, le=1_000_000)]
    leakage_status: Literal["pass", "fail", "not_run"]

    @model_validator(mode="after")
    def split_state_is_consistent(self) -> SplitPolicyV1:
        if self.allowed_splits != ["train", "validation", "test"]:
            raise ValueError("allowed splits must have canonical order")
        if len(self.required_group_keys) != len(set(self.required_group_keys)):
            raise ValueError("required split group keys must be unique")
        has_failure = self.exact_duplicate_count > 0 or self.cross_split_group_count > 0
        if self.leakage_status == "pass" and has_failure:
            raise ValueError("passing split policy cannot contain leakage")
        if self.leakage_status == "fail" and not has_failure:
            raise ValueError("failed split policy requires leakage evidence")
        return self


class DatasetManifestV1(DigestBoundRecord):
    digest_field: ClassVar[str] = "manifest_digest"
    contract_type: Literal["hcam.analytics.dataset-manifest.v1"] = (
        "hcam.analytics.dataset-manifest.v1"
    )
    dataset_id: StableId
    semantic_version: SemanticVersion
    manifest_digest: Digest
    status: Literal["draft", "approved", "retired"]
    purpose: NonBlankText
    sources: Annotated[list[SourceEvidenceV1], Field(min_length=1, max_length=32)]
    inventory: Annotated[
        list[ContentInventoryItemV1],
        Field(min_length=1, max_length=10_000),
    ]
    taxonomy_version: StableId
    annotation_specification: ManifestReferenceV1
    transformations: Annotated[list[ManifestReferenceV1], Field(max_length=64)] = Field(
        default_factory=list
    )
    parents: Annotated[list[ManifestReferenceV1], Field(max_length=16)] = Field(
        default_factory=list
    )
    retention: RetentionPolicyV1
    split_policy: SplitPolicyV1
    known_gaps: Annotated[list[NonBlankText], Field(min_length=1, max_length=128)]
    exclusions: Annotated[list[StableId], Field(min_length=1, max_length=128)]
    approval: ApprovalRecordV1
    created_at: UtcDateTime
    review_due_on: date

    @model_validator(mode="after")
    def approved_dataset_uses_only_authorized_sources(self) -> DatasetManifestV1:
        if self.status == "approved":
            if self.approval.status != "owner_approved":
                raise ValueError("approved dataset requires owner approval")
            if any(source.authorization_state != "authorized" for source in self.sources):
                raise ValueError("approved dataset cannot use unapproved source tiers")
            if self.split_policy.leakage_status != "pass":
                raise ValueError("approved dataset requires passing leakage checks")
        return self


class GeneratorIdentityV1(EvaluationContractModel):
    generator_id: StableId
    generator_version: SemanticVersion
    code_digest: Digest
    configuration_digest: Digest
    external_inputs: Annotated[list[StableId], Field(max_length=16)] = Field(
        default_factory=list
    )


class FixtureCoverageV1(EvaluationContractModel):
    domain: Literal["detection", "tracking", "geometry", "synthetic_plate", "misuse"]
    scenario: StableId
    expected_outcome: Literal["pass", "reject", "abstain"]
    class_id: ClassId | None = None
    script: Literal["Latin", "Devanagari", "Gujarati"] | None = None


class FileHashV1(EvaluationContractModel):
    artifact_name: Annotated[
        str,
        Field(pattern=r"^[a-z0-9][a-z0-9_.-]{2,127}$"),
    ]
    digest: Digest
    bytes: Annotated[int, Field(ge=1, le=MAX_EVALUATION_RECORD_BYTES)]
    record_count: Annotated[int, Field(ge=1, le=1_000_000)]


class FixtureManifestV1(DigestBoundRecord):
    digest_field: ClassVar[str] = "manifest_digest"
    contract_type: Literal["hcam.analytics.fixture-manifest.v1"] = (
        "hcam.analytics.fixture-manifest.v1"
    )
    fixture_suite_id: StableId
    semantic_version: SemanticVersion
    manifest_digest: Digest
    generator: GeneratorIdentityV1
    seeds: Annotated[list[int], Field(min_length=1, max_length=256)]
    template_digests: Annotated[list[Digest], Field(min_length=1, max_length=256)]
    expected_contracts: Annotated[list[StableId], Field(min_length=1, max_length=64)]
    expected_failure_codes: Annotated[list[StableId], Field(min_length=1, max_length=64)]
    coverage: Annotated[list[FixtureCoverageV1], Field(min_length=1, max_length=2_000)]
    declared_omissions: Annotated[list[NonBlankText], Field(min_length=1, max_length=128)]
    generated_only: Literal[True] = True
    prohibited_sources_absent: Literal[True] = True
    files: Annotated[list[FileHashV1], Field(min_length=1, max_length=256)]
    approval: ApprovalRecordV1
    created_at: UtcDateTime

    @field_validator("seeds", "template_digests", "expected_contracts")
    @classmethod
    def fixture_lists_are_unique(cls, value: list[Any]) -> list[Any]:
        if len(value) != len(set(value)):
            raise ValueError("fixture manifest entries must be unique")
        return value

    @model_validator(mode="after")
    def generator_has_no_external_inputs(self) -> FixtureManifestV1:
        if self.generator.external_inputs:
            raise ValueError("generated fixtures cannot declare external inputs")
        if self.approval.status != "owner_approved":
            raise ValueError("fixture manifest requires owner approval")
        return self


class AttributeDefinitionV1(EvaluationContractModel):
    name: StableId
    value_type: Literal["boolean", "enum", "integer", "number", "text"]
    required: bool
    allowed_values: Annotated[list[ShortText], Field(max_length=64)] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def enum_values_match_type(self) -> AttributeDefinitionV1:
        if (self.value_type == "enum") != bool(self.allowed_values):
            raise ValueError("only enum attributes may define allowed values")
        return self


class AnnotationRuleSetV1(EvaluationContractModel):
    coordinate_system: Literal["normalized_top_left"] = "normalized_top_left"
    geometry_types: Annotated[
        list[Literal["bounding_box", "line", "polygon", "text_region"]],
        Field(min_length=1, max_length=4),
    ]
    ignore_rules: Annotated[list[NonBlankText], Field(min_length=1, max_length=64)]
    uncertain_rule: NonBlankText
    occlusion_values: Annotated[
        list[Literal["none", "partial", "heavy", "unknown"]],
        Field(min_length=4, max_length=4),
    ]
    truncated_rule: NonBlankText
    track_lifecycle_rules: Annotated[list[NonBlankText], Field(min_length=1, max_length=64)]
    synthetic_plate_rules: Annotated[list[NonBlankText], Field(min_length=1, max_length=64)]
    normalization_rules: Annotated[list[NonBlankText], Field(min_length=1, max_length=64)]


class QualityPolicyV1(EvaluationContractModel):
    automated_checks: Annotated[list[StableId], Field(min_length=1, max_length=128)]
    qa_sample_basis_points: Annotated[int, Field(ge=1, le=10_000)]
    duplicate_annotation_basis_points: Annotated[int, Field(ge=0, le=10_000)]
    adjudication_required: bool
    proposed_error_rate_ceiling: Annotated[float, Field(ge=0, le=1)]
    calibration_evidence_required: Literal[True] = True


class AnnotationSpecificationV1(DigestBoundRecord):
    digest_field: ClassVar[str] = "specification_digest"
    contract_type: Literal["hcam.analytics.annotation-specification.v1"] = (
        "hcam.analytics.annotation-specification.v1"
    )
    specification_id: StableId
    semantic_version: SemanticVersion
    specification_digest: Digest
    status: Literal["draft", "approved", "retired"]
    taxonomy_version: StableId
    tasks: Annotated[
        list[Literal["detection", "tracking", "geometry", "synthetic_plate"]],
        Field(min_length=1, max_length=4),
    ]
    rules: AnnotationRuleSetV1
    attributes: Annotated[list[AttributeDefinitionV1], Field(min_length=1, max_length=128)]
    import_format: StableId
    export_format: StableId
    quality_policy: QualityPolicyV1
    approval: ApprovalRecordV1
    version_history: Annotated[list[ManifestReferenceV1], Field(max_length=64)] = Field(
        default_factory=list
    )
    created_at: UtcDateTime

    @model_validator(mode="after")
    def specification_is_unique_and_approved(self) -> AnnotationSpecificationV1:
        if len(self.tasks) != len(set(self.tasks)):
            raise ValueError("annotation tasks must be unique")
        names = [attribute.name for attribute in self.attributes]
        if len(names) != len(set(names)):
            raise ValueError("annotation attribute names must be unique")
        if self.status == "approved" and self.approval.status != "owner_approved":
            raise ValueError("approved annotation specification requires owner approval")
        return self


class ResolutionFieldV1(EvaluationContractModel):
    state: Literal["resolved", "unresolved"]
    value: ShortText | None = None
    digest: Digest | None = None
    blocker: StableId | None = None

    @model_validator(mode="after")
    def resolution_is_consistent(self) -> ResolutionFieldV1:
        if self.state == "resolved":
            if self.value is None or self.blocker is not None:
                raise ValueError("resolved field requires a value and no blocker")
        elif self.value is not None or self.digest is not None or self.blocker is None:
            raise ValueError("unresolved field requires only a blocker")
        return self


class ArtifactLicenseV1(EvaluationContractModel):
    component: Literal["code", "weights", "training_data", "font", "runtime"]
    license_id: ResolutionFieldV1
    redistribution: Literal["allowed", "restricted", "prohibited", "unresolved"]
    commercial_or_government_use: Literal[
        "allowed",
        "restricted",
        "prohibited",
        "unresolved",
    ]
    notice_required: bool | None = None


class CandidateArtifactManifestV1(DigestBoundRecord):
    digest_field: ClassVar[str] = "manifest_digest"
    contract_type: Literal["hcam.analytics.candidate-artifact-manifest.v1"] = (
        "hcam.analytics.candidate-artifact-manifest.v1"
    )
    candidate_id: StableId
    semantic_version: SemanticVersion
    manifest_digest: Digest
    intended_role: Literal[
        "detector_reference",
        "detector_low_compute",
        "detector_balanced",
        "detector_accuracy",
        "stream_local_tracker",
        "ocr_latin_small",
        "ocr_latin_medium",
        "ocr_devanagari",
        "ocr_gujarati_fast",
        "ocr_gujarati_best",
        "plate_region_detector",
    ]
    source_tier: Literal["S0", "S3"]
    source_reference: ResearchReferenceV1 | None = None
    source_revision: ResolutionFieldV1
    artifact_identity: ResolutionFieldV1
    licenses: Annotated[list[ArtifactLicenseV1], Field(min_length=1, max_length=8)]
    lineage: ResolutionFieldV1
    model_card: ResolutionFieldV1
    sbom: ResolutionFieldV1
    supported_taxonomy: Annotated[list[ClassId], Field(max_length=128)]
    runtime_expectations: Annotated[list[StableId], Field(min_length=1, max_length=16)]
    export_expectations: Annotated[list[StableId], Field(min_length=1, max_length=16)]
    known_limits: Annotated[list[NonBlankText], Field(min_length=1, max_length=64)]
    eligibility: Literal["blocked", "research_only", "eligible", "retired"]
    blockers: Annotated[list[StableId], Field(min_length=1, max_length=64)]
    approval: ApprovalRecordV1
    recorded_at: UtcDateTime

    @model_validator(mode="after")
    def candidate_does_not_claim_unproven_eligibility(self) -> CandidateArtifactManifestV1:
        if self.source_tier == "S3" and self.source_reference is None:
            raise ValueError("S3 candidate requires a research reference")
        if self.source_tier == "S0" and self.source_reference is not None:
            raise ValueError("S0 candidate cannot use an external source reference")
        if self.eligibility in {"eligible", "retired"}:
            fields = (
                self.source_revision,
                self.artifact_identity,
                self.lineage,
                self.model_card,
                self.sbom,
            )
            if self.blockers or any(field.state != "resolved" for field in fields):
                raise ValueError("eligible candidate cannot contain unresolved blockers")
            if self.approval.status != "owner_approved":
                raise ValueError("eligible candidate requires owner approval")
        elif not self.blockers:
            raise ValueError("blocked candidate requires explicit blockers")
        return self


class SourceRevisionV1(EvaluationContractModel):
    commit: Annotated[str, Field(pattern=r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")]
    dirty_worktree: bool


class CommandInvocationV1(EvaluationContractModel):
    executable: StableId
    arguments: Annotated[list[ShortText], Field(max_length=64)] = Field(
        default_factory=list
    )
    network_access: Literal["denied"] = "denied"
    gpu_access: Literal["denied"] = "denied"
    secrets_required: Literal[False] = False


class HardwareProfileV1(EvaluationContractModel):
    profile_id: StableId
    cpu: ShortText
    logical_processors: Annotated[int, Field(ge=1, le=4_096)]
    memory_mib: Annotated[int, Field(ge=256, le=16_777_216)]
    gpu: ShortText
    os: ShortText
    python_version: Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]
    container_engine: ShortText
    authorized_claims: Annotated[list[StableId], Field(min_length=1, max_length=32)]
    prohibited_claims: Annotated[list[StableId], Field(min_length=1, max_length=32)]


class RunArtifactV1(EvaluationContractModel):
    artifact_name: Annotated[
        str,
        Field(pattern=r"^[a-z0-9][a-z0-9_.-]{2,127}$"),
    ]
    digest: Digest
    media_free: Literal[True] = True


class EvaluationRunManifestV1(DigestBoundRecord):
    digest_field: ClassVar[str] = "manifest_digest"
    contract_type: Literal["hcam.analytics.evaluation-run-manifest.v1"] = (
        "hcam.analytics.evaluation-run-manifest.v1"
    )
    run_id: StableId
    semantic_version: SemanticVersion
    manifest_digest: Digest
    executed_at: UtcDateTime
    source: SourceRevisionV1
    operator_id: StableId
    command: CommandInvocationV1
    seed: Annotated[int, Field(ge=0, le=2_147_483_647)]
    dataset: ManifestReferenceV1
    fixture_suite: ManifestReferenceV1
    candidate: ManifestReferenceV1 | None = None
    pipeline_digest: Digest
    taxonomy_version: StableId
    metric_suite_digest: Digest
    configuration_digest: Digest
    hardware: HardwareProfileV1
    dependency_lock_digest: Digest
    container_profile_digest: Digest | None = None
    precision: Literal["not_applicable", "float32", "float16", "int8"]
    warmup_iterations: Annotated[int, Field(ge=0, le=10_000)]
    repetitions: Annotated[int, Field(ge=1, le=100_000)]
    batch_size: Annotated[int, Field(ge=1, le=100_000)]
    concurrency: Annotated[int, Field(ge=1, le=10_000)]
    timeout_seconds: Annotated[int, Field(ge=1, le=86_400)]
    maximum_memory_mib: Annotated[int, Field(ge=1, le=16_777_216)]
    result_artifacts: Annotated[list[RunArtifactV1], Field(min_length=1, max_length=128)]
    failed_gates: Annotated[list[StableId], Field(max_length=128)] = Field(
        default_factory=list
    )
    warnings: Annotated[list[NonBlankText], Field(max_length=128)] = Field(
        default_factory=list
    )
    reproducibility_status: Literal["pass", "fail", "not_run"]
    approval: ApprovalRecordV1

    @model_validator(mode="after")
    def generated_baseline_has_no_candidate_runtime(self) -> EvaluationRunManifestV1:
        if self.command.network_access != "denied" or self.command.gpu_access != "denied":
            raise ValueError("P3.1 evaluation runs must be offline and GPU-free")
        if self.precision != "not_applicable" and self.candidate is None:
            raise ValueError("generated-only metric run must use not_applicable precision")
        if self.reproducibility_status == "pass" and self.failed_gates:
            raise ValueError("passing run cannot contain failed gates")
        return self


class PopulationDefinitionV1(EvaluationContractModel):
    population_id: StableId
    description: NonBlankText
    sample_count: Annotated[int, Field(ge=0, le=1_000_000_000)]
    class_id: ClassId | None = None
    slice_id: StableId | None = None


class MetricValueV1(EvaluationContractModel):
    metric_name: MetricName
    domain: Literal["detection", "tracking", "geometry", "synthetic_anpr", "system"]
    population_id: StableId
    value: float
    unit: Literal[
        "ratio",
        "count",
        "milliseconds",
        "characters",
        "events_per_stream_hour",
    ]
    numerator: Annotated[int, Field(ge=0, le=1_000_000_000)] | None = None
    denominator: Annotated[int, Field(ge=0, le=1_000_000_000)] | None = None
    uncertainty: Annotated[float, Field(ge=0)] | None = None
    outcome: Literal["pass", "fail", "reported"]

    @field_validator("value")
    @classmethod
    def metric_value_is_finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("metric value must be finite")
        return value

    @model_validator(mode="after")
    def ratio_counts_are_consistent(self) -> MetricValueV1:
        if (self.numerator is None) != (self.denominator is None):
            raise ValueError("metric numerator and denominator must appear together")
        if self.numerator is not None and self.numerator > self.denominator:
            raise ValueError("metric numerator cannot exceed denominator")
        return self


class HardGateResultV1(EvaluationContractModel):
    gate_id: StableId
    metric_name: MetricName
    comparator: Literal["gte", "lte", "eq"]
    threshold: float
    observed: float
    outcome: Literal["pass", "fail", "proposal_only"]
    owner_approved: bool

    @field_validator("threshold", "observed")
    @classmethod
    def gate_values_are_finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("gate values must be finite")
        return value

    @model_validator(mode="after")
    def unapproved_gate_is_only_a_proposal(self) -> HardGateResultV1:
        if not self.owner_approved and self.outcome != "proposal_only":
            raise ValueError("unapproved numeric gate must remain proposal_only")
        return self


class MetricReportV1(DigestBoundRecord):
    digest_field: ClassVar[str] = "report_digest"
    contract_type: Literal["hcam.analytics.metric-report.v1"] = (
        "hcam.analytics.metric-report.v1"
    )
    report_id: StableId
    semantic_version: SemanticVersion
    report_digest: Digest
    metric_suite_id: StableId
    metric_suite_version: SemanticVersion
    generated_at: UtcDateTime
    populations: Annotated[
        list[PopulationDefinitionV1],
        Field(min_length=1, max_length=10_000),
    ]
    metrics: Annotated[list[MetricValueV1], Field(min_length=1, max_length=100_000)]
    invalid_prediction_handling: NonBlankText
    abstention_handling: NonBlankText
    missing_prediction_handling: NonBlankText
    baseline_report: ManifestReferenceV1 | None = None
    regressions: Annotated[list[StableId], Field(max_length=1_000)] = Field(
        default_factory=list
    )
    hard_gates: Annotated[list[HardGateResultV1], Field(max_length=1_000)] = Field(
        default_factory=list
    )
    failed_gates: Annotated[list[StableId], Field(max_length=1_000)] = Field(
        default_factory=list
    )
    approval: ApprovalRecordV1

    @model_validator(mode="after")
    def report_references_are_complete(self) -> MetricReportV1:
        populations = [population.population_id for population in self.populations]
        if len(populations) != len(set(populations)):
            raise ValueError("metric populations must be unique")
        known = set(populations)
        if any(metric.population_id not in known for metric in self.metrics):
            raise ValueError("metric references an unknown population")
        gate_failures = {
            gate.gate_id for gate in self.hard_gates if gate.outcome == "fail"
        }
        if set(self.failed_gates) != gate_failures:
            raise ValueError("failed gate list must match hard-gate outcomes")
        return self


EVALUATION_RECORD_MODELS: tuple[type[DigestBoundRecord], ...] = (
    DatasetManifestV1,
    FixtureManifestV1,
    AnnotationSpecificationV1,
    CandidateArtifactManifestV1,
    EvaluationRunManifestV1,
    MetricReportV1,
)


def evaluation_contract_bundle() -> dict[str, object]:
    return {
        "contract_format": "hcam.analytics.evaluation-contract-bundle.v1",
        "maximum_record_bytes": MAX_EVALUATION_RECORD_BYTES,
        "digest_algorithm": "sha256",
        "canonical_json": "utf8_sorted_keys_compact_ascii_no_nan",
        "source_tiers": {
            "S0": "authorized_generated_only",
            "S1": "planning_only_exact_owner_record",
            "S2": "research_only_no_download",
            "S3": "research_only_no_download",
            "S4": "prohibited_new_authorization_required",
            "S5": "prohibited",
        },
        "records": {
            model.model_fields["contract_type"].default: model.model_json_schema(
                mode="validation"
            )
            for model in EVALUATION_RECORD_MODELS
        },
        "prohibited_fields": sorted(_PROHIBITED_KEYS),
    }
