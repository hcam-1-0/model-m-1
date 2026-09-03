#!/usr/bin/env python3
"""Acquire explicitly manifested P3.2 research artifacts into quarantine."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "contracts/phase-3/p3-2-research-artifacts.json"
DEFAULT_RESEARCH_ROOT = Path(
    os.environ.get(
        "HCAM_P32_RESEARCH_ROOT",
        r"F:\h cam\research-cache\phase-3\p3-2",
    )
)
ARTIFACT_ID = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,127}$")
REDIRECT_CODES = {301, 302, 303, 307, 308}


class AcquisitionError(RuntimeError):
    """A policy, validation, or transfer failure."""


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AcquisitionError(f"{path} must contain a JSON object")
    return value


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_research_root(path: Path) -> Path:
    absolute = path.absolute()
    current = absolute
    existing_components: list[Path] = []
    while current != current.parent:
        if current.exists():
            existing_components.append(current)
        current = current.parent
    if any(component.is_symlink() for component in existing_components):
        raise AcquisitionError("research root cannot traverse a symlink")
    absolute.mkdir(parents=True, exist_ok=True)
    if absolute.is_symlink():
        raise AcquisitionError("research root cannot be a symlink")
    resolved = absolute.resolve(strict=True)
    if _inside(resolved, ROOT.resolve(strict=True)):
        raise AcquisitionError("research root must be outside the Git worktree")
    return resolved


def _safe_component(value: str, field: str) -> str:
    if not ARTIFACT_ID.fullmatch(value):
        raise AcquisitionError(f"invalid {field}")
    return value


def _safe_filename(value: str) -> str:
    if not value or Path(value).name != value or "/" in value or "\\" in value:
        raise AcquisitionError("artifact filename must be one plain path component")
    return value


def _validate_url(url: str, allowed_hosts: set[str]) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise AcquisitionError("artifact URLs must use HTTPS")
    if parsed.username or parsed.password:
        raise AcquisitionError("artifact URLs cannot contain credentials")
    if parsed.port not in (None, 443):
        raise AcquisitionError("artifact URLs must use the default HTTPS port")
    if not parsed.hostname or parsed.hostname.lower() not in allowed_hosts:
        raise AcquisitionError("artifact URL host is not allowlisted")
    if parsed.fragment:
        raise AcquisitionError("artifact URLs cannot contain fragments")


def _sanitized_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def _select_artifact(manifest: dict[str, Any], artifact_id: str) -> dict[str, Any]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise AcquisitionError("manifest artifacts must be a list")
    matches = [item for item in artifacts if item.get("artifact_id") == artifact_id]
    if len(matches) != 1 or not isinstance(matches[0], dict):
        raise AcquisitionError("artifact ID must identify exactly one manifest entry")
    return matches[0]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _artifact_bytes(root: Path) -> int:
    artifact_root = root / "artifacts"
    if not artifact_root.exists():
        return 0
    return sum(path.stat().st_size for path in artifact_root.rglob("*") if path.is_file())


def _existing_receipt(root: Path, artifact: dict[str, Any]) -> dict[str, Any] | None:
    artifact_id = artifact["artifact_id"]
    destination = root / "artifacts" / artifact_id / artifact["filename"]
    receipt_path = root / "receipts" / f"{artifact_id}.json"
    if not destination.exists() and not receipt_path.exists():
        return None
    if (
        not destination.is_file()
        or destination.is_symlink()
        or not receipt_path.is_file()
        or receipt_path.is_symlink()
    ):
        raise AcquisitionError("partial existing artifact state requires manual review")
    receipt = _read_json(receipt_path)
    digest = _sha256(destination)
    if receipt.get("sha256") != digest or receipt.get("bytes") != destination.stat().st_size:
        raise AcquisitionError("existing artifact does not match its receipt")
    expected = artifact.get("expected_sha256")
    if expected and digest != str(expected).upper():
        raise AcquisitionError("existing artifact does not match the manifest digest")
    expected_bytes = artifact.get("expected_bytes")
    if expected_bytes is not None and destination.stat().st_size != int(expected_bytes):
        raise AcquisitionError("existing artifact does not match the manifest size")
    return {**receipt, "reused": True}


def acquire_artifact(
    manifest: dict[str, Any],
    artifact_id: str,
    research_root: Path,
    *,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    artifact_id = _safe_component(artifact_id, "artifact ID")
    artifact = _select_artifact(manifest, artifact_id)
    filename = _safe_filename(str(artifact.get("filename", "")))
    root = validate_research_root(research_root)
    existing = _existing_receipt(root, artifact)
    if existing is not None:
        return existing

    limits = manifest.get("limits")
    if not isinstance(limits, dict):
        raise AcquisitionError("manifest limits are missing")
    artifact_limit = min(
        int(limits["maximum_artifact_bytes"]),
        int(artifact["maximum_bytes"]),
    )
    cumulative_limit = int(limits["cumulative_artifact_bytes"])
    redirect_limit = int(limits["redirect_limit"])
    timeout = float(limits["timeout_seconds"])
    if artifact_limit <= 0 or cumulative_limit <= 0 or redirect_limit < 0:
        raise AcquisitionError("manifest limits must be positive")

    initial_url = str(artifact["source_url"])
    allowed_hosts = {
        str(host).lower() for host in artifact.get("allowed_redirect_hosts", [])
    }
    if urlsplit(initial_url).hostname:
        allowed_hosts.add(str(urlsplit(initial_url).hostname).lower())
    _validate_url(initial_url, allowed_hosts)

    artifact_dir = root / "artifacts" / artifact_id
    receipt_dir = root / "receipts"
    for directory in (artifact_dir.parent, receipt_dir):
        if directory.exists() and directory.is_symlink():
            raise AcquisitionError("research cache directories cannot be symlinks")
    existing_artifact_bytes = _artifact_bytes(root)
    artifact_dir.mkdir(parents=True, exist_ok=False)
    receipt_dir.mkdir(parents=True, exist_ok=True)
    destination = artifact_dir / filename
    partial = artifact_dir / f"{filename}.partial"

    owns_client = client is None
    active_client = client or httpx.Client(
        follow_redirects=False,
        timeout=httpx.Timeout(timeout),
        trust_env=False,
        headers={"User-Agent": "H-CAM-P3.2-Research-Acquirer/1.0"},
    )
    current_url = initial_url
    final_response: httpx.Response | None = None
    try:
        for redirect_count in range(redirect_limit + 1):
            _validate_url(current_url, allowed_hosts)
            response = active_client.build_request("GET", current_url)
            streamed = active_client.send(response, stream=True)
            if streamed.status_code in REDIRECT_CODES:
                location = streamed.headers.get("location")
                streamed.close()
                if not location or redirect_count == redirect_limit:
                    raise AcquisitionError("redirect policy limit reached")
                current_url = urljoin(current_url, location)
                continue
            final_response = streamed
            break
        if final_response is None:
            raise AcquisitionError("no final artifact response was received")
        final_response.raise_for_status()
        content_length = final_response.headers.get("content-length")
        if content_length and int(content_length) > artifact_limit:
            raise AcquisitionError("artifact exceeds the per-file size limit")
        content_type = final_response.headers.get("content-type", "").split(";", 1)[0]
        expected_types = set(artifact.get("expected_content_types", []))
        if expected_types and content_type and content_type not in expected_types:
            raise AcquisitionError("artifact content type is not permitted by the manifest")

        digest = hashlib.sha256()
        transferred = 0
        with partial.open("xb") as handle:
            for chunk in final_response.iter_bytes(1024 * 1024):
                transferred += len(chunk)
                if transferred > artifact_limit:
                    raise AcquisitionError("artifact exceeded the per-file size limit")
                if existing_artifact_bytes + transferred > cumulative_limit:
                    raise AcquisitionError("artifact cache exceeded the cumulative limit")
                digest.update(chunk)
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        observed_digest = digest.hexdigest().upper()
        expected_bytes = artifact.get("expected_bytes")
        if expected_bytes is not None and transferred != int(expected_bytes):
            raise AcquisitionError("artifact size does not match the manifest")
        expected_digest = artifact.get("expected_sha256")
        if expected_digest and observed_digest != str(expected_digest).upper():
            raise AcquisitionError("artifact SHA-256 does not match the manifest")
        partial.replace(destination)

        receipt = {
            "artifact_id": artifact_id,
            "authorization_id": manifest["authorization_id"],
            "bytes": transferred,
            "content_type": content_type or None,
            "downloaded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "final_url": _sanitized_url(current_url),
            "initial_url": initial_url,
            "local_path": str(destination.relative_to(root)).replace("\\", "/"),
            "research_status": artifact["research_status"],
            "reused": False,
            "sha256": observed_digest,
        }
        receipt_path = receipt_dir / f"{artifact_id}.json"
        with receipt_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        return receipt
    except (httpx.HTTPError, OSError, ValueError) as exc:
        raise AcquisitionError(str(exc)) from exc
    finally:
        if final_response is not None:
            final_response.close()
        if owns_client:
            active_client.close()
        if partial.exists():
            partial.unlink()
        if artifact_dir.exists() and not any(artifact_dir.iterdir()):
            artifact_dir.rmdir()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download one explicitly manifested P3.2 research artifact."
    )
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--root", type=Path, default=DEFAULT_RESEARCH_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        receipt = acquire_artifact(
            _read_json(args.manifest.resolve(strict=True)),
            args.artifact_id,
            args.root,
        )
    except (AcquisitionError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"research acquisition failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
