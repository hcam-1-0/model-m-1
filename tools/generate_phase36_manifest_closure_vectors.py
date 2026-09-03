"""Generate the deterministic Phase 3.6 U4F manifest resolver vectors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.phase36_manifest_closure_resolver_r1_reference import (
    CONTRACT_VERSION,
    OPERATION,
    candidate_paths,
    resolve_manifest_closure,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "contracts/phase-3/p3-6-manifest-closure-resolver-r1-vectors.json"
GROUPS = (
    "valid_pshome_bare_binary_fallback",
    "valid_manifest_relative_target",
    "missing_load_bearing_target",
    "ambiguous_dual_candidate",
    "untrusted_target",
    "invalid_or_reparse_target",
    "missing_code_like_FileList_target",
    "missing_non_code_FileList_inventory_allowed",
    "parent_traversal_rejected",
    "absolute_or_URI_reference_rejected",
    "ScriptsToProcess_rejected",
    "malformed_observation_rejected",
    "duplicate_canonical_target_rejected",
    "aggregate_size_bound_enforced",
    "path_context_containment_enforced",
    "unsupported_field_rejected",
)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _base_request() -> dict[str, object]:
    return {
        "contract_version": CONTRACT_VERSION,
        "operation": OPERATION,
        "manifest_directory": r"C:\Program Files\PowerShell\7\Modules\Microsoft.PowerShell.Utility",
        "module_root": r"C:\Program Files\PowerShell\7\Modules",
        "ps_home": r"C:\Program Files\PowerShell\7",
        "entries": [],
        "observations": [],
    }


def _add_entry(
    request: dict[str, object],
    field: str,
    value: str,
    states: tuple[tuple[bool, bool, bool, bool, int], ...],
) -> None:
    entries = request["entries"]
    observations = request["observations"]
    assert isinstance(entries, list) and isinstance(observations, list)
    index = len(entries)
    entries.append({"field": field, "value": value})
    candidates = candidate_paths(
        field,
        value,
        str(request["manifest_directory"]),
        str(request["ps_home"]),
    )
    assert len(candidates) == len(states)
    for (base, path), state in zip(candidates, states, strict=True):
        present, regular, nonreparse, trusted, size_bytes = state
        observations.append(
            {
                "entry_index": index,
                "base": base,
                "candidate_path": path,
                "present": present,
                "regular": regular,
                "nonreparse": nonreparse,
                "trusted": trusted,
                "size_bytes": size_bytes,
            }
        )


def _request_for(group: str, variant: int) -> dict[str, object]:
    request = _base_request()
    if group == "valid_pshome_bare_binary_fallback":
        _add_entry(request, "NestedModules", f"Utility{variant}.dll", ((False, False, True, False, 0), (True, True, True, True, 4096 + variant)))
    elif group == "valid_manifest_relative_target":
        _add_entry(request, "TypesToProcess", f"Types\\Type{variant}.ps1xml", ((True, True, True, True, 1024 + variant),))
    elif group == "missing_load_bearing_target":
        _add_entry(request, "RootModule", f"Module{variant}.psm1", ((False, False, True, False, 0),))
    elif group == "ambiguous_dual_candidate":
        _add_entry(request, "NestedModules", f"Duplicate{variant}.dll", ((True, True, True, True, 1024), (True, True, True, True, 1024)))
    elif group == "untrusted_target":
        _add_entry(request, "RequiredAssemblies", f"Assembly{variant}.dll", ((True, True, True, False, 1024), (False, False, True, False, 0)))
    elif group == "invalid_or_reparse_target":
        _add_entry(request, "FormatsToProcess", f"Formats\\Format{variant}.ps1xml", ((True, True, False, True, 1024),))
    elif group == "missing_code_like_FileList_target":
        _add_entry(request, "FileList", f"Scripts\\Missing{variant}.psm1", ((False, False, True, False, 0),))
    elif group == "missing_non_code_FileList_inventory_allowed":
        _add_entry(request, "FileList", f"docs\\Readme{variant}.md", ((False, False, True, False, 0),))
    elif group == "parent_traversal_rejected":
        request["entries"] = [{"field": "RootModule", "value": f"..\\Escape{variant}.psm1"}]
    elif group == "absolute_or_URI_reference_rejected":
        value = f"C:\\Outside\\Item{variant}.dll" if variant % 2 == 0 else f"https://invalid.example/{variant}.dll"
        request["entries"] = [{"field": "RootModule", "value": value}]
    elif group == "ScriptsToProcess_rejected":
        request["entries"] = [{"field": "ScriptsToProcess", "value": f"Init{variant}.ps1"}]
    elif group == "malformed_observation_rejected":
        _add_entry(request, "RootModule", f"Module{variant}.psm1", ((True, True, True, True, 1024),))
        request["observations"][0].pop("trusted")
    elif group == "duplicate_canonical_target_rejected":
        value = f"Shared{variant}.psm1"
        _add_entry(request, "RootModule", value, ((True, True, True, True, 1024),))
        _add_entry(request, "FileList", value, ((True, True, True, True, 1024),))
    elif group == "aggregate_size_bound_enforced":
        for field, prefix in (("RootModule", "Root"), ("TypesToProcess", "Type"), ("FormatsToProcess", "Format")):
            extension = ".psm1" if field == "RootModule" else ".ps1xml"
            _add_entry(request, field, f"{prefix}{variant}{extension}", ((True, True, True, True, 50 * 1024 * 1024),))
    elif group == "path_context_containment_enforced":
        request["module_root"] = r"D:\Outside"
    elif group == "unsupported_field_rejected":
        request["entries"] = [{"field": "RequiredModules", "value": f"Module{variant}"}]
    else:
        raise AssertionError(group)
    return request


def build_manifest() -> dict[str, object]:
    vectors = []
    for group in GROUPS:
        for variant in range(32):
            request = _request_for(group, variant)
            expected = resolve_manifest_closure(request)
            vectors.append(
                {
                    "id": f"{group}-{variant:02d}",
                    "group": group,
                    "request": request,
                    "expected_result": expected,
                    "expected_result_sha256": hashlib.sha256(_canonical(expected)).hexdigest().upper(),
                }
            )
    return {
        "contract_format": "hcam.phase3.p3_6.manifest_closure_resolver_r1_vectors.v1",
        "contract_version": CONTRACT_VERSION,
        "vector_count": len(vectors),
        "group_counts": {group: 32 for group in GROUPS},
        "generator": {
            "algorithm": "deterministic_manifest_closure_matrix_v1",
            "random_seed": None,
            "external_input_or_data": False,
            "machine_or_runtime_observation": False,
        },
        "vectors": vectors,
    }


def main() -> None:
    OUTPUT.write_text(json.dumps(build_manifest(), indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
