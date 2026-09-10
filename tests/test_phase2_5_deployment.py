from __future__ import annotations

from pathlib import Path

from tools.phase2_5_lab import (
    _compose_files,
    _compose_profile_args,
    build_parser,
    media_summary,
)


ROOT = Path(__file__).resolve().parents[1]


def test_phase2_5_compose_is_additive_loopback_only_and_no_recording() -> None:
    compose = (ROOT / "deploy" / "compose.phase2-5.yaml").read_text(encoding="utf-8")
    mediamtx = (ROOT / "deploy" / "mediamtx.phase2-5.yml").read_text(encoding="utf-8")
    sentinel_mediamtx = (
        ROOT / "deploy" / "mediamtx.phase2-5-sentinel.yml"
    ).read_text(encoding="utf-8")

    assert "127.0.0.1:${HCAM_PHASE2_5_DASHBOARD_PORT:-8091}:8091" in compose
    assert "127.0.0.1:${HCAM_WHEP_PORT:-8889}:8889" in compose
    assert "127.0.0.1:${HCAM_WEBRTC_UDP_PORT:-8189}:8189/udp" in compose
    assert "127.0.0.1:${HCAM_WEBRTC_TCP_PORT:-8190}:8190/tcp" in compose
    assert "127.0.0.1:${HCAM_SENTINEL_WHEP_PORT:-8890}:8889" in compose
    assert "127.0.0.1:${HCAM_SENTINEL_WEBRTC_UDP_PORT:-8191}:8191/udp" in compose
    assert "127.0.0.1:${HCAM_SENTINEL_WEBRTC_TCP_PORT:-8192}:8192/tcp" in compose
    assert "8090:8090" not in compose
    assert "8554:8554" not in compose
    assert "8555:8555" not in compose
    assert "rtsp-fault-proxy:" in compose
    assert "hcam.labs.sentinel.fault_proxy" in compose
    assert "record: false" in mediamtx
    assert "record: false" in sentinel_mediamtx
    assert "rtspTransports: [tcp]" in sentinel_mediamtx
    assert "webrtcLocalUDPAddress: :8191" in sentinel_mediamtx
    assert "webrtcLocalTCPAddress: :8192" in sentinel_mediamtx
    assert "authMethod: internal" in sentinel_mediamtx
    assert 'path: "~^hcam-sentinel/[0-9a-f]{32}$"' in sentinel_mediamtx
    assert ":9997" not in "\n".join(
        line
        for line in compose.splitlines()
        if line.strip().startswith("- 127.0.0.1:")
    )
    assert "rtspTransports: [tcp]" in mediamtx
    assert "webrtc: true" in mediamtx
    assert "webrtcLocalTCPAddress: :8190" in mediamtx
    assert "hcam.labs.sentinel" in compose
    assert "postgis/postgis:18-3.6-alpine@sha256:" in compose
    assert "pg_isready -h 127.0.0.1" in compose
    assert "active-lab-adapter.json" in compose
    assert "publisher-state.json" in compose
    assert "cleanup-request.json" not in compose
    assert "start_period: 240s" in compose
    assert 'HCAM_PHASE2_5_REQUIRE_PUBLISHER_STATE: "false"' in compose
    assert "HCAM_PHASE2_5_CATALOG_MODE: sentinel-online" in compose
    assert "https://live.corp8.cloud/api/ingest" in compose
    assert "hcam.labs.sentinel.standby" in compose
    assert "hcam.labs.sentinel.publisher" not in compose


def test_phase2_5_overlay_reuses_the_postgis_phase2_baseline() -> None:
    phase2 = (ROOT / "deploy" / "compose.phase2.yaml").read_text(encoding="utf-8")
    overlay = (ROOT / "deploy" / "compose.phase2-5.yaml").read_text(encoding="utf-8")

    assert "postgis/postgis:18-3.6-alpine@sha256:" in phase2
    assert "SELECT PostGIS_Version()" in phase2
    assert "postgis/postgis:18-3.6-alpine@sha256:" in overlay


def test_gpu_overlays_are_opt_in_and_cpu_compose_has_no_device_request() -> None:
    base = (ROOT / "deploy" / "compose.phase2-5.yaml").read_text(encoding="utf-8")
    nvidia = (ROOT / "deploy" / "compose.phase2-5.nvidia.yaml").read_text(
        encoding="utf-8"
    )
    vaapi = (ROOT / "deploy" / "compose.phase2-5.vaapi.yaml").read_text(
        encoding="utf-8"
    )

    assert "gpus:" not in base
    assert "devices:" not in base
    assert "gpus: all" in nvidia
    assert "NVIDIA_DRIVER_CAPABILITIES: compute,video,utility" in nvidia
    assert "/dev/dri:/dev/dri" in vaapi
    assert _compose_files("none")[-1].endswith("compose.phase2-5.yaml")
    assert _compose_files("nvidia")[-1].endswith("compose.phase2-5.nvidia.yaml")
    assert _compose_files("vaapi")[-1].endswith("compose.phase2-5.vaapi.yaml")


def test_generated_fallback_compose_profile_is_explicit() -> None:
    assert _compose_profile_args(False) == []
    assert _compose_profile_args(True) == ["--profile", "generated-fallback"]


def test_product_application_does_not_import_phase2_5_lab() -> None:
    product_sources = [
        ROOT / "app" / "hcam" / "main.py",
        ROOT / "app" / "hcam" / "cli.py",
        *sorted((ROOT / "app" / "hcam" / "camera_registry").glob("*.py")),
        *sorted((ROOT / "app" / "hcam" / "streams").glob("*.py")),
        *sorted((ROOT / "app" / "hcam" / "analytics").glob("*.py")),
    ]

    assert all(
        "hcam.labs" not in path.read_text(encoding="utf-8") for path in product_sources
    )


def test_teammate_runner_exposes_portable_acceleration_modes() -> None:
    parser = build_parser()
    cpu = parser.parse_args(["doctor", "--host-only", "--accelerator", "cpu"])
    nvidia = parser.parse_args(["config", "--container-gpu", "nvidia"])

    assert cpu.accelerator == "cpu"
    assert cpu.host_only
    assert nvidia.container_gpu == "nvidia"


def test_runtime_image_includes_ffmpeg_and_portable_font() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "ffmpeg fonts-dejavu-core" in dockerfile


def test_media_summary_is_compact_and_points_to_external_state(tmp_path) -> None:
    result = media_summary(
        {
            "classification": "generated-only",
            "fixture_count": 1,
            "total_bytes": 123,
            "accelerator": {"requested": "cpu"},
            "fixtures": [
                {
                    "codec": "h264",
                    "probe": {"width": 320, "height": 180},
                    "source_profile": {"timing_pattern": "variable_pts"},
                }
            ],
        },
        state_root=tmp_path,
    )

    assert result["fixture_count"] == 1
    assert result["codecs"] == ["h264"]
    assert result["variable_timing_fixtures"] == 1
    assert str(tmp_path.resolve()) in result["evidence_path"]
