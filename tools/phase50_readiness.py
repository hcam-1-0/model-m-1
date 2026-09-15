from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from hcam.operator_application import (
    AccessibilityMatrixV1,
    ContractCatalogueV1,
    GisParityMatrixV1,
    JourneyContractV1,
    RouteContractV1,
    validate_generated_portfolio,
)


ROOT = Path(__file__).resolve().parents[1]
START_PACKAGE = ROOT / "contracts/phase-5/p5-0-start-authorization-package.json"
PLANNING_PACKAGE = ROOT / "contracts/phase-5/planning-package-r2.json"
EXPECTED_START_SHA256 = (
    "66F40E71B2E96F2C61C267EF5A14CD709692A0C389AC23560651BC2B9C38B7F8"
)
EXPECTED_PLANNING_SHA256 = (
    "CA13BB9D897A7815E89BE4F71240855C4F9392A55133DE99282EE59728A082F3"
)
SOURCE_ROOT = ROOT / "app/hcam/operator_application"
CONTRACT_ROOT = ROOT / "contracts/phase-5"
FIXTURE_ROOT = ROOT / "fixtures/phase-5/p5-0"
PROHIBITED_IMPORTS = frozenset(
    {
        "aiohttp",
        "cv2",
        "ffmpeg",
        "httpx",
        "kubernetes",
        "onnx",
        "onnxruntime",
        "requests",
        "socket",
        "torch",
        "ultralytics",
        "urllib",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def _prohibited_imports() -> set[str]:
    found: set[str] = set()
    for path in SOURCE_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [item.name.partition(".")[0] for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.partition(".")[0]]
            else:
                names = []
            found.update(name for name in names if name in PROHIBITED_IMPORTS)
    return found


def checks(*, require_evidence: bool = False) -> dict[str, bool]:
    start = _json(START_PACKAGE)
    catalogue = ContractCatalogueV1.model_validate_json(
        (CONTRACT_ROOT / "operator-ui-contract-catalogue.v1.json").read_text(
            encoding="utf-8"
        )
    )
    accessibility = AccessibilityMatrixV1.model_validate_json(
        (CONTRACT_ROOT / "operator-ui-accessibility.v1.json").read_text(
            encoding="utf-8"
        )
    )
    GIS = GisParityMatrixV1.model_validate_json(
        (CONTRACT_ROOT / "operator-ui-gis-parity.v1.json").read_text(encoding="utf-8")
    )
    routes_document = _json(CONTRACT_ROOT / "operator-ui-route-journeys.v1.json")
    routes = [RouteContractV1.model_validate(item) for item in routes_document["routes"]]
    journeys = [
        JourneyContractV1.model_validate(item) for item in routes_document["journeys"]
    ]
    producer_coverage = _json(
        CONTRACT_ROOT / "operator-ui-producer-coverage.v1.json"
    )
    capability_matrix = _json(
        CONTRACT_ROOT / "operator-ui-capability-matrix.v1.json"
    )
    positive = _json(FIXTURE_ROOT / "canonical-positive.json")
    GIS_seeds = _json(FIXTURE_ROOT / "gis-parity-vectors.json")
    portfolio = validate_generated_portfolio(GIS)
    exact_paths = start["exact_additive_implementation_paths"]
    expected_sources = {path for path in exact_paths if path.startswith("app/")}
    expected_contracts = {
        path
        for path in exact_paths
        if path.startswith("contracts/phase-5/operator-ui-")
    }
    expected_fixtures = {path for path in exact_paths if path.startswith("fixtures/")}
    evidence_paths = {
        ROOT / "contracts/phase-5/p5-0-evidence.json",
        ROOT / "contracts/phase-5/p5-0-evidence-package.json",
        ROOT / "contracts/phase-5/p5-0-acceptance-proposal.json",
        ROOT / "docs/phase-5/p5-0-evidence.md",
    }
    result = {
        "planning_package_exact": _sha256(PLANNING_PACKAGE)
        == EXPECTED_PLANNING_SHA256,
        "start_package_exact": _sha256(START_PACKAGE) == EXPECTED_START_SHA256,
        "start_package_owner_authorized_externally": "D-P5.0-START"
        in (ROOT / "docs/phase-5/status.md").read_text(encoding="utf-8"),
        "source_paths_exact": expected_sources
        == {
            path.relative_to(ROOT).as_posix()
            for path in SOURCE_ROOT.glob("*.py")
        },
        "contract_paths_present": all((ROOT / path).is_file() for path in expected_contracts),
        "fixture_paths_present": all((ROOT / path).is_file() for path in expected_fixtures),
        "implementation_paths_unique": len(exact_paths) == len(set(exact_paths)),
        "catalogue_has_ten_unique_views": len(catalogue.views) == 10,
        "catalogue_routes_unique": len({item.route_id for item in catalogue.views}) == 10,
        "producer_coverage_exact": {item.view_id for item in catalogue.views}
        == {item["view_id"] for item in producer_coverage["entries"]},
        "all_views_generated_and_non_operational": all(
            item.generated_only and not item.operational for item in catalogue.views
        ),
        "route_contracts_bounded": len(routes) == 6
        and all(not item.sensitive_state_permitted for item in routes),
        "journey_contracts_bounded": len(journeys) == 3
        and all(item.generated_only and not item.operational for item in journeys),
        "accessibility_categories_complete": len(accessibility.requirements) == 9
        and len(accessibility.alternatives) == 5,
        "GIS_parity_requirements_complete": len(GIS.requirements) == 12
        and GIS.authoritative_2d
        and GIS.accessible_list_equivalent
        and not GIS.optional_3d_default_enabled,
        "generated_contract_cases_sufficient": portfolio.contract_case_count >= 320
        and positive["expected_materialized_case_count"]
        == portfolio.contract_case_count,
        "generated_GIS_cases_exact": portfolio.GIS_case_count == 96
        and GIS_seeds["expected_materialized_case_count"] == portfolio.GIS_case_count,
        "generated_identifiers_unique": portfolio.identifiers_unique,
        "generated_payloads_safe": portfolio.generated_payloads_safe,
        "capabilities_server_authoritative": capability_matrix["server_authoritative"]
        and not capability_matrix["client_may_expand_server_authority"],
        "three_resource_profiles_present": len(capability_matrix["profiles"]) == 3,
        "prohibited_imports_absent": not _prohibited_imports(),
        "frontend_and_map_runtime_absent": not start["binding_profile"][
            "framework_or_UI_runtime_in_P5_0"
        ]
        and "React_TypeScript_Vite_workspace_or_UI_component implementation"
        in start["explicit_non_goals"],
        "remote_Git_closed": start["remote_git_authorized"] is False,
        "P5_1_closed": "P5_1_or_later implementation"
        in start["continuing_prohibitions"],
        "evidence_paths_present": (not require_evidence)
        or all(path.is_file() for path in evidence_paths),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate P5.0 contract readiness")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-evidence", action="store_true")
    args = parser.parse_args()
    result = checks(require_evidence=args.require_evidence)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        for name, passed in sorted(result.items()):
            print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return 0 if all(result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
