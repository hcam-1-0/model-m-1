#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from hcam.settings import Settings
from hcam.streams.capabilities import (
    CapabilityDiscoveryError,
    CapabilityEndpointConfig,
    build_capability_discovery_engine,
)


_STREAM_ID = re.compile(r"^str_[0-9a-f]{32}$")
_AUTH_MODES = {
    "none",
    "wsse_password_digest",
    "http_digest",
    "wsse_and_http_digest",
}


class PrivateCameraLabError(RuntimeError):
    pass


def load_manifest(path: Path) -> CapabilityEndpointConfig:
    try:
        if not path.is_file() or path.stat().st_size > 64 * 1024:
            raise PrivateCameraLabError("manifest must be a small regular JSON file")
        document = json.loads(path.read_text(encoding="utf-8"))
    except PrivateCameraLabError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PrivateCameraLabError("private camera manifest is invalid") from exc
    if not isinstance(document, dict) or set(document) != {
        "version",
        "authorization",
        "camera",
    }:
        raise PrivateCameraLabError("private camera manifest has an invalid shape")
    authorization = document["authorization"]
    camera = document["camera"]
    if document["version"] != 1 or not isinstance(authorization, dict):
        raise PrivateCameraLabError("private camera manifest version must be 1")
    if set(authorization) != {"owned_or_authorized", "operator", "scope"}:
        raise PrivateCameraLabError("private camera authorization is incomplete")
    if (
        authorization["owned_or_authorized"] is not True
        or authorization["scope"] != "metadata-only"
        or not isinstance(authorization["operator"], str)
        or not authorization["operator"].strip()
    ):
        raise PrivateCameraLabError(
            "owned authorization for metadata-only validation is required"
        )
    required_camera_fields = {
        "stream_id",
        "camera_id",
        "locator",
        "protocol",
        "management_locator",
        "onvif_auth_mode",
        "secret_ref",
    }
    if not isinstance(camera, dict) or set(camera) != required_camera_fields:
        raise PrivateCameraLabError("private camera entry has an invalid shape")
    if (
        not isinstance(camera["stream_id"], str)
        or _STREAM_ID.fullmatch(camera["stream_id"]) is None
        or not isinstance(camera["camera_id"], str)
        or not camera["camera_id"].strip()
        or camera["protocol"] not in {"http", "https"}
        or camera["onvif_auth_mode"] not in _AUTH_MODES
    ):
        raise PrivateCameraLabError("private camera entry is invalid")
    for key in ("locator", "management_locator"):
        if not isinstance(camera[key], str) or not camera[key]:
            raise PrivateCameraLabError("private camera service URLs are required")
    secret_ref = camera["secret_ref"]
    if secret_ref is not None and not isinstance(secret_ref, str):
        raise PrivateCameraLabError("private camera secret reference is invalid")
    if camera["onvif_auth_mode"] != "none" and not secret_ref:
        raise PrivateCameraLabError(
            "authenticated private camera validation requires secret_ref"
        )
    return CapabilityEndpointConfig(
        stream_id=camera["stream_id"],
        camera_id=camera["camera_id"],
        locator=camera["locator"],
        protocol=camera["protocol"],
        management_locator=camera["management_locator"],
        onvif_auth_mode=camera["onvif_auth_mode"],
        secret_ref=secret_ref,
    )


def run(
    manifest: Path,
    *,
    settings: Settings | None = None,
    engine=None,
) -> dict[str, object]:
    if os.getenv("HCAM_PRIVATE_CAMERA_LAB_ENABLED", "").strip().lower() not in {
        "1",
        "true",
    }:
        raise PrivateCameraLabError("HCAM_PRIVATE_CAMERA_LAB_ENABLED=true is required")
    resolved_settings = settings or Settings.from_environment()
    if resolved_settings.environment not in {"development", "test"}:
        raise PrivateCameraLabError("private camera validation is forbidden in production")
    endpoint = load_manifest(manifest)
    discovery_engine = engine or build_capability_discovery_engine(resolved_settings)
    try:
        result = discovery_engine.discover(endpoint)
    except CapabilityDiscoveryError as exc:
        raise PrivateCameraLabError(
            f"private camera capability validation failed ({exc.reason_code})"
        ) from exc
    return {
        "mode": "authorized-private-camera-metadata-only",
        "stream_id": endpoint.stream_id,
        "camera_id": endpoint.camera_id,
        "source": result.source,
        "completeness": result.completeness,
        "capabilities": result.payload,
        "duration_ms": result.duration_ms,
        "captures_images": False,
        "records_video": False,
        "performs_network_discovery": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate one owned or authorized ONVIF camera without video capture"
    )
    parser.add_argument("manifest")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run(Path(args.manifest))
    except (PrivateCameraLabError, ValueError) as exc:
        print(f"private camera lab failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
