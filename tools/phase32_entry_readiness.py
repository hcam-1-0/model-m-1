#!/usr/bin/env python3
"""Verify the fail-closed pre-P3.2 owner-decision state."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PASS = "pass"
FAIL = "fail"
EXPECTED_RECORD_DIGEST = (
    "382A5ACB82760A434B6373F19DCE42A98564D48A34519F8B6EE8766B736885F2"
)
ACCEPTED_P31_DIGEST = (
    "956F6521E21BF0FB43741F97768194617DE881B1BD1644E03DDC33ED5FDC0618"
)
ENTRY_RECORD = "contracts/phase-3/p3-2-entry-gates.json"
PACKET = "docs/phase-3/p3-2-entry-decision-packet.md"
CANDIDATE = "contracts/phase-3/p3-1/candidates/candidate-det-r0.json"
REQUIRED_FILES = (
    ENTRY_RECORD,
    PACKET,
    CANDIDATE,
    "contracts/phase-3/p3-0-owner-decisions.json",
    "contracts/phase-3/p3-1-acceptance.json",
    "docs/phase-3/README.md",
    "docs/phase-3/implementation-backlog.md",
    "docs/phase-3/decision-register.md",
    "tools/phase32_entry_readiness.py",
    "tests/test_phase32_entry_readiness.py",
    ".github/workflows/python-ci.yml",
)
EXPECTED_DECISIONS = [
    ("D-P3.2-001", "pending"),
    ("D-P3.2-002", "blocked_pending_evidence"),
    ("D-P3.2-003", "blocked_pending_evidence"),
    ("D-P3.2-004", "planned_not_approved"),
    ("D-P3.2-START", "not_authorized"),
]
EXPECTED_NON_AUTHORIZATION = {
    "p3_2_implementation",
    "model_or_dataset_acquisition",
    "training_finetuning_export_or_inference",
    "decoder_or_gpu_execution",
    "camera_sentinel_or_media_access",
    "government_private_scraped_or_unreviewed_data",
    "identity_watchlist_or_owner_lookup",
    "operational_alerting_or_autonomous_action",
    "pilot_production_or_statewide_deployment",
    "remote_git_push_pull_request_or_merge",
}


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str
    evidence: list[str]


@dataclass(frozen=True)
class EntryReadinessReport:
    status: str
    scope: str
    record_digest: str
    failures: int
    manual_gates: int
    checks: list[CheckResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scope": self.scope,
            "record_digest": self.record_digest,
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


def canonical_digest(document: dict[str, Any]) -> str:
    canonical = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest().upper()


def check_required_files() -> CheckResult:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        return CheckResult("required_files", FAIL, "Required files are missing.", missing)
    return CheckResult(
        "required_files",
        PASS,
        f"All {len(REQUIRED_FILES)} pre-P3.2 governance files exist.",
        list(REQUIRED_FILES),
    )


def check_entry_record() -> CheckResult:
    try:
        record = _read_json(ENTRY_RECORD)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("entry_record", FAIL, f"Entry record is invalid: {exc}", [])

    failures: list[str] = []
    digest = canonical_digest(record)
    if digest != EXPECTED_RECORD_DIGEST:
        failures.append("canonical entry record changed without verifier review")
    if record.get("contract_format") != "hcam.phase3.p3_2.entry-gates.v1":
        failures.append("contract format changed")
    if record.get("record_id") != "P3.2-ENTRY-2026-08-24":
        failures.append("record identifier changed")
    if record.get("prepared_on") != "2026-08-24":
        failures.append("prepared date changed")
    if record.get("accountable_owner_id") != "mayank-admin":
        failures.append("accountable owner changed")
    if record.get("status") != "blocked_pending_owner_decisions":
        failures.append("P3.2 blocked state changed")
    if record.get("start_authorization") != "not_authorized":
        failures.append("P3.2 start authorization is not fail-closed")

    decisions = record.get("decisions")
    decision_pairs = (
        [(item.get("decision_id"), item.get("status")) for item in decisions]
        if isinstance(decisions, list)
        and all(isinstance(item, dict) for item in decisions)
        else []
    )
    if decision_pairs != EXPECTED_DECISIONS:
        failures.append("ordered decision inventory or pending states changed")
    start = decisions[-1] if decision_pairs == EXPECTED_DECISIONS else {}
    if start.get("requires") != [item[0] for item in EXPECTED_DECISIONS[:-1]]:
        failures.append("P3.2 start dependencies changed")

    non_authorization = record.get("non_authorization")
    if (
        not isinstance(non_authorization, list)
        or len(non_authorization) != len(EXPECTED_NON_AUTHORIZATION)
        or set(non_authorization) != EXPECTED_NON_AUTHORIZATION
    ):
        failures.append("non-authorization boundary changed or contains duplicates")

    expected_reference = {
        "artifact_downloads": 0,
        "artifact_eligibility": "blocked",
        "artifact_execution": False,
        "candidate_id": "DET-R0",
        "family": "YOLOX-Tiny",
        "input_size": 416,
        "runtime": "onnxruntime_cpu",
        "runtime_status": "planned_not_approved",
    }
    if record.get("planned_reference") != expected_reference:
        failures.append("planned reference boundary changed")

    if failures:
        return CheckResult("entry_record", FAIL, "; ".join(failures), [ENTRY_RECORD])
    return CheckResult(
        "entry_record",
        PASS,
        "Five ordered owner decisions remain fail-closed; P3.2 start is not authorized.",
        [ENTRY_RECORD, f"canonical_sha256={digest}"],
    )


def check_accepted_dependencies() -> CheckResult:
    files = [
        "contracts/phase-3/p3-0-owner-decisions.json",
        "contracts/phase-3/p3-1-acceptance.json",
        ENTRY_RECORD,
    ]
    try:
        p30 = _read_json(files[0])
        p31 = _read_json(files[1])
        entry = _read_json(files[2])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("accepted_dependencies", FAIL, str(exc), files)

    failures: list[str] = []
    if p30.get("status") != "p3_0_accepted":
        failures.append("P3.0 is not accepted")
    if (
        p31.get("record_id") != "D-P3.1-ACCEPTANCE"
        or p31.get("status") != "accepted"
        or p31.get("evidence_package_digest") != ACCEPTED_P31_DIGEST
    ):
        failures.append("P3.1 acceptance identity changed")
    dependencies = entry.get("dependencies")
    expected = {
        "p3_0": {"record_id": "D-P3.0-001", "status": "accepted"},
        "p3_1": {
            "evidence_package_digest": ACCEPTED_P31_DIGEST,
            "record_id": "D-P3.1-ACCEPTANCE",
            "status": "accepted",
        },
    }
    if dependencies != expected:
        failures.append("entry dependency record changed")
    if failures:
        return CheckResult(
            "accepted_dependencies",
            FAIL,
            "; ".join(failures),
            files,
        )
    return CheckResult(
        "accepted_dependencies",
        PASS,
        "P3.0 and the exact digest-bound P3.1 package are accepted dependencies.",
        files,
    )


def check_reference_candidate_blocked() -> CheckResult:
    try:
        candidate = _read_json(CANDIDATE)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("reference_candidate", FAIL, str(exc), [CANDIDATE])

    required_blockers = {
        "exact-checkpoint-unresolved",
        "weight-license-unverified",
        "training-lineage-unverified",
        "model-card-unresolved",
        "sbom-unresolved",
    }
    approval = candidate.get("approval")
    artifact = candidate.get("artifact_identity")
    source = candidate.get("source_reference")
    failures: list[str] = []
    if candidate.get("candidate_id") != "DET-R0":
        failures.append("portable reference candidate changed")
    if candidate.get("eligibility") != "blocked":
        failures.append("DET-R0 is no longer blocked")
    if not isinstance(approval, dict) or approval.get("status") != "pending":
        failures.append("DET-R0 approval is not pending")
    if not isinstance(artifact, dict) or artifact.get("state") != "unresolved":
        failures.append("exact artifact is not unresolved")
    if set(candidate.get("blockers", [])) != required_blockers:
        failures.append("DET-R0 blocker inventory changed")
    if not isinstance(source, dict) or source.get("no_download_performed") is not True:
        failures.append("no-download source evidence changed")
    if failures:
        return CheckResult(
            "reference_candidate",
            FAIL,
            "; ".join(failures),
            [CANDIDATE],
        )
    return CheckResult(
        "reference_candidate",
        PASS,
        "DET-R0 remains metadata-only, unapproved, undownloaded, and blocked by five evidence gaps.",
        [CANDIDATE, *sorted(required_blockers)],
    )


def check_documentation_boundary() -> CheckResult:
    files = [
        PACKET,
        "docs/phase-3/README.md",
        "docs/phase-3/implementation-backlog.md",
        "docs/phase-3/decision-register.md",
    ]
    try:
        packet, index, backlog, decisions = (_read(path) for path in files)
    except OSError as exc:
        return CheckResult("documentation_boundary", FAIL, str(exc), files)

    failures: list[str] = []
    required_packet_terms = (
        "Status: `blocked_pending_owner_decisions`",
        "This packet is not P3.2 authorization.",
        "Current state: `not_authorized`.",
        "This packet does not authorize P3.2",
    )
    failures.extend(
        f"packet boundary is missing: {term}"
        for term in required_packet_terms
        if term not in packet
    )
    link = "[P3.2 entry decision packet](p3-2-entry-decision-packet.md)"
    if link not in index or link not in backlog or link not in decisions:
        failures.append("P3.2 entry packet is not linked from all live indexes")
    if failures:
        return CheckResult(
            "documentation_boundary",
            FAIL,
            "; ".join(failures),
            files,
        )
    return CheckResult(
        "documentation_boundary",
        PASS,
        "Live Phase 3 documents expose the blocked packet and continuing non-authorization.",
        files,
    )


def check_ci_integration() -> CheckResult:
    path = ".github/workflows/python-ci.yml"
    command = "python tools/phase32_entry_readiness.py"
    try:
        workflow = _read(path)
    except OSError as exc:
        return CheckResult("ci_integration", FAIL, str(exc), [path])
    lines = {line.strip() for line in workflow.splitlines()}
    if f"run: {command}" not in lines:
        return CheckResult(
            "ci_integration",
            FAIL,
            "CI does not verify the blocked pre-P3.2 entry state.",
            [path, command],
        )
    return CheckResult(
        "ci_integration",
        PASS,
        "CI verifies the valid blocked state without treating manual gates as approval.",
        [path, command],
    )


def build_readiness_report() -> EntryReadinessReport:
    try:
        digest = canonical_digest(_read_json(ENTRY_RECORD))
    except (OSError, ValueError, json.JSONDecodeError):
        digest = "unavailable"
    checks = [
        check_required_files(),
        check_entry_record(),
        check_accepted_dependencies(),
        check_reference_candidate_blocked(),
        check_documentation_boundary(),
        check_ci_integration(),
    ]
    failures = sum(check.status == FAIL for check in checks)
    return EntryReadinessReport(
        status="not_ready" if failures else "blocked_pending_owner_decisions",
        scope="phase3.p3_2.portable_detection.pre_entry",
        record_digest=digest,
        failures=failures,
        manual_gates=len(EXPECTED_DECISIONS),
        checks=checks,
    )


def print_text_report(report: EntryReadinessReport) -> None:
    print(f"Phase 3 P3.2 entry readiness: {report.status}")
    print(f"Scope: {report.scope}")
    print(f"Entry record digest: {report.record_digest}")
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
        description="Verify the H-CAM pre-P3.2 blocked entry state."
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_readiness_report()
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
