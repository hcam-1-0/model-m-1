from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, Field, model_validator

from hcam.analytics.contracts import (
    ContractModel,
    ImmutableDigest,
    NormalizedBoundingBox,
    StreamId,
    TrackerEpoch,
    TrackId,
)


ANPR_GENERATED_SOURCE_ID = "DATA-PLATE-GEN-R0"
ANPR_TOKEN_POLICY_ID = "hcam.anpr.synthetic-non-issuable.v1"
ANPR_TOKEN_PATTERN = r"^SYN-[A-Z0-9]{4}-[A-Z0-9]{4}$"
ANPR_GENERATOR_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.generator.v1:sha256-domain-separated:visible-syn-4x4"
    ).hexdigest()
)
ANPR_TOKEN_POLICY_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.synthetic-non-issuable.v1:ascii-upper-digit:mixed:zero-retention"
    ).hexdigest()
)
ANPR_SPLIT_POLICY_ID = "hcam.anpr.sealed-splits.v1"
ANPR_SPLIT_POLICY_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.sealed-splits.v1:independent-namespaces:final-test-holdouts"
    ).hexdigest()
)
ANPR_FRAME_GENERATOR_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.generated-frame.v1:bgr8:procedural-geometry-marker:no-font"
    ).hexdigest()
)
ANPR_GROUND_TRUTH_LOCALIZER_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.ground-truth-localizer.v1:no-model:no-weights:maximum-eight"
    ).hexdigest()
)
ANPR_RECTIFIER_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.axis-aligned-ground-truth-crop.v1:bgr8:ephemeral"
    ).hexdigest()
)
ANPR_LATIN_RENDERER_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.generated-latin-bitmap.v1:5x7:ascii-upper-digit-hyphen"
    ).hexdigest()
)
ANPR_LATIN_OCR_ADAPTER_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.paddleocr-latin-adapter.v1:raw-output:generated-only:cpu"
    ).hexdigest()
)
ANPR_LATIN_DICTIONARY_VERSION = (
    "sha256:a98ac29121eec9aef70836341b9d35806da7939b4f0fe1e20443acc00d915adc"
)
OCR_L0_ARTIFACT_SHA256 = (
    "sha256:da460f968ce9f88325ac3a34fa302077d6e9b0dcefb16ba3137cd7796f879d06"
)
OCR_L1_ARTIFACT_SHA256 = (
    "sha256:4eecc1c6a4623765042e6fc15446da0da110b7d875b6b72b2d351d2b2dbd4da6"
)
ANPR_AUXILIARY_GENERATOR_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.auxiliary-generator.v1:closed-base-graphemes:no-external-text"
    ).hexdigest()
)
ANPR_AUXILIARY_RENDERER_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.auxiliary-renderer.v1:pillow-12.3.0:basic-freetype:no-raqm"
    ).hexdigest()
)
ANPR_DEVANAGARI_OCR_ADAPTER_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.paddleocr-devanagari-adapter.v1:raw-output:generated-only:cpu"
    ).hexdigest()
)
ANPR_DEVANAGARI_DICTIONARY_VERSION = (
    "sha256:15dd5c96dabcc64d3d3bdfeefd7cdc71cffefe05e9598a07f767b23b8fe75184"
)
OCR_D0_ARTIFACT_SHA256 = (
    "sha256:ac8279d27fc7e8cda559364f9a3c506f43984cf6ba5e1b7a06450458bfe07dfb"
)
FONT_D0_ARTIFACT_SHA256 = (
    "sha256:9ce7b04f60e363d8870e5997744cf85cf69d38a4d7d129d364d92a3b14b461d7"
)
FONT_G0_ARTIFACT_SHA256 = (
    "sha256:9901d8552f1dd5d2c50dbd4caa6f6e174e74e8264f06594ab259ae6e7b1ac428"
)
ANPR_NORMALIZATION_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.normalization.v1:raw-preserving:nfc:closed-allowlist:no-autocorrect"
    ).hexdigest()
)
ANPR_GRAPHEME_POLICY_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.graphemes.v1:regex-2026.7.19:unicode-15.0.0:extended-clusters"
    ).hexdigest()
)
ANPR_CALIBRATION_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.calibration.v1:identity-baseline:five-equal-width-bins:no-threshold"
    ).hexdigest()
)
ANPR_ABSTENTION_POLICY_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.abstention.v1:hard-gates:unapproved-quality-threshold:always-abstain"
    ).hexdigest()
)
ANPR_CONSENSUS_POLICY_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.anpr.consensus.v1:exact-string:confidence-weighted:stream-epoch-track:always-abstain"
    ).hexdigest()
)
ANPR_PINNED_PYTHON_VERSION = "3.12.13"
ANPR_PINNED_REGEX_VERSION = "2026.7.19"
ANPR_PINNED_UNICODE_VERSION = "15.0.0"
MAX_ANPR_REQUEST_BYTES = 4 * 1024
MAX_ANPR_DOCUMENT_DEPTH = 8
MAX_ANPR_DOCUMENT_NODES = 256
MAX_ANPR_LOCAL_SAMPLES = 10_000
MAX_ANPR_FRAME_WIDTH = 1_280
MAX_ANPR_FRAME_HEIGHT = 720
MAX_ANPR_PLATE_REGIONS = 8
MAX_ANPR_CROP_WIDTH = 512
MAX_ANPR_CROP_HEIGHT = 128
MAX_ANPR_CONSENSUS_OBSERVATIONS = 5
MAX_ANPR_CONSENSUS_WINDOW_MS = 2_000
MAX_ANPR_CONSENSUS_STATES_PER_STREAM = 256

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
LatinOcrCandidate = Literal["OCR-L0", "OCR-L1"]
AuxiliaryScript = Literal["devanagari", "gujarati"]
AuxiliaryFontCandidate = Literal["FONT-D0", "FONT-G0"]
AuxiliaryDegradation = Literal["clean", "low_contrast", "downscaled"]
NormalizationCandidate = Literal["OCR-L0", "OCR-L1", "OCR-D0"]
NormalizationScript = Literal["latin", "devanagari"]
NormalizationFormatFamily = Literal["synthetic_non_issuable", "unrecognized"]
NormalizationAbstentionReason = Literal[
    "auxiliary_observation_only",
    "quality_threshold_unapproved",
    "synthetic_grammar_rejected",
]
NormalizationValidationOutcome = Literal[
    "allowlist_valid",
    "graphemes_segmented",
    "nfc_derived",
    "synthetic_grammar_rejected",
    "synthetic_grammar_valid",
    "unicode_scalar_valid",
    "utf8_valid",
]
ConsensusCloseReason = Literal[
    "count_limit",
    "epoch_reset",
    "event_time_window",
    "overload",
    "track_end",
]
ConsensusAbstentionReason = Literal[
    "consensus_thresholds_unapproved",
    "overload_fail_closed",
]
ConsensusScenario = Literal[
    "agreement",
    "cross_boundary_isolation",
    "disagreement",
    "duplicate_rejection",
    "epoch_reset",
    "event_time_window",
    "out_of_order_rejection",
    "overload",
    "track_end",
]
LatinOcrFailureCode = Literal[
    "engine_error",
    "invalid_confidence",
    "invalid_output",
    "malformed_result",
    "no_result",
    "output_too_long",
    "unexpected_whitespace",
    "unsupported_script",
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
            self.contract_fixture + self.development + self.validation + self.final_test
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
    split_policy_version: Literal[ANPR_SPLIT_POLICY_VERSION] = ANPR_SPLIT_POLICY_VERSION
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
    split_policy_version: Literal[ANPR_SPLIT_POLICY_VERSION] = ANPR_SPLIT_POLICY_VERSION
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
        positions = [
            (ordering[entry.split], entry.sample_index) for entry in self.entries
        ]
        if positions != sorted(positions):
            raise ValueError("manifest entries must use canonical split/index ordering")
        for split in ordering:
            indexes = [
                entry.sample_index for entry in self.entries if entry.split == split
            ]
            if indexes != list(range(len(indexes))):
                raise ValueError(
                    "manifest split indexes must be contiguous and zero-based"
                )
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


class NormalizedPointV1(ContractModel):
    x: Annotated[float, Field(ge=0, le=1)]
    y: Annotated[float, Field(ge=0, le=1)]


class GroundTruthPlateRegionContentV1(ContractModel):
    contract_type: Literal["hcam.anpr.ground-truth-region-content.v1"] = (
        "hcam.anpr.ground-truth-region-content.v1"
    )
    region_id: Annotated[str, Field(pattern=r"^anprregion_[0-9a-f]{32}$")]
    sample_id: Annotated[str, Field(pattern=r"^anprsample_[0-9a-f]{32}$")]
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: Literal[ANPR_GENERATOR_VERSION] = ANPR_GENERATOR_VERSION
    frame_generator_version: Literal[ANPR_FRAME_GENERATOR_VERSION] = (
        ANPR_FRAME_GENERATOR_VERSION
    )
    layout: AnprLayout
    bbox: NormalizedBoundingBox
    quadrilateral: tuple[
        NormalizedPointV1,
        NormalizedPointV1,
        NormalizedPointV1,
        NormalizedPointV1,
    ]
    class_id: Literal["vehicle.registration_plate_region"] = (
        "vehicle.registration_plate_region"
    )
    ground_truth_only: Literal[True] = True
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def quadrilateral_matches_axis_aligned_box(self) -> GroundTruthPlateRegionContentV1:
        expected = (
            (self.bbox.x, self.bbox.y),
            (self.bbox.x + self.bbox.width, self.bbox.y),
            (self.bbox.x + self.bbox.width, self.bbox.y + self.bbox.height),
            (self.bbox.x, self.bbox.y + self.bbox.height),
        )
        actual = tuple((point.x, point.y) for point in self.quadrilateral)
        if any(
            abs(actual_value - expected_value) > 1e-9
            for actual_point, expected_point in zip(actual, expected, strict=True)
            for actual_value, expected_value in zip(
                actual_point,
                expected_point,
                strict=True,
            )
        ):
            raise ValueError(
                "ground-truth quadrilateral must match the axis-aligned box"
            )
        return self


def _region_content_digest(content: GroundTruthPlateRegionContentV1) -> str:
    serialized = json.dumps(
        content.model_dump(mode="json"),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(serialized).hexdigest()}"


class SealedGroundTruthPlateRegionV1(ContractModel):
    contract_type: Literal["hcam.anpr.sealed-ground-truth-region.v1"] = (
        "hcam.anpr.sealed-ground-truth-region.v1"
    )
    content: GroundTruthPlateRegionContentV1
    region_digest: ImmutableDigest

    @model_validator(mode="after")
    def digest_matches_content(self) -> SealedGroundTruthPlateRegionV1:
        if self.region_digest != _region_content_digest(self.content):
            raise ValueError("ground-truth region digest does not match content")
        return self


def seal_ground_truth_region(
    content: GroundTruthPlateRegionContentV1,
) -> SealedGroundTruthPlateRegionV1:
    return SealedGroundTruthPlateRegionV1(
        content=content,
        region_digest=_region_content_digest(content),
    )


class PlateLocalizationHypothesisV1(ContractModel):
    hypothesis_id: Annotated[str, Field(pattern=r"^anprhyp_[0-9a-f]{32}$")]
    class_id: Literal["vehicle.registration_plate_region"] = (
        "vehicle.registration_plate_region"
    )
    bbox: NormalizedBoundingBox
    quadrilateral: tuple[
        NormalizedPointV1,
        NormalizedPointV1,
        NormalizedPointV1,
        NormalizedPointV1,
    ]
    confidence: Literal[1.0] = 1.0
    quality: Literal["generated_ground_truth_exact"] = "generated_ground_truth_exact"
    reason_code: Literal["ground_truth_only"] = "ground_truth_only"
    region_digest: ImmutableDigest

    @model_validator(mode="after")
    def quadrilateral_matches_axis_aligned_box(
        self,
    ) -> PlateLocalizationHypothesisV1:
        expected = (
            (self.bbox.x, self.bbox.y),
            (self.bbox.x + self.bbox.width, self.bbox.y),
            (self.bbox.x + self.bbox.width, self.bbox.y + self.bbox.height),
            (self.bbox.x, self.bbox.y + self.bbox.height),
        )
        actual = tuple((point.x, point.y) for point in self.quadrilateral)
        if any(
            abs(actual_value - expected_value) > 1e-9
            for actual_point, expected_point in zip(actual, expected, strict=True)
            for actual_value, expected_value in zip(
                actual_point,
                expected_point,
                strict=True,
            )
        ):
            raise ValueError("localization quadrilateral must match the bounding box")
        return self


class PlateLocalizationResultV1(ContractModel):
    contract_type: Literal["hcam.anpr.plate-localization-result.v1"] = (
        "hcam.anpr.plate-localization-result.v1"
    )
    result_id: Annotated[str, Field(pattern=r"^anprloc_[0-9a-f]{32}$")]
    sample_id: Annotated[str, Field(pattern=r"^anprsample_[0-9a-f]{32}$")]
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: Literal[ANPR_GENERATOR_VERSION] = ANPR_GENERATOR_VERSION
    frame_generator_version: Literal[ANPR_FRAME_GENERATOR_VERSION] = (
        ANPR_FRAME_GENERATOR_VERSION
    )
    source_frame_digest: ImmutableDigest
    localizer_id: Literal["GT-PLATE-R0"] = "GT-PLATE-R0"
    localizer_version: Literal[ANPR_GROUND_TRUTH_LOCALIZER_VERSION] = (
        ANPR_GROUND_TRUTH_LOCALIZER_VERSION
    )
    taxonomy_version: Literal["hcam.taxonomy.vehicle-registration-plate-region.v1"] = (
        "hcam.taxonomy.vehicle-registration-plate-region.v1"
    )
    preprocessing_version: Literal[ANPR_FRAME_GENERATOR_VERSION] = (
        ANPR_FRAME_GENERATOR_VERSION
    )
    postprocessing_version: Literal[ANPR_GROUND_TRUTH_LOCALIZER_VERSION] = (
        ANPR_GROUND_TRUTH_LOCALIZER_VERSION
    )
    runtime_id: Literal["python-stdlib-reference"] = "python-stdlib-reference"
    runtime_contract_version: Literal[ANPR_GROUND_TRUTH_LOCALIZER_VERSION] = (
        ANPR_GROUND_TRUTH_LOCALIZER_VERSION
    )
    execution_mode: Literal["generated_ground_truth_only"] = (
        "generated_ground_truth_only"
    )
    candidate_id: Literal[None] = None
    model_execution_performed: Literal[False] = False
    weights_loaded: Literal[False] = False
    hypothesis_count: Annotated[int, Field(ge=0, le=MAX_ANPR_PLATE_REGIONS)]
    hypotheses: Annotated[
        tuple[PlateLocalizationHypothesisV1, ...],
        Field(max_length=MAX_ANPR_PLATE_REGIONS),
    ]
    crop_bytes_returned: Literal[False] = False
    image_path_returned: Literal[False] = False
    media_url_returned: Literal[False] = False
    plate_text_returned: Literal[False] = False
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def hypothesis_count_matches(self) -> PlateLocalizationResultV1:
        if self.hypothesis_count != len(self.hypotheses):
            raise ValueError("localization hypothesis count does not match results")
        return self


class GroundTruthCropDescriptorV1(ContractModel):
    contract_type: Literal["hcam.anpr.ground-truth-crop-descriptor.v1"] = (
        "hcam.anpr.ground-truth-crop-descriptor.v1"
    )
    crop_id: Annotated[str, Field(pattern=r"^anprcrop_[0-9a-f]{32}$")]
    sample_id: Annotated[str, Field(pattern=r"^anprsample_[0-9a-f]{32}$")]
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: Literal[ANPR_GENERATOR_VERSION] = ANPR_GENERATOR_VERSION
    frame_generator_version: Literal[ANPR_FRAME_GENERATOR_VERSION] = (
        ANPR_FRAME_GENERATOR_VERSION
    )
    rectifier_version: Literal[ANPR_RECTIFIER_VERSION] = ANPR_RECTIFIER_VERSION
    region_digest: ImmutableDigest
    source_frame_digest: ImmutableDigest
    crop_digest: ImmutableDigest
    width: Annotated[int, Field(ge=1, le=MAX_ANPR_CROP_WIDTH)]
    height: Annotated[int, Field(ge=1, le=MAX_ANPR_CROP_HEIGHT)]
    pixel_format: Literal["bgr8"] = "bgr8"
    transform_matrix: tuple[
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
    ]
    method: Literal["axis_aligned_generated_ground_truth"] = (
        "axis_aligned_generated_ground_truth"
    )
    pixels_ephemeral: Literal[True] = True
    pixels_persisted: Literal[False] = False
    token_text_in_contract: Literal[False] = False
    model_execution_performed: Literal[False] = False
    synthetic_only: Literal[True] = True


class LatinOcrAlternativeV1(ContractModel):
    rank: Annotated[int, Field(ge=1, le=5)]
    raw_text: Annotated[
        str,
        Field(min_length=1, max_length=16, pattern=r"^[A-Za-z0-9-]+$"),
    ]
    raw_confidence: Annotated[float, Field(ge=0, le=1)]


class EphemeralLatinOcrHypothesisV1(ContractModel):
    """Raw OCR output. It is valid only in memory and is never evidence-safe."""

    contract_type: Literal["hcam.anpr.ephemeral-latin-ocr-hypothesis.v1"] = (
        "hcam.anpr.ephemeral-latin-ocr-hypothesis.v1"
    )
    result_id: Annotated[str, Field(pattern=r"^anprocr_[0-9a-f]{32}$")]
    region_id: Annotated[str, Field(pattern=r"^anprregion_[0-9a-f]{32}$")]
    sample_id: Annotated[str, Field(pattern=r"^anprsample_[0-9a-f]{32}$")]
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: Literal[ANPR_GENERATOR_VERSION] = ANPR_GENERATOR_VERSION
    renderer_version: Literal[ANPR_LATIN_RENDERER_VERSION] = (
        ANPR_LATIN_RENDERER_VERSION
    )
    adapter_version: Literal[ANPR_LATIN_OCR_ADAPTER_VERSION] = (
        ANPR_LATIN_OCR_ADAPTER_VERSION
    )
    candidate_id: LatinOcrCandidate
    engine_id: Literal["paddleocr-text-recognition"] = (
        "paddleocr-text-recognition"
    )
    artifact_id: Literal[
        "OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED",
        "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED",
    ]
    artifact_sha256: ImmutableDigest
    dictionary_version: Literal[ANPR_LATIN_DICTIONARY_VERSION] = (
        ANPR_LATIN_DICTIONARY_VERSION
    )
    preprocessing_version: Literal[ANPR_LATIN_RENDERER_VERSION] = (
        ANPR_LATIN_RENDERER_VERSION
    )
    runtime_id: Literal["paddleocr-3.7.0-paddlepaddle-3.3.1-cpu"] = (
        "paddleocr-3.7.0-paddlepaddle-3.3.1-cpu"
    )
    script_lane: Literal["latin"] = "latin"
    raw_text: Annotated[
        str,
        Field(min_length=1, max_length=16, pattern=r"^[A-Za-z0-9-]+$"),
    ]
    raw_confidence: Annotated[float, Field(ge=0, le=1)]
    alternatives: Annotated[tuple[LatinOcrAlternativeV1, ...], Field(max_length=5)] = (
        ()
    )
    latency_ms: Annotated[float, Field(ge=0, le=600_000)]
    raw_output_mutated: Literal[False] = False
    ephemeral_only: Literal[True] = True
    retained: Literal[False] = False
    synthetic_only: Literal[True] = True
    review_state: Literal["unreviewed"] = "unreviewed"

    @model_validator(mode="after")
    def candidate_matches_exact_artifact(self) -> EphemeralLatinOcrHypothesisV1:
        expected = {
            "OCR-L0": (
                "OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED",
                OCR_L0_ARTIFACT_SHA256,
            ),
            "OCR-L1": (
                "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED",
                OCR_L1_ARTIFACT_SHA256,
            ),
        }[self.candidate_id]
        if (self.artifact_id, self.artifact_sha256) != expected:
            raise ValueError("Latin OCR candidate does not match its exact artifact")
        if tuple(item.rank for item in self.alternatives) != tuple(
            range(1, len(self.alternatives) + 1)
        ):
            raise ValueError("Latin OCR alternative ranks must be contiguous")
        return self


class LatinOcrFailureCountsV1(ContractModel):
    engine_error: Annotated[int, Field(ge=0)] = 0
    invalid_confidence: Annotated[int, Field(ge=0)] = 0
    invalid_output: Annotated[int, Field(ge=0)] = 0
    malformed_result: Annotated[int, Field(ge=0)] = 0
    no_result: Annotated[int, Field(ge=0)] = 0
    output_too_long: Annotated[int, Field(ge=0)] = 0
    unexpected_whitespace: Annotated[int, Field(ge=0)] = 0
    unsupported_script: Annotated[int, Field(ge=0)] = 0

    @property
    def total(self) -> int:
        return sum(self.model_dump().values())


class LatinOcrDistributionV1(ContractModel):
    minimum: Annotated[float, Field(ge=0)]
    p50: Annotated[float, Field(ge=0)]
    p95: Annotated[float, Field(ge=0)]
    maximum: Annotated[float, Field(ge=0)]
    mean: Annotated[float, Field(ge=0)]

    @model_validator(mode="after")
    def percentiles_are_ordered(self) -> LatinOcrDistributionV1:
        if not self.minimum <= self.p50 <= self.p95 <= self.maximum:
            raise ValueError("distribution percentiles must be ordered")
        if not self.minimum <= self.mean <= self.maximum:
            raise ValueError("distribution mean must be within the observed range")
        return self


class LatinOcrGeneratedSliceV1(ContractModel):
    layout: AnprLayout
    sample_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    succeeded: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    failed: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    exact_matches: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    reference_scalar_count: Annotated[int, Field(ge=0)]
    raw_edit_distance: Annotated[int, Field(ge=0)]
    failure_counts: LatinOcrFailureCountsV1

    @model_validator(mode="after")
    def counts_are_consistent(self) -> LatinOcrGeneratedSliceV1:
        if self.succeeded + self.failed != self.sample_count:
            raise ValueError("Latin OCR slice success/failure count is inconsistent")
        if self.exact_matches > self.succeeded:
            raise ValueError("Latin OCR exact matches exceed successful outputs")
        if self.failure_counts.total != self.failed:
            raise ValueError("Latin OCR slice failure reasons are inconsistent")
        return self


class LatinOcrCandidateEvaluationV1(ContractModel):
    candidate_id: LatinOcrCandidate
    artifact_id: Literal[
        "OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED",
        "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED",
    ]
    artifact_sha256: ImmutableDigest
    extracted_inventory_sha256: ImmutableDigest
    model_name: Literal["PP-OCRv6_small_rec", "PP-OCRv6_medium_rec"]
    dictionary_version: Literal[ANPR_LATIN_DICTIONARY_VERSION] = (
        ANPR_LATIN_DICTIONARY_VERSION
    )
    adapter_version: Literal[ANPR_LATIN_OCR_ADAPTER_VERSION] = (
        ANPR_LATIN_OCR_ADAPTER_VERSION
    )
    sample_count: Annotated[int, Field(ge=1, le=MAX_ANPR_LOCAL_SAMPLES)]
    succeeded: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    failed: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    exact_matches: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    reference_scalar_count: Annotated[int, Field(ge=1)]
    raw_edit_distance: Annotated[int, Field(ge=0)]
    failure_counts: LatinOcrFailureCountsV1
    slices: Annotated[tuple[LatinOcrGeneratedSliceV1, ...], Field(min_length=2, max_length=2)]
    confidence_distribution: LatinOcrDistributionV1 | None
    latency_ms_distribution: LatinOcrDistributionV1
    replay_runs: Literal[20] = 20
    replay_output_deterministic: bool
    network_attempt_count: Annotated[int, Field(ge=0)]
    network_access_performed: Literal[False] = False
    final_test_used: Literal[False] = False
    raw_output_persisted: Literal[False] = False
    alternatives_persisted: Literal[False] = False
    identifiers_persisted: Literal[False] = False
    promotion_authorized: Literal[False] = False
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def evaluation_counts_are_consistent(self) -> LatinOcrCandidateEvaluationV1:
        expected = {
            "OCR-L0": (
                "OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED",
                OCR_L0_ARTIFACT_SHA256,
                "PP-OCRv6_small_rec",
            ),
            "OCR-L1": (
                "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED",
                OCR_L1_ARTIFACT_SHA256,
                "PP-OCRv6_medium_rec",
            ),
        }[self.candidate_id]
        if (self.artifact_id, self.artifact_sha256, self.model_name) != expected:
            raise ValueError("Latin OCR evaluation does not match its exact artifact")
        if self.succeeded + self.failed != self.sample_count:
            raise ValueError("Latin OCR evaluation success/failure count is inconsistent")
        if self.exact_matches > self.succeeded:
            raise ValueError("Latin OCR exact matches exceed successful outputs")
        if self.failure_counts.total != self.failed:
            raise ValueError("Latin OCR evaluation failure reasons are inconsistent")
        if sum(item.sample_count for item in self.slices) != self.sample_count:
            raise ValueError("Latin OCR slice counts do not cover the evaluation")
        if {item.layout for item in self.slices} != {"single_line", "two_line"}:
            raise ValueError("Latin OCR evaluation requires both layout slices")
        return self


class LatinOcrGeneratedEvaluationV1(ContractModel):
    contract_type: Literal["hcam.phase3.p3_5.latin-ocr-generated-evaluation.v1"] = (
        "hcam.phase3.p3_5.latin-ocr-generated-evaluation.v1"
    )
    work_package: Literal[
        "P35-W5_exact_Latin_Paddle_OCR_adapters_and_generated_evaluation"
    ] = "P35-W5_exact_Latin_Paddle_OCR_adapters_and_generated_evaluation"
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: Literal[ANPR_GENERATOR_VERSION] = ANPR_GENERATOR_VERSION
    renderer_version: Literal[ANPR_LATIN_RENDERER_VERSION] = (
        ANPR_LATIN_RENDERER_VERSION
    )
    adapter_version: Literal[ANPR_LATIN_OCR_ADAPTER_VERSION] = (
        ANPR_LATIN_OCR_ADAPTER_VERSION
    )
    runtime_id: Literal["cpython-3.12.13-windows-x86_64"] = (
        "cpython-3.12.13-windows-x86_64"
    )
    paddleocr_version: Literal["3.7.0"] = "3.7.0"
    paddlepaddle_version: Literal["3.3.1"] = "3.3.1"
    pillow_version: Literal["12.3.0"] = "12.3.0"
    regex_version: Literal["2026.7.19"] = "2026.7.19"
    candidate_evaluations: Annotated[
        tuple[LatinOcrCandidateEvaluationV1, ...], Field(min_length=2, max_length=2)
    ]
    generated_sample_plan: Literal["development_then_validation_no_final_test"] = (
        "development_then_validation_no_final_test"
    )
    external_input_count: Literal[0] = 0
    model_download_count: Literal[0] = 0
    camera_or_media_input_count: Literal[0] = 0
    real_registration_mark_count: Literal[0] = 0
    raw_output_persisted: Literal[False] = False
    alternatives_persisted: Literal[False] = False
    sample_or_region_identifiers_persisted: Literal[False] = False
    plate_text_retention_hours: Literal[0] = 0
    quality_threshold_decided: Literal[False] = False
    promotion_authorized: Literal[False] = False
    deployment_authorized: Literal[False] = False
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def baseline_and_challenger_are_both_present(self) -> LatinOcrGeneratedEvaluationV1:
        if {item.candidate_id for item in self.candidate_evaluations} != {
            "OCR-L0",
            "OCR-L1",
        }:
            raise ValueError("Latin OCR evidence requires the exact L0 and L1 pair")
        return self


class EphemeralAuxiliaryOcrHypothesisV1(ContractModel):
    """Generated auxiliary-script OCR output that must remain process-local."""

    contract_type: Literal["hcam.anpr.ephemeral-auxiliary-ocr-hypothesis.v1"] = (
        "hcam.anpr.ephemeral-auxiliary-ocr-hypothesis.v1"
    )
    result_id: Annotated[str, Field(pattern=r"^anprauxocr_[0-9a-f]{32}$")]
    region_id: Annotated[str, Field(pattern=r"^anprauxregion_[0-9a-f]{32}$")]
    sample_id: Annotated[str, Field(pattern=r"^anprauxsample_[0-9a-f]{32}$")]
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: Literal[ANPR_AUXILIARY_GENERATOR_VERSION] = (
        ANPR_AUXILIARY_GENERATOR_VERSION
    )
    renderer_version: Literal[ANPR_AUXILIARY_RENDERER_VERSION] = (
        ANPR_AUXILIARY_RENDERER_VERSION
    )
    adapter_version: Literal[ANPR_DEVANAGARI_OCR_ADAPTER_VERSION] = (
        ANPR_DEVANAGARI_OCR_ADAPTER_VERSION
    )
    candidate_id: Literal["OCR-D0"] = "OCR-D0"
    engine_id: Literal["paddleocr-text-recognition"] = (
        "paddleocr-text-recognition"
    )
    artifact_id: Literal["OCR-D0-PPOCRV5-DEVANAGARI-INFER-PROPOSED"] = (
        "OCR-D0-PPOCRV5-DEVANAGARI-INFER-PROPOSED"
    )
    artifact_sha256: Literal[OCR_D0_ARTIFACT_SHA256] = OCR_D0_ARTIFACT_SHA256
    dictionary_version: Literal[ANPR_DEVANAGARI_DICTIONARY_VERSION] = (
        ANPR_DEVANAGARI_DICTIONARY_VERSION
    )
    runtime_id: Literal["paddleocr-3.7.0-paddlepaddle-3.3.1-cpu"] = (
        "paddleocr-3.7.0-paddlepaddle-3.3.1-cpu"
    )
    script_lane: Literal["devanagari"] = "devanagari"
    raw_text: Annotated[str, Field(min_length=1, max_length=16)]
    raw_confidence: Annotated[float, Field(ge=0, le=1)]
    latency_ms: Annotated[float, Field(ge=0, le=600_000)]
    modifies_registration_mark: Literal[False] = False
    transliteration_performed: Literal[False] = False
    raw_output_mutated: Literal[False] = False
    ephemeral_only: Literal[True] = True
    retained: Literal[False] = False
    synthetic_only: Literal[True] = True
    review_state: Literal["unreviewed"] = "unreviewed"


class AuxiliaryFailureCountsV1(ContractModel):
    engine_error: Annotated[int, Field(ge=0)] = 0
    invalid_confidence: Annotated[int, Field(ge=0)] = 0
    invalid_output: Annotated[int, Field(ge=0)] = 0
    malformed_result: Annotated[int, Field(ge=0)] = 0
    no_result: Annotated[int, Field(ge=0)] = 0
    output_too_long: Annotated[int, Field(ge=0)] = 0
    unexpected_whitespace: Annotated[int, Field(ge=0)] = 0
    unsupported_script: Annotated[int, Field(ge=0)] = 0

    @property
    def total(self) -> int:
        return sum(self.model_dump().values())


class AuxiliaryGeneratedSliceV1(ContractModel):
    degradation: AuxiliaryDegradation
    sample_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    succeeded: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    failed: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    exact_matches: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    reference_scalar_count: Annotated[int, Field(ge=0)]
    reference_grapheme_count: Annotated[int, Field(ge=0)]
    raw_edit_distance: Annotated[int, Field(ge=0)]
    failure_counts: AuxiliaryFailureCountsV1

    @model_validator(mode="after")
    def counts_are_consistent(self) -> AuxiliaryGeneratedSliceV1:
        if self.succeeded + self.failed != self.sample_count:
            raise ValueError("auxiliary slice success/failure count is inconsistent")
        if self.exact_matches > self.succeeded:
            raise ValueError("auxiliary exact matches exceed successful outputs")
        if self.failure_counts.total != self.failed:
            raise ValueError("auxiliary slice failure reasons are inconsistent")
        return self


class DevanagariOcrCandidateEvaluationV1(ContractModel):
    candidate_id: Literal["OCR-D0"] = "OCR-D0"
    artifact_id: Literal["OCR-D0-PPOCRV5-DEVANAGARI-INFER-PROPOSED"] = (
        "OCR-D0-PPOCRV5-DEVANAGARI-INFER-PROPOSED"
    )
    artifact_sha256: Literal[OCR_D0_ARTIFACT_SHA256] = OCR_D0_ARTIFACT_SHA256
    extracted_inventory_sha256: ImmutableDigest
    model_name: Literal["devanagari_PP-OCRv5_mobile_rec"] = (
        "devanagari_PP-OCRv5_mobile_rec"
    )
    font_candidate_id: Literal["FONT-D0"] = "FONT-D0"
    font_artifact_sha256: Literal[FONT_D0_ARTIFACT_SHA256] = (
        FONT_D0_ARTIFACT_SHA256
    )
    dictionary_version: Literal[ANPR_DEVANAGARI_DICTIONARY_VERSION] = (
        ANPR_DEVANAGARI_DICTIONARY_VERSION
    )
    adapter_version: Literal[ANPR_DEVANAGARI_OCR_ADAPTER_VERSION] = (
        ANPR_DEVANAGARI_OCR_ADAPTER_VERSION
    )
    sample_count: Annotated[int, Field(ge=1, le=MAX_ANPR_LOCAL_SAMPLES)]
    succeeded: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    failed: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    exact_matches: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    reference_scalar_count: Annotated[int, Field(ge=1)]
    reference_grapheme_count: Annotated[int, Field(ge=1)]
    raw_edit_distance: Annotated[int, Field(ge=0)]
    failure_counts: AuxiliaryFailureCountsV1
    slices: Annotated[
        tuple[AuxiliaryGeneratedSliceV1, ...], Field(min_length=3, max_length=3)
    ]
    confidence_distribution: LatinOcrDistributionV1 | None
    latency_ms_distribution: LatinOcrDistributionV1
    replay_runs: Literal[20] = 20
    replay_output_deterministic: bool
    network_attempt_count: Annotated[int, Field(ge=0)]
    network_access_performed: Literal[False] = False
    final_test_used: Literal[False] = False
    raw_output_persisted: Literal[False] = False
    alternatives_persisted: Literal[False] = False
    identifiers_persisted: Literal[False] = False
    modifies_registration_mark: Literal[False] = False
    transliteration_performed: Literal[False] = False
    promotion_authorized: Literal[False] = False
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def evaluation_counts_are_consistent(self) -> DevanagariOcrCandidateEvaluationV1:
        if self.succeeded + self.failed != self.sample_count:
            raise ValueError("Devanagari OCR success/failure count is inconsistent")
        if self.exact_matches > self.succeeded:
            raise ValueError("Devanagari exact matches exceed successful outputs")
        if self.failure_counts.total != self.failed:
            raise ValueError("Devanagari OCR failure reasons are inconsistent")
        if sum(item.sample_count for item in self.slices) != self.sample_count:
            raise ValueError("Devanagari OCR slices do not cover the evaluation")
        if {item.degradation for item in self.slices} != {
            "clean",
            "low_contrast",
            "downscaled",
        }:
            raise ValueError("Devanagari OCR requires every degradation slice")
        return self


class AuxiliaryFontRenderingSliceV1(ContractModel):
    degradation: AuxiliaryDegradation
    sample_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    succeeded: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    failed: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]

    @model_validator(mode="after")
    def counts_are_consistent(self) -> AuxiliaryFontRenderingSliceV1:
        if self.succeeded + self.failed != self.sample_count:
            raise ValueError("font-rendering slice counts are inconsistent")
        return self


class AuxiliaryFontRenderingEvaluationV1(ContractModel):
    candidate_id: AuxiliaryFontCandidate
    artifact_id: Literal[
        "FONT-D0-NOTO-SANS-DEVANAGARI-VARIABLE-PROPOSED",
        "FONT-G0-NOTO-SANS-GUJARATI-VARIABLE-PROPOSED",
    ]
    artifact_sha256: ImmutableDigest
    script_lane: AuxiliaryScript
    font_family: Literal["Noto Sans Devanagari", "Noto Sans Gujarati"]
    renderer_version: Literal[ANPR_AUXILIARY_RENDERER_VERSION] = (
        ANPR_AUXILIARY_RENDERER_VERSION
    )
    shaping_backend: Literal["basic_freetype_no_raqm"] = "basic_freetype_no_raqm"
    complex_shaping_available: Literal[False] = False
    complex_shaping_used: Literal[False] = False
    standalone_graphemes_only: Literal[True] = True
    sample_count: Annotated[int, Field(ge=1, le=MAX_ANPR_LOCAL_SAMPLES)]
    generated_grapheme_count: Annotated[int, Field(ge=1)]
    succeeded: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    failed: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    slices: Annotated[
        tuple[AuxiliaryFontRenderingSliceV1, ...], Field(min_length=3, max_length=3)
    ]
    replay_runs: Literal[20] = 20
    replay_pixels_deterministic: bool
    generated_text_persisted: Literal[False] = False
    rendered_pixels_persisted: Literal[False] = False
    identifiers_persisted: Literal[False] = False
    ocr_execution_performed: bool
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def exact_font_and_counts_are_consistent(self) -> AuxiliaryFontRenderingEvaluationV1:
        expected = {
            "FONT-D0": (
                "FONT-D0-NOTO-SANS-DEVANAGARI-VARIABLE-PROPOSED",
                FONT_D0_ARTIFACT_SHA256,
                "devanagari",
                "Noto Sans Devanagari",
                True,
            ),
            "FONT-G0": (
                "FONT-G0-NOTO-SANS-GUJARATI-VARIABLE-PROPOSED",
                FONT_G0_ARTIFACT_SHA256,
                "gujarati",
                "Noto Sans Gujarati",
                False,
            ),
        }[self.candidate_id]
        observed = (
            self.artifact_id,
            self.artifact_sha256,
            self.script_lane,
            self.font_family,
            self.ocr_execution_performed,
        )
        if observed != expected:
            raise ValueError("font-rendering evidence is cross-wired")
        if self.succeeded + self.failed != self.sample_count:
            raise ValueError("font-rendering totals are inconsistent")
        if sum(item.sample_count for item in self.slices) != self.sample_count:
            raise ValueError("font-rendering slices do not cover the evaluation")
        if {item.degradation for item in self.slices} != {
            "clean",
            "low_contrast",
            "downscaled",
        }:
            raise ValueError("font rendering requires every degradation slice")
        return self


class AuxiliaryScriptGeneratedEvaluationV1(ContractModel):
    contract_type: Literal[
        "hcam.phase3.p3_5.auxiliary-script-generated-evaluation.v1"
    ] = "hcam.phase3.p3_5.auxiliary-script-generated-evaluation.v1"
    work_package: Literal[
        "P35-W6_exact_Devanagari_Paddle_OCR_lane_and_Gujarati_font_rendering_only"
    ] = "P35-W6_exact_Devanagari_Paddle_OCR_lane_and_Gujarati_font_rendering_only"
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: Literal[ANPR_AUXILIARY_GENERATOR_VERSION] = (
        ANPR_AUXILIARY_GENERATOR_VERSION
    )
    renderer_version: Literal[ANPR_AUXILIARY_RENDERER_VERSION] = (
        ANPR_AUXILIARY_RENDERER_VERSION
    )
    adapter_version: Literal[ANPR_DEVANAGARI_OCR_ADAPTER_VERSION] = (
        ANPR_DEVANAGARI_OCR_ADAPTER_VERSION
    )
    runtime_id: Literal["cpython-3.12.13-windows-x86_64"] = (
        "cpython-3.12.13-windows-x86_64"
    )
    paddleocr_version: Literal["3.7.0"] = "3.7.0"
    paddlepaddle_version: Literal["3.3.1"] = "3.3.1"
    pillow_version: Literal["12.3.0"] = "12.3.0"
    regex_version: Literal["2026.7.19"] = "2026.7.19"
    devanagari_ocr: DevanagariOcrCandidateEvaluationV1
    font_rendering: Annotated[
        tuple[AuxiliaryFontRenderingEvaluationV1, ...],
        Field(min_length=2, max_length=2),
    ]
    generated_sample_plan: Literal["internal_vocabulary_no_final_test"] = (
        "internal_vocabulary_no_final_test"
    )
    external_text_input_count: Literal[0] = 0
    model_download_count: Literal[0] = 0
    camera_or_media_input_count: Literal[0] = 0
    real_registration_mark_count: Literal[0] = 0
    gujarati_ocr_execution_count: Literal[0] = 0
    tesseract_execution_count: Literal[0] = 0
    raw_output_persisted: Literal[False] = False
    generated_text_persisted: Literal[False] = False
    rendered_pixels_persisted: Literal[False] = False
    sample_or_region_identifiers_persisted: Literal[False] = False
    plate_text_retention_hours: Literal[0] = 0
    modifies_registration_mark: Literal[False] = False
    transliteration_performed: Literal[False] = False
    quality_threshold_decided: Literal[False] = False
    promotion_authorized: Literal[False] = False
    deployment_authorized: Literal[False] = False
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def exact_auxiliary_lanes_are_present(self) -> AuxiliaryScriptGeneratedEvaluationV1:
        if {item.candidate_id for item in self.font_rendering} != {
            "FONT-D0",
            "FONT-G0",
        }:
            raise ValueError("W6 evidence requires exact Devanagari and Gujarati fonts")
        return self


class EphemeralPlateNormalizationV1(ContractModel):
    """Derived text semantics that are valid only inside the generated harness."""

    contract_type: Literal["hcam.anpr.ephemeral-plate-normalization.v1"] = (
        "hcam.anpr.ephemeral-plate-normalization.v1"
    )
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    candidate_id: NormalizationCandidate
    script_lane: NormalizationScript
    raw_hypothesis_digest: ImmutableDigest
    nfc_value: Annotated[str, Field(min_length=1, max_length=32)]
    graphemes: Annotated[
        tuple[Annotated[str, Field(min_length=1, max_length=32)], ...],
        Field(min_length=1, max_length=16),
    ]
    normalized_display_candidate: Annotated[str, Field(min_length=1, max_length=32)]
    raw_scalar_count: Annotated[int, Field(ge=1, le=32)]
    nfc_scalar_count: Annotated[int, Field(ge=1, le=32)]
    grapheme_count: Annotated[int, Field(ge=1, le=16)]
    normalization_version: Literal[ANPR_NORMALIZATION_VERSION] = (
        ANPR_NORMALIZATION_VERSION
    )
    grapheme_policy_version: Literal[ANPR_GRAPHEME_POLICY_VERSION] = (
        ANPR_GRAPHEME_POLICY_VERSION
    )
    unicode_version: Literal[ANPR_PINNED_UNICODE_VERSION] = (
        ANPR_PINNED_UNICODE_VERSION
    )
    regex_version: Literal[ANPR_PINNED_REGEX_VERSION] = ANPR_PINNED_REGEX_VERSION
    format_family: NormalizationFormatFamily
    validation_outcomes: Annotated[
        tuple[NormalizationValidationOutcome, ...], Field(min_length=6, max_length=7)
    ]
    nfc_transform_performed: bool
    separator_transform_performed: Literal[False] = False
    case_transform_performed: bool
    raw_confidence: Annotated[float, Field(ge=0, le=1)]
    calibrated_confidence: Annotated[float, Field(ge=0, le=1)]
    calibration_version: Literal[ANPR_CALIBRATION_VERSION] = ANPR_CALIBRATION_VERSION
    calibration_method: Literal["identity_generated_baseline"] = (
        "identity_generated_baseline"
    )
    quality_threshold_approved: Literal[False] = False
    abstention_policy_version: Literal[ANPR_ABSTENTION_POLICY_VERSION] = (
        ANPR_ABSTENTION_POLICY_VERSION
    )
    abstain: Literal[True] = True
    abstention_reason: NormalizationAbstentionReason
    raw_output_mutated: Literal[False] = False
    confusable_substitution_performed: Literal[False] = False
    transliteration_performed: Literal[False] = False
    dictionary_completion_performed: Literal[False] = False
    record_lookup_performed: Literal[False] = False
    ephemeral_only: Literal[True] = True
    retained: Literal[False] = False
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def derived_values_are_consistent(self) -> EphemeralPlateNormalizationV1:
        if unicodedata.normalize("NFC", self.nfc_value) != self.nfc_value:
            raise ValueError("normalization value must be NFC")
        if "".join(self.graphemes) != self.nfc_value:
            raise ValueError("graphemes must exactly cover the NFC value")
        if (
            self.raw_scalar_count < 1
            or self.nfc_scalar_count != len(self.nfc_value)
            or self.grapheme_count != len(self.graphemes)
        ):
            raise ValueError("normalization counts are inconsistent")
        expected_script = {
            "OCR-L0": "latin",
            "OCR-L1": "latin",
            "OCR-D0": "devanagari",
        }[self.candidate_id]
        if self.script_lane != expected_script:
            raise ValueError("normalization candidate is routed to the wrong script")
        if self.calibrated_confidence != self.raw_confidence:
            raise ValueError("W7 identity calibration cannot change confidence")
        if self.script_lane == "devanagari":
            if (
                self.format_family != "unrecognized"
                or self.abstention_reason != "auxiliary_observation_only"
                or self.case_transform_performed
            ):
                raise ValueError("auxiliary normalization cannot become a plate result")
        else:
            expected_family = (
                "synthetic_non_issuable"
                if _TOKEN_PATTERN.fullmatch(self.normalized_display_candidate)
                else "unrecognized"
            )
            expected_reason = (
                "quality_threshold_unapproved"
                if expected_family == "synthetic_non_issuable"
                else "synthetic_grammar_rejected"
            )
            if (
                self.format_family != expected_family
                or self.abstention_reason != expected_reason
            ):
                raise ValueError("Latin grammar classification is inconsistent")
        expected_grammar_outcome = (
            "synthetic_grammar_valid"
            if self.format_family == "synthetic_non_issuable"
            else "synthetic_grammar_rejected"
        )
        if expected_grammar_outcome not in self.validation_outcomes:
            raise ValueError("normalization grammar outcome is missing")
        return self


class EphemeralCalibrationObservationV1(ContractModel):
    """Identifier-free generated calibration input; never persisted individually."""

    candidate_id: NormalizationCandidate
    split: Literal["development", "validation"]
    raw_confidence: Annotated[float, Field(ge=0, le=1)]
    correct: bool
    synthetic_only: Literal[True] = True
    retained: Literal[False] = False


class CalibrationBinV1(ContractModel):
    bin_index: Annotated[int, Field(ge=0, le=4)]
    lower_bound: Annotated[float, Field(ge=0, le=1)]
    upper_bound: Annotated[float, Field(ge=0, le=1)]
    sample_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    correct_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    mean_confidence: Annotated[float, Field(ge=0, le=1)] | None
    accuracy: Annotated[float, Field(ge=0, le=1)] | None
    absolute_calibration_gap: Annotated[float, Field(ge=0, le=1)] | None

    @model_validator(mode="after")
    def bin_is_consistent(self) -> CalibrationBinV1:
        if self.lower_bound >= self.upper_bound or self.correct_count > self.sample_count:
            raise ValueError("calibration bin bounds or counts are invalid")
        values = (self.mean_confidence, self.accuracy, self.absolute_calibration_gap)
        if self.sample_count == 0 and any(value is not None for value in values):
            raise ValueError("empty calibration bins cannot contain statistics")
        if self.sample_count > 0 and any(value is None for value in values):
            raise ValueError("populated calibration bins require statistics")
        return self


class CandidateCalibrationEvaluationV1(ContractModel):
    candidate_id: NormalizationCandidate
    calibration_version: Literal[ANPR_CALIBRATION_VERSION] = ANPR_CALIBRATION_VERSION
    method: Literal["identity_generated_baseline_five_equal_width_bins"] = (
        "identity_generated_baseline_five_equal_width_bins"
    )
    fixture_kind: Literal["deterministic_contract_semantics_not_model_quality"] = (
        "deterministic_contract_semantics_not_model_quality"
    )
    sample_count: Annotated[int, Field(ge=1, le=MAX_ANPR_LOCAL_SAMPLES)]
    correct_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    bins: Annotated[tuple[CalibrationBinV1, ...], Field(min_length=5, max_length=5)]
    expected_calibration_error: Annotated[float, Field(ge=0, le=1)]
    brier_score: Annotated[float, Field(ge=0, le=1)]
    quality_threshold_approved: Literal[False] = False
    promotion_authorized: Literal[False] = False

    @model_validator(mode="after")
    def calibration_is_consistent(self) -> CandidateCalibrationEvaluationV1:
        if tuple(item.bin_index for item in self.bins) != tuple(range(5)):
            raise ValueError("calibration bins must be ordered and complete")
        expected_bounds = tuple((index / 5, (index + 1) / 5) for index in range(5))
        observed_bounds = tuple(
            (item.lower_bound, item.upper_bound) for item in self.bins
        )
        if observed_bounds != expected_bounds:
            raise ValueError("calibration bins must use the frozen equal-width grid")
        if sum(item.sample_count for item in self.bins) != self.sample_count:
            raise ValueError("calibration bin counts do not cover the fixture")
        if sum(item.correct_count for item in self.bins) != self.correct_count:
            raise ValueError("calibration correctness counts are inconsistent")
        return self


class NormalizationGeneratedSliceV1(ContractModel):
    script_lane: Literal["latin", "devanagari", "gujarati"]
    fixture_kind: Literal[
        "deterministic_hypothesis_contract_fixture",
        "generated_render_reference_only",
    ]
    sample_count: Annotated[int, Field(ge=1, le=MAX_ANPR_LOCAL_SAMPLES)]
    hypothesis_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    normalized_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    abstained_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    synthetic_format_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    unrecognized_format_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    nfc_transform_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    case_transform_count: Annotated[int, Field(ge=0, le=MAX_ANPR_LOCAL_SAMPLES)]
    separator_transform_count: Literal[0] = 0
    reference_scalar_count: Annotated[int, Field(ge=1)]
    reference_grapheme_count: Annotated[int, Field(ge=1)]
    observed_scalar_count: Annotated[int, Field(ge=0)]
    observed_grapheme_count: Annotated[int, Field(ge=0)]
    code_point_edit_distance: Annotated[int, Field(ge=0)]
    grapheme_edit_distance: Annotated[int, Field(ge=0)]
    ocr_execution_performed: Literal[False] = False

    @model_validator(mode="after")
    def slice_counts_are_consistent(self) -> NormalizationGeneratedSliceV1:
        if (
            self.normalized_count != self.hypothesis_count
            or self.abstained_count != self.normalized_count
            or self.synthetic_format_count + self.unrecognized_format_count
            != self.normalized_count
        ):
            raise ValueError("normalization slice counts are inconsistent")
        if self.script_lane == "gujarati":
            if (
                self.fixture_kind != "generated_render_reference_only"
                or self.hypothesis_count != 0
                or self.observed_scalar_count != 0
                or self.observed_grapheme_count != 0
            ):
                raise ValueError("Gujarati W7 evidence must remain reference-only")
        elif (
            self.fixture_kind != "deterministic_hypothesis_contract_fixture"
            or self.hypothesis_count != self.sample_count
        ):
            raise ValueError("normalization fixtures must cover their generated samples")
        return self


class NormalizationGeneratedEvaluationV1(ContractModel):
    contract_type: Literal[
        "hcam.phase3.p3_5.normalization-generated-evaluation.v1"
    ] = "hcam.phase3.p3_5.normalization-generated-evaluation.v1"
    work_package: Literal[
        "P35-W7_normalization_grapheme_metrics_calibration_and_abstention"
    ] = "P35-W7_normalization_grapheme_metrics_calibration_and_abstention"
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    normalization_version: Literal[ANPR_NORMALIZATION_VERSION] = (
        ANPR_NORMALIZATION_VERSION
    )
    grapheme_policy_version: Literal[ANPR_GRAPHEME_POLICY_VERSION] = (
        ANPR_GRAPHEME_POLICY_VERSION
    )
    calibration_version: Literal[ANPR_CALIBRATION_VERSION] = ANPR_CALIBRATION_VERSION
    abstention_policy_version: Literal[ANPR_ABSTENTION_POLICY_VERSION] = (
        ANPR_ABSTENTION_POLICY_VERSION
    )
    runtime_id: Literal["cpython-3.12.13-windows-x86_64"] = (
        "cpython-3.12.13-windows-x86_64"
    )
    python_version: Literal[ANPR_PINNED_PYTHON_VERSION] = ANPR_PINNED_PYTHON_VERSION
    regex_version: Literal[ANPR_PINNED_REGEX_VERSION] = ANPR_PINNED_REGEX_VERSION
    unicode_version: Literal[ANPR_PINNED_UNICODE_VERSION] = (
        ANPR_PINNED_UNICODE_VERSION
    )
    slices: Annotated[
        tuple[NormalizationGeneratedSliceV1, ...], Field(min_length=3, max_length=3)
    ]
    calibration_evaluations: Annotated[
        tuple[CandidateCalibrationEvaluationV1, ...],
        Field(min_length=3, max_length=3),
    ]
    replay_runs: Literal[20] = 20
    replay_output_deterministic: bool
    network_attempt_count: Literal[1] = 1
    network_access_performed: Literal[False] = False
    model_execution_count: Literal[0] = 0
    model_download_count: Literal[0] = 0
    external_text_input_count: Literal[0] = 0
    camera_or_media_input_count: Literal[0] = 0
    real_registration_mark_count: Literal[0] = 0
    gujarati_ocr_execution_count: Literal[0] = 0
    tesseract_execution_count: Literal[0] = 0
    consensus_execution_count: Literal[0] = 0
    operational_acceptance_count: Literal[0] = 0
    raw_output_persisted: Literal[False] = False
    normalized_output_persisted: Literal[False] = False
    grapheme_values_persisted: Literal[False] = False
    alternatives_persisted: Literal[False] = False
    sample_region_or_result_identifiers_persisted: Literal[False] = False
    plate_text_retention_hours: Literal[0] = 0
    quality_threshold_decided: Literal[False] = False
    promotion_authorized: Literal[False] = False
    deployment_authorized: Literal[False] = False
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def exact_generated_lanes_are_present(self) -> NormalizationGeneratedEvaluationV1:
        if {item.script_lane for item in self.slices} != {
            "latin",
            "devanagari",
            "gujarati",
        }:
            raise ValueError("W7 evidence requires all three generated script slices")
        if {item.candidate_id for item in self.calibration_evaluations} != {
            "OCR-L0",
            "OCR-L1",
            "OCR-D0",
        }:
            raise ValueError("W7 calibration evidence requires each approved OCR lane")
        return self


class SyntheticConsensusPolicyV1(ContractModel):
    """Default-off policy for generated, in-memory temporal consensus only."""

    contract_type: Literal["hcam.anpr.synthetic-consensus-policy.v1"] = (
        "hcam.anpr.synthetic-consensus-policy.v1"
    )
    enabled: bool = False
    environment: Literal["development", "test", "production"] = "development"
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    policy_version: Literal[ANPR_CONSENSUS_POLICY_VERSION] = (
        ANPR_CONSENSUS_POLICY_VERSION
    )
    grouping_key: Literal["stream_id_tracker_epoch_track_id"] = (
        "stream_id_tracker_epoch_track_id"
    )
    voting_method: Literal["exact_string_confidence_weighted"] = (
        "exact_string_confidence_weighted"
    )
    maximum_observations: Literal[5] = MAX_ANPR_CONSENSUS_OBSERVATIONS
    maximum_event_time_window_ms: Literal[2000] = MAX_ANPR_CONSENSUS_WINDOW_MS
    maximum_active_states_per_stream: Literal[256] = (
        MAX_ANPR_CONSENSUS_STATES_PER_STREAM
    )
    minimum_support: None = None
    minimum_margin: None = None
    thresholds_approved: Literal[False] = False
    result_acceptance: Literal["prohibited"] = "prohibited"
    network_access: Literal["denied"] = "denied"
    persistence: Literal["denied"] = "denied"
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def production_is_fail_closed(self) -> SyntheticConsensusPolicyV1:
        if self.enabled and self.environment == "production":
            raise ValueError("generated ANPR consensus is forbidden in production")
        return self


class EphemeralConsensusObservationV1(ContractModel):
    """One typed W7 result scoped to an anonymous stream-local track."""

    contract_type: Literal["hcam.anpr.ephemeral-consensus-observation.v1"] = (
        "hcam.anpr.ephemeral-consensus-observation.v1"
    )
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    stream_id: StreamId
    tracker_epoch: TrackerEpoch
    track_id: TrackId
    event_time_ms: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    source_sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    normalization: EphemeralPlateNormalizationV1
    ephemeral_only: Literal[True] = True
    retained: Literal[False] = False
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def only_core_generated_candidates_are_eligible(
        self,
    ) -> EphemeralConsensusObservationV1:
        if (
            self.normalization.source_id != self.source_id
            or self.normalization.script_lane != "latin"
            or self.normalization.candidate_id not in {"OCR-L0", "OCR-L1"}
            or self.normalization.format_family != "synthetic_non_issuable"
        ):
            raise ValueError(
                "consensus accepts only valid generated Latin core observations"
            )
        return self


class EphemeralConsensusVoteV1(ContractModel):
    """An exact-string vote that may exist only inside the bounded state machine."""

    normalized_display_candidate: SyntheticPlateToken
    observation_count: Annotated[
        int, Field(ge=1, le=MAX_ANPR_CONSENSUS_OBSERVATIONS)
    ]
    confidence_weight: Annotated[
        float, Field(ge=0, le=MAX_ANPR_CONSENSUS_OBSERVATIONS)
    ]
    first_event_time_ms: Annotated[int, Field(ge=0)]
    first_source_sequence: Annotated[int, Field(ge=0)]
    retained: Literal[False] = False


class EphemeralConsensusResultV1(ContractModel):
    """Closed consensus state; it is never eligible for evidence persistence."""

    contract_type: Literal["hcam.anpr.ephemeral-consensus-result.v1"] = (
        "hcam.anpr.ephemeral-consensus-result.v1"
    )
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    stream_id: StreamId
    tracker_epoch: TrackerEpoch
    track_id: TrackId
    policy_version: Literal[ANPR_CONSENSUS_POLICY_VERSION] = (
        ANPR_CONSENSUS_POLICY_VERSION
    )
    close_reason: ConsensusCloseReason
    first_event_time_ms: Annotated[int, Field(ge=0)]
    last_event_time_ms: Annotated[int, Field(ge=0)]
    observation_count: Annotated[
        int, Field(ge=1, le=MAX_ANPR_CONSENSUS_OBSERVATIONS)
    ]
    unique_candidate_count: Annotated[
        int, Field(ge=1, le=MAX_ANPR_CONSENSUS_OBSERVATIONS)
    ]
    ranked_votes: Annotated[
        tuple[EphemeralConsensusVoteV1, ...],
        Field(min_length=1, max_length=MAX_ANPR_CONSENSUS_OBSERVATIONS),
    ]
    winning_candidate: SyntheticPlateToken
    winning_support: Annotated[
        int, Field(ge=1, le=MAX_ANPR_CONSENSUS_OBSERVATIONS)
    ]
    winning_confidence_weight: Annotated[
        float, Field(ge=0, le=MAX_ANPR_CONSENSUS_OBSERVATIONS)
    ]
    confidence_margin: Annotated[
        float, Field(ge=0, le=MAX_ANPR_CONSENSUS_OBSERVATIONS)
    ]
    minimum_support: None = None
    minimum_margin: None = None
    thresholds_approved: Literal[False] = False
    abstain: Literal[True] = True
    abstention_reason: ConsensusAbstentionReason
    accepted_value_emitted: Literal[False] = False
    operational_event_emitted: Literal[False] = False
    persisted: Literal[False] = False
    ephemeral_only: Literal[True] = True
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def result_is_ranked_and_fail_closed(self) -> EphemeralConsensusResultV1:
        if self.last_event_time_ms < self.first_event_time_ms:
            raise ValueError("consensus result event times are reversed")
        if len(self.ranked_votes) != self.unique_candidate_count:
            raise ValueError("consensus unique-candidate count is inconsistent")
        if sum(item.observation_count for item in self.ranked_votes) != (
            self.observation_count
        ):
            raise ValueError("consensus vote counts do not cover observations")
        expected_ranking = tuple(
            sorted(
                self.ranked_votes,
                key=lambda item: (
                    -item.confidence_weight,
                    -item.observation_count,
                    item.normalized_display_candidate,
                ),
            )
        )
        if self.ranked_votes != expected_ranking:
            raise ValueError("consensus votes are not in canonical rank order")
        winner = self.ranked_votes[0]
        if (
            winner.normalized_display_candidate != self.winning_candidate
            or winner.observation_count != self.winning_support
            or winner.confidence_weight != self.winning_confidence_weight
        ):
            raise ValueError("consensus winner does not match the first ranked vote")
        runner_up_weight = (
            self.ranked_votes[1].confidence_weight
            if len(self.ranked_votes) > 1
            else 0.0
        )
        expected_margin = Decimal(str(winner.confidence_weight)) - Decimal(
            str(runner_up_weight)
        )
        if Decimal(str(self.confidence_margin)) != expected_margin:
            raise ValueError("consensus confidence margin is inconsistent")
        expected_reason: ConsensusAbstentionReason = (
            "overload_fail_closed"
            if self.close_reason == "overload"
            else "consensus_thresholds_unapproved"
        )
        if self.abstention_reason != expected_reason:
            raise ValueError("consensus abstention reason is inconsistent")
        return self


class ConsensusGeneratedScenarioV1(ContractModel):
    scenario: ConsensusScenario
    execution_count: Annotated[int, Field(ge=1, le=100_000)]
    closed_result_count: Annotated[int, Field(ge=0, le=100_000)]
    abstained_result_count: Annotated[int, Field(ge=0, le=100_000)]
    violation_count: Annotated[int, Field(ge=0, le=100_000)]

    @model_validator(mode="after")
    def counts_are_consistent(self) -> ConsensusGeneratedScenarioV1:
        if (
            self.abstained_result_count != self.closed_result_count
            or self.closed_result_count > self.execution_count
            or self.violation_count > self.execution_count
        ):
            raise ValueError("generated consensus scenario counts are inconsistent")
        return self


class ConsensusGeneratedEvaluationV1(ContractModel):
    contract_type: Literal[
        "hcam.phase3.p3_5.consensus-generated-evaluation.v1"
    ] = "hcam.phase3.p3_5.consensus-generated-evaluation.v1"
    work_package: Literal["P35-W8_bounded_synthetic_track_local_consensus"] = (
        "P35-W8_bounded_synthetic_track_local_consensus"
    )
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    consensus_policy_version: Literal[ANPR_CONSENSUS_POLICY_VERSION] = (
        ANPR_CONSENSUS_POLICY_VERSION
    )
    grouping_key: Literal["stream_id_tracker_epoch_track_id"] = (
        "stream_id_tracker_epoch_track_id"
    )
    voting_method: Literal["exact_string_confidence_weighted"] = (
        "exact_string_confidence_weighted"
    )
    scenario_evaluations: Annotated[
        tuple[ConsensusGeneratedScenarioV1, ...], Field(min_length=9, max_length=9)
    ]
    replay_runs: Literal[20] = 20
    replay_output_deterministic: bool
    maximum_observations: Literal[5] = MAX_ANPR_CONSENSUS_OBSERVATIONS
    maximum_event_time_window_ms: Literal[2000] = MAX_ANPR_CONSENSUS_WINDOW_MS
    maximum_active_states_per_stream: Literal[256] = (
        MAX_ANPR_CONSENSUS_STATES_PER_STREAM
    )
    maximum_active_states_observed: Annotated[int, Field(ge=0, le=256)]
    consensus_execution_count: Annotated[int, Field(ge=1, le=100_000)]
    consensus_closed_result_count: Annotated[int, Field(ge=1, le=100_000)]
    consensus_abstained_result_count: Annotated[int, Field(ge=1, le=100_000)]
    duplicate_rejection_count: Annotated[int, Field(ge=1, le=100_000)]
    out_of_order_rejection_count: Annotated[int, Field(ge=1, le=100_000)]
    cross_stream_epoch_or_track_merge_count: Literal[0] = 0
    network_attempt_count: Literal[1] = 1
    network_access_performed: Literal[False] = False
    model_execution_count: Literal[0] = 0
    model_download_count: Literal[0] = 0
    external_text_input_count: Literal[0] = 0
    camera_or_media_input_count: Literal[0] = 0
    real_registration_mark_count: Literal[0] = 0
    accepted_value_count: Literal[0] = 0
    operational_event_count: Literal[0] = 0
    threshold_configuration_approved: Literal[False] = False
    minimum_support: None = None
    minimum_margin: None = None
    plate_or_normalized_text_persisted: Literal[False] = False
    ranked_votes_persisted: Literal[False] = False
    stream_epoch_or_track_identifiers_persisted: Literal[False] = False
    plate_text_retention_hours: Literal[0] = 0
    promotion_authorized: Literal[False] = False
    deployment_authorized: Literal[False] = False
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def exact_scenarios_and_totals_are_present(
        self,
    ) -> ConsensusGeneratedEvaluationV1:
        expected = {
            "agreement",
            "cross_boundary_isolation",
            "disagreement",
            "duplicate_rejection",
            "epoch_reset",
            "event_time_window",
            "out_of_order_rejection",
            "overload",
            "track_end",
        }
        if {item.scenario for item in self.scenario_evaluations} != expected:
            raise ValueError("W8 evidence requires every bounded consensus scenario")
        if sum(
            item.closed_result_count for item in self.scenario_evaluations
        ) != self.consensus_closed_result_count:
            raise ValueError("W8 scenario close counts are inconsistent")
        if sum(
            item.abstained_result_count for item in self.scenario_evaluations
        ) != self.consensus_abstained_result_count:
            raise ValueError("W8 scenario abstention counts are inconsistent")
        if self.consensus_abstained_result_count != self.consensus_closed_result_count:
            raise ValueError("W8 cannot emit a non-abstaining consensus result")
        if sum(
            item.execution_count for item in self.scenario_evaluations
        ) != self.consensus_execution_count:
            raise ValueError("W8 scenario execution counts are inconsistent")
        scenario_map = {item.scenario: item for item in self.scenario_evaluations}
        if (
            scenario_map["duplicate_rejection"].violation_count
            != self.duplicate_rejection_count
            or scenario_map["out_of_order_rejection"].violation_count
            != self.out_of_order_rejection_count
        ):
            raise ValueError("W8 rejection counts are inconsistent")
        return self


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
            "ground_truth_crop_descriptor": GroundTruthCropDescriptorV1.model_json_schema(
                mode="validation"
            ),
            "ground_truth_region": SealedGroundTruthPlateRegionV1.model_json_schema(
                mode="validation"
            ),
            "ephemeral_latin_ocr_hypothesis": EphemeralLatinOcrHypothesisV1.model_json_schema(
                mode="validation"
            ),
            "ephemeral_auxiliary_ocr_hypothesis": EphemeralAuxiliaryOcrHypothesisV1.model_json_schema(
                mode="validation"
            ),
            "ephemeral_plate_normalization": EphemeralPlateNormalizationV1.model_json_schema(
                mode="validation"
            ),
            "ephemeral_consensus_observation": EphemeralConsensusObservationV1.model_json_schema(
                mode="validation"
            ),
            "ephemeral_consensus_result": EphemeralConsensusResultV1.model_json_schema(
                mode="validation"
            ),
            "synthetic_consensus_policy": SyntheticConsensusPolicyV1.model_json_schema(
                mode="validation"
            ),
            "auxiliary_script_generated_evaluation": AuxiliaryScriptGeneratedEvaluationV1.model_json_schema(
                mode="validation"
            ),
            "latin_ocr_generated_evaluation": LatinOcrGeneratedEvaluationV1.model_json_schema(
                mode="validation"
            ),
            "normalization_generated_evaluation": NormalizationGeneratedEvaluationV1.model_json_schema(
                mode="validation"
            ),
            "consensus_generated_evaluation": ConsensusGeneratedEvaluationV1.model_json_schema(
                mode="validation"
            ),
            "plate_localization_result": PlateLocalizationResultV1.model_json_schema(
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
            "maximum_crop_height": MAX_ANPR_CROP_HEIGHT,
            "maximum_crop_width": MAX_ANPR_CROP_WIDTH,
            "maximum_document_depth": MAX_ANPR_DOCUMENT_DEPTH,
            "maximum_document_nodes": MAX_ANPR_DOCUMENT_NODES,
            "maximum_frame_height": MAX_ANPR_FRAME_HEIGHT,
            "maximum_frame_width": MAX_ANPR_FRAME_WIDTH,
            "maximum_local_samples": MAX_ANPR_LOCAL_SAMPLES,
            "maximum_plate_regions_per_frame": MAX_ANPR_PLATE_REGIONS,
            "maximum_request_bytes": MAX_ANPR_REQUEST_BYTES,
        },
        "localization_policy": {
            "localizer_id": "GT-PLATE-R0",
            "localizer_version": ANPR_GROUND_TRUTH_LOCALIZER_VERSION,
            "rectifier_version": ANPR_RECTIFIER_VERSION,
            "execution_mode": "generated_ground_truth_only",
            "candidate_id": None,
            "model_execution_performed": False,
            "weights_loaded": False,
            "crop_pixels_in_contracts": False,
            "plate_text_in_contracts": False,
        },
        "latin_ocr_policy": {
            "adapter_version": ANPR_LATIN_OCR_ADAPTER_VERSION,
            "renderer_version": ANPR_LATIN_RENDERER_VERSION,
            "dictionary_version": ANPR_LATIN_DICTIONARY_VERSION,
            "candidates": {
                "OCR-L0": OCR_L0_ARTIFACT_SHA256,
                "OCR-L1": OCR_L1_ARTIFACT_SHA256,
            },
            "raw_output_ephemeral_only": True,
            "maximum_unicode_scalars": 32,
            "maximum_grapheme_clusters": 16,
            "maximum_alternatives": 5,
            "generated_only": True,
            "promotion_authorized": False,
        },
        "auxiliary_script_policy": {
            "generator_version": ANPR_AUXILIARY_GENERATOR_VERSION,
            "renderer_version": ANPR_AUXILIARY_RENDERER_VERSION,
            "devanagari_adapter_version": ANPR_DEVANAGARI_OCR_ADAPTER_VERSION,
            "devanagari_dictionary_version": ANPR_DEVANAGARI_DICTIONARY_VERSION,
            "ocr_candidate": {"OCR-D0": OCR_D0_ARTIFACT_SHA256},
            "font_candidates": {
                "FONT-D0": FONT_D0_ARTIFACT_SHA256,
                "FONT-G0": FONT_G0_ARTIFACT_SHA256,
            },
            "closed_internal_vocabulary": True,
            "standalone_graphemes_only": True,
            "complex_shaping_used": False,
            "gujarati_ocr_authorized": False,
            "modifies_registration_mark": False,
            "transliteration_allowed": False,
            "generated_only": True,
            "promotion_authorized": False,
        },
        "normalization_policy": {
            "normalization_version": ANPR_NORMALIZATION_VERSION,
            "grapheme_policy_version": ANPR_GRAPHEME_POLICY_VERSION,
            "calibration_version": ANPR_CALIBRATION_VERSION,
            "abstention_policy_version": ANPR_ABSTENTION_POLICY_VERSION,
            "python_version": ANPR_PINNED_PYTHON_VERSION,
            "regex_version": ANPR_PINNED_REGEX_VERSION,
            "unicode_version": ANPR_PINNED_UNICODE_VERSION,
            "normalization_form": "NFC",
            "compatibility_normalization_allowed": False,
            "transliteration_allowed": False,
            "dictionary_completion_allowed": False,
            "confusable_autocorrection_allowed": False,
            "record_lookup_allowed": False,
            "raw_output_mutation_allowed": False,
            "calibration_method": "identity_generated_baseline",
            "quality_threshold_approved": False,
            "operational_acceptance_allowed": False,
            "generated_only": True,
        },
        "persistence_policy": {
            "plate_text_retention_hours": 0,
            "token_or_alternative_in_evidence": False,
            "identifier_free_aggregate_evidence_only": True,
        },
    }
