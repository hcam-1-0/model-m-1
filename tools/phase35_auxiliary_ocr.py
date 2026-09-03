#!/usr/bin/env python3
"""Safely run the exact generated-only P3.5 W6 auxiliary-script evaluation."""

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
APP_ROOT = ROOT / "app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from hcam.analytics.anpr.contracts import (  # noqa: E402
    AuxiliaryScriptGeneratedEvaluationV1,
)
from hcam.analytics.anpr.guardrails import canonical_anpr_evidence_json  # noqa: E402


ARTIFACT_ROOT = Path(r"E:\h-cam-research-cache\phase-3\p3-5\artifacts")
RUNTIME_ROOT = Path(r"E:\h-cam-research-cache\phase-3\p3-5-runtime")
AUTHORIZATION_PATH = ROOT / "contracts" / "phase-3" / "p3-5-start-authorization.json"
EVIDENCE_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-auxiliary-script-evaluation.json"
)
WORKER_PATH = ROOT / "tools" / "phase35_auxiliary_ocr_worker.py"
RESULT_PREFIX = "HCAM_P35_W6_RESULT="
MAX_MEMBER_COUNT = 16
MAX_EXPANDED_BYTES = 16 * 1024 * 1024
MAX_EVIDENCE_BYTES = 128 * 1024
MAX_EVIDENCE_NODES = 8_192


@dataclass(frozen=True, slots=True)
class ModelProfile:
    candidate_id: str
    artifact_id: str
    archive_relative_path: str
    archive_sha256: str
    top_level: str
    member_sizes: dict[str, int]
    inference_yml_sha256: str
    extracted_inventory_sha256: str


MODEL_PROFILE = ModelProfile(
    candidate_id="OCR-D0",
    artifact_id="OCR-D0-PPOCRV5-DEVANAGARI-INFER-PROPOSED",
    archive_relative_path=(
        "OCR-D0-PPOCRV5-DEVANAGARI-INFER-PROPOSED/"
        "devanagari_PP-OCRv5_mobile_rec_infer.tar"
    ),
    archive_sha256=(
        "AC8279D27FC7E8CDA559364F9A3C506F43984CF6BA5E1B7A06450458BFE07DFB"
    ),
    top_level="devanagari_PP-OCRv5_mobile_rec_infer",
    member_sizes={
        "export_result.json": 114,
        "inference.json": 217_712,
        "inference.pdiparams": 7_836_203,
        "inference.yml": 5_027,
    },
    inference_yml_sha256=(
        "9BD172DD26440C8CE94D1CDE5D5BAEA6AEFDC7CF3C5C8492E0BEEDEF656D4E54"
    ),
    extracted_inventory_sha256=(
        "sha256:e7f6b0b7cf6e937e56540ba5254d6aed9a1958e5b3bca3a3e7c41b29673a2cb6"
    ),
)
FONT_PROFILES = {
    "FONT-D0": {
        "artifact_id": "FONT-D0-NOTO-SANS-DEVANAGARI-VARIABLE-PROPOSED",
        "relative_path": (
            "FONT-D0-NOTO-SANS-DEVANAGARI-VARIABLE-PROPOSED/"
            "NotoSansDevanagari-wdth-wght.ttf"
        ),
        "sha256": (
            "9CE7B04F60E363D8870E5997744CF85CF69D38A4D7D129D364D92A3B14B461D7"
        ),
        "bytes": 647_144,
    },
    "FONT-G0": {
        "artifact_id": "FONT-G0-NOTO-SANS-GUJARATI-VARIABLE-PROPOSED",
        "relative_path": (
            "FONT-G0-NOTO-SANS-GUJARATI-VARIABLE-PROPOSED/"
            "NotoSansGujarati-wdth-wght.ttf"
        ),
        "sha256": (
            "9901D8552F1DD5D2C50DBD4CAA6F6E174E74E8264F06594AB259AE6E7B1AC428"
        ),
        "bytes": 672_904,
    },
}


class AuxiliaryOcrToolError(RuntimeError):
    pass


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _load_authorization() -> dict[str, Any]:
    try:
        authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AuxiliaryOcrToolError("W6 authorization cannot be read") from exc
    runtime = authorization.get("allowed_runtime", {})
    if (
        authorization.get("decision_id") != "D-P3.5-START"
        or authorization.get("effective") is not True
        or "P35-W6_exact_Devanagari_Paddle_OCR_lane_and_Gujarati_font_rendering_only"
        not in authorization.get("allowed_work_packages", [])
        or authorization.get("allowed_network_actions") != []
        or runtime.get("network_access") is not False
        or runtime.get("external_runtime_root") != str(RUNTIME_ROOT)
        or runtime.get("direct_packages")
        != [
            "paddleocr==3.7.0",
            "paddlepaddle==3.3.1",
            "pillow==12.3.0",
            "regex==2026.7.19",
        ]
        or runtime.get("python_version") != "3.12.13"
        or runtime.get("repository_dependency_or_lockfile_change") is not False
        or runtime.get("tesseract_runtime_authorized") is not False
    ):
        raise AuxiliaryOcrToolError("effective W6 authorization is missing or changed")
    allowed = {
        item["candidate_id"]: item
        for item in authorization.get("allowed_artifacts", [])
    }
    expected = {
        "OCR-D0": (
            MODEL_PROFILE.artifact_id,
            MODEL_PROFILE.archive_sha256,
            [
                "safe_extract_in_external_local_quarantine",
                "load_for_generated_only_local_inference",
            ],
        ),
        **{
            candidate_id: (
                profile["artifact_id"],
                profile["sha256"],
                ["load_for_deterministic_generated_rendering"],
            )
            for candidate_id, profile in FONT_PROFILES.items()
        },
    }
    for candidate_id, (artifact_id, digest, actions) in expected.items():
        item = allowed.get(candidate_id)
        if (
            item is None
            or item.get("artifact_id") != artifact_id
            or item.get("sha256") != digest
            or item.get("allowed_actions") != actions
        ):
            raise AuxiliaryOcrToolError("exact W6 artifact authorization changed")
    blocked = {
        item.get("candidate_id")
        for item in authorization.get("blocked_reviewed_artifacts", [])
    }
    if blocked != {"OCR-G0", "OCR-G1"}:
        raise AuxiliaryOcrToolError("Gujarati OCR block changed")
    return authorization


def _validate_external_roots() -> tuple[Path, Path]:
    if ARTIFACT_ROOT.drive.upper() == "B:" or RUNTIME_ROOT.drive.upper() == "B:":
        raise AuxiliaryOcrToolError("B drive is prohibited")
    artifacts = ARTIFACT_ROOT.resolve(strict=True)
    runtime = RUNTIME_ROOT.resolve(strict=True)
    if ARTIFACT_ROOT.is_symlink() or RUNTIME_ROOT.is_symlink():
        raise AuxiliaryOcrToolError("W6 external roots cannot be symlinks")
    if artifacts != ARTIFACT_ROOT or runtime != RUNTIME_ROOT:
        raise AuxiliaryOcrToolError("W6 external roots changed")
    return artifacts, runtime


def _inspect_archive(path: Path) -> list[tarfile.TarInfo]:
    profile = MODEL_PROFILE
    if not path.is_file() or path.is_symlink() or _sha256(path) != profile.archive_sha256:
        raise AuxiliaryOcrToolError("exact W6 archive digest mismatch")
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
                    raise AuxiliaryOcrToolError("W6 archive member limit exceeded")
                pure = PurePosixPath(member.name)
                if pure.is_absolute() or ".." in pure.parts or not pure.parts:
                    raise AuxiliaryOcrToolError("W6 archive contains an unsafe path")
                normalized = pure.as_posix().rstrip("/")
                if member.isdir():
                    if member.size != 0:
                        raise AuxiliaryOcrToolError(
                            "W6 archive directory has a nonzero payload"
                        )
                    directories.add(normalized)
                elif member.isfile():
                    if normalized in observed_files:
                        raise AuxiliaryOcrToolError("W6 archive contains a duplicate file")
                    observed_files[normalized] = member.size
                    expanded += member.size
                else:
                    raise AuxiliaryOcrToolError(
                        "W6 archive contains a link or special entry"
                    )
                if member.size < 0 or expanded > MAX_EXPANDED_BYTES:
                    raise AuxiliaryOcrToolError("W6 archive expanded size exceeds limit")
    except (OSError, tarfile.TarError, UnicodeError) as exc:
        raise AuxiliaryOcrToolError("W6 archive inspection failed") from exc
    if observed_files != expected_files or directories != {profile.top_level}:
        raise AuxiliaryOcrToolError(
            "W6 archive inventory differs from the reviewed inventory"
        )
    return members


def _model_inventory(model_dir: Path) -> str:
    profile = MODEL_PROFILE
    if model_dir.is_symlink():
        raise AuxiliaryOcrToolError("extracted W6 model directory cannot be a symlink")
    resolved = model_dir.resolve(strict=True)
    observed: dict[str, Path] = {}
    for path in resolved.rglob("*"):
        if path.is_symlink():
            raise AuxiliaryOcrToolError("extracted W6 model contains a symlink")
        if path.is_dir():
            raise AuxiliaryOcrToolError("extracted W6 model contains an extra directory")
        if path.is_file():
            observed[path.relative_to(resolved).as_posix()] = path
    if set(observed) != set(profile.member_sizes):
        raise AuxiliaryOcrToolError("extracted W6 model inventory changed")
    digest = hashlib.sha256()
    for name in sorted(observed):
        path = observed[name]
        if path.stat().st_size != profile.member_sizes[name]:
            raise AuxiliaryOcrToolError("extracted W6 model member changed")
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(_sha256(path).encode("ascii"))
        digest.update(b"\0")
    observed_digest = f"sha256:{digest.hexdigest()}"
    if (
        observed_digest != profile.extracted_inventory_sha256
        or _sha256(resolved / "inference.yml") != profile.inference_yml_sha256
    ):
        raise AuxiliaryOcrToolError("extracted W6 model content changed")
    return observed_digest


def _verify_font(candidate_id: str, artifacts: Path) -> Path:
    profile = FONT_PROFILES[candidate_id]
    source = artifacts / profile["relative_path"]
    if source.is_symlink():
        raise AuxiliaryOcrToolError("W6 font cannot be a symlink")
    resolved = source.resolve(strict=True)
    if (
        not _inside(resolved, artifacts)
        or not resolved.is_file()
        or resolved.stat().st_size != profile["bytes"]
        or _sha256(resolved) != profile["sha256"]
    ):
        raise AuxiliaryOcrToolError("exact W6 font changed")
    return resolved


def _write_external_json(path: Path, value: object, runtime: Path) -> None:
    if path.parent.is_symlink() or path.is_symlink():
        raise AuxiliaryOcrToolError("external W6 evidence path cannot be a symlink")
    if not _inside(path.parent.resolve(strict=True), runtime):
        raise AuxiliaryOcrToolError("external W6 evidence escaped the runtime root")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def safe_extract_model() -> dict[str, Any]:
    _load_authorization()
    artifacts, runtime = _validate_external_roots()
    archive_source = artifacts / MODEL_PROFILE.archive_relative_path
    if archive_source.is_symlink():
        raise AuxiliaryOcrToolError("W6 archive cannot be a symlink")
    archive_path = archive_source.resolve(strict=True)
    if not _inside(archive_path, artifacts):
        raise AuxiliaryOcrToolError("W6 archive escaped the artifact root")
    members = _inspect_archive(archive_path)
    models_root = runtime / "models"
    evidence_root = runtime / "evidence"
    models_root.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)
    if models_root.is_symlink() or evidence_root.is_symlink():
        raise AuxiliaryOcrToolError("W6 runtime directories cannot be symlinks")
    candidate_root = models_root / "OCR-D0"
    model_dir = candidate_root / MODEL_PROFILE.top_level

    if candidate_root.exists():
        if not candidate_root.is_dir() or candidate_root.is_symlink():
            raise AuxiliaryOcrToolError("existing W6 candidate path is unsafe")
        if {path.name for path in candidate_root.iterdir()} != {MODEL_PROFILE.top_level}:
            raise AuxiliaryOcrToolError("existing W6 candidate root has extra entries")
        inventory = _model_inventory(model_dir)
        extracted_now = False
    else:
        temporary_root = models_root / f".extract-OCR-D0-{uuid.uuid4().hex}"
        temporary_root.mkdir()
        try:
            with tarfile.open(archive_path, mode="r:*") as archive:
                for member in members:
                    pure = PurePosixPath(member.name)
                    destination = temporary_root.joinpath(*pure.parts)
                    if not _inside(
                        destination.parent.resolve(strict=False),
                        temporary_root.resolve(strict=True),
                    ):
                        raise AuxiliaryOcrToolError(
                            "W6 extraction destination escaped quarantine"
                        )
                    if member.isdir():
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    source = archive.extractfile(member)
                    if source is None:
                        raise AuxiliaryOcrToolError("W6 archive member cannot be opened")
                    remaining = member.size
                    with source, destination.open("xb") as output:
                        while remaining:
                            chunk = source.read(min(1024 * 1024, remaining))
                            if not chunk:
                                raise AuxiliaryOcrToolError("W6 archive member is truncated")
                            output.write(chunk)
                            remaining -= len(chunk)
                        if source.read(1):
                            raise AuxiliaryOcrToolError(
                                "W6 archive member exceeds declared size"
                            )
            inventory = _model_inventory(temporary_root / MODEL_PROFILE.top_level)
            temporary_root.rename(candidate_root)
            extracted_now = True
        except Exception:
            if temporary_root.exists() and _inside(
                temporary_root.resolve(strict=False), models_root.resolve(strict=True)
            ):
                shutil.rmtree(temporary_root)
            raise

    receipt = {
        "contract_type": "hcam.phase3.p3_5.auxiliary-ocr-extraction-receipt.v1",
        "work_package": (
            "P35-W6_exact_Devanagari_Paddle_OCR_lane_and_Gujarati_font_rendering_only"
        ),
        "candidate_id": "OCR-D0",
        "artifact_id": MODEL_PROFILE.artifact_id,
        "archive_sha256": f"sha256:{MODEL_PROFILE.archive_sha256.lower()}",
        "extracted_inventory_sha256": inventory,
        "member_count": len(MODEL_PROFILE.member_sizes),
        "expanded_bytes": sum(MODEL_PROFILE.member_sizes.values()),
        "extracted_now": extracted_now,
        "external_runtime_only": True,
        "network_access_performed": False,
        "model_execution_performed": False,
    }
    _write_external_json(
        evidence_root / "p3-5-w6-ocr-d0-extraction.json",
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
    temporary = runtime / "temp" / "p3-5-w6"
    cache = runtime / "cache" / "p3-5-w6"
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


def build_evaluation(*, sample_count: int) -> AuxiliaryScriptGeneratedEvaluationV1:
    _load_authorization()
    if not 1 <= sample_count <= 12:
        raise AuxiliaryOcrToolError("W6 sample count exceeds the closed vocabulary")
    receipt = safe_extract_model()
    artifacts, runtime = _validate_external_roots()
    font_d0 = _verify_font("FONT-D0", artifacts)
    font_g0 = _verify_font("FONT-G0", artifacts)
    python = runtime / "venv" / "Scripts" / "python.exe"
    if not python.is_file() or python.is_symlink():
        raise AuxiliaryOcrToolError("exact W6 Python runtime is missing")
    completed = subprocess.run(
        [
            str(python),
            "-I",
            str(WORKER_PATH),
            "--model-dir",
            receipt["model_dir"],
            "--inventory-sha256",
            receipt["extracted_inventory_sha256"],
            "--font-d0",
            str(font_d0),
            "--font-g0",
            str(font_g0),
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
        raise AuxiliaryOcrToolError("isolated W6 worker failed")
    result_line = next(
        (
            line[len(RESULT_PREFIX) :]
            for line in reversed(completed.stdout.splitlines())
            if line.startswith(RESULT_PREFIX)
        ),
        None,
    )
    if result_line is None:
        raise AuxiliaryOcrToolError("isolated W6 worker emitted no result")
    try:
        return AuxiliaryScriptGeneratedEvaluationV1.model_validate_json(result_line)
    except ValueError as exc:
        raise AuxiliaryOcrToolError("isolated W6 result is invalid") from exc


def render_evaluation(evaluation: AuxiliaryScriptGeneratedEvaluationV1) -> str:
    return canonical_anpr_evidence_json(
        evaluation,
        maximum_bytes=MAX_EVIDENCE_BYTES,
        maximum_nodes=MAX_EVIDENCE_NODES,
    )


def check_evidence() -> int:
    try:
        actual = EVIDENCE_PATH.read_text(encoding="utf-8")
        parsed = AuxiliaryScriptGeneratedEvaluationV1.model_validate_json(actual)
        canonical = render_evaluation(parsed)
    except (OSError, ValueError) as exc:
        print(f"[fail] P3.5 W6 evidence: {exc}")
        return 1
    prohibited = (
        '"raw_text"',
        '"bgr_bytes"',
        '"sample_id"',
        '"region_id"',
        "anprauxsample_",
        "anprauxregion_",
    )
    if actual != canonical or any(item in actual for item in prohibited):
        print("[fail] P3.5 W6 evidence contains ephemeral auxiliary data")
        return 1
    print(f"[pass] {EVIDENCE_PATH.relative_to(ROOT)}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("extract")
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
            receipt = safe_extract_model()
            print(
                "[pass] OCR-D0 exact extraction "
                + receipt["extracted_inventory_sha256"]
            )
            return 0
        if args.command == "check-evidence":
            return check_evidence()
        if args.write_evidence and not args.acknowledge_generated_only_evidence:
            print("Refusing to write W6 evidence without generated-only acknowledgment")
            return 2
        evaluation = build_evaluation(sample_count=args.sample_count)
        rendered = render_evaluation(evaluation)
        if args.write_evidence:
            EVIDENCE_PATH.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"[write] {EVIDENCE_PATH.relative_to(ROOT)}")
        else:
            print(rendered, end="")
        return 0
    except (
        AuxiliaryOcrToolError,
        OSError,
        ValueError,
        subprocess.TimeoutExpired,
        tarfile.TarError,
    ) as exc:
        print(f"P3.5 W6 failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
