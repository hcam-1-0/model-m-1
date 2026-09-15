from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "contracts" / "phase-4" / "p4-5" / "fixtures"
GENERATOR_VERSION = "p4.5.generated-investigations.v1"
MINIMUM_SCENARIOS = 512
SPECS = (
    ("generated-timelines-v2.json", "timeline", 40),
    ("generated-temporal-assertions-v1.json", "temporal_assertion", 40),
    ("generated-evidence-references-v1.json", "evidence_reference", 40),
    ("generated-integrity-assessments-v1.json", "integrity_assessment", 40),
    ("generated-provenance-bundles-v1.json", "provenance_bundle", 40),
    ("generated-correction-propagation-v1.json", "correction_propagation", 40),
    ("generated-review-disposition-v1.json", "review_disposition", 40),
    ("generated-merge-reopen-v1.json", "merge_reopen", 40),
    ("generated-retention-hold-v1.json", "retention_hold", 40),
    ("generated-deletion-receipts-v1.json", "deletion_receipt", 40),
    ("generated-export-manifests-v1.json", "export_manifest", 40),
    ("generated-case-bridge-v1.json", "case_bridge", 32),
    ("generated-prov-projections-v1.json", "prov_projection", 40),
    ("generated-security-abuse-v1.json", "security_abuse", 40),
)


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _scenario(family: str, index: int) -> dict[str, Any]:
    outcomes = {
        "timeline": ("open", "closed", "reopened", "duplicate"),
        "temporal_assertion": ("ordered", "late", "skewed", "unknown"),
        "evidence_reference": ("registered", "duplicate", "versioned", "denied"),
        "integrity_assessment": ("matched", "mismatched", "unavailable", "unverifiable"),
        "provenance_bundle": ("complete", "partial", "cycle_denied", "bounded"),
        "correction_propagation": ("pending", "partial", "blocked", "complete"),
        "review_disposition": ("support", "contradict", "no_conclusion", "superseded"),
        "merge_reopen": ("related", "merged", "reopened", "cycle_denied"),
        "retention_hold": ("retain", "eligible", "blocked", "unknown"),
        "deletion_receipt": ("simulated_deleted", "blocked", "residual_known", "unknown"),
        "export_manifest": ("complete", "partial", "blocked", "denied"),
        "case_bridge": ("disabled", "projection_only", "stale_denied", "scope_denied"),
        "prov_projection": ("mapped", "lossy", "unmapped", "import_denied"),
        "security_abuse": ("unknown_field", "oversized", "locator_denied", "secret_denied"),
    }[family]
    material = {
        "family": family,
        "index": index,
        "generated_key": f"gen_{family}_{index:03d}",
        "generated_value": f"gen_value_{index:03d}",
        "department": f"Generated-Department-{index % 4}",
        "expected_outcome": outcomes[index % len(outcomes)],
        "generated_only": True,
        "operational": False,
        "source_payload_retained": False,
    }
    return {
        "scenario_id": f"p45-{family}-{index:03d}",
        **material,
        "scenario_digest": _digest(material),
    }


def documents() -> dict[Path, dict[str, Any]]:
    result: dict[Path, dict[str, Any]] = {}
    for filename, family, count in SPECS:
        vectors = [_scenario(family, index) for index in range(count)]
        result[FIXTURE_ROOT / filename] = {
            "schema_version": "hcam.p4-5.generated-fixture-set.v1",
            "generator_version": GENERATOR_VERSION,
            "family": family,
            "scenario_count": count,
            "vectors": vectors,
            "fixture_digest": _digest(vectors),
        }
    return result


def render(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, sort_keys=True, indent=2) + "\n"


def scenario_count() -> int:
    return sum(document["scenario_count"] for document in documents().values())


def write() -> None:
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    for path, document in documents().items():
        path.write_text(render(document), encoding="utf-8", newline="\n")


def check() -> None:
    expected = documents()
    if scenario_count() < MINIMUM_SCENARIOS:
        raise SystemExit("generated scenario floor is not met")
    failures = []
    for path, document in expected.items():
        if not path.is_file() or path.read_text(encoding="utf-8") != render(document):
            failures.append(path.relative_to(ROOT).as_posix())
    if failures:
        raise SystemExit("generated fixtures differ: " + ", ".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        write()
    if args.check or not args.write:
        check()
    print(f"P4.5 generated fixtures: {scenario_count()} scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
