from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

from hcam.analytics.anpr.contracts import (
    ANPR_FRAME_GENERATOR_VERSION,
    ANPR_GENERATED_SOURCE_ID,
    ANPR_GENERATOR_VERSION,
    ANPR_GROUND_TRUTH_LOCALIZER_VERSION,
    ANPR_RECTIFIER_VERSION,
    MAX_ANPR_CROP_HEIGHT,
    MAX_ANPR_CROP_WIDTH,
    MAX_ANPR_FRAME_HEIGHT,
    MAX_ANPR_FRAME_WIDTH,
    AnprSplit,
    GeneratedTokenRequestV1,
    GroundTruthCropDescriptorV1,
    GroundTruthPlateRegionContentV1,
    NormalizedPointV1,
    PlateLocalizationHypothesisV1,
    PlateLocalizationResultV1,
    SealedGroundTruthPlateRegionV1,
    SyntheticAnprExecutionPolicyV1,
    SyntheticCorpusPlanV1,
    seal_ground_truth_region,
)
from hcam.analytics.anpr.generator import (
    derive_generated_request,
    derive_split_manifest_entry,
    generate_ephemeral_token,
)
from hcam.analytics.contracts import NormalizedBoundingBox


AnprLocalizationCode = Literal[
    "crop_byte_count_mismatch",
    "crop_digest_mismatch",
    "crop_dimensions_invalid",
    "frame_byte_count_mismatch",
    "frame_dimensions_invalid",
    "generated_lineage_mismatch",
    "region_out_of_bounds",
]

_FRAME_WIDTH = 640
_FRAME_HEIGHT = 360
_BYTES_PER_PIXEL = 3


class AnprLocalizationViolation(ValueError):
    """Bounded W4 failure that never includes generated content or pixel data."""

    def __init__(self, code: AnprLocalizationCode) -> None:
        super().__init__(f"P3.5 ground-truth localization failed: {code}")
        self.code = code


def _digest_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _identifier(prefix: str, domain: str, value: object) -> str:
    hasher = hashlib.sha256()
    hasher.update(domain.encode("ascii"))
    hasher.update(b"\0")
    hasher.update(_canonical_bytes(value))
    return f"{prefix}_{hasher.hexdigest()[:32]}"


@dataclass(frozen=True, slots=True)
class GeneratedPlateFrameV1:
    """In-memory generated frame. Pixel bytes are intentionally not serializable."""

    width: int
    height: int
    bgr_bytes: bytes
    request: GeneratedTokenRequestV1
    ground_truth_region: SealedGroundTruthPlateRegionV1
    source_id: str = ANPR_GENERATED_SOURCE_ID
    generator_version: str = ANPR_GENERATOR_VERSION
    frame_generator_version: str = ANPR_FRAME_GENERATOR_VERSION
    pixel_format: str = "bgr8"

    def __post_init__(self) -> None:
        if not (
            1 <= self.width <= MAX_ANPR_FRAME_WIDTH
            and 1 <= self.height <= MAX_ANPR_FRAME_HEIGHT
        ):
            raise AnprLocalizationViolation("frame_dimensions_invalid")
        if len(self.bgr_bytes) != self.width * self.height * _BYTES_PER_PIXEL:
            raise AnprLocalizationViolation("frame_byte_count_mismatch")
        content = self.ground_truth_region.content
        if (
            self.source_id != ANPR_GENERATED_SOURCE_ID
            or self.generator_version != ANPR_GENERATOR_VERSION
            or self.frame_generator_version != ANPR_FRAME_GENERATOR_VERSION
            or self.pixel_format != "bgr8"
            or self.request.source_id != self.source_id
            or self.request.generator_version != self.generator_version
            or content.source_id != self.source_id
            or content.generator_version != self.generator_version
            or content.frame_generator_version != self.frame_generator_version
            or content.layout != self.request.layout
        ):
            raise AnprLocalizationViolation("generated_lineage_mismatch")

    @property
    def frame_digest(self) -> str:
        return _digest_bytes(self.bgr_bytes)


@dataclass(frozen=True, slots=True)
class EphemeralGroundTruthCropV1:
    """Rectified pixels exist only in memory; evidence receives the descriptor."""

    descriptor: GroundTruthCropDescriptorV1
    bgr_bytes: bytes

    def __post_init__(self) -> None:
        if len(self.bgr_bytes) != (
            self.descriptor.width * self.descriptor.height * _BYTES_PER_PIXEL
        ):
            raise AnprLocalizationViolation("crop_byte_count_mismatch")
        if _digest_bytes(self.bgr_bytes) != self.descriptor.crop_digest:
            raise AnprLocalizationViolation("crop_digest_mismatch")


def _fill_rectangle(
    frame: bytearray,
    *,
    frame_width: int,
    x: int,
    y: int,
    width: int,
    height: int,
    color: bytes,
) -> None:
    row = color * width
    stride = frame_width * _BYTES_PER_PIXEL
    for row_index in range(y, y + height):
        start = row_index * stride + x * _BYTES_PER_PIXEL
        frame[start : start + len(row)] = row


def _draw_procedural_marker(
    frame: bytearray,
    *,
    frame_width: int,
    x: int,
    y: int,
    width: int,
    height: int,
    marker_digest: bytes,
    two_line: bool,
) -> None:
    """Draw non-font geometry so W4 is not an OCR or text-rendering path."""

    columns = 4 if two_line else 8
    rows = 2 if two_line else 1
    gap = 5
    cell_width = max(4, (width - gap * (columns + 1)) // columns)
    cell_height = max(8, (height - gap * (rows + 1)) // rows)
    for row_index in range(rows):
        for column_index in range(columns):
            marker_index = row_index * columns + column_index
            marker = marker_digest[marker_index]
            cell_x = x + gap + column_index * (cell_width + gap)
            cell_y = y + gap + row_index * (cell_height + gap)
            bar_width = max(2, cell_width // 3)
            bar_height = max(3, cell_height // 3)
            if marker & 1:
                _fill_rectangle(
                    frame,
                    frame_width=frame_width,
                    x=cell_x,
                    y=cell_y,
                    width=bar_width,
                    height=cell_height,
                    color=b"\x22\x22\x22",
                )
            if marker & 2:
                _fill_rectangle(
                    frame,
                    frame_width=frame_width,
                    x=cell_x,
                    y=cell_y,
                    width=cell_width,
                    height=bar_height,
                    color=b"\x22\x22\x22",
                )
            if marker & 4:
                _fill_rectangle(
                    frame,
                    frame_width=frame_width,
                    x=cell_x + cell_width - bar_width,
                    y=cell_y,
                    width=bar_width,
                    height=cell_height,
                    color=b"\x22\x22\x22",
                )
            if marker & 8:
                _fill_rectangle(
                    frame,
                    frame_width=frame_width,
                    x=cell_x,
                    y=cell_y + cell_height - bar_height,
                    width=cell_width,
                    height=bar_height,
                    color=b"\x22\x22\x22",
                )


def generate_ground_truth_plate_frame(
    plan: SyntheticCorpusPlanV1,
    split: AnprSplit,
    sample_index: int,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
) -> GeneratedPlateFrameV1:
    request = derive_generated_request(plan, split, sample_index)
    manifest_entry = derive_split_manifest_entry(plan, split, sample_index)
    ephemeral = generate_ephemeral_token(request, policy=policy)
    marker_digest = hashlib.sha256(
        b"hcam.anpr.p35w4.procedural-marker.v1\0" + ephemeral.token.encode("ascii")
    ).digest()

    frame = bytearray(b"\x34\x2c\x24" * (_FRAME_WIDTH * _FRAME_HEIGHT))
    _fill_rectangle(
        frame,
        frame_width=_FRAME_WIDTH,
        x=70,
        y=80,
        width=500,
        height=230,
        color=bytes((70 + marker_digest[2] % 40, 92, 118)),
    )

    region_width, region_height = (
        (240, 64) if request.layout == "single_line" else (168, 96)
    )
    x = 110 + marker_digest[0] % (_FRAME_WIDTH - region_width - 220)
    y = 185 + marker_digest[1] % (90 - region_height // 2)
    _fill_rectangle(
        frame,
        frame_width=_FRAME_WIDTH,
        x=x - 4,
        y=y - 4,
        width=region_width + 8,
        height=region_height + 8,
        color=b"\x18\x18\x18",
    )
    _fill_rectangle(
        frame,
        frame_width=_FRAME_WIDTH,
        x=x,
        y=y,
        width=region_width,
        height=region_height,
        color=b"\xe8\xec\xf0",
    )
    _draw_procedural_marker(
        frame,
        frame_width=_FRAME_WIDTH,
        x=x,
        y=y,
        width=region_width,
        height=region_height,
        marker_digest=marker_digest,
        two_line=request.layout == "two_line",
    )

    bbox = NormalizedBoundingBox(
        x=x / _FRAME_WIDTH,
        y=y / _FRAME_HEIGHT,
        width=region_width / _FRAME_WIDTH,
        height=region_height / _FRAME_HEIGHT,
    )
    right = bbox.x + bbox.width
    bottom = bbox.y + bbox.height
    region_material = {
        "bbox": bbox.model_dump(mode="json"),
        "frame_generator_version": ANPR_FRAME_GENERATOR_VERSION,
        "sample_id": manifest_entry.sample_id,
    }
    region = seal_ground_truth_region(
        GroundTruthPlateRegionContentV1(
            region_id=_identifier(
                "anprregion",
                "hcam.anpr.p35w4.region-id.v1",
                region_material,
            ),
            sample_id=manifest_entry.sample_id,
            layout=request.layout,
            bbox=bbox,
            quadrilateral=(
                NormalizedPointV1(x=bbox.x, y=bbox.y),
                NormalizedPointV1(x=right, y=bbox.y),
                NormalizedPointV1(x=right, y=bottom),
                NormalizedPointV1(x=bbox.x, y=bottom),
            ),
        )
    )
    return GeneratedPlateFrameV1(
        width=_FRAME_WIDTH,
        height=_FRAME_HEIGHT,
        bgr_bytes=bytes(frame),
        request=request,
        ground_truth_region=region,
    )


def localize_generated_ground_truth(
    frame: GeneratedPlateFrameV1,
) -> PlateLocalizationResultV1:
    region = frame.ground_truth_region
    content = region.content
    material = {
        "frame_digest": frame.frame_digest,
        "localizer_version": ANPR_GROUND_TRUTH_LOCALIZER_VERSION,
        "region_digest": region.region_digest,
    }
    hypothesis = PlateLocalizationHypothesisV1(
        hypothesis_id=_identifier(
            "anprhyp",
            "hcam.anpr.p35w4.hypothesis-id.v1",
            material,
        ),
        bbox=content.bbox,
        quadrilateral=content.quadrilateral,
        region_digest=region.region_digest,
    )
    return PlateLocalizationResultV1(
        result_id=_identifier(
            "anprloc",
            "hcam.anpr.p35w4.localization-id.v1",
            material,
        ),
        sample_id=content.sample_id,
        source_frame_digest=frame.frame_digest,
        hypothesis_count=1,
        hypotheses=(hypothesis,),
    )


def _pixel_bounds(frame: GeneratedPlateFrameV1) -> tuple[int, int, int, int]:
    bbox = frame.ground_truth_region.content.bbox
    left = round(bbox.x * frame.width)
    top = round(bbox.y * frame.height)
    right = round((bbox.x + bbox.width) * frame.width)
    bottom = round((bbox.y + bbox.height) * frame.height)
    if not (0 <= left < right <= frame.width and 0 <= top < bottom <= frame.height):
        raise AnprLocalizationViolation("region_out_of_bounds")
    if right - left > MAX_ANPR_CROP_WIDTH or bottom - top > MAX_ANPR_CROP_HEIGHT:
        raise AnprLocalizationViolation("crop_dimensions_invalid")
    return left, top, right, bottom


def extract_generated_ground_truth_crop(
    frame: GeneratedPlateFrameV1,
) -> EphemeralGroundTruthCropV1:
    left, top, right, bottom = _pixel_bounds(frame)
    crop_width = right - left
    crop_height = bottom - top
    frame_stride = frame.width * _BYTES_PER_PIXEL
    crop_rows = []
    for row_index in range(top, bottom):
        start = row_index * frame_stride + left * _BYTES_PER_PIXEL
        end = start + crop_width * _BYTES_PER_PIXEL
        crop_rows.append(frame.bgr_bytes[start:end])
    crop_bytes = b"".join(crop_rows)
    region = frame.ground_truth_region
    material = {
        "crop_digest": _digest_bytes(crop_bytes),
        "rectifier_version": ANPR_RECTIFIER_VERSION,
        "region_digest": region.region_digest,
    }
    descriptor = GroundTruthCropDescriptorV1(
        crop_id=_identifier(
            "anprcrop",
            "hcam.anpr.p35w4.crop-id.v1",
            material,
        ),
        sample_id=region.content.sample_id,
        region_digest=region.region_digest,
        source_frame_digest=frame.frame_digest,
        crop_digest=_digest_bytes(crop_bytes),
        width=crop_width,
        height=crop_height,
        transform_matrix=(
            1.0,
            0.0,
            float(-left),
            0.0,
            1.0,
            float(-top),
            0.0,
            0.0,
            1.0,
        ),
    )
    return EphemeralGroundTruthCropV1(descriptor=descriptor, bgr_bytes=crop_bytes)


def generated_ground_truth_fixture(
    plan: SyntheticCorpusPlanV1,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
) -> tuple[
    GeneratedPlateFrameV1,
    PlateLocalizationResultV1,
    EphemeralGroundTruthCropV1,
]:
    frame = generate_ground_truth_plate_frame(
        plan,
        "contract_fixture",
        0,
        policy=policy,
    )
    return (
        frame,
        localize_generated_ground_truth(frame),
        extract_generated_ground_truth_crop(frame),
    )
