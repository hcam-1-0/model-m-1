#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from prometheus_client.parser import text_string_to_metric_families


ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "deploy" / "compose.phase2.yaml"
DEFAULT_SECRET_ROOT = ROOT / "var" / "phase2-lab-secrets"


class LabError(RuntimeError):
    pass


class LabHttpError(LabError):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"Phase 2 lab HTTP check returned {status_code}")
        self.status_code = status_code


def _write_secret(path: Path, value: str, *, force: bool) -> None:
    if force or not path.exists():
        path.write_text(value, encoding="ascii")
    try:
        # Linux Compose file secrets preserve host ownership. The private
        # parent directory protects the files on the host, while 0644 lets
        # the fixed non-root container UID read its service-specific mount.
        path.chmod(0o644)
    except OSError:
        pass


def prepare(secret_root: Path, *, force: bool = False) -> dict[str, object]:
    secret_root.mkdir(parents=True, exist_ok=True)
    try:
        secret_root.chmod(0o700)
    except OSError:
        pass
    password = secrets.token_urlsafe(32)
    _write_secret(secret_root / "postgres-password", password, force=force)
    stored_password = (secret_root / "postgres-password").read_text(encoding="ascii")
    database_url = (
        "postgresql+psycopg://hcam_phase2:"
        f"{stored_password}@database:5432/hcam_phase2"
    )
    _write_secret(secret_root / "database-url", database_url, force=force)
    _write_secret(
        secret_root / "metrics-token", secrets.token_urlsafe(32), force=force
    )
    key_path = secret_root / "playback-signing-key.pem"
    if force or not key_path.exists():
        private_key = ec.generate_private_key(ec.SECP256R1())
        key_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("ascii")
        _write_secret(key_path, key_pem, force=True)
    else:
        try:
            key_path.chmod(0o644)
        except OSError:
            pass
    private_key = serialization.load_pem_private_key(
        key_path.read_bytes(), password=None
    )
    public_der = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    key_id = hashlib.sha256(public_der).hexdigest()[:24]
    now = datetime.now(UTC)
    probe_token = jwt.encode(
        {
            "aud": "mediamtx",
            "exp": now + timedelta(hours=24),
            "iat": now,
            "iss": "hcam-core",
            "jti": secrets.token_hex(16),
            "mediamtx_permissions": [
                {"action": "read", "path": "~^hcam/str_[0-9a-f]{32}$"}
            ],
            "nbf": now,
            "sub": "phase2-stream-worker",
        },
        private_key,
        algorithm="ES256",
        headers={"kid": key_id, "typ": "JWT"},
    )
    _write_secret(secret_root / "probe-token", probe_token, force=True)
    return {
        "prepared": True,
        "secret_root": str(secret_root),
        "files": 5,
        "contains_government_data": False,
        "contains_real_video": False,
    }


def _compose_environment(secret_root: Path) -> dict[str, str]:
    required = {
        "HCAM_POSTGRES_PASSWORD_FILE": secret_root / "postgres-password",
        "HCAM_DATABASE_URL_SECRET_FILE": secret_root / "database-url",
        "HCAM_METRICS_TOKEN_SECRET_FILE": secret_root / "metrics-token",
        "HCAM_PLAYBACK_SIGNING_KEY_SECRET_FILE": secret_root
        / "playback-signing-key.pem",
        "HCAM_STREAM_PROBE_TOKEN_SECRET_FILE": secret_root / "probe-token",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise LabError("Phase 2 lab secrets are missing; run prepare first")
    environment = os.environ.copy()
    environment.update({name: str(path.resolve()) for name, path in required.items()})
    return environment


def load_metrics_token(secret_root: Path) -> str:
    try:
        token = (secret_root / "metrics-token").read_text(encoding="ascii").strip()
    except OSError as exc:
        raise LabError("Phase 2 lab metrics token is unavailable") from exc
    if not token:
        raise LabError("Phase 2 lab metrics token is empty")
    return token


def compose(
    secret_root: Path,
    *arguments: str,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = ["docker", "compose", "-f", str(COMPOSE_FILE), *arguments]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=_compose_environment(secret_root),
            check=False,
            text=True,
            capture_output=capture_output,
        )
    except FileNotFoundError as exc:
        raise LabError("Docker CLI is unavailable") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip().splitlines()
        suffix = f": {detail[-1]}" if detail else ""
        raise LabError(f"Docker Compose command failed{suffix}")
    return completed


def doctor() -> dict[str, object]:
    try:
        completed = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            check=False,
            text=True,
            capture_output=True,
            timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise LabError("Docker Desktop is unavailable") from exc
    if completed.returncode != 0 or not completed.stdout.strip():
        raise LabError("Docker Desktop engine is not running")
    return {"docker_engine": "ready", "server_version": completed.stdout.strip()}


def _json_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    timeout: float = 10,
) -> dict[str, object]:
    request = Request(url, method=method, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read(1024 * 1024 + 1)
    except HTTPError as exc:
        raise LabHttpError(exc.code) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise LabError("Phase 2 lab HTTP check failed") from exc
    if len(payload) > 1024 * 1024:
        raise LabError("Phase 2 lab API response exceeded the safety limit")
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LabError("Phase 2 lab API returned invalid JSON") from exc
    if not isinstance(document, dict):
        raise LabError("Phase 2 lab API returned an invalid document")
    return document


def _create_playback_session(
    api_url: str,
    stream_id: str,
    headers: dict[str, str],
    *,
    timeout_seconds: float = 30,
) -> dict[str, object]:
    deadline = monotonic() + timeout_seconds
    while True:
        try:
            return _json_request(
                f"{api_url.rstrip('/')}/streams/{stream_id}/playback-sessions",
                method="POST",
                headers=headers,
            )
        except LabHttpError as exc:
            if exc.status_code != 409 or monotonic() >= deadline:
                raise
            sleep(1)


def verify_metrics(
    api_url: str,
    metrics_token: str,
    *,
    timeout_seconds: float = 30,
) -> dict[str, object]:
    if not metrics_token:
        raise LabError("metrics token is required")
    metrics_url = f"{api_url.rstrip('/')}/internal/metrics"
    try:
        urlopen(Request(metrics_url), timeout=10)
    except HTTPError as exc:
        if exc.code != 401:
            raise LabError("anonymous metrics check returned an unexpected status") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise LabError("anonymous metrics check failed") from exc
    else:
        raise LabError("metrics endpoint accepted an anonymous request")

    deadline = monotonic() + timeout_seconds
    latest: dict[str, float] = {}
    while monotonic() < deadline:
        request = Request(
            metrics_url,
            headers={"Authorization": f"Bearer {metrics_token}"},
        )
        try:
            with urlopen(request, timeout=10) as response:
                payload = response.read(1024 * 1024 + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise LabError("authorized metrics check failed") from exc
        if len(payload) > 1024 * 1024:
            raise LabError("metrics response exceeded the safety limit")
        try:
            families = text_string_to_metric_families(payload.decode("utf-8"))
            latest = {
                sample.name + ":" + str(sample.labels.get("state", "")): float(
                    sample.value
                )
                for family in families
                for sample in family.samples
                if sample.name
                in {
                    "hcam_stream_health_state_total",
                    "hcam_stream_outbox_unpublished_total",
                }
            }
        except (UnicodeDecodeError, ValueError) as exc:
            raise LabError("metrics response was invalid") from exc
        healthy = latest.get("hcam_stream_health_state_total:healthy")
        unhealthy = sum(
            latest.get(f"hcam_stream_health_state_total:{state}", 0)
            for state in (
                "unknown",
                "degraded",
                "offline",
                "unauthorized",
                "misconfigured",
                "unsupported",
            )
        )
        unpublished = latest.get("hcam_stream_outbox_unpublished_total:")
        if healthy == 50 and unhealthy == 0 and unpublished == 0:
            return {
                "metrics_protected": True,
                "metrics_healthy_streams": 50,
                "outbox_unpublished": 0,
            }
        sleep(1)
    raise LabError(f"stream metrics did not converge; latest={latest}")


def verify(
    *,
    api_url: str,
    metrics_token: str,
    timeout_seconds: float,
) -> dict[str, object]:
    if timeout_seconds <= 0:
        raise LabError("verification timeout must be positive")
    viewer_headers = {
        "X-HCAM-Actor": "phase2-lab-verifier",
        "X-HCAM-Roles": "camera.viewer",
        "X-HCAM-Departments": "*",
    }
    editor_headers = {
        "X-HCAM-Actor": "phase2-lab-verifier",
        "X-HCAM-Roles": "camera.editor",
        "X-HCAM-Departments": "*",
        "X-HCAM-Reason": "Authorized synthetic ONVIF capability verification",
    }
    deadline = monotonic() + timeout_seconds
    latest: dict[str, object] = {}
    while monotonic() < deadline:
        try:
            latest = _json_request(f"{api_url.rstrip('/')}/streams?limit=100", headers=viewer_headers)
        except LabError:
            sleep(2)
            continue
        items = latest.get("items")
        if isinstance(items, list) and len(items) == 50 and all(
            isinstance(item, dict)
            and isinstance(item.get("health"), dict)
            and item["health"].get("state") == "healthy"
            for item in items
        ):
            break
        sleep(2)
    else:
        raise LabError("50 synthetic streams did not become healthy before timeout")

    items = latest["items"]
    assert isinstance(items, list)
    onvif_item = next(
        (
            item
            for item in items
            if isinstance(item, dict) and item.get("adapter_kind") == "onvif"
        ),
        None,
    )
    if not isinstance(onvif_item, dict) or not isinstance(
        onvif_item.get("stream_id"), str
    ):
        raise LabError("ONVIF synthetic stream is unavailable for capability discovery")
    capability_report = _json_request(
        f"{api_url.rstrip('/')}/streams/{onvif_item['stream_id']}/capabilities/discover",
        method="POST",
        headers=editor_headers,
    )
    media_capabilities = capability_report.get("media")
    if not isinstance(media_capabilities, dict):
        raise LabError("ONVIF capability response is incomplete")
    profiles = media_capabilities.get("profiles")
    if (
        capability_report.get("source") != "onvif_media_service"
        or media_capabilities.get("maximum_profiles") != 8
        or not isinstance(profiles, list)
        or len(profiles) != 2
        or not isinstance(profiles[0], dict)
        or profiles[0].get("video_encoding") != "H264"
        or profiles[0].get("ptz_configured") is not True
    ):
        raise LabError("ONVIF capability response did not match the synthetic contract")
    first = items[0]
    assert isinstance(first, dict)
    stream_id = first.get("stream_id")
    if not isinstance(stream_id, str):
        raise LabError("stream response did not contain a stream ID")
    playback = _create_playback_session(
        api_url,
        stream_id,
        {
            **viewer_headers,
            "X-HCAM-Reason": "Authorized synthetic Phase 2 playback verification",
        },
    )
    playback_url = playback.get("playback_url")
    access_token = playback.get("access_token")
    if not isinstance(playback_url, str) or not isinstance(access_token, str):
        raise LabError("playback contract is incomplete")
    request = Request(
        playback_url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            manifest = response.read(64 * 1024 + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise LabError("authenticated HLS manifest check failed") from exc
    if len(manifest) > 64 * 1024 or not manifest.startswith(b"#EXTM3U"):
        raise LabError("HLS response is not a bounded playlist manifest")
    try:
        urlopen(Request(playback_url), timeout=10)
    except HTTPError as exc:
        if exc.code not in {401, 403}:
            raise LabError("unauthenticated HLS request returned an unexpected status") from exc
    else:
        raise LabError("MediaMTX accepted an unauthenticated HLS request")
    if len(items) < 2 or not isinstance(items[1], dict):
        raise LabError("a second stream is required for path-scope verification")
    second_id = items[1].get("stream_id")
    if not isinstance(second_id, str):
        raise LabError("second stream response did not contain a stream ID")
    cross_path_url = playback_url.replace(stream_id, second_id)
    try:
        urlopen(
            Request(
                cross_path_url,
                headers={"Authorization": f"Bearer {access_token}"},
            ),
            timeout=10,
        )
    except HTTPError as exc:
        if exc.code not in {401, 403}:
            raise LabError("cross-stream token request returned an unexpected status") from exc
    else:
        raise LabError("MediaMTX accepted a token for the wrong stream path")
    metrics = verify_metrics(api_url, metrics_token)
    return {
        "passed": True,
        "healthy_streams": 50,
        "onvif_simulator_streams": 1,
        "onvif_capability_profiles": 2,
        "onvif_capability_discovery": "validated",
        "playback_jwt": "validated-by-mediamtx",
        "anonymous_playback_denied": True,
        "cross_stream_token_denied": True,
        "hls_manifest_only": True,
        "video_downloaded": False,
        **metrics,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="H-CAM Phase 2 synthetic lab")
    parser.add_argument("--secret-root", type=Path, default=DEFAULT_SECRET_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--force", action="store_true")
    subparsers.add_parser("doctor")
    subparsers.add_parser("config")
    subparsers.add_parser("start")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    verify_parser.add_argument("--timeout", type=float, default=240)
    subparsers.add_parser("stop")
    subparsers.add_parser("logs")
    all_parser = subparsers.add_parser("all")
    all_parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    all_parser.add_argument("--timeout", type=float, default=240)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            report = prepare(args.secret_root, force=args.force)
        elif args.command == "doctor":
            report = doctor()
        elif args.command == "config":
            compose(args.secret_root, "config", "-q")
            report = {"compose_config": "valid"}
        elif args.command == "start":
            doctor()
            compose(args.secret_root, "build", "api")
            compose(
                args.secret_root,
                "up",
                "--no-build",
                "--wait",
                "--wait-timeout",
                "240",
            )
            report = {"stack": "started"}
        elif args.command == "verify":
            report = verify(
                api_url=args.api_url,
                metrics_token=load_metrics_token(args.secret_root),
                timeout_seconds=args.timeout,
            )
        elif args.command == "stop":
            compose(args.secret_root, "down", "--volumes", "--remove-orphans")
            report = {"stack": "stopped", "disposable_volume_removed": True}
        elif args.command == "logs":
            compose(args.secret_root, "logs", "--no-color")
            report = {"logs": "printed"}
        elif args.command == "all":
            prepare(args.secret_root)
            doctor()
            try:
                compose(args.secret_root, "build", "api")
                compose(
                    args.secret_root,
                    "up",
                    "--no-build",
                    "--wait",
                    "--wait-timeout",
                    "240",
                )
                report = verify(
                    api_url=args.api_url,
                    metrics_token=load_metrics_token(args.secret_root),
                    timeout_seconds=args.timeout,
                )
            finally:
                compose(args.secret_root, "down", "--volumes", "--remove-orphans")
        else:
            return 2
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except LabError as exc:
        print(f"phase2 lab failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
