from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
from dataclasses import dataclass
from pathlib import Path


class TimingEvidenceError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise TimingEvidenceError("packet_timestamps_missing")
    ordered = sorted(values)
    position = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[position]


def analyze_fixture_timing(
    path: Path,
    *,
    ffprobe: str = "ffprobe",
    max_output_bytes: int = 4 * 1024 * 1024,
) -> dict[str, object]:
    try:
        completed = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_frames",
                "-show_entries",
                "frame=best_effort_timestamp_time,key_frame",
                "-of",
                "json",
                str(path),
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TimingEvidenceError("timing_probe_failed") from exc
    if completed.returncode != 0 or len(completed.stdout) > max_output_bytes:
        raise TimingEvidenceError("timing_probe_failed")
    try:
        document = json.loads(completed.stdout)
        frames = document["frames"]
        points = [
            float(frame["best_effort_timestamp_time"])
            for frame in frames
            if "best_effort_timestamp_time" in frame
        ]
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise TimingEvidenceError("timing_probe_invalid") from exc
    if len(points) < 2:
        raise TimingEvidenceError("packet_timestamps_missing")
    deltas = [
        later - earlier for earlier, later in zip(points, points[1:], strict=False)
    ]
    positive = all(delta > 0 for delta in deltas)
    keyframes = sum(
        1 for frame in frames if isinstance(frame, dict) and frame.get("key_frame") == 1
    )
    return {
        "frame_count": len(points),
        "pts_start": round(points[0], 6),
        "pts_end": round(points[-1], 6),
        "monotonic": positive,
        "min_delta": round(min(deltas), 6),
        "max_delta": round(max(deltas), 6),
        "median_delta": round(statistics.median(deltas), 6),
        "p95_delta": round(_percentile(deltas, 0.95), 6),
        "unique_delta_count": len({round(delta, 6) for delta in deltas}),
        "keyframe_count": keyframes,
        "uses_pts_not_arrival_time": True,
        "retained_frames": 0,
    }


@dataclass(slots=True)
class ConnectionEpochState:
    stream_key: str
    connection_epoch: int = 0
    discontinuity_epoch: int = 0
    retry_attempt: int = 0
    connected: bool = False

    def on_connected(self) -> None:
        self.connection_epoch += 1
        self.retry_attempt = 0
        self.connected = True

    def on_disconnected(self) -> None:
        self.connected = False

    def on_discontinuity(self) -> None:
        self.discontinuity_epoch += 1

    def next_retry_delay(
        self, *, base_seconds: float = 1, ceiling_seconds: float = 30
    ) -> float:
        if base_seconds <= 0 or ceiling_seconds < base_seconds:
            raise ValueError("invalid retry bounds")
        self.retry_attempt += 1
        exponential = min(
            ceiling_seconds, base_seconds * (2 ** (self.retry_attempt - 1))
        )
        seed = hashlib.sha256(
            f"{self.stream_key}:{self.retry_attempt}".encode("utf-8")
        ).digest()
        jitter = int.from_bytes(seed[:2], "big") / 65535 * min(1.0, exponential * 0.2)
        return round(min(ceiling_seconds, exponential + jitter), 3)


def classify_loop(points: list[float]) -> dict[str, object]:
    if len(points) < 2:
        raise TimingEvidenceError("packet_timestamps_missing")
    discontinuities = sum(
        1
        for earlier, later in zip(points, points[1:], strict=False)
        if later <= earlier
    )
    return {
        "discontinuity_epochs": discontinuities,
        "cross_epoch_state_allowed": False,
        "monotonic_within_epoch_required": True,
    }


FAULT_SCENARIOS: dict[str, dict[str, object]] = {
    "F1": {"name": "startup_gop_burst", "max_cameras": 1, "clock": "pts"},
    "F2": {"name": "delayed_keyframe", "max_cameras": 1, "grace_required": True},
    "F3": {"name": "variable_pts", "max_cameras": 1, "rewrite_timestamps": False},
    "F4": {"name": "supervised_restart", "max_cameras": 1, "bounded_retry": True},
    "F5": {
        "name": "hard_loop_discontinuity",
        "max_cameras": 1,
        "invalidate_state": True,
    },
    "F6": {
        "name": "rtsp_failure_hls_fallback",
        "max_cameras": 1,
        "inference_stays_failed": True,
    },
    "F7": {
        "name": "catalog_live_transport_offline",
        "max_cameras": 1,
        "states_separate": True,
    },
}
