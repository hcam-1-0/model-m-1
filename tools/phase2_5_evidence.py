#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_ROOT = ROOT / "var" / "phase2-5"
EVIDENCE_SCHEMA = "hcam.phase2_5.generated_evidence.v1"


class EvidenceError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_paths() -> tuple[Path, ...]:
    candidates: list[Path] = []
    candidates.extend((ROOT / "app" / "hcam" / "labs" / "sentinel").rglob("*.py"))
    candidates.extend(
        (ROOT / "app" / "hcam" / "labs" / "sentinel" / "static").glob("*")
    )
    candidates.extend((ROOT / "deploy").glob("*phase2-5*"))
    candidates.extend((ROOT / "tests").glob("test_phase2_5_*.py"))
    candidates.extend((ROOT / "docs" / "phase-2-5").glob("*.md"))
    candidates.extend(
        (
            ROOT / "Dockerfile",
            ROOT / "pyproject.toml",
            ROOT / "tools" / "phase2_5_lab.py",
            ROOT / "tools" / "phase2_5_evidence.py",
        )
    )
    return tuple(
        sorted(
            {path.resolve() for path in candidates if path.is_file()},
            key=lambda item: item.relative_to(ROOT).as_posix(),
        )
    )


def package_manifest(
    paths: Iterable[Path] | None = None,
) -> tuple[list[dict[str, object]], str]:
    selected = tuple(paths or package_paths())
    if not selected:
        raise EvidenceError("package_files_missing")
    files = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in selected
    ]
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("ascii")
    return files, hashlib.sha256(canonical).hexdigest()


def _load_json(path: Path, *, maximum: int) -> dict[str, object]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise EvidenceError("evidence_input_invalid")
    try:
        document = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("evidence_input_invalid") from exc
    if not isinstance(document, dict):
        raise EvidenceError("evidence_input_invalid")
    return document


def fixture_checks(document: dict[str, object]) -> dict[str, bool]:
    fixtures = document.get("fixtures")
    if not isinstance(fixtures, list):
        raise EvidenceError("fixture_evidence_invalid")
    source_profiles = [
        item.get("source_profile")
        for item in fixtures
        if isinstance(item, dict) and isinstance(item.get("source_profile"), dict)
    ]
    probes = [
        item.get("probe")
        for item in fixtures
        if isinstance(item, dict) and isinstance(item.get("probe"), dict)
    ]
    timing = [
        probe.get("timing")
        for probe in probes
        if isinstance(probe, dict) and isinstance(probe.get("timing"), dict)
    ]
    fixture_names = {
        item.get("fixture_name") for item in fixtures if isinstance(item, dict)
    }
    codecs = {item.get("codec") for item in fixtures if isinstance(item, dict)}
    h264_probes = [
        item.get("probe")
        for item in fixtures
        if isinstance(item, dict)
        and item.get("codec") == "h264"
        and isinstance(item.get("probe"), dict)
    ]
    return {
        "classification_generated_only": document.get("classification")
        == "generated-only",
        "fixture_count_50": document.get("fixture_count") == 50 and len(fixtures) == 50,
        "unique_fixture_names_50": len(fixture_names) == 50,
        "active_default_30": sum(
            profile.get("active_by_default") is True
            for profile in source_profiles
            if isinstance(profile, dict)
        )
        == 30,
        "mixed_h264_hevc": codecs == {"h264", "hevc"},
        "all_probed": len(probes) == 50,
        "all_h264_no_b_frames": len(h264_probes) > 0
        and all(probe.get("has_b_frames") == 0 for probe in h264_probes),
        "all_timestamps_monotonic": len(timing) == 50
        and all(
            item.get("monotonic") is True for item in timing if isinstance(item, dict)
        ),
        "zero_retained_frames": len(timing) == 50
        and all(
            item.get("retained_frames") == 0
            for item in timing
            if isinstance(item, dict)
        ),
        "variable_pts_present": any(
            profile.get("timing_pattern") == "variable_pts"
            for profile in source_profiles
            if isinstance(profile, dict)
        ),
    }


def source_safety_checks() -> dict[str, bool]:
    runtime_paths = [
        *(ROOT / "app" / "hcam" / "labs" / "sentinel").rglob("*.py"),
        ROOT / "tools" / "phase2_5_lab.py",
        *(ROOT / "deploy").glob("*phase2-5*"),
    ]
    rendered = "\n".join(
        path.read_text(encoding="utf-8", errors="strict")
        for path in runtime_paths
        if path.is_file()
    )
    product_paths = [
        ROOT / "app" / "hcam" / "main.py",
        ROOT / "app" / "hcam" / "cli.py",
        *(ROOT / "app" / "hcam" / "camera_registry").glob("*.py"),
        *(ROOT / "app" / "hcam" / "streams").glob("*.py"),
        *(ROOT / "app" / "hcam" / "analytics").glob("*.py"),
    ]
    product_rendered = "\n".join(
        path.read_text(encoding="utf-8") for path in product_paths if path.is_file()
    )
    compose = (ROOT / "deploy" / "compose.phase2-5.yaml").read_text(encoding="utf-8")
    mediamtx = (ROOT / "deploy" / "mediamtx.phase2-5.yml").read_text(encoding="utf-8")
    sentinel_mediamtx = (
        ROOT / "deploy" / "mediamtx.phase2-5-sentinel.yml"
    ).read_text(encoding="utf-8")
    return {
        "production_host_absent": "sentinel.gujarat.gov.in" not in rendered,
        "exact_public_sandbox_catalogue": (
            "https://live.corp8.cloud/api/ingest" in compose
            and 'NetworkRule("https", "live.corp8.cloud", 443, "/api/ingest")'
            in rendered
        ),
        "product_does_not_import_lab": "hcam.labs" not in product_rendered,
        "recording_disabled": "record: false" in mediamtx
        and "record: false" in sentinel_mediamtx,
        "rtsp_tcp_only": "rtspTransports: [tcp]" in mediamtx
        and "rtspTransports: [tcp]" in sentinel_mediamtx,
        "catalogue_not_host_published": "8090:8090" not in compose,
        "rtsp_not_host_published": "8554:8554" not in compose
        and "8555:8555" not in compose,
        "private_external_gates_closed": "HCAM_PHASE2_5_EXTERNAL" not in rendered,
        "two_lab_profiles_declared": "lab1highadapter" in rendered
        and "lab2lowadapter" in rendered,
        "high_profile_not_downgraded": "quality_downgraded" in rendered
        and '"quality_downgraded": False' in rendered,
    }


def runtime_checks(dashboard_url: str) -> dict[str, bool]:
    url = f"{dashboard_url.rstrip('/')}/api/status"
    try:
        with urlopen(
            Request(url, headers={"Accept": "application/json"}), timeout=20
        ) as response:
            payload = response.read(1024 * 1024 + 1)
            classification = response.headers.get("X-HCAM-Data-Classification")
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise EvidenceError("runtime_dashboard_unavailable") from exc
    if len(payload) > 1024 * 1024:
        raise EvidenceError("runtime_dashboard_response_too_large")
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("runtime_dashboard_response_invalid") from exc
    counts = document.get("counts", {})
    boundaries = document.get("boundaries", {})
    adapter = document.get("adapter", {})
    publisher = document.get("publisher", {})
    return {
        "dashboard_generated_only": classification == "generated-only",
        "high_adapter_active": adapter.get("adapter_id") == "lab1highadapter",
        "catalogue_total_50": counts.get("total") == 50,
        "advertised_live_30": counts.get("advertised_live") == 30,
        "runtime_streams_30": publisher.get("active_stream_count") == 30,
        "runtime_stream_copy": publisher.get("stream_copy") is True,
        "runtime_quality_not_downgraded": publisher.get("quality_downgraded") is False,
        "test_dashboard_only": boundaries.get("test_dashboard_only") is True,
        "government_data_false": boundaries.get("government_data") is False,
        "recording_false": boundaries.get("recording") is False,
        "analytics_false": boundaries.get("analytics") is False,
    }


def git_state() -> dict[str, object]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "worktree_dirty": bool(status.stdout.strip())
        if status.returncode == 0
        else None,
    }


def build_evidence(
    state_root: Path,
    *,
    dashboard_url: str,
    require_runtime: bool,
) -> dict[str, object]:
    fixture_path = state_root / "media" / "fixture-evidence.json"
    if not fixture_path.is_file():
        fixture_path = state_root / "evidence" / "fixture-evidence.json"
    fixture_document = _load_json(fixture_path, maximum=8 * 1024 * 1024)
    files, package_digest = package_manifest()
    checks = {
        **fixture_checks(fixture_document),
        **source_safety_checks(),
    }
    runtime: dict[str, bool] | None = None
    if require_runtime:
        runtime = runtime_checks(dashboard_url)
        checks.update(runtime)
    if not all(checks.values()):
        raise EvidenceError("phase2_5_evidence_check_failed")
    retained_fixture_path = state_root / "evidence" / "fixture-evidence.json"
    retained_fixture_path.parent.mkdir(parents=True, exist_ok=True)
    retained_fixture_path.write_text(
        json.dumps(fixture_document, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    document: dict[str, object] = {
        "schema": EVIDENCE_SCHEMA,
        "classification": "generated-only",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "scope": "phase2-5-generated-lab-g0-g5",
        "external_gates": {
            "G6": "separate_online_evidence",
            "G7": "separate_online_evidence",
            "G8": "closed",
        },
        "package_digest_sha256": package_digest,
        "package_files": files,
        "fixture_evidence_sha256": _sha256(retained_fixture_path),
        "fixture_count": fixture_document.get("fixture_count"),
        "checks": checks,
        "runtime_checks": runtime,
        "git": git_state(),
        "limitations": {
            "external_access": False,
            "government_data": False,
            "recording": False,
            "analytics": False,
            "deployment": False,
        },
    }
    output = state_root / "evidence" / "phase2-5-evidence.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    document["evidence_path"] = str(output.resolve())
    return document


def check_evidence(state_root: Path) -> dict[str, object]:
    evidence_path = state_root / "evidence" / "phase2-5-evidence.json"
    document = _load_json(evidence_path, maximum=8 * 1024 * 1024)
    files, package_digest = package_manifest()
    del files
    fixture_path = state_root / "evidence" / "fixture-evidence.json"
    checks = document.get("checks")
    valid = (
        document.get("schema") == EVIDENCE_SCHEMA
        and document.get("classification") == "generated-only"
        and document.get("package_digest_sha256") == package_digest
        and document.get("fixture_evidence_sha256") == _sha256(fixture_path)
        and isinstance(checks, dict)
        and all(value is True for value in checks.values())
    )
    if not valid:
        raise EvidenceError("phase2_5_evidence_drift")
    return {
        "valid": True,
        "classification": "generated-only",
        "package_digest_sha256": package_digest,
        "evidence_path": str(evidence_path.resolve()),
        "external_gates": document.get("external_gates"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or verify Phase 2.5 generated-only evidence"
    )
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE_ROOT)
    parser.add_argument("--dashboard-url", default="http://127.0.0.1:8091")
    parser.add_argument("--require-runtime", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build_evidence(
                args.state_root,
                dashboard_url=args.dashboard_url,
                require_runtime=args.require_runtime,
            )
            output = {
                "classification": result["classification"],
                "evidence_path": result["evidence_path"],
                "external_gates": result["external_gates"],
                "fixture_count": result["fixture_count"],
                "package_digest_sha256": result["package_digest_sha256"],
                "runtime_verified": result["runtime_checks"] is not None,
            }
        else:
            output = check_evidence(args.state_root)
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except (EvidenceError, OSError, ValueError) as exc:
        code = getattr(exc, "code", "phase2_5_evidence_failed")
        print(f"Phase 2.5 evidence failed ({code})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
