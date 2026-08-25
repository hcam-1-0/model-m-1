#!/usr/bin/env python3
"""Verify the bounded P3.3 generated-only tracking evidence package."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from hcam.analytics.activation import (
    P3_3_CONFIGURATION_VERSION,
    P3_3_PIPELINE_VERSION,
    P3_3_POLICY_VERSION,
    P3_3_TRACKER_VERSION,
)
from hcam.analytics.models import (
    AnalyticsTrackerEpoch,
    AnalyticsTrack,
    AnalyticsTrackLifecycle,
    AnalyticsTrackingRun,
)
from hcam.analytics.tracking import TrackerConfiguration
from hcam.analytics.tracking.generated_sequences import GENERATOR_VERSION
from hcam.settings import Settings
try:
    from tools.phase33_sbom import SBOM_PATH, validate as validate_sbom
    from tools.phase33_tracking_evidence import REPORT, _validate_report
except ModuleNotFoundError:  # Direct execution places tools/ on sys.path.
    from phase33_sbom import SBOM_PATH, validate as validate_sbom
    from phase33_tracking_evidence import REPORT, _validate_report


ROOT = Path(__file__).resolve().parents[1]
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"
ACCEPTANCE_PATH = ROOT / "contracts" / "phase-3" / "p3-3-acceptance.json"
VALIDATION_PATH = ROOT / "contracts" / "phase-3" / "p3-3-validation-evidence.json"

PACKAGE_FILES = (
    ".github/workflows/python-ci.yml",
    "MANIFEST.in",
    "app/hcam/analytics/activation.py",
    "app/hcam/analytics/contracts.py",
    "app/hcam/analytics/fixtures.py",
    "app/hcam/analytics/models.py",
    "app/hcam/analytics/repository.py",
    "app/hcam/analytics/routes.py",
    "app/hcam/analytics/schemas.py",
    "app/hcam/analytics/service.py",
    "app/hcam/analytics/tracking/__init__.py",
    "app/hcam/analytics/tracking/bytetrack.py",
    "app/hcam/analytics/tracking/generated_sequences.py",
    "app/hcam/analytics/tracking/kalman.py",
    "app/hcam/analytics/tracking/lanes.py",
    "app/hcam/analytics/tracking/matching.py",
    "app/hcam/analytics/tracking/metrics.py",
    "app/hcam/analytics/tracking/types.py",
    "app/hcam/analytics/tracking_execution.py",
    "app/hcam/database.py",
    "app/hcam/main.py",
    "app/hcam/metrics.py",
    "app/hcam/settings.py",
    "contracts/phase-3/analytics-contracts.json",
    "contracts/phase-3/database.json",
    "contracts/phase-3/fixtures/track-lifecycle-v2.json",
    "contracts/phase-3/openapi.json",
    "contracts/phase-3/p3-3-evaluator-source.json",
    "contracts/phase-3/p3-3-generated-suite.json",
    "contracts/phase-3/p3-3-planning-authorization.json",
    "contracts/phase-3/p3-3-runtime-profile.json",
    "contracts/phase-3/p3-3-sbom.cdx.json",
    "contracts/phase-3/p3-3-tracker-policy.json",
    "contracts/phase-3/p3-3-tracker-source.json",
    "contracts/phase-3/p3-3-validation-evidence.json",
    "contracts/phase-3/p3-3-work-authorization.json",
    "contracts/phase-3/p3-3/evaluation-report.json",
    "docs/phase-3/README.md",
    "docs/phase-3/decision-register.md",
    "docs/phase-3/implementation-backlog.md",
    "docs/phase-3/p3-3-implementation.md",
    "docs/phase-3/p3-3-plan.md",
    "docs/phase-3/p3-3-third-party-notices.md",
    "docs/phase-3/p3-3-work-authorization.md",
    "migrations/versions/0010_generated_tracking.py",
    "pyproject.toml",
    "tests/test_analytics_assignment_migration.py",
    "tests/test_analytics_contracts.py",
    "tests/test_analytics_tracking.py",
    "tests/test_phase31_readiness.py",
    "tests/test_phase32_implementation_readiness.py",
    "tests/test_phase33_implementation_readiness.py",
    "tests/test_phase3_readiness.py",
    "tests/test_postgres_integration.py",
    "tests/test_release_contracts.py",
    "tools/phase32_implementation_readiness.py",
    "tools/phase33_implementation_readiness.py",
    "tools/phase33_sbom.py",
    "tools/phase33_tracking_evidence.py",
    "tools/phase3_readiness.py",
    "tools/release_contracts.py",
    "uv.lock",
)


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    status: str
    detail: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Report:
    status: str
    scope: str
    package_digest: str
    failures: int
    manual_gates: int
    checks: tuple[Check, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scope": self.scope,
            "package_digest": self.package_digest,
            "failures": self.failures,
            "manual_gates": self.manual_gates,
            "checks": [asdict(check) for check in self.checks],
        }


def _json(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain an object")
    return document


def _canonical_digest(relative_path: str) -> str:
    payload = json.dumps(
        _json(ROOT / relative_path),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _file_digest(relative_path: str) -> str:
    payload = (ROOT / relative_path).read_bytes().replace(b"\r\n", b"\n")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def package_digest() -> tuple[str, tuple[str, ...]]:
    digest = hashlib.sha256()
    manifest: list[str] = []
    for relative_path in sorted(PACKAGE_FILES):
        payload = (ROOT / relative_path).read_bytes().replace(b"\r\n", b"\n")
        file_digest = hashlib.sha256(payload).hexdigest()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
        manifest.append(
            f"{relative_path} sha256={file_digest} bytes={len(payload)}"
        )
    return digest.hexdigest().upper(), tuple(manifest)


def check_required_files() -> Check:
    missing = tuple(path for path in PACKAGE_FILES if not (ROOT / path).is_file())
    if missing:
        return Check("required_files", FAIL, "P3.3 package files are missing.", missing)
    return Check(
        "required_files",
        PASS,
        f"All {len(PACKAGE_FILES)} P3.3 package files exist.",
    )


def check_work_authorization() -> Check:
    try:
        record = _json(ROOT / "contracts/phase-3/p3-3-work-authorization.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("work_authorization", FAIL, str(exc))
    required_work = {
        "generated_only_stream_local_tracking_implementation",
        "local_database_migrations_and_tests",
        "local_git_checkpoint_commits",
        "evidence_generation_and_digest_freeze",
    }
    prohibited = {
        "physical_camera_or_media_access",
        "external_public_private_or_government_dataset_use",
        "biometric_or_reidentification_processing",
        "cross_camera_linkage",
        "pilot_or_production_deployment",
        "remote_git_push_pull_request_or_merge",
    }
    if (
        record.get("authorization_id") != "D-P3.3-WORK-AUTH"
        or record.get("authorized") is not True
        or record.get("implementation_authorized") is not True
        or record.get("final_acceptance_granted") is not False
        or not required_work.issubset(set(record.get("authorized_work", [])))
        or not prohibited.issubset(set(record.get("prohibited_work", [])))
    ):
        return Check("work_authorization", FAIL, "P3.3 work boundary changed.")
    return Check(
        "work_authorization",
        PASS,
        "Generated-only P3.3 implementation and local evidence work are authorized.",
    )


def check_artifact_bindings() -> Check:
    tracker = _json(ROOT / "contracts/phase-3/p3-3-tracker-source.json")
    expected = (
        (P3_3_TRACKER_VERSION, tracker.get("canonical_selected_source_digest")),
        (
            P3_3_POLICY_VERSION,
            _file_digest("contracts/phase-3/p3-3-tracker-policy.json"),
        ),
        (
            P3_3_PIPELINE_VERSION,
            _canonical_digest("contracts/phase-3/p3-3-runtime-profile.json"),
        ),
        (
            GENERATOR_VERSION,
            _canonical_digest("contracts/phase-3/p3-3-generated-suite.json"),
        ),
        (P3_3_CONFIGURATION_VERSION, TrackerConfiguration().digest),
    )
    failures = tuple(
        f"binding[{index}]" for index, (actual, wanted) in enumerate(expected) if actual != wanted
    )
    if failures:
        return Check("artifact_bindings", FAIL, "P3.3 digest binding drifted.", failures)
    return Check(
        "artifact_bindings",
        PASS,
        "Tracker, policy, runtime, generator, and configuration are digest-bound.",
    )


def check_evaluation() -> Check:
    try:
        document = _json(REPORT)
        failures = tuple(_validate_report(document))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("generated_evaluation", FAIL, str(exc))
    if failures:
        return Check("generated_evaluation", FAIL, "Evaluation gates failed.", failures)
    return Check(
        "generated_evaluation",
        PASS,
        "Generated HOTA/IDF1, determinism, parity, and overload gates pass.",
    )


def check_sbom() -> Check:
    try:
        document = _json(SBOM_PATH)
        failures = tuple(validate_sbom(document))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("sbom", FAIL, str(exc))
    if failures:
        return Check("sbom", FAIL, "P3.3 SBOM validation failed.", failures)
    components = document.get("components", [])
    return Check(
        "sbom",
        PASS,
        f"Deterministic CycloneDX SBOM contains {len(components)} audited components.",
    )


def check_structural_boundaries() -> Check:
    prohibited = {
        "biometric",
        "embedding",
        "face",
        "global",
        "identity",
        "image",
        "media",
        "plate",
        "reid",
        "video",
        "watchlist",
    }
    failures: list[str] = []
    for model in (
        AnalyticsTrackingRun,
        AnalyticsTrackerEpoch,
        AnalyticsTrack,
        AnalyticsTrackLifecycle,
    ):
        columns = {column.name.lower() for column in model.__table__.columns}
        if any(token in column for column in columns for token in prohibited):
            failures.append(model.__tablename__)
    if Settings(environment="test").analytics_generated_tracking_enabled:
        failures.append("default-on")
    try:
        Settings(
            environment="production",
            database_url="postgresql+psycopg://hcam@db/hcam",
            analytics_generated_tracking_enabled=True,
        )
    except ValueError:
        pass
    else:
        failures.append("production-enabled")
    if failures:
        return Check(
            "structural_boundaries",
            FAIL,
            "Generated-only tracking boundaries failed.",
            tuple(failures),
        )
    return Check(
        "structural_boundaries",
        PASS,
        "Storage is media/identity-free; runtime is default-off and production-forbidden.",
    )


def check_validation_evidence() -> Check:
    try:
        document = _json(VALIDATION_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("validation_evidence", FAIL, str(exc))
    results = document.get("results")
    failures: list[str] = []
    if document.get("scope") != "generated_structured_observations_only":
        failures.append("scope")
    if document.get("prohibited_input_count") != 0:
        failures.append("prohibited_input_count")
    if not isinstance(results, dict):
        failures.append("results")
    else:
        required_passes = {
            "archive_boundary",
            "build_and_isolated_install",
            "compile",
            "dependency_audit",
            "full_suite",
            "postgresql",
            "ruff",
            "tracking_evidence",
        }
        for name in required_passes:
            item = results.get(name)
            if not isinstance(item, dict) or item.get("status") != "pass":
                failures.append(name)
        coverage = results.get("coverage")
        if (
            not isinstance(coverage, dict)
            or coverage.get("status") != "pass"
            or float(coverage.get("branch_percent", 0)) < 90
        ):
            failures.append("coverage")
    if failures:
        return Check(
            "validation_evidence",
            FAIL,
            "P3.3 validation evidence is incomplete.",
            tuple(failures),
        )
    return Check(
        "validation_evidence",
        PASS,
        "Tests, PostgreSQL, coverage, build, audit, and boundary scans pass.",
    )


def check_clean_source() -> Check:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--", *PACKAGE_FILES],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return Check("clean_source", FAIL, "Git clean-source check failed.")
    dirty = tuple(line for line in completed.stdout.splitlines() if line.strip())
    if dirty:
        return Check(
            "clean_source",
            FAIL,
            "P3.3 package files are not committed cleanly.",
            dirty,
        )
    return Check("clean_source", PASS, "P3.3 package files are clean in Git.")


def check_owner_acceptance() -> Check:
    if not ACCEPTANCE_PATH.is_file():
        return Check(
            "owner_acceptance",
            MANUAL,
            "mayank-admin must accept the exact final package digest.",
        )
    record = _json(ACCEPTANCE_PATH)
    digest, _ = package_digest()
    if (
        record.get("decision_id") == "D-P3.3-ACCEPTANCE"
        and record.get("status") == "accepted"
        and record.get("accepted_by") == "mayank-admin"
        and record.get("evidence_package_digest") == digest
    ):
        return Check("owner_acceptance", PASS, "Owner accepted this exact package.")
    return Check(
        "owner_acceptance",
        FAIL,
        "P3.3 acceptance record does not match the current package digest.",
    )


def build_report(*, require_clean_source: bool) -> Report:
    checks = [
        check_required_files(),
        check_work_authorization(),
        check_artifact_bindings(),
        check_evaluation(),
        check_sbom(),
        check_structural_boundaries(),
        check_validation_evidence(),
    ]
    if require_clean_source:
        checks.append(check_clean_source())
    checks.append(check_owner_acceptance())
    failures = sum(check.status == FAIL for check in checks)
    manual_gates = sum(check.status == MANUAL for check in checks)
    status = (
        "blocked"
        if failures
        else "ready_for_owner_acceptance"
        if manual_gates
        else "accepted"
    )
    digest, _ = package_digest()
    return Report(
        status=status,
        scope="phase3.p3_3.generated_only_stream_local_anonymous_tracking",
        package_digest=digest,
        failures=failures,
        manual_gates=manual_gates,
        checks=tuple(checks),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-clean-source", action="store_true")
    parser.add_argument("--require-acceptance", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(require_clean_source=args.require_clean_source)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(
            f"P3.3 implementation: {report.status}; failures={report.failures}; "
            f"manual_gates={report.manual_gates}; digest={report.package_digest}"
        )
        for check in report.checks:
            print(f"[{check.status}] {check.name}: {check.detail}")
    if report.failures:
        return 1
    if args.require_acceptance and report.manual_gates:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
