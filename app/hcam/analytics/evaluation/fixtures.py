from __future__ import annotations

import hashlib
import json
import random
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from hcam.analytics.contracts import NormalizedBoundingBox
from hcam.analytics.evaluation.contracts import (
    ClassId,
    EvaluationContractModel,
    StableId,
)


FIXTURE_SEED = 31_001
APPROVED_EMITTED_CLASSES = (
    "object.person",
    "vehicle.bicycle",
    "vehicle.motorcycle",
    "vehicle.car",
    "vehicle.bus",
    "vehicle.truck",
    "object.unknown",
)


class DetectionTruthV1(EvaluationContractModel):
    object_id: StableId
    class_id: ClassId
    bbox: NormalizedBoundingBox
    occlusion: Literal["none", "partial", "heavy"] = "none"
    truncated: bool = False


class DetectionPredictionV1(EvaluationContractModel):
    prediction_id: StableId
    class_id: ClassId
    confidence: Annotated[float, Field(ge=0, le=1)]
    bbox: NormalizedBoundingBox


class DetectionFixtureV1(EvaluationContractModel):
    case_id: StableId
    scenario: StableId
    frame_width: Annotated[int, Field(ge=16, le=32_768)]
    frame_height: Annotated[int, Field(ge=16, le=32_768)]
    truths: Annotated[list[DetectionTruthV1], Field(max_length=128)] = Field(
        default_factory=list
    )
    predictions: Annotated[list[DetectionPredictionV1], Field(max_length=256)] = Field(
        default_factory=list
    )
    expected_outcome: Literal["match", "miss", "false_positive", "reject", "empty"]
    slices: Annotated[list[StableId], Field(min_length=1, max_length=32)]


class TrackingAssociationV1(EvaluationContractModel):
    frame_sequence: Annotated[int, Field(ge=0, le=1_000_000)]
    truth_track_id: StableId | None = None
    predicted_track_id: StableId | None = None
    visible: bool

    @model_validator(mode="after")
    def association_has_an_entity(self) -> TrackingAssociationV1:
        if self.truth_track_id is None and self.predicted_track_id is None:
            raise ValueError("tracking association requires a truth or predicted track")
        return self


class TrackingFixtureV1(EvaluationContractModel):
    case_id: StableId
    scenario: StableId
    tracker_epoch: StableId
    associations: Annotated[
        list[TrackingAssociationV1],
        Field(min_length=1, max_length=10_000),
    ]
    expected_identity_switches: Annotated[int, Field(ge=0, le=10_000)]
    expected_fragments: Annotated[int, Field(ge=0, le=10_000)]
    expected_outcome: Literal["pass", "reject", "reset"]

    @field_validator("associations")
    @classmethod
    def frames_are_ordered(cls, value: list[TrackingAssociationV1]) -> list[TrackingAssociationV1]:
        sequences = [item.frame_sequence for item in value]
        if sequences != sorted(sequences):
            raise ValueError("tracking associations must be ordered by frame sequence")
        return value


class PointV1(EvaluationContractModel):
    x: Annotated[float, Field(ge=0, le=1)]
    y: Annotated[float, Field(ge=0, le=1)]


class GeometryFixtureV1(EvaluationContractModel):
    case_id: StableId
    scenario: StableId
    geometry_kind: Literal["line", "zone", "schedule", "ordering"]
    trajectory: Annotated[list[PointV1], Field(min_length=1, max_length=1_000)]
    expected_events: Annotated[list[StableId], Field(max_length=64)] = Field(
        default_factory=list
    )
    duplicate_input_count: Annotated[int, Field(ge=0, le=1_000)] = 0
    late_input_count: Annotated[int, Field(ge=0, le=1_000)] = 0
    expected_outcome: Literal["pass", "reject", "inactive"]


class PlateAlternativeV1(EvaluationContractModel):
    text: Annotated[str, Field(min_length=1, max_length=32)]
    confidence: Annotated[float, Field(ge=0, le=1)]


class SyntheticPlateFixtureV1(EvaluationContractModel):
    case_id: StableId
    scenario: StableId
    script: Literal["Latin", "Devanagari", "Gujarati"]
    truth_text: Annotated[str, Field(min_length=1, max_length=32)]
    alternatives: Annotated[list[PlateAlternativeV1], Field(max_length=8)] = Field(
        default_factory=list
    )
    abstained: bool
    valid_format: bool
    region_bbox: NormalizedBoundingBox
    expected_outcome: Literal["exact", "alternative", "abstain", "reject"]

    @model_validator(mode="after")
    def abstention_has_no_alternatives(self) -> SyntheticPlateFixtureV1:
        if self.abstained and self.alternatives:
            raise ValueError("abstained plate fixture cannot contain alternatives")
        if not self.abstained and not self.alternatives:
            raise ValueError("non-abstained plate fixture requires alternatives")
        return self


class MisuseFixtureV1(EvaluationContractModel):
    case_id: StableId
    prohibited_field: StableId
    payload_kind: Literal[
        "path",
        "url",
        "credential",
        "media",
        "biometric",
        "owner",
        "government",
        "watchlist",
        "oversized",
        "invalid_digest",
    ]
    expected_failure_code: StableId
    contains_sensitive_value: Literal[False] = False


def _box(rng: random.Random, *, small: bool = False) -> NormalizedBoundingBox:
    width = 0.02 if small else round(rng.uniform(0.12, 0.24), 4)
    height = 0.03 if small else round(rng.uniform(0.16, 0.32), 4)
    x = round(rng.uniform(0.05, 0.9 - width), 4)
    y = round(rng.uniform(0.05, 0.9 - height), 4)
    return NormalizedBoundingBox(x=x, y=y, width=width, height=height)


def generated_detection_fixtures(seed: int = FIXTURE_SEED) -> list[DetectionFixtureV1]:
    rng = random.Random(seed)
    fixtures: list[DetectionFixtureV1] = []
    for index, class_id in enumerate(APPROVED_EMITTED_CLASSES, start=1):
        bbox = _box(rng)
        fixtures.append(
            DetectionFixtureV1(
                case_id=f"det-class-{index:02d}",
                scenario="approved-class",
                frame_width=640,
                frame_height=360,
                truths=[
                    DetectionTruthV1(
                        object_id=f"truth-{index:02d}",
                        class_id=class_id,
                        bbox=bbox,
                    )
                ],
                predictions=[
                    DetectionPredictionV1(
                        prediction_id=f"prediction-{index:02d}",
                        class_id=class_id,
                        confidence=round(0.99 - index * 0.01, 4),
                        bbox=bbox,
                    )
                ],
                expected_outcome="match",
                slices=["class-coverage", class_id.replace(".", "-")],
            )
        )

    fixtures.extend(
        [
            DetectionFixtureV1(
                case_id="det-empty-scene",
                scenario="empty-scene",
                frame_width=640,
                frame_height=360,
                expected_outcome="empty",
                slices=["empty-scene"],
            ),
            DetectionFixtureV1(
                case_id="det-overlap",
                scenario="overlap",
                frame_width=640,
                frame_height=360,
                truths=[
                    DetectionTruthV1(
                        object_id="truth-overlap-a",
                        class_id="object.person",
                        bbox=NormalizedBoundingBox(x=0.2, y=0.2, width=0.2, height=0.4),
                        occlusion="partial",
                    ),
                    DetectionTruthV1(
                        object_id="truth-overlap-b",
                        class_id="vehicle.motorcycle",
                        bbox=NormalizedBoundingBox(x=0.3, y=0.35, width=0.3, height=0.3),
                        occlusion="partial",
                    ),
                ],
                predictions=[],
                expected_outcome="miss",
                slices=["overlap", "occlusion-partial"],
            ),
            DetectionFixtureV1(
                case_id="det-truncated",
                scenario="truncation",
                frame_width=640,
                frame_height=360,
                truths=[
                    DetectionTruthV1(
                        object_id="truth-truncated",
                        class_id="vehicle.bus",
                        bbox=NormalizedBoundingBox(x=0.0, y=0.4, width=0.35, height=0.5),
                        truncated=True,
                    )
                ],
                predictions=[],
                expected_outcome="miss",
                slices=["truncation"],
            ),
            DetectionFixtureV1(
                case_id="det-heavy-occlusion",
                scenario="occlusion",
                frame_width=640,
                frame_height=360,
                truths=[
                    DetectionTruthV1(
                        object_id="truth-occluded",
                        class_id="vehicle.car",
                        bbox=_box(rng),
                        occlusion="heavy",
                    )
                ],
                predictions=[],
                expected_outcome="miss",
                slices=["occlusion-heavy"],
            ),
            DetectionFixtureV1(
                case_id="det-small-object",
                scenario="small-object",
                frame_width=1_920,
                frame_height=1_080,
                truths=[
                    DetectionTruthV1(
                        object_id="truth-small",
                        class_id="vehicle.bicycle",
                        bbox=_box(rng, small=True),
                    )
                ],
                predictions=[],
                expected_outcome="miss",
                slices=["small-object"],
            ),
            DetectionFixtureV1(
                case_id="det-low-contrast",
                scenario="low-contrast",
                frame_width=640,
                frame_height=360,
                truths=[
                    DetectionTruthV1(
                        object_id="truth-low-contrast",
                        class_id="object.person",
                        bbox=_box(rng),
                    )
                ],
                predictions=[],
                expected_outcome="miss",
                slices=["low-contrast"],
            ),
            DetectionFixtureV1(
                case_id="det-false-positive",
                scenario="false-positive",
                frame_width=640,
                frame_height=360,
                predictions=[
                    DetectionPredictionV1(
                        prediction_id="prediction-false",
                        class_id="vehicle.truck",
                        confidence=0.51,
                        bbox=_box(rng),
                    )
                ],
                expected_outcome="false_positive",
                slices=["false-positive"],
            ),
            DetectionFixtureV1(
                case_id="det-malformed-prediction",
                scenario="malformed-prediction",
                frame_width=640,
                frame_height=360,
                expected_outcome="reject",
                slices=["invalid-input"],
            ),
        ]
    )
    return fixtures


def generated_tracking_fixtures() -> list[TrackingFixtureV1]:
    cases = (
        ("start", "pass", 0, 0),
        ("update", "pass", 0, 0),
        ("end", "pass", 0, 0),
        ("occlusion", "pass", 0, 1),
        ("crossing-tracks", "pass", 1, 0),
        ("duplicate-detection", "reject", 0, 0),
        ("missed-frames", "pass", 0, 1),
        ("discontinuity", "reset", 0, 0),
        ("reconnect", "reset", 0, 0),
        ("bounded-state", "pass", 0, 0),
    )
    fixtures: list[TrackingFixtureV1] = []
    for index, (scenario, outcome, switches, fragments) in enumerate(cases, start=1):
        associations = [
            TrackingAssociationV1(
                frame_sequence=frame,
                truth_track_id="truth-track-a",
                predicted_track_id=(
                    "predicted-track-b"
                    if switches and frame == 2
                    else "predicted-track-a"
                ),
                visible=not (scenario in {"occlusion", "missed-frames"} and frame == 1),
            )
            for frame in range(3)
        ]
        fixtures.append(
            TrackingFixtureV1(
                case_id=f"track-{index:02d}",
                scenario=scenario,
                tracker_epoch=f"fixture-epoch-{index:02d}",
                associations=associations,
                expected_identity_switches=switches,
                expected_fragments=fragments,
                expected_outcome=outcome,
            )
        )
    return fixtures


def generated_geometry_fixtures() -> list[GeometryFixtureV1]:
    return [
        GeometryFixtureV1(
            case_id="geometry-line-forward",
            scenario="line-forward",
            geometry_kind="line",
            trajectory=[PointV1(x=0.2, y=0.4), PointV1(x=0.2, y=0.6)],
            expected_events=["line-crossing-forward"],
            expected_outcome="pass",
        ),
        GeometryFixtureV1(
            case_id="geometry-line-reverse",
            scenario="line-reverse",
            geometry_kind="line",
            trajectory=[PointV1(x=0.2, y=0.6), PointV1(x=0.2, y=0.4)],
            expected_events=["line-crossing-reverse"],
            expected_outcome="pass",
        ),
        GeometryFixtureV1(
            case_id="geometry-line-touch",
            scenario="touch-without-cross",
            geometry_kind="line",
            trajectory=[PointV1(x=0.2, y=0.4), PointV1(x=0.2, y=0.5)],
            expected_outcome="pass",
        ),
        GeometryFixtureV1(
            case_id="geometry-boundary-jitter",
            scenario="boundary-jitter",
            geometry_kind="line",
            trajectory=[
                PointV1(x=0.2, y=0.499),
                PointV1(x=0.2, y=0.501),
                PointV1(x=0.2, y=0.499),
            ],
            expected_events=["line-crossing-forward"],
            expected_outcome="pass",
        ),
        GeometryFixtureV1(
            case_id="geometry-zone-enter",
            scenario="zone-enter",
            geometry_kind="zone",
            trajectory=[PointV1(x=0.1, y=0.1), PointV1(x=0.5, y=0.5)],
            expected_events=["zone-entry"],
            expected_outcome="pass",
        ),
        GeometryFixtureV1(
            case_id="geometry-zone-exit",
            scenario="zone-exit",
            geometry_kind="zone",
            trajectory=[PointV1(x=0.5, y=0.5), PointV1(x=0.1, y=0.1)],
            expected_events=["zone-exit"],
            expected_outcome="pass",
        ),
        GeometryFixtureV1(
            case_id="geometry-zone-occupancy",
            scenario="zone-occupancy",
            geometry_kind="zone",
            trajectory=[PointV1(x=0.5, y=0.5)],
            expected_events=["zone-occupancy"],
            expected_outcome="pass",
        ),
        GeometryFixtureV1(
            case_id="geometry-zone-dwell",
            scenario="dwell-threshold",
            geometry_kind="zone",
            trajectory=[PointV1(x=0.5, y=0.5), PointV1(x=0.51, y=0.5)],
            expected_events=["zone-dwell"],
            expected_outcome="pass",
        ),
        GeometryFixtureV1(
            case_id="geometry-schedule-inactive",
            scenario="schedule-inactive",
            geometry_kind="schedule",
            trajectory=[PointV1(x=0.5, y=0.5)],
            expected_outcome="inactive",
        ),
        GeometryFixtureV1(
            case_id="geometry-duplicate-late",
            scenario="duplicate-and-late-input",
            geometry_kind="ordering",
            trajectory=[PointV1(x=0.4, y=0.4), PointV1(x=0.6, y=0.6)],
            expected_events=["zone-entry"],
            duplicate_input_count=1,
            late_input_count=1,
            expected_outcome="reject",
        ),
    ]


def generated_plate_fixtures() -> list[SyntheticPlateFixtureV1]:
    region = NormalizedBoundingBox(x=0.25, y=0.4, width=0.5, height=0.2)
    return [
        SyntheticPlateFixtureV1(
            case_id="plate-latin-exact",
            scenario="exact-normalized-match",
            script="Latin",
            truth_text="GJ01AB1234",
            alternatives=[PlateAlternativeV1(text="GJ01AB1234", confidence=0.99)],
            abstained=False,
            valid_format=True,
            region_bbox=region,
            expected_outcome="exact",
        ),
        SyntheticPlateFixtureV1(
            case_id="plate-devanagari-alternative",
            scenario="ranked-alternative",
            script="Devanagari",
            truth_text="\u0917\u0941\u091c\u0930\u093e\u0924\u0967\u0968\u0969",
            alternatives=[
                PlateAlternativeV1(
                    text="\u0917\u0941\u091c\u0930\u093e\u0924\u0967\u0968\u096a",
                    confidence=0.7,
                ),
                PlateAlternativeV1(
                    text="\u0917\u0941\u091c\u0930\u093e\u0924\u0967\u0968\u0969",
                    confidence=0.25,
                ),
            ],
            abstained=False,
            valid_format=True,
            region_bbox=region,
            expected_outcome="alternative",
        ),
        SyntheticPlateFixtureV1(
            case_id="plate-gujarati-exact",
            scenario="exact-script-match",
            script="Gujarati",
            truth_text="\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ae7\u0ae8\u0ae9",
            alternatives=[
                PlateAlternativeV1(
                    text="\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ae7\u0ae8\u0ae9",
                    confidence=0.91,
                )
            ],
            abstained=False,
            valid_format=True,
            region_bbox=region,
            expected_outcome="exact",
        ),
        SyntheticPlateFixtureV1(
            case_id="plate-abstention",
            scenario="low-confidence-abstention",
            script="Latin",
            truth_text="GJ05ZZ0001",
            abstained=True,
            valid_format=True,
            region_bbox=region,
            expected_outcome="abstain",
        ),
        SyntheticPlateFixtureV1(
            case_id="plate-invalid-format",
            scenario="invalid-format",
            script="Latin",
            truth_text="INVALID",
            alternatives=[PlateAlternativeV1(text="INVALID", confidence=0.9)],
            abstained=False,
            valid_format=False,
            region_bbox=region,
            expected_outcome="reject",
        ),
    ]


def generated_misuse_fixtures() -> list[MisuseFixtureV1]:
    cases = (
        ("path", "path", "local-path-denied"),
        ("source-url", "url", "unapproved-source-url"),
        ("credential", "credential", "credential-field-denied"),
        ("image-bytes", "media", "media-field-denied"),
        ("video", "media", "media-field-denied"),
        ("face-template", "biometric", "biometric-field-denied"),
        ("owner-record", "owner", "owner-field-denied"),
        ("government-data", "government", "government-field-denied"),
        ("watchlist-match", "watchlist", "watchlist-field-denied"),
        ("oversized-payload", "oversized", "payload-too-large"),
        ("manifest-digest", "invalid_digest", "digest-mismatch"),
    )
    return [
        MisuseFixtureV1(
            case_id=f"misuse-{index:02d}",
            prohibited_field=field,
            payload_kind=kind,
            expected_failure_code=failure,
        )
        for index, (field, kind, failure) in enumerate(cases, start=1)
    ]


def generated_fixture_documents(seed: int = FIXTURE_SEED) -> dict[str, object]:
    suites: dict[str, list[EvaluationContractModel]] = {
        "detection-v1.json": generated_detection_fixtures(seed),
        "tracking-v1.json": generated_tracking_fixtures(),
        "geometry-v1.json": generated_geometry_fixtures(),
        "synthetic-plate-v1.json": generated_plate_fixtures(),
        "misuse-v1.json": generated_misuse_fixtures(),
    }
    return {
        name: {
            "contract_type": "hcam.analytics.generated-fixture-suite.v1",
            "suite": name.removesuffix(".json"),
            "seed": seed,
            "generated_only": True,
            "external_inputs": [],
            "records": [record.model_dump(mode="json") for record in records],
        }
        for name, records in suites.items()
    }


def fixture_document_digest(document: object) -> str:
    serialized = json.dumps(
        document,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"
