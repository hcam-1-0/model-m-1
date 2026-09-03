from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from tools.phase36_manifest_closure_resolver_r1_reference import (
    BASES,
    CODE_EXTENSIONS,
    CONTRACT_VERSION,
    FALLBACK_FIELDS,
    FIELDS,
    MAX_ENTRIES,
    MAX_FILE_BYTES,
    MAX_REFERENCE_CHARS,
    MAX_TOTAL_BYTES,
    OPERATION,
    REASONS,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/phase-3/p3-6-manifest-closure-resolver-r1-contract.json"
VECTORS = ROOT / "contracts/phase-3/p3-6-manifest-closure-resolver-r1-vectors.json"
DELEGATION = ROOT / "contracts/phase-3/p3-6-combined-execution-delegation.json"
U4E_PACKAGE = ROOT / (
    "contracts/phase-3/"
    "p3-6-consolidated-runtime-closeout-u4e-remediation-planning-package.json"
)
U4E_PACKAGE_SHA256 = "C0BF901B7D66BE11A250F9369C5CE564A59A726E88877E4A77CD36F310997B7D"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_delegation_binds_all_five_recommended_U4E_decisions_transparently() -> None:
    delegation = _read(DELEGATION)
    selected = delegation["selected_current_decisions"]

    assert delegation["delegated_by"] == "mayank-admin"
    assert delegation["delegated_to"] == "codex-agent"
    assert selected["planning_package_sha256"] == U4E_PACKAGE_SHA256
    assert _sha256(U4E_PACKAGE) == U4E_PACKAGE_SHA256
    assert selected["selection_basis"] == (
        "agent_selected_recommended_options_under_explicit_owner_combined_execution_delegation"
    )
    assert {selected[f"D-P3.6-U4E-{index:03d}"] for index in range(1, 6)} == {"A"}
    assert "no_push_merge_PR_or_other_unrequested_remote_Git_write" in delegation[
        "continuing_exclusions"
    ]


def test_contract_matches_machine_disabled_reference_projection() -> None:
    contract = _read(CONTRACT)

    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["operation"] == OPERATION
    assert contract["bounds"] == {
        "maximum_entries": MAX_ENTRIES,
        "maximum_individual_file_bytes": MAX_FILE_BYTES,
        "maximum_total_selected_file_bytes": MAX_TOTAL_BYTES,
        "maximum_reference_characters": MAX_REFERENCE_CHARS,
        "maximum_candidate_count_per_entry": 2,
    }
    assert tuple(contract["field_policies"]) == FIELDS
    assert tuple(contract["resolution_order"]["bare_NestedModules_or_RequiredAssemblies_binary_name"]) == BASES
    assert set(FALLBACK_FIELDS) == {"NestedModules", "RequiredAssemblies"}
    assert set(contract["sanitized_terminal_reason_codes"]) == set(REASONS)
    assert set(CODE_EXTENSIONS).issuperset({".dll", ".ps1", ".psm1"})
    assert contract["result_retention"]["raw_path_or_reference_retained"] is False


def test_vector_manifest_has_512_unique_balanced_generated_cases() -> None:
    manifest = _read(VECTORS)
    vectors = manifest["vectors"]

    assert manifest["contract_version"] == CONTRACT_VERSION
    assert manifest["vector_count"] == len(vectors) == 512
    assert len(manifest["group_counts"]) == 16
    assert set(manifest["group_counts"].values()) == {32}
    assert Counter(item["group"] for item in vectors) == Counter(
        manifest["group_counts"]
    )
    assert len({item["id"] for item in vectors}) == 512
    assert manifest["generator"] == {
        "algorithm": "deterministic_manifest_closure_matrix_v1",
        "random_seed": None,
        "external_input_or_data": False,
        "machine_or_runtime_observation": False,
    }


def test_new_contract_sources_and_vectors_use_LF() -> None:
    for path in (CONTRACT, VECTORS, DELEGATION):
        payload = path.read_bytes()
        assert payload.endswith(b"\n")
        assert b"\r\n" not in payload
