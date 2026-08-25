#!/usr/bin/env python3
"""Offline Phase 3 P3.0 readiness and owner-gate verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE3 = ROOT / "docs" / "phase-3"
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"
OWNER_GATE_IDS = ("P3-G1", "P3-G2", "P3-G3", "P3-G4")
_OWNER_GATE_PATTERN = re.compile(
    r"^- \[(?P<mark>[ xX])\] `(?P<gate_id>P3-G\d+)` (?P<title>.+)$",
    re.MULTILINE,
)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+)\)")

REQUIRED_FILES = (
    "uv.lock",
    "app/hcam/analytics/contracts.py",
    "app/hcam/analytics/fixtures.py",
    "app/hcam/analytics/geometry.py",
    "app/hcam/analytics/models.py",
    "app/hcam/analytics/repository.py",
    "app/hcam/analytics/routes.py",
    "app/hcam/analytics/runtime.py",
    "app/hcam/analytics/schemas.py",
    "app/hcam/analytics/service.py",
    "app/hcam/analytics/taxonomy.py",
    "app/hcam/security/errors.py",
    "migrations/versions/0008_analytics_assignments.py",
    "contracts/phase-3/README.md",
    "contracts/phase-3/analytics-contracts.json",
    "contracts/phase-3/openapi.json",
    "contracts/phase-3/database.json",
    "contracts/phase-3/p3-0-owner-decisions.json",
    "contracts/phase-3/p3-2-entry-gates.json",
    "contracts/phase-3/fixtures/assignment-v1.json",
    "contracts/phase-3/fixtures/observation-created-v1.json",
    "contracts/phase-3/fixtures/track-updated-v1.json",
    "contracts/phase-3/fixtures/analytic-event-created-v1.json",
    "contracts/phase-3/fixtures/model-deployment-changed-v1.json",
    "contracts/phase-3/fixtures/taxonomy-draft-v1.json",
    "contracts/phase-3/fixtures/geometry-line-draft-v1.json",
    "contracts/phase-3/fixtures/geometry-zone-draft-v1.json",
    "contracts/phase-3/fixtures/runtime-adapter-unconfigured-v1.json",
    "contracts/phase-3/fixtures/runtime-request-v1.json",
    "contracts/phase-3/fixtures/runtime-result-unconfigured-v1.json",
    "deploy/observability/hcam-phase3-control-plane.json",
    "deploy/observability/hcam-phase3-control-plane-alerts.yml",
    "docs/phase-3/README.md",
    "docs/phase-3/acceptance-checklist.md",
    "docs/phase-3/assignment-control-plane.md",
    "docs/phase-3/build-and-test.md",
    "docs/phase-3/decision-register.md",
    "docs/phase-3/implementation-backlog.md",
    "docs/phase-3/owner-review.md",
    "docs/phase-3/p3-0-owner-decisions.md",
    "docs/phase-3/p3-2-entry-decision-packet.md",
    "docs/phase-3/readiness-report.md",
    "docs/phase-3/security-privacy-and-safety.md",
    "tests/test_analytics_assignment_api.py",
    "tests/test_analytics_assignment_migration.py",
    "tests/test_analytics_contracts.py",
    "tests/test_analytics_geometry.py",
    "tests/test_analytics_runtime.py",
    "tests/test_analytics_taxonomy.py",
    "tests/test_phase3_readiness.py",
    "tests/test_phase32_entry_readiness.py",
    "tests/test_validation_errors.py",
    "tools/analytics_contracts.py",
    "tools/phase3_readiness.py",
    "tools/phase32_entry_readiness.py",
    "tools/release_contracts.py",
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
    documentation_digest: str
    failures: int
    manual_gates: int
    checks: list[CheckResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scope": self.scope,
            "documentation_digest": self.documentation_digest,
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


def documentation_digest() -> tuple[str, list[str]]:
    files = sorted(PHASE3.glob("*.md"), key=lambda path: path.name)
    manifest: list[str] = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        manifest.append(f"{path.name}:{digest}\n")
    aggregate = hashlib.sha256("".join(manifest).encode("utf-8")).hexdigest()
    return aggregate.upper(), manifest


def check_required_files() -> CheckResult:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        return CheckResult(
            "required_files", FAIL, f"missing: {', '.join(missing)}", missing
        )
    return CheckResult(
        "required_files",
        PASS,
        f"{len(REQUIRED_FILES)} P3.0 implementation and evidence files are present.",
        list(REQUIRED_FILES),
    )


def check_contract_snapshots() -> CheckResult:
    evidence = [
        "contracts/phase-3/analytics-contracts.json",
        "contracts/phase-3/openapi.json",
        "contracts/phase-3/database.json",
        "contracts/phase-3/p3-2-start-authorization.json",
    ]
    failures: list[str] = []
    try:
        analytics = _read_json(evidence[0])
        openapi = _read_json(evidence[1])
        database = _read_json(evidence[2])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("contract_snapshots", FAIL, str(exc), evidence)

    if analytics.get("contract_format") != "hcam.analytics.contract-bundle.v1":
        failures.append("unexpected analytics contract format")
    if analytics.get("maximum_event_bytes") != 65_536:
        failures.append("analytics event-size ceiling is not 65536 bytes")
    required_events = {
        "hcam.analytics.observation.created.v1",
        "hcam.analytics.track.updated.v1",
        "hcam.analytics.event.created.v1",
        "hcam.analytics.model.deployment.changed.v1",
    }
    events = analytics.get("events")
    if not isinstance(events, dict) or not required_events.issubset(events):
        failures.append("required versioned analytics events are missing")

    openapi_schema = openapi.get("schema")
    if not isinstance(openapi_schema, dict):
        failures.append("OpenAPI schema object is missing")
        openapi_schema = {}
    paths = openapi_schema.get("paths")
    if not isinstance(paths, dict):
        failures.append("OpenAPI paths object is missing")
        paths = {}
    required_operations = {
        "/analytics-assignments": {"get"},
        "/analytics-assignments/{assignment_id}": {"get", "patch"},
        "/analytics-assignments/{assignment_id}/revisions": {"get"},
        "/streams/{stream_id}/analytics-assignments": {"post"},
    }
    for path, methods in required_operations.items():
        operations = paths.get(path)
        if not isinstance(operations, dict) or not methods.issubset(operations):
            failures.append(f"OpenAPI operation is missing: {path} {sorted(methods)}")
    allowed_activation_paths = {"/analytics-assignments/{assignment_id}/activate"}
    unsafe_paths = [
        path
        for path in paths
        if "activat" in path.casefold() and path not in allowed_activation_paths
    ]
    if unsafe_paths:
        failures.append("an unapproved analytics activation path is present")

    activation_paths = allowed_activation_paths.intersection(paths)
    if activation_paths:
        try:
            start = _read_json(evidence[3])
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"P3.2 activation authorization is unavailable: {exc}")
        else:
            target = start.get("target")
            if (
                start.get("decision_id") != "D-P3.2-START"
                or start.get("status") != "owner_authorized"
                or not isinstance(target, dict)
                or target.get("data_source") != "DATA-GEN-R0"
                or target.get("deployment") != "local_development_and_ci_only"
            ):
                failures.append("P3.2 activation authorization is invalid")

    allowed_heads = {
        ("0008_analytics_assignments",),
        ("0009_generated_analytics",),
        ("0010_generated_tracking",),
    }
    heads = database.get("alembic_heads")
    if not isinstance(heads, list) or tuple(heads) not in allowed_heads:
        failures.append(
            "database snapshot is not at an approved P3.0 through P3.3 revision"
        )
    raw_tables = database.get("tables")
    tables = (
        {
            table.get("name"): table
            for table in raw_tables
            if isinstance(raw_tables, list) and isinstance(table, dict)
        }
        if isinstance(raw_tables, list)
        else {}
    )
    assignment = tables.get("analytics_assignments")
    revision = tables.get("analytics_assignment_revisions")
    if not isinstance(assignment, dict) or not isinstance(revision, dict):
        failures.append("analytics assignment tables are missing")
    else:
        constraints = {
            item.get("name"): item.get("sql")
            for item in assignment.get("check_constraints", [])
            if isinstance(item, dict)
        }
        allowed_constraints = {
            "ck_analytics_assignment_p3_desired_state": {
                "desired_state = 'paused'",
                "desired_state IN ('paused', 'enabled')",
            },
            "ck_analytics_assignment_p3_lifecycle_state": {
                "lifecycle_state = 'blocked'",
                "lifecycle_state IN ('blocked', 'paused', 'running', 'degraded', 'failed')",
            },
            "ck_analytics_assignment_p3_reason_code": {
                "reason_code = 'owner_gates_pending'",
                "reason_code IN ('owner_gates_pending', 'manual_pause', "
                "'generated_runtime_active', 'runtime_degraded', 'runtime_failed')",
            },
        }
        for name, expressions in allowed_constraints.items():
            if constraints.get(name) not in expressions:
                failures.append(f"database guard is missing or changed: {name}")
        if heads in (["0009_generated_analytics"], ["0010_generated_tracking"]):
            if constraints.get("ck_analytics_assignment_execution_scope") != (
                "execution_scope = 'generated_only'"
            ):
                failures.append("generated-only execution-scope guard is missing")
            state_consistency = constraints.get(
                "ck_analytics_assignment_state_consistency", ""
            )
            blocked_state = (
                "desired_state = 'paused' AND lifecycle_state = 'blocked' AND "
                "reason_code = 'owner_gates_pending'"
            )
            if blocked_state not in state_consistency:
                failures.append("the original P3.0 blocked state is no longer valid")

    for fixture in REQUIRED_FILES:
        if not fixture.startswith("contracts/phase-3/fixtures/"):
            continue
        try:
            _read_json(fixture)
        except (OSError, ValueError, json.JSONDecodeError):
            failures.append(f"fixture is not a JSON object: {fixture}")

    if failures:
        return CheckResult("contract_snapshots", FAIL, "; ".join(failures), evidence)
    return CheckResult(
        "contract_snapshots",
        PASS,
        "Structured analytics, OpenAPI, database, and fixture contracts are valid.",
        evidence,
    )


def check_fail_closed_boundaries() -> CheckResult:
    files = [
        "app/hcam/analytics/models.py",
        "app/hcam/analytics/schemas.py",
        "app/hcam/analytics/service.py",
        "app/hcam/analytics/runtime.py",
        "migrations/versions/0008_analytics_assignments.py",
        "app/hcam/analytics/activation.py",
        "migrations/versions/0009_generated_analytics.py",
    ]
    content = "\n".join(_read(path) for path in files)
    required = (
        'desired_state="paused"',
        'lifecycle_state="blocked"',
        'reason_code="owner_gates_pending"',
        'Literal["paused"]',
        'execution_scope="generated_only"',
        "UnavailableAnalyticsRuntimeAdapter",
        'return failed_runtime_result(request, "runtime_unconfigured")',
        'network_access: Literal["denied"]',
        'artifact_access: Literal["verified_handle_only"]',
        "ck_analytics_assignment_p3_desired_state",
        "ck_analytics_assignment_p3_lifecycle_state",
        "ck_analytics_assignment_p3_reason_code",
        "ck_analytics_assignment_execution_scope",
        'P3_2_APPROVAL_RECORD_ID = "D-P3.2-START"',
    )
    missing = [term for term in required if term not in content]
    if missing:
        return CheckResult(
            "fail_closed_boundaries",
            FAIL,
            f"missing or unsafe invariants: {', '.join(missing)}",
            files,
        )
    return CheckResult(
        "fail_closed_boundaries",
        PASS,
        "The P3.0 blocked default remains intact and P3.2 activation is generated-only and explicitly authorized.",
        files,
    )


def check_privacy_and_safety() -> CheckResult:
    files = [
        "contracts/phase-3/analytics-contracts.json",
        "app/hcam/security/errors.py",
        "app/hcam/main.py",
        "docs/phase-3/security-privacy-and-safety.md",
        "docs/phase-3/README.md",
    ]
    analytics = _read_json(files[0])
    prohibited = analytics.get("prohibited_fields")
    required_prohibited = {
        "biometric",
        "credential",
        "face_template",
        "government_data",
        "image_bytes",
        "owner_record",
        "person_embedding",
        "secret_ref",
        "stream_url",
        "video",
        "watchlist_match",
    }
    failures: list[str] = []
    if not isinstance(prohibited, list) or not required_prohibited.issubset(prohibited):
        failures.append("prohibited analytics fields are incomplete")
    errors = _read(files[1])
    main = _read(files[2])
    docs = "\n".join(_read(path) for path in files[3:])
    required_terms = {
        "validation": (
            "RequestValidationError",
            "sanitized_request_validation_error",
            '"Cache-Control": "no-store"',
        ),
        "documentation": (
            "Face recognition",
            "person re-identification",
            "Government",
            "Sentinel",
            "metadata-only",
        ),
    }
    combined_validation = errors + main
    for term in required_terms["validation"]:
        if term not in combined_validation:
            failures.append(f"validation safeguard is missing: {term}")
    for term in required_terms["documentation"]:
        if term not in docs:
            failures.append(f"safety boundary is missing: {term}")
    if failures:
        return CheckResult("privacy_and_safety", FAIL, "; ".join(failures), files)
    return CheckResult(
        "privacy_and_safety",
        PASS,
        "Prohibited data, validation redaction, and Phase 3 safety boundaries hold.",
        files,
    )


def check_observability() -> CheckResult:
    dashboard_path = "deploy/observability/hcam-phase3-control-plane.json"
    alerts_path = "deploy/observability/hcam-phase3-control-plane-alerts.yml"
    dashboard = _read_json(dashboard_path)
    serialized = json.dumps(dashboard, sort_keys=True)
    alerts = _read(alerts_path)
    metrics = {
        "hcam_analytics_assignments_total",
        "hcam_analytics_assignments_blocked_total",
        "hcam_analytics_assignment_revisions_retained_total",
        "hcam_analytics_outbox_unpublished_total",
        "hcam_analytics_assignment_failures_recent_total",
    }
    forbidden = {
        "assignment_id",
        "camera_id",
        "stream_id",
        "actor_id",
        "model_id",
        "locator",
        "secret_ref",
    }
    failures = [
        f"metric is missing: {metric}" for metric in metrics if metric not in serialized
    ]
    failures.extend(
        f"identifier appears in observability artifacts: {term}"
        for term in forbidden
        if term in serialized.casefold() or term in alerts.casefold()
    )
    panels = dashboard.get("panels")
    if not isinstance(panels, list) or len(panels) < 5:
        failures.append(
            "Phase 3 dashboard must preserve at least five control-plane panels"
        )
    required_alerts = {
        "HcamAnalyticsAssignmentInvariantViolation",
        "HcamAnalyticsOutboxBacklog",
        "HcamAnalyticsAssignmentFailureSpike",
    }
    failures.extend(
        f"alert is missing: {alert}" for alert in required_alerts if alert not in alerts
    )
    if failures:
        return CheckResult(
            "observability",
            FAIL,
            "; ".join(failures),
            [dashboard_path, alerts_path],
        )
    return CheckResult(
        "observability",
        PASS,
        f"{len(panels)} identifier-free control-plane panels and the bounded alerts exist.",
        [dashboard_path, alerts_path],
    )


def check_documentation_digest() -> CheckResult:
    digest, manifest = documentation_digest()
    if not manifest:
        return CheckResult(
            "documentation_digest", FAIL, "no Phase 3 Markdown files found", []
        )
    return CheckResult(
        "documentation_digest",
        PASS,
        f"{len(manifest)} Phase 3 documents hash to {digest}.",
        [item.rstrip("\n") for item in manifest],
    )


def check_owner_decision_record() -> CheckResult:
    path = "contracts/phase-3/p3-0-owner-decisions.json"
    record = _read_json(path)
    failures: list[str] = []
    if record.get("contract_format") != "hcam.phase3.owner-decisions.v1":
        failures.append("unexpected owner-decision contract format")
    if record.get("status") != "p3_0_accepted":
        failures.append("P3.0 acceptance status changed")
    if record.get("record_id") != "P3-G1-G3-2026-08-24":
        failures.append("owner-decision record identifier changed")
    if record.get("recorded_on") != "2026-08-24":
        failures.append("owner-decision date changed")
    owner = record.get("accountable_owner_id")
    reviewer = record.get("independent_reviewer_id")
    if owner != "mayank-admin":
        failures.append("accountable owner does not match the recorded decision")
    if reviewer != "mahin-eleveted" or reviewer == owner:
        failures.append("independent reviewer is missing or not independent")
    if record.get("independent_reviewer_role") != "member":
        failures.append("independent reviewer role changed")

    expected_owner_acceptance = {
        "accepted_by": "mayank-admin",
        "accepted_on": "2026-08-24",
        "capacity": ["main_developer", "team_lead", "accountable_owner"],
        "effective": True,
        "effective_for_gate": "P3-G4",
        "independent_review_status": "optional_reviewer_unavailable",
        "review_policy": "accountable_owner_self_review_permitted",
        "status": "accepted",
    }
    if record.get("owner_p3_0_acceptance") != expected_owner_acceptance:
        failures.append("owner acceptance or P3-G4 self-review policy changed")

    expected_later_gate_review_policy = {
        "accountable_owner_id": "mayank-admin",
        "effective_on": "2026-08-24",
        "evidence_requirements_remain_mandatory": True,
        "mode": "accountable_owner_review_sufficient",
        "separate_person_review_required": False,
        "status": "disabled_by_owner",
        "workstreams": [
            "model_promotion",
            "operational_geometry",
            "datasets",
            "deployment",
        ],
    }
    if record.get("later_gate_review_policy") != expected_later_gate_review_policy:
        failures.append("later-gate separate-review policy changed")

    scope = record.get("tier_a_scope")
    expected_classes = {
        "object.person",
        "vehicle.bicycle",
        "vehicle.motorcycle",
        "vehicle.car",
        "vehicle.bus",
        "vehicle.truck",
        "object.unknown",
    }
    expected_capabilities = {
        "object_detection",
        "stream_local_tracking",
        "line_crossing",
        "zone_entry_exit",
        "zone_occupancy",
        "zone_dwell_duration",
    }
    expected_supporting_classes = {"object.entity", "object.vehicle"}
    expected_exclusions = {
        "synthetic_anpr",
        "tier_b_scenario_analytics",
        "tier_c_high_consequence_analytics",
        "face_recognition",
        "person_reidentification",
        "cross_camera_identity",
        "sensitive_trait_inference",
        "watchlists",
        "government_matching",
        "autonomous_enforcement",
    }
    expected_geometry = {
        "coordinates": "normalized_top_left",
        "line_direction_required": True,
        "operational_coordinates_require_owner_approval": True,
        "operational_coordinates_require_separate_review": False,
        "schedule": "always_active_or_explicit_iana_timezone_weekly_windows",
        "site_specific_geometry_approved": False,
        "zone_shape": "simple_polygon_3_to_128_unique_vertices",
    }
    if not isinstance(scope, dict):
        failures.append("Tier A scope is missing")
    else:
        if set(scope.get("emitted_classes", [])) != expected_classes:
            failures.append("owner-approved emitted class set changed")
        if set(scope.get("capabilities", [])) != expected_capabilities:
            failures.append("owner-approved capability set changed")
        if set(scope.get("supporting_classes", [])) != expected_supporting_classes:
            failures.append("owner-approved supporting class set changed")
        if set(scope.get("excluded_from_this_gate", [])) != expected_exclusions:
            failures.append("P3-G1 exclusion boundary changed")
        if scope.get("unknown_class_policy") != "emit_unknown":
            failures.append("unknown-class policy changed")
        if scope.get("geometry") != expected_geometry:
            failures.append("owner-approved geometry semantics changed")

    policy = record.get("metadata_policy")
    expected_data_classes = {
        "derived.analytics.standard": (
            168,
            {"camera.viewer", "camera.editor", "platform.admin"},
            False,
        ),
        "derived.analytics.restricted": (24, {"platform.admin"}, True),
        "control.analytics.configuration": (
            2160,
            {"camera.editor", "platform.admin"},
            True,
        ),
        "audit.analytics": (2160, {"platform.admin"}, True),
        "telemetry.analytics.aggregate": (720, {"metrics.reader"}, False),
        "derived.analytics.plate_text": (0, set(), True),
        "media.analytics.raw": (0, set(), True),
    }
    if not isinstance(policy, dict):
        failures.append("metadata policy is missing")
    else:
        rows = policy.get("data_classes")
        valid_rows = (
            [item for item in rows if isinstance(item, dict)]
            if isinstance(rows, list)
            else []
        )
        classifications = [item.get("classification") for item in valid_rows]
        if (
            len(valid_rows) != len(expected_data_classes)
            or len(set(classifications)) != len(classifications)
            or set(classifications) != set(expected_data_classes)
        ):
            failures.append(
                "owner-approved data-class inventory changed or contains duplicates"
            )
        else:
            for item in valid_rows:
                classification = item["classification"]
                retention, roles, reason_required = expected_data_classes[
                    classification
                ]
                if (
                    item.get("maximum_retention_hours") != retention
                    or set(item.get("access_roles", [])) != roles
                    or item.get("reason_required") is not reason_required
                ):
                    failures.append(
                        f"owner-approved data-class policy changed: {classification}"
                    )
        required_policy = {
            "scope": "synthetic_lab_only",
            "raw_media_persistence": "denied",
            "export_policy": "denied",
            "training_reuse": "denied_requires_new_purpose_approval",
            "deletion_interval_hours": 24,
            "deletion_maximum_lag_hours": 24,
            "deletion_proof": "audited_metadata_only",
            "backup_retention_days": 7,
            "restore_policy": "delete_expired_records_before_access",
            "legal_hold_policy": "not_available_requires_separate_approval",
        }
        for key, value in required_policy.items():
            if policy.get(key) != value:
                failures.append(f"owner-approved metadata policy changed: {key}")

    expected_non_authorization = {
        "model_or_dataset_download",
        "training_or_inference",
        "media_or_physical_camera_access",
        "sentinel_video",
        "government_or_private_data",
        "identity_or_watchlist_processing",
        "operational_alerting_or_autonomous_action",
        "pilot_or_production_deployment",
    }
    non_authorization = record.get("non_authorization")
    if (
        not isinstance(non_authorization, list)
        or len(non_authorization) != len(expected_non_authorization)
        or set(non_authorization) != expected_non_authorization
    ):
        failures.append("non-authorization boundary changed or contains duplicates")

    approvals = record.get("approvals")
    valid_approvals = (
        [item for item in approvals if isinstance(item, dict)]
        if isinstance(approvals, list)
        else []
    )
    gate_ids = [item.get("gate_id") for item in valid_approvals]
    approval_status = {
        item.get("gate_id"): item.get("status") for item in valid_approvals
    }
    expected_approval_status = {
        "P3-G1": "owner_approved",
        "P3-G2": "owner_approved",
        "P3-G3": "owner_approved",
        "P3-G4": "owner_accepted",
    }
    if (
        len(valid_approvals) != len(expected_approval_status)
        or len(set(gate_ids)) != len(gate_ids)
        or approval_status != expected_approval_status
    ):
        failures.append("owner-gate status record changed or contains duplicates")

    if failures:
        return CheckResult("owner_decision_record", FAIL, "; ".join(failures), [path])
    return CheckResult(
        "owner_decision_record",
        PASS,
        "P3-G1 through P3-G4 and the later-gate accountable-owner review mode "
        "match the recorded decisions.",
        [path, "docs/phase-3/p3-0-owner-decisions.md"],
    )


def _safe_owner_evidence(target: str) -> bool:
    if target.startswith("https://github.com/mayankthakor227/h-cam-2.0/"):
        return True
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


def check_owner_gates() -> list[CheckResult]:
    path = "docs/phase-3/readiness-report.md"
    content = _read(path)
    status_match = re.search(r"^Status: `(?P<status>[^`]+)`$", content, re.MULTILINE)
    matches = list(_OWNER_GATE_PATTERN.finditer(content))
    gate_ids = [match.group("gate_id") for match in matches]
    if gate_ids != list(OWNER_GATE_IDS):
        return [
            CheckResult(
                "owner_gate_structure",
                FAIL,
                "owner gates must appear exactly once and in order: "
                + ", ".join(OWNER_GATE_IDS),
                [path],
            )
        ]

    results: list[CheckResult] = []
    checked_count = 0
    incomplete_gate_seen = False
    for index, match in enumerate(matches):
        block_end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(content)
        )
        block = content[match.end() : block_end]
        evidence_match = re.search(r"^  Evidence: (?P<value>.+)$", block, re.MULTILINE)
        evidence = evidence_match.group("value").strip() if evidence_match else None
        gate_id = match.group("gate_id")
        title = match.group("title").strip()
        checked = match.group("mark").casefold() == "x"
        if not checked:
            incomplete_gate_seen = True
            if evidence != "`pending`":
                results.append(
                    CheckResult(
                        gate_id,
                        FAIL,
                        "An incomplete owner gate must use `pending` evidence.",
                        [path, title],
                    )
                )
            else:
                results.append(
                    CheckResult(gate_id, MANUAL, f"Pending: {title}", [path])
                )
            continue

        checked_count += 1
        if incomplete_gate_seen:
            results.append(
                CheckResult(
                    gate_id,
                    FAIL,
                    "Owner gates must be completed in order.",
                    [path, title],
                )
            )
            continue
        targets = (
            [
                item.group("target").strip()
                for item in _MARKDOWN_LINK_PATTERN.finditer(evidence)
            ]
            if evidence
            else []
        )
        if not targets or not all(_safe_owner_evidence(target) for target in targets):
            results.append(
                CheckResult(
                    gate_id,
                    FAIL,
                    "A completed owner gate requires a safe repository evidence link.",
                    [path, title],
                )
            )
        else:
            results.append(CheckResult(gate_id, PASS, f"Accepted: {title}", targets))

    declared_status = status_match.group("status") if status_match else None
    expected_status = (
        "accepted" if checked_count == len(OWNER_GATE_IDS) else "ready_for_owner_review"
    )
    if declared_status != expected_status:
        results.append(
            CheckResult(
                "owner_gate_status",
                FAIL,
                f"readiness status must be `{expected_status}`",
                [path],
            )
        )
    return results


def check_future_boundaries() -> CheckResult:
    files = [
        "docs/phase-3/acceptance-checklist.md",
        "docs/phase-3/implementation-backlog.md",
        "docs/phase-3/decision-register.md",
    ]
    content = re.sub(r"\s+", " ", "\n".join(_read(path) for path in files))
    required = (
        "- [ ] Exact selected model artifacts and datasets",
        "- [x] Developer baseline `LAB-LAPTOP-01` is recorded",
        "- [ ] Target accelerator/lab hardware for model/runtime promotion is recorded.",
        "No model download, dataset download, media capture, inference, or later milestone may begin",
        "implementation and artifacts remain unauthorized",
        "No executable inference runtime is part of P3.0.",
    )
    missing = [term for term in required if term not in content]
    if missing:
        return CheckResult(
            "future_boundaries",
            FAIL,
            f"later milestone boundary is missing: {', '.join(missing)}",
            files,
        )
    return CheckResult(
        "future_boundaries",
        PASS,
        "Model, dataset, hardware, inference, media, and later milestones remain gated.",
        files,
    )


def _display_command(command: list[str]) -> str:
    values = list(command)
    try:
        if Path(values[0]).resolve() == Path(sys.executable).resolve():
            values[0] = "python"
    except (IndexError, OSError):
        pass
    return " ".join(values)


def _run(
    command: list[str], *, env: dict[str, str] | None = None
) -> tuple[str, str | None]:
    command_text = _display_command(command)
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
        return command_text, type(exc).__name__
    evidence = f"{command_text} -> exit {completed.returncode}"
    if completed.returncode == 0:
        return evidence, None
    return evidence, f"command_failed(exit={completed.returncode})"


def run_validation_commands() -> CheckResult:
    evidence: list[str] = []
    failures: list[str] = []
    commands = [
        ["uv", "lock", "--check"],
        [sys.executable, "-m", "compileall", "-q", "app", "tools", "migrations"],
        [sys.executable, "-m", "ruff", "check", "app", "tests", "tools", "migrations"],
        [sys.executable, "tools/analytics_contracts.py", "check"],
        [sys.executable, "tools/release_contracts.py", "check"],
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_analytics_contracts.py",
            "tests/test_analytics_taxonomy.py",
            "tests/test_analytics_geometry.py",
            "tests/test_analytics_runtime.py",
            "tests/test_analytics_assignment_api.py",
            "tests/test_analytics_assignment_migration.py",
            "tests/test_deployment_artifacts.py",
            "tests/test_metrics.py",
            "tests/test_validation_errors.py",
            "tests/test_phase3_readiness.py",
        ],
        ["git", "diff", "--check"],
    ]
    for command in commands:
        item, failure = _run(command)
        evidence.append(item)
        if failure:
            failures.append(failure)

    with tempfile.TemporaryDirectory(prefix="hcam-phase3-readiness-") as temp:
        database_url = f"sqlite:///{(Path(temp) / 'migration.db').as_posix()}"
        environment = {**os.environ, "HCAM_DATABASE_URL": database_url}
        for arguments in (
            ["upgrade", "head"],
            ["check"],
            ["downgrade", "base"],
            ["upgrade", "head"],
            ["check"],
        ):
            command = [sys.executable, "-m", "alembic", *arguments]
            item, failure = _run(command, env=environment)
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
        "Offline P3.0 contracts, tests, migration cycle, lint, and diff checks passed.",
        evidence,
    )


def build_readiness_report(run_validation: bool = False) -> ReadinessReport:
    digest, _manifest = documentation_digest()
    checks = [
        check_required_files(),
        check_contract_snapshots(),
        check_fail_closed_boundaries(),
        check_privacy_and_safety(),
        check_observability(),
        check_documentation_digest(),
        check_owner_decision_record(),
        check_future_boundaries(),
        *check_owner_gates(),
    ]
    if run_validation:
        checks.append(run_validation_commands())
    failures = sum(check.status == FAIL for check in checks)
    manual_gates = sum(check.status == MANUAL for check in checks)
    status_name = (
        "not_ready"
        if failures
        else "ready_for_owner_review"
        if manual_gates
        else "accepted"
    )
    return ReadinessReport(
        status=status_name,
        scope="phase3.p3_0.contracts_and_guardrails",
        documentation_digest=digest,
        failures=failures,
        manual_gates=manual_gates,
        checks=checks,
    )


def print_text_report(report: ReadinessReport) -> None:
    print(f"Phase 3 P3.0 readiness: {report.status}")
    print(f"Scope: {report.scope}")
    print(f"Documentation digest: {report.documentation_digest}")
    print(f"Failures: {report.failures}")
    print(f"Manual gates: {report.manual_gates}")
    print()
    for check in report.checks:
        print(f"[{check.status}] {check.name}: {check.detail}")
        for item in check.evidence:
            print(f"  - {item}")
        print()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify H-CAM Phase 3 P3.0 readiness.")
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
