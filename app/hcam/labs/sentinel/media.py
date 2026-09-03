from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from time import monotonic

from hcam.labs.sentinel.accelerators import (
    AcceleratorReport,
    EncoderSelection,
    encoder_quality_arguments,
)
from hcam.labs.sentinel.fixtures import GeneratedMediaProfile
from hcam.labs.sentinel.timing import analyze_fixture_timing


class MediaFixtureError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


MEDIA_GENERATOR_VERSION = "hcam.phase2_5.media.v3"


def default_font_file() -> Path | None:
    candidates = (
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "arial.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    )
    return next((path for path in candidates if path.is_file()), None)


def fixture_command(
    ffmpeg: str,
    profile: GeneratedMediaProfile,
    output: Path,
    selection: EncoderSelection,
    *,
    duration_seconds: float = 2.0,
    font_file: Path | None = None,
) -> list[str]:
    if not 0.1 <= duration_seconds <= 30:
        raise ValueError("fixture duration must be between 0.1 and 30 seconds")
    label = f"HCAM GENERATED {profile.camera_id} | {profile.profile_id} | FRAME %{{n}}"
    selected_font = font_file or default_font_file()
    base_filters = (
        f"testsrc2=size={profile.width}x{profile.height}:rate={profile.fps},"
        f"hue=h={profile.hue_degrees},drawgrid=w=96:h=96:t=2:c=white@0.25"
    )
    if selected_font is not None:
        escaped_font = selected_font.as_posix().replace(":", r"\:").replace("'", r"\'")
        drawtext = (
            f"drawtext=fontfile='{escaped_font}':text='{label}':x=32:y=32:"
            "fontsize=30:fontcolor=white:box=1:boxcolor=black@0.70:boxborderw=12"
        )
        filters = f"{base_filters},{drawtext}"
    else:
        filters = base_filters
    if profile.timing_pattern == "variable_pts":
        filters = rf"{filters},select='not(eq(mod(n\,5)\,0))',setpts=PTS-STARTPTS"
    command = [
        ffmpeg,
        "-nostdin",
        "-v",
        "error",
    ]
    if selection.encoder.endswith("_vaapi"):
        command.extend(["-vaapi_device", "/dev/dri/renderD128"])
    command.extend(
        [
            "-f",
            "lavfi",
            "-i",
            filters,
            "-t",
            str(duration_seconds),
            "-an",
        ]
    )
    command.extend(
        encoder_quality_arguments(
            selection,
            crf=profile.crf,
            bitrate_kbps=profile.bitrate_kbps,
        )
    )
    if profile.actual_codec == "h264":
        command.extend(["-bf", "0"])
    command.extend(
        [
            "-g",
            str(profile.gop),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
        ]
    )
    if profile.actual_codec == "hevc":
        command.extend(["-tag:v", "hvc1"])
    if profile.timing_pattern == "variable_pts":
        command.extend(["-fps_mode", "vfr"])
    command.extend(["-f", "mp4", "-y", str(output)])
    return command


def _run_fixture(
    report: AcceleratorReport,
    profile: GeneratedMediaProfile,
    output_dir: Path,
    *,
    duration_seconds: float,
    font_file: Path | None,
) -> dict[str, object]:
    destination = output_dir / profile.fixture_name
    temporary = destination.with_suffix(destination.suffix + ".partial")
    selection = report.h264 if profile.actual_codec == "h264" else report.hevc
    started = monotonic()
    try:
        completed = subprocess.run(
            fixture_command(
                report.ffmpeg,
                profile,
                temporary,
                selection,
                duration_seconds=duration_seconds,
                font_file=font_file,
            ),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=max(60, duration_seconds * 20),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        temporary.unlink(missing_ok=True)
        raise MediaFixtureError("fixture_encoder_failed") from exc
    if (
        completed.returncode != 0
        or not temporary.is_file()
        or temporary.stat().st_size == 0
    ):
        temporary.unlink(missing_ok=True)
        raise MediaFixtureError("fixture_encoder_failed")
    os.replace(temporary, destination)
    return {
        "camera_id": profile.camera_id,
        "profile_id": profile.profile_id,
        "fixture_name": profile.fixture_name,
        "codec": profile.actual_codec,
        "encoder": selection.encoder,
        "bytes": destination.stat().st_size,
        "duration_ms": round((monotonic() - started) * 1000),
        "source_profile": asdict(profile),
    }


def _frame_rate(value: object) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        if "/" in value:
            numerator, denominator = value.split("/", 1)
            return float(numerator) / float(denominator)
        return float(value)
    except (ValueError, ZeroDivisionError):
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe_media_fixture(
    profile: GeneratedMediaProfile,
    path: Path,
    *,
    ffprobe: str,
    expected_duration: float,
) -> dict[str, object]:
    try:
        completed = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name,width,height,avg_frame_rate,has_b_frames:format=duration",
                "-of",
                "json",
                str(path),
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaFixtureError("fixture_probe_failed") from exc
    try:
        document = json.loads(completed.stdout)
        stream = document["streams"][0]
        duration = float(document["format"]["duration"])
        codec = stream["codec_name"]
        width = int(stream["width"])
        height = int(stream["height"])
        fps = _frame_rate(stream.get("avg_frame_rate"))
        has_b_frames = int(stream["has_b_frames"])
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
    ) as exc:
        raise MediaFixtureError("fixture_probe_invalid") from exc
    if completed.returncode != 0:
        raise MediaFixtureError("fixture_probe_failed")
    if (
        codec != profile.actual_codec
        or width != profile.width
        or height != profile.height
    ):
        raise MediaFixtureError("fixture_media_mismatch")
    if profile.actual_codec == "h264" and has_b_frames != 0:
        raise MediaFixtureError("fixture_h264_b_frames_present")
    timing = analyze_fixture_timing(path, ffprobe=ffprobe)
    if not timing["monotonic"]:
        raise MediaFixtureError("fixture_non_monotonic_timestamps")
    if profile.timing_pattern == "variable_pts":
        if (
            timing["unique_delta_count"] < 2
            or timing["max_delta"] < timing["min_delta"] * 1.5
        ):
            raise MediaFixtureError("fixture_variable_timing_missing")
    elif fps is None or abs(fps - profile.fps) > 0.2:
        raise MediaFixtureError("fixture_frame_rate_mismatch")
    if duration < expected_duration * 0.8 or duration > expected_duration + 1:
        raise MediaFixtureError("fixture_duration_mismatch")
    return {
        "codec": codec,
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "has_b_frames": has_b_frames,
        "duration_seconds": round(duration, 3),
        "sha256": _sha256(path),
        "timing": timing,
    }


def prepare_media_fixtures(
    profiles: Iterable[GeneratedMediaProfile],
    output_dir: Path,
    report: AcceleratorReport,
    *,
    duration_seconds: float = 2.0,
    parallelism: int | None = None,
    reuse_existing: bool = True,
    font_file: Path | None = None,
    progress: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    selected = tuple(profiles)
    if not selected or len(selected) > 50:
        raise ValueError("fixture preparation requires between 1 and 50 profiles")
    output_dir.mkdir(parents=True, exist_ok=True)
    workers = parallelism or (
        4
        if report.h264.hardware or report.hevc.hardware
        else max(1, min(2, report.cpu_count // 2))
    )
    if not 1 <= workers <= 8:
        raise ValueError("parallelism must be between 1 and 8")
    prepared: list[dict[str, object]] = []
    pending: list[GeneratedMediaProfile] = []
    prior_profiles: dict[str, object] = {}
    prior_evidence: dict[str, object] | None = None
    evidence_path = output_dir / "fixture-evidence.json"
    prior_generator_version: str | None = None
    if (
        reuse_existing
        and evidence_path.is_file()
        and evidence_path.stat().st_size <= 4 * 1024 * 1024
    ):
        try:
            prior = json.loads(evidence_path.read_text(encoding="ascii"))
            if not isinstance(prior, dict):
                raise AttributeError
            prior_evidence = prior
            prior_generator_version = prior.get("generator_version")
            prior_profiles = {
                str(item["camera_id"]): item.get("source_profile")
                for item in prior.get("fixtures", [])
                if isinstance(item, dict) and "camera_id" in item
            }
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            prior_profiles = {}
            prior_evidence = None
    for profile in selected:
        destination = output_dir / profile.fixture_name
        if (
            reuse_existing
            and destination.is_file()
            and destination.stat().st_size > 0
            and prior_generator_version == MEDIA_GENERATOR_VERSION
            and prior_profiles.get(profile.camera_id) == asdict(profile)
        ):
            prepared.append(
                {
                    "camera_id": profile.camera_id,
                    "profile_id": profile.profile_id,
                    "fixture_name": profile.fixture_name,
                    "codec": profile.actual_codec,
                    "encoder": "existing",
                    "bytes": destination.stat().st_size,
                    "duration_ms": 0,
                    "source_profile": asdict(profile),
                }
            )
        else:
            pending.append(profile)
    regenerated_count = len(pending)
    reused_count = len(prepared)
    with ThreadPoolExecutor(
        max_workers=workers, thread_name_prefix="p25-fixture"
    ) as executor:
        futures = {
            executor.submit(
                _run_fixture,
                report,
                profile,
                output_dir,
                duration_seconds=duration_seconds,
                font_file=font_file,
            ): profile
            for profile in pending
        }
        try:
            for future in as_completed(futures):
                item = future.result()
                prepared.append(item)
                if progress is not None:
                    progress(item)
        except Exception:
            for future in futures:
                future.cancel()
            raise
    prepared.sort(key=lambda item: str(item["camera_id"]))
    probe_binary = shutil.which("ffprobe")
    if probe_binary is None:
        sibling = Path(report.ffmpeg).with_name(
            "ffprobe.exe" if os.name == "nt" else "ffprobe"
        )
        probe_binary = str(sibling) if sibling.is_file() else None
    if probe_binary is None:
        raise MediaFixtureError("ffprobe_unavailable")
    profile_by_camera = {profile.camera_id: profile for profile in selected}
    for item in prepared:
        profile = profile_by_camera[str(item["camera_id"])]
        item["probe"] = probe_media_fixture(
            profile,
            output_dir / profile.fixture_name,
            ffprobe=probe_binary,
            expected_duration=duration_seconds,
        )
    encoding_accelerator = report.document()
    if regenerated_count == 0 and prior_evidence is not None:
        prior_accelerator = prior_evidence.get("accelerator")
        if isinstance(prior_accelerator, dict):
            encoding_accelerator = prior_accelerator
    evidence = {
        "classification": "generated-only",
        "generator_version": MEDIA_GENERATOR_VERSION,
        "accelerator": encoding_accelerator,
        "validation_accelerator": report.document(),
        "fixture_count": len(prepared),
        "regenerated_fixture_count": regenerated_count,
        "reused_fixture_count": reused_count,
        "parallelism": workers,
        "duration_seconds": duration_seconds,
        "total_bytes": sum(int(item["bytes"]) for item in prepared),
        "fixtures": prepared,
    }
    (output_dir / "fixture-evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    expected_files = {profile.fixture_name for profile in selected}
    for stale in output_dir.glob("*.mp4"):
        if stale.name not in expected_files:
            stale.unlink()
    return evidence


def remove_media_fixtures(output_dir: Path) -> int:
    if not output_dir.exists():
        return 0
    removed = 0
    for path in output_dir.iterdir():
        if path.is_file() and (
            path.suffix in {".mp4", ".partial"} or path.name == "fixture-evidence.json"
        ):
            path.unlink()
            removed += 1
    try:
        output_dir.rmdir()
    except OSError:
        pass
    return removed
