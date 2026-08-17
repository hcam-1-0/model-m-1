#!/usr/bin/env python3
"""Read-only Sentinel Gujarat CCTV environment probe.

This tool intentionally limits itself to documented/observed public endpoints
and metadata-only stream checks. It does not bulk-download video.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://live.sentinelgujarat.in"
DEFAULT_CAMERA_IDS = ("1", "6", "13", "22")
DEFAULT_HTTP_TIMEOUT = 20
DEFAULT_FFPROBE_TIMEOUT = 30
USER_AGENT = "H-CAM-Sentinel-CCTV-Probe/0.1"


class ProbeError(RuntimeError):
    """Raised for tool/runtime failures."""


def normalized_base_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise ProbeError("Base URL cannot be empty.")
    return value.rstrip("/")


def url_join(base_url: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return urllib.parse.urljoin(base_url + "/", path.lstrip("/"))


def fetch_json(base_url: str, path: str, timeout: int) -> Any:
    url = url_join(base_url, path)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        raise ProbeError(f"HTTP {exc.code} while fetching {url}") from exc
    except urllib.error.URLError as exc:
        raise ProbeError(f"Unable to fetch {url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise ProbeError(f"Timed out fetching {url}") from exc

    try:
        return json.loads(body.decode(charset))
    except json.JSONDecodeError as exc:
        raise ProbeError(f"Invalid JSON from {url}: {exc}") from exc


def fetch_cameras(base_url: str, timeout: int) -> list[dict[str, Any]]:
    payload = fetch_json(base_url, "/api/cameras", timeout)
    cameras = payload.get("cameras")
    if not isinstance(cameras, list):
        raise ProbeError("Unexpected /api/cameras payload: missing cameras list.")
    return cameras


def fetch_prepare_status(base_url: str, timeout: int) -> dict[str, Any]:
    payload = fetch_json(base_url, "/api/prepare/status", timeout)
    if not isinstance(payload, dict):
        raise ProbeError("Unexpected /api/prepare/status payload.")
    return payload


def fetch_camera_state(base_url: str, camera_id: str, timeout: int) -> dict[str, Any]:
    quoted = urllib.parse.quote(camera_id, safe="")
    payload = fetch_json(base_url, f"/api/cameras/{quoted}/state", timeout)
    if not isinstance(payload, dict):
        raise ProbeError(f"Unexpected state payload for camera {camera_id}.")
    return payload


def counter_from(cameras: list[dict[str, Any]], field: str) -> dict[str, int]:
    values = Counter(str(camera.get(field) or "unknown") for camera in cameras)
    return dict(sorted(values.items()))


def summarize_cameras(cameras: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "camera_count": len(cameras),
        "status": counter_from(cameras, "status"),
        "codec": counter_from(cameras, "codec"),
        "container": counter_from(cameras, "container"),
        "delivery": counter_from(cameras, "delivery"),
        "camera_ids": [str(camera.get("id")) for camera in cameras],
        "sample_locations": [
            {
                "id": str(camera.get("id")),
                "number": camera.get("number"),
                "name": camera.get("name"),
                "location": camera.get("location"),
            }
            for camera in cameras[:10]
        ],
    }


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def print_summary(summary: dict[str, Any], base_url: str) -> None:
    print("Sentinel CCTV metadata")
    print(f"base_url: {base_url}")
    print(f"camera_count: {summary['camera_count']}")
    for key in ("status", "codec", "container", "delivery"):
        values = ", ".join(f"{name}={count}" for name, count in summary[key].items())
        print(f"{key}: {values or 'none'}")
    print("sample_cameras:")
    for camera in summary["sample_locations"]:
        print(
            f"  {camera['id']}: {camera.get('name')} - "
            f"{camera.get('location') or 'unknown location'}"
        )


def parse_camera_ids(value: str | None) -> list[str]:
    raw = value or os.environ.get("SENTINEL_PROBE_CAMERA_IDS") or ",".join(DEFAULT_CAMERA_IDS)
    ids = [part.strip() for part in raw.split(",") if part.strip()]
    if not ids:
        raise ProbeError("At least one camera id is required.")
    return ids


def stream_url_from_state(base_url: str, state: dict[str, Any]) -> tuple[str | None, str | None]:
    hls_url = state.get("hls_url")
    stream_url = state.get("stream_url")
    if isinstance(hls_url, str) and hls_url:
        return "hls", url_join(base_url, hls_url)
    if isinstance(stream_url, str) and stream_url:
        return "progressive", url_join(base_url, stream_url)
    return None, None


def ffprobe_stream(url: str, timeout: int) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise ProbeError("ffprobe was not found on PATH.")

    command = [
        ffprobe,
        "-v",
        "error",
        "-hide_banner",
        "-rw_timeout",
        str(timeout * 1_000_000),
        "-user_agent",
        USER_AGENT,
        "-analyzeduration",
        "5000000",
        "-probesize",
        "5000000",
        "-show_entries",
        "stream=index,codec_name,codec_type,width,height,avg_frame_rate:"
        "format=format_name,duration,size,bit_rate",
        "-of",
        "json",
        url,
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "returncode": None,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "error": f"ffprobe timed out after {timeout} seconds",
        }

    elapsed = round(time.monotonic() - started, 3)
    result: dict[str, Any] = {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed,
    }

    if completed.stdout.strip():
        try:
            result["probe"] = json.loads(completed.stdout)
        except json.JSONDecodeError:
            result["stdout"] = completed.stdout.strip()[:2000]
    if completed.stderr.strip():
        result["stderr"] = completed.stderr.strip()[:2000]
    return result


def cmd_metadata(args: argparse.Namespace) -> int:
    cameras = fetch_cameras(args.base_url, args.http_timeout)
    summary = summarize_cameras(cameras)
    if args.json:
        print_json({"base_url": args.base_url, **summary})
    else:
        print_summary(summary, args.base_url)
    return 0


def cmd_state(args: argparse.Namespace) -> int:
    state = fetch_camera_state(args.base_url, args.camera_id, args.http_timeout)
    print_json(state)
    return 0


def cmd_stream_test(args: argparse.Namespace) -> int:
    state = fetch_camera_state(args.base_url, args.camera_id, args.http_timeout)
    delivery, stream_url = stream_url_from_state(args.base_url, state)
    result: dict[str, Any] = {
        "camera_id": args.camera_id,
        "status": state.get("status"),
        "delivery": delivery,
        "stream_url": stream_url,
    }

    if state.get("status") != "live":
        result["ok"] = False
        result["message"] = "Camera is not live; stream probe skipped."
        print_json(result)
        return 0

    if not stream_url:
        result["ok"] = False
        result["message"] = "Camera state did not include hls_url or stream_url."
        print_json(result)
        return 0

    result["ffprobe"] = ffprobe_stream(stream_url, args.ffprobe_timeout)
    print_json(result)
    return 0


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cmd_snapshot(args: argparse.Namespace) -> int:
    camera_ids = parse_camera_ids(args.camera_ids)
    output_dir = Path(args.output_dir)
    cameras = fetch_cameras(args.base_url, args.http_timeout)
    prepare = fetch_prepare_status(args.base_url, args.http_timeout)
    states: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for camera_id in camera_ids:
        try:
            states[camera_id] = fetch_camera_state(args.base_url, camera_id, args.http_timeout)
        except ProbeError as exc:
            errors[camera_id] = str(exc)

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    summary = {
        "created_at": timestamp,
        "base_url": args.base_url,
        "camera_ids": camera_ids,
        "camera_summary": summarize_cameras(cameras),
        "state_errors": errors,
        "safe_use": "Metadata and state JSON only. No CCTV video is stored.",
    }

    write_json(output_dir / "cameras.json", {"cameras": cameras})
    write_json(output_dir / "prepare-status.json", prepare)
    for camera_id, state in states.items():
        safe_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in camera_id)
        write_json(output_dir / f"camera-{safe_id}-state.json", state)
    write_json(output_dir / "snapshot-summary.json", summary)

    print(f"snapshot_dir: {output_dir}")
    print(f"camera_count: {len(cameras)}")
    print(f"state_files: {len(states)}")
    if errors:
        print("state_errors:")
        for camera_id, message in errors.items():
            print(f"  {camera_id}: {message}")
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    camera_ids = parse_camera_ids(args.camera_ids)
    cameras = fetch_cameras(args.base_url, args.http_timeout)
    summary = summarize_cameras(cameras)
    print_summary(summary, args.base_url)
    print()

    try:
        prepare = fetch_prepare_status(args.base_url, args.http_timeout)
        print("prepare_status:")
        print_json(prepare)
    except ProbeError as exc:
        print(f"prepare_status_error: {exc}")
    print()

    for camera_id in camera_ids:
        print(f"camera_state: {camera_id}")
        try:
            state = fetch_camera_state(args.base_url, camera_id, args.http_timeout)
            print_json(state)
        except ProbeError as exc:
            print_json({"camera_id": camera_id, "error": str(exc)})
        print()

    for camera_id in camera_ids:
        print(f"stream_test: {camera_id}")
        stream_args = argparse.Namespace(
            base_url=args.base_url,
            camera_id=camera_id,
            http_timeout=args.http_timeout,
            ffprobe_timeout=args.ffprobe_timeout,
        )
        try:
            cmd_stream_test(stream_args)
        except ProbeError as exc:
            print_json({"camera_id": camera_id, "tool_error": str(exc)})
        print()

    return 0


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SENTINEL_BASE_URL", DEFAULT_BASE_URL),
        type=normalized_base_url,
        help=f"Sentinel base URL. Default: {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--http-timeout",
        default=DEFAULT_HTTP_TIMEOUT,
        type=int,
        help=f"HTTP timeout in seconds. Default: {DEFAULT_HTTP_TIMEOUT}",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Sentinel CCTV adapter and stream metadata probe."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata = subparsers.add_parser("metadata", help="Fetch and summarize /api/cameras.")
    add_common_args(metadata)
    metadata.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    metadata.set_defaults(func=cmd_metadata)

    state = subparsers.add_parser("state", help="Fetch one /api/cameras/{id}/state payload.")
    add_common_args(state)
    state.add_argument("--camera-id", required=True, help="Camera id to inspect.")
    state.set_defaults(func=cmd_state)

    stream_test = subparsers.add_parser(
        "stream-test", help="Run a metadata-only ffprobe check for one camera stream."
    )
    add_common_args(stream_test)
    stream_test.add_argument("--camera-id", required=True, help="Camera id to inspect.")
    stream_test.add_argument(
        "--ffprobe-timeout",
        default=DEFAULT_FFPROBE_TIMEOUT,
        type=int,
        help=f"ffprobe timeout in seconds. Default: {DEFAULT_FFPROBE_TIMEOUT}",
    )
    stream_test.set_defaults(func=cmd_stream_test)

    snapshot = subparsers.add_parser(
        "snapshot", help="Save camera metadata and selected states as small JSON fixtures."
    )
    add_common_args(snapshot)
    snapshot.add_argument(
        "--camera-ids",
        help="Comma-separated camera ids. Default comes from SENTINEL_PROBE_CAMERA_IDS or 1,6,13,22.",
    )
    snapshot.add_argument(
        "--output-dir",
        default="fixtures/sentinel",
        help="Output directory for generated JSON fixtures.",
    )
    snapshot.set_defaults(func=cmd_snapshot)

    all_cmd = subparsers.add_parser("all", help="Run metadata, state, and stream checks.")
    add_common_args(all_cmd)
    all_cmd.add_argument(
        "--camera-ids",
        help="Comma-separated camera ids. Default comes from SENTINEL_PROBE_CAMERA_IDS or 1,6,13,22.",
    )
    all_cmd.add_argument(
        "--ffprobe-timeout",
        default=DEFAULT_FFPROBE_TIMEOUT,
        type=int,
        help=f"ffprobe timeout in seconds. Default: {DEFAULT_FFPROBE_TIMEOUT}",
    )
    all_cmd.set_defaults(func=cmd_all)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ProbeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
