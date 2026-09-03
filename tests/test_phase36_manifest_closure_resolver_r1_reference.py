from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools.phase36_manifest_closure_resolver_r1_reference import (
    candidate_paths,
    canonical_projection,
    resolve_manifest_closure,
)


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tools/phase36_manifest_closure_resolver_r1_reference.py"
VECTORS = ROOT / "contracts/phase-3/p3-6-manifest-closure-resolver-r1-vectors.json"


def _manifest() -> dict[str, object]:
    return json.loads(VECTORS.read_text(encoding="utf-8"))


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest().upper()


@pytest.mark.parametrize("vector", _manifest()["vectors"], ids=lambda item: item["id"])
def test_all_generated_vectors_match_reference(vector: dict[str, object]) -> None:
    actual = resolve_manifest_closure(vector["request"])

    assert actual == vector["expected_result"]
    assert _canonical_sha256(actual) == vector["expected_result_sha256"]
    assert actual["terminal"] is True
    assert not any(
        forbidden in actual
        for forbidden in ("path", "reference", "manifest", "exception", "identity")
    )
    assert all(value is False for value in actual["retention"].values())


def test_exact_Utility_shape_uses_bounded_PSHome_fallback_for_bare_nested_DLL() -> None:
    candidates = candidate_paths(
        "NestedModules",
        "Microsoft.PowerShell.Commands.Utility.dll",
        r"C:\Program Files\PowerShell\7\Modules\Microsoft.PowerShell.Utility",
        r"C:\Program Files\PowerShell\7",
    )

    assert tuple(base for base, _ in candidates) == (
        "manifest_directory",
        "ps_home",
    )
    assert candidates[0][1].endswith(
        r"modules\microsoft.powershell.utility\microsoft.powershell.commands.utility.dll"
    )
    assert candidates[1][1].endswith(
        r"powershell\7\microsoft.powershell.commands.utility.dll"
    )


def test_reference_rejects_unknown_and_malformed_top_level_shapes() -> None:
    valid = copy.deepcopy(_manifest()["vectors"][0]["request"])
    assert resolve_manifest_closure(valid)["succeeded"] is True

    for mutation in (None, [], "request"):
        assert resolve_manifest_closure(mutation)["reason_code"] == "resolver_input_invalid"
    valid["unknown"] = True
    assert resolve_manifest_closure(valid)["reason_code"] == "resolver_input_invalid"


def test_reference_import_surface_has_no_machine_or_process_access() -> None:
    tree = ast.parse(REFERENCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".", 1)[0])

    assert imported == {"collections", "ntpath", "typing", "__future__"}
    assert imported.isdisjoint(
        {
            "ctypes",
            "importlib",
            "os",
            "pathlib",
            "platform",
            "requests",
            "socket",
            "subprocess",
            "urllib",
            "winreg",
        }
    )


def test_canonical_projection_exposes_only_policy_constants() -> None:
    projection = canonical_projection()

    assert projection["contract_version"] == "1.1.0"
    assert projection["operation"] == "resolve_manifest_closure_v1"
    assert projection["maximum_entries"] == 64
    assert projection["maximum_total_bytes"] == 134217728
    assert projection["fallback_fields"] == ["NestedModules", "RequiredAssemblies"]
