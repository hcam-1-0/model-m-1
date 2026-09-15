from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "eb46749"
EXPECTED_BRANCH = "codex/phase5-product-ux-contracts"
START_PACKAGE_SHA256 = (
    "3B4A0CDD44185A94E7C04FB9038032EDDB1EB145E3C551A5A12BA81BD4A2A66E"
)
BOUND_INPUT_DIGEST = (
    "4C44F600C3BAB1D7D997391BDF880AC2BD3CBEDA565A5DF274F5753B381DCFE2"
)
EVIDENCE_PATH = ROOT / "contracts/phase-5/p5-1-evidence.json"
PACKAGE_PATH = ROOT / "contracts/phase-5/p5-1-evidence-package.json"
PROPOSAL_PATH = ROOT / "contracts/phase-5/p5-1-acceptance-proposal.json"


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


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def component(path_value: str) -> dict[str, Any]:
    path = ROOT / path_value
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"invalid_component:{path_value}")
    return {
        "path": path_value,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def canonical_component_digest(components: list[dict[str, Any]]) -> str:
    rendered = "\n".join(
        f"{item['path']}|{item['bytes']}|{item['sha256']}"
        for item in sorted(components, key=lambda item: item["path"])
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--technical-commit", required=True)
    args = parser.parse_args()

    technical_commit = git("rev-parse", args.technical_commit)
    if git("branch", "--show-current") != EXPECTED_BRANCH:
        raise RuntimeError("unexpected_branch")
    if git("merge-base", "--is-ancestor", BASE_COMMIT, technical_commit) != "":
        raise RuntimeError("unexpected_git_output")

    summary = json.loads(
        (ROOT / "frontend/evidence/validation-summary.json").read_text(
            encoding="utf-8"
        )
    )
    if summary.get("result") != "pass":
        raise RuntimeError("validation_summary_not_passed")

    evidence = {
        "schema_version": "hcam.phase5.p5_1.evidence.v1",
        "evidence_id": "P5.1-EVIDENCE-R0",
        "status": "technical_complete_owner_acceptance_pending",
        "generated_on": "2026-09-07",
        "technical_commit": technical_commit,
        "start_package_sha256": START_PACKAGE_SHA256,
        "bound_input_digest": BOUND_INPUT_DIGEST,
        "validation": summary,
        "environment": {
            "generated_only": True,
            "network_used_after_dependency_materialization": False,
            "real_data_used": False,
            "camera_or_media_used": False,
            "map_or_provider_runtime_used": False,
            "model_or_inference_used": False,
            "container_or_kubernetes_used": False,
            "remote_git_used": False,
        },
        "limitations": [
            "generated_only_operator_foundation",
            "no_manual_screen_reader_or_separately_witnessed_200_percent_zoom_claim",
            "no_configured_PostgreSQL_PostGIS_integration_database",
            "no_map_tile_camera_media_provider_model_inference_or operational_runtime",
            "no_Government_police_private_biometric_case_or evidence_data",
            "generated_dependency_and_build_trees_preserved_outside_repository",
            "P5_2_deployment_and_remote_Git_remain_closed",
        ],
        "product_progress_before_owner_acceptance": {
            "P5_1": "10.5/12 (87.5000%)",
            "Phase_5": "18.5/100 (18.5000%)",
        },
    }
    write_json(EVIDENCE_PATH, evidence)

    changed = git(
        "diff",
        "--name-only",
        "--diff-filter=ACMR",
        f"{BASE_COMMIT}..{technical_commit}",
    ).splitlines()
    components = [component(path) for path in sorted(set(changed))]
    components.append(component(EVIDENCE_PATH.relative_to(ROOT).as_posix()))
    components.sort(key=lambda item: item["path"])
    content_digest = canonical_component_digest(components)
    package = {
        "schema_version": "hcam.phase5.p5_1.evidence-package.v1",
        "package_id": "P5.1-EVIDENCE-PACKAGE-R0",
        "status": "owner_acceptance_required",
        "effective": False,
        "generated_on": "2026-09-07",
        "technical_commit": technical_commit,
        "start_package_sha256": START_PACKAGE_SHA256,
        "bound_input_digest": BOUND_INPUT_DIGEST,
        "component_digest_algorithm": (
            "Sort components by path using ordinal path text, render "
            "path|bytes|sha256 with LF separators and no terminal LF, then "
            "SHA-256 over UTF-8 bytes."
        ),
        "canonical_component_digest": content_digest,
        "components": components,
        "component_count": len(components),
        "generated_only": True,
        "P5_1_complete": False,
        "P5_2_authorized": False,
        "remote_Git_authorized": False,
    }
    write_json(PACKAGE_PATH, package)
    package_sha256 = sha256(PACKAGE_PATH)

    statement = (
        "D-P5.1-ACCEPTANCE: I, mayank-admin, accept P5.1 evidence package "
        f"P5.1-EVIDENCE-PACKAGE-R0 with SHA-256 {package_sha256} and canonical "
        f"component digest {content_digest} at technical commit {technical_commit}, "
        "including its generated-only Shared Application Foundation, validation "
        "results, dependency and supply-chain evidence, explicit environment "
        "limitations, and documented safety boundaries. This acceptance completes "
        "P5.1 only. It does not authorize P5.2, source import, backend routes or "
        "migrations, map or media runtime, providers or operational network access, "
        "Government or private data, models or inference, operational actions, "
        "containers, Kubernetes, deployment, or remote Git."
    )
    proposal = {
        "schema_version": "hcam.phase5.p5_1.acceptance-proposal.v1",
        "decision_id": "D-P5.1-ACCEPTANCE",
        "status": "owner_acceptance_required",
        "effective": False,
        "evidence_package": {
            "package_id": "P5.1-EVIDENCE-PACKAGE-R0",
            "path": PACKAGE_PATH.relative_to(ROOT).as_posix(),
            "sha256": package_sha256,
            "canonical_component_digest": content_digest,
        },
        "technical_commit": technical_commit,
        "accepted_progress_if_approved": {
            "P5_1": "12/12 (100.0000%)",
            "Phase_5": "20/100 (20.0000%)",
        },
        "owner_acceptance_statement": statement,
        "P5_2_authorized": False,
        "remote_Git_authorized": False,
    }
    write_json(PROPOSAL_PATH, proposal)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
