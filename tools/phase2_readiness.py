#!/usr/bin/env python3
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
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"

REQUIRED_FILES = [
    "app/hcam/streams/models.py",
    "app/hcam/streams/schemas.py",
    "app/hcam/streams/repository.py",
    "app/hcam/streams/service.py",
    "app/hcam/streams/routes.py",
    "app/hcam/streams/network.py",
    "app/hcam/streams/probe.py",
    "app/hcam/streams/worker.py",
    "app/hcam/streams/onvif.py",
    "app/hcam/streams/onvif_simulator.py",
    "app/hcam/streams/outbox.py",
    "app/hcam/streams/playback.py",
    "app/hcam/streams/lab.py",
    "app/hcam/streams/lab_publisher.py",
    "migrations/versions/0004_stream_management.py",
    "migrations/versions/0005_playback_sessions.py",
    "deploy/compose.phase2.yaml",
    "deploy/mediamtx.phase2.yml",
    "deploy/observability/hcam-phase2-streams.json",
    "deploy/observability/hcam-phase2-alerts.yml",
    "tools/phase2_lab.py",
    "tools/phase2_failure_drill.py",
    "docs/phase-2/README.md",
    "docs/phase-2/architecture-and-contracts.md",
    "docs/phase-2/adapters-and-health.md",
    "docs/phase-2/playback-security.md",
    "docs/phase-2/synthetic-lab.md",
    "docs/phase-2/operations-and-observability.md",
    "docs/phase-2/safety-and-governance.md",
    "docs/phase-2/build-and-test.md",
    "docs/phase-2/acceptance-checklist.md",
    "docs/phase-2/readiness-report.md",
    "docs/phase-2/owner-review.md",
    "tests/test_stream_management_api.py",
    "tests/test_stream_migration.py",
    "tests/test_stream_probe.py",
    "tests/test_stream_worker.py",
    "tests/test_stream_outbox.py",
    "tests/test_onvif_simulator.py",
    "tests/test_playback_sessions.py",
    "tests/test_phase2_lab.py",
]


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str
    evidence: list[str]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _contract_check(name: str, files: list[str], terms: list[str]) -> Check:
    content = "\n".join(_read(path) for path in files)
    missing = [term for term in terms if term not in content]
    if missing:
        return Check(name, FAIL, f"missing terms: {', '.join(missing)}", files)
    return Check(name, PASS, "Required contracts are present.", files)


def check_files() -> Check:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        return Check("required_files", FAIL, f"missing: {', '.join(missing)}", missing)
    return Check(
        "required_files",
        PASS,
        f"{len(REQUIRED_FILES)} Phase 2 implementation and evidence files are present.",
        REQUIRED_FILES,
    )


def check_acceptance() -> Check:
    path = "docs/phase-2/acceptance-checklist.md"
    unchecked = re.findall(r"^- \[ \] (.+)$", _read(path), re.MULTILINE)
    if unchecked == ["Owner reviews the Phase 2 evidence and explicitly accepts or rejects it"]:
        return Check(
            "owner_gate",
            MANUAL,
            "Explicit Phase 2 owner acceptance is pending.",
            [path],
        )
    if unchecked:
        return Check("owner_gate", FAIL, "Unexpected incomplete checklist items.", unchecked)
    return Check("owner_gate", PASS, "Owner gate is accepted.", [path])


def _run(command: list[str], *, env: dict[str, str] | None = None) -> tuple[str, str | None]:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return " ".join(command), str(exc)
    evidence = f"{' '.join(command)} -> exit {completed.returncode}"
    if completed.returncode == 0:
        return evidence, None
    detail = completed.stderr.strip() or completed.stdout.strip()
    return evidence, detail[-2000:]


def validation() -> Check:
    evidence: list[str] = []
    failures: list[str] = []
    commands = [
        [sys.executable, "-m", "compileall", "-q", "app", "tools", "migrations"],
        [sys.executable, "-m", "ruff", "check", "app", "tests", "tools", "migrations"],
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "tools/phase1_readiness.py", "--json"],
        ["git", "diff", "--check"],
    ]
    for command in commands:
        item, failure = _run(command)
        evidence.append(item)
        if failure:
            failures.append(failure)
    with tempfile.TemporaryDirectory(prefix="hcam-phase2-readiness-") as temp:
        database_url = f"sqlite:///{(Path(temp) / 'migration.db').as_posix()}"
        environment = {**os.environ, "HCAM_DATABASE_URL": database_url}
        for arguments in (["upgrade", "head"], ["check"]):
            item, failure = _run(
                [sys.executable, "-m", "alembic", *arguments], env=environment
            )
            evidence.append(item)
            if failure:
                failures.append(failure)
        secret_root = Path(temp) / "lab-secrets"
        for arguments in (
            ["--secret-root", str(secret_root), "prepare", "--force"],
            ["--secret-root", str(secret_root), "config"],
        ):
            item, failure = _run([sys.executable, "tools/phase2_lab.py", *arguments])
            evidence.append(item)
            if failure:
                failures.append(failure)
    if failures:
        return Check("validation", FAIL, "; ".join(failures), evidence)
    return Check("validation", PASS, "Offline Phase 2 validation passed.", evidence)


def build_report(run_validation: bool) -> dict[str, object]:
    checks = [
        check_files(),
        _contract_check(
            "stream_control_plane",
            [
                "app/hcam/streams/models.py",
                "app/hcam/streams/routes.py",
                "app/hcam/streams/service.py",
                "migrations/versions/0004_stream_management.py",
            ],
            [
                "StreamEndpoint",
                "StreamHealthCurrent",
                "StreamProbeRun",
                "StreamEventOutbox",
                "If-Match",
                "X-HCAM-Reason",
                "allowed_departments",
            ],
        ),
        _contract_check(
            "health_worker",
            [
                "app/hcam/streams/probe.py",
                "app/hcam/streams/worker.py",
                "app/hcam/streams/network.py",
            ],
            [
                "shell=False",
                "network_policy_denied",
                "with_for_update(skip_locked=True)",
                "hcam.stream.health.changed.v1",
                "timedelta(days=7)",
            ],
        ),
        _contract_check(
            "adapter_egress_hardening",
            [
                "app/hcam/streams/network.py",
                "app/hcam/streams/onvif.py",
                "app/hcam/streams/probe.py",
                "tests/test_onvif_simulator.py",
                "tests/test_stream_probe.py",
            ],
            [
                "stream hostname must be explicitly allowlisted",
                "ProxyHandler({})",
                "_NoRedirectHandler",
                "onvif_redirect_denied",
                "_run_bounded_process",
                "test_bounded_process_terminates_during_output_flood",
                "test_onvif_resolver_does_not_follow_redirects",
            ],
        ),
        _contract_check(
            "event_delivery",
            [
                "app/hcam/streams/outbox.py",
                "deploy/compose.phase2.yaml",
                "tests/test_stream_outbox.py",
            ],
            [
                "StreamEventOutboxDispatcher",
                "StreamEventDeliveryError",
                "with_for_update(skip_locked=True)",
                "stream-event-dispatcher",
                "published_at",
            ],
        ),
        _contract_check(
            "playback_security",
            [
                "app/hcam/streams/playback.py",
                "deploy/mediamtx.phase2.yml",
                "docs/phase-2/playback-security.md",
            ],
            [
                "ES256",
                "P-256",
                "mediamtx_permissions",
                '"action": "read"',
                "no-store",
                "record: false",
            ],
        ),
        _contract_check(
            "synthetic_safety",
            [
                "deploy/compose.phase2.yaml",
                "tools/phase2_lab.py",
                "docs/phase-2/safety-and-governance.md",
            ],
            [
                "50",
                "127.0.0.1",
                "HCAM_ALLOW_SYNTHETIC_LAB",
                "real-person footage",
                "Government data",
                "biometrics",
            ],
        ),
        check_acceptance(),
    ]
    if run_validation:
        checks.append(validation())
    failures = sum(check.status == FAIL for check in checks)
    manual = sum(check.status == MANUAL for check in checks)
    status = "not_ready" if failures else "ready_for_owner_review" if manual else "complete"
    return {
        "status": status,
        "failures": failures,
        "manual_gates": manual,
        "checks": [asdict(check) for check in checks],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify H-CAM Phase 2 readiness")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--run-validation", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.run_validation)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Phase 2 readiness: {report['status']}")
        print(f"Failures: {report['failures']}")
        print(f"Manual gates: {report['manual_gates']}")
        for check in report["checks"]:
            print(f"[{check['status']}] {check['name']}: {check['detail']}")
    if report["failures"]:
        return 1
    if args.strict and report["manual_gates"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
