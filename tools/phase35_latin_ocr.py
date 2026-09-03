#!/usr/bin/env python3
"""Extract and evaluate the exact P3.5 W5 Latin PaddleOCR artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "app") not in sys.path:
    sys.path.insert(0, str(ROOT / "app"))

from hcam.analytics.anpr.contracts import (  # noqa: E402
    LatinOcrCandidateEvaluationV1,
    LatinOcrGeneratedEvaluationV1,
)
from hcam.analytics.anpr.guardrails import canonical_anpr_evidence_json  # noqa: E402


ARTIFACT_ROOT = Path(r"E:\h-cam-research-cache\phase-3\p3-5\artifacts")
RUNTIME_ROOT = Path(r"E:\h-cam-research-cache\phase-3\p3-5-runtime")
EVIDENCE_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-latin-ocr-evaluation.json"
)
START_AUTHORIZATION = (
    ROOT / "contracts" / "phase-3" / "p3-5-start-authorization.json"
)
WORKER_PATH = ROOT / "tools" / "phase35_latin_ocr_worker.py"
RESULT_PREFIX = "HCAM_P35_W5_RESULT="
MAX_MEMBER_COUNT = 8
MAX_EXPANDED_BYTES = 128 * 1024 * 1024
MAX_EVIDENCE_BYTES = 128 * 1024
MAX_EVIDENCE_NODES = 8_192


class LatinOcrToolError(RuntimeError):
    """Safe parent-side W5 tooling failure."""


@dataclass(frozen=True, slots=True)
class ArtifactProfile:
    candidate_id: str
    artifact_id: str
    archive_relative_path: str
    archive_sha256: str
    top_level: str
    member_sizes: dict[str, int]
    inference_yml_sha256: str


PROFILES = {
    "OCR-L0": ArtifactProfile(
        candidate_id="OCR-L0",
        artifact_id="OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED",
        archive_relative_path=(
            "OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED/PP-OCRv6_small_rec_infer.tar"
        ),
        archive_sha256=(
            "DA460F968CE9F88325AC3A34FA302077D6E9B0DCEFB16BA3137CD7796F879D06"
        ),
        top_level="PP-OCRv6_small_rec_infer",
        member_sizes={
            "inference.json": 208_004,
            "inference.pdiparams": 21_074_618,
            "inference.yml": 150_579,
        },
        inference_yml_sha256=(
            "AB078671BB49F06228EADCCD34F1BB501E157F7A047095FFB943BA81512C77D1"
        ),
    ),
    "OCR-L1": ArtifactProfile(
        candidate_id="OCR-L1",
        artifact_id="OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED",
        archive_relative_path=(
            "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED/PP-OCRv6_medium_rec_infer.tar"
        ),
        archive_sha256=(
            "4EECC1C6A4623765042E6FC15446DA0DA110B7D875B6B72B2D351D2B2DBD4DA6"
        ),
        top_level="PP-OCRv6_medium_rec_infer",
        member_sizes={
            "inference.json": 221_814,
            "inference.pdiparams": 76_465_087,
            "inference.yml": 150_580,
        },
        inference_yml_sha256=(
            "991B700FACF5B50A7DE193468207D5F4255B538DDE0D312AE3B7C7A9B6873129"
        ),
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_external_roots() -> tuple[Path, Path]:
    if ARTIFACT_ROOT.is_symlink() or RUNTIME_ROOT.is_symlink():
        raise LatinOcrToolError("external W5 roots cannot be symlinks")
    artifacts = ARTIFACT_ROOT.resolve(strict=True)
    runtime = RUNTIME_ROOT.resolve(strict=True)
    repository = ROOT.resolve(strict=True)
    if (
        artifacts.drive.upper() != "E:"
        or runtime.drive.upper() != "E:"
        or _inside(artifacts, repository)
        or _inside(runtime, repository)
    ):
        raise LatinOcrToolError("external W5 roots do not match the authorized boundary")
    return artifacts, runtime


def _load_authorization() -> dict[str, Any]:
    authorization = json.loads(START_AUTHORIZATION.read_text(encoding="utf-8"))
    if (
        authorization.get("decision_id") != "D-P3.5-START"
        or authorization.get("effective") is not True
        or "P35-W5_exact_Latin_Paddle_OCR_adapters_and_generated_evaluation"
        not in authorization.get("allowed_work_packages", [])
        or authorization.get("allowed_network_actions") != []
        or authorization.get("allowed_runtime", {}).get("network_access") is not False
        or authorization.get("allowed_runtime", {}).get("external_runtime_root")
        != str(RUNTIME_ROOT)
        or authorization.get("allowed_runtime", {}).get("direct_packages")
        != [
            "paddleocr==3.7.0",
            "paddlepaddle==3.3.1",
            "pillow==12.3.0",
            "regex==2026.7.19",
        ]
        or authorization.get("allowed_runtime", {}).get("python_version")
        != "3.12.13"
        or authorization.get("allowed_runtime", {}).get(
            "repository_dependency_or_lockfile_change"
        )
        is not False
        or authorization.get("allowed_runtime", {}).get(
            "tesseract_runtime_authorized"
        )
        is not False
    ):
        raise LatinOcrToolError("effective W5 authorization is missing or changed")
    allowed = {
        item["candidate_id"]: item
        for item in authorization.get("allowed_artifacts", [])
    }
    for profile in PROFILES.values():
        item = allowed.get(profile.candidate_id)
        if (
            item is None
            or item.get("artifact_id") != profile.artifact_id
            or item.get("sha256") != profile.archive_sha256
            or item.get("allowed_actions")
            != [
                "safe_extract_in_external_local_quarantine",
                "load_for_generated_only_local_inference",
            ]
        ):
            raise LatinOcrToolError("exact W5 artifact authorization changed")
    return authorization


def _inspect_archive(path: Path, profile: ArtifactProfile) -> list[tarfile.TarInfo]:
    if not path.is_file() or path.is_symlink() or _sha256(path) != profile.archive_sha256:
        raise LatinOcrToolError("exact W5 archive digest mismatch")
    expected_files = {
        f"{profile.top_level}/{name}": size
        for name, size in profile.member_sizes.items()
    }
    observed_files: dict[str, int] = {}
    directories: set[str] = set()
    members: list[tarfile.TarInfo] = []
    expanded = 0
    try:
        with tarfile.open(path, mode="r:*") as archive:
            for member in archive:
                members.append(member)
                if len(members) > MAX_MEMBER_COUNT:
                    raise LatinOcrToolError("W5 archive member limit exceeded")
                pure = PurePosixPath(member.name)
                if pure.is_absolute() or ".." in pure.parts or not pure.parts:
                    raise LatinOcrToolError("W5 archive contains an unsafe path")
                normalized = pure.as_posix().rstrip("/")
                if member.isdir():
                    if member.size != 0:
                        raise LatinOcrToolError(
                            "W5 archive directory has a nonzero payload"
                        )
                    directories.add(normalized)
                elif member.isfile():
                    if normalized in observed_files:
                        raise LatinOcrToolError("W5 archive contains a duplicate file")
                    observed_files[normalized] = member.size
                    expanded += member.size
                else:
                    raise LatinOcrToolError("W5 archive contains a link or special entry")
                if member.size < 0 or expanded > MAX_EXPANDED_BYTES:
                    raise LatinOcrToolError("W5 archive expanded size exceeds limit")
    except (OSError, tarfile.TarError, UnicodeError) as exc:
        raise LatinOcrToolError("W5 archive inspection failed") from exc
    if observed_files != expected_files or directories != {profile.top_level}:
        raise LatinOcrToolError("W5 archive inventory differs from the reviewed inventory")
    return members


def _model_inventory(model_dir: Path, profile: ArtifactProfile) -> str:
    if model_dir.is_symlink():
        raise LatinOcrToolError("extracted W5 model directory cannot be a symlink")
    resolved = model_dir.resolve(strict=True)
    observed: dict[str, Path] = {}
    for path in resolved.rglob("*"):
        if path.is_symlink():
            raise LatinOcrToolError("extracted W5 model contains a symlink")
        if path.is_dir():
            raise LatinOcrToolError("extracted W5 model contains an extra directory")
        if path.is_file():
            observed[path.relative_to(resolved).as_posix()] = path
    if set(observed) != set(profile.member_sizes):
        raise LatinOcrToolError("extracted W5 model inventory changed")
    digest = hashlib.sha256()
    for name in sorted(observed):
        path = observed[name]
        if path.is_symlink() or path.stat().st_size != profile.member_sizes[name]:
            raise LatinOcrToolError("extracted W5 model member changed")
        member_sha256 = _sha256(path)
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(member_sha256.encode("ascii"))
        digest.update(b"\0")
    if _sha256(resolved / "inference.yml") != profile.inference_yml_sha256:
        raise LatinOcrToolError("extracted W5 inference configuration changed")
    return f"sha256:{digest.hexdigest()}"


def _write_external_json(path: Path, value: object, runtime: Path) -> None:
    if path.parent.is_symlink():
        raise LatinOcrToolError("external W5 evidence directory cannot be a symlink")
    if path.is_symlink():
        raise LatinOcrToolError("external W5 evidence file cannot be a symlink")
    resolved_parent = path.parent.resolve(strict=True)
    if not _inside(resolved_parent, runtime):
        raise LatinOcrToolError("external W5 evidence path escaped the runtime root")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        )
    os.replace(temporary, path)


def safe_extract_candidate(candidate_id: str) -> dict[str, Any]:
    _load_authorization()
    artifacts, runtime = _validate_external_roots()
    profile = PROFILES[candidate_id]
    archive_source = artifacts / profile.archive_relative_path
    if archive_source.is_symlink():
        raise LatinOcrToolError("W5 archive cannot be a symlink")
    archive_path = archive_source.resolve(strict=True)
    if not _inside(archive_path, artifacts):
        raise LatinOcrToolError("W5 archive escaped the artifact root")
    members = _inspect_archive(archive_path, profile)

    models_root = runtime / "models"
    evidence_root = runtime / "evidence"
    models_root.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)
    if models_root.is_symlink() or evidence_root.is_symlink():
        raise LatinOcrToolError("W5 runtime directories cannot be symlinks")
    candidate_root = models_root / candidate_id
    model_dir = candidate_root / profile.top_level

    if candidate_root.exists():
        if not candidate_root.is_dir() or candidate_root.is_symlink():
            raise LatinOcrToolError("existing W5 candidate path is unsafe")
        if {path.name for path in candidate_root.iterdir()} != {profile.top_level}:
            raise LatinOcrToolError("existing W5 candidate root contains extra entries")
        inventory = _model_inventory(model_dir, profile)
        extracted_now = False
    else:
        temporary_root = models_root / f".extract-{candidate_id}-{uuid.uuid4().hex}"
        temporary_root.mkdir()
        try:
            with tarfile.open(archive_path, mode="r:*") as archive:
                for member in members:
                    pure = PurePosixPath(member.name)
                    destination = temporary_root.joinpath(*pure.parts)
                    resolved_parent = destination.parent.resolve(strict=False)
                    if not _inside(resolved_parent, temporary_root.resolve(strict=True)):
                        raise LatinOcrToolError("W5 extraction destination escaped quarantine")
                    if member.isdir():
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    source = archive.extractfile(member)
                    if source is None:
                        raise LatinOcrToolError("W5 archive file could not be opened")
                    remaining = member.size
                    with source, destination.open("xb") as output:
                        while remaining:
                            chunk = source.read(min(1024 * 1024, remaining))
                            if not chunk:
                                raise LatinOcrToolError("W5 archive member is truncated")
                            output.write(chunk)
                            remaining -= len(chunk)
                        if source.read(1):
                            raise LatinOcrToolError("W5 archive member exceeds declared size")
            inventory = _model_inventory(
                temporary_root / profile.top_level,
                profile,
            )
            temporary_root.rename(candidate_root)
            extracted_now = True
        except Exception:
            resolved_temporary = temporary_root.resolve(strict=False)
            if temporary_root.exists() and _inside(
                resolved_temporary, models_root.resolve(strict=True)
            ):
                shutil.rmtree(temporary_root)
            raise

    receipt = {
        "contract_type": "hcam.phase3.p3_5.latin-ocr-extraction-receipt.v1",
        "work_package": "P35-W5_exact_Latin_Paddle_OCR_adapters_and_generated_evaluation",
        "candidate_id": candidate_id,
        "artifact_id": profile.artifact_id,
        "archive_sha256": f"sha256:{profile.archive_sha256.lower()}",
        "extracted_inventory_sha256": inventory,
        "member_count": len(profile.member_sizes),
        "expanded_bytes": sum(profile.member_sizes.values()),
        "extracted_now": extracted_now,
        "external_runtime_only": True,
        "network_access_performed": False,
        "model_execution_performed": False,
    }
    _write_external_json(
        evidence_root / f"p3-5-w5-{candidate_id.lower()}-extraction.json",
        receipt,
        runtime,
    )
    return {**receipt, "model_dir": str(model_dir)}


def _safe_environment(runtime: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.lower().endswith("_proxy")
        and not key.upper().startswith(
            (
                "HF_",
                "HOME",
                "PADDLE",
                "PIP_",
                "PYTHON",
                "TEMP",
                "TMP",
                "TRANSFORMERS_",
                "USERPROFILE",
                "UV_",
            )
        )
    }
    temporary = runtime / "temp" / "p3-5-w5"
    cache = runtime / "cache" / "p3-5-w5"
    temporary.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    environment.update(
        {
            "HF_HUB_OFFLINE": "1",
            "HOME": str(cache),
            "PADDLE_HOME": str(cache / "paddle"),
            "PADDLE_PDX_CACHE_HOME": str(cache / "paddlex"),
            "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": "1",
            "PYTHONNOUSERSITE": "1",
            "TEMP": str(temporary),
            "TMP": str(temporary),
            "TRANSFORMERS_OFFLINE": "1",
            "USERPROFILE": str(cache),
        }
    )
    return environment


def evaluate_candidate(candidate_id: str, *, sample_count: int) -> LatinOcrCandidateEvaluationV1:
    receipt = safe_extract_candidate(candidate_id)
    _, runtime = _validate_external_roots()
    python = runtime / "venv" / "Scripts" / "python.exe"
    if not python.is_file() or python.is_symlink():
        raise LatinOcrToolError("exact W5 Python runtime is missing")
    completed = subprocess.run(
        [
            str(python),
            "-I",
            str(WORKER_PATH),
            "--candidate",
            candidate_id,
            "--model-dir",
            receipt["model_dir"],
            "--inventory-sha256",
            receipt["extracted_inventory_sha256"],
            "--sample-count",
            str(sample_count),
        ],
        cwd=runtime,
        env=_safe_environment(runtime),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=1_800,
    )
    if completed.returncode != 0:
        raise LatinOcrToolError("isolated W5 OCR worker failed")
    result_line = next(
        (
            line[len(RESULT_PREFIX) :]
            for line in reversed(completed.stdout.splitlines())
            if line.startswith(RESULT_PREFIX)
        ),
        None,
    )
    if result_line is None:
        raise LatinOcrToolError("isolated W5 OCR worker emitted no result")
    try:
        result = LatinOcrCandidateEvaluationV1.model_validate_json(result_line)
    except ValueError as exc:
        raise LatinOcrToolError("isolated W5 OCR result is invalid") from exc
    return result


def build_evaluation(*, sample_count: int) -> LatinOcrGeneratedEvaluationV1:
    _load_authorization()
    if not 1 <= sample_count <= 12:
        raise LatinOcrToolError(
            "W5 sample count must stay within development and validation splits"
        )
    evaluations = tuple(
        evaluate_candidate(candidate_id, sample_count=sample_count)
        for candidate_id in ("OCR-L0", "OCR-L1")
    )
    return LatinOcrGeneratedEvaluationV1(candidate_evaluations=evaluations)


def render_evaluation(evaluation: LatinOcrGeneratedEvaluationV1) -> str:
    return canonical_anpr_evidence_json(
        evaluation,
        maximum_bytes=MAX_EVIDENCE_BYTES,
        maximum_nodes=MAX_EVIDENCE_NODES,
    )


def check_evidence() -> int:
    try:
        actual = EVIDENCE_PATH.read_text(encoding="utf-8")
        parsed = LatinOcrGeneratedEvaluationV1.model_validate_json(actual)
        canonical = render_evaluation(parsed)
    except (OSError, ValueError) as exc:
        print(f"[fail] P3.5 W5 evidence: {exc}")
        return 1
    if actual != canonical or "SYN-" in actual or '"raw_text"' in actual:
        print("[fail] P3.5 W5 evidence is non-canonical or contains ephemeral OCR data")
        return 1
    print(f"[pass] {EVIDENCE_PATH.relative_to(ROOT)}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    extract = subparsers.add_parser("extract")
    extract.add_argument("--candidate", choices=[*PROFILES, "all"], default="all")
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--sample-count", type=int, default=12)
    evaluate.add_argument("--write-evidence", action="store_true")
    evaluate.add_argument("--acknowledge-generated-only-evidence", action="store_true")
    subparsers.add_parser("check-evidence")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "extract":
            candidates = PROFILES if args.candidate == "all" else (args.candidate,)
            for candidate_id in candidates:
                receipt = safe_extract_candidate(candidate_id)
                print(
                    f"[pass] {candidate_id} exact extraction "
                    f"{receipt['extracted_inventory_sha256']}"
                )
            return 0
        if args.command == "check-evidence":
            return check_evidence()
        if args.write_evidence and not args.acknowledge_generated_only_evidence:
            print("Refusing to write W5 evidence without generated-only acknowledgment")
            return 2
        evaluation = build_evaluation(sample_count=args.sample_count)
        rendered = render_evaluation(evaluation)
        if args.write_evidence:
            EVIDENCE_PATH.write_text(
                rendered,
                encoding="utf-8",
                newline="\n",
            )
            print(f"[write] {EVIDENCE_PATH.relative_to(ROOT)}")
        else:
            print(rendered, end="")
        return 0
    except (
        LatinOcrToolError,
        OSError,
        ValueError,
        subprocess.TimeoutExpired,
        tarfile.TarError,
    ) as exc:
        print(f"P3.5 W5 failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
