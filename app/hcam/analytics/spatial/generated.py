from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from hcam.analytics.spatial.evaluator import LifecycleInput


GENERATOR_ID = "hcam.p3-4.c10-lifecycle"
GENERATOR_VERSION = "sha256:" + hashlib.sha256(b"hcam.p3-4.c10-lifecycle.v1").hexdigest()


@dataclass(frozen=True, slots=True)
class GeneratedLifecycleScenario:
    scenario_id: str
    seed: int
    generator_id: str
    generator_version: str
    inputs: tuple[LifecycleInput, ...]

    @property
    def digest(self) -> str:
        payload = "\n".join(
            item.digest for item in sorted(self.inputs, key=lambda value: value.source_sequence)
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def build_generated_lifecycle_scenario(
    scenario_id: str,
    *,
    seed: int,
    observed_at: datetime,
    department: str,
    assignment_id: str,
    stream_id: str,
    camera_id: str,
    maximum_dwell_ms: int = 2_000,
    retention_class: str = "derived.analytics.standard",
) -> GeneratedLifecycleScenario:
    randomizer = random.Random(seed)
    jitter = (randomizer.random() - 0.5) * 0.002
    epoch_id = _stable_id("epoch", assignment_id, scenario_id, seed)
    track_a = _stable_id("trk", epoch_id, "a")
    track_b = _stable_id("trk", epoch_id, "b")
    rows: list[tuple[int, float, float, str, str, int]]
    if scenario_id == "c10-line-crossing":
        rows = [(1, 0.30, 0.50, track_a, "updated", 0), (2, 0.70, 0.50, track_a, "updated", 1_000)]
    elif scenario_id == "c10-zone-lifecycle":
        rows = [
            (1, 0.10, 0.50, track_a, "updated", 0),
            (2, 0.50, 0.50, track_a, "updated", 1_000),
            (3, 0.90, 0.50, track_a, "updated", 2_000),
        ]
    elif scenario_id == "c10-dwell":
        rows = [
            (1, 0.50, 0.50, track_a, "updated", 0),
            (2, 0.50, 0.50, track_a, "updated", maximum_dwell_ms),
            (3, 0.50, 0.50, track_a, "updated", maximum_dwell_ms + 1_000),
        ]
    elif scenario_id == "c10-occupancy":
        rows = [
            (1, 0.50, 0.50, track_a, "updated", 0),
            (2, 0.60, 0.50, track_b, "updated", 1_000),
            (3, 0.60, 0.50, track_b, "ended", 2_000),
            (4, 0.50, 0.50, track_a, "ended", 3_000),
        ]
    elif scenario_id == "c10-out-of-order":
        rows = [
            (3, 0.70, 0.50, track_a, "updated", 3_000),
            (1, 0.30, 0.50, track_a, "updated", 0),
            (2, 0.40, 0.50, track_a, "updated", 1_000),
            (4, 0.70, 0.50, track_a, "updated", 4_000),
        ]
    else:
        raise ValueError("unsupported generated geometry scenario")
    inputs = tuple(
        _input(
            sequence,
            x + jitter,
            y,
            track_id,
            state,
            observed_at + timedelta(milliseconds=offset_ms),
            department=department,
            assignment_id=assignment_id,
            stream_id=stream_id,
            camera_id=camera_id,
            epoch_id=epoch_id,
            retention_class=retention_class,
        )
        for sequence, x, y, track_id, state, offset_ms in rows
    )
    return GeneratedLifecycleScenario(
        scenario_id=scenario_id,
        seed=seed,
        generator_id=GENERATOR_ID,
        generator_version=GENERATOR_VERSION,
        inputs=inputs,
    )


def _input(
    sequence: int,
    x: float,
    y: float,
    track_id: str,
    state: str,
    observed_at: datetime,
    *,
    department: str,
    assignment_id: str,
    stream_id: str,
    camera_id: str,
    epoch_id: str,
    retention_class: str,
) -> LifecycleInput:
    return LifecycleInput(
        lifecycle_id=_stable_id("lfc", epoch_id, sequence, track_id),
        department=department,
        assignment_id=assignment_id,
        stream_id=stream_id,
        camera_id=camera_id,
        epoch_id=epoch_id,
        track_id=track_id,
        class_id="vehicle.car",
        state=state,
        reason="lost_timeout" if state == "ended" else "matched",
        observed_at=observed_at,
        source_sequence=sequence,
        latest_observation_id=_stable_id("obs", epoch_id, sequence, track_id),
        bbox=(x - 0.01, y - 0.02, 0.02, 0.02),
        confidence=0.90,
        lineage={
            "execution_scope": "generated_only",
            "generator_id": GENERATOR_ID,
            "generator_version": GENERATOR_VERSION,
        },
        retention_class=retention_class,
    )


def _stable_id(prefix: str, *parts: object) -> str:
    payload = "\x00".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(payload).hexdigest()[:32]}"
