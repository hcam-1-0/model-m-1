from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from time import monotonic, sleep, time

from hcam.labs.sentinel.accelerators import AcceleratorError, discover_acceleration
from hcam.labs.sentinel.fixtures import (
    GeneratedMediaProfile,
    generated_media_profiles,
    generated_stream_id,
)
from hcam.labs.sentinel.faults import (
    FaultRequest,
    FaultRequestError,
    atomic_write_json,
    read_fault_request,
)
from hcam.labs.sentinel.media import (
    MediaFixtureError,
    prepare_media_fixtures,
    remove_media_fixtures,
)
from hcam.labs.sentinel.lab_adapters import (
    LabAdapterProfile,
    LabAdapterStateError,
    read_active_lab_adapter,
)
from hcam.labs.sentinel.timing import (
    ConnectionEpochState,
    analyze_fixture_timing,
    classify_loop,
)


@dataclass(slots=True)
class PublisherProcess:
    number: int
    camera_id: str
    command: list[str]
    process: subprocess.Popen[bytes]
    epoch: ConnectionEpochState
    restarts: int = 0
    restart_due_at: float = 0
    paused_until_epoch: float = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="H-CAM Phase 2.5 generated media publisher"
    )
    parser.add_argument("--active-count", type=int, default=30)
    parser.add_argument("--capacity", type=int, default=50)
    parser.add_argument("--base-url", default="rtsp://mediamtx:8554/hcam")
    parser.add_argument(
        "--fixture-dir", type=Path, default=Path("/tmp/hcam-phase2-5-media")
    )
    parser.add_argument("--fixture-duration", type=float, default=2.0)
    parser.add_argument("--parallelism", type=int)
    parser.add_argument(
        "--accelerator",
        choices=("auto", "cpu", "nvidia", "intel", "amd", "vaapi"),
        default=os.getenv("HCAM_LAB_ACCELERATOR", "auto"),
    )
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--heartbeat-file", type=Path)
    parser.add_argument("--fault-request-path", type=Path)
    parser.add_argument("--fault-status-path", type=Path)
    parser.add_argument("--adapter-state-path", type=Path)
    parser.add_argument("--publisher-state-path", type=Path)
    parser.add_argument("--cleanup-request-path", type=Path)
    parser.add_argument("--cleanup-fixtures", action="store_true")
    return parser


def cleanup_requested(path: Path | None) -> bool:
    if path is None:
        return True
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 16 * 1024:
        return False
    try:
        document = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(document, dict)
        and document.get("classification") == "generated-only"
        and document.get("cleanup") is True
    )


def publisher_command(ffmpeg: str, fixture: Path, destination: str) -> list[str]:
    return [
        ffmpeg,
        "-nostdin",
        "-v",
        "error",
        "-re",
        "-stream_loop",
        "-1",
        "-i",
        str(fixture),
        "-map",
        "0:v:0",
        "-an",
        "-c:v",
        "copy",
        "-f",
        "rtsp",
        "-rtsp_transport",
        "tcp",
        destination,
    ]


def _start(
    number: int,
    command: list[str],
    epoch: ConnectionEpochState | None = None,
) -> PublisherProcess:
    state = epoch or ConnectionEpochState(stream_key=f"C{number:02d}")
    state.on_connected()
    return PublisherProcess(
        number=number,
        camera_id=f"C{number:02d}",
        command=command,
        process=subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        epoch=state,
    )


def _stop(publisher: PublisherProcess) -> None:
    if publisher.process.poll() is None:
        publisher.process.terminate()
    try:
        publisher.process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        publisher.process.kill()
        publisher.process.wait(timeout=5)


def reconcile_publishers(
    publishers: list[PublisherProcess],
    *,
    target_count: int,
    profiles: tuple[GeneratedMediaProfile, ...],
    ffmpeg: str,
    fixture_dir: Path,
    base_url: str,
) -> None:
    if not 1 <= target_count <= len(profiles):
        raise ValueError("publisher target is outside generated profile capacity")
    desired = set(range(1, target_count + 1))
    for publisher in tuple(publishers):
        if publisher.number not in desired:
            _stop(publisher)
            publishers.remove(publisher)
    active = {publisher.number for publisher in publishers}
    for profile in profiles[:target_count]:
        if profile.camera_number in active:
            continue
        destination = (
            f"{base_url.rstrip('/')}/{generated_stream_id(profile.camera_number)}"
        )
        command = publisher_command(
            ffmpeg,
            fixture_dir / profile.fixture_name,
            destination,
        )
        publishers.append(_start(profile.camera_number, command))
    publishers.sort(key=lambda item: item.number)


def publisher_state_document(
    adapter: LabAdapterProfile | None,
    publishers: list[PublisherProcess],
) -> dict[str, object]:
    return {
        "classification": "generated-only",
        "adapter_id": adapter.adapter_id if adapter is not None else "fixed",
        "active_stream_count": len(publishers),
        "active_camera_ids": [publisher.camera_id for publisher in publishers],
        "stream_copy": True,
        "quality_downgraded": False,
    }


def apply_fault(
    request: FaultRequest,
    publishers: list[PublisherProcess],
    *,
    fixture_dir: Path,
    profiles_by_camera: dict[str, GeneratedMediaProfile],
) -> dict[str, object]:
    publisher = next(
        (item for item in publishers if item.camera_id == request.camera_id),
        None,
    )
    if publisher is None:
        raise FaultRequestError("fault_camera_not_active")
    profile = profiles_by_camera[request.camera_id]
    evidence: dict[str, object] = {
        "classification": "generated-only",
        "request_id": request.request_id,
        "scenario": request.scenario,
        "camera_id": request.camera_id,
        "status": "applied",
        "zero_retained_media": True,
        "expires_at_epoch": request.expires_at_epoch,
    }
    if request.scenario in {"F1", "F3"}:
        evidence["timing"] = analyze_fixture_timing(fixture_dir / profile.fixture_name)
        evidence["time_basis"] = "pts"
    elif request.scenario == "F2":
        publisher.epoch.on_disconnected()
        if publisher.process.poll() is None:
            publisher.process.terminate()
        grace = min(request.duration_seconds, max(1.0, profile.gop / profile.fps))
        publisher.paused_until_epoch = time() + grace
        evidence["keyframe_grace_seconds"] = round(grace, 3)
        evidence["health_during_grace"] = "connecting"
    elif request.scenario == "F4":
        publisher.epoch.on_disconnected()
        if publisher.process.poll() is None:
            publisher.process.terminate()
        evidence["recovery_scope"] = "single-stream"
        evidence["bounded_retry"] = True
    elif request.scenario == "F5":
        publisher.epoch.on_discontinuity()
        publisher.epoch.on_disconnected()
        if publisher.process.poll() is None:
            publisher.process.terminate()
        evidence["loop_classification"] = classify_loop([0.0, 0.04, 0.08, 0.0, 0.04])
        evidence["transient_state_invalidated"] = True
    elif request.scenario == "F6":
        evidence["inference_transport"] = "blocked-by-private-proxy"
        evidence["preview_transport"] = "hls-direct-mediamtx"
        evidence["hls_fallback_available"] = True
        evidence["inference_stays_failed"] = True
    elif request.scenario == "F7":
        publisher.epoch.on_disconnected()
        if publisher.process.poll() is None:
            publisher.process.terminate()
        publisher.paused_until_epoch = request.expires_at_epoch
        evidence["advertised_live"] = True
        evidence["observed_health"] = "offline"
    evidence["connection_epoch"] = publisher.epoch.connection_epoch
    evidence["discontinuity_epoch"] = publisher.epoch.discontinuity_epoch
    return evidence


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if os.getenv("HCAM_ALLOW_SYNTHETIC_LAB", "").lower() not in {"1", "true"}:
        print("HCAM_ALLOW_SYNTHETIC_LAB=true is required", file=sys.stderr)
        return 2
    if not 1 <= args.active_count <= args.capacity <= 50:
        print(
            "counts must satisfy 1 <= active-count <= capacity <= 50", file=sys.stderr
        )
        return 2
    if args.parallelism is not None and not 1 <= args.parallelism <= 8:
        print("parallelism must be between 1 and 8", file=sys.stderr)
        return 2
    profiles = generated_media_profiles(args.capacity, args.active_count)
    profiles_by_camera = {profile.camera_id: profile for profile in profiles}
    try:
        report = discover_acceleration(
            args.ffmpeg,
            requested=args.accelerator,  # type: ignore[arg-type]
        )
        prepare_media_fixtures(
            profiles,
            args.fixture_dir,
            report,
            duration_seconds=args.fixture_duration,
            parallelism=args.parallelism,
        )
    except (AcceleratorError, MediaFixtureError, OSError, ValueError) as exc:
        code = getattr(exc, "code", "fixture_preparation_failed")
        print(f"Phase 2.5 publisher failed ({code})", file=sys.stderr)
        return 1

    stopping = False
    publishers: list[PublisherProcess] = []
    last_fault_request_id: str | None = None
    fault_evidence: dict[str, object] | None = None
    active_adapter: LabAdapterProfile | None = None
    if args.adapter_state_path is not None:
        try:
            active_adapter = read_active_lab_adapter(args.adapter_state_path)
        except LabAdapterStateError as exc:
            print(f"Phase 2.5 publisher failed ({exc.code})", file=sys.stderr)
            return 1

    def stop_publishers(_signum=None, _frame=None) -> None:
        nonlocal stopping
        stopping = True
        for publisher in publishers:
            if publisher.process.poll() is None:
                publisher.process.terminate()

    signal.signal(signal.SIGTERM, stop_publishers)
    signal.signal(signal.SIGINT, stop_publishers)
    try:
        reconcile_publishers(
            publishers,
            target_count=(
                active_adapter.active_stream_count
                if active_adapter is not None
                else args.active_count
            ),
            profiles=profiles,
            ffmpeg=report.ffmpeg,
            fixture_dir=args.fixture_dir,
            base_url=args.base_url,
        )
        while not stopping:
            now = monotonic()
            now_epoch = time()
            if args.adapter_state_path is not None:
                try:
                    requested_adapter = read_active_lab_adapter(args.adapter_state_path)
                except LabAdapterStateError as exc:
                    print(f"Phase 2.5 publisher failed ({exc.code})", file=sys.stderr)
                    return 1
                if requested_adapter != active_adapter:
                    reconcile_publishers(
                        publishers,
                        target_count=requested_adapter.active_stream_count,
                        profiles=profiles,
                        ffmpeg=report.ffmpeg,
                        fixture_dir=args.fixture_dir,
                        base_url=args.base_url,
                    )
                    active_adapter = requested_adapter
            if args.fault_request_path is not None:
                try:
                    request = read_fault_request(args.fault_request_path)
                    if (
                        request is not None
                        and request.active(now_epoch)
                        and request.request_id != last_fault_request_id
                    ):
                        fault_evidence = apply_fault(
                            request,
                            publishers,
                            fixture_dir=args.fixture_dir,
                            profiles_by_camera=profiles_by_camera,
                        )
                        last_fault_request_id = request.request_id
                    elif (
                        request is not None
                        and request.request_id == last_fault_request_id
                        and not request.active(now_epoch)
                        and fault_evidence is not None
                        and fault_evidence.get("status") == "applied"
                    ):
                        fault_evidence = {
                            **fault_evidence,
                            "status": "expired",
                            "active_fault": False,
                        }
                except FaultRequestError as exc:
                    fault_evidence = {
                        "classification": "generated-only",
                        "status": "rejected",
                        "safe_reason": exc.code,
                    }
            failed_permanently = False
            for publisher in publishers:
                if publisher.process.poll() is None:
                    continue
                if publisher.paused_until_epoch > now_epoch:
                    continue
                publisher.paused_until_epoch = 0
                if publisher.restarts >= 3:
                    failed_permanently = True
                    continue
                if publisher.restart_due_at == 0:
                    publisher.restarts += 1
                    publisher.restart_due_at = now + min(8, 2**publisher.restarts)
                elif now >= publisher.restart_due_at:
                    replacement = _start(
                        publisher.number, publisher.command, publisher.epoch
                    )
                    publisher.process = replacement.process
                    publisher.restart_due_at = 0
            if failed_permanently:
                return 1
            if args.heartbeat_file is not None:
                args.heartbeat_file.touch()
            if args.fault_status_path is not None:
                status = fault_evidence or {
                    "classification": "generated-only",
                    "status": "ready",
                    "active_fault": False,
                }
                atomic_write_json(args.fault_status_path, status)
            if args.publisher_state_path is not None:
                atomic_write_json(
                    args.publisher_state_path,
                    publisher_state_document(active_adapter, publishers),
                )
            sleep(1)
        return 0
    finally:
        stop_publishers()
        for publisher in publishers:
            _stop(publisher)
        if args.cleanup_fixtures and cleanup_requested(args.cleanup_request_path):
            remove_media_fixtures(args.fixture_dir)
        if args.heartbeat_file is not None:
            args.heartbeat_file.unlink(missing_ok=True)
        if args.publisher_state_path is not None:
            args.publisher_state_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
