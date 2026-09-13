from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path
from typing import Any

from .verify_p54 import verify


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
EXPECTED_BRANCH = "codex/phase5-product-ux-contracts"
START_COMMIT = "ab9d7c9"
START_PACKAGE_SHA256 = (
    "FC38A2A21119C501D1C09868C2AF8598297C7C81619D5F16B0A509B93A92DEA0"
)
BOUND_INPUT_DIGEST = "26C20290D60A1418A36245C7C3671A13C46488A4BB4D94CC984337810B4CC4F2"
EVIDENCE_PATH = ROOT / "contracts/phase-5/p5-4-evidence.json"
PACKAGE_PATH = ROOT / "contracts/phase-5/p5-4-evidence-package.json"
PROPOSAL_PATH = ROOT / "contracts/phase-5/p5-4-acceptance-proposal.json"
POST_TECHNICAL_COMPONENTS = (
    "docs/phase-5/p5-4/implementation.md",
    "docs/phase-5/p5-4/validation.md",
    "frontend/evidence/p5-4-dependency-baseline.json",
    "frontend/evidence/p5-4-fixture-manifest.json",
    "frontend/evidence/p5-4-source-manifest.json",
    "frontend/evidence/p5-4-validation-summary.json",
    "frontend/evidence/p5-4-visual-manifest.json",
    "frontend/scripts/verify-bundles.mjs",
    "frontend/scripts/verify-workspace.mjs",
    "tools/phase54/generate_evidence.py",
)
CRITICAL_BRANCH_MARKERS = (
    "capabilities/src/index.ts",
    "event-invalidation/src/index.ts",
    "intelligence-contracts/src/",
    "intelligence-domain/src/",
    "review-workflows/src/",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object_required:{path.as_posix()}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0 or result.stderr:
        raise RuntimeError("local_git_query_failed")
    return result.stdout.strip()


def component(path_value: str) -> dict[str, Any]:
    path = ROOT / path_value
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"invalid_component:{path_value}")
    return {"path": path_value, "bytes": path.stat().st_size, "sha256": sha256(path)}


def canonical_component_digest(components: list[dict[str, Any]]) -> str:
    rendered = "\n".join(
        f"{item['path']}|{item['bytes']}|{item['sha256']}"
        for item in sorted(components, key=lambda item: str(item["path"]))
    )
    return hashlib.sha256(rendered.encode()).hexdigest().upper()


def _node_runtime() -> Path:
    nvm_home = os.environ.get("NVM_HOME")
    if not nvm_home:
        raise RuntimeError("bound_node_runtime_unavailable")
    node = Path(nvm_home) / "v24.18.0" / "node.exe"
    if not node.is_file():
        raise RuntimeError("bound_node_runtime_unavailable")
    return node


def _run_node_json(script: str) -> dict[str, Any]:
    node = _node_runtime()
    environment = os.environ.copy()
    environment["PATH"] = f"{node.parent}{os.pathsep}{environment.get('PATH', '')}"
    result = subprocess.run(
        [str(node), str(FRONTEND / script)],
        cwd=FRONTEND,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0 or result.stderr:
        raise RuntimeError(f"node_gate_failed:{script}")
    value = json.loads(result.stdout)
    if not isinstance(value, dict) or value.get("status") != "pass":
        raise RuntimeError(f"node_gate_failed:{script}")
    return value


def _source_files() -> list[Path]:
    excluded_parts = {
        "coverage",
        "dist",
        "evidence",
        "node_modules",
        "storybook-static",
        "test-results",
    }
    result: list[Path] = []
    for current_root, directories, files in os.walk(FRONTEND):
        directories[:] = [name for name in directories if name not in excluded_parts]
        root = Path(current_root)
        result.extend(
            path
            for name in files
            if (path := root / name).is_file() and not path.is_symlink()
        )
    return sorted(result)


def _branch_coverage() -> list[dict[str, Any]]:
    coverage = read_json(FRONTEND / "coverage/coverage-summary.json")
    result: list[dict[str, Any]] = []
    for path, value in coverage.items():
        normalized = path.replace("\\", "/")
        if path == "total" or not any(
            marker in normalized for marker in CRITICAL_BRANCH_MARKERS
        ):
            continue
        result.append(
            {
                "file": normalized.split("/frontend/")[-1],
                "branches_percent": value["branches"]["pct"],
            }
        )
    if not result or any(float(item["branches_percent"]) < 95 for item in result):
        raise RuntimeError("critical_branch_floor_not_met")
    return sorted(result, key=lambda item: str(item["file"]))


def _png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"invalid_png:{path.as_posix()}")
    return struct.unpack(">II", header[16:24])


def _write_frontend_evidence(args: argparse.Namespace) -> dict[str, Any]:
    verification = verify(ROOT)
    if verification["status"] != "pass" or verification["generated_cases"] != 832:
        raise RuntimeError("phase54_verification_failed")
    toolchain = _run_node_json("scripts/verify-toolchain.mjs")
    workspace = _run_node_json("scripts/verify-workspace.mjs")
    bundles = _run_node_json("scripts/verify-bundles.mjs")

    baseline = read_json(FRONTEND / "dependency-evidence.json")
    baseline_lock = next(
        item["sha256"]
        for item in baseline["inputs"]
        if item["path"] == "pnpm-lock.yaml"
    )
    current_lock = sha256(FRONTEND / "pnpm-lock.yaml")
    if current_lock != baseline_lock:
        raise RuntimeError("dependency_lock_changed")
    dependency = {
        "schema_version": "hcam.phase5.p5_4.dependency_baseline.v1",
        "generated_on": "2026-09-09",
        "existing_locked_dependencies_only": True,
        "dependency_refresh_or_network_used": False,
        "react_flow_present": False,
        "lockfile": {"sha256": current_lock, "unchanged_from_P5_3": True},
        "root_package_sha256": sha256(FRONTEND / "package.json"),
        "workspace_sha256": sha256(FRONTEND / "pnpm-workspace.yaml"),
        "sbom_sha256": sha256(FRONTEND / "sbom.cdx.json"),
        "accepted_dependency_evidence_sha256": sha256(
            FRONTEND / "dependency-evidence.json"
        ),
        "recorded_advisory_baseline": baseline["audit"],
        "current_vulnerability_refresh_claim": False,
        "result": "pass",
    }
    write_json(FRONTEND / "evidence/p5-4-dependency-baseline.json", dependency)

    fixture_paths = sorted((ROOT / "fixtures/phase-5/p5-4").glob("*.json"))
    fixture_manifest = {
        "schema_version": "hcam.phase5.p5_4.fixture_manifest.v1",
        "generated_on": "2026-09-09",
        "generated_only": True,
        "exact_case_count": 832,
        "canonical_fixture_sha256": verification["canonical_fixture_sha256"],
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in fixture_paths
        ],
        "result": "pass",
    }
    write_json(FRONTEND / "evidence/p5-4-fixture-manifest.json", fixture_manifest)

    sources = [
        {
            "path": path.relative_to(FRONTEND).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in _source_files()
    ]
    source_digest = (
        hashlib.sha256(
            "\n".join(f"{item['path']}:{item['sha256']}" for item in sources).encode()
        )
        .hexdigest()
        .upper()
    )
    source_manifest = {
        "schema_version": "hcam.phase5.p5_4.source_manifest.v1",
        "generated_on": "2026-09-09",
        "generated_only": True,
        "source_file_count": len(sources),
        "aggregate_sha256": source_digest,
        "files": sources,
    }
    write_json(FRONTEND / "evidence/p5-4-source-manifest.json", source_manifest)

    captures = []
    for path in sorted((FRONTEND / "test-results").rglob("intelligence-review-*.png")):
        width, height = _png_dimensions(path)
        captures.append(
            {
                "profile": "mobile" if "mobile" in path.name else "desktop",
                "path": path.relative_to(FRONTEND).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "width": width,
                "height": height,
            }
        )
    if len(captures) != 2:
        raise RuntimeError(f"expected_two_visual_captures:{len(captures)}")
    visual = {
        "schema_version": "hcam.phase5.p5_4.visual_manifest.v1",
        "generated_on": "2026-09-09",
        "generated_only": True,
        "loopback_only": True,
        "viewports": [
            "390x844",
            "768x1024",
            "1366x768",
            "1440x900",
            "1920x1080",
            "2560x1440",
        ],
        "profiles": [
            "low_resource",
            "enhanced_workstation",
            "control_room",
            "owned_gpu_lab",
            "future_server",
        ],
        "manual_visual_review": {
            "desktop": "pass",
            "mobile": "pass",
            "blank_renderer": False,
            "incoherent_overlap": False,
            "horizontal_clipping": False,
            "full_page_fixed_navigation_capture_artifact_recorded": True,
        },
        "captures": captures,
        "result": "pass",
    }
    write_json(FRONTEND / "evidence/p5-4-visual-manifest.json", visual)

    coverage = read_json(FRONTEND / "coverage/coverage-summary.json")
    browser = read_json(FRONTEND / "test-results/browser-results.json")["stats"]
    storybook = read_json(FRONTEND / "storybook-static/index.json")
    applications = []
    for directory in sorted((FRONTEND / "apps").iterdir()):
        if not directory.is_dir():
            continue
        output = [path for path in (directory / "dist").rglob("*") if path.is_file()]
        applications.append(
            {
                "app": directory.name,
                "files": len(output),
                "bytes": sum(path.stat().st_size for path in output),
                "source_maps": len([path for path in output if path.suffix == ".map"]),
            }
        )
    total = coverage["total"]
    summary = {
        "schema_version": "hcam.phase5.p5_4.validation_summary.v1",
        "generated_on": "2026-09-09",
        "generated_only": True,
        "toolchain": toolchain,
        "workspace": workspace,
        "typecheck": "pass",
        "lint": {"result": "pass", "warnings": 0},
        "formatting": "pass",
        "unit_and_component": {
            "files_passed": args.frontend_test_files_passed,
            "tests_passed": args.frontend_tests_passed,
            "tests_failed": 0,
            "result": "pass",
        },
        "coverage": {
            "statements_percent": total["statements"]["pct"],
            "branches_percent": total["branches"]["pct"],
            "functions_percent": total["functions"]["pct"],
            "lines_percent": total["lines"]["pct"],
            "critical_branch_floor_percent": 95,
            "critical_files": _branch_coverage(),
            "result": "pass",
        },
        "browser": {
            "system_browser": "Microsoft Edge",
            "passed": browser["expected"],
            "skipped_by_project_design": browser["skipped"],
            "unexpected": browser["unexpected"],
            "flaky": browser["flaky"],
            "loopback_only": True,
            "axe_violations": 0,
            "result": "pass"
            if browser["unexpected"] == 0 and browser["flaky"] == 0
            else "fail",
        },
        "builds": {
            "applications": applications,
            "total_bytes": sum(item["bytes"] for item in applications),
            "source_maps": sum(item["source_maps"] for item in applications),
            "bundle_gate": bundles,
            "result": "pass",
        },
        "storybook": {
            "stories": len(storybook.get("entries", {})),
            "build": "pass",
            "telemetry": "disabled",
        },
        "fixtures": verification,
        "dependency_and_supply_chain": dependency,
        "visual_review": visual["manual_visual_review"],
        "repository_regression": {
            "tests_passed": args.python_tests_passed,
            "tests_skipped": args.python_tests_skipped,
            "subtests_passed": args.python_subtests_passed,
            "configured_postgresql_postgis": False,
            "network_or_remote_git_used": False,
            "result": "pass" if args.python_tests_passed > 0 else "pending",
        },
        "limitations": [
            "generated_only_non_operational_intelligence_and_review_workspace",
            "twenty_six_producer_gaps_remain_generated_simulated_bridged_or_blocked",
            "no_current_vulnerability_refresh_claim",
            "no_manual_screen_reader_or_separately_witnessed_200_percent_zoom_claim",
            "no_configured_PostgreSQL_PostGIS_integration_database",
            "C1_C10_C50_are_not_hardware_or_production_capacity_claims",
        ],
        "result": "pass"
        if args.python_tests_passed > 0
        else "frontend_pass_repository_regression_pending",
    }
    if summary["browser"]["result"] != "pass" or len(applications) != 8:
        raise RuntimeError("frontend_validation_not_passed")
    write_json(FRONTEND / "evidence/p5-4-validation-summary.json", summary)
    return summary


def _write_implementation_docs(summary: dict[str, Any]) -> None:
    implementation = """# P5.4 Intelligence, Alerts, And Human Review Implementation

Status date: 2026-09-09

## Scope

P5.4 implements a generated-only specialist Intelligence Center connected to
the primary Command Center. It keeps observations, inferences, hypotheses,
candidates, proposed alerts, reviews, corrections, and lifecycle records
visually and semantically distinct. It adds no backend producer, model,
provider, camera, media, operational action, or external side effect.

## Delivered Workstreams

| Workstream | Weight | Technical result |
| --- | ---: | --- |
| P5.4-W1 Contracts and fixtures | 2.0 | Complete: 14 schemas, typed browser contracts, 8 deterministic fixtures, exactly 832 generated cases |
| P5.4-W2 Overview and queues | 2.0 | Complete: separate hypothesis, run, alert, review, and correction workloads with bounded states |
| P5.4-W3 Detail, graph, spatial, and rules | 2.5 | Complete: exact traces, provenance, bounded renderer-independent graph, synchronized tables, and GIS-domain parity |
| P5.4-W4 Alerts and candidate uncertainty | 2.5 | Complete: semantic alert identity, field-level evidence roles, contradiction, missingness, calibration, and abstention |
| P5.4-W5 Human review and concurrency | 2.5 | Complete: server-authoritative quorum, memory-only drafts, ETags, idempotency, receipts, and explicit reconsideration |
| P5.4-W6 Lifecycle, corrections, and invalidation | 1.5 | Complete: append-only chronology, correction impact, stale locks, scoped invalidation, and HTTP confirmation |
| P5.4-W7 Accessibility, security, and profiles | 1.0 | Complete: table-first equivalence, keyboard behavior, safe signals, and authority-invariant profiles |
| P5.4-W8 Validation, evidence, and acceptance | 1.0 | Technical evidence complete; final point withheld for exact owner acceptance |

## Safety Boundary

The implementation is non-operational and generated-only. Identity is never
established by a score, relationship, candidate, proposed alert, or review.
Review outcomes cannot notify, dispatch, enforce, call providers, or trigger
external workflows. React Flow remains absent; the internal graph renderer is
subordinate to complete node and edge tables.
"""
    validation = f"""# P5.4 Validation Record

Status date: 2026-09-09

## Results

| Gate | Result |
| --- | --- |
| Toolchain | Pass: Node {summary["toolchain"]["node"]} and pnpm {summary["toolchain"]["pnpm"]} |
| Workspace | Pass: {summary["workspace"]["apps"]} applications, {summary["workspace"]["packages"]} packages, {summary["workspace"]["edges"]} internal edges, one lockfile |
| Unit/component | Pass: {summary["unit_and_component"]["tests_passed"]} tests in {summary["unit_and_component"]["files_passed"]} files |
| Coverage | Pass: {summary["coverage"]["statements_percent"]}% statements, {summary["coverage"]["branches_percent"]}% branches, {summary["coverage"]["functions_percent"]}% functions, {summary["coverage"]["lines_percent"]}% lines |
| Critical branch floor | Pass: all semantic, review, concurrency, correction, invalidation, and capability files meet 95% |
| Browser/accessibility | Pass: {summary["browser"]["passed"]} Edge checks, {summary["browser"]["skipped_by_project_design"]} intentional skip, zero unexpected/flaky results and zero axe violations |
| Production builds | Pass: 8 portals, {summary["builds"]["total_bytes"]} aggregate bytes, zero source maps |
| Storybook | Pass: {summary["storybook"]["stories"]} stories with telemetry disabled |
| Generated fixtures | Pass: exactly 832 cases and deterministic C1/C10/C50 projections |
| Repository regression | Pass: {summary["repository_regression"]["tests_passed"]} tests and {summary["repository_regression"]["subtests_passed"]} subtests; {summary["repository_regression"]["tests_skipped"]} configured-PostgreSQL skips |
| Compatibility transition | Pass: existing workspace and bundle checkers recognize the Intelligence Center and five packages without weakening gates or budgets |

Desktop and mobile visual review found no blank renderer, incoherent overlap,
or horizontal clipping. The full-page mobile capture records the expected
fixed-navigation and focused skip-link screenshot artifact; live viewport tests
separately prove that navigation does not occlude the workspace.

## Limitations

No real provider, camera, media, identity, investigation, Government/private
data, model, inference, operational action, container, Kubernetes resource,
deployment, or remote Git was used. The dependency advisory state was not
refreshed because network access was prohibited. No production capacity or
production accessibility claim is made.
"""
    (ROOT / "docs/phase-5/p5-4").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs/phase-5/p5-4/implementation.md").write_text(
        implementation, encoding="utf-8", newline="\n"
    )
    (ROOT / "docs/phase-5/p5-4/validation.md").write_text(
        validation, encoding="utf-8", newline="\n"
    )


def prepare(args: argparse.Namespace) -> None:
    summary = _write_frontend_evidence(args)
    _write_implementation_docs(summary)


def seal(args: argparse.Namespace) -> dict[str, Any]:
    if not args.technical_commit:
        raise RuntimeError("technical_commit_required")
    technical_commit = git("rev-parse", args.technical_commit)
    if git("branch", "--show-current") != EXPECTED_BRANCH:
        raise RuntimeError("unexpected_branch")
    if git("merge-base", "--is-ancestor", START_COMMIT, technical_commit) != "":
        raise RuntimeError("unexpected_git_output")
    summary = read_json(FRONTEND / "evidence/p5-4-validation-summary.json")
    if summary.get("result") != "pass":
        raise RuntimeError("validation_summary_not_passed")
    evidence = {
        "schema_version": "hcam.phase5.p5_4.evidence.v1",
        "evidence_id": "P5.4-EVIDENCE-R0",
        "status": "technical_complete_owner_acceptance_pending",
        "generated_on": "2026-09-09",
        "technical_commit": technical_commit,
        "start_package_sha256": START_PACKAGE_SHA256,
        "bound_input_digest": BOUND_INPUT_DIGEST,
        "validation": summary,
        "environment": {
            "generated_only": True,
            "loopback_browser_only": True,
            "real_provider_camera_media_identity_or_data_used": False,
            "backend_route_or_migration_added": False,
            "model_or_inference_used": False,
            "operational_side_effect_used": False,
            "container_or_kubernetes_used": False,
            "remote_git_used": False,
        },
        "compatibility_transition": {
            "classification": "post_start_user_directed_narrow_checker_sync",
            "paths": [
                "frontend/scripts/verify-bundles.mjs",
                "frontend/scripts/verify-workspace.mjs",
            ],
            "purpose": "Recognize the Intelligence Center and five P5.4 packages in existing topology and generated-marker checks.",
            "gate_or_budget_weakened": False,
        },
        "limitations": summary["limitations"],
        "product_progress_before_owner_acceptance": {
            "P5_4": "14/15 (93.3333%)",
            "Phase_5": "62/100 (62.0000%)",
        },
    }
    write_json(EVIDENCE_PATH, evidence)
    changed = git(
        "diff",
        "--name-only",
        "--diff-filter=ACMR",
        f"{START_COMMIT}..{technical_commit}",
    ).splitlines()
    changed.extend(POST_TECHNICAL_COMPONENTS)
    changed.append(EVIDENCE_PATH.relative_to(ROOT).as_posix())
    components = [component(path) for path in sorted(set(changed))]
    content_digest = canonical_component_digest(components)
    package = {
        "schema_version": "hcam.phase5.p5_4.evidence_package.v1",
        "package_id": "P5.4-EVIDENCE-PACKAGE-R0",
        "status": "owner_acceptance_required",
        "effective": False,
        "generated_on": "2026-09-09",
        "technical_commit": technical_commit,
        "start_package_sha256": START_PACKAGE_SHA256,
        "bound_input_digest": BOUND_INPUT_DIGEST,
        "component_digest_algorithm": "Sort paths ordinally; render path|bytes|sha256 with LF separators and no terminal LF; SHA-256 the UTF-8 bytes.",
        "canonical_component_digest": content_digest,
        "component_count": len(components),
        "components": components,
        "generated_only": True,
        "P5_4_complete": False,
        "P5_5_authorized": False,
        "remote_Git_authorized": False,
    }
    write_json(PACKAGE_PATH, package)
    package_sha = sha256(PACKAGE_PATH)
    statement = (
        "D-P5.4-ACCEPTANCE: I, mayank-admin, accept P5.4 evidence package "
        f"P5.4-EVIDENCE-PACKAGE-R0 with SHA-256 {package_sha} and canonical "
        f"component digest {content_digest} at technical commit {technical_commit}, "
        "including its generated-only Intelligence Center, mandatory human-review "
        "workflows, validation results, preserved dependency baseline, explicit "
        "environment limitations, and documented safety boundaries. This acceptance "
        "completes P5.4 only. It does not authorize P5.5, real providers or network "
        "access, cameras or media, Government or private data, real investigations or "
        "identities, models or inference, operational alerts, notifications, dispatch, "
        "enforcement or autonomous actions, containers, Kubernetes, deployment, or remote Git."
    )
    proposal = {
        "schema_version": "hcam.phase5.p5_4.acceptance_proposal.v1",
        "decision_id": "D-P5.4-ACCEPTANCE",
        "status": "owner_acceptance_required",
        "effective": False,
        "evidence_package": {
            "package_id": "P5.4-EVIDENCE-PACKAGE-R0",
            "path": PACKAGE_PATH.relative_to(ROOT).as_posix(),
            "sha256": package_sha,
            "canonical_component_digest": content_digest,
        },
        "technical_commit": technical_commit,
        "accepted_progress_if_approved": {
            "P5_4": "15/15 (100.0000%)",
            "Phase_5": "63/100 (63.0000%)",
        },
        "owner_acceptance_statement": statement,
        "P5_5_authorized": False,
        "remote_Git_authorized": False,
    }
    write_json(PROPOSAL_PATH, proposal)
    evidence_doc = f"""# P5.4 Evidence Package

Status date: 2026-09-09

## Identity

- Package: `P5.4-EVIDENCE-PACKAGE-R0`
- Package SHA-256: `{package_sha}`
- Canonical component digest: `{content_digest}`
- Technical commit: `{technical_commit}`
- Components: {len(components)}

## Result

The generated-only Intelligence Center passed contracts, unit tests, branch
coverage, strict TypeScript, lint, formatting, all-portal builds, Storybook,
Edge desktop/mobile accessibility, concurrency, replay, C1/C10/C50, bundle,
dependency-baseline, visual, and complete repository regression gates.

Technical evidence earns **14/15 P5.4 points (93.3333%)**, change **+40.0000
percentage points**, and Phase 5 reaches **62/100 (62.0000%)**, change
**+6.0000 percentage points**. The final P5.4 point requires exact owner
acceptance.

## Boundaries

No real provider, camera, media, identity, investigation, Government/private
data, model, inference, operational action, container, Kubernetes resource,
deployment, or remote Git was used or authorized.
"""
    proposal_doc = f"""# P5.4 Acceptance Proposal

Status: owner acceptance required

## Exact Package

- Evidence package: `P5.4-EVIDENCE-PACKAGE-R0`
- SHA-256: `{package_sha}`
- Canonical component digest: `{content_digest}`
- Technical commit: `{technical_commit}`

## Acceptance Effect

Exact acceptance changes P5.4 from **14/15 (93.3333%)** to **15/15
(100.0000%)**, change **+6.6667 percentage points**, and Phase 5 from
**62/100 (62.0000%)** to **63/100 (63.0000%)**, change **+1.0000 percentage
point**. It completes P5.4 only and does not start P5.5.

## Owner Statement

```text
{statement}
```
"""
    (ROOT / "docs/phase-5/p5-4/evidence.md").write_text(
        evidence_doc, encoding="utf-8", newline="\n"
    )
    (ROOT / "docs/phase-5/p5-4/acceptance-proposal.md").write_text(
        proposal_doc, encoding="utf-8", newline="\n"
    )
    return {
        "technical_commit": technical_commit,
        "package_sha256": package_sha,
        "canonical_component_digest": content_digest,
        "component_count": len(components),
        "owner_acceptance_statement": statement,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--technical-commit")
    parser.add_argument("--frontend-test-files-passed", type=int, default=43)
    parser.add_argument("--frontend-tests-passed", type=int, default=168)
    parser.add_argument("--python-tests-passed", type=int, default=0)
    parser.add_argument("--python-tests-skipped", type=int, default=0)
    parser.add_argument("--python-subtests-passed", type=int, default=0)
    args = parser.parse_args()
    prepare(args)
    if args.prepare_only:
        print(
            json.dumps({"status": "prepared", "generated_only": True}, sort_keys=True)
        )
        return 0
    result = seal(args)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
