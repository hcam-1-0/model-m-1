#!/usr/bin/env python3
"""Offline verifier for Phase 3 P3.1 planning and authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE3 = ROOT / "docs" / "phase-3"
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"

AUTHORIZATION_PATH = "contracts/phase-3/p3-1-authorization.json"
PLAN_PATH = "docs/phase-3/p3-1-plan.md"
HARDWARE_PATH = "docs/phase-3/p3-1-hardware-profile.md"
AUTHORIZATION_DOC_PATH = "docs/phase-3/p3-1-authorization.md"
READINESS_PATH = "docs/phase-3/p3-1-readiness-report.md"

PACKAGE_FILES = (
    AUTHORIZATION_PATH,
    AUTHORIZATION_DOC_PATH,
    HARDWARE_PATH,
    PLAN_PATH,
    READINESS_PATH,
)
REQUIRED_FILES = (
    *PACKAGE_FILES,
    "tools/phase31_readiness.py",
    "tests/test_phase31_readiness.py",
)
PLANNING_GATE_IDS = ("P31-G1", "P31-G2", "P31-G3", "P31-G4", "P31-G5")
IMPLEMENTATION_GATE_COUNT = 7
WORK_PACKAGES = tuple(f"P31-W{index}" for index in range(1, 10))
CONTRACT_FAMILIES = (
    "DatasetManifestV1",
    "FixtureManifestV1",
    "AnnotationSpecificationV1",
    "CandidateArtifactManifestV1",
    "EvaluationRunManifestV1",
    "MetricReportV1",
)
IMPLEMENTATION_SCOPE = (
    "versioned_manifest_and_report_schemas",
    "deterministic_generated_metadata_and_assets",
    "annotation_and_qa_specification",
    "split_duplicate_and_leakage_validation",
    "offline_generated_fixture_metrics",
    "metadata_only_candidate_registry",
    "source_license_provenance_research_without_downloads",
    "clean_machine_reproducibility_and_evidence_index",
)
NON_AUTHORIZATION = (
    "external_dataset_or_font_download",
    "model_checkpoint_or_weight_download",
    "training_finetuning_export_or_inference",
    "decoder_or_gpu_runtime_execution",
    "sentinel_live_cctv_or_physical_camera_access",
    "government_private_scraped_or_unreviewed_media",
    "raw_camera_media_persistence",
    "identity_watchlist_owner_lookup_or_sensitive_traits",
    "operational_alerting_or_autonomous_action",
    "p3_2_implementation",
    "pilot_production_or_statewide_deployment",
)
EXIT_GATES = (
    "contracts_and_canonical_fixtures_pass",
    "generated_only_source_proof_passes",
    "annotation_qa_split_and_leakage_checks_pass",
    "metric_goldens_and_determinism_pass",
    "candidate_records_expose_all_unresolved_blockers",
    "ci_is_offline_gpu_free_and_secret_free",
    "developer_profile_baseline_is_reproducible",
    "proposed_numeric_gates_are_owner_recorded",
    "p3_1_evidence_and_limitations_are_owner_accepted",
)
SOURCE_TIERS = (
    {
        "source_tier": "S0",
        "state": "authorized",
        "type": "generated_metadata_and_programmatic_assets",
    },
    {
        "source_tier": "S1",
        "state": "planning_only_requires_exact_owner_record",
        "type": "team_created_media",
    },
    {
        "source_tier": "S2",
        "state": "research_only_no_download",
        "type": "public_datasets_and_fonts",
    },
    {
        "source_tier": "S3",
        "state": "research_only_no_download",
        "type": "public_model_code_and_artifacts",
    },
    {
        "source_tier": "S4",
        "state": "prohibited_requires_new_authorization",
        "type": "owned_private_lab_camera_media",
    },
    {
        "source_tier": "S5",
        "state": "prohibited",
        "type": "sentinel_government_police_scraped_or_private_data",
    },
)

_PLANNING_GATE_PATTERN = re.compile(
    r"^- \[(?P<mark>[ xX])\] `(?P<gate_id>P31-G\d+)` (?P<title>.+)$",
    re.MULTILINE,
)
_IMPLEMENTATION_GATE_PATTERN = re.compile(
    r"^- \[(?P<mark>[ xX])\] (?P<title>.+)$",
    re.MULTILINE,
)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+)\)")


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


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _read_json(relative_path: str) -> dict[str, Any]:
    value = json.loads(_read(relative_path))
    if not isinstance(value, dict):
        raise ValueError(f"{relative_path} must contain a JSON object")
    return value


def package_digest() -> tuple[str, list[str]]:
    manifest: list[str] = []
    for relative_path in sorted(PACKAGE_FILES):
        path = ROOT / relative_path
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        manifest.append(f"{relative_path}:{digest}\n")
    aggregate = hashlib.sha256("".join(manifest).encode("utf-8")).hexdigest()
    return aggregate.upper(), manifest


def check_required_files() -> CheckResult:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        return CheckResult(
            "required_files",
            FAIL,
            f"missing: {', '.join(missing)}",
            missing,
        )
    return CheckResult(
        "required_files",
        PASS,
        f"{len(REQUIRED_FILES)} P3.1 planning and verification files are present.",
        list(REQUIRED_FILES),
    )


def check_authorization_record() -> CheckResult:
    failures: list[str] = []
    try:
        record = _read_json(AUTHORIZATION_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult(
            "authorization_record",
            FAIL,
            str(exc),
            [AUTHORIZATION_PATH],
        )

    expected_scalars = {
        "contract_format": "hcam.phase3.p3-1-authorization.v1",
        "authorization_id": "D-P3.1-001",
        "status": "authorized_for_implementation",
        "accountable_owner_id": "mayank-admin",
        "authorized_on": "2026-08-24",
        "decision_basis": "complete P3.1 planning and authorization",
        "hardware_profile_id": "LAB-LAPTOP-01",
    }
    for key, expected in expected_scalars.items():
        if record.get(key) != expected:
            failures.append(f"authorization field changed: {key}")

    expected_objects: dict[str, object] = {
        "implementation_scope": list(IMPLEMENTATION_SCOPE),
        "non_authorization": list(NON_AUTHORIZATION),
        "p3_1_exit_gates": list(EXIT_GATES),
        "source_tiers": list(SOURCE_TIERS),
        "work_packages": list(WORK_PACKAGES),
        "later_review_policy": {
            "accountable_owner_review_sufficient": True,
            "evidence_requirements_remain_mandatory": True,
            "separate_person_review_required": False,
        },
        "p3_0_dependency": {
            "required_status": "accepted",
            "scope": "phase3.p3_0.contracts_and_guardrails",
        },
    }
    for key, expected in expected_objects.items():
        if record.get(key) != expected:
            failures.append(f"authorization boundary changed: {key}")

    if failures:
        return CheckResult(
            "authorization_record",
            FAIL,
            "; ".join(failures),
            [AUTHORIZATION_PATH],
        )
    return CheckResult(
        "authorization_record",
        PASS,
        "Owner, scope, source tiers, exit gates, and non-authorization match D-P3.1-001.",
        [AUTHORIZATION_PATH, AUTHORIZATION_DOC_PATH],
    )


def check_plan_completeness() -> CheckResult:
    content = _read(PLAN_PATH)
    normalized = re.sub(r"\s+", " ", content)
    failures: list[str] = []
    required_sections = (
        "## Objective",
        "## Dependencies",
        "## Authorized Scope",
        "## Not Authorized",
        "## Source Tiers",
        "## Contract Package",
        "## Generated Fixture Matrix",
        "## Annotation And QA Plan",
        "## Split And Leakage Plan",
        "## Metric Harness Plan",
        "## Work Packages",
        "## Delivery Sequence",
        "## P3.1 Acceptance Criteria",
        "## Risks And Controls",
        "## Authorization Result",
    )
    for section in required_sections:
        if content.count(section) != 1:
            failures.append(f"plan section missing or duplicated: {section}")
    for family in CONTRACT_FAMILIES:
        if content.count(f"### {family}") != 1:
            failures.append(f"contract family missing or duplicated: {family}")
    for package in WORK_PACKAGES:
        if content.count(f"`{package}`") != 1:
            failures.append(f"work package missing or duplicated: {package}")

    required_terms = (
        "P3.1 does not select a production champion and does not implement inference.",
        "CI must use `S0` only",
        "No labeling at scale starts from planning authorization alone.",
        "No numeric promotion threshold is approved until a measured baseline exists.",
        "P3.2 remains blocked until an exact detector artifact and dataset are owner",
        "P3.1 implementation and exit evidence are not yet complete",
    )
    for term in required_terms:
        if term not in normalized:
            failures.append(f"required plan boundary is missing: {term}")

    if failures:
        return CheckResult(
            "plan_completeness",
            FAIL,
            "; ".join(failures),
            [PLAN_PATH],
        )
    return CheckResult(
        "plan_completeness",
        PASS,
        "P3.1 contracts, fixtures, QA, leakage, metrics, work, risks, and exits are planned.",
        [PLAN_PATH],
    )


def check_hardware_profile() -> CheckResult:
    content = _read(HARDWARE_PATH)
    required = (
        "Profile ID: `LAB-LAPTOP-01`",
        "Intel Core i5-8365U, 4 cores, 8 logical processors",
        "7.2 GiB reported physical memory",
        "Intel UHD Graphics 620",
        "Microsoft Windows 10 Pro, version 10.0.19045, build 19045",
        "Python | 3.14.6",
        "Docker engine | 28.5.2",
        "cannot establish production throughput, GPU parity,",
        "C10/C50 capacity",
        "statewide infrastructure sizing",
    )
    missing = [term for term in required if term not in content]
    forbidden = ("SerialNumber", "BIOS serial", "host name", "hostname")
    exposed = [term for term in forbidden if term.casefold() in content.casefold()]
    if missing or exposed:
        detail = []
        if missing:
            detail.append(f"missing profile evidence: {', '.join(missing)}")
        if exposed:
            detail.append(f"machine identifier must not be recorded: {', '.join(exposed)}")
        return CheckResult(
            "hardware_profile",
            FAIL,
            "; ".join(detail),
            [HARDWARE_PATH],
        )
    return CheckResult(
        "hardware_profile",
        PASS,
        "Developer hardware is declared with bounded generated-only benchmark claims.",
        [HARDWARE_PATH],
    )


def _safe_local_evidence(target: str) -> bool:
    if (
        "://" in target
        or target.startswith(("/", "\\"))
        or re.match(r"^[A-Za-z]:[\\/]", target)
    ):
        return False
    relative = target.split("#", 1)[0]
    if not relative or ".." in Path(relative).parts:
        return False
    candidate = (PHASE3 / relative).resolve()
    try:
        candidate.relative_to(PHASE3.resolve())
    except ValueError:
        return False
    return candidate.is_file()


def check_planning_gates() -> list[CheckResult]:
    content = _read(READINESS_PATH)
    status_match = re.search(r"^Status: `(?P<status>[^`]+)`$", content, re.MULTILINE)
    planning_matches = list(_PLANNING_GATE_PATTERN.finditer(content))
    gate_ids = [match.group("gate_id") for match in planning_matches]
    if gate_ids != list(PLANNING_GATE_IDS):
        return [
            CheckResult(
                "planning_gate_structure",
                FAIL,
                "planning gates must appear exactly once and in order: "
                + ", ".join(PLANNING_GATE_IDS),
                [READINESS_PATH],
            )
        ]

    results: list[CheckResult] = []
    incomplete_seen = False
    checked_count = 0
    for index, match in enumerate(planning_matches):
        block_end = (
            planning_matches[index + 1].start()
            if index + 1 < len(planning_matches)
            else content.find("## Implementation Gates", match.end())
        )
        if block_end < 0:
            block_end = len(content)
        block = content[match.end() : block_end]
        evidence_match = re.search(r"^  Evidence: (?P<value>.+)$", block, re.MULTILINE)
        evidence = evidence_match.group("value").strip() if evidence_match else None
        checked = match.group("mark").casefold() == "x"
        gate_id = match.group("gate_id")
        title = match.group("title").strip()
        if not checked:
            incomplete_seen = True
            if evidence != "`pending`":
                results.append(
                    CheckResult(
                        gate_id,
                        FAIL,
                        "An incomplete planning gate must use `pending` evidence.",
                        [READINESS_PATH, title],
                    )
                )
            else:
                results.append(CheckResult(gate_id, MANUAL, f"Pending: {title}", []))
            continue

        checked_count += 1
        if incomplete_seen:
            results.append(
                CheckResult(
                    gate_id,
                    FAIL,
                    "Planning gates must be completed in order.",
                    [READINESS_PATH, title],
                )
            )
            continue
        targets = (
            [item.group("target").strip() for item in _MARKDOWN_LINK_PATTERN.finditer(evidence)]
            if evidence
            else []
        )
        if not targets or not all(_safe_local_evidence(target) for target in targets):
            results.append(
                CheckResult(
                    gate_id,
                    FAIL,
                    "A completed planning gate requires a safe local evidence link.",
                    [READINESS_PATH, title],
                )
            )
        else:
            results.append(CheckResult(gate_id, PASS, f"Complete: {title}", targets))

    declared_status = status_match.group("status") if status_match else None
    expected_status = (
        "authorized_for_implementation"
        if checked_count == len(PLANNING_GATE_IDS)
        else "ready_for_owner_authorization"
    )
    if declared_status != expected_status:
        results.append(
            CheckResult(
                "planning_gate_status",
                FAIL,
                f"planning status must be `{expected_status}`",
                [READINESS_PATH],
            )
        )
    return results


def check_implementation_gates_pending() -> CheckResult:
    content = _read(READINESS_PATH)
    section_match = re.search(
        r"^## Implementation Gates\s+(?P<section>.*?)^## Boundary$",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return CheckResult(
            "implementation_gates_pending",
            FAIL,
            "implementation gate section is missing or malformed",
            [READINESS_PATH],
        )
    matches = list(
        _IMPLEMENTATION_GATE_PATTERN.finditer(section_match.group("section"))
    )
    if len(matches) != IMPLEMENTATION_GATE_COUNT:
        return CheckResult(
            "implementation_gates_pending",
            FAIL,
            f"expected {IMPLEMENTATION_GATE_COUNT} P3.1 implementation gates",
            [READINESS_PATH],
        )
    completed = [match.group("title") for match in matches if match.group("mark").casefold() == "x"]
    if completed:
        return CheckResult(
            "implementation_gates_pending",
            FAIL,
            "planning authorization cannot claim implementation completion: "
            + ", ".join(completed),
            [READINESS_PATH],
        )
    return CheckResult(
        "implementation_gates_pending",
        PASS,
        "All seven implementation exits remain explicitly incomplete.",
        [READINESS_PATH],
    )


def _p3_0_report() -> Any:
    try:
        from tools import phase3_readiness
    except ModuleNotFoundError:  # pragma: no cover - direct script fallback
        import phase3_readiness  # type: ignore[no-redef]

    return phase3_readiness.build_readiness_report(run_validation=False)


def check_p3_0_dependency() -> CheckResult:
    try:
        report = _p3_0_report()
    except (ImportError, OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult(
            "p3_0_dependency",
            FAIL,
            f"P3.0 readiness could not be verified: {type(exc).__name__}",
            ["tools/phase3_readiness.py"],
        )
    failures = getattr(report, "failures", None)
    manual_gates = getattr(report, "manual_gates", None)
    status = getattr(report, "status", None)
    scope = getattr(report, "scope", None)
    if (
        status != "accepted"
        or scope != "phase3.p3_0.contracts_and_guardrails"
        or failures != 0
        or manual_gates != 0
    ):
        return CheckResult(
            "p3_0_dependency",
            FAIL,
            "P3.0 must be accepted with zero failures and zero manual gates.",
            ["tools/phase3_readiness.py"],
        )
    return CheckResult(
        "p3_0_dependency",
        PASS,
        "P3.0 is accepted with zero failures and zero manual gates.",
        ["tools/phase3_readiness.py", "docs/phase-3/readiness-report.md"],
    )


def check_package_digest() -> CheckResult:
    try:
        digest, manifest = package_digest()
    except OSError as exc:
        return CheckResult(
            "package_digest",
            FAIL,
            str(exc),
            list(PACKAGE_FILES),
        )
    return CheckResult(
        "package_digest",
        PASS,
        f"{len(manifest)} P3.1 planning artifacts hash to {digest}.",
        [item.rstrip("\n") for item in manifest],
    )


def _display_command(command: list[str]) -> str:
    values = list(command)
    try:
        if Path(values[0]).resolve() == Path(sys.executable).resolve():
            values[0] = "python"
    except (IndexError, OSError):
        pass
    return " ".join(values)


def _run(command: list[str]) -> tuple[str, str | None]:
    command_text = _display_command(command)
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return command_text, type(exc).__name__
    evidence = f"{command_text} -> exit {completed.returncode}"
    if completed.returncode == 0:
        return evidence, None
    return evidence, f"command_failed(exit={completed.returncode})"


def run_validation_commands() -> CheckResult:
    commands = [
        ["uv", "lock", "--check"],
        [sys.executable, "-m", "compileall", "-q", "tools/phase31_readiness.py"],
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "tools/phase31_readiness.py",
            "tests/test_phase31_readiness.py",
        ],
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_phase31_readiness.py",
            "tests/test_phase3_readiness.py",
        ],
        [sys.executable, "tools/phase3_readiness.py", "--strict"],
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
        "Offline lock, compile, lint, tests, P3.0 dependency, and diff checks passed.",
        evidence,
    )


def build_readiness_report(run_validation: bool = False) -> ReadinessReport:
    try:
        digest, _manifest = package_digest()
    except OSError:
        digest = "0" * 64
    checks = [
        check_required_files(),
        check_authorization_record(),
        check_plan_completeness(),
        check_hardware_profile(),
        check_p3_0_dependency(),
        check_implementation_gates_pending(),
        check_package_digest(),
        *check_planning_gates(),
    ]
    if run_validation:
        checks.append(run_validation_commands())
    failures = sum(check.status == FAIL for check in checks)
    manual_gates = sum(check.status == MANUAL for check in checks)
    status = (
        "not_ready"
        if failures
        else "ready_for_owner_authorization"
        if manual_gates
        else "authorized_for_implementation"
    )
    return ReadinessReport(
        status=status,
        scope="phase3.p3_1.data_and_evaluation_foundation.planning",
        package_digest=digest,
        failures=failures,
        manual_gates=manual_gates,
        checks=checks,
    )


def print_text_report(report: ReadinessReport) -> None:
    print(f"Phase 3 P3.1 planning readiness: {report.status}")
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
        description="Verify H-CAM Phase 3 P3.1 planning and authorization."
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
