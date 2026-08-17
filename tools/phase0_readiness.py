#!/usr/bin/env python3
"""Phase 0 readiness verifier for the H-CAM repository.

The verifier is intentionally offline by default. It checks repository evidence
for Phase 0 planning, governance, validation, and Sentinel adapter readiness
without calling live CCTV endpoints or reading generated fixture JSON.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PHASE0 = ROOT / "docs" / "phase-0"
GITHUB = ROOT / ".github"

PASS = "pass"
FAIL = "fail"
MANUAL = "manual"

REQUIRED_PHASE0_DOCS = [
    "README.md",
    "product-brief.md",
    "requirements.md",
    "architecture-baseline.md",
    "data-governance.md",
    "validation-plan.md",
    "roadmap.md",
    "acceptance-checklist.md",
    "phase-1-handoff.md",
    "decision-records.md",
    "phase-1-backlog.md",
    "review-questions.md",
    "cctv-environment.md",
    "team-workflow.md",
    "readiness-report.md",
    "owner-review.md",
    "official-constraints-intake.md",
    "manual-gate-issues.md",
]

REQUIRED_README_LINKS = [
    "product-brief.md",
    "requirements.md",
    "architecture-baseline.md",
    "data-governance.md",
    "validation-plan.md",
    "roadmap.md",
    "acceptance-checklist.md",
    "phase-1-handoff.md",
    "decision-records.md",
    "phase-1-backlog.md",
    "review-questions.md",
    "cctv-environment.md",
    "team-workflow.md",
    "readiness-report.md",
    "owner-review.md",
    "official-constraints-intake.md",
    "manual-gate-issues.md",
]

REQUIRED_SENTINEL_COMMANDS = [
    "metadata",
    "state",
    "stream-test",
    "snapshot",
    "offline-summary",
    "registry-export",
    "all",
]

REQUIRED_GITHUB_FILES = [
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/phase_task.yml",
    ".github/ISSUE_TEMPLATE/architecture_decision.yml",
    ".github/ISSUE_TEMPLATE/risk_compliance.yml",
    ".github/ISSUE_TEMPLATE/review_question.yml",
    ".github/workflows/python-ci.yml",
]

ALLOWED_MANUAL_GATE_PREFIXES = [
    "Review Phase 0 docs with project owner",
    "Confirm official challenge constraints and dataset rules",
    "Approve, revise, or reject proposed Phase 1 decisions",
    "Start camera registry backend implementation after Phase 1 is approved",
]


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str
    evidence: list[str]


@dataclass(frozen=True)
class ReadinessReport:
    status: str
    failures: int
    manual_gates: int
    checks: list[CheckResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "failures": self.failures,
            "manual_gates": self.manual_gates,
            "checks": [asdict(check) for check in self.checks],
        }


@dataclass(frozen=True)
class ChecklistItem:
    checked: bool
    text: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def result(name: str, status: str, detail: str, evidence: Iterable[str]) -> CheckResult:
    return CheckResult(name=name, status=status, detail=detail, evidence=list(evidence))


def missing_terms(content: str, terms: Iterable[str]) -> list[str]:
    return [term for term in terms if term not in content]


def parse_checklist_items(content: str) -> list[ChecklistItem]:
    items: list[ChecklistItem] = []
    current: list[str] | None = None
    checked = False

    def flush() -> None:
        nonlocal current
        if current is not None:
            items.append(ChecklistItem(checked=checked, text=" ".join(current).strip()))
            current = None

    for line in content.splitlines():
        match = re.match(r"^- \[([ xX])\]\s+(.*)$", line)
        if match:
            flush()
            checked = match.group(1).lower() == "x"
            current = [match.group(2).strip()]
            continue
        if current is not None and line.startswith("  ") and line.strip():
            current.append(line.strip())
            continue
        if current is not None and line and not line.startswith(" "):
            flush()

    flush()
    return items


def is_allowed_manual_gate(text: str) -> bool:
    return any(text.startswith(prefix) for prefix in ALLOWED_MANUAL_GATE_PREFIXES)


def check_phase0_docs() -> CheckResult:
    missing: list[str] = []
    too_small: list[str] = []
    for filename in REQUIRED_PHASE0_DOCS:
        path = PHASE0 / filename
        if not path.exists():
            missing.append(rel(path))
        elif path.stat().st_size < 200:
            too_small.append(rel(path))

    if missing or too_small:
        parts = []
        if missing:
            parts.append(f"missing: {', '.join(missing)}")
        if too_small:
            parts.append(f"too small: {', '.join(too_small)}")
        return result("phase0_documents", FAIL, "; ".join(parts), [rel(PHASE0)])

    return result(
        "phase0_documents",
        PASS,
        f"{len(REQUIRED_PHASE0_DOCS)} required Phase 0 documents are present.",
        [rel(PHASE0 / name) for name in REQUIRED_PHASE0_DOCS],
    )


def check_phase0_links() -> CheckResult:
    phase0_readme = read_text(PHASE0 / "README.md")
    root_readme = read_text(ROOT / "README.md")
    missing = missing_terms(phase0_readme, REQUIRED_README_LINKS)
    if "docs/phase-0/README.md" not in root_readme:
        missing.append("root README link to docs/phase-0/README.md")

    if missing:
        return result("phase0_links", FAIL, f"missing links: {', '.join(missing)}", [rel(PHASE0 / "README.md"), "README.md"])

    return result(
        "phase0_links",
        PASS,
        "Phase 0 index and root README link the required documents.",
        [rel(PHASE0 / "README.md"), "README.md"],
    )


def check_sentinel_probe() -> CheckResult:
    probe = ROOT / "tools" / "sentinel_cctv_probe.py"
    if not probe.exists():
        return result("sentinel_probe", FAIL, "Sentinel probe tool is missing.", [rel(probe)])

    content = read_text(probe)
    missing = missing_terms(content, [f'"{command}"' for command in REQUIRED_SENTINEL_COMMANDS])
    required_phrases = [
        "metadata-only",
        "ffprobe",
        "hcam.camera_registry.seed.v1",
        "DEFAULT_CAMERA_IDS",
    ]
    missing.extend(missing_terms(content, required_phrases))

    if missing:
        return result("sentinel_probe", FAIL, f"missing command or safety terms: {', '.join(missing)}", [rel(probe)])

    return result(
        "sentinel_probe",
        PASS,
        "Sentinel probe exposes all Phase 0 commands and registry export support.",
        [rel(probe)],
    )


def check_fixture_policy() -> CheckResult:
    fixture_dir = ROOT / "fixtures" / "sentinel"
    fixture_ignore = fixture_dir / ".gitignore"
    fixture_readme = fixture_dir / "README.md"
    missing: list[str] = []
    if not fixture_ignore.exists():
        missing.append(rel(fixture_ignore))
    elif "*.json" not in read_text(fixture_ignore):
        missing.append(f"{rel(fixture_ignore)} must ignore generated JSON")
    if not fixture_readme.exists():
        missing.append(rel(fixture_readme))
    else:
        readme = read_text(fixture_readme)
        missing.extend(missing_terms(readme, ["must not store CCTV footage", "registry-export"]))

    if missing:
        return result("fixture_policy", FAIL, "; ".join(missing), [rel(fixture_dir)])

    return result(
        "fixture_policy",
        PASS,
        "Generated Sentinel JSON fixtures are ignored and documented as metadata-only.",
        [rel(fixture_ignore), rel(fixture_readme)],
    )


def check_github_governance() -> CheckResult:
    missing = [path for path in REQUIRED_GITHUB_FILES if not (ROOT / path).exists()]
    if missing:
        return result("github_governance", FAIL, f"missing: {', '.join(missing)}", REQUIRED_GITHUB_FILES)

    pr_template = read_text(GITHUB / "PULL_REQUEST_TEMPLATE.md")
    workflow = read_text(GITHUB / "workflows" / "python-ci.yml")
    phase_task = read_text(GITHUB / "ISSUE_TEMPLATE" / "phase_task.yml")
    missing_terms_list: list[str] = []
    missing_terms_list.extend(missing_terms(pr_template, ["Safety And Data Handling", "CCTV video", "government data"]))
    missing_terms_list.extend(missing_terms(phase_task, ["Acceptance Criteria", "Validation Plan"]))
    missing_terms_list.extend(missing_terms(workflow, ["py_compile tools/sentinel_cctv_probe.py", "unittest discover -s tests -v"]))

    if missing_terms_list:
        return result("github_governance", FAIL, f"missing terms: {', '.join(missing_terms_list)}", REQUIRED_GITHUB_FILES)

    return result(
        "github_governance",
        PASS,
        "CI, PR template, and issue templates are present with safety and validation gates.",
        REQUIRED_GITHUB_FILES,
    )


def check_validation_plan() -> CheckResult:
    validation = read_text(PHASE0 / "validation-plan.md")
    required = [
        "python -m py_compile tools/sentinel_cctv_probe.py tools/phase0_readiness.py",
        "python -m unittest discover -s tests -v",
        "python tools/phase0_readiness.py --run-validation",
        "Live Sentinel behavior can change",
    ]
    missing = missing_terms(validation, required)
    if missing:
        return result("validation_plan", FAIL, f"missing validation items: {', '.join(missing)}", [rel(PHASE0 / "validation-plan.md")])
    return result(
        "validation_plan",
        PASS,
        "Validation plan includes compile, unit, readiness, live caveat, and evidence expectations.",
        [rel(PHASE0 / "validation-plan.md")],
    )


def check_manual_gate_artifacts() -> CheckResult:
    owner_review = read_text(PHASE0 / "owner-review.md")
    constraints = read_text(PHASE0 / "official-constraints-intake.md")
    manual_issues = read_text(PHASE0 / "manual-gate-issues.md")
    missing: list[str] = []
    missing.extend(
        missing_terms(
            owner_review,
            [
                "Review Outcome",
                "Manual Gates",
                "Review Phase 0 Docs With Project Owner",
                "Approve, Revise, Or Reject Phase 1 Decisions",
                "Phase 1 starts only after manual review",
            ],
        )
    )
    missing.extend(
        missing_terms(
            constraints,
            [
                "Current status: official source intake is not complete.",
                "attached official PDF files",
                "Public Source Scan",
                "Required Official Answers",
                "Do not commit CCTV video",
                "watchlist",
                "government database",
            ],
        )
    )
    missing.extend(
        missing_terms(
            manual_issues,
            [
                "Manual Gate Issues",
                "https://github.com/mayankthakor227/h-cam-2.0/issues/10",
                "https://github.com/mayankthakor227/h-cam-2.0/issues/11",
                "https://github.com/mayankthakor227/h-cam-2.0/issues/12",
                "https://github.com/mayankthakor227/h-cam-2.0/issues/13",
                "Do not close a manual gate issue because tests pass",
            ],
        )
    )

    if missing:
        return result(
            "manual_gate_artifacts",
            FAIL,
            f"missing manual gate artifact terms: {', '.join(missing)}",
            [
                rel(PHASE0 / "owner-review.md"),
                rel(PHASE0 / "official-constraints-intake.md"),
                rel(PHASE0 / "manual-gate-issues.md"),
            ],
        )

    return result(
        "manual_gate_artifacts",
        PASS,
        "Owner review, official constraints intake, and GitHub manual-gate issue index are present.",
        [
            rel(PHASE0 / "owner-review.md"),
            rel(PHASE0 / "official-constraints-intake.md"),
            rel(PHASE0 / "manual-gate-issues.md"),
        ],
    )


def check_acceptance_checklist() -> CheckResult:
    checklist_path = PHASE0 / "acceptance-checklist.md"
    items = parse_checklist_items(read_text(checklist_path))
    unchecked = [item.text for item in items if not item.checked]
    unexpected = [text for text in unchecked if not is_allowed_manual_gate(text)]

    if unexpected:
        return result(
            "acceptance_checklist",
            FAIL,
            f"unexpected unchecked gates: {', '.join(unexpected)}",
            [rel(checklist_path)],
        )

    if unchecked:
        return result(
            "acceptance_checklist",
            MANUAL,
            f"{len(unchecked)} manual Phase 0/Phase 1 gates still require owner or official approval.",
            unchecked,
        )

    return result("acceptance_checklist", PASS, "All acceptance checklist items are checked.", [rel(checklist_path)])


def run_validation_commands() -> CheckResult:
    commands = [
        [sys.executable, "-m", "py_compile", "tools/sentinel_cctv_probe.py", "tools/phase0_readiness.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        ["git", "diff", "--check"],
    ]
    evidence: list[str] = []
    failures: list[str] = []

    for command in commands:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=120)
        rendered = " ".join(command)
        evidence.append(f"{rendered} -> exit {completed.returncode}")
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            failures.append(f"{rendered}: {detail}")

    if failures:
        return result("local_validation_commands", FAIL, "; ".join(failures), evidence)
    return result("local_validation_commands", PASS, "Compile, unit tests, and diff whitespace checks passed.", evidence)


def build_readiness_report(run_validation: bool = False) -> ReadinessReport:
    checks = [
        check_phase0_docs(),
        check_phase0_links(),
        check_sentinel_probe(),
        check_fixture_policy(),
        check_github_governance(),
        check_validation_plan(),
        check_manual_gate_artifacts(),
        check_acceptance_checklist(),
    ]
    if run_validation:
        checks.append(run_validation_commands())

    failures = sum(1 for check in checks if check.status == FAIL)
    manual_gates = sum(len(check.evidence) for check in checks if check.status == MANUAL)
    if failures:
        status = "not_ready"
    elif manual_gates:
        status = "ready_for_owner_review"
    else:
        status = "complete"
    return ReadinessReport(status=status, failures=failures, manual_gates=manual_gates, checks=checks)


def print_text_report(report: ReadinessReport) -> None:
    print(f"Phase 0 readiness: {report.status}")
    print(f"Failures: {report.failures}")
    print(f"Manual gates: {report.manual_gates}")
    print()
    for check in report.checks:
        print(f"[{check.status}] {check.name}: {check.detail}")
        for evidence in check.evidence:
            print(f"  - {evidence}")
        print()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify H-CAM Phase 0 readiness evidence.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--run-validation",
        action="store_true",
        help="Also run local compile, unit test, and diff whitespace commands.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return nonzero when manual owner/official gates are still pending.",
    )
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
