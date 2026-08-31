from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from hcam.labs.sentinel import LAB_SCHEMA_VERSION


LabMode = Literal["compatibility", "default", "capacity", "low"]


def generated_stream_id(number: int) -> str:
    if not 1 <= number <= 50:
        raise ValueError("Phase 2.5 stream number must be between 1 and 50")
    return f"str_{number:032x}"


def generated_inference_host(number: int) -> tuple[str, int]:
    if number == 4:
        return "rtsp-fault-proxy", 8555
    return "mediamtx", 8554


@dataclass(frozen=True, slots=True)
class GeneratedMediaProfile:
    camera_number: int
    camera_id: str
    profile_id: str
    fixture_name: str
    actual_codec: Literal["h264", "hevc"]
    advertised_codec: Literal["h264", "hevc"] | None
    width: int
    height: int
    fps: float
    bitrate_kbps: int
    crf: int
    gop: int
    hue_degrees: int
    active_by_default: bool
    expected_reachable: bool
    timing_pattern: Literal["cfr", "variable_pts", "loop_boundary"] = "cfr"


_GEOMETRIES = (
    (1280, 720, 25.0),
    (1280, 960, 24.8),
    (1920, 1080, 12.5),
    (1920, 1080, 25.0),
    (1920, 1080, 20.0),
    (2560, 1440, 13.35),
    (1280, 720, 15.0),
    (1920, 1080, 15.0),
)


def generated_media_profiles(
    capacity: int = 50, active_count: int = 30
) -> tuple[GeneratedMediaProfile, ...]:
    if not 1 <= active_count <= capacity <= 50:
        raise ValueError(
            "generated profile bounds must satisfy 1 <= active <= capacity <= 50"
        )
    profiles: list[GeneratedMediaProfile] = []
    for number in range(1, capacity + 1):
        width, height, base_fps = _GEOMETRIES[(number - 1) % len(_GEOMETRIES)]
        actual_codec: Literal["h264", "hevc"] = (
            "hevc" if number % 4 == 0 or number in {5, 6, 8} else "h264"
        )
        if number <= 25:
            advertised_codec: Literal["h264", "hevc"] | None = "h264"
        elif number <= 35:
            advertised_codec = "hevc"
        else:
            advertised_codec = None
        fps = round(base_fps + ((number % 3) * 0.01), 2)
        bitrate = int(
            width * height * fps * (0.055 if actual_codec == "h264" else 0.035) / 1000
        )
        profiles.append(
            GeneratedMediaProfile(
                camera_number=number,
                camera_id=f"C{number:02d}",
                profile_id=f"P{((number - 1) % 8) + 1}-C{number:02d}",
                fixture_name=f"camera-{number:02d}-{actual_codec}-{width}x{height}-{str(fps).replace('.', '_')}.mp4",
                actual_codec=actual_codec,
                advertised_codec=advertised_codec,
                width=width,
                height=height,
                fps=fps,
                bitrate_kbps=max(900, min(bitrate, 12_000)),
                crf=18 + (number % 3),
                gop=max(12, round(fps * (1.5 + (number % 2) * 0.5))),
                hue_degrees=(number * 37) % 360,
                active_by_default=number <= active_count,
                expected_reachable=number not in {9, 31, 44},
                timing_pattern=(
                    "variable_pts"
                    if number == 11
                    else "loop_boundary"
                    if number == 12
                    else "cfr"
                ),
            )
        )
    return tuple(profiles)


def generated_catalog_document(
    *,
    mode: LabMode = "default",
    scenario: str = "base",
    media_host: str = "mediamtx",
) -> dict[str, object]:
    profiles = generated_media_profiles()
    selected = profiles[:12] if mode in {"compatibility", "low"} else profiles
    records: list[dict[str, object]] = []
    for profile in selected:
        live_limit = 50 if mode == "capacity" else 4 if mode == "low" else 30
        live = profile.camera_number <= live_limit
        record: dict[str, object] = {
            "id": profile.camera_id,
            "number": profile.camera_number,
            "name": f"Generated Camera {profile.camera_number:02d}",
            "location": f"Synthetic Zone {((profile.camera_number - 1) % 6) + 1}",
            "codec": profile.advertised_codec or "",
            "live": live,
            "width": profile.width if profile.advertised_codec is not None else 0,
            "height": profile.height if profile.advertised_codec is not None else 0,
            "fps": profile.fps if profile.advertised_codec is not None else 0,
            "bitrate_kbps": profile.bitrate_kbps
            if profile.advertised_codec is not None
            else 0,
            "bits_per_pixel": round(
                profile.bitrate_kbps
                * 1000
                / (profile.width * profile.height * profile.fps),
                5,
            ),
            "rtsp_url": (
                f"rtsp://{generated_inference_host(profile.camera_number)[0]}:"
                f"{generated_inference_host(profile.camera_number)[1]}/hcam/"
                f"{generated_stream_id(profile.camera_number)}"
            ),
            "webrtc_url": f"http://{media_host}:8889/hcam/{generated_stream_id(profile.camera_number)}/whep",
            "hls_live_url": f"http://{media_host}:8888/hcam/{generated_stream_id(profile.camera_number)}/index.m3u8",
            "lab_profile": profile.profile_id,
            "capacity_holder": not live,
        }
        records.append(record)
    if scenario == "reordered":
        records.reverse()
    elif scenario == "empty":
        records = []
    elif scenario == "new" and mode == "compatibility":
        expanded = generated_catalog_document(
            mode="default", scenario="base", media_host=media_host
        )
        records.append(dict(expanded["cameras"][12]))  # type: ignore[index]
    elif scenario == "offline" and records:
        records[0]["live"] = False
    elif scenario == "updated" and records:
        records[0]["name"] = "Generated Camera 01 Updated"
        records[0]["bitrate_kbps"] = 4321
    elif scenario == "missing" and records:
        records = records[1:]
    elif scenario == "duplicate" and records:
        records.append(dict(records[0]))
    elif scenario == "hostile" and records:
        records[0]["rtsp_url"] = "rtsp://user:secret@unapproved.invalid:8554/hcam/c01"
    elif scenario == "malformed" and records:
        records[0]["live"] = "yes"
    elif scenario == "unknown" and records:
        records[0]["vendor_extension"] = {"opaque": True}
    elif scenario == "endpoint" and records:
        records[0]["rtsp_url"] = (
            f"rtsp://{media_host}:8554/hcam/{generated_stream_id(2)}"
        )
    elif scenario == "codec" and records:
        records[0]["codec"] = "hevc"
        records[0]["width"] = 1920
        records[0]["height"] = 1080
    elif scenario != "base":
        raise ValueError("unsupported generated catalogue scenario")
    return {
        "schema": LAB_SCHEMA_VERSION,
        "mode": mode,
        "scenario": scenario,
        "cameras": records,
    }


def write_media_manifest(path: Path, *, active_count: int = 30) -> dict[str, object]:
    profiles = generated_media_profiles(active_count=active_count)
    document = {
        "schema": LAB_SCHEMA_VERSION,
        "classification": "generated-only",
        "active_count": active_count,
        "capacity": len(profiles),
        "profiles": [asdict(profile) for profile in profiles],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    return document
