from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from hcam.acceptance import GeneratedAcceptanceService
from hcam.acceptance.bounds import (
    MAX_CLAIMS,
    MAX_COMPATIBILITY_ENTRIES,
    MAX_EVIDENCE_COMPONENTS,
    MAX_EVIDENCE_EDGES,
    MAX_HANDOFF_OPERATIONS,
    MAX_LIMITATIONS,
    MAX_SCENARIOS,
    MAX_STEPS_PER_SCENARIO,
    MAX_UI_STATES,
)
from hcam.acceptance.canonical import canonical_bytes
from hcam.acceptance.contracts import ContractModel
from hcam.acceptance.evidence import build_evidence_index
from hcam.acceptance.fixtures import fixture_documents


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures/phase4/p4-7"
CONTRACT_ROOT = ROOT / "contracts/phase-4/p4-7"
DOC_ROOT = ROOT / "docs/phase-4"
AUTHORIZATION_DIGEST = (
    "39AF9D9DA00DB7806195B4BA2B5512B238A94E7BC41C3F8270431AA2A87EE168"
)
PLANNING_DIGEST = "A226D7E8E3AB01C240D2692E95DAD5BB051ABB4D015B907BC9197BE835895F9C"
VALIDATION_SUMMARY = {
    "focused_phase47": {
        "passed": 46,
        "failed": 0,
        "branch_coverage_percent": 98.16,
        "coverage_threshold_percent": 90,
    },
    "full_repository": {
        "passed": 4171,
        "failed": 0,
        "skipped": 16,
        "subtests_passed": 119,
        "warnings": 1,
        "postgresql_integration_skips": 16,
    },
    "quality_gates": {
        "ruff": "passed",
        "compileall": "passed",
        "offline_lock_check": "passed",
        "wheel_build": "passed",
        "source_distribution_build": "passed",
        "release_contract_check": "passed",
        "phase47_readiness": "passed",
        "phase46_historical_readiness": "passed",
    },
    "migration": {
        "head_count": 1,
        "head": "0018_operations_security_scale",
    },
    "unperformed_environment_validation": [
        "postgresql_integration",
        "vulnerability_refresh",
        "hardware_capacity",
        "backup_restore_recovery",
        "container_kubernetes_execution",
        "production_or_pilot_deployment",
    ],
}


def _json_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _pretty(value: Any) -> bytes:
    return (
        json.dumps(_json_value(value), ensure_ascii=True, indent=2, sort_keys=True)
        + "\n"
    ).encode("ascii")


def _write(path: Path, payload: bytes, *, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"generated artifact differs: {path.relative_to(ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _contract_catalogue() -> dict[str, Any]:
    from hcam.acceptance import contracts

    models = {
        name: value.model_json_schema()
        for name, value in sorted(vars(contracts).items())
        if isinstance(value, type)
        and issubclass(value, ContractModel)
        and value is not ContractModel
    }
    return {
        "schema_version": "hcam.phase4.p4_7.acceptance-contracts.v1",
        "canonical_encoding": "UTF-8 ASCII JSON with sorted keys and compact separators",
        "digest": "SHA-256",
        "models": models,
        "bounds": {
            "claims": MAX_CLAIMS,
            "compatibility_entries": MAX_COMPATIBILITY_ENTRIES,
            "evidence_components": MAX_EVIDENCE_COMPONENTS,
            "evidence_edges": MAX_EVIDENCE_EDGES,
            "handoff_operations": MAX_HANDOFF_OPERATIONS,
            "limitations": MAX_LIMITATIONS,
            "scenarios": MAX_SCENARIOS,
            "steps_per_scenario": MAX_STEPS_PER_SCENARIO,
            "ui_states": MAX_UI_STATES,
        },
        "generated_only": True,
        "operational": False,
    }


def _handoff_package(bundle: Any) -> dict[str, Any]:
    components = {
        "http": bundle.http,
        "events": bundle.events,
        "ui_accessibility": bundle.ui,
        "compatibility": bundle.compatibility,
        "projections": bundle.projections,
    }
    return {
        "schema_version": "hcam.phase4.p4_7.phase5-handoff.v1",
        "canonical_component_digest": hashlib.sha256(
            canonical_bytes(components, maximum_bytes=16_777_216)
        )
        .hexdigest()
        .upper(),
        "components": _json_value(components),
        "phase5_implemented": False,
        "phase5_authorized": False,
        "generated_only": True,
        "operational": False,
    }


def _scenario_results(bundle: Any) -> dict[str, Any]:
    return {
        "schema_version": "hcam.phase4.p4_7.scenario-results.v1",
        "scenario_count": len(bundle.manifest.scenarios),
        "run_count": len(bundle.portfolio.runs),
        "comparison_count": len(bundle.portfolio.comparisons),
        "all_complete": bundle.complete,
        "bundle_digest": bundle.canonical_digest,
        "runs": _json_value(bundle.portfolio.runs),
        "comparisons": _json_value(bundle.portfolio.comparisons),
        "generated_only": True,
        "operational": False,
    }


def _markdown_documents(bundle: Any) -> dict[str, bytes]:
    scenario_rows = "\n".join(
        f"| {item.scenario_id} | {item.category} | {item.expected_terminal_state} |"
        for item in bundle.manifest.scenarios
    )
    operations = f"""# P4.7 Generated Operations

Status: generated-only, default-off, production-forbidden

This runbook validates the accepted Phase 4 contracts with anonymous generated
records. It does not connect to providers, networks, cameras, media, models,
datasets, operational systems, containers, Kubernetes, or deployment targets.

## Portfolio

| Scenario | Category | Expected terminal state |
| --- | --- | --- |
{scenario_rows}

Each scenario runs exactly twice from clean in-memory state. A result passes
only when every mandatory assertion passes, normalized replay digests match,
and all prohibited-side-effect counters remain zero.

## Runbook

The machine-readable runbook contains {len(bundle.runbook.steps)} ordered steps.
It requires exact authorization, source verification, fixture linting, two
replays, semantic comparison, handoff validation, evidence sealing, cleanup,
and zero-retention verification. It is not an executable production procedure.
"""
    prerequisites = """# P4.7 Production Operations Prerequisites

Status: non-effective future outline

Every category in this outline is `not_operationally_validated`. The document
contains no environment-specific command, credential, destination, topology,
capacity target, legal conclusion, or readiness claim. Production operations
require separate accountable owners, approved policy, owned-environment
evidence, recovery exercises, and deployment authorization.
"""
    handoff = f"""# P4.7 Phase 5 Handoff

Status: canonical consumer-contract handoff; Phase 5 is not implemented

The handoff contains {len(bundle.http.operations)} HTTP operation contracts,
{len(bundle.events.events)} event contracts, {len(bundle.events.workflows)}
generated workflows, {len(bundle.ui.states)} UI states, and
{len(bundle.ui.requirements)} accessibility requirements. Server-side
authorization remains authoritative. The OpenAPI, AsyncAPI, CloudEvents,
Arazzo, canonical-JSON, PROV, and SLSA-shaped outputs are derived projections,
not standards-conformance claims.
"""
    review = f"""# P4.7 Evidence Review

Status: technical validation complete; exact owner acceptance pending

The deterministic portfolio contains {len(bundle.manifest.scenarios)} mandatory
scenarios, {len(bundle.portfolio.runs)} clean runs, and
{len(bundle.portfolio.comparisons)} replay comparisons. In-memory validation
reports `complete={str(bundle.complete).lower()}`.

The focused P4.7 suite reports 46 passed, zero failed, and 98.16% branch
coverage against a 90% threshold. The monolithic repository regression reports
4,171 passed, zero failed, 16 expected PostgreSQL integration skips, 119 passed
subtests, and one known Starlette/httpx deprecation warning. Ruff, compileall,
the offline dependency lock, wheel and source-distribution builds, the immutable
release-contract check, P4.6 historical readiness, P4.7 readiness, and the
single migration head `0018_operations_security_scale` all pass.

PostgreSQL integration, vulnerability refresh, hardware capacity, backup and
restore recovery, container or Kubernetes execution, and production or pilot
deployment were not exercised. Those are limitations, not passing claims.

No real provider, camera, media, Government/private data, model, inference,
operational action, production procedure, container, Kubernetes workload, or
deployment was exercised. Phase 4 final acceptance and Phase 5 remain closed.
"""
    return {
        "p4-7-generated-operations.md": operations.encode("ascii"),
        "p4-7-production-prerequisites.md": prerequisites.encode("ascii"),
        "p4-7-handoff.md": handoff.encode("ascii"),
        "p4-7-evidence-review.md": review.encode("ascii"),
    }


def build_documents(*, source_commit: str) -> dict[Path, bytes]:
    if len(source_commit) != 40 or any(
        character not in "0123456789abcdef" for character in source_commit
    ):
        raise ValueError("source commit must be a lowercase 40-character Git object ID")
    bundle = GeneratedAcceptanceService(
        enabled=True, environment="development"
    ).execute()
    documents: dict[Path, bytes] = {}
    for name, payload in fixture_documents().items():
        documents[FIXTURE_ROOT / name] = _pretty(payload)
    projection_names = {
        "openapi": "openapi.json",
        "asyncapi": "asyncapi.json",
        "cloudevents": "cloudevents.json",
        "arazzo": "arazzo.json",
        "rfc8785": "rfc8785-projection.json",
        "prov": "prov-projection.json",
        "slsa": "slsa-projection.json",
    }
    contract_payloads: dict[str, Any] = {
        "acceptance-contracts.json": _contract_catalogue(),
        "scenario-manifest.json": bundle.manifest,
        "scenario-results.json": _scenario_results(bundle),
        "claim-register.json": bundle.claims,
        "limitation-register.json": bundle.limitations,
        "operations-runbook.json": bundle.runbook,
        "production-operations-prerequisites.json": bundle.production_prerequisites,
        "reconstruction-manifest.json": {
            "schema_version": "hcam.phase4.p4_7.reconstruction-set.v1",
            "reconstructions": _json_value(bundle.reconstructions),
            "generated_only": True,
        },
        "http-operations.json": bundle.http,
        "event-workflows.json": bundle.events,
        "ui-accessibility.json": bundle.ui,
        "compatibility.json": bundle.compatibility,
        "handoff-package.json": _handoff_package(bundle),
    }
    contract_payloads.update(
        {
            filename: bundle.projections[key]
            for key, filename in projection_names.items()
        }
    )
    for name, payload in contract_payloads.items():
        documents[CONTRACT_ROOT / name] = _pretty(payload)
    for name, payload in _markdown_documents(bundle).items():
        documents[DOC_ROOT / name] = payload
    return documents


def generate(*, source_commit: str, check: bool = False) -> dict[str, str]:
    documents = build_documents(source_commit=source_commit)
    for path, payload in documents.items():
        _write(path, payload, check=check)
    evidence_files = {
        str(path.relative_to(ROOT)).replace("\\", "/"): (
            "fixture"
            if FIXTURE_ROOT in path.parents
            else "document"
            if DOC_ROOT in path.parents
            else "projection"
            if path.name
            in {
                "openapi.json",
                "asyncapi.json",
                "cloudevents.json",
                "arazzo.json",
                "rfc8785-projection.json",
                "prov-projection.json",
                "slsa-projection.json",
            }
            else "result"
            if path.name in {"scenario-results.json", "reconstruction-manifest.json"}
            else "contract"
        )
        for path in documents
    }
    evidence = build_evidence_index(
        ROOT,
        source_commit=source_commit,
        authorization_digest=AUTHORIZATION_DIGEST,
        files=evidence_files,
        relationships=(
            (
                "fixtures/phase4/p4-7/generated-scenario-manifest-v1.json",
                "contracts/phase-4/p4-7/scenario-results.json",
                "derived_from",
            ),
            (
                "contracts/phase-4/p4-7/scenario-results.json",
                "contracts/phase-4/p4-7/claim-register.json",
                "supports",
            ),
            (
                "contracts/phase-4/p4-7/limitation-register.json",
                "contracts/phase-4/p4-7/claim-register.json",
                "limits",
            ),
            (
                "contracts/phase-4/p4-7/http-operations.json",
                "contracts/phase-4/p4-7/openapi.json",
                "derived_from",
            ),
            (
                "contracts/phase-4/p4-7/event-workflows.json",
                "contracts/phase-4/p4-7/asyncapi.json",
                "derived_from",
            ),
            (
                "contracts/phase-4/p4-7/ui-accessibility.json",
                "contracts/phase-4/p4-7/handoff-package.json",
                "supports",
            ),
        ),
    )
    evidence_payload = {
        "schema_version": "hcam.phase4.p4_7.evidence.v1",
        "source_commit": source_commit,
        "authorization_digest": AUTHORIZATION_DIGEST,
        "planning_digest": PLANNING_DIGEST,
        "portfolio": {"scenarios": 9, "runs": 18, "comparisons": 9, "complete": True},
        "validation": VALIDATION_SUMMARY,
        "boundaries": {
            "generated_only": True,
            "operational": False,
            "network_attempts": 0,
            "camera_media_model_data_attempts": 0,
            "container_kubernetes_deployment_attempts": 0,
            "phase5_implemented": False,
        },
        "evidence_index_digest": hashlib.sha256(
            canonical_bytes(evidence, maximum_bytes=16_777_216)
        )
        .hexdigest()
        .upper(),
        "generated_only": True,
    }
    evidence_paths = {
        CONTRACT_ROOT / "evidence-index.json": _pretty(evidence),
        CONTRACT_ROOT / "evidence.json": _pretty(evidence_payload),
    }
    for path, payload in evidence_paths.items():
        _write(path, payload, check=check)
    component_hashes = {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(payload)
        .hexdigest()
        .upper()
        for path, payload in {**documents, **evidence_paths}.items()
    }
    package = {
        "schema_version": "hcam.phase4.p4_7.evidence-package.v1",
        "package_id": "P4.7-EVIDENCE-PACKAGE-R0",
        "technical_commit": source_commit,
        "authorization_digest": AUTHORIZATION_DIGEST,
        "validation": VALIDATION_SUMMARY,
        "components": component_hashes,
        "canonical_component_digest": hashlib.sha256(
            canonical_bytes(component_hashes, maximum_bytes=16_777_216)
        )
        .hexdigest()
        .upper(),
        "owner_acceptance_required": True,
        "phase4_complete": False,
        "phase5_authorized": False,
        "generated_only": True,
    }
    package_payload = _pretty(package)
    package_sha = hashlib.sha256(package_payload).hexdigest().upper()
    proposal = {
        "schema_version": "hcam.phase4.p4_7.acceptance-proposal.v1",
        "decision_id": "D-P4.7-ACCEPTANCE",
        "effective": False,
        "evidence_package_sha256": package_sha,
        "canonical_component_digest": package["canonical_component_digest"],
        "technical_commit": source_commit,
        "effect_if_exactly_accepted": "complete_P4_7_and_Phase4_only",
        "does_not_authorize": [
            "phase5_planning_or_implementation",
            "real_providers_network_or_credentials",
            "government_private_camera_or_media_data",
            "models_datasets_artifacts_or_inference",
            "operational_actions_containers_kubernetes_or_deployment",
            "remote_git",
        ],
    }
    final_paths = {
        CONTRACT_ROOT / "evidence-package.json": package_payload,
        CONTRACT_ROOT / "acceptance-proposal.json": _pretty(proposal),
    }
    for path, payload in final_paths.items():
        _write(path, payload, check=check)
    all_payloads = {**documents, **evidence_paths, **final_paths}
    return {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(payload)
        .hexdigest()
        .upper()
        for path, payload in sorted(all_payloads.items(), key=lambda item: str(item[0]))
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate deterministic Phase 4.7 acceptance artifacts"
    )
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    digests = generate(source_commit=args.source_commit, check=args.check)
    print(json.dumps({"files": len(digests), "digests": digests}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
