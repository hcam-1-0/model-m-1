from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, Field, model_validator

from hcam.analytics.contracts import ContractModel, ImmutableDigest


ANPR_GENERATED_SOURCE_ID = "DATA-PLATE-GEN-R0"
ANPR_TOKEN_POLICY_ID = "hcam.anpr.synthetic-non-issuable.v1"
ANPR_TOKEN_PATTERN = r"^SYN-[A-Z0-9]{4}-[A-Z0-9]{4}$"
ANPR_GENERATOR_VERSION = "sha256:" + hashlib.sha256(
    b"hcam.anpr.generator.v1:sha256-domain-separated:visible-syn-4x4"
).hexdigest()
ANPR_TOKEN_POLICY_VERSION = "sha256:" + hashlib.sha256(
    b"hcam.anpr.synthetic-non-issuable.v1:ascii-upper-digit:mixed:zero-retention"
).hexdigest()
ANPR_SPLIT_POLICY_ID = "hcam.anpr.sealed-splits.v1"
ANPR_SPLIT_POLICY_VERSION = "sha256:" + hashlib.sha256(
    b"hcam.anpr.sealed-splits.v1:independent-namespaces:final-test-holdouts"
).hexdigest()
MAX_ANPR_REQUEST_BYTES = 4 * 1024
MAX_ANPR_DOCUMENT_DEPTH = 8
MAX_ANPR_DOCUMENT_NODES = 256
MAX_ANPR_LOCAL_SAMPLES = 10_000

_TOKEN_PATTERN = re.compile(ANPR_TOKEN_PATTERN, flags=re.ASCII)

AnprRequestId = Annotated[str, Field(pattern=r"^anprreq_[0-9a-f]{32}$")]
AnprScript = Literal["latin"]
AnprLayout = Literal["single_line", "two_line"]
AnprTokenClass = Literal["synthetic_non_issuable"]
AnprSplit = Literal[
    "contract_fixture",
    "development",
    "validation",
    "final_test",
]


def _validate_namespaced_token(value: str) -> str:
    if not value.isascii() or _TOKEN_PATTERN.fullmatch(value) is None:
        raise ValueError("token must use the approved synthetic namespace")
    payload = value.removeprefix("SYN-").replace("-", "")
    if not any(character.isalpha() for character in payload) or not any(
        character.isdigit() for character in payload
    ):
        raise ValueError("synthetic token payload must contain letters and digits")
    return value


SyntheticPlateToken = Annotated[
    str,
    Field(min_length=13, max_length=13, pattern=ANPR_TOKEN_PATTERN),
    AfterValidator(_validate_namespaced_token),
]


class GeneratedTokenRequestV1(ContractModel):
    """Seed-only request; it deliberately has no text, file, media, or URL field."""

    contract_type: Literal["hcam.anpr.generated-token-request.v1"] = (
        "hcam.anpr.generated-token-request.v1"
    )
    request_id: AnprRequestId
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: ImmutableDigest
    policy_id: Literal["hcam.anpr.synthetic-non-issuable.v1"] = ANPR_TOKEN_POLICY_ID
    policy_version: ImmutableDigest
    seed: Annotated[int, Field(ge=0, le=4_294_967_295)]
    sample_index: Annotated[int, Field(ge=0, lt=MAX_ANPR_LOCAL_SAMPLES)]
    script: AnprScript = "latin"
    layout: AnprLayout
    token_class: AnprTokenClass = "synthetic_non_issuable"
    input_mode: Literal["deterministic_seed_only"] = "deterministic_seed_only"
    synthetic_only: Literal[True] = True


class EphemeralSyntheticTokenV1(ContractModel):
    """In-memory ground truth that must never enter evidence or persistence."""

    contract_type: Literal["hcam.anpr.ephemeral-synthetic-token.v1"] = (
        "hcam.anpr.ephemeral-synthetic-token.v1"
    )
    request_id: AnprRequestId
    token: SyntheticPlateToken
    token_class: AnprTokenClass = "synthetic_non_issuable"
    script: AnprScript = "latin"
    layout: AnprLayout
    synthetic_only: Literal[True] = True
    persistence: Literal["prohibited"] = "prohibited"


class SyntheticAnprExecutionPolicyV1(ContractModel):
    contract_type: Literal["hcam.anpr.execution-policy.v1"] = (
        "hcam.anpr.execution-policy.v1"
    )
    enabled: bool = False
    environment: Literal["development", "test", "production"] = "development"
    execution_scope: Literal["generated_only"] = "generated_only"
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    input_mode: Literal["deterministic_seed_only"] = "deterministic_seed_only"
    network_access: Literal["denied"] = "denied"
    artifact_download: Literal["denied"] = "denied"
    plate_text_persistence: Literal["denied"] = "denied"
    arbitrary_input: Literal["denied"] = "denied"
    maximum_request_bytes: Literal[4096] = MAX_ANPR_REQUEST_BYTES

    @model_validator(mode="after")
    def production_is_fail_closed(self) -> SyntheticAnprExecutionPolicyV1:
        if self.enabled and self.environment == "production":
            raise ValueError("generated ANPR execution is forbidden in production")
        return self


class SyntheticCorpusSplitCountsV1(ContractModel):
    contract_fixture: Annotated[int, Field(ge=1, le=128)]
    development: Annotated[int, Field(ge=1, le=9_997)]
    validation: Annotated[int, Field(ge=1, le=9_997)]
    final_test: Annotated[int, Field(ge=1, le=9_997)]

    @property
    def total(self) -> int:
        return (
            self.contract_fixture
            + self.development
            + self.validation
            + self.final_test
        )

    @model_validator(mode="after")
    def total_is_bounded(self) -> SyntheticCorpusSplitCountsV1:
        if self.total > MAX_ANPR_LOCAL_SAMPLES:
            raise ValueError("synthetic corpus exceeds the local sample ceiling")
        return self


class SyntheticCorpusPlanV1(ContractModel):
    contract_type: Literal["hcam.anpr.synthetic-corpus-plan.v1"] = (
        "hcam.anpr.synthetic-corpus-plan.v1"
    )
    plan_id: Annotated[str, Field(pattern=r"^anprplan_[0-9a-f]{32}$")]
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: Literal[ANPR_GENERATOR_VERSION] = ANPR_GENERATOR_VERSION
    policy_id: Literal["hcam.anpr.synthetic-non-issuable.v1"] = ANPR_TOKEN_POLICY_ID
    policy_version: Literal[ANPR_TOKEN_POLICY_VERSION] = ANPR_TOKEN_POLICY_VERSION
    split_policy_id: Literal["hcam.anpr.sealed-splits.v1"] = ANPR_SPLIT_POLICY_ID
    split_policy_version: Literal[ANPR_SPLIT_POLICY_VERSION] = (
        ANPR_SPLIT_POLICY_VERSION
    )
    root_seed: Annotated[int, Field(ge=0, le=4_294_967_295)]
    counts: SyntheticCorpusSplitCountsV1
    input_mode: Literal["deterministic_seed_only"] = "deterministic_seed_only"
    external_input_count: Literal[0] = 0
    final_test_frozen: Literal[True] = True
    final_test_tuning_allowed: Literal[False] = False
    synthetic_only: Literal[True] = True


class SyntheticSplitManifestEntryV1(ContractModel):
    sample_id: Annotated[str, Field(pattern=r"^anprsample_[0-9a-f]{32}$")]
    request_id: AnprRequestId
    sample_spec_digest: ImmutableDigest
    split: AnprSplit
    seed_namespace: Annotated[
        str,
        Field(
            pattern=(
                r"^p35w3:(?:contract_fixture|development|validation|final_test):v1$"
            )
        ),
    ]
    sample_index: Annotated[int, Field(ge=0, lt=MAX_ANPR_LOCAL_SAMPLES)]
    layout: AnprLayout
    generator_profile: Literal["primary", "holdout"]
    font_partition: Literal["primary", "holdout"]
    token_class: AnprTokenClass = "synthetic_non_issuable"
    synthetic_only: Literal[True] = True


class SyntheticSplitManifestContentV1(ContractModel):
    contract_type: Literal["hcam.anpr.synthetic-split-manifest-content.v1"] = (
        "hcam.anpr.synthetic-split-manifest-content.v1"
    )
    manifest_id: Annotated[str, Field(pattern=r"^anprmanifest_[0-9a-f]{32}$")]
    plan_id: Annotated[str, Field(pattern=r"^anprplan_[0-9a-f]{32}$")]
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: Literal[ANPR_GENERATOR_VERSION] = ANPR_GENERATOR_VERSION
    policy_id: Literal["hcam.anpr.synthetic-non-issuable.v1"] = ANPR_TOKEN_POLICY_ID
    policy_version: Literal[ANPR_TOKEN_POLICY_VERSION] = ANPR_TOKEN_POLICY_VERSION
    split_policy_id: Literal["hcam.anpr.sealed-splits.v1"] = ANPR_SPLIT_POLICY_ID
    split_policy_version: Literal[ANPR_SPLIT_POLICY_VERSION] = (
        ANPR_SPLIT_POLICY_VERSION
    )
    root_seed: Annotated[int, Field(ge=0, le=4_294_967_295)]
    counts: SyntheticCorpusSplitCountsV1
    entries: Annotated[
        tuple[SyntheticSplitManifestEntryV1, ...],
        Field(min_length=4, max_length=MAX_ANPR_LOCAL_SAMPLES),
    ]
    sealed: Literal[True] = True
    final_test_frozen: Literal[True] = True
    final_test_tuning_allowed: Literal[False] = False
    final_test_access_count: Literal[0] = 0
    external_input_count: Literal[0] = 0
    duplicate_token_count: Literal[0] = 0
    token_text_persisted: Literal[False] = False
    token_commitment_persisted: Literal[False] = False
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def entries_are_sealed_and_partitioned(self) -> SyntheticSplitManifestContentV1:
        if len(self.entries) != self.counts.total:
            raise ValueError("split counts do not match manifest entries")
        actual_counts = Counter(entry.split for entry in self.entries)
        if actual_counts != Counter(self.counts.model_dump(mode="python")):
            raise ValueError("manifest split membership does not match declared counts")
        ordering = {
            "contract_fixture": 0,
            "development": 1,
            "validation": 2,
            "final_test": 3,
        }
        positions = [(ordering[entry.split], entry.sample_index) for entry in self.entries]
        if positions != sorted(positions):
            raise ValueError("manifest entries must use canonical split/index ordering")
        for split in ordering:
            indexes = [entry.sample_index for entry in self.entries if entry.split == split]
            if indexes != list(range(len(indexes))):
                raise ValueError("manifest split indexes must be contiguous and zero-based")
        for attribute in ("sample_id", "request_id", "sample_spec_digest"):
            values = [getattr(entry, attribute) for entry in self.entries]
            if len(values) != len(set(values)):
                raise ValueError("manifest identifiers and digests must be unique")
        for entry in self.entries:
            expected_namespace = f"p35w3:{entry.split}:v1"
            if entry.seed_namespace != expected_namespace:
                raise ValueError("manifest seed namespace does not match split")
            if entry.split != "final_test" and (
                entry.generator_profile != "primary"
                or entry.font_partition != "primary"
            ):
                raise ValueError("holdout partitions are reserved for final test")
        final_entries = [entry for entry in self.entries if entry.split == "final_test"]
        if not any(entry.generator_profile == "holdout" for entry in final_entries):
            raise ValueError("final test requires a holdout generator profile")
        if not any(entry.font_partition == "holdout" for entry in final_entries):
            raise ValueError("final test requires a holdout font partition")
        return self


def _content_digest(content: SyntheticSplitManifestContentV1) -> str:
    serialized = json.dumps(
        content.model_dump(mode="json"),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(serialized).hexdigest()}"


class SealedSyntheticSplitManifestV1(ContractModel):
    contract_type: Literal["hcam.anpr.sealed-split-manifest.v1"] = (
        "hcam.anpr.sealed-split-manifest.v1"
    )
    content: SyntheticSplitManifestContentV1
    manifest_digest: ImmutableDigest

    @model_validator(mode="after")
    def digest_matches_content(self) -> SealedSyntheticSplitManifestV1:
        if self.manifest_digest != _content_digest(self.content):
            raise ValueError("sealed split manifest digest does not match content")
        return self


def seal_split_manifest(
    content: SyntheticSplitManifestContentV1,
) -> SealedSyntheticSplitManifestV1:
    return SealedSyntheticSplitManifestV1(
        content=content,
        manifest_digest=_content_digest(content),
    )


def generated_request_fixture() -> GeneratedTokenRequestV1:
    return GeneratedTokenRequestV1(
        request_id="anprreq_11111111111111111111111111111111",
        generator_version=ANPR_GENERATOR_VERSION,
        policy_version=ANPR_TOKEN_POLICY_VERSION,
        seed=1_337,
        sample_index=7,
        layout="single_line",
    )


def anpr_contract_bundle() -> dict[str, Any]:
    return {
        "contract_format": "hcam.anpr.contract-bundle.v1",
        "contracts": {
            "ephemeral_token": EphemeralSyntheticTokenV1.model_json_schema(
                mode="validation"
            ),
            "execution_policy": SyntheticAnprExecutionPolicyV1.model_json_schema(
                mode="validation"
            ),
            "generated_request": GeneratedTokenRequestV1.model_json_schema(
                mode="validation"
            ),
            "sealed_split_manifest": SealedSyntheticSplitManifestV1.model_json_schema(
                mode="validation"
            ),
            "synthetic_corpus_plan": SyntheticCorpusPlanV1.model_json_schema(
                mode="validation"
            ),
        },
        "source_policy": {
            "allowed_source_id": ANPR_GENERATED_SOURCE_ID,
            "input_mode": "deterministic_seed_only",
            "synthetic_only": True,
            "external_text_allowed": False,
            "file_url_upload_or_media_allowed": False,
        },
        "token_policy": {
            "policy_id": ANPR_TOKEN_POLICY_ID,
            "policy_version": ANPR_TOKEN_POLICY_VERSION,
            "classification": "synthetic_non_issuable",
            "pattern": ANPR_TOKEN_PATTERN,
            "visible_namespace": "SYN-",
            "production_grammar_strategy": (
                "deny_every_value_outside_the_disjoint_visible_synthetic_namespace"
            ),
            "required_character_classes": ["ascii_uppercase", "ascii_digit"],
            "normalization_or_lookup": "prohibited",
        },
        "generator_policy": {
            "generator_version": ANPR_GENERATOR_VERSION,
            "algorithm": "sha256_domain_separated_platform_independent",
            "external_entropy": False,
            "hidden_random_augmentation": False,
        },
        "split_policy": {
            "policy_id": ANPR_SPLIT_POLICY_ID,
            "policy_version": ANPR_SPLIT_POLICY_VERSION,
            "ordered_splits": [
                "contract_fixture",
                "development",
                "validation",
                "final_test",
            ],
            "independent_seed_namespaces": True,
            "final_test_frozen": True,
            "final_test_tuning_allowed": False,
            "holdout_generator_profile_required": True,
            "holdout_font_partition_required": True,
            "manifest_token_text_allowed": False,
            "manifest_token_commitment_allowed": False,
        },
        "resource_limits": {
            "maximum_document_depth": MAX_ANPR_DOCUMENT_DEPTH,
            "maximum_document_nodes": MAX_ANPR_DOCUMENT_NODES,
            "maximum_local_samples": MAX_ANPR_LOCAL_SAMPLES,
            "maximum_request_bytes": MAX_ANPR_REQUEST_BYTES,
        },
        "persistence_policy": {
            "plate_text_retention_hours": 0,
            "token_or_alternative_in_evidence": False,
            "identifier_free_aggregate_evidence_only": True,
        },
    }
