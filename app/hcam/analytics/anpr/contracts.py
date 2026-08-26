from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, Field, model_validator

from hcam.analytics.contracts import (
    ContractModel,
    ImmutableDigest,
    NormalizedBoundingBox,
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
MAX_ANPR_REQUEST_BYTES = 4 * 1024
MAX_ANPR_DOCUMENT_DEPTH = 8
MAX_ANPR_DOCUMENT_NODES = 256
MAX_ANPR_LOCAL_SAMPLES = 10_000
MAX_ANPR_FRAME_WIDTH = 1_280
MAX_ANPR_FRAME_HEIGHT = 720
MAX_ANPR_PLATE_REGIONS = 8
MAX_ANPR_CROP_WIDTH = 512
MAX_ANPR_CROP_HEIGHT = 128

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
            "latin_ocr_generated_evaluation": LatinOcrGeneratedEvaluationV1.model_json_schema(
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
        "persistence_policy": {
            "plate_text_retention_hours": 0,
            "token_or_alternative_in_evidence": False,
            "identifier_free_aggregate_evidence_only": True,
        },
    }
