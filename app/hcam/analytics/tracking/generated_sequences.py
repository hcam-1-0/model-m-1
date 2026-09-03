from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Callable

from hcam.analytics.tracking.types import (
    GeneratedTrackingFrame,
    GeneratedTrackingScenario,
    GroundTruthObject,
    TIER_A_CLASSES,
    TrackingDetection,
    TrackingFrame,
)


GENERATOR_ID = "DATA-TRK-GEN-R0"
GENERATOR_VERSION = (
    "sha256:59969078d590844ecb19dd82e7bfc4f4446d67aded74112f29216c0e532b981b"
)
GENERATED_TRACKING_SCENARIOS = (
    "single-object",
    "two-crossing",
    "short-occlusion",
    "long-occlusion",
    "all-tier-a",
    "discontinuity",
    "overload",
)


def _identifier(prefix: str, *parts: object) -> str:
    material = "\x00".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(material).hexdigest()[:32]}"


def _box(
    x: float,
    y: float,
    width: float,
    height: float,
) -> tuple[float, float, float, float]:
    return (
        round(max(0.0, min(x, 1.0 - width)), 6),
        round(max(0.0, min(y, 1.0 - height)), 6),
        round(width, 6),
        round(height, 6),
    )


def _detection(
    scenario_id: str,
    seed: int,
    sequence: int,
    object_key: str,
    class_id: str,
    bbox: tuple[float, float, float, float],
    confidence: float = 0.90,
) -> TrackingDetection:
    return TrackingDetection(
        observation_id=_identifier(
            "obs",
            scenario_id,
            seed,
            sequence,
            object_key,
        ),
        class_id=class_id,
        confidence=confidence,
        bbox=bbox,
    )


def _truth(
    object_key: str,
    class_id: str,
    bbox: tuple[float, float, float, float],
) -> GroundTruthObject:
    return GroundTruthObject(
        truth_track_id=f"truth_{object_key}",
        class_id=class_id,
        bbox=bbox,
    )


def _frame(
    *,
    scenario_id: str,
    seed: int,
    base: datetime,
    sequence: int,
    objects: tuple[
        tuple[
            str,
            str,
            tuple[float, float, float, float],
            float,
            bool,
            bool,
        ],
        ...,
    ],
    reset_before=None,
) -> GeneratedTrackingFrame:
    detections = tuple(
        _detection(
            scenario_id,
            seed,
            sequence,
            key,
            class_id,
            bbox,
            confidence,
        )
        for key, class_id, bbox, confidence, detected, _include_truth in objects
        if detected
    )
    ground_truth = tuple(
        _truth(key, class_id, bbox)
        for key, class_id, bbox, _confidence, _detected, include_truth in objects
        if include_truth
    )
    return GeneratedTrackingFrame(
        frame=TrackingFrame(
            sequence=sequence,
            observed_at=base + timedelta(seconds=sequence),
            detections=detections,
            reset_before=reset_before,
        ),
        ground_truth=ground_truth,
    )


def _single(seed: int, base: datetime) -> tuple[GeneratedTrackingFrame, ...]:
    frames = []
    for sequence in range(6):
        bbox = _box(0.10 + sequence * 0.025, 0.20, 0.10, 0.20)
        frames.append(
            _frame(
                scenario_id="single-object",
                seed=seed,
                base=base,
                sequence=sequence,
                objects=(("person-1", "object.person", bbox, 0.95, True, sequence > 0),),
            )
        )
    return tuple(frames)


def _crossing(seed: int, base: datetime) -> tuple[GeneratedTrackingFrame, ...]:
    frames = []
    for sequence in range(16):
        first = _box(0.08 + sequence * 0.04, 0.18, 0.14, 0.18)
        second = _box(0.76 - sequence * 0.04, 0.30, 0.14, 0.18)
        frames.append(
            _frame(
                scenario_id="two-crossing",
                seed=seed,
                base=base,
                sequence=sequence,
                objects=(
                    ("person-left", "object.person", first, 0.93, True, sequence > 0),
                    ("person-right", "object.person", second, 0.91, True, sequence > 0),
                ),
            )
        )
    return tuple(frames)


def _short_occlusion(
    seed: int,
    base: datetime,
) -> tuple[GeneratedTrackingFrame, ...]:
    frames = []
    for sequence in range(8):
        bbox = _box(0.12 + sequence * 0.035, 0.55, 0.16, 0.12)
        detected = sequence != 4
        confidence = 0.20 if sequence in {3, 5} else 0.90
        frames.append(
            _frame(
                scenario_id="short-occlusion",
                seed=seed,
                base=base,
                sequence=sequence,
                objects=(
                    (
                        "car-1",
                        "vehicle.car",
                        bbox,
                        confidence,
                        detected,
                        sequence > 0,
                    ),
                ),
            )
        )
    return tuple(frames)


def _long_occlusion(
    seed: int,
    base: datetime,
) -> tuple[GeneratedTrackingFrame, ...]:
    frames = []
    for sequence in range(36):
        bbox = _box(0.15 + min(sequence, 5) * 0.02, 0.35, 0.12, 0.12)
        detected = sequence < 3 or sequence == 35
        include_truth = sequence > 0
        frames.append(
            _frame(
                scenario_id="long-occlusion",
                seed=seed,
                base=base,
                sequence=sequence,
                objects=(
                    (
                        "motorcycle-1",
                        "vehicle.motorcycle",
                        bbox,
                        0.92,
                        detected,
                        include_truth,
                    ),
                ),
            )
        )
    return tuple(frames)


def _all_classes(seed: int, base: datetime) -> tuple[GeneratedTrackingFrame, ...]:
    frames = []
    for sequence in range(5):
        objects = []
        for index, class_id in enumerate(TIER_A_CLASSES):
            row = index // 4
            column = index % 4
            bbox = _box(
                0.04 + column * 0.22 + sequence * 0.006,
                0.10 + row * 0.38,
                0.10,
                0.16,
            )
            objects.append(
                (
                    f"tier-a-{index}",
                    class_id,
                    bbox,
                    0.88 + index * 0.01,
                    True,
                    sequence > 0,
                )
            )
        frames.append(
            _frame(
                scenario_id="all-tier-a",
                seed=seed,
                base=base,
                sequence=sequence,
                objects=tuple(objects),
            )
        )
    return tuple(frames)


def _discontinuity(
    seed: int,
    base: datetime,
) -> tuple[GeneratedTrackingFrame, ...]:
    frames = []
    for sequence in range(6):
        bbox = _box(0.25 + sequence * 0.02, 0.25, 0.12, 0.20)
        object_key = "person-reset-a" if sequence < 3 else "person-reset-b"
        frames.append(
            _frame(
                scenario_id="discontinuity",
                seed=seed,
                base=base,
                sequence=sequence,
                objects=(
                    (
                        object_key,
                        "object.person",
                        bbox,
                        0.94,
                        True,
                        sequence not in {0, 3},
                    ),
                ),
                reset_before="explicit_reset" if sequence == 3 else None,
            )
        )
    return tuple(frames)


def _overload(seed: int, base: datetime) -> tuple[GeneratedTrackingFrame, ...]:
    detections = tuple(
        _detection(
            "overload",
            seed,
            0,
            f"noise-{index}",
            "object.unknown",
            _box((index % 20) * 0.045, (index // 20) * 0.045, 0.03, 0.03),
            0.90,
        )
        for index in range(301)
    )
    return (
        GeneratedTrackingFrame(
            frame=TrackingFrame(
                sequence=0,
                observed_at=base,
                detections=detections,
            ),
            ground_truth=(),
        ),
    )


_BUILDERS: dict[
    str,
    Callable[[int, datetime], tuple[GeneratedTrackingFrame, ...]],
] = {
    "single-object": _single,
    "two-crossing": _crossing,
    "short-occlusion": _short_occlusion,
    "long-occlusion": _long_occlusion,
    "all-tier-a": _all_classes,
    "discontinuity": _discontinuity,
    "overload": _overload,
}


def build_generated_tracking_scenario(
    scenario_id: str,
    seed: int,
    observed_at: datetime,
) -> GeneratedTrackingScenario:
    if scenario_id not in _BUILDERS:
        raise ValueError("generated tracking scenario is not approved")
    if not 0 <= seed <= 4_294_967_295:
        raise ValueError("generated tracking seed is out of range")
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("generated tracking timestamp must be timezone-aware")
    base = observed_at.astimezone(UTC)
    return GeneratedTrackingScenario(
        scenario_id=scenario_id,
        seed=seed,
        generator_id=GENERATOR_ID,
        generator_version=GENERATOR_VERSION,
        frames=_BUILDERS[scenario_id](seed, base),
    )
