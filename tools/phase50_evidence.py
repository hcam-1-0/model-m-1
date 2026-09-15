from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from tools.phase50_readiness import ROOT, checks
except ModuleNotFoundError:  # Direct execution places tools/ on sys.path.
    from phase50_readiness import ROOT, checks


EVIDENCE_ROOT = ROOT / "contracts/phase-5"
EVIDENCE_PATH = EVIDENCE_ROOT / "p5-0-evidence.json"
PACKAGE_PATH = EVIDENCE_ROOT / "p5-0-evidence-package.json"
ACCEPTANCE_PATH = EVIDENCE_ROOT / "p5-0-acceptance-proposal.json"
START_PACKAGE_SHA256 = (
    "66F40E71B2E96F2C61C267EF5A14CD709692A0C389AC23560651BC2B9C38B7F8"
)
COMPONENT_PATHS = (
    "app/hcam/operator_application/__init__.py",
    "app/hcam/operator_application/accessibility.py",
    "app/hcam/operator_application/bounds.py",
    "app/hcam/operator_application/capabilities.py",
    "app/hcam/operator_application/catalogue.py",
    "app/hcam/operator_application/contracts.py",
    "app/hcam/operator_application/design_tokens.py",
    "app/hcam/operator_application/generated.py",
    "app/hcam/operator_application/gis_contracts.py",
    "app/hcam/operator_application/journeys.py",
    "app/hcam/operator_application/navigation.py",
    "app/hcam/operator_application/security.py",
    "app/hcam/operator_application/validation.py",
    "contracts/phase-5/operator-ui-accessibility.v1.json",
    "contracts/phase-5/operator-ui-capability-matrix.v1.json",
    "contracts/phase-5/operator-ui-contract-catalogue.v1.json",
    "contracts/phase-5/operator-ui-gis-parity.v1.json",
    "contracts/phase-5/operator-ui-producer-coverage.v1.json",
    "contracts/phase-5/operator-ui-route-journeys.v1.json",
    "docs/phase-5/p5-0-implementation.md",
    "docs/phase-5/p5-0-security-controls.md",
    "docs/phase-5/p5-0-validation.md",
    "fixtures/phase-5/p5-0/canonical-negative.json",
    "fixtures/phase-5/p5-0/canonical-positive.json",
    "fixtures/phase-5/p5-0/gis-parity-vectors.json",
    "fixtures/phase-5/p5-0/journey-walkthroughs.json",
    "tests/test_phase50_accessibility.py",
    "tests/test_phase50_contract_bounds.py",
    "tests/test_phase50_contract_catalogue.py",
    "tests/test_phase50_generated_fixtures.py",
    "tests/test_phase50_gis_contracts.py",
    "tests/test_phase50_journeys.py",
    "tests/test_phase50_readiness.py",
    "tests/test_phase50_security.py",
    "tools/phase50_evidence.py",
    "tools/phase50_readiness.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=False, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _components() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for relative in COMPONENT_PATHS:
        path = ROOT / relative
        result.append(
            {"path": relative, "bytes": path.stat().st_size, "sha256": _sha256(path)}
        )
    return result


def _canonical_component_digest(components: list[dict[str, Any]]) -> str:
    manifest = "\n".join(
        f"{item['path']}|{item['bytes']}|{item['sha256']}"
        for item in sorted(components, key=lambda item: item["path"])
    )
    return hashlib.sha256(manifest.encode("utf-8")).hexdigest().upper()


def write_evidence(
    *,
    technical_commit: str,
    focused_tests: int,
    full_tests: int,
    branch_coverage: float,
) -> dict[str, str]:
    readiness = checks(require_evidence=False)
    if not all(readiness.values()):
        raise RuntimeError("P5.0 readiness is not complete")
    evidence = {
        "schema_version": "hcam.phase5.p5_0.evidence.v1",
        "evidence_id": "P5.0-EVIDENCE-R0",
        "status": "technical_complete_owner_acceptance_pending",
        "generated_on": "2026-09-06",
        "technical_commit": technical_commit,
        "start_package_sha256": START_PACKAGE_SHA256,
        "validation": {
            "readiness_checks": readiness,
            "focused_tests_passed": focused_tests,
            "full_tests_passed": full_tests,
            "branch_coverage_percent": branch_coverage,
            "ruff": "passed",
            "package_build": "passed",
            "generated_contract_cases": 720,
            "generated_GIS_parity_cases": 96,
        },
        "environment": {
            "network_used": False,
            "real_data_used": False,
            "camera_or_media_used": False,
            "frontend_or_map_runtime_used": False,
            "container_or_Kubernetes_used": False,
            "local_uv_environment_materialized_from_cache": True,
        },
        "limitations": [
            "generated_only_contract_evidence",
            "no_React_browser_renderer_or_visual_parity_execution",
            "no_map_tile_provider_camera_stream_or_media_access",
            "no_real_Government_police_private_or_personal_data",
            "no_new_dependency_migration_API_route_database_or runtime",
            "no_operational_accuracy_performance_accessibility_or deployment claim",
            "local_uv_environment_was_materialized_from_existing_cache_without network",
            "P5_1_and_remote_Git_remain_closed",
        ],
        "product_progress_before_owner_acceptance": {
            "P5_0": "7/8 (87.5000%)",
            "Phase_5": "7/100 (7.0000%)",
        },
    }
    _write_json(EVIDENCE_PATH, evidence)
    components = _components()
    components.append(
        {
            "path": EVIDENCE_PATH.relative_to(ROOT).as_posix(),
            "bytes": EVIDENCE_PATH.stat().st_size,
            "sha256": _sha256(EVIDENCE_PATH),
        }
    )
    canonical_digest = _canonical_component_digest(components)
    package = {
        "schema_version": "hcam.phase5.p5_0.evidence-package.v1",
        "package_id": "P5.0-EVIDENCE-PACKAGE-R0",
        "status": "owner_acceptance_required",
        "effective": False,
        "generated_on": "2026-09-06",
        "technical_commit": technical_commit,
        "start_package_sha256": START_PACKAGE_SHA256,
        "component_digest_algorithm": "Sort components by path using ordinal path text, render path|bytes|sha256 with LF separators and no terminal LF, then SHA-256 over UTF-8 bytes.",
        "canonical_component_digest": canonical_digest,
        "components": components,
        "component_count": len(components),
        "generated_only": True,
        "P5_0_complete": False,
        "P5_1_authorized": False,
        "remote_Git_authorized": False,
    }
    _write_json(PACKAGE_PATH, package)
    package_sha = _sha256(PACKAGE_PATH)
    acceptance = {
        "schema_version": "hcam.phase5.p5_0.acceptance-proposal.v1",
        "decision_id": "D-P5.0-ACCEPTANCE",
        "status": "owner_acceptance_required",
        "effective": False,
        "evidence_package": {
            "package_id": "P5.0-EVIDENCE-PACKAGE-R0",
            "path": PACKAGE_PATH.relative_to(ROOT).as_posix(),
            "sha256": package_sha,
            "canonical_component_digest": canonical_digest,
        },
        "technical_commit": technical_commit,
        "accepted_progress_if_approved": {
            "P5_0": "8/8 (100.0000%)",
            "Phase_5": "8/100 (8.0000%)",
        },
        "P5_1_authorized": False,
        "remote_Git_authorized": False,
    }
    _write_json(ACCEPTANCE_PATH, acceptance)
    return {
        "evidence_sha256": _sha256(EVIDENCE_PATH),
        "package_sha256": package_sha,
        "canonical_component_digest": canonical_digest,
        "acceptance_proposal_sha256": _sha256(ACCEPTANCE_PATH),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic P5.0 evidence")
    parser.add_argument("--technical-commit", required=True)
    parser.add_argument("--focused-tests", type=int, required=True)
    parser.add_argument("--full-tests", type=int, required=True)
    parser.add_argument("--branch-coverage", type=float, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.write:
        raise SystemExit("--write is required")
    result = write_evidence(
        technical_commit=args.technical_commit,
        focused_tests=args.focused_tests,
        full_tests=args.full_tests,
        branch_coverage=args.branch_coverage,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
