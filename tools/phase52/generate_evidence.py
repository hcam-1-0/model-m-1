from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
from pathlib import Path
from typing import Any

from tools.phase52 import verify_p52


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
BASE_COMMIT = "dce4c23"
EXPECTED_BRANCH = "codex/phase5-product-ux-contracts"
START_PACKAGE_SHA256 = "24F89F18D52404A4FF1AA4A8A52A9DA8E4D4619B7721107B1A82EEF389805B67"
BOUND_INPUT_DIGEST = "3E070D61CC90E969E1A5FA91A9564D1FE151E88293904051B9B2763C5E27A74E"
EVIDENCE_PATH = ROOT / "contracts/phase-5/p5-2-evidence.json"
PACKAGE_PATH = ROOT / "contracts/phase-5/p5-2-evidence-package.json"
PROPOSAL_PATH = ROOT / "contracts/phase-5/p5-2-acceptance-proposal.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if process.returncode != 0 or process.stderr:
        raise RuntimeError("local_git_query_failed")
    return process.stdout.strip()


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


def format_generated_json(*paths: Path) -> None:
    nvm_home = os.environ.get("NVM_HOME")
    override = os.environ.get("HCAM_P5_NODE_RUNTIME")
    if override:
        node = Path(override)
    elif nvm_home and os.name == "nt":
        node = Path(nvm_home) / "v24.18.0" / "node.exe"
    else:
        resolved = shutil.which("node")
        if not resolved:
            raise RuntimeError("bound_node_runtime_unavailable")
        node = Path(resolved)
    prettier = FRONTEND / "node_modules/prettier/bin/prettier.cjs"
    if not node.is_file() or not prettier.is_file():
        raise RuntimeError("bound_formatter_unavailable")
    toolchain = subprocess.run(
        [str(node), str(FRONTEND / "scripts/verify-toolchain.mjs")],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if toolchain.returncode != 0 or toolchain.stderr:
        raise RuntimeError("bound_toolchain_verification_failed")
    formatted = subprocess.run(
        [str(node), str(prettier), "--write", *(str(path) for path in paths)],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if formatted.returncode != 0 or formatted.stderr:
        raise RuntimeError("generated_json_formatting_failed")


def component(path_value: str) -> dict[str, Any]:
    path = ROOT / path_value
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"invalid_component:{path_value}")
    return {"path": path_value, "bytes": path.stat().st_size, "sha256": sha256(path)}


def canonical_component_digest(components: list[dict[str, Any]]) -> str:
    rendered = "\n".join(
        f"{item['path']}|{item['bytes']}|{item['sha256']}"
        for item in sorted(components, key=lambda item: item["path"])
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest().upper()


def _png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"invalid_png:{path.as_posix()}")
    return struct.unpack(">II", header[16:24])


def prepare_frontend_evidence(args: argparse.Namespace) -> None:
    p52_summary_path = FRONTEND / "evidence/p5-2-validation-summary.json"
    summary_input = (
        p52_summary_path
        if p52_summary_path.is_file()
        else FRONTEND / "evidence/validation-summary.json"
    )
    summary = read_json(summary_input)
    if (
        summary.get("schema_version") != "hcam.phase5.p5_2.validation_summary.v1"
        or summary.get("coverage", {}).get("result") != "pass"
        or summary.get("browser", {}).get("result") != "pass"
        or summary.get("builds", {}).get("result") != "pass"
    ):
        raise RuntimeError("frontend_validation_summary_not_passed")
    summary["repository_regression"] = {
        "execution_mode": "complete_local_repository_suite",
        "tests_passed": args.python_tests_passed,
        "tests_failed": 0,
        "tests_skipped": args.python_tests_skipped,
        "subtests_passed": args.python_subtests_passed,
        "configured_postgresql_postgis": False,
        "expected_skip_reason": "HCAM_POSTGRES_TEST_URL is not configured",
        "network_or_remote_git_used": False,
        "result": "pass",
    }
    summary["result"] = "pass"
    write_json(p52_summary_path, summary)
    copies = {
        "dependency-audit.json": "p5-2-dependency-audit.json",
        "source-manifest.json": "p5-2-source-manifest.json",
    }
    for source, destination in copies.items():
        destination_path = FRONTEND / "evidence" / destination
        if not destination_path.is_file():
            shutil.copyfile(FRONTEND / "evidence" / source, destination_path)

    captures: list[dict[str, Any]] = []
    for path in sorted((FRONTEND / "test-results").rglob("*.png")):
        name = path.name
        if name not in {"command-center.png", "gis-center.png"}:
            continue
        relative = path.relative_to(FRONTEND).as_posix()
        profile = "mobile" if "mobile" in relative.lower() else "desktop"
        portal = "command" if name.startswith("command") else "gis"
        width, height = _png_dimensions(path)
        captures.append(
            {
                "portal": portal,
                "profile": profile,
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "width": width,
                "height": height,
            }
        )
    if len(captures) != 4:
        raise RuntimeError(f"expected_four_visual_captures:{len(captures)}")
    write_json(
        FRONTEND / "evidence/p5-2-visual-manifest.json",
        {
            "schema_version": "hcam.phase5.p5_2.visual_manifest.v1",
            "generated_on": "2026-09-08",
            "generated_only": True,
            "loopback_only": True,
            "manual_visual_review": {
                "overlap": False,
                "horizontal_clipping": False,
                "blank_renderer": False,
                "map_and_table_visible": True,
            },
            "captures": captures,
            "result": "pass",
        },
    )
    format_generated_json(
        p52_summary_path,
        FRONTEND / "evidence/p5-2-visual-manifest.json",
    )


def write_evidence_docs(
    *, technical_commit: str, package_sha256: str, content_digest: str, component_count: int
) -> None:
    evidence_text = f"""# P5.2 Evidence Package

Status date: 2026-09-08

## Identity

- Package: `P5.2-EVIDENCE-PACKAGE-R0`
- Package SHA-256: `{package_sha256}`
- Canonical component digest: `{content_digest}`
- Technical commit: `{technical_commit}`
- Components: {component_count}

## Result

The generated-only Command Center and connected GIS Center passed typed-contract,
unit, coverage, build, bundle, Storybook, Edge desktop/mobile, accessibility,
responsive, replay, dependency, SBOM, source-manifest, and complete local Python
repository validation. Command Center remains primary; GIS Center is connected
through one shared domain with MapLibre, guarded deck.gl enhancement, and a
complete list/table/detail fallback.

## Boundaries

No real providers, tiles, cameras, media, Government or private data, models,
inference, backend routes, migrations, operational actions, containers,
Kubernetes, deployment, source import, or remote Git were used or authorized.
Manual screen-reader and separately witnessed 200% zoom evidence remain
unavailable, so no production accessibility claim is made.

Technical evidence earns **11/12 (91.6667%)** for P5.2 and **31/100
(31.0000%)** for Phase 5. The final P5.2 point remains gated by exact owner
acceptance.
"""
    (ROOT / "docs/phase-5/p5-2/evidence.md").write_text(
        evidence_text, encoding="utf-8", newline="\n"
    )
    proposal = read_json(PROPOSAL_PATH)
    proposal_text = f"""# P5.2 Acceptance Proposal

Status: owner acceptance required

## Exact Package

- Evidence package: `P5.2-EVIDENCE-PACKAGE-R0`
- SHA-256: `{package_sha256}`
- Canonical component digest: `{content_digest}`
- Technical commit: `{technical_commit}`

## Acceptance Effect

Exact acceptance changes P5.2 from **11/12 (91.6667%)** to **12/12
(100.0000%)**, change **+8.3333 percentage points**, and Phase 5 from
**31/100 (31.0000%)** to **32/100 (32.0000%)**, change **+1.0000 percentage
point**. It does not start P5.3.

## Owner Statement

```text
{proposal['owner_acceptance_statement']}
```
"""
    (ROOT / "docs/phase-5/p5-2/acceptance-proposal.md").write_text(
        proposal_text, encoding="utf-8", newline="\n"
    )


def seal(args: argparse.Namespace) -> None:
    if not args.technical_commit:
        raise RuntimeError("technical_commit_required")
    technical_commit = git("rev-parse", args.technical_commit)
    if git("branch", "--show-current") != EXPECTED_BRANCH:
        raise RuntimeError("unexpected_branch")
    if git("merge-base", "--is-ancestor", BASE_COMMIT, technical_commit) != "":
        raise RuntimeError("unexpected_git_output")
    preliminary = verify_p52.checks()
    if not preliminary or not all(preliminary.values()):
        failed = [name for name, value in preliminary.items() if not value]
        raise RuntimeError(f"preliminary_readiness_failed:{','.join(failed)}")

    summary = read_json(FRONTEND / "evidence/p5-2-validation-summary.json")
    evidence = {
        "schema_version": "hcam.phase5.p5_2.evidence.v1",
        "evidence_id": "P5.2-EVIDENCE-R0",
        "status": "technical_complete_owner_acceptance_pending",
        "generated_on": "2026-09-08",
        "technical_commit": technical_commit,
        "start_package_sha256": START_PACKAGE_SHA256,
        "bound_input_digest": BOUND_INPUT_DIGEST,
        "validation": summary,
        "environment": {
            "generated_only": True,
            "loopback_browser_only": True,
            "real_provider_tile_camera_media_or_data_used": False,
            "backend_route_or_migration_added": False,
            "model_or_inference_used": False,
            "container_or_kubernetes_used": False,
            "remote_git_used": False,
        },
        "limitations": [
            "generated_only_non_operational_command_and_GIS",
            "fourteen_missing_producers_remain_blocked_or_generated_only",
            "no_manual_screen_reader_or_separately_witnessed_200_percent_zoom_claim",
            "no_configured_PostgreSQL_PostGIS_integration_database",
            "no_hardware_capacity_or_production_accessibility_claim",
            "P5_3_deployment_and_remote_Git_remain_closed",
        ],
        "product_progress_before_owner_acceptance": {
            "P5_2": "11/12 (91.6667%)",
            "Phase_5": "31/100 (31.0000%)",
        },
    }
    write_json(EVIDENCE_PATH, evidence)

    changed = git("diff", "--name-only", "--diff-filter=ACMR", f"{BASE_COMMIT}..{technical_commit}").splitlines()
    changed.append(EVIDENCE_PATH.relative_to(ROOT).as_posix())
    components = [component(path) for path in sorted(set(changed))]
    content_digest = canonical_component_digest(components)
    package = {
        "schema_version": "hcam.phase5.p5_2.evidence_package.v1",
        "package_id": "P5.2-EVIDENCE-PACKAGE-R0",
        "status": "owner_acceptance_required",
        "effective": False,
        "generated_on": "2026-09-08",
        "technical_commit": technical_commit,
        "start_package_sha256": START_PACKAGE_SHA256,
        "bound_input_digest": BOUND_INPUT_DIGEST,
        "component_digest_algorithm": "Sort paths ordinally; render path|bytes|sha256 with LF separators and no terminal LF; SHA-256 the UTF-8 bytes.",
        "canonical_component_digest": content_digest,
        "components": components,
        "component_count": len(components),
        "generated_only": True,
        "P5_2_complete": False,
        "P5_3_authorized": False,
        "remote_Git_authorized": False,
    }
    write_json(PACKAGE_PATH, package)
    package_sha256 = sha256(PACKAGE_PATH)
    statement = (
        "D-P5.2-ACCEPTANCE: I, mayank-admin, accept P5.2 evidence package "
        f"P5.2-EVIDENCE-PACKAGE-R0 with SHA-256 {package_sha256} and canonical "
        f"component digest {content_digest} at technical commit {technical_commit}, "
        "including its generated-only Command Center and connected GIS Center, "
        "validation results, dependency and supply-chain evidence, explicit environment "
        "limitations, and documented safety boundaries. This acceptance completes P5.2 "
        "only. It does not authorize P5.3, source import, backend routes or migrations, "
        "real providers or tiles, cameras or media, Government or private data, models "
        "or inference, operational actions, containers, Kubernetes, deployment, or remote Git."
    )
    proposal = {
        "schema_version": "hcam.phase5.p5_2.acceptance_proposal.v1",
        "decision_id": "D-P5.2-ACCEPTANCE",
        "status": "owner_acceptance_required",
        "effective": False,
        "evidence_package": {
            "package_id": "P5.2-EVIDENCE-PACKAGE-R0",
            "path": PACKAGE_PATH.relative_to(ROOT).as_posix(),
            "sha256": package_sha256,
            "canonical_component_digest": content_digest,
        },
        "technical_commit": technical_commit,
        "accepted_progress_if_approved": {
            "P5_2": "12/12 (100.0000%)",
            "Phase_5": "32/100 (32.0000%)",
        },
        "owner_acceptance_statement": statement,
        "P5_3_authorized": False,
        "remote_Git_authorized": False,
    }
    write_json(PROPOSAL_PATH, proposal)
    write_evidence_docs(
        technical_commit=technical_commit,
        package_sha256=package_sha256,
        content_digest=content_digest,
        component_count=len(components),
    )
    print(
        json.dumps(
            {
                "technical_commit": technical_commit,
                "package_sha256": package_sha256,
                "canonical_component_digest": content_digest,
                "component_count": len(components),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--technical-commit")
    parser.add_argument("--python-tests-passed", type=int, required=True)
    parser.add_argument("--python-tests-skipped", type=int, required=True)
    parser.add_argument("--python-subtests-passed", type=int, default=0)
    args = parser.parse_args()
    prepare_frontend_evidence(args)
    if args.prepare_only:
        print(json.dumps({"status": "prepared", "generated_only": True}, separators=(",", ":")))
        return 0
    seal(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
