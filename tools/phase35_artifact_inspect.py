#!/usr/bin/env python3
"""Inspect authorized P3.5 quarantine artifacts without extraction or execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import phase35_artifact_research as research  # noqa: E402


MAX_TAR_MEMBERS = 512
MAX_TAR_UNPACKED_BYTES = 2 * 1024 * 1024 * 1024
MAX_FONT_TABLES = 128


class InspectionError(RuntimeError):
    """An artifact receipt, identity, or passive structure check failed."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def inspect_tar(path: Path) -> dict[str, Any]:
    inventory = hashlib.sha256()
    member_count = 0
    file_count = 0
    unpacked_bytes = 0
    top_levels: set[str] = set()
    try:
        with tarfile.open(path, mode="r:*") as archive:
            for member in archive:
                member_count += 1
                if member_count > MAX_TAR_MEMBERS:
                    raise InspectionError("archive member count exceeds limit")
                pure = PurePosixPath(member.name)
                if pure.is_absolute() or ".." in pure.parts or not pure.parts:
                    raise InspectionError("archive contains an unsafe member path")
                if not (member.isfile() or member.isdir()):
                    raise InspectionError("archive contains a link or special entry")
                if member.size < 0:
                    raise InspectionError("archive member has a negative size")
                if member.isfile():
                    file_count += 1
                    unpacked_bytes += member.size
                    if unpacked_bytes > MAX_TAR_UNPACKED_BYTES:
                        raise InspectionError("archive expanded size exceeds limit")
                top_levels.add(pure.parts[0])
                inventory.update(member.name.encode("utf-8", errors="strict"))
                inventory.update(b"\0")
                inventory.update(str(member.size).encode())
                inventory.update(b"\0")
                inventory.update(b"f" if member.isfile() else b"d")
                inventory.update(b"\0")
    except (tarfile.TarError, UnicodeError, OSError) as exc:
        raise InspectionError(f"archive inspection failed: {exc}") from exc
    return {
        "format": "tar",
        "member_count": member_count,
        "file_count": file_count,
        "unpacked_bytes": unpacked_bytes,
        "top_levels": sorted(top_levels),
        "inventory_sha256": inventory.hexdigest().upper(),
        "extracted": False,
    }


def inspect_font(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    if len(payload) < 12:
        raise InspectionError("font header is truncated")
    signature = payload[:4]
    if signature not in {b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"}:
        raise InspectionError("font sfnt signature is invalid")
    table_count = struct.unpack(">H", payload[4:6])[0]
    if not 0 < table_count <= MAX_FONT_TABLES:
        raise InspectionError("font table count is invalid")
    directory_end = 12 + (table_count * 16)
    if directory_end > len(payload):
        raise InspectionError("font table directory is truncated")
    tags: list[str] = []
    for index in range(table_count):
        start = 12 + (index * 16)
        tag_bytes, _checksum, offset, length = struct.unpack(
            ">4sIII", payload[start : start + 16]
        )
        try:
            tag = tag_bytes.decode("ascii")
        except UnicodeDecodeError as exc:
            raise InspectionError("font table tag is not ASCII") from exc
        if offset > len(payload) or length > len(payload) - offset:
            raise InspectionError("font table exceeds file bounds")
        tags.append(tag)
    required = {"cmap", "head", "name"}
    if not required.issubset(tags):
        raise InspectionError("font is missing required sfnt tables")
    return {
        "format": "sfnt",
        "signature_hex": signature.hex().upper(),
        "table_count": table_count,
        "table_tags": sorted(tags),
        "variable_font": "fvar" in tags,
        "executed": False,
    }


def inspect_traineddata(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    if size < 1024:
        raise InspectionError("traineddata file is unexpectedly small")
    with path.open("rb") as handle:
        header = handle.read(32)
    return {
        "format": "tesseract_traineddata",
        "header_hex": header.hex().upper(),
        "size_sanity": "pass",
        "executed": False,
    }


def inspect_quarantine(
    root: Path,
    authorization: dict[str, Any],
    proposal: dict[str, Any],
    proposal_sha256: str,
) -> dict[str, Any]:
    research.validate_authorization(authorization, proposal, proposal_sha256)
    resolved_root = root.resolve(strict=True)
    if research._inside(resolved_root, research.ROOT.resolve(strict=True)):
        raise InspectionError("quarantine must be outside the Git worktree")
    allowed = research._artifact_map(authorization, "allowed_artifacts")
    proposed = research._artifact_map(proposal, "artifacts")
    results: list[dict[str, Any]] = []
    for artifact_id, item in allowed.items():
        receipt_path = resolved_root / "receipts" / f"{artifact_id}.json"
        receipt = research._read_json(receipt_path)
        local_path = PurePosixPath(str(receipt.get("local_path", "")))
        if local_path.is_absolute() or ".." in local_path.parts:
            raise InspectionError("receipt contains an unsafe local path")
        artifact_path = resolved_root.joinpath(*local_path.parts)
        if (
            not artifact_path.is_file()
            or artifact_path.is_symlink()
            or not research._inside(artifact_path.resolve(strict=True), resolved_root)
        ):
            raise InspectionError("receipt artifact path is invalid")
        observed_sha256 = _sha256(artifact_path)
        if (
            receipt.get("authorization_id") != authorization["authorization_id"]
            or receipt.get("proposal_sha256") != proposal_sha256
            or receipt.get("sha256") != observed_sha256
            or receipt.get("bytes") != artifact_path.stat().st_size
            or receipt.get("runtime_loading_authorized") is not False
            or artifact_path.stat().st_size != item["expected_bytes"]
        ):
            raise InspectionError("artifact receipt or digest does not match")
        proposal_item = proposed[artifact_id]
        observed_blob = research._verify_identity(artifact_path, proposal_item)
        kind = proposal_item.get("kind")
        if kind == "model_archive":
            structure = inspect_tar(artifact_path)
        elif kind == "font":
            structure = inspect_font(artifact_path)
        elif kind == "tesseract_traineddata":
            structure = inspect_traineddata(artifact_path)
        else:
            raise InspectionError("artifact kind is not inspectable")
        results.append(
            {
                "artifact_id": artifact_id,
                "bytes": artifact_path.stat().st_size,
                "git_blob_sha1": observed_blob,
                "kind": kind,
                "sha256": observed_sha256,
                "structure": structure,
            }
        )
    return {
        "artifact_count": len(results),
        "artifacts": results,
        "authorization_id": authorization["authorization_id"],
        "extraction_performed": False,
        "proposal_id": authorization["proposal_id"],
        "proposal_sha256": proposal_sha256,
        "runtime_execution_performed": False,
        "status": "pass",
        "total_bytes": sum(item["bytes"] for item in results),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--authorization", type=Path, default=research.DEFAULT_AUTHORIZATION
    )
    parser.add_argument("--proposal", type=Path, default=research.DEFAULT_PROPOSAL)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        authorization, proposal, proposal_sha256 = research.load_authorized_context(
            args.authorization, args.proposal
        )
        report = inspect_quarantine(
            args.root, authorization, proposal, proposal_sha256
        )
    except (
        InspectionError,
        research.ArtifactResearchError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"P3.5 artifact inspection failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
