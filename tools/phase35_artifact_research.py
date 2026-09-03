#!/usr/bin/env python3
"""Acquire exact authorized P3.5 artifacts into a non-runtime quarantine."""

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
from urllib.parse import urlsplit, urlunsplit

import httpx


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUTHORIZATION = (
    ROOT / "contracts" / "phase-3" / "p3-5-artifact-research-authorization.json"
)
DEFAULT_PROPOSAL = (
    ROOT / "contracts" / "phase-3" / "p3-5-artifact-review-proposal.json"
)
DEFAULT_RESEARCH_ROOT = Path(
    os.environ.get(
        "HCAM_P35_RESEARCH_ROOT",
        r"F:\h cam\research-cache\phase-3\p3-5",
    )
)
ARTIFACT_ID = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,127}$")
SHA256 = re.compile(r"^[A-F0-9]{64}$")
ALLOWED_HOSTS = {
    "paddle-model-ecology.bj.bcebos.com",
    "raw.githubusercontent.com",
}


class ArtifactResearchError(RuntimeError):
    """A P3.5 authorization, validation, or transfer failure."""


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ArtifactResearchError(f"{path} must contain a JSON object")
    return value


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1(usedforsecurity=False)
    digest.update(f"blob {size}\0".encode())
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_research_root(path: Path) -> Path:
    absolute = path.absolute()
    current = absolute
    while current != current.parent:
        if current.exists() and current.is_symlink():
            raise ArtifactResearchError("quarantine root cannot traverse a symlink")
        current = current.parent
    absolute.mkdir(parents=True, exist_ok=True)
    if absolute.is_symlink():
        raise ArtifactResearchError("quarantine root cannot be a symlink")
    resolved = absolute.resolve(strict=True)
    if _inside(resolved, ROOT.resolve(strict=True)):
        raise ArtifactResearchError("quarantine root must be outside the Git worktree")
    return resolved


def _safe_artifact_id(value: str) -> str:
    if not ARTIFACT_ID.fullmatch(value):
        raise ArtifactResearchError("invalid artifact ID")
    return value


def _safe_filename(value: str) -> str:
    if not value or Path(value).name != value or "/" in value or "\\" in value:
        raise ArtifactResearchError("filename must be one plain path component")
    return value


def _validate_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise ArtifactResearchError("artifact URLs must use HTTPS")
    if parsed.username or parsed.password:
        raise ArtifactResearchError("artifact URLs cannot contain credentials")
    if parsed.port not in (None, 443):
        raise ArtifactResearchError("artifact URLs must use the default HTTPS port")
    if not parsed.hostname or parsed.hostname.lower() not in ALLOWED_HOSTS:
        raise ArtifactResearchError("artifact URL host is not allowlisted")
    if parsed.fragment:
        raise ArtifactResearchError("artifact URLs cannot contain fragments")


def _sanitized_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def load_authorized_context(
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    proposal_path: Path = DEFAULT_PROPOSAL,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    proposal_payload = proposal_path.resolve(strict=True).read_bytes()
    proposal_sha256 = _sha256_bytes(proposal_payload)
    authorization = _read_json(authorization_path.resolve(strict=True))
    proposal = json.loads(proposal_payload)
    if not isinstance(proposal, dict):
        raise ArtifactResearchError("proposal must contain a JSON object")
    validate_authorization(authorization, proposal, proposal_sha256)
    return authorization, proposal, proposal_sha256


def _artifact_map(record: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    artifacts = record.get(key)
    if not isinstance(artifacts, list):
        raise ArtifactResearchError(f"{key} must be a list")
    result: dict[str, dict[str, Any]] = {}
    for item in artifacts:
        if not isinstance(item, dict):
            raise ArtifactResearchError(f"{key} entries must be objects")
        artifact_id = _safe_artifact_id(str(item.get("artifact_id", "")))
        if artifact_id in result:
            raise ArtifactResearchError("artifact IDs must be unique")
        result[artifact_id] = item
    return result


def validate_authorization(
    authorization: dict[str, Any],
    proposal: dict[str, Any],
    proposal_sha256: str,
) -> None:
    if not SHA256.fullmatch(proposal_sha256):
        raise ArtifactResearchError("proposal SHA-256 is invalid")
    limits = authorization.get("limits")
    if (
        authorization.get("authorization_id") != "D-P3.5-ARTIFACT-RESEARCH"
        or authorization.get("status") != "owner_approved_restricted"
        or authorization.get("proposal_id") != proposal.get("proposal_id")
        or authorization.get("proposal_sha256") != proposal_sha256
        or authorization.get("implementation_authorized") is not False
        or authorization.get("allowed_network_actions")
        != ["https_get_exact_allowlisted_urls_only"]
        or not isinstance(limits, dict)
        or limits.get("maximum_redirects") != 0
        or limits.get("environment_proxies") is not False
        or limits.get("runtime_loading_from_quarantine") is not False
    ):
        raise ArtifactResearchError("artifact research authorization is not effective")

    allowed = _artifact_map(authorization, "allowed_artifacts")
    proposed = _artifact_map(proposal, "artifacts")
    if len(allowed) != 7:
        raise ArtifactResearchError("authorization must contain exactly seven artifacts")
    for artifact_id, item in allowed.items():
        source_url = str(item.get("source_url", ""))
        _validate_url(source_url)
        _safe_filename(str(item.get("filename", "")))
        proposal_item = proposed.get(artifact_id)
        if (
            proposal_item is None
            or proposal_item.get("proposed_source_url") != source_url
            or proposal_item.get("expected_bytes") != item.get("expected_bytes")
            or proposal_item.get("maximum_bytes") != item.get("maximum_bytes")
        ):
            raise ArtifactResearchError("authorization does not match proposal R0")


def _artifact_bytes(root: Path) -> int:
    artifact_root = root / "artifacts"
    if not artifact_root.exists():
        return 0
    return sum(path.stat().st_size for path in artifact_root.rglob("*") if path.is_file())


def _normalize_etag(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized.startswith("W/"):
        normalized = normalized[2:]
    return normalized.strip('"')


def _verify_identity(path: Path, proposal_item: dict[str, Any]) -> str | None:
    expected = proposal_item.get("git_blob_sha1")
    if expected is None:
        return None
    observed = _git_blob_sha1(path)
    if observed != expected:
        raise ArtifactResearchError("artifact Git blob SHA-1 does not match proposal")
    return observed


def _existing_receipt(
    root: Path,
    authorization: dict[str, Any],
    item: dict[str, Any],
    proposal_item: dict[str, Any],
    proposal_sha256: str,
) -> dict[str, Any] | None:
    artifact_id = str(item["artifact_id"])
    destination = root / "artifacts" / artifact_id / str(item["filename"])
    receipt_path = root / "receipts" / f"{artifact_id}.json"
    if not destination.exists() and not receipt_path.exists():
        return None
    if (
        not destination.is_file()
        or destination.is_symlink()
        or not receipt_path.is_file()
        or receipt_path.is_symlink()
    ):
        raise ArtifactResearchError("partial existing artifact state requires review")
    receipt = _read_json(receipt_path)
    digest = _sha256_file(destination)
    if (
        receipt.get("authorization_id") != authorization.get("authorization_id")
        or receipt.get("proposal_sha256") != proposal_sha256
        or receipt.get("sha256") != digest
        or receipt.get("bytes") != destination.stat().st_size
        or receipt.get("initial_url") != item.get("source_url")
        or destination.stat().st_size != item.get("expected_bytes")
    ):
        raise ArtifactResearchError("existing artifact does not match its receipt")
    _verify_identity(destination, proposal_item)
    return {**receipt, "reused": True}


def acquire_artifact(
    authorization: dict[str, Any],
    proposal: dict[str, Any],
    proposal_sha256: str,
    artifact_id: str,
    research_root: Path,
    *,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    validate_authorization(authorization, proposal, proposal_sha256)
    artifact_id = _safe_artifact_id(artifact_id)
    allowed = _artifact_map(authorization, "allowed_artifacts")
    proposed = _artifact_map(proposal, "artifacts")
    if artifact_id not in allowed:
        raise ArtifactResearchError("artifact ID is not authorized")
    item = allowed[artifact_id]
    proposal_item = proposed[artifact_id]
    filename = _safe_filename(str(item["filename"]))
    root = validate_research_root(research_root)
    existing = _existing_receipt(
        root, authorization, item, proposal_item, proposal_sha256
    )
    if existing is not None:
        return existing

    limits = authorization["limits"]
    maximum_bytes = int(item["maximum_bytes"])
    expected_bytes = int(item["expected_bytes"])
    cumulative_limit = int(limits["cumulative_artifact_bytes"])
    timeout = float(limits["per_artifact_timeout_seconds"])
    if not 0 < expected_bytes <= maximum_bytes or cumulative_limit <= 0 or timeout <= 0:
        raise ArtifactResearchError("artifact limits must be positive and bounded")

    source_url = str(item["source_url"])
    _validate_url(source_url)
    artifact_parent = root / "artifacts"
    receipt_dir = root / "receipts"
    for directory in (artifact_parent, receipt_dir):
        if directory.exists() and directory.is_symlink():
            raise ArtifactResearchError("quarantine directories cannot be symlinks")
    artifact_parent.mkdir(parents=True, exist_ok=True)
    receipt_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = artifact_parent / artifact_id
    artifact_dir.mkdir(exist_ok=False)
    destination = artifact_dir / filename
    partial = artifact_dir / f"{filename}.partial"
    existing_bytes = _artifact_bytes(root)

    owns_client = client is None
    active_client = client or httpx.Client(
        follow_redirects=False,
        timeout=httpx.Timeout(timeout),
        trust_env=False,
        headers={"User-Agent": "H-CAM-P3.5-Artifact-Research/1.0"},
    )
    response: httpx.Response | None = None
    try:
        request = active_client.build_request("GET", source_url)
        response = active_client.send(request, stream=True, follow_redirects=False)
        if response.is_redirect:
            raise ArtifactResearchError("redirects are prohibited")
        response.raise_for_status()
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) != expected_bytes:
            raise ArtifactResearchError("Content-Length does not match authorization")
        content_type = response.headers.get("content-type", "").split(";", 1)[0]
        expected_types = set(item.get("expected_content_types", []))
        if not content_type or content_type not in expected_types:
            raise ArtifactResearchError("content type is not authorized")
        observed_etag = _normalize_etag(response.headers.get("etag"))
        expected_etag = _normalize_etag(proposal_item.get("observed_etag"))
        if expected_etag is not None and observed_etag != expected_etag:
            raise ArtifactResearchError("ETag does not match proposal")
        observed_modified = response.headers.get("last-modified")
        expected_modified = proposal_item.get("observed_last_modified")
        if expected_modified is not None and observed_modified != expected_modified:
            raise ArtifactResearchError("Last-Modified does not match proposal")

        digest = hashlib.sha256()
        transferred = 0
        with partial.open("xb") as handle:
            for chunk in response.iter_bytes(1024 * 1024):
                transferred += len(chunk)
                if transferred > maximum_bytes:
                    raise ArtifactResearchError("artifact exceeds its size ceiling")
                if existing_bytes + transferred > cumulative_limit:
                    raise ArtifactResearchError("quarantine exceeds cumulative size ceiling")
                digest.update(chunk)
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        if transferred != expected_bytes:
            raise ArtifactResearchError("artifact size does not match authorization")
        partial.replace(destination)
        git_blob_sha1 = _verify_identity(destination, proposal_item)
        receipt = {
            "acquired_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "artifact_id": artifact_id,
            "authorization_id": authorization["authorization_id"],
            "bytes": transferred,
            "content_type": content_type,
            "etag": observed_etag,
            "final_url": _sanitized_url(str(response.url)),
            "git_blob_sha1": git_blob_sha1,
            "initial_url": source_url,
            "last_modified": observed_modified,
            "local_path": str(destination.relative_to(root)).replace("\\", "/"),
            "proposal_id": authorization["proposal_id"],
            "proposal_sha256": proposal_sha256,
            "reused": False,
            "runtime_loading_authorized": False,
            "sha256": digest.hexdigest().upper(),
        }
        receipt_path = receipt_dir / f"{artifact_id}.json"
        with receipt_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        return receipt
    except (httpx.HTTPError, OSError, ValueError) as exc:
        raise ArtifactResearchError(str(exc)) from exc
    finally:
        if response is not None:
            response.close()
        if owns_client:
            active_client.close()
        if partial.exists():
            partial.unlink()
        if artifact_dir.exists() and not any(artifact_dir.iterdir()):
            artifact_dir.rmdir()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--artifact-id")
    selection.add_argument("--all", action="store_true")
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL)
    parser.add_argument("--root", type=Path, default=DEFAULT_RESEARCH_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        authorization, proposal, proposal_sha256 = load_authorized_context(
            args.authorization, args.proposal
        )
        allowed = _artifact_map(authorization, "allowed_artifacts")
        artifact_ids = tuple(allowed) if args.all else (args.artifact_id,)
        receipts = [
            acquire_artifact(
                authorization,
                proposal,
                proposal_sha256,
                str(artifact_id),
                args.root,
            )
            for artifact_id in artifact_ids
        ]
    except (ArtifactResearchError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"P3.5 artifact research failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipts, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
