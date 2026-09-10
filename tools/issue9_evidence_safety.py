#!/usr/bin/env python3
"""Validate that Issue #9 evidence is aggregate-only and safe to publish."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FORBIDDEN_TEXT = (
    "http://",
    "https://",
    "rtsp://",
    "whep",
    "hls://",
    "authorization",
    "bearer ",
    "token",
    "password",
    "sdp",
    "candidate:",
    "external_camera_id",
    "camera_id",
)
REQUIRED = {
    "schema": "hcam.issue9.browser_evidence.v1",
    "classification": "generated-only",
    "provider_contacted": False,
    "retained_media": False,
}


class EvidenceSafetyError(RuntimeError):
    """The artifact is unsuitable for CI publication."""


def _walk(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [*value.keys(), *[item for child in value.values() for item in _walk(child)]]
    if isinstance(value, list):
        return [item for child in value for item in _walk(child)]
    return [value] if isinstance(value, str) else []


def validate(path: Path) -> dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceSafetyError("evidence_invalid") from exc
    if not isinstance(document, dict) or any(document.get(key) != value for key, value in REQUIRED.items()):
        raise EvidenceSafetyError("evidence_contract_invalid")
    text = "\n".join(_walk(document)).casefold()
    if any(forbidden in text for forbidden in FORBIDDEN_TEXT):
        raise EvidenceSafetyError("evidence_sensitive_content")
    return {"valid": True, "classification": "generated-only", "retained_media": False}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate safe Issue #9 CI evidence")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.path), sort_keys=True))
    except EvidenceSafetyError as exc:
        print(json.dumps({"valid": False, "reason": exc.args[0]}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
