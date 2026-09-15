from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.phase54.generate_fixtures import GROUPS, MARKER, build_documents, canonical_sha

EXPECTED_CONTRACTS = {
    "analytical-concept.v1.json", "candidate-evidence.v1.json", "command-receipt.v1.json",
    "correction-impact.v1.json", "intelligence-event.v1.json", "intelligence-handoff.v1.json",
    "intelligence-page.v1.json", "intelligence-queue.v1.json", "relationship-projection.v1.json",
    "review-command.v1.json", "review-policy.v1.json", "rule-trace.v1.json", "safe-problem.v1.json",
    "spatial-projection.v1.json",
}
EXPECTED_FIXTURES = {
    "c1.generated.v1.json", "c10.generated.v1.json", "c50.generated.v1.json",
    "intelligence-cases.generated.v1.json", "replay-manifest.generated.v1.json",
    "review-cases.generated.v1.json", "security-cases.generated.v1.json", "visual-cases.generated.v1.json",
}
FORBIDDEN_KEYS = {"password", "secret", "secret_ref", "token", "credential", "camera_locator", "provider_payload", "biometric_template", "vehicle_plate", "person_name"}


def recursive_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(key).lower() for key in value} | set().union(
            *(recursive_keys(item) for item in value.values()), set()
        )
    if isinstance(value, list):
        return set().union(*(recursive_keys(item) for item in value), set())
    return set()


def verify(repo: Path) -> dict[str, Any]:
    failures: list[str] = []
    contract_root = repo / "contracts" / "phase-5" / "p5-4"
    fixture_root = repo / "fixtures" / "phase-5" / "p5-4"
    contract_names = {path.name for path in contract_root.glob("*.json")}
    fixture_names = {path.name for path in fixture_root.glob("*.json")}
    if contract_names != EXPECTED_CONTRACTS:
        failures.append("contract_set_mismatch")
    if fixture_names != EXPECTED_FIXTURES:
        failures.append("fixture_set_mismatch")
    documents = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in sorted(fixture_root.glob("*.json"))}
    if any(document.get("marker") != MARKER for document in documents.values()):
        failures.append("generated_marker_missing")
    cases = documents.get("intelligence-cases.generated.v1.json", {}).get("cases", [])
    if len(cases) != 832 or sum(count for _, count in GROUPS) != 832:
        failures.append("contract_case_count_mismatch")
    if len({case.get("case_ref") for case in cases}) != 832:
        failures.append("contract_case_ref_collision")
    if recursive_keys(documents) & FORBIDDEN_KEYS:
        failures.append("forbidden_browser_field")
    expected = build_documents()
    for name, document in documents.items():
        if canonical_sha(document) != canonical_sha(expected.get(name)):
            failures.append(f"non_deterministic:{name}")
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted((repo / "frontend" / "apps" / "intelligence-center" / "src").rglob("*.tsx")))
    if re.search(r"@xyflow/react|reactflow", source_text, re.IGNORECASE):
        failures.append("blocked_graph_dependency_present")
    if "Identity not established" not in source_text or "no operational" not in source_text.lower():
        failures.append("truth_boundary_copy_missing")
    producer_source = (repo / "frontend" / "packages" / "intelligence-fixtures" / "src" / "cases.ts").read_text(encoding="utf-8")
    producer_match = re.search(
        r"export const p54UnavailableProducers = \[(?P<body>.*?)\] as const;",
        producer_source,
        re.DOTALL,
    )
    producer_count = (
        len(re.findall(r'"[a-z0-9_]+"', producer_match.group("body")))
        if producer_match
        else 0
    )
    if producer_count != 26:
        failures.append("producer_gap_inventory_incomplete")
    return {
        "schema_version": "hcam.phase5.p5_4.verification.v1",
        "status": "pass" if not failures else "fail",
        "contracts": len(contract_names),
        "fixtures": len(fixture_names),
        "generated_cases": len(cases),
        "canonical_fixture_sha256": canonical_sha(documents),
        "failures": sorted(failures),
    }


def main() -> int:
    result = verify(Path(__file__).resolve().parents[2])
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
