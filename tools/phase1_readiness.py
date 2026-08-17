#!/usr/bin/env python3
"""Offline Phase 1 evidence and validation verifier."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "docs" / "phase-1"
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"

REQUIRED_FILES = [
    "pyproject.toml",
    "alembic.ini",
    "app/hcam/main.py",
    "app/hcam/security/auth.py",
    "app/hcam/camera_registry/models.py",
    "app/hcam/camera_registry/schemas.py",
    "app/hcam/camera_registry/importer.py",
    "app/hcam/camera_registry/repository.py",
    "app/hcam/camera_registry/service.py",
    "app/hcam/camera_registry/routes.py",
    "app/hcam/camera_registry/import_routes.py",
    "app/hcam/audit/models.py",
    "migrations/versions/0001_camera_registry.py",
    "migrations/versions/0002_camera_version.py",
    "docs/phase-1/README.md",
    "docs/phase-1/security-and-management.md",
    "docs/phase-1/acceptance-checklist.md",
    "docs/phase-1/readiness-report.md",
    "docs/phase-1/owner-review.md",
    "tests/fixtures/camera-registry-seed.json",
    "tests/test_camera_registry_api.py",
    "tests/test_camera_registry_import.py",
    "tests/test_camera_management_api.py",
    "tests/test_camera_import_api.py",
    "tests/test_security.py",
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


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _missing_terms(content: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term not in content]


def check_required_files() -> CheckResult:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        return CheckResult("required_files", FAIL, f"missing: {', '.join(missing)}", missing)
    return CheckResult(
        "required_files",
        PASS,
        f"{len(REQUIRED_FILES)} Phase 1 implementation and evidence files are present.",
        REQUIRED_FILES,
    )


def check_api_and_security_contracts() -> CheckResult:
    routes = _read("app/hcam/camera_registry/routes.py")
    imports = _read("app/hcam/camera_registry/import_routes.py")
    security = _read("app/hcam/security/auth.py")
    models = _read("app/hcam/camera_registry/models.py")
    missing: list[str] = []
    missing.extend(
        _missing_terms(
            routes,
            [
                "@router.get(",
                "@router.post(",
                "@router.patch(",
                '"/{camera_id}"',
                "If-Match",
                "X-HCAM-Reason",
                "allowed_departments",
            ],
        )
    )
    missing.extend(
        _missing_terms(imports, ["MAX_SYNCHRONOUS_CAMERAS", "PLATFORM_ADMIN"])
    )
    missing.extend(
        _missing_terms(
            security,
            [
                "UnconfiguredAuthenticator",
                "Local development authentication is forbidden in production",
                "camera.viewer",
                "camera.editor",
                "platform.admin",
            ],
        )
    )
    missing.extend(_missing_terms(models, ["version_id_col", "version_id"]))
    if missing:
        return CheckResult(
            "api_security_contracts",
            FAIL,
            f"missing contract terms: {', '.join(missing)}",
            [
                "app/hcam/camera_registry/routes.py",
                "app/hcam/camera_registry/import_routes.py",
                "app/hcam/security/auth.py",
                "app/hcam/camera_registry/models.py",
            ],
        )
    return CheckResult(
        "api_security_contracts",
        PASS,
        "Read, write, import, authorization, and concurrency contracts are present.",
        [
            "app/hcam/camera_registry/routes.py",
            "app/hcam/camera_registry/import_routes.py",
            "app/hcam/security/auth.py",
            "app/hcam/camera_registry/models.py",
        ],
    )


def check_safety_documentation() -> CheckResult:
    content = "\n".join(
        [
            _read("docs/phase-1/README.md"),
            _read("docs/phase-1/security-and-management.md"),
            _read("docs/phase-1/readiness-report.md"),
        ]
    )
    required = [
        "No CCTV footage",
        "not production credentials",
        "No production identity integration",
        "Government",
        "biometrics",
        "watchlists",
        "ready_for_owner_review",
    ]
    missing = _missing_terms(content, required)
    if missing:
        return CheckResult(
            "safety_documentation",
            FAIL,
            f"missing safety terms: {', '.join(missing)}",
            ["docs/phase-1/README.md", "docs/phase-1/security-and-management.md"],
        )
    return CheckResult(
        "safety_documentation",
        PASS,
        "Phase 1 safety, identity, and future-integration boundaries are documented.",
        [
            "docs/phase-1/README.md",
            "docs/phase-1/security-and-management.md",
            "docs/phase-1/readiness-report.md",
        ],
    )


def check_acceptance_gate() -> CheckResult:
    path = "docs/phase-1/acceptance-checklist.md"
    content = _read(path)
    unchecked = [
        match.group(1).strip()
        for match in re.finditer(r"^- \[ \] (.+(?:\n  .+)*)", content, re.MULTILINE)
    ]
    unexpected = [
        item
        for item in unchecked
        if not item.startswith("Owner accepts Phase 1 and authorizes Phase 2 planning")
    ]
    if unexpected:
        return CheckResult(
            "acceptance_gate",
            FAIL,
            f"unexpected incomplete checklist items: {', '.join(unexpected)}",
            [path],
        )
    if unchecked:
        return CheckResult(
            "acceptance_gate",
            MANUAL,
            "Project-owner Phase 1 acceptance is pending.",
            [item.replace("\n", " ") for item in unchecked],
        )
    return CheckResult("acceptance_gate", PASS, "Phase 1 owner gate is accepted.", [path])


def check_owner_review_packet() -> CheckResult:
    path = "docs/phase-1/owner-review.md"
    content = _read(path)
    required = [
        "I accept Phase 1 and authorize Phase 2 planning under the documented safety boundaries.",
        "Implementation PR #21",
        "Post-merge `main` validation run",
        "Manual gate issue #20",
        "production CCTV access",
        "Government database",
        "AI processing of real people",
    ]
    missing = _missing_terms(content, required)
    if missing:
        return CheckResult(
            "owner_review_packet",
            FAIL,
            f"missing owner-review terms: {', '.join(missing)}",
            [path],
        )
    return CheckResult(
        "owner_review_packet",
        PASS,
        "Owner decision, published evidence, and safety boundaries are documented.",
        [path],
    )


def _run(command: list[str], *, env: dict[str, str] | None = None) -> tuple[str, str | None]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    rendered = " ".join(command)
    evidence = f"{rendered} -> exit {completed.returncode}"
    if completed.returncode == 0:
        return evidence, None
    detail = completed.stderr.strip() or completed.stdout.strip()
    return evidence, f"{rendered}: {detail}"


def run_validation_commands() -> CheckResult:
    evidence: list[str] = []
    failures: list[str] = []
    commands = [
        [sys.executable, "-m", "compileall", "-q", "app", "tools", "migrations"],
        [sys.executable, "-m", "pytest", "-q"],
        ["git", "diff", "--check"],
    ]
    for command in commands:
        command_evidence, failure = _run(command)
        evidence.append(command_evidence)
        if failure:
            failures.append(failure)

    with tempfile.TemporaryDirectory(prefix="hcam-phase1-") as temp_dir:
        database_path = (Path(temp_dir) / "migration.db").as_posix()
        migration_env = {**os.environ, "HCAM_DATABASE_URL": f"sqlite:///{database_path}"}
        for arguments in (["upgrade", "head"], ["check"]):
            command = [sys.executable, "-m", "alembic", *arguments]
            command_evidence, failure = _run(command, env=migration_env)
            evidence.append(command_evidence)
            if failure:
                failures.append(failure)

    if failures:
        return CheckResult("validation_commands", FAIL, "; ".join(failures), evidence)
    return CheckResult(
        "validation_commands",
        PASS,
        "Compile, tests, migration upgrade/drift, and diff checks passed.",
        evidence,
    )


def build_readiness_report(run_validation: bool = False) -> ReadinessReport:
    checks = [
        check_required_files(),
        check_api_and_security_contracts(),
        check_safety_documentation(),
        check_owner_review_packet(),
        check_acceptance_gate(),
    ]
    if run_validation:
        checks.append(run_validation_commands())

    failures = sum(check.status == FAIL for check in checks)
    manual_gates = sum(1 for check in checks if check.status == MANUAL)
    if failures:
        status_name = "not_ready"
    elif manual_gates:
        status_name = "ready_for_owner_review"
    else:
        status_name = "complete"
    return ReadinessReport(status_name, failures, manual_gates, checks)


def print_text_report(report: ReadinessReport) -> None:
    print(f"Phase 1 readiness: {report.status}")
    print(f"Failures: {report.failures}")
    print(f"Manual gates: {report.manual_gates}")
    print()
    for check in report.checks:
        print(f"[{check.status}] {check.name}: {check.detail}")
        for item in check.evidence:
            print(f"  - {item}")
        print()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify H-CAM Phase 1 readiness.")
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
