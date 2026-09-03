#!/usr/bin/env python3
"""Generate and verify the offline, generated-only P3.1 evidence package."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path

from pydantic import BaseModel

from hcam.analytics.evaluation.baseline import (
    build_baseline_evidence,
    rendered_json_bytes,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "phase-3" / "p3-1"
FIXTURE_GENERATOR = ROOT / "app" / "hcam" / "analytics" / "evaluation" / "fixtures.py"
DEPENDENCY_LOCK = ROOT / "uv.lock"
MAX_ARTIFACT_BYTES = 1024 * 1024
MAX_DIFF_LINES = 200


class EvidenceGenerationError(RuntimeError):
    """Raised when local evidence inputs cannot be established."""


def _file_digest(path: Path) -> str:
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise EvidenceGenerationError(
            f"required evidence input is unavailable: {path.name}"
        ) from exc
    # Evidence must not drift solely because Git materialized text with CRLF.
    content = content.replace(b"\r\n", b"\n")
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _git_output(arguments: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EvidenceGenerationError("git metadata is unavailable") from exc
    if result.returncode != 0:
        raise EvidenceGenerationError("git metadata command failed")
    return result.stdout.strip()


def _validate_commit(commit: str) -> str:
    if len(commit) not in {40, 64} or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise EvidenceGenerationError("source commit is invalid")
    return commit


def source_state() -> tuple[str, bool]:
    commit = _validate_commit(_git_output(["rev-parse", "HEAD"]))
    dirty = bool(_git_output(["status", "--porcelain=v1", "--untracked-files=all"]))
    return commit, dirty


def recorded_source_state() -> tuple[str, bool]:
    path = CONTRACT_ROOT / "evaluation-run-v1.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        source = document["source"]
        commit = source["commit"]
        dirty = source["dirty_worktree"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise EvidenceGenerationError(
            "recorded baseline source state is unavailable"
        ) from exc
    if not isinstance(commit, str) or not isinstance(dirty, bool):
        raise EvidenceGenerationError("recorded baseline source state is invalid")
    return _validate_commit(commit), dirty


def recorded_input_digests() -> tuple[str, str]:
    """Return the immutable inputs bound into the accepted P3.1 evidence."""
    try:
        fixture_manifest = json.loads(
            (CONTRACT_ROOT / "fixture-manifest-v1.json").read_text(encoding="utf-8")
        )
        evaluation_run = json.loads(
            (CONTRACT_ROOT / "evaluation-run-v1.json").read_text(encoding="utf-8")
        )
        generator_digest = fixture_manifest["generator"]["code_digest"]
        dependency_digest = evaluation_run["dependency_lock_digest"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise EvidenceGenerationError(
            "recorded evidence input digests are unavailable"
        ) from exc
    for value in (generator_digest, dependency_digest):
        if not isinstance(value, str) or not re.fullmatch(
            r"sha256:[0-9a-f]{64}", value
        ):
            raise EvidenceGenerationError("recorded evidence input digest is invalid")
    return generator_digest, dependency_digest


def _json_document(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    return value


def _serialized(value: object) -> str:
    return rendered_json_bytes(_json_document(value)).decode("utf-8")


def render_contracts(
    *,
    source_commit: str | None = None,
    dirty_worktree: bool | None = None,
    generator_code_digest: str | None = None,
    dependency_lock_digest: str | None = None,
) -> dict[Path, str]:
    detected_commit, detected_dirty = recorded_source_state()
    commit = source_commit or detected_commit
    dirty = detected_dirty if dirty_worktree is None else dirty_worktree
    recorded_generator, recorded_dependency = recorded_input_digests()
    evidence = build_baseline_evidence(
        source_commit=commit,
        dirty_worktree=dirty,
        generator_code_digest=generator_code_digest or recorded_generator,
        dependency_lock_digest=dependency_lock_digest or recorded_dependency,
        container_profile_digest=None,
    )
    rendered: dict[Path, str] = {}
    for name, value in evidence.items():
        if name == "generated":
            assert isinstance(value, dict)
            for artifact_name, document in value.items():
                rendered[CONTRACT_ROOT / "generated" / artifact_name] = _serialized(
                    document
                )
        elif name == "candidates":
            assert isinstance(value, dict)
            for candidate_id, manifest in value.items():
                artifact_name = f"candidate-{candidate_id.lower()}.json"
                rendered[CONTRACT_ROOT / "candidates" / artifact_name] = _serialized(
                    manifest
                )
        else:
            rendered[CONTRACT_ROOT / name] = _serialized(value)
    return dict(sorted(rendered.items(), key=lambda item: item[0].as_posix()))


def _validate_artifact(path: Path, document: str) -> list[str]:
    failures: list[str] = []
    try:
        relative = path.relative_to(CONTRACT_ROOT)
    except ValueError:
        return ["artifact escapes the P3.1 contract root"]
    if path.suffix != ".json" or any(part.startswith(".") for part in relative.parts):
        failures.append("artifact must be a visible JSON record")
    encoded = document.encode("utf-8")
    if not encoded or len(encoded) > MAX_ARTIFACT_BYTES:
        failures.append("artifact violates the one MiB record bound")
    try:
        parsed = json.loads(document)
    except json.JSONDecodeError:
        failures.append("artifact is not valid JSON")
    else:
        if not isinstance(parsed, dict):
            failures.append("artifact root must be an object")
    return failures


def _diff(path: Path, expected: str, actual: str) -> list[str]:
    lines = list(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile=f"tracked/{path.name}",
            tofile=f"current/{path.name}",
            lineterm="",
        )
    )
    if len(lines) > MAX_DIFF_LINES:
        return [
            *lines[:MAX_DIFF_LINES],
            f"... {len(lines) - MAX_DIFF_LINES} diff lines omitted",
        ]
    return lines


def _document_digest(document: str) -> str:
    return hashlib.sha256(document.encode("utf-8")).hexdigest()


def check_contracts(*, require_clean_source: bool) -> int:
    try:
        source_commit, dirty = recorded_source_state()
        current_commit, current_dirty = source_state()
        rendered = render_contracts(
            source_commit=source_commit,
            dirty_worktree=dirty,
        )
    except EvidenceGenerationError as exc:
        print(f"[fail] {exc}")
        return 1
    failures = 0
    print(
        f"[pass] recorded baseline source commit={source_commit} "
        f"dirty={str(dirty).lower()}"
    )
    print(
        f"[pass] current source commit={current_commit} "
        f"dirty={str(current_dirty).lower()}"
    )
    if require_clean_source:
        if dirty:
            print("[fail] clean-source gate: recorded baseline worktree was dirty")
            failures += 1
        if current_dirty:
            print("[fail] clean-source gate: current worktree is dirty")
            failures += 1

    expected_paths = set(rendered)
    tracked_paths = (
        set(CONTRACT_ROOT.rglob("*.json")) if CONTRACT_ROOT.exists() else set()
    )
    unexpected = sorted(tracked_paths - expected_paths)
    for path in unexpected:
        print(f"[fail] unexpected P3.1 JSON artifact: {path.relative_to(ROOT)}")
        failures += 1

    for path, actual in rendered.items():
        safety_failures = _validate_artifact(path, actual)
        if safety_failures:
            for failure in safety_failures:
                print(f"[fail] {path.relative_to(ROOT)}: {failure}")
            failures += len(safety_failures)
            continue
        try:
            expected = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[fail] {path.relative_to(ROOT)}: {exc}")
            failures += 1
            continue
        if expected != actual:
            print(f"[fail] {path.relative_to(ROOT)} drifted")
            for line in _diff(path, expected, actual):
                print(line)
            failures += 1
            continue
        print(f"[pass] {path.relative_to(ROOT)} sha256={_document_digest(actual)}")

    print(
        "P3.1 evidence summary: "
        f"artifacts={len(rendered)} failures={failures} "
        "network=denied gpu=denied downloads=0 media=0"
    )
    return 1 if failures else 0


def write_contracts(*, acknowledged: bool) -> int:
    if not acknowledged:
        print(
            "Refusing to write P3.1 evidence without "
            "--acknowledge-generated-only-evidence"
        )
        return 2
    try:
        source_commit, dirty = source_state()
        rendered = render_contracts(
            source_commit=source_commit,
            dirty_worktree=dirty,
            generator_code_digest=_file_digest(FIXTURE_GENERATOR),
            dependency_lock_digest=_file_digest(DEPENDENCY_LOCK),
        )
    except EvidenceGenerationError as exc:
        print(f"[fail] {exc}")
        return 1
    failures = 0
    for path, document in rendered.items():
        artifact_failures = _validate_artifact(path, document)
        if artifact_failures:
            for failure in artifact_failures:
                print(f"[fail] {path.relative_to(ROOT)}: {failure}")
            failures += len(artifact_failures)
    if failures:
        return 1
    for path, document in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(document, encoding="utf-8", newline="\n")
        print(f"[write] {path.relative_to(ROOT)} sha256={_document_digest(document)}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify generated-only H-CAM P3.1 contracts and baseline evidence."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser(
        "check", help="Fail when tracked P3.1 evidence drifts"
    )
    check.add_argument(
        "--require-clean-source",
        action="store_true",
        help="Also require a clean Git worktree for final reproducibility evidence",
    )
    write = subparsers.add_parser(
        "write",
        help="Rewrite P3.1 evidence after reviewing generated-only inputs",
    )
    write.add_argument("--acknowledge-generated-only-evidence", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "check":
        return check_contracts(require_clean_source=args.require_clean_source)
    return write_contracts(acknowledged=args.acknowledge_generated_only_evidence)


if __name__ == "__main__":
    raise SystemExit(main())
