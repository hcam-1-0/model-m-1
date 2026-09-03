from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


TIER_A_CLASSES = (
    "object.person",
    "vehicle.bicycle",
    "vehicle.car",
    "vehicle.motorcycle",
    "vehicle.bus",
    "vehicle.truck",
    "object.unknown",
)

TrackState = Literal["started", "updated", "lost", "ended"]
TransitionReason = Literal[
    "confirmed",
    "matched",
    "recovered",
    "temporarily_unmatched",
    "lost_timeout",
    "explicit_reset",
    "sequence_gap",
    "sequence_regression",
    "timestamp_regression",
    "configuration_change",
    "source_change",
    "worker_restart",
    "resource_exhausted",
]


class TrackingInputError(ValueError):
    pass


class TrackingResourceError(RuntimeError):
    code = "resource_exhausted"


@dataclass(frozen=True, slots=True)
class TrackingDetection:
    observation_id: str
    class_id: str
    confidence: float
    bbox: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if self.class_id not in TIER_A_CLASSES:
            raise TrackingInputError("tracking detection uses an unapproved class")
        if not 0 <= self.confidence <= 1:
            raise TrackingInputError("tracking confidence must be between zero and one")
        if not self.observation_id.startswith("obs_"):
            raise TrackingInputError("tracking observation identifier is invalid")
        x, y, width, height = self.bbox
        if (
            x < 0
            or y < 0
            or width <= 0
            or height <= 0
            or x + width > 1
            or y + height > 1
        ):
            raise TrackingInputError("tracking box must be normalized and bounded")


@dataclass(frozen=True, slots=True)
class TrackingFrame:
    sequence: int
    observed_at: datetime
    detections: tuple[TrackingDetection, ...]
    reset_before: TransitionReason | None = None

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise TrackingInputError("tracking sequence must be non-negative")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise TrackingInputError("tracking timestamp must be timezone-aware")
        identifiers = [item.observation_id for item in self.detections]
        if len(identifiers) != len(set(identifiers)):
            raise TrackingInputError("tracking frame contains duplicate observations")

    @property
    def digest(self) -> str:
        document = {
            "detections": [
                {
                    "bbox": detection.bbox,
                    "class_id": detection.class_id,
                    "confidence": detection.confidence,
                    "observation_id": detection.observation_id,
                }
                for detection in sorted(
                    self.detections,
                    key=lambda item: (item.class_id, item.observation_id),
                )
            ],
            "observed_at": self.observed_at.isoformat(),
            "reset_before": self.reset_before,
            "sequence": self.sequence,
        }
        payload = json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class GroundTruthObject:
    truth_track_id: str
    class_id: str
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class GeneratedTrackingFrame:
    frame: TrackingFrame
    ground_truth: tuple[GroundTruthObject, ...]


@dataclass(frozen=True, slots=True)
class GeneratedTrackingScenario:
    scenario_id: str
    seed: int
    generator_id: str
    generator_version: str
    frames: tuple[GeneratedTrackingFrame, ...]

    @property
    def digest(self) -> str:
        payload = "\n".join(
            f"{item.frame.digest}:{','.join(sorted(gt.truth_track_id for gt in item.ground_truth))}"
            for item in self.frames
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class TrackerConfiguration:
    high_confidence_threshold: float = 0.25
    low_confidence_floor: float = 0.10
    first_match_cost_limit: float = 0.80
    second_match_cost_limit: float = 0.50
    tentative_match_cost_limit: float = 0.70
    new_track_margin: float = 0.10
    minimum_confirmations: int = 2
    maximum_lost_frames: int = 30
    maximum_gap_ms: int = 3_000
    maximum_detections_per_frame: int = 300
    maximum_tracks_per_class: int = 512

    def __post_init__(self) -> None:
        if not 0 <= self.low_confidence_floor < self.high_confidence_threshold <= 1:
            raise ValueError("tracking confidence thresholds are invalid")
        for value in (
            self.first_match_cost_limit,
            self.second_match_cost_limit,
            self.tentative_match_cost_limit,
        ):
            if not 0 < value <= 1:
                raise ValueError("tracking match threshold must be in (0, 1]")
        if not 1 <= self.minimum_confirmations <= 10:
            raise ValueError("tracking confirmations must be between one and ten")
        if not 1 <= self.maximum_lost_frames <= 300:
            raise ValueError("tracking lost-frame limit must be between one and 300")
        if not 100 <= self.maximum_gap_ms <= 60_000:
            raise ValueError("tracking gap limit must be between 100 and 60000 ms")
        if not 1 <= self.maximum_detections_per_frame <= 300:
            raise ValueError("tracking detection limit must be between one and 300")
        if not 1 <= self.maximum_tracks_per_class <= 512:
            raise ValueError("tracking state limit must be between one and 512")

    @property
    def digest(self) -> str:
        document = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
        }
        payload = json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(payload).hexdigest()}"


@dataclass(frozen=True, slots=True)
class TrackTransition:
    epoch_id: str
    track_id: str
    local_track_number: int
    class_id: str
    state: TrackState
    reason: TransitionReason
    first_observed_at: datetime
    first_sequence: int
    observed_at: datetime
    source_sequence: int
    last_visible_at: datetime
    last_visible_sequence: int
    latest_observation_id: str
    bbox: tuple[float, float, float, float]
    confidence: float
    age_frames: int
    visible_frames: int
    missed_frames: int


@dataclass(frozen=True, slots=True)
class VisibleTrack:
    epoch_id: str
    track_id: str
    class_id: str
    bbox: tuple[float, float, float, float]
    confidence: float


@dataclass(frozen=True, slots=True)
class ClosedEpoch:
    epoch_id: str
    reason: TransitionReason
    ended_at: datetime
    end_sequence: int


@dataclass(frozen=True, slots=True)
class TrackerFrameResult:
    epoch_id: str
    epoch_started: bool
    replayed: bool
    transitions: tuple[TrackTransition, ...]
    visible_tracks: tuple[VisibleTrack, ...]
    closed_epochs: tuple[ClosedEpoch, ...]


@dataclass(frozen=True, slots=True)
class TrackingClassMetric:
    hota: float
    detection_accuracy: float
    association_accuracy: float
    localization_accuracy: float
    idf1: float
    id_precision: float
    id_recall: float
    id_true_positives: int
    id_false_positives: int
    id_false_negatives: int
    identity_switches: int


@dataclass(frozen=True, slots=True)
class TrackingMetricResult(TrackingClassMetric):
    per_class: dict[str, TrackingClassMetric]
