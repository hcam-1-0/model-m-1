from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
TOOLS = ROOT / "tools"

AUTH_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-source-implementation-authorization-package.json"
)
CONTRACT = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-contract.json"
)
POWERSHELL = TOOLS / "phase36_quarantine_runtime_controller_u3v_h1_r1_diagnostic.ps1"
REFERENCE = TOOLS / "phase36_quarantine_runtime_controller_u3v_h1_r1_diagnostic_reference.py"
VECTORS = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-vectors.json"
)
EVIDENCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-implementation-evidence.json"
)
IMPLEMENTATION_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-implementation-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-evidence-review.md"
)

AUTH_PACKAGE_DIGEST = "745C50AEB4DB61147C541F897F5E78987F64D9C3B137559F7CA811C0A6A5FD33"
OWNER_STATEMENT_DIGEST = "5C1CE929B0670E3CA0C3B48981233AD60330018DEFAADA6B6F6DC6DB6846EBC4"
IMMUTABLE_INPUTS = {
    TOOLS / "phase36_quarantine_runtime_controller_u3t_preflight.ps1": (
        "69CBF4637A22BB7859ED07D19804C8576D76FB1270FF58D0D182EED2592FCE7B"
    ),
    TOOLS / "phase36_quarantine_runtime_controller.ps1": (
        "78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB"
    ),
    TOOLS / "phase36_quarantine_runtime_controller_reference.py": (
        "C1470C65C6D5DA3EF93161F519BBC01507BBB805C6D433F58C65FDCAFE3FFC4F"
    ),
    CONTRACTS / "p3-6-quarantine-runtime-controller-r0-contract.json": (
        "3F2A0975F92892A96FBC67B951B226D5AB958AE067F55B697ABA43669B8FB00E"
    ),
    CONTRACTS / "p3-6-quarantine-runtime-controller-r0-vectors.json": (
        "31335510565E4C74908C674B88951E81B7A7983331C6DE2E91964C1F8B48C20B"
    ),
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-runtime-binding-r1-evidence.json": (
        "2706F18CA283428A17FDEB0AEB02CC350FE88336D8FBF9AC00CD040F3F0A51E1"
    ),
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-runtime-binding-r1-failure-analysis-r0.json": (
        "51F123AA0E4D8F34255D1EAECC340ABAEAC430CBA00A56AD9ECCA66545ABDC6A"
    ),
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3u-remediation-decision-packet.json": (
        "F3585723D81EC71A7D6F231B6A0EBF477D60611CB8DDC71E5ACAF6A463279F1C"
    ),
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3u-remediation-planning-package.json": (
        "C58B9291E06396374DE92308F2CC52CDB51824BFFDFD1958E4D655C75A894CCD"
    ),
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3u-remediation-planning-acceptance.json": (
        "64C1CDAC72E15988A86434AD85981C59A94AC885DE8D1927A025D13DA2165A03"
    ),
}


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_reference() -> ModuleType:
    spec = importlib.util.spec_from_file_location("hcam_u3v_diagnostic_reference", REFERENCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _apply_mutations(base: object, mutations: list[dict[str, Any]]) -> object:
    candidate = copy.deepcopy(base)
    for mutation in mutations:
        operation = mutation["op"]
        path = mutation["path"]
        if operation == "noop":
            continue
        if operation == "replace_root":
            candidate = copy.deepcopy(mutation["value"])
            continue
        assert isinstance(candidate, dict)
        parent: Any = candidate
        for key in path[:-1]:
            parent = parent[key]
        if operation == "delete":
            del parent[path[-1]]
        elif operation == "set":
            parent[path[-1]] = copy.deepcopy(mutation["value"])
        else:
            raise AssertionError(f"unsupported generated mutation: {operation}")
    return candidate


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(_all_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_all_keys(child))
        return keys
    return set()


def test_exact_digest_bound_authorization_is_recorded_without_runtime_authority() -> None:
    assert _sha256(AUTH_PACKAGE) == AUTH_PACKAGE_DIGEST
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        gate = state[
            "quarantine_runtime_controller_u3v_h1_r1_diagnostic_source_implementation_authorization_package"
        ]
        assert gate["package_digest_sha256"] == AUTH_PACKAGE_DIGEST
        assert gate["owner_U3V_source_implementation_authorization_pending"] is False
        assert gate["source_or_test_implementation_authorized"] is True
        assert gate["owner_statement_utf8_bytes"] == 1761
        assert gate["owner_statement_sha256"] == OWNER_STATEMENT_DIGEST
        assert gate["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
        assert gate["runtime_or_machine_observation_authorized"] is False
        assert gate["another_attempt_or_U3K_authorized"] is False
        assert gate["deployment_or_remote_git_authorized"] is False


def test_all_historical_runtime_planning_and_failure_inputs_remain_byte_exact() -> None:
    for path, digest in IMMUTABLE_INPUTS.items():
        assert _sha256(path) == digest


def test_contract_and_both_source_projections_are_canonical_and_equivalent() -> None:
    reference = _load_reference()
    contract = _read(CONTRACT)
    assert contract["contract_version"] == "1.0.0"
    assert contract["canonical_projection"] == reference.contract_projection()
    assert len(contract["allowlisted_terminal_reason_codes"]) == 11
    assert contract["fixed_invariants"]["maximum_output_bytes"] == 4096

    source = POWERSHELL.read_text(encoding="utf-8")
    match = re.search(
        r"# HCAM_U3V_CANONICAL_PROJECTION_BEGIN\n# (?P<projection>\{.*\})\n# HCAM_U3V_CANONICAL_PROJECTION_END",
        source,
    )
    assert match is not None
    powershell_projection = json.loads(
        match.group("projection"), object_pairs_hook=_reject_duplicates
    )
    assert powershell_projection == contract["canonical_projection"]


def test_exact_128_generated_vectors_cover_every_reason_group_and_family() -> None:
    manifest = _read(VECTORS)
    vectors = manifest["vectors"]
    assert manifest["generated_only"] is True
    assert manifest["external_fixture_model_media_or_Government_data"] is False
    assert manifest["vector_count"] == len(vectors) == 128
    assert len({vector["vector_id"] for vector in vectors}) == 128
    assert {vector["expected_reason_code"] for vector in vectors} == set(
        _read(CONTRACT)["allowlisted_terminal_reason_codes"]
    )
    assert {vector["expected_controller_reason_family"] for vector in vectors} == {
        "policy_valid",
        "sanitized_failure",
        "unknown_or_unavailable",
    }
    assert {vector["group"] for vector in vectors} >= {
        "top_level_shape",
        "contract_identity",
        "terminal_state",
        "reason_family",
        "stage_projection",
        "action_counts",
        "retention_projection",
        "gate_effect",
        "terminal_projection",
    }


def test_generated_vectors_match_machine_disabled_reference_and_remain_sanitized() -> None:
    reference = _load_reference()
    manifest = _read(VECTORS)
    forbidden_output_keys = {
        "candidate",
        "candidate_value",
        "candidate_values",
        "type_name",
        "type_names",
        "keys",
        "raw_projection",
        "exception",
        "stdout",
        "stderr",
        "environment",
        "identity",
        "security_material",
    }
    for vector in manifest["vectors"]:
        if vector["input_kind"] == "candidate":
            candidate = _apply_mutations(
                manifest["base_candidate"], vector["mutations"]
            )
            projection = reference.evaluate_candidate(candidate)
        else:
            projection = reference.diagnostic_projection(
                vector["input_reason_code"],
                vector["input_controller_reason_family"],
            )
        assert projection["reason_code"] == vector["expected_reason_code"]
        assert (
            projection["diagnostic_projection"]["controller_reason_family"]
            == vector["expected_controller_reason_family"]
        )
        assert projection["succeeded"] is vector["expected_succeeded"]
        assert projection["terminal"] is True
        assert projection["retention_projection"] == {
            "raw_controller_material_retained_bytes": 0,
            "sanitized_result_only": True,
        }
        assert projection["gate_effect"]["machine_action_authorized"] is False
        assert projection["gate_effect"]["python_machine_fallback"] is False
        assert projection["gate_effect"]["retry_authorized"] is False
        assert projection["gate_effect"]["U3K_authorized"] is False
        assert projection["gate_effect"]["deployment_authorized"] is False
        assert not (_all_keys(projection) & forbidden_output_keys)
        encoded = json.dumps(projection, separators=(",", ":")).encode("utf-8")
        assert len(encoded) <= 4096


def test_reference_classifier_has_no_machine_or_dynamic_execution_surface() -> None:
    tree = ast.parse(REFERENCE.read_text(encoding="utf-8"), filename=str(REFERENCE))
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add((node.module or "").split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            calls.add(node.func.id)
    assert imports == {"typing"}
    assert not imports & {
        "ctypes",
        "os",
        "pathlib",
        "platform",
        "socket",
        "subprocess",
        "sys",
        "winreg",
    }
    assert not calls & {"__import__", "compile", "eval", "exec", "open"}


def test_powershell_is_source_only_bounded_and_does_not_emit_raw_material() -> None:
    source = POWERSHELL.read_text(encoding="utf-8")
    assert "Do not parse, import, dot-source, or execute" in source
    assert "$Script:HcamU3VMaximumOutputBytes = 4096" in source
    assert "$Candidate = $null" in source
    assert "Invoke-HcamRuntimeController" in source
    assert "ConvertTo-Json" not in source
    assert "Write-Error" not in source
    assert "Write-Host" not in source
    assert ".Exception" not in source
    assert ".Message" not in source


def test_implementation_evidence_package_and_review_are_nonobservational() -> None:
    evidence = _read(EVIDENCE)
    package = _read(IMPLEMENTATION_PACKAGE)
    assert evidence["authorization_package_sha256"] == AUTH_PACKAGE_DIGEST
    assert evidence["generated_vector_count"] == 128
    assert evidence["PowerShell_parse_import_dot_source_or_execution"] is False
    assert evidence["runtime_or_machine_observation"] is False
    assert evidence["another_attempt_or_U3K_authorized"] is False
    assert package["status"] == "source_implementation_complete_owner_acceptance_pending"
    assert package["core_file_count"] == len(package["core_files"])
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    review = REVIEW.read_text(encoding="utf-8")
    assert AUTH_PACKAGE_DIGEST in review
    assert "owner source implementation acceptance pending" in review.lower()
    assert "PowerShell was not parsed or executed" in review


def test_new_records_are_registered_LF_and_human_state_is_synchronized() -> None:
    paths = [
        CONTRACT,
        POWERSHELL,
        REFERENCE,
        VECTORS,
        Path(__file__),
        EVIDENCE,
        IMPLEMENTATION_PACKAGE,
        REVIEW,
    ]
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in paths:
        relative = path.as_posix().removeprefix(ROOT.as_posix() + "/")
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()

    for path in (
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "D-P3.6-U3V-H1-R1-DIAGNOSTIC-IMPLEMENTATION-AUTH" in text
        assert AUTH_PACKAGE_DIGEST in text
        assert "source implementation" in text.lower()
