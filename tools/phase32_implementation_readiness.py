#!/usr/bin/env python3
"""Verify the bounded P3.2 generated-only implementation evidence package."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from hcam.analytics.activation import (
    P3_2_GENERATOR_VERSION,
    P3_2_MODEL_ID,
    P3_2_MODEL_VERSION,
    P3_2_PIPELINE_VERSION,
    P3_2_POLICY_VERSION,
    P3_2_TAXONOMY_VERSION,
)
from hcam.analytics.artifacts import DET_R0_BYTES, DET_R0_SHA256
from hcam.analytics.taxonomy import TaxonomyManifestV1


ROOT = Path(__file__).resolve().parents[1]
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"
P3_2_ACCEPTED_PACKAGE_DIGEST = (
    "F8673BE6AD8D8CABFA4636DA1505DE4C816398B115073B1F5261B03D2B0C7BCF"
)

PACKAGE_FILES = (
    ".github/workflows/python-ci.yml",
    "MANIFEST.in",
    "app/hcam/analytics/__init__.py",
    "app/hcam/analytics/activation.py",
    "app/hcam/analytics/artifacts.py",
    "app/hcam/analytics/bootstrap.py",
    "app/hcam/analytics/contracts.py",
    "app/hcam/analytics/execution.py",
    "app/hcam/analytics/fixtures.py",
    "app/hcam/analytics/generated.py",
    "app/hcam/analytics/models.py",
    "app/hcam/analytics/repository.py",
    "app/hcam/analytics/routes.py",
    "app/hcam/analytics/runtime.py",
    "app/hcam/analytics/schemas.py",
    "app/hcam/analytics/service.py",
    "app/hcam/analytics/yolox.py",
    "app/hcam/database.py",
    "app/hcam/main.py",
    "app/hcam/metrics.py",
    "app/hcam/settings.py",
    "contracts/phase-3/analytics-contracts.json",
    "contracts/phase-3/database.json",
    "contracts/phase-3/openapi.json",
    "contracts/phase-3/p3-2-dataset-approval.json",
    "contracts/phase-3/p3-2-entry-gates.json",
    "contracts/phase-3/p3-2-local-e2e-evidence.json",
    "contracts/phase-3/p3-2-model-approval.json",
    "contracts/phase-3/p3-2-model-card.json",
    "contracts/phase-3/p3-2-research-artifacts.json",
    "contracts/phase-3/p3-2-research-authorization.json",
    "contracts/phase-3/p3-2-research-evidence.json",
    "contracts/phase-3/p3-2-research-requirements.in",
    "contracts/phase-3/p3-2-research-requirements.lock",
    "contracts/phase-3/p3-2-runtime-approval.json",
    "contracts/phase-3/p3-2-sbom.spdx.json",
    "contracts/phase-3/p3-2-start-authorization.json",
    "contracts/phase-3/p3-2-taxonomy.json",
    "contracts/phase-3/fixtures/runtime-request-v2.json",
    "deploy/README.md",
    "deploy/observability/hcam-phase3-control-plane-alerts.yml",
    "deploy/observability/hcam-phase3-control-plane.json",
    "docs/phase-3/README.md",
    "docs/phase-3/assignment-control-plane.md",
    "docs/phase-3/decision-register.md",
    "docs/phase-3/implementation-backlog.md",
    "docs/phase-3/p3-2-entry-decision-packet.md",
    "docs/phase-3/p3-2-implementation.md",
    "docs/phase-3/p3-2-research-record.md",
    "docs/phase-3/p3-2-start-authorization.md",
    "migrations/versions/0009_generated_analytics.py",
    "pyproject.toml",
    "tests/test_analytics_activation.py",
    "tests/test_analytics_assignment_migration.py",
    "tests/test_analytics_bootstrap.py",
    "tests/test_analytics_contracts.py",
    "tests/test_analytics_generated_execution.py",
    "tests/test_analytics_taxonomy.py",
    "tests/test_analytics_yolox.py",
    "tests/test_deployment_artifacts.py",
    "tests/test_metrics.py",
    "tests/test_phase32_entry_readiness.py",
    "tests/test_phase32_implementation_readiness.py",
    "tests/test_phase32_research_acquire.py",
    "tools/phase31_contracts.py",
    "tools/phase32_entry_readiness.py",
    "tools/phase32_generated_e2e.py",
    "tools/phase32_implementation_readiness.py",
    "tools/phase32_offline_experiment.py",
    "tools/phase32_research_acquire.py",
    "tools/phase3_readiness.py",
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


def _json(relative_path: str) -> dict[str, object]:
    document = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("JSON root must be an object")
    return document


def _canonical_digest(document: dict[str, object]) -> str:
    encoded = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def package_digest() -> tuple[str, tuple[str, ...]]:
    digest = hashlib.sha256()
    manifest: list[str] = []
    for relative_path in sorted(PACKAGE_FILES):
        path = ROOT / relative_path
        content = path.read_bytes()
        file_digest = hashlib.sha256(content).hexdigest()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
        manifest.append(f"{relative_path} sha256={file_digest} bytes={len(content)}")
    return digest.hexdigest().upper(), tuple(manifest)


def check_required_files() -> Check:
    missing = tuple(path for path in PACKAGE_FILES if not (ROOT / path).is_file())
    if missing:
        return Check(
            "required_files",
            FAIL,
            f"Missing {len(missing)} required implementation files.",
            missing,
        )
    return Check(
        "required_files",
        PASS,
        f"All {len(PACKAGE_FILES)} required implementation files exist.",
    )


def check_owner_records() -> Check:
    failures: list[str] = []
    try:
        start = _json("contracts/phase-3/p3-2-start-authorization.json")
        model = _json("contracts/phase-3/p3-2-model-approval.json")
        dataset = _json("contracts/phase-3/p3-2-dataset-approval.json")
        runtime = _json("contracts/phase-3/p3-2-runtime-approval.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("owner_records", FAIL, f"Owner record parsing failed: {exc}")
    expected = (
        (start, "status", "owner_authorized"),
        (start, "decision_id", "D-P3.2-START"),
        (start, "expires_on", "2026-09-24"),
        (model, "status", "owner_approved_restricted"),
        (dataset, "status", "owner_approved_generated_only"),
        (runtime, "status", "owner_approved_cpu_reference"),
    )
    for record, key, value in expected:
        if record.get(key) != value:
            failures.append(f"{key}={record.get(key)!r}")
    artifact = model.get("artifact")
    if not isinstance(artifact, dict):
        failures.append("model.artifact")
    else:
        if artifact.get("artifact_id") != P3_2_MODEL_ID:
            failures.append("model.artifact_id")
        if artifact.get("bytes") != DET_R0_BYTES:
            failures.append("model.bytes")
        if artifact.get("sha256") != DET_R0_SHA256:
            failures.append("model.sha256")
    if failures:
        return Check(
            "owner_records",
            FAIL,
            "P3.2 owner records do not match the authorized start gate.",
            tuple(failures),
        )
    return Check(
        "owner_records",
        PASS,
        "D-P3.2-001 through D-P3.2-004 and D-P3.2-START remain exact.",
    )


def check_implementation_bindings() -> Check:
    bindings = (
        (
            P3_2_POLICY_VERSION,
            "contracts/phase-3/p3-2-start-authorization.json",
        ),
        (
            P3_2_PIPELINE_VERSION,
            "contracts/phase-3/p3-2-runtime-approval.json",
        ),
        (
            P3_2_GENERATOR_VERSION,
            "contracts/phase-3/p3-2-dataset-approval.json",
        ),
    )
    failures = tuple(
        relative_path
        for expected, relative_path in bindings
        if expected != _canonical_digest(_json(relative_path))
    )
    if failures or P3_2_MODEL_VERSION != f"sha256:{DET_R0_SHA256.lower()}":
        return Check(
            "implementation_bindings",
            FAIL,
            "Runtime activation constants drifted from approved records.",
            failures,
        )
    return Check(
        "implementation_bindings",
        PASS,
        "Runtime, generator, policy, and model versions are digest-bound.",
    )


def check_taxonomy() -> Check:
    try:
        document = _json("contracts/phase-3/p3-2-taxonomy.json")
        taxonomy = TaxonomyManifestV1.model_validate(document)
        recorded_digest = document.pop("artifact_digest")
        computed_digest = _canonical_digest(document)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("taxonomy", FAIL, f"P3.2 taxonomy is invalid: {exc}")
    expected_classes = {
        "object.person",
        "vehicle.bicycle",
        "vehicle.car",
        "vehicle.motorcycle",
        "vehicle.bus",
        "vehicle.truck",
        "object.unknown",
    }
    if (
        taxonomy.status != "approved"
        or taxonomy.taxonomy_version != P3_2_TAXONOMY_VERSION
        or {item.id for item in taxonomy.classes} != expected_classes
        or recorded_digest != computed_digest
    ):
        return Check(
            "taxonomy",
            FAIL,
            "P3.2 Tier A taxonomy or its digest is inconsistent.",
        )
    return Check(
        "taxonomy",
        PASS,
        "The approved Tier A taxonomy has seven bounded anonymous classes.",
    )


def check_local_e2e_evidence() -> Check:
    try:
        evidence = _json("contracts/phase-3/p3-2-local-e2e-evidence.json")
        result = evidence["result"]
        boundary = evidence["data_boundary"]
        artifact = evidence["artifact"]
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        return Check("local_e2e", FAIL, f"Local E2E evidence is invalid: {exc}")
    failures: list[str] = []
    if not isinstance(result, dict) or result.get("status") != "succeeded":
        failures.append("result.status")
    if not isinstance(result, dict) or result.get("frame_leases_after_run") != 0:
        failures.append("result.frame_leases_after_run")
    if not isinstance(result, dict) or result.get("idempotent_replay") is not True:
        failures.append("result.idempotent_replay")
    if not isinstance(boundary, dict) or any(
        boundary.get(key) is not False
        for key in (
            "camera_access",
            "external_network_access",
            "government_or_private_data",
            "public_dataset_access",
        )
    ):
        failures.append("data_boundary")
    if not isinstance(artifact, dict) or artifact.get("sha256") != DET_R0_SHA256:
        failures.append("artifact.sha256")
    if evidence.get("temporary_database_deleted") is not True:
        failures.append("temporary_database_deleted")
    if failures:
        return Check(
            "local_e2e",
            FAIL,
            "Local generated-only evidence does not satisfy the recorded boundary.",
            tuple(failures),
        )
    return Check(
        "local_e2e",
        PASS,
        "Verified local CPU E2E succeeded with no retained frame lease.",
        (
            f"candidate_count={result.get('candidate_count')}",
            f"duration_ms={result.get('duration_ms')}",
        ),
    )


def _run(name: str, command: list[str]) -> Check:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    output = [
        line
        for line in (completed.stdout + completed.stderr).splitlines()
        if line.strip()
    ]
    return Check(
        name,
        PASS if completed.returncode == 0 else FAIL,
        f"Command exited with code {completed.returncode}.",
        tuple(output[-8:]),
    )


def validation_checks(artifact_root: Path | None) -> tuple[Check, ...]:
    checks = [
        _run(
            "ruff",
            [
                "uv",
                "run",
                "ruff",
                "check",
                "app/hcam/analytics",
                "app/hcam/database.py",
                "app/hcam/main.py",
                "app/hcam/metrics.py",
                "app/hcam/settings.py",
                "migrations/versions/0009_generated_analytics.py",
                "tools/phase32_generated_e2e.py",
                "tools/phase32_implementation_readiness.py",
                "tests/test_analytics_activation.py",
                "tests/test_analytics_assignment_migration.py",
                "tests/test_analytics_bootstrap.py",
                "tests/test_analytics_generated_execution.py",
                "tests/test_analytics_yolox.py",
            ],
        ),
        _run(
            "focused_tests",
            [
                "uv",
                "run",
                "pytest",
                "-q",
                "tests/test_analytics_activation.py",
                "tests/test_analytics_assignment_migration.py",
                "tests/test_analytics_bootstrap.py",
                "tests/test_analytics_contracts.py",
                "tests/test_analytics_generated_execution.py",
                "tests/test_analytics_taxonomy.py",
                "tests/test_analytics_yolox.py",
                "tests/test_metrics.py",
                "tests/test_deployment_artifacts.py",
            ],
        ),
        _run(
            "analytics_contracts",
            ["uv", "run", "python", "tools/analytics_contracts.py", "check"],
        ),
        _run(
            "release_contracts",
            ["uv", "run", "python", "tools/release_contracts.py", "check"],
        ),
        _run(
            "entry_authorization",
            ["uv", "run", "python", "tools/phase32_entry_readiness.py"],
        ),
    ]
    if artifact_root is not None:
        checks.append(
            _run(
                "live_local_generated_e2e",
                [
                    "uv",
                    "run",
                    "python",
                    "tools/phase32_generated_e2e.py",
                    "--artifact-root",
                    str(artifact_root),
                ],
            )
        )
    return tuple(checks)


def build_report(
    *,
    run_validation: bool,
    artifact_root: Path | None,
) -> Report:
    checks: list[Check] = [
        check_required_files(),
        check_owner_records(),
        check_implementation_bindings(),
        check_taxonomy(),
        check_local_e2e_evidence(),
    ]
    if run_validation:
        checks.extend(validation_checks(artifact_root))
    acceptance_path = ROOT / "contracts/phase-3/p3-2-acceptance.json"
    if acceptance_path.is_file():
        acceptance = _json("contracts/phase-3/p3-2-acceptance.json")
        if (
            acceptance.get("status") == "accepted"
            and acceptance.get("record_id") == "D-P3.2-ACCEPTANCE"
            and acceptance.get("scope")
            == "phase3.p3_2.generated_only_cpu_detection"
            and acceptance.get("accepted_by") == "mayank-admin"
            and acceptance.get("evidence_package_digest")
            == P3_2_ACCEPTED_PACKAGE_DIGEST
            and acceptance.get("package_file_count") == len(PACKAGE_FILES)
        ):
            checks.append(
                Check(
                    "owner_acceptance",
                    PASS,
                    "Owner acceptance of the immutable P3.2 package remains valid; "
                    "the live package digest may include additive later-phase work.",
                    (f"accepted_digest={P3_2_ACCEPTED_PACKAGE_DIGEST}",),
                )
            )
        else:
            checks.append(
                Check(
                    "owner_acceptance",
                    FAIL,
                    "P3.2 acceptance record is missing or differs from the exact "
                    "historical package decision.",
                )
            )
    else:
        checks.append(
            Check(
                "owner_acceptance",
                MANUAL,
                "mayank-admin must accept the final package digest before P3.2 closes.",
            )
        )
    failures = sum(check.status == FAIL for check in checks)
    manual_gates = sum(check.status == MANUAL for check in checks)
    digest, _ = package_digest()
    if failures:
        status = "blocked"
    elif manual_gates:
        status = "ready_for_owner_acceptance"
    else:
        status = "accepted"
    return Report(
        status=status,
        scope="phase3.p3_2.generated_only_cpu_detection",
        package_digest=digest,
        failures=failures,
        manual_gates=manual_gates,
        checks=tuple(checks),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify P3.2 generated-only implementation readiness."
    )
    parser.add_argument("--run-validation", action="store_true")
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-acceptance", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        run_validation=args.run_validation,
        artifact_root=args.artifact_root,
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(
            f"P3.2 implementation: {report.status}; failures={report.failures}; "
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
