from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "contracts" / "phase-4" / "p4-4" / "fixtures"
GENERATOR_VERSION = "p4.4.generated-integrations.v1"
MINIMUM_SCENARIOS = 324
SPECS = (
    ("generated-provider-manifests-v1.json", "provider_manifest", 12),
    ("generated-auth-profile-cases-v1.json", "auth_profile", 12),
    ("generated-catalogue-snapshots-v1.json", "catalogue_snapshot", 36),
    ("generated-query-jobs-v1.json", "query_job", 48),
    ("generated-provider-responses-v1.json", "provider_response", 48),
    ("generated-candidate-evidence-v1.json", "candidate_evidence", 72),
    ("generated-abstention-cases-v1.json", "abstention", 48),
    ("generated-workflow-executor-cases-v1.json", "workflow_executor", 24),
    ("generated-revocation-cases-v1.json", "revocation", 24),
    ("generated-redaction-cases-v1.json", "redaction", 24),
    ("generated-hypothesis-enrichment-v1.json", "hypothesis_enrichment", 24),
)


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _scenario(family: str, index: int) -> dict[str, Any]:
    outcome_by_family = {
        "auth_profile": ("accepted", "denied", "disabled"),
        "provider_response": ("accepted", "transient_failure", "permanent_failure"),
        "candidate_evidence": ("exact", "normalized", "approximate", "contradicts"),
        "abstention": ("insufficient_evidence", "ambiguous", "minimum_score"),
        "workflow_executor": ("accepted", "duplicate", "timeout", "cancelled", "revoked", "late"),
        "revocation": ("allowed", "revoked", "quarantined"),
        "redaction": ("retained_digest_only", "denied_before_formatting"),
        "hypothesis_enrichment": ("supporting", "contradicting", "missing", "stale"),
    }
    outcomes = outcome_by_family.get(family, ("accepted", "duplicate", "bounded"))
    material = {
        "family": family,
        "index": index,
        "generated_key": f"gen_{family}_{index:03d}",
        "generated_value": f"gen_value_{index:03d}",
        "expected_outcome": outcomes[index % len(outcomes)],
        "department": f"Generated-Department-{index % 3}",
        "generated_only": True,
        "operational": False,
    }
    return {
        "scenario_id": f"p44-{family}-{index:03d}",
        **material,
        "scenario_digest": _digest(material),
    }


def documents() -> dict[Path, dict[str, Any]]:
    result: dict[Path, dict[str, Any]] = {}
    for filename, family, count in SPECS:
        vectors = [_scenario(family, index) for index in range(count)]
        result[FIXTURE_ROOT / filename] = {
            "schema_version": "hcam.p4-4.generated-fixture-set.v1",
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
    print(f"P4.4 generated fixtures: {scenario_count()} scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
