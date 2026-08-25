#!/usr/bin/env python3
"""Verify the bounded P3.4 generated-only geometry/event package."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from hcam.analytics.models import (
    AnalyticsEvent,
    AnalyticsGeometry,
    AnalyticsGeometryEvaluatorRun,
    AnalyticsGeometryRule,
    AnalyticsTrackRuleState,
)
from hcam.settings import Settings

try:
    from tools.phase34_c10_evidence import REPORT as C10_REPORT
    from tools.phase34_c10_evidence import validate as validate_c10
    from tools.phase34_supply_chain import (
        CONTAINER_REVIEW,
        DEPENDENCIES,
        SBOM,
        validate_container_review,
        validate_dependencies,
        validate_sbom,
    )
except ModuleNotFoundError:  # Direct execution places tools/ on sys.path.
    from phase34_c10_evidence import REPORT as C10_REPORT
    from phase34_c10_evidence import validate as validate_c10
    from phase34_supply_chain import (
        CONTAINER_REVIEW,
        DEPENDENCIES,
        SBOM,
        validate_container_review,
        validate_dependencies,
        validate_sbom,
    )


ROOT = Path(__file__).resolve().parents[1]
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"
ACCEPTANCE_PATH = ROOT / "contracts" / "phase-3" / "p3-4-acceptance.json"
VALIDATION_PATH = ROOT / "contracts" / "phase-3" / "p3-4-validation-evidence.json"
START_PATH = ROOT / "contracts" / "phase-3" / "p3-4-start-authorization.json"

PACKAGE_FILES = (
    ".github/workflows/python-ci.yml",
    "Dockerfile",
    "README.md",
    "app/hcam/analytics/contracts.py",
    "app/hcam/analytics/fixtures.py",
    "app/hcam/analytics/geometry.py",
    "app/hcam/analytics/models.py",
    "app/hcam/analytics/spatial/__init__.py",
    "app/hcam/analytics/spatial/cel_policy.py",
    "app/hcam/analytics/spatial/contracts.py",
    "app/hcam/analytics/spatial/evaluator.py",
    "app/hcam/analytics/spatial/execution.py",
    "app/hcam/analytics/spatial/generated.py",
    "app/hcam/analytics/spatial/geometry_engine.py",
    "app/hcam/analytics/spatial/routes.py",
    "app/hcam/analytics/spatial/schemas.py",
    "app/hcam/analytics/spatial/service.py",
    "app/hcam/analytics/spatial/sql_types.py",
    "app/hcam/database.py",
    "app/hcam/main.py",
    "app/hcam/metrics.py",
    "app/hcam/settings.py",
    "contracts/phase-3/README.md",
    "contracts/phase-3/analytics-contracts.json",
    "contracts/phase-3/database.json",
    "contracts/phase-3/fixtures/geometry-rule-draft-v1.json",
    "contracts/phase-3/openapi.json",
    "contracts/phase-3/p3-4-c10-evidence.json",
    "contracts/phase-3/p3-4-container-vulnerability-review.json",
    "contracts/phase-3/p3-4-dependencies.json",
    "contracts/phase-3/p3-4-sbom.cdx.json",
    "contracts/phase-3/p3-4-start-authorization.json",
    "contracts/phase-3/p3-4-validation-evidence.json",
    "deploy/compose.phase3.yaml",
    "docs/phase-3/README.md",
    "docs/phase-3/build-and-test.md",
    "docs/phase-3/decision-register.md",
    "docs/phase-3/implementation-backlog.md",
    "docs/phase-3/p3-4-implementation-readiness-report.md",
    "docs/phase-3/p3-4-implementation.md",
    "docs/phase-3/p3-4-plan.md",
    "docs/phase-3/p3-4-third-party-notices.md",
    "migrations/versions/0011_geometry_events.py",
    "pyproject.toml",
    "tests/test_analytics_assignment_migration.py",
    "tests/test_analytics_spatial.py",
    "tests/test_analytics_spatial_api.py",
    "tests/test_analytics_spatial_c10.py",
    "tests/test_phase34_evidence.py",
    "tests/test_phase34_implementation_readiness.py",
    "tests/test_phase34_postgres.py",
    "tests/test_phase34_supply_chain.py",
    "tools/phase34_c10_evidence.py",
    "tools/phase34_implementation_readiness.py",
    "tools/phase34_supply_chain.py",
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
    package_file_count: int
    failures: int
    manual_gates: int
    checks: tuple[Check, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scope": self.scope,
            "package_digest": self.package_digest,
            "package_file_count": self.package_file_count,
            "failures": self.failures,
            "manual_gates": self.manual_gates,
            "checks": [asdict(check) for check in self.checks],
        }


def _json(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain an object")
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
        manifest.append(
            f"{relative_path} sha256={file_digest} bytes={len(payload)}"
        )
    return digest.hexdigest().upper(), tuple(manifest)


def check_required_files() -> Check:
    missing = tuple(path for path in PACKAGE_FILES if not (ROOT / path).is_file())
    if missing:
        return Check("required_files", FAIL, "P3.4 package files are missing.", missing)
    return Check(
        "required_files",
        PASS,
        f"All {len(PACKAGE_FILES)} P3.4 package files exist.",
    )


def check_start_authorization() -> Check:
    try:
        record = _json(START_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("start_authorization", FAIL, str(exc))
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
        "operational_alerting_autonomous_action_or_enforcement",
        "pilot_production_statewide_deployment_or_performance_claims",
        "remote_git_push_pull_request_or_merge",
        "p3_5_or_later_work",
    }
    if (
        record.get("decision_id") != "D-P3.4-START"
        or record.get("status") != "authorized"
        or record.get("authorized_by") != "mayank-admin"
        or record.get("owner_statement_received") != "I authorize D-P3.4-START"
        or record.get("implementation_authorized") is not True
        or record.get("final_acceptance_granted") is not False
        or not required_work.issubset(set(record.get("authorized_work", [])))
        or not prohibited.issubset(set(record.get("prohibited_work", [])))
    ):
        return Check("start_authorization", FAIL, "D-P3.4-START boundary changed.")
    return Check(
        "start_authorization",
        PASS,
        "D-P3.4-START authorizes this bounded local generated-only package.",
    )


def check_supply_chain() -> Check:
    try:
        dependencies = _json(DEPENDENCIES)
        sbom = _json(SBOM)
        container = _json(CONTAINER_REVIEW)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("supply_chain", FAIL, str(exc))
    failures = (
        validate_dependencies(dependencies)
        + validate_sbom(sbom)
        + validate_container_review(container)
    )
    if failures:
        return Check(
            "supply_chain",
            FAIL,
            "Dependency, SBOM, or container evidence failed.",
            tuple(failures),
        )
    counts = container["severity_counts"]
    return Check(
        "supply_chain",
        PASS,
        "Exact Python/native dependencies are recorded; the PostGIS image "
        "remains blocked from deployment because its scan has unresolved findings.",
        (
            f"container_critical={counts['CRITICAL']}",
            f"container_high={counts['HIGH']}",
            f"deployment_gate={container['deployment_gate']}",
        ),
    )


def check_c10_evidence() -> Check:
    try:
        document = _json(C10_REPORT)
        failures = tuple(validate_c10(document))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("generated_c10", FAIL, str(exc))
    reports = document.get("scenario_reports")
    if failures:
        return Check("generated_c10", FAIL, "C10 evidence failed.", failures)
    if (
        document.get("execution_scope") != "generated_only"
        or document.get("prohibited_inputs_present") is not False
        or document.get("logic_agreement") != 1.0
        or document.get("replay_stable") is not True
        or document.get("replay_count") != 20
        or not isinstance(reports, list)
        or len(reports) != 5
    ):
        return Check("generated_c10", FAIL, "C10 safety or replay gates changed.")
    return Check(
        "generated_c10",
        PASS,
        "Five sealed generated scenarios have exact logic agreement and 20 stable replays.",
    )


def check_structural_boundaries() -> Check:
    prohibited = {
        "biometric",
        "clip",
        "face",
        "identity",
        "media",
        "plate",
        "reid",
        "snapshot",
        "watchlist",
    }
    failures: list[str] = []
    for model in (
        AnalyticsGeometry,
        AnalyticsGeometryRule,
        AnalyticsGeometryEvaluatorRun,
        AnalyticsTrackRuleState,
        AnalyticsEvent,
    ):
        columns = {column.name.lower() for column in model.__table__.columns}
        if any(token in column for column in columns for token in prohibited):
            failures.append(model.__tablename__)
    settings = Settings(environment="test")
    if settings.analytics_generated_geometry_enabled:
        failures.append("default_on")
    try:
        Settings(
            environment="production",
            database_url="postgresql+psycopg://hcam@db/hcam",
            analytics_generated_geometry_enabled=True,
        )
    except ValueError:
        pass
    else:
        failures.append("production_enabled")
    if failures:
        return Check(
            "structural_boundaries",
            FAIL,
            "P3.4 generated-only boundaries failed.",
            tuple(failures),
        )
    return Check(
        "structural_boundaries",
        PASS,
        "Storage has no prohibited media/identity fields; runtime is default-off "
        "and production-forbidden.",
    )


def check_migration_contract() -> Check:
    source = (ROOT / "migrations" / "versions" / "0011_geometry_events.py").read_text(
        encoding="utf-8"
    )
    required = (
        'revision: str = "0011_geometry_events"',
        'down_revision: str | None = "0010_generated_tracking"',
        "CREATE EXTENSION IF NOT EXISTS postgis",
        "analytics_geometries",
        "analytics_geometry_rules",
        "analytics_geometry_evaluator_runs",
        "analytics_track_rule_states",
        "analytics_events",
        "ST_IsValid(spatial_geometry)",
        "ST_AsBinary(spatial_geometry) = canonical_wkb",
        'postgresql_using="gist"',
        "alert_state = 'not_evaluated'",
    )
    missing = tuple(token for token in required if token not in source)
    database_source = (ROOT / "app" / "hcam" / "database.py").read_text(
        encoding="utf-8"
    )
    if "0011_geometry_events" not in database_source:
        missing += ("database_current_revision",)
    if missing:
        return Check(
            "migration_contract",
            FAIL,
            "P3.4 additive migration contract is incomplete.",
            missing,
        )
    return Check(
        "migration_contract",
        PASS,
        "Revision 0011 contains the five stores, PostGIS validity/WKB checks, and GiST index.",
    )


def check_contract_snapshots() -> Check:
    try:
        analytics = _json(ROOT / "contracts" / "phase-3" / "analytics-contracts.json")
        database = _json(ROOT / "contracts" / "phase-3" / "database.json")
        openapi = _json(ROOT / "contracts" / "phase-3" / "openapi.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("contract_snapshots", FAIL, str(exc))
    serialized = json.dumps(
        {"analytics": analytics, "database": database, "openapi": openapi},
        sort_keys=True,
    )
    required = (
        "GeometryRuleV1",
        "RuleGraphV1",
        "RuleNodeV1",
        "0011_geometry_events",
        "/analytics-geometries",
        "/analytics-geometry-rules",
        "/analytics-assignments/{assignment_id}/generated-geometry-runs",
        "/analytics-geometry-runs/{run_id}/events",
    )
    missing = tuple(token for token in required if token not in serialized)
    if missing:
        return Check(
            "contract_snapshots",
            FAIL,
            "P3.4 reviewed contract snapshots are incomplete.",
            missing,
        )
    return Check(
        "contract_snapshots",
        PASS,
        "Analytics, OpenAPI, and migrated-database snapshots include P3.4 contracts.",
    )


def check_validation_evidence() -> Check:
    try:
        document = _json(VALIDATION_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("validation_evidence", FAIL, str(exc))
    failures: list[str] = []
    if document.get("scope") != "generated_structured_lifecycle_only":
        failures.append("scope")
    if document.get("prohibited_input_count") != 0:
        failures.append("prohibited_input_count")
    results = document.get("results")
    required_passes = {
        "archive_boundary",
        "build_and_isolated_install",
        "compile",
        "contract_checks",
        "dependency_audit",
        "docker",
        "full_suite",
        "generated_c10",
        "postgresql_postgis",
        "ruff",
        "sqlite_migration",
    }
    if not isinstance(results, dict):
        failures.append("results")
    else:
        for name in required_passes:
            item = results.get(name)
            if not isinstance(item, dict) or item.get("status") != "pass":
                failures.append(name)
        coverage = results.get("evaluator_coverage")
        if (
            not isinstance(coverage, dict)
            or coverage.get("status") != "pass"
            or float(coverage.get("branch_percent", 0)) < 90.0
        ):
            failures.append("evaluator_coverage")
        container = results.get("postgis_container_review")
        if (
            not isinstance(container, dict)
            or container.get("status") != "deployment_blocked"
            or int(container.get("critical", 0)) < 1
            or int(container.get("high", 0)) < 1
        ):
            failures.append("postgis_container_review")
    if failures:
        return Check(
            "validation_evidence",
            FAIL,
            "P3.4 validation evidence is incomplete.",
            tuple(failures),
        )
    return Check(
        "validation_evidence",
        PASS,
        "Compilation, lint, tests, migrations, packaging, audit, Docker, and boundary scans pass.",
    )


def check_clean_source() -> Check:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--", *PACKAGE_FILES],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if completed.returncode != 0:
        return Check("clean_source", FAIL, "Git clean-source check failed.")
    dirty = tuple(line for line in completed.stdout.splitlines() if line.strip())
    if dirty:
        return Check(
            "clean_source",
            FAIL,
            "P3.4 package files are not committed cleanly.",
            dirty,
        )
    return Check("clean_source", PASS, "P3.4 package files are clean in Git.")


def check_owner_acceptance() -> Check:
    if not ACCEPTANCE_PATH.is_file():
        return Check(
            "owner_acceptance",
            MANUAL,
            "mayank-admin must accept the exact clean-source package digest.",
        )
    try:
        record = _json(ACCEPTANCE_PATH)
        digest, _ = package_digest()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("owner_acceptance", FAIL, str(exc))
    if (
        record.get("decision_id") == "D-P3.4-ACCEPTANCE"
        and record.get("status") == "accepted"
        and record.get("accepted_by") == "mayank-admin"
        and record.get("scope")
        == "phase3.p3_4.generated_only_geometry_and_event_primitives"
        and record.get("evidence_package_digest") == digest
        and record.get("package_file_count") == len(PACKAGE_FILES)
    ):
        return Check("owner_acceptance", PASS, "Exact P3.4 package is owner accepted.")
    return Check(
        "owner_acceptance",
        FAIL,
        "P3.4 acceptance record does not match the exact current package.",
    )


def build_report(*, require_clean_source: bool) -> Report:
    checks = [
        check_required_files(),
        check_start_authorization(),
        check_supply_chain(),
        check_c10_evidence(),
        check_structural_boundaries(),
        check_migration_contract(),
        check_contract_snapshots(),
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
    try:
        digest, _ = package_digest()
    except OSError:
        digest = "UNAVAILABLE"
    return Report(
        status=status,
        scope="phase3.p3_4.generated_only_geometry_and_event_primitives",
        package_digest=digest,
        package_file_count=len(PACKAGE_FILES),
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
            f"P3.4 implementation: {report.status}; failures={report.failures}; "
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
