#!/usr/bin/env python3
"""Verify the planning-only P3.4 geometry and event package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"

AUTHORIZATION = "contracts/phase-3/p3-4-planning-authorization.json"
ENTRY_GATES = "contracts/phase-3/p3-4-entry-gates.json"
OWNER_DECISIONS = "contracts/phase-3/p3-4-owner-decisions.json"
START_AUTHORIZATION = "contracts/phase-3/p3-4-start-authorization.json"
P3_3_ACCEPTANCE = "contracts/phase-3/p3-3-acceptance.json"
P3_3_ACCEPTED_DIGEST = (
    "0BE4154E28A4D1A18AC8DA9F8D018CDBEB18F0457DDD1ECC2109D60A956ACA96"
)
P3_3_ACCEPTED_HEAD = "207cc9cef89e531aa9328f311db86bf46b6c9cd9"
P3_4_BASELINE_HEAD = "5887096c2d173a1db1337ed7c7c1db141904cfd3"

DECISION_IDS = (
    "D-P3.4-001",
    "D-P3.4-002",
    "D-P3.4-003",
    "D-P3.4-004",
    "D-P3.4-START",
)
APPROVED_DECISION_IDS = DECISION_IDS[:4]
P3_4_ACCEPTED_PLANNING_DIGEST = (
    "E3D0D0DEB5AE20D68AF6A5CE72229BDC63AE55B4200C7E2A011CFA834AFBEBF0"
)
P3_4_TECHNICAL_BASELINE_HEAD = "f9a798f5103da1249ecc5b3e86eb4de7166d8fb9"
SELECTED_OPTIONS = {
    "D-P3.4-001": "hybrid_shapely_2_1_2_runtime_and_postgis_authoritative_geometry",
    "D-P3.4-002": "visual_rule_graph_typed_temporal_nodes_and_constrained_cel",
    "D-P3.4-003": "balanced_event_time_sequence_ordering_bounded_lateness_and_deterministic_replay",
    "D-P3.4-004": "bounded_postgresql_postgis_state_transactional_outbox_inherited_retention_and_c10_evidence",
}

REQUIRED_PROHIBITIONS = {
    "runtime_geometry_or_event_implementation",
    "dependency_or_model_download",
    "database_migration_or_api_addition",
    "generated_or_real_inference_execution",
    "physical_camera_onvif_media_or_sentinel_stream_access",
    "real_public_private_government_police_or_scraped_media",
    "external_dataset_access",
    "identity_biometric_reidentification_or_cross_camera_linkage",
    "watchlist_vehicle_owner_or_government_database_matching",
    "operational_alerting_autonomous_action_or_enforcement",
    "pilot_production_or_statewide_deployment",
    "remote_git_push_pull_request_or_merge",
    "p3_5_or_later_work",
}

PRIMARY_SOURCE_HOSTS = {
    "beam.apache.org",
    "docs.ogc.org",
    "docs.python.org",
    "hypothesis.readthedocs.io",
    "shapely.readthedocs.io",
    "www.postgresql.org",
}

PACKAGE_FILES = (
    ".github/workflows/python-ci.yml",
    "README.md",
    "contracts/phase-3/README.md",
    "contracts/phase-3/p3-3-acceptance.json",
    AUTHORIZATION,
    ENTRY_GATES,
    OWNER_DECISIONS,
    START_AUTHORIZATION,
    "docs/phase-3/README.md",
    "docs/phase-3/decision-register.md",
    "docs/phase-3/implementation-backlog.md",
    "docs/phase-3/p3-4-decision-packet.md",
    "docs/phase-3/p3-4-plan.md",
    "docs/phase-3/p3-4-owner-decisions.md",
    "docs/phase-3/p3-4-planning-authorization.md",
    "docs/phase-3/p3-4-research-record.md",
    "docs/phase-3/p3-4-start-authorization.md",
    "pyproject.toml",
    "tests/test_phase34_readiness.py",
    "tools/phase34_readiness.py",
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


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _read_json(relative_path: str) -> dict[str, object]:
    document = json.loads(_read(relative_path))
    if not isinstance(document, dict):
        raise ValueError(f"{relative_path} must contain a JSON object")
    return document


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
        manifest.append(f"{relative_path} sha256={file_digest} bytes={len(payload)}")
    return digest.hexdigest().upper(), tuple(manifest)


def check_required_files() -> Check:
    missing = tuple(path for path in PACKAGE_FILES if not (ROOT / path).is_file())
    if missing:
        return Check(
            "required_files", FAIL, "P3.4 planning files are missing.", missing
        )
    return Check(
        "required_files",
        PASS,
        f"All {len(PACKAGE_FILES)} planning package files exist.",
    )


def check_planning_authorization() -> Check:
    try:
        record = _read_json(AUTHORIZATION)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("planning_authorization", FAIL, str(exc))

    failures: list[str] = []
    expected = {
        "decision_id": "D-P3.4-PLAN-AUTH",
        "record_id": "D-P3.4-PLAN-AUTH",
        "status": "authorized",
        "authorized_by": "mayank-admin",
        "scope": "phase3.p3_4.geometry_and_event_primitives.planning_only",
        "baseline_repository_head": P3_4_BASELINE_HEAD,
        "planning_authorized": True,
        "implementation_authorized": False,
        "next_milestone_authorized": False,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            failures.append(key)
    if not REQUIRED_PROHIBITIONS.issubset(set(record.get("prohibited_actions", []))):
        failures.append("prohibited_actions")
    if failures:
        return Check(
            "planning_authorization",
            FAIL,
            "P3.4 planning authorization boundary changed.",
            tuple(failures),
        )
    return Check(
        "planning_authorization",
        PASS,
        "Planning is authorized while implementation and later work remain prohibited.",
    )


def check_accepted_dependency() -> Check:
    try:
        record = _read_json(P3_3_ACCEPTANCE)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("accepted_p3_3_dependency", FAIL, str(exc))

    if (
        record.get("decision_id") != "D-P3.3-ACCEPTANCE"
        or record.get("status") != "accepted"
        or record.get("accepted_by") != "mayank-admin"
        or record.get("accepted_repository_head") != P3_3_ACCEPTED_HEAD
        or record.get("evidence_package_digest") != P3_3_ACCEPTED_DIGEST
        or record.get("next_phase_authorized") is not False
    ):
        return Check(
            "accepted_p3_3_dependency",
            FAIL,
            "The exact accepted P3.3 dependency identity changed.",
        )
    return Check(
        "accepted_p3_3_dependency",
        PASS,
        "P3.4 planning is bound to the accepted anonymous stream-local P3.3 package.",
    )


def check_owner_decisions() -> Check:
    try:
        record = _read_json(OWNER_DECISIONS)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("owner_technical_decisions", FAIL, str(exc))

    decisions = record.get("decisions")
    if not isinstance(decisions, list):
        return Check(
            "owner_technical_decisions",
            FAIL,
            "P3.4 owner decisions must be an array.",
        )
    actual = {
        decision.get("decision_id"): decision.get("selected_option")
        for decision in decisions
        if isinstance(decision, dict)
    }
    required_prohibitions = {
        "dependency_package_or_model_download",
        "runtime_geometry_rule_or_event_implementation",
        "database_extension_migration_or_api_addition",
        "physical_camera_onvif_media_or_sentinel_stream_access",
        "identity_biometric_reidentification_or_cross_camera_linkage",
        "operational_alerting_autonomous_action_or_enforcement",
        "remote_git_push_pull_request_or_merge",
        "p3_5_or_later_work",
    }
    if (
        record.get("record_id") != "D-P3.4-TECHNICAL-DECISIONS"
        or record.get("status") != "accepted"
        or record.get("accepted_by") != "mayank-admin"
        or tuple(record.get("decision_ids", ())) != APPROVED_DECISION_IDS
        or actual != SELECTED_OPTIONS
        or record.get("implementation_authorized") is not False
        or record.get("start_decision_id") != "D-P3.4-START"
        or record.get("start_status") != "pending_owner_authorization"
        or not required_prohibitions.issubset(set(record.get("non_authorization", [])))
    ):
        return Check(
            "owner_technical_decisions",
            FAIL,
            "P3.4 selected technical baseline or continuing boundary changed.",
        )
    return Check(
        "owner_technical_decisions",
        PASS,
        "Four exact owner-selected technical options are accepted and remain independently recorded.",
        APPROVED_DECISION_IDS,
    )


def check_start_authorization() -> Check:
    try:
        record = _read_json(START_AUTHORIZATION)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("implementation_authorization", FAIL, str(exc))

    required_work = {
        "exact_dependency_acquisition_and_supply_chain_evidence",
        "local_default_off_production_forbidden_geometry_rule_and_event_implementation",
        "additive_postgresql_postgis_migration_and_sqlite_compatibility",
        "generated_only_contract_fixture_and_c10_execution",
        "bounded_api_rbac_audit_metrics_outbox_and_retention_implementation",
        "local_tests_evidence_documentation_and_checkpoint_commits",
    }
    prohibited = {
        "physical_camera_onvif_media_or_sentinel_stream_access",
        "real_public_private_government_police_or_scraped_media",
        "external_dataset_download_training_finetuning_or_accuracy_claims",
        "face_biometric_identity_reidentification_or_cross_camera_linkage",
        "watchlists_vehicle_owner_lookup_or_government_database_matching",
        "operational_alerting_autonomous_action_or_enforcement",
        "pilot_production_statewide_deployment_or_performance_claims",
        "remote_git_push_pull_request_or_merge",
        "p3_5_or_later_work",
    }
    if (
        record.get("authorization_id") != "D-P3.4-START"
        or record.get("decision_id") != "D-P3.4-START"
        or record.get("status") != "authorized"
        or record.get("authorized_by") != "mayank-admin"
        or record.get("owner_statement_received") != "I authorize D-P3.4-START"
        or record.get("baseline_planning_digest")
        != P3_4_ACCEPTED_PLANNING_DIGEST
        or record.get("baseline_repository_head") != P3_4_TECHNICAL_BASELINE_HEAD
        or record.get("selected_technical_baseline_record")
        != "p3-4-owner-decisions.json"
        or record.get("implementation_authorized") is not True
        or record.get("final_acceptance_granted") is not False
        or not required_work.issubset(set(record.get("authorized_work", [])))
        or not prohibited.issubset(set(record.get("prohibited_work", [])))
    ):
        return Check(
            "implementation_authorization",
            FAIL,
            "D-P3.4-START identity, scope, baseline, or exclusions changed.",
        )
    return Check(
        "implementation_authorization",
        PASS,
        "D-P3.4-START authorizes bounded local generated-only implementation without final acceptance.",
    )


def check_entry_gates() -> Check:
    try:
        record = _read_json(ENTRY_GATES)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("entry_gates", FAIL, str(exc))

    decisions = record.get("decisions")
    if not isinstance(decisions, list):
        return Check("entry_gates", FAIL, "P3.4 decisions must be an array.")
    actual_ids = tuple(
        decision.get("decision_id")
        for decision in decisions
        if isinstance(decision, dict)
    )
    statuses = tuple(
        decision.get("status") for decision in decisions if isinstance(decision, dict)
    )
    selections = {
        decision.get("decision_id"): decision.get("selected_option")
        for decision in decisions
        if isinstance(decision, dict)
        and decision.get("decision_id") in APPROVED_DECISION_IDS
    }
    start = decisions[-1] if decisions and isinstance(decisions[-1], dict) else {}
    if (
        actual_ids != DECISION_IDS
        or statuses != ("owner_approved",) * 5
        or selections != SELECTED_OPTIONS
        or start.get("selected_option")
        != "authorize_generated_only_implementation_after_gates_001_through_004"
        or start.get("decided_by") != "mayank-admin"
        or record.get("status") != "implementation_authorized_generated_only"
        or record.get("manual_gate_count") != 0
        or record.get("owner_decisions_completed") != 4
        or record.get("owner_decision_record") != "p3-4-owner-decisions.json"
        or record.get("implementation_authorization_record")
        != "p3-4-start-authorization.json"
        or record.get("implementation_authorized") is not True
    ):
        return Check(
            "entry_gates",
            FAIL,
            "P3.4 owner gates or implementation status changed.",
        )
    return Check(
        "entry_gates",
        PASS,
        "All four technical decisions and D-P3.4-START are explicitly owner approved.",
        DECISION_IDS,
    )


def check_research_sources() -> Check:
    try:
        research = _read("docs/phase-3/p3-4-research-record.md")
    except OSError as exc:
        return Check("primary_source_research", FAIL, str(exc))

    urls = tuple(re.findall(r"https://[^)\s]+", research))
    hosts = {urlparse(url).hostname for url in urls}
    missing = PRIMARY_SOURCE_HOSTS - hosts
    unapproved = {host for host in hosts if host not in PRIMARY_SOURCE_HOSTS}
    if missing or unapproved:
        evidence = tuple(sorted(f"missing:{host}" for host in missing)) + tuple(
            sorted(f"unapproved:{host}" for host in unapproved)
        )
        return Check(
            "primary_source_research",
            FAIL,
            "P3.4 primary-source provenance changed.",
            evidence,
        )
    return Check(
        "primary_source_research",
        PASS,
        f"Research cites {len(urls)} primary-source references on approved hosts.",
    )


def check_plan_contract() -> Check:
    try:
        plan = _read("docs/phase-3/p3-4-plan.md")
        packet = _read("docs/phase-3/p3-4-decision-packet.md")
    except OSError as exc:
        return Check("plan_contract", FAIL, str(exc))

    required_plan_tokens = (
        "normalized image-space",
        "PostgreSQL/PostGIS is authoritative",
        "GeometryRuleV1",
        "Visual Rule Graph And Constrained CEL",
        "bottom_center",
        "line.crossing",
        "zone.entry",
        "zone.exit",
        "zone.dwell.threshold_met",
        "zone.occupancy.threshold_entered",
        "event-time",
        "zoneinfo",
        "transactional outbox",
        "16,384",
        "DATA-GEO-EVT-GEN-C10",
        "alert_state: not_evaluated",
        "acceptance remains separately gated",
    )
    missing = tuple(token for token in required_plan_tokens if token not in plan)
    missing += tuple(decision for decision in DECISION_IDS if decision not in packet)
    if missing:
        return Check(
            "plan_contract",
            FAIL,
            "The P3.4 technical plan or owner packet is incomplete.",
            missing,
        )
    return Check(
        "plan_contract",
        PASS,
        "Geometry, state, time, idempotency, limits, evidence, and owner choices are explicit.",
    )


def check_dependency_boundary() -> Check:
    pyproject = _read("pyproject.toml").lower()
    lock = _read("uv.lock").lower()
    compose = (
        _read("deploy/compose.phase1.yaml") + _read("deploy/compose.phase2.yaml")
    ).lower()
    selected_present = (
        "shapely" in pyproject
        or 'name = "shapely"' in lock
        or "cel-python" in pyproject
        or 'name = "cel-python"' in lock
        or "postgis/postgis" in compose
    )
    detail = (
        "Selected P3.4 dependency acquisition has started under D-P3.4-START."
        if selected_present
        else "Selected P3.4 dependencies are authorized but not yet installed."
    )
    return Check(
        "dependency_boundary",
        PASS,
        detail,
    )


def check_documentation_sync() -> Check:
    required = {
        "README.md": ("tools/phase34_readiness.py", "D-P3.4-START"),
        "docs/phase-3/README.md": (
            "[P3.4 plan](p3-4-plan.md)",
            "[P3.4 owner decisions](p3-4-owner-decisions.md)",
            "Implementation and technical evidence are",
            "exact-digest final acceptance remains pending",
        ),
        "docs/phase-3/implementation-backlog.md": (
            "D-P3.4-PLAN-AUTH",
            "D-P3.4-START",
        ),
        "docs/phase-3/decision-register.md": ("DR-0033", "D-P3.4-START"),
        "contracts/phase-3/README.md": (
            "p3-4-entry-gates.json",
            "p3-4-owner-decisions.json",
        ),
        ".github/workflows/python-ci.yml": (
            "python tools/phase34_readiness.py --strict",
        ),
    }
    missing: list[str] = []
    for relative_path, tokens in required.items():
        try:
            document = _read(relative_path)
            if any(token not in document for token in tokens):
                missing.append(relative_path)
        except OSError:
            missing.append(relative_path)
    if missing:
        return Check(
            "documentation_sync",
            FAIL,
            "P3.4 status, planning links, or CI verification are out of sync.",
            tuple(missing),
        )
    return Check(
        "documentation_sync",
        PASS,
        "Root, phase index, backlog, decision register, contract index, and CI are synchronized.",
    )


def check_source_clean() -> Check:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return Check("clean_source", FAIL, "Unable to inspect Git source state.")
    dirty = tuple(line for line in result.stdout.splitlines() if line.strip())
    if dirty:
        return Check(
            "clean_source",
            FAIL,
            "Repository contains uncommitted changes.",
            dirty,
        )
    return Check("clean_source", PASS, "Repository source is clean.")


def build_readiness_report(*, require_clean_source: bool = False) -> Report:
    checks = [
        check_required_files(),
        check_planning_authorization(),
        check_accepted_dependency(),
        check_owner_decisions(),
        check_start_authorization(),
        check_entry_gates(),
        check_research_sources(),
        check_plan_contract(),
        check_dependency_boundary(),
        check_documentation_sync(),
    ]
    if require_clean_source:
        checks.append(check_source_clean())

    failures = sum(check.status == FAIL for check in checks)
    manual_gates = sum(
        len(check.evidence) if check.name == "entry_gates" else 1
        for check in checks
        if check.status == MANUAL
    )
    try:
        digest, _ = package_digest()
    except OSError:
        digest = "UNAVAILABLE"
    status = "invalid"
    if failures == 0:
        status = "implementation_authorized_generated_only"
    return Report(
        status=status,
        scope="phase3.p3_4.geometry_and_event_primitives.generated_only_start",
        package_digest=digest,
        failures=failures,
        manual_gates=manual_gates,
        checks=tuple(checks),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when a technical planning check fails.",
    )
    parser.add_argument(
        "--require-decisions",
        action="store_true",
        help="Exit 2 while owner decisions remain pending.",
    )
    parser.add_argument(
        "--require-clean-source",
        action="store_true",
        help="Require an empty Git porcelain status.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = build_readiness_report(require_clean_source=args.require_clean_source)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"Phase 3 P3.4 planning readiness: {report.status}")
        print(f"Package digest: {report.package_digest}")
        print(f"Technical failures: {report.failures}")
        print(f"Manual owner gates: {report.manual_gates}")
        for check in report.checks:
            print(f"- {check.status.upper()}: {check.name}: {check.detail}")

    if args.strict and report.failures:
        return 1
    if args.require_decisions and report.manual_gates:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
