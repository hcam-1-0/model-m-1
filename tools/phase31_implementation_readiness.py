#!/usr/bin/env python3
"""Offline readiness verifier for the P3.1 implementation evidence package."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from hcam.analytics.evaluation.annotations import AnnotationQaReportV1
from hcam.analytics.evaluation.candidates import SourceResearchDossierV1
from hcam.analytics.evaluation.contracts import (
    CandidateArtifactManifestV1,
    DatasetManifestV1,
    EvaluationRunManifestV1,
    FixtureManifestV1,
    MetricReportV1,
    canonical_digest,
)
from hcam.analytics.evaluation.splits import SplitValidationReportV1

try:
    from tools import phase31_contracts
except ModuleNotFoundError:  # Direct script execution adds tools/, not the repo root.
    import phase31_contracts


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "contracts" / "phase-3" / "p3-1"
ACCEPTANCE_PATH = ROOT / "contracts" / "phase-3" / "p3-1-acceptance.json"
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"

ACCEPTED_PACKAGE_DIGEST = "956F6521E21BF0FB43741F97768194617DE881B1BD1644E03DDC33ED5FDC0618"
ACCEPTED_REPOSITORY_HEAD = "ccaef84993cbe3dee3e78692dd40a305bc2baea4"
BASELINE_SOURCE_COMMIT = "be7749d4315f46a49370b65f14c6e583e51a0c6e"
CLEAN_EVIDENCE_COMMIT = "e379ff028882295d82fbc82cff33aa11a100008e"
ACCEPTANCE_STATEMENT = (
    "I, mayank-admin, accept D-P3.1-ACCEPTANCE for package digest "
    f"{ACCEPTED_PACKAGE_DIGEST}, including its generated-only evidence and documented "
    "limitations. This does not authorize P3.2, model or dataset downloads, inference, "
    "cameras or media, Government/private data, or deployment."
)
ACCEPTANCE_RECORD = {
    "accepted_by": "mayank-admin",
    "accepted_on": "2026-08-24",
    "accepted_repository_head": ACCEPTED_REPOSITORY_HEAD,
    "baseline_source_commit": BASELINE_SOURCE_COMMIT,
    "clean_evidence_commit": CLEAN_EVIDENCE_COMMIT,
    "contract_format": "hcam.phase3.p3_1.acceptance.v1",
    "documented_limitations_accepted": True,
    "evidence_package_digest": ACCEPTED_PACKAGE_DIGEST,
    "evidence_profile": {
        "external_downloads": 0,
        "generated_only": True,
        "gpu_required": False,
        "media_artifacts": 0,
        "model_artifacts": 0,
        "network_required": False,
        "secrets_required": False,
    },
    "non_authorization": [
        "p3_2",
        "model_or_dataset_downloads",
        "inference",
        "cameras_or_media",
        "government_or_private_data",
        "deployment",
    ],
    "record_id": "D-P3.1-ACCEPTANCE",
    "scope": "phase3.p3_1.data_and_evaluation_foundation.implementation",
    "statement": ACCEPTANCE_STATEMENT,
    "status": "accepted",
}

ROOT_ARTIFACTS = (
    "annotation-qa-report-v1.json",
    "annotation-specification-v1.json",
    "dataset-manifest-v1.json",
    "evaluation-contracts.json",
    "evaluation-run-v1.json",
    "evidence-index.json",
    "fixture-manifest-v1.json",
    "metric-report-v1.json",
    "source-research-dossier-v1.json",
    "split-validation-report-v1.json",
)
CANDIDATE_IDS = (
    "DET-A1",
    "DET-B1",
    "DET-E1",
    "DET-R0",
    "OCR-D0",
    "OCR-G0",
    "OCR-G1",
    "OCR-L0",
    "OCR-L1",
    "PLATE-D0",
    "TRK-R0",
)
GENERATED_ARTIFACTS = (
    "annotation-items-v1.json",
    "detection-v1.json",
    "geometry-v1.json",
    "misuse-v1.json",
    "split-items-v1.json",
    "synthetic-plate-v1.json",
    "tracking-v1.json",
)
IMPLEMENTATION_FILES = (
    "app/hcam/analytics/evaluation/__init__.py",
    "app/hcam/analytics/evaluation/annotations.py",
    "app/hcam/analytics/evaluation/baseline.py",
    "app/hcam/analytics/evaluation/candidates.py",
    "app/hcam/analytics/evaluation/contracts.py",
    "app/hcam/analytics/evaluation/fixtures.py",
    "app/hcam/analytics/evaluation/metrics.py",
    "app/hcam/analytics/evaluation/splits.py",
    "tools/phase31_contracts.py",
    "tools/phase31_implementation_readiness.py",
    "tests/test_analytics_evaluation_contracts.py",
    "tests/test_analytics_generated_evaluation.py",
    "tests/test_phase31_evidence_contracts.py",
    "tests/test_phase31_implementation_readiness.py",
    "docs/phase-3/p3-1-implementation-readiness-report.md",
    "docs/phase-3/p3-1-acceptance.md",
    "contracts/phase-3/p3-1-acceptance.json",
    ".github/workflows/python-ci.yml",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str
    evidence: list[str]


@dataclass(frozen=True)
class ReadinessReport:
    status: str
    scope: str
    package_digest: str
    failures: int
    manual_gates: int
    checks: list[CheckResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scope": self.scope,
            "package_digest": self.package_digest,
            "failures": self.failures,
            "manual_gates": self.manual_gates,
            "checks": [asdict(check) for check in self.checks],
        }


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("JSON root must be an object")
    return document


def expected_artifact_paths() -> tuple[Path, ...]:
    paths = [EVIDENCE_ROOT / name for name in ROOT_ARTIFACTS]
    paths.extend(
        EVIDENCE_ROOT / "candidates" / f"candidate-{candidate_id.lower()}.json"
        for candidate_id in CANDIDATE_IDS
    )
    paths.extend(EVIDENCE_ROOT / "generated" / name for name in GENERATED_ARTIFACTS)
    return tuple(sorted(paths, key=lambda path: path.as_posix()))


def package_digest() -> tuple[str, list[str]]:
    digest = hashlib.sha256()
    manifest: list[str] = []
    for path in expected_artifact_paths():
        content = path.read_bytes()
        relative = _relative(path)
        file_digest = hashlib.sha256(content).hexdigest()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
        manifest.append(f"{relative} sha256={file_digest} bytes={len(content)}")
    return digest.hexdigest().upper(), manifest


def check_required_files() -> CheckResult:
    expected = [*expected_artifact_paths(), *(ROOT / path for path in IMPLEMENTATION_FILES)]
    missing = [_relative(path) for path in expected if not path.is_file()]
    if missing:
        return CheckResult(
            "required_files",
            FAIL,
            f"Missing {len(missing)} required implementation or evidence files.",
            missing,
        )
    return CheckResult(
        "required_files",
        PASS,
        f"All {len(expected)} required implementation and evidence files exist.",
        [_relative(path) for path in expected],
    )


def check_snapshot_drift() -> CheckResult:
    output = io.StringIO()
    with redirect_stdout(output):
        result = phase31_contracts.check_contracts(require_clean_source=False)
    lines = [line for line in output.getvalue().splitlines() if line]
    if result:
        return CheckResult(
            "snapshot_drift",
            FAIL,
            "Tracked P3.1 evidence does not match deterministic generation.",
            lines[-20:],
        )
    return CheckResult(
        "snapshot_drift",
        PASS,
        "All 28 tracked artifacts regenerate byte-for-byte without network or GPU use.",
        lines[-3:],
    )


def check_evidence_index() -> CheckResult:
    try:
        document = _read_json(EVIDENCE_ROOT / "evidence-index.json")
        recorded_digest = document.pop("index_digest")
        computed_digest = canonical_digest(document)
        assertions = document["assertions"]
        records = document["records"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return CheckResult("evidence_index", FAIL, f"Evidence index is invalid: {exc}", [])
    expected_assertions = {
        "generated_only": True,
        "external_downloads": 0,
        "model_artifacts": 0,
        "media_artifacts": 0,
        "network_required": False,
        "gpu_required": False,
        "secrets_required": False,
        "candidate_count": 11,
        "candidate_eligible_count": 0,
    }
    failures = [
        key for key, expected in expected_assertions.items() if assertions.get(key) != expected
    ]
    if recorded_digest != computed_digest:
        failures.append("index_digest")
    if len(records) != 19:
        failures.append("record_count")
    if document.get("p3_2_status") != "blocked_pending_exact_artifact_and_dataset_approval":
        failures.append("p3_2_status")
    if failures:
        return CheckResult(
            "evidence_index",
            FAIL,
            "Evidence index assertions are incomplete or inconsistent.",
            sorted(failures),
        )
    return CheckResult(
        "evidence_index",
        PASS,
        "Evidence index binds 19 records and keeps downloads, media, candidates, and P3.2 closed.",
        [f"index_digest={recorded_digest}", "candidate_eligible_count=0", "p3_2=blocked"],
    )


def check_generated_source_evidence() -> CheckResult:
    try:
        fixture = FixtureManifestV1.model_validate(
            _read_json(EVIDENCE_ROOT / "fixture-manifest-v1.json")
        )
        dataset = DatasetManifestV1.model_validate(
            _read_json(EVIDENCE_ROOT / "dataset-manifest-v1.json")
        )
        generated = [
            _read_json(EVIDENCE_ROOT / "generated" / name) for name in GENERATED_ARTIFACTS
        ]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return CheckResult("generated_source_evidence", FAIL, f"Generated source evidence is invalid: {exc}", [])
    failures: list[str] = []
    if not fixture.generated_only or not fixture.prohibited_sources_absent:
        failures.append("fixture-source-assertions")
    if len(fixture.files) != len(GENERATED_ARTIFACTS):
        failures.append("fixture-file-count")
    if any(source.source_tier != "S0" or source.authorization_state != "authorized" for source in dataset.sources):
        failures.append("dataset-source-tier")
    for name, document in zip(GENERATED_ARTIFACTS, generated, strict=True):
        if document.get("generated_only") is not True or document.get("external_inputs") != []:
            failures.append(name)
        serialized = json.dumps(document, ensure_ascii=True, sort_keys=True).casefold()
        if "https://" in serialized or "rtsp://" in serialized or "rtsps://" in serialized:
            failures.append(f"{name}-external-reference")
    if failures:
        return CheckResult(
            "generated_source_evidence",
            FAIL,
            "Generated source package contains an invalid source assertion.",
            sorted(set(failures)),
        )
    return CheckResult(
        "generated_source_evidence",
        PASS,
        "Seven generated suites are S0-only, deterministic, hashed, and external-input free.",
        [f"fixture_digest={fixture.manifest_digest}", f"dataset_digest={dataset.manifest_digest}"],
    )


def check_quality_and_leakage_reports() -> CheckResult:
    try:
        qa = AnnotationQaReportV1.model_validate(
            _read_json(EVIDENCE_ROOT / "annotation-qa-report-v1.json")
        )
        split = SplitValidationReportV1.model_validate(
            _read_json(EVIDENCE_ROOT / "split-validation-report-v1.json")
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return CheckResult("quality_and_leakage", FAIL, f"QA or split report is invalid: {exc}", [])
    failures: list[str] = []
    if qa.status != "pass" or qa.invalid_item_count or qa.unresolved_blockers:
        failures.append("annotation-qa")
    if split.status != "pass":
        failures.append("split-status")
    if split.exact_duplicate_count or split.cross_split_group_count or split.missing_group_key_count:
        failures.append("split-leakage")
    if set(split.split_counts) != {"train", "validation", "test"} or not all(split.split_counts.values()):
        failures.append("split-coverage")
    if failures:
        return CheckResult(
            "quality_and_leakage",
            FAIL,
            "Annotation QA or split/leakage evidence failed.",
            failures,
        )
    return CheckResult(
        "quality_and_leakage",
        PASS,
        "Annotation QA passes and immutable train/validation/test splits contain no detected leakage.",
        [f"qa_digest={qa.report_digest}", f"split_digest={split.report_digest}"],
    )


def check_metric_goldens() -> CheckResult:
    try:
        report = MetricReportV1.model_validate(
            _read_json(EVIDENCE_ROOT / "metric-report-v1.json")
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return CheckResult("metric_goldens", FAIL, f"Metric report is invalid: {exc}", [])
    values = {metric.metric_name: metric.value for metric in report.metrics}
    required = {
        "detection.precision",
        "detection.recall",
        "detection.map50",
        "tracking.idf1",
        "tracking.identity_switches",
        "geometry.precision",
        "geometry.recall",
        "synthetic_anpr.exact_match",
        "synthetic_anpr.character_error_rate",
    }
    failures: list[str] = []
    if set(values) != required:
        failures.append("metric-set")
    if report.failed_gates or report.regressions:
        failures.append("fabricated-gate-or-regression")
    if not report.hard_gates or any(
        gate.outcome != "proposal_only" or gate.owner_approved for gate in report.hard_gates
    ):
        failures.append("numeric-gate-policy")
    if report.approval.status != "owner_recorded":
        failures.append("baseline-owner-record")
    if failures:
        return CheckResult(
            "metric_goldens",
            FAIL,
            "Metric report is incomplete or overclaims promotion evidence.",
            failures,
        )
    return CheckResult(
        "metric_goldens",
        PASS,
        "Hand-computable metrics are recorded and every numeric threshold remains proposal-only.",
        [f"report_digest={report.report_digest}", f"metric_count={len(report.metrics)}"],
    )


def check_candidate_dossier() -> CheckResult:
    failures: list[str] = []
    manifests: list[CandidateArtifactManifestV1] = []
    try:
        for candidate_id in CANDIDATE_IDS:
            path = EVIDENCE_ROOT / "candidates" / f"candidate-{candidate_id.lower()}.json"
            manifest = CandidateArtifactManifestV1.model_validate(_read_json(path))
            manifests.append(manifest)
            if manifest.candidate_id != candidate_id:
                failures.append(f"{candidate_id}-identity")
            if manifest.eligibility != "blocked" or not manifest.blockers:
                failures.append(f"{candidate_id}-eligibility")
            if manifest.approval.status != "pending":
                failures.append(f"{candidate_id}-approval")
        dossier = SourceResearchDossierV1.model_validate(
            _read_json(EVIDENCE_ROOT / "source-research-dossier-v1.json")
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return CheckResult("candidate_dossier", FAIL, f"Candidate dossier is invalid: {exc}", failures)
    if dossier.downloaded_artifacts:
        failures.append("downloaded-artifacts")
    if len(dossier.candidates) != len(CANDIDATE_IDS) or not dossier.unresolved_blockers:
        failures.append("dossier-completeness")
    if failures:
        return CheckResult(
            "candidate_dossier",
            FAIL,
            "Candidate records do not preserve blocked metadata-only status.",
            failures,
        )
    return CheckResult(
        "candidate_dossier",
        PASS,
        "All 11 candidates are metadata-only, blocked, and expose unresolved source blockers; downloads remain zero.",
        [f"dossier_digest={dossier.dossier_digest}", f"blockers={len(dossier.unresolved_blockers)}"],
    )


def check_run_safety() -> CheckResult:
    try:
        run = EvaluationRunManifestV1.model_validate(
            _read_json(EVIDENCE_ROOT / "evaluation-run-v1.json")
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return CheckResult("run_safety", FAIL, f"Evaluation run is invalid: {exc}", [])
    failures: list[str] = []
    if run.command.network_access != "denied" or run.command.gpu_access != "denied":
        failures.append("runtime-access")
    if run.command.secrets_required or run.candidate is not None:
        failures.append("secret-or-candidate-runtime")
    if run.precision != "not_applicable" or run.failed_gates:
        failures.append("generated-run-state")
    if run.reproducibility_status != "pass" or run.hardware.profile_id != "LAB-LAPTOP-01":
        failures.append("reproducibility-profile")
    if failures:
        return CheckResult(
            "run_safety",
            FAIL,
            "Baseline run violates generated-only execution boundaries.",
            failures,
        )
    return CheckResult(
        "run_safety",
        PASS,
        "Baseline is CPU-only, offline, secret-free, candidate-free, and bound to LAB-LAPTOP-01.",
        [f"run_digest={run.manifest_digest}", f"source_commit={run.source.commit}"],
    )


def check_ci_integration() -> CheckResult:
    try:
        workflow = (ROOT / ".github" / "workflows" / "python-ci.yml").read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        return CheckResult("ci_integration", FAIL, f"CI workflow is unavailable: {exc}", [])
    commands = (
        "python tools/phase31_contracts.py check --require-clean-source",
        "python tools/phase31_implementation_readiness.py --strict",
    )
    missing = [command for command in commands if command not in workflow]
    if missing:
        return CheckResult(
            "ci_integration",
            FAIL,
            "CI does not enforce the accepted P3.1 evidence state.",
            missing,
        )
    return CheckResult(
        "ci_integration",
        PASS,
        "Python CI verifies clean P3.1 evidence and fails closed if acceptance regresses.",
        [*commands, "pytest --cov=hcam --cov-fail-under=90"],
    )


def check_clean_source_baseline() -> CheckResult:
    try:
        run = EvaluationRunManifestV1.model_validate(
            _read_json(EVIDENCE_ROOT / "evaluation-run-v1.json")
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return CheckResult("clean_source_baseline", FAIL, f"Evaluation run is invalid: {exc}", [])
    if run.source.dirty_worktree:
        return CheckResult(
            "clean_source_baseline",
            MANUAL,
            "Rerun and regenerate the baseline from the accepted clean commit before P3.1 exit acceptance.",
            [f"recorded_commit={run.source.commit}", "dirty_worktree=true"],
        )
    return CheckResult(
        "clean_source_baseline",
        PASS,
        "Recorded baseline was generated from a clean source commit.",
        [f"recorded_commit={run.source.commit}", "dirty_worktree=false"],
    )


def check_owner_acceptance() -> CheckResult:
    try:
        index = _read_json(EVIDENCE_ROOT / "evidence-index.json")
        requirement = index["owner_acceptance"]
        acceptance = _read_json(ACCEPTANCE_PATH)
        digest, _manifest = package_digest()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return CheckResult("owner_acceptance", FAIL, f"Owner acceptance state is invalid: {exc}", [])
    if requirement != {"required_record": "D-P3.1-ACCEPTANCE", "status": "pending"}:
        return CheckResult(
            "owner_acceptance",
            FAIL,
            "Evidence package acceptance requirement was altered.",
            [f"requirement={requirement!r}"],
        )
    if digest != ACCEPTED_PACKAGE_DIGEST:
        return CheckResult(
            "owner_acceptance",
            FAIL,
            "Current evidence package does not match the owner-accepted digest.",
            [f"accepted_digest={ACCEPTED_PACKAGE_DIGEST}", f"current_digest={digest}"],
        )
    if acceptance != ACCEPTANCE_RECORD:
        return CheckResult(
            "owner_acceptance",
            FAIL,
            "Owner acceptance record does not match the exact digest-bound decision.",
            [f"record={acceptance.get('record_id', 'missing')}"],
        )
    return CheckResult(
        "owner_acceptance",
        PASS,
        "Accountable owner acceptance is recorded and bound to the unchanged evidence package.",
        [
            f"record={acceptance['record_id']}",
            f"accepted_by={acceptance['accepted_by']}",
            f"package_digest={digest}",
            f"accepted_repository_head={acceptance['accepted_repository_head']}",
        ],
    )


def check_package_digest() -> CheckResult:
    try:
        digest, manifest = package_digest()
    except OSError as exc:
        return CheckResult("package_digest", FAIL, f"Evidence package cannot be hashed: {exc}", [])
    return CheckResult(
        "package_digest",
        PASS,
        "All 28 evidence artifacts are included in the canonical package digest.",
        [f"package_digest={digest}", *manifest],
    )


def _run(command: list[str]) -> tuple[str, str | None]:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=240,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return " ".join(command), str(exc)
    evidence = f"{' '.join(command)} exit={result.returncode}"
    if result.returncode:
        output = (result.stdout + result.stderr).strip().splitlines()
        return evidence, output[-1] if output else "command failed"
    return evidence, None


def run_validation_commands() -> CheckResult:
    commands = [
        [
            sys.executable,
            "tools/phase31_contracts.py",
            "check",
            "--require-clean-source",
        ],
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_analytics_evaluation_contracts.py",
            "tests/test_analytics_generated_evaluation.py",
            "tests/test_phase31_evidence_contracts.py",
            "tests/test_phase31_implementation_readiness.py",
        ],
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "app/hcam/analytics/evaluation",
            "tools/phase31_contracts.py",
            "tools/phase31_implementation_readiness.py",
            "tests/test_analytics_evaluation_contracts.py",
            "tests/test_analytics_generated_evaluation.py",
            "tests/test_phase31_evidence_contracts.py",
            "tests/test_phase31_implementation_readiness.py",
        ],
        ["git", "diff", "--check"],
    ]
    evidence: list[str] = []
    failures: list[str] = []
    for command in commands:
        item, failure = _run(command)
        evidence.append(item)
        if failure:
            failures.append(failure)
    if failures:
        return CheckResult(
            "validation_commands",
            FAIL,
            "; ".join(failures),
            evidence,
        )
    return CheckResult(
        "validation_commands",
        PASS,
        "Focused offline tests, lint, snapshot drift, and whitespace validation passed.",
        evidence,
    )


def build_readiness_report(*, run_validation: bool = False) -> ReadinessReport:
    checks = [
        check_required_files(),
        check_snapshot_drift(),
        check_evidence_index(),
        check_generated_source_evidence(),
        check_quality_and_leakage_reports(),
        check_metric_goldens(),
        check_candidate_dossier(),
        check_run_safety(),
        check_ci_integration(),
        check_clean_source_baseline(),
        check_owner_acceptance(),
        check_package_digest(),
    ]
    if run_validation:
        checks.append(run_validation_commands())
    try:
        digest, _manifest = package_digest()
    except OSError:
        digest = "0" * 64
    failures = sum(check.status == FAIL for check in checks)
    manual_gates = sum(check.status == MANUAL for check in checks)
    if failures:
        status = "not_ready"
    elif manual_gates:
        status = "technical_evidence_ready_with_manual_gates"
    else:
        status = "accepted"
    return ReadinessReport(
        status=status,
        scope="phase3.p3_1.data_and_evaluation_foundation.implementation",
        package_digest=digest,
        failures=failures,
        manual_gates=manual_gates,
        checks=checks,
    )


def print_text_report(report: ReadinessReport) -> None:
    print(f"Phase 3 P3.1 implementation readiness: {report.status}")
    print(f"Scope: {report.scope}")
    print(f"Package digest: {report.package_digest}")
    print(f"Failures: {report.failures}")
    print(f"Manual gates: {report.manual_gates}")
    print()
    for check in report.checks:
        print(f"[{check.status}] {check.name}: {check.detail}")
        for item in check.evidence:
            print(f"  - {item}")
        print()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify H-CAM Phase 3 P3.1 implementation evidence."
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--run-validation", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_readiness_report(run_validation=args.run_validation)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print_text_report(report)
    if report.failures:
        return 1
    if args.strict and report.manual_gates:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
