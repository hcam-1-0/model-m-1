#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from hcam.labs.sentinel.accelerators import AcceleratorError, discover_acceleration
from hcam.labs.sentinel.fixtures import generated_media_profiles, write_media_manifest
from hcam.labs.sentinel.faults import (
    FAULT_SCENARIOS,
    FaultRequestError,
    atomic_write_json,
    make_fault_request,
    write_fault_request,
)
from hcam.labs.sentinel.media import (
    MediaFixtureError,
    prepare_media_fixtures,
    remove_media_fixtures,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_COMPOSE = ROOT / "deploy" / "compose.phase2.yaml"
LAB_COMPOSE = ROOT / "deploy" / "compose.phase2-5.yaml"
NVIDIA_COMPOSE = ROOT / "deploy" / "compose.phase2-5.nvidia.yaml"
VAAPI_COMPOSE = ROOT / "deploy" / "compose.phase2-5.vaapi.yaml"
PHASE2_TOOL = ROOT / "tools" / "phase2_lab.py"
DEFAULT_SECRET_ROOT = ROOT / "var" / "phase2-lab-secrets"
DEFAULT_STATE_ROOT = Path(
    os.getenv("HCAM_PHASE2_5_STATE_ROOT", str(ROOT / "var" / "phase2-5"))
).expanduser()


class LabError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _json_request(
    url: str, *, timeout: float = 10
) -> tuple[dict[str, object], dict[str, str]]:
    try:
        with urlopen(
            Request(url, headers={"Accept": "application/json"}), timeout=timeout
        ) as response:
            payload = response.read(1024 * 1024 + 1)
            headers = {key.lower(): value for key, value in response.headers.items()}
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise LabError("lab_http_check_failed") from exc
    if len(payload) > 1024 * 1024:
        raise LabError("lab_http_response_too_large")
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LabError("lab_http_response_invalid") from exc
    if not isinstance(document, dict):
        raise LabError("lab_http_response_invalid")
    return document, headers


def _phase2(
    command: str, secret_root: Path, *, capture: bool = True
) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(PHASE2_TOOL), "--secret-root", str(secret_root), command],
        cwd=ROOT,
        text=True,
        capture_output=capture,
        check=False,
    )
    if completed.returncode != 0:
        raise LabError("phase2_baseline_command_failed")
    if not capture:
        return {"status": "ok"}
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise LabError("phase2_baseline_output_invalid") from exc
    if not isinstance(result, dict):
        raise LabError("phase2_baseline_output_invalid")
    return result


def prepare(secret_root: Path, state_root: Path) -> dict[str, object]:
    baseline = _phase2("prepare", secret_root)
    state_root.mkdir(parents=True, exist_ok=True)
    media_root = state_root / "media"
    media_root.mkdir(parents=True, exist_ok=True)
    manifest = write_media_manifest(state_root / "generated-media-manifest.json")
    return {
        "prepared": True,
        "classification": "generated-only",
        "baseline_secrets": baseline.get("prepared") is True,
        "state_root": str(state_root),
        "media_root": str(media_root),
        "active_count": manifest["active_count"],
        "capacity": manifest["capacity"],
    }


def _secret_environment(secret_root: Path, state_root: Path) -> dict[str, str]:
    required = {
        "HCAM_POSTGRES_PASSWORD_FILE": secret_root / "postgres-password",
        "HCAM_DATABASE_URL_SECRET_FILE": secret_root / "database-url",
        "HCAM_METRICS_TOKEN_SECRET_FILE": secret_root / "metrics-token",
        "HCAM_PLAYBACK_SIGNING_KEY_SECRET_FILE": secret_root
        / "playback-signing-key.pem",
        "HCAM_STREAM_PROBE_TOKEN_SECRET_FILE": secret_root / "probe-token",
    }
    if any(not path.is_file() for path in required.values()):
        raise LabError("lab_secrets_missing")
    corp8 = {
        "HCAM_CORP8_EMAIL_FILE": secret_root / "corp8-email",
        "HCAM_CORP8_PASSWORD_FILE": secret_root / "corp8-password",
    }
    available_corp8 = {name: path.is_file() for name, path in corp8.items()}
    if any(available_corp8.values()) and not all(available_corp8.values()):
        raise LabError("corp8_secrets_incomplete")
    state_root.mkdir(parents=True, exist_ok=True)
    media_root = state_root / "media"
    media_root.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update({name: str(path.resolve()) for name, path in required.items()})
    environment.update(
        {
            "HCAM_PHASE2_5_STATE_DIR": str(state_root.resolve()),
            "HCAM_PHASE2_5_MEDIA_DIR": str(media_root.resolve()),
        }
    )
    if all(available_corp8.values()):
        environment.update({name: str(path.resolve()) for name, path in corp8.items()})
    return environment


def _compose_files(container_gpu: str) -> list[str]:
    files = ["-f", str(BASE_COMPOSE), "-f", str(LAB_COMPOSE)]
    if container_gpu == "nvidia":
        files.extend(["-f", str(NVIDIA_COMPOSE)])
    elif container_gpu == "vaapi":
        files.extend(["-f", str(VAAPI_COMPOSE)])
    elif container_gpu != "none":
        raise LabError("container_gpu_mode_invalid")
    return files


def _compose_profile_args(include_generated_fallback: bool) -> list[str]:
    if include_generated_fallback:
        return ["--profile", "generated-fallback"]
    return []


def compose(
    secret_root: Path,
    state_root: Path,
    container_gpu: str,
    *arguments: str,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = ["docker", "compose", *_compose_files(container_gpu), *arguments]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=_secret_environment(secret_root, state_root),
            text=True,
            capture_output=capture,
            check=False,
        )
    except FileNotFoundError as exc:
        raise LabError("docker_cli_unavailable") from exc
    if completed.returncode != 0:
        raise LabError("docker_compose_failed")
    return completed


def _docker_status() -> dict[str, object]:
    try:
        completed = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise LabError("docker_engine_unavailable") from exc
    if completed.returncode != 0 or not completed.stdout.strip():
        raise LabError("docker_engine_unavailable")
    return {"ready": True, "server_version": completed.stdout.strip()}


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        return probe.connect_ex(("127.0.0.1", port)) != 0


def doctor(
    *,
    accelerator: str,
    ffmpeg: str,
    state_root: Path,
    require_docker: bool,
) -> dict[str, object]:
    acceleration = discover_acceleration(ffmpeg, requested=accelerator)  # type: ignore[arg-type]
    disk = shutil.disk_usage(state_root.parent if state_root.parent.exists() else ROOT)
    minimum_free_bytes = 512 * 1024**2
    if disk.free < minimum_free_bytes:
        raise LabError("insufficient_free_disk")
    docker: dict[str, object]
    try:
        docker = _docker_status()
    except LabError:
        if require_docker:
            raise
        docker = {"ready": False, "server_version": None}
    ports = {str(port): _port_available(port) for port in (8000, 8091, 8888, 8889)}
    return {
        "classification": "generated-only",
        "docker": docker,
        "host_acceleration": acceleration.document(),
        "free_disk_bytes": disk.free,
        "minimum_free_disk_bytes": minimum_free_bytes,
        "ports_available": ports,
        "recommended_execution": "host-prepared",
        "container_gpu_options": ["none", "nvidia", "vaapi"],
        "note": "GPU accelerates fixture encoding; active streams are lossless remuxed.",
    }


def prepare_media(
    *,
    state_root: Path,
    accelerator: str,
    ffmpeg: str,
    parallelism: int | None,
    duration: float,
) -> dict[str, object]:
    report = discover_acceleration(ffmpeg, requested=accelerator)  # type: ignore[arg-type]
    return prepare_media_fixtures(
        generated_media_profiles(),
        state_root / "media",
        report,
        duration_seconds=duration,
        parallelism=parallelism,
        progress=lambda item: print(
            f"prepared {item['camera_id']} with {item['encoder']}", file=sys.stderr
        ),
    )


def media_summary(
    evidence: dict[str, object], *, state_root: Path
) -> dict[str, object]:
    fixtures = evidence.get("fixtures")
    if not isinstance(fixtures, list):
        raise LabError("media_evidence_invalid")
    codecs = sorted(
        {
            str(item.get("codec"))
            for item in fixtures
            if isinstance(item, dict) and item.get("codec")
        }
    )
    geometries = {
        (
            item.get("probe", {}).get("width"),
            item.get("probe", {}).get("height"),
        )
        for item in fixtures
        if isinstance(item, dict) and isinstance(item.get("probe"), dict)
    }
    variable_timing = sum(
        1
        for item in fixtures
        if isinstance(item, dict)
        and isinstance(item.get("source_profile"), dict)
        and item["source_profile"].get("timing_pattern") == "variable_pts"
    )
    return {
        "classification": evidence.get("classification"),
        "fixture_count": evidence.get("fixture_count"),
        "active_default": 30,
        "capacity": 50,
        "codecs": codecs,
        "geometry_count": len(geometries),
        "variable_timing_fixtures": variable_timing,
        "total_bytes": evidence.get("total_bytes"),
        "accelerator": evidence.get("accelerator"),
        "evidence_path": str(
            (state_root / "media" / "fixture-evidence.json").resolve()
        ),
    }


def request_fault(
    *,
    state_root: Path,
    scenario: str,
    camera_id: str | None,
    duration_seconds: float,
) -> dict[str, object]:
    state_root.mkdir(parents=True, exist_ok=True)
    request = make_fault_request(
        scenario,
        camera_id=camera_id,
        duration_seconds=duration_seconds,
    )
    write_fault_request(state_root / "fault-request.json", request)
    result = request.document()
    result["queued"] = True
    result["private_control_path"] = True
    result["host_port_opened"] = False
    result["zero_retention"] = True
    deadline = time.monotonic() + 5
    status_path = state_root / "publisher-fault-status.json"
    while time.monotonic() < deadline:
        if (
            status_path.is_file()
            and not status_path.is_symlink()
            and status_path.stat().st_size <= 16 * 1024
        ):
            try:
                status = json.loads(status_path.read_text(encoding="ascii"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                status = None
            if (
                isinstance(status, dict)
                and status.get("request_id") == request.request_id
            ):
                result["queued"] = False
                result["publisher_status"] = status
                break
        time.sleep(0.1)
    return result


def verify(state_root: Path, dashboard_url: str) -> dict[str, object]:
    status, status_headers = _json_request(
        f"{dashboard_url.rstrip('/')}/api/status", timeout=20
    )
    cameras, _ = _json_request(f"{dashboard_url.rstrip('/')}/api/cameras", timeout=20)
    health, _ = _json_request(f"{dashboard_url.rstrip('/')}/health", timeout=20)
    counts = status.get("counts")
    boundaries = status.get("boundaries")
    media = status.get("media_preparation")
    adapter = status.get("adapter")
    publisher = status.get("publisher")
    classification = status.get("classification")
    if not isinstance(adapter, dict):
        raise LabError("lab_adapter_assertion_failed")
    expected_records = adapter.get("record_count")
    expected_active = adapter.get("active_stream_count")
    catalog_capacity = adapter.get("catalog_capacity")
    adapter_id = adapter.get("adapter_id")
    if (
        not isinstance(expected_records, int)
        or not isinstance(expected_active, int)
        or adapter_id not in {"lab1highadapter", "lab2lowadapter"}
    ):
        raise LabError("lab_adapter_assertion_failed")
    if not isinstance(counts, dict) or not isinstance(cameras.get("items"), list):
        raise LabError("dashboard_inventory_assertion_failed")
    if (
        not isinstance(boundaries, dict)
        or boundaries.get("test_dashboard_only") is not True
    ):
        raise LabError("dashboard_boundary_assertion_failed")
    if (
        boundaries.get("government_data") is not False
        or boundaries.get("recording") is not False
        or boundaries.get("analytics") is not False
    ):
        raise LabError("lab_safety_assertion_failed")
    if health.get("status") != "ok":
        raise LabError("dashboard_health_assertion_failed")
    if status_headers.get("x-hcam-data-classification") != classification:
        raise LabError("data_classification_header_missing")
    if classification == "sentinel-sandbox":
        total = counts.get("total")
        advertised_live = counts.get("advertised_live")
        if (
            not isinstance(total, int)
            or not isinstance(advertised_live, int)
            or not isinstance(catalog_capacity, int)
            or not 1 <= total <= catalog_capacity <= 50
            or not 0 <= advertised_live <= total
            or cameras.get("total") != total
        ):
            raise LabError("sentinel_catalogue_capacity_assertion_failed")
        if publisher is not None or media is not None:
            raise LabError("sentinel_generated_runtime_isolation_failed")
        if boundaries.get("organizer_sandbox") is not True:
            raise LabError("sentinel_sandbox_boundary_assertion_failed")
        serialized_cameras = json.dumps(cameras, sort_keys=True)
        if "rtsp://" in serialized_cameras or "live.corp8.cloud" in serialized_cameras:
            raise LabError("sentinel_locator_redaction_failed")
        config = (ROOT / "deploy" / "mediamtx.phase2-5-sentinel.yml").read_text(
            encoding="utf-8"
        )
        if "record: false" not in config or "rtspTransports: [tcp]" not in config:
            raise LabError("sentinel_relay_safety_assertion_failed")
        return {
            "verified": True,
            "classification": classification,
            "catalogue_records": total,
            "advertised_live": advertised_live,
            "active_adapter": adapter_id,
            "runtime_connection_limit": expected_active,
            "preview_session_limit": adapter.get("preview_session_limit"),
            "quality_policy": adapter.get("quality_policy"),
            "test_dashboard_only": True,
            "recording": False,
            "government_data": False,
            "analytics": False,
        }
    if classification != "generated-only":
        raise LabError("lab_classification_unknown")
    if (
        counts.get("total") != expected_records
        or counts.get("advertised_live") != expected_active
        or cameras.get("total") != expected_records
    ):
        raise LabError("catalogue_capacity_assertion_failed")
    if (
        not isinstance(publisher, dict)
        or publisher.get("adapter_id") != adapter_id
        or publisher.get("active_stream_count") != expected_active
        or publisher.get("quality_downgraded") is not False
    ):
        raise LabError("publisher_adapter_assertion_failed")
    if not isinstance(media, dict) or media.get("fixture_count") != 50:
        raise LabError("media_fixture_assertion_failed")
    config = (ROOT / "deploy" / "mediamtx.phase2-5.yml").read_text(encoding="utf-8")
    if "record: false" not in config or "rtspTransports: [tcp]" not in config:
        raise LabError("media_gateway_safety_assertion_failed")
    return {
        "verified": True,
        "classification": "generated-only",
        "catalogue_records": counts["total"],
        "advertised_live": counts["advertised_live"],
        "active_adapter": adapter_id,
        "runtime_active_streams": publisher["active_stream_count"],
        "quality_downgraded": False,
        "prepared_fixtures": media["fixture_count"],
        "test_dashboard_only": True,
        "recording": False,
        "government_data": False,
        "analytics": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="H-CAM Phase 2.5 generated Sentinel lab"
    )
    parser.add_argument(
        "command",
        choices=(
            "prepare",
            "doctor",
            "prepare-media",
            "config",
            "start",
            "verify",
            "fault",
            "stop",
            "clean-media",
            "all",
        ),
    )
    parser.add_argument("--secret-root", type=Path, default=DEFAULT_SECRET_ROOT)
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE_ROOT)
    parser.add_argument("--dashboard-url", default="http://127.0.0.1:8091")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument(
        "--accelerator",
        choices=("auto", "cpu", "nvidia", "intel", "amd", "vaapi"),
        default="auto",
    )
    parser.add_argument(
        "--container-gpu", choices=("none", "nvidia", "vaapi"), default="none"
    )
    parser.add_argument("--parallelism", type=int)
    parser.add_argument("--fixture-duration", type=float, default=2.0)
    parser.add_argument("--skip-media-prepare", action="store_true")
    parser.add_argument("--prepare-generated-fallback", action="store_true")
    parser.add_argument("--host-only", action="store_true")
    parser.add_argument("--scenario", choices=tuple(FAULT_SCENARIOS))
    parser.add_argument("--camera-id")
    parser.add_argument("--fault-duration", type=float, default=10)
    parser.add_argument("--confirm-generated-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.parallelism is not None and not 1 <= args.parallelism <= 8:
        print("--parallelism must be between 1 and 8", file=sys.stderr)
        return 2
    try:
        if args.command == "prepare":
            result = prepare(args.secret_root, args.state_root)
        elif args.command == "doctor":
            result = doctor(
                accelerator=args.accelerator,
                ffmpeg=args.ffmpeg,
                state_root=args.state_root,
                require_docker=not args.host_only,
            )
        elif args.command == "prepare-media":
            prepare(args.secret_root, args.state_root)
            result = media_summary(
                prepare_media(
                    state_root=args.state_root,
                    accelerator=args.accelerator,
                    ffmpeg=args.ffmpeg,
                    parallelism=args.parallelism,
                    duration=args.fixture_duration,
                ),
                state_root=args.state_root,
            )
        elif args.command == "config":
            prepare(args.secret_root, args.state_root)
            compose(
                args.secret_root,
                args.state_root,
                args.container_gpu,
                *_compose_profile_args(args.prepare_generated_fallback),
                "config",
                "--quiet",
            )
            result = {"config": "valid", "container_gpu": args.container_gpu}
        elif args.command == "start":
            prepare(args.secret_root, args.state_root)
            (args.state_root / "cleanup-request.json").unlink(missing_ok=True)
            if args.prepare_generated_fallback and not args.skip_media_prepare:
                prepare_media(
                    state_root=args.state_root,
                    accelerator=args.accelerator,
                    ffmpeg=args.ffmpeg,
                    parallelism=args.parallelism,
                    duration=args.fixture_duration,
                )
            compose(
                args.secret_root, args.state_root, args.container_gpu, "build", "api"
            )
            compose(
                args.secret_root,
                args.state_root,
                args.container_gpu,
                *_compose_profile_args(args.prepare_generated_fallback),
                "up",
                "--no-build",
                "--wait",
                "--wait-timeout",
                "600",
            )
            result = {"stack": "started", "dashboard": args.dashboard_url}
        elif args.command == "verify":
            result = verify(args.state_root, args.dashboard_url)
        elif args.command == "fault":
            if not args.confirm_generated_only:
                raise LabError("generated_lab_confirmation_required")
            if args.scenario is None:
                raise LabError("fault_scenario_required")
            result = request_fault(
                state_root=args.state_root,
                scenario=args.scenario,
                camera_id=args.camera_id,
                duration_seconds=args.fault_duration,
            )
        elif args.command == "stop":
            cleanup_request = args.state_root / "cleanup-request.json"
            atomic_write_json(
                cleanup_request,
                {"classification": "generated-only", "cleanup": True},
            )
            try:
                compose(
                    args.secret_root,
                    args.state_root,
                    args.container_gpu,
                    "down",
                    "--volumes",
                    "--remove-orphans",
                )
            finally:
                removed = remove_media_fixtures(args.state_root / "media")
                cleanup_request.unlink(missing_ok=True)
            result = {
                "stack": "stopped",
                "media_files_removed": removed,
                "metadata_state_retained": True,
            }
        elif args.command == "clean-media":
            result = {
                "media_files_removed": remove_media_fixtures(args.state_root / "media")
            }
        elif args.command == "all":
            prepare(args.secret_root, args.state_root)
            doctor(
                accelerator=args.accelerator,
                ffmpeg=args.ffmpeg,
                state_root=args.state_root,
                require_docker=True,
            )
            if args.prepare_generated_fallback:
                prepare_media(
                    state_root=args.state_root,
                    accelerator=args.accelerator,
                    ffmpeg=args.ffmpeg,
                    parallelism=args.parallelism,
                    duration=args.fixture_duration,
                )
            try:
                compose(
                    args.secret_root,
                    args.state_root,
                    args.container_gpu,
                    "build",
                    "api",
                )
                compose(
                    args.secret_root,
                    args.state_root,
                    args.container_gpu,
                    "up",
                    "--no-build",
                    "--wait",
                    "--wait-timeout",
                    "600",
                )
                result = verify(args.state_root, args.dashboard_url)
            finally:
                compose(
                    args.secret_root,
                    args.state_root,
                    args.container_gpu,
                    "down",
                    "--volumes",
                    "--remove-orphans",
                )
                if args.prepare_generated_fallback:
                    remove_media_fixtures(args.state_root / "media")
            result["cleanup_complete"] = (
                not args.prepare_generated_fallback
                or not (args.state_root / "media").exists()
            )
        else:
            return 2
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (
        LabError,
        AcceleratorError,
        FaultRequestError,
        MediaFixtureError,
        OSError,
        ValueError,
    ) as exc:
        code = getattr(exc, "code", "phase2_5_lab_failed")
        print(f"Phase 2.5 lab failed ({code})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
