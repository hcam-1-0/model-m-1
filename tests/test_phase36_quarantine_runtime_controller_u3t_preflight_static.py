from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
HARNESS = ROOT / "tools" / "phase36_quarantine_runtime_controller_u3t_preflight.ps1"
VECTORS = CONTRACTS / "p3-6-quarantine-runtime-controller-u3t-preflight-r0-vectors.json"
EVIDENCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-preflight-r0-harness-implementation-evidence.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-preflight-r0-harness-implementation-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u3t-preflight-r0-harness-evidence-review.md"
)
AUTHORIZATION_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-preflight-r0-planning-package.json"
)
AUTHORIZATION_DIGEST = (
    "26B8A0A6FF1B8DA556BB68D6E1EA13B51FFF4460D5CA2F50F3E64952528E69F2"
)
DECISION = "D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-AUTH"
EXPECTED_GROUPS = {
    "request_and_source_binding": 12,
    "controller_load_and_function_binding": 8,
    "sanitized_result_contract": 12,
    "timeout_and_output_bounds": 8,
    "forbidden_surface_and_gate_closure": 8,
}
IMMUTABLE_HASHES = {
    "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-contract.json": (
        "3F2A0975F92892A96FBC67B951B226D5AB958AE067F55B697ABA43669B8FB00E"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-vectors.json": (
        "31335510565E4C74908C674B88951E81B7A7983331C6DE2E91964C1F8B48C20B"
    ),
    "tools/phase36_quarantine_runtime_controller.ps1": (
        "78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB"
    ),
    "tools/phase36_quarantine_runtime_controller_reference.py": (
        "C1470C65C6D5DA3EF93161F519BBC01507BBB805C6D433F58C65FDCAFE3FFC4F"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-source-implementation-evidence.json": (
        "012AECD9316A6361C2AA2AD5B6E7F87494C306F9222012464D70440B34EC0813"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-source-implementation-package.json": (
        "484A6FB71216F43A1EAF668DC59091D4FD42EF8543585BFBB588CFCDE089BE30"
    ),
    "tools/phase36_quarantine_generated_validation.ps1": (
        "830D88F8915B084DEF1089927FF785C9C0E7BDB6F0755B5315EE85E9DA8A8B8A"
    ),
    "contracts/phase-3/p3-6-quarantine-generated-powershell-validation-r0-vectors.json": (
        "5C9C9CF9AF61D7AE6F20B4150592B57A4AC540AA983A35CB8384BBD82C764C0C"
    ),
    "tools/phase36_quarantine_transaction_runner.ps1": (
        "22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A"
    ),
    "tools/phase36_quarantine_machine_handlers.psm1": (
        "41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721"
    ),
    "tools/phase36_quarantine_windows_storage_adapter.psm1": (
        "232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9"
    ),
}


def _no_duplicate_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read(path: Path) -> dict[str, object]:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_object
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_exact_authorization_is_bound_without_execution_authority() -> None:
    assert _sha256(AUTHORIZATION_PACKAGE) == AUTHORIZATION_DIGEST
    evidence = _read(EVIDENCE)
    authorization = evidence["implementation_authorization"]
    assert authorization["decision_id"] == DECISION
    assert authorization["authorization_package_digest_sha256"] == AUTHORIZATION_DIGEST
    statement = authorization["canonical_owner_statement"]
    assert len(statement.encode("utf-8")) == 1295
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        "82A090BEEA1A7DE641C39DA2C5195A6E4B565EAFE2647D75AD938A5246A7639B"
    )
    boundaries = evidence["non_observational_boundaries"]
    assert boundaries["PowerShell_parsed_imported_dot_sourced_or_executed"] is False
    assert boundaries["Python_machine_access_or_fallback"] is False
    assert boundaries["runtime_manifest_hardware_or_machine_observation"] is False


def test_manifest_has_exactly_48_generated_vectors_in_required_groups() -> None:
    manifest = _read(VECTORS)
    vectors = manifest["vectors"]
    assert manifest["vector_count"] == 48
    assert len(vectors) == 48
    assert manifest["group_counts"] == EXPECTED_GROUPS
    assert Counter(vector["group"] for vector in vectors) == Counter(EXPECTED_GROUPS)
    assert len({vector["id"] for vector in vectors}) == 48
    generator = manifest["generator"]
    assert generator["external_input_or_data"] is False
    assert generator["PowerShell_parse_import_dot_source_or_execution"] is False
    assert generator["machine_or_runtime_observation"] is False


def test_all_generated_source_text_vectors_pass() -> None:
    source = HARNESS.read_text(encoding="utf-8")
    manifest = _read(VECTORS)
    for vector in manifest["vectors"]:
        check = vector["check"]
        needle = vector["needle"]
        if check == "contains":
            assert needle in source, vector["id"]
        elif check == "not_contains":
            assert needle not in source, vector["id"]
        elif check == "count":
            assert source.count(needle) == vector["expected"], vector["id"]
        else:
            raise AssertionError(f"unsupported generated check: {check}")


def test_embedded_outputs_are_bounded_sanitized_json_contracts() -> None:
    source = HARNESS.read_text(encoding="utf-8")
    pattern = re.compile(r"\$(Hcam\w+Json) = '(\{[^\r\n]+\})'")
    outputs = {name: json.loads(payload) for name, payload in pattern.findall(source)}
    assert set(outputs) == {
        "HcamSourceBindingFailureJson",
        "HcamResultInvalidJson",
        "HcamPolicyValidJson",
    }
    assert {value["reason_code"] for value in outputs.values()} == {
        "source_binding_failed",
        "result_contract_invalid",
        "policy_valid",
    }
    for output in outputs.values():
        assert len(json.dumps(output, separators=(",", ":")).encode("utf-8")) <= 65536
        assert output["terminal"] is True
        assert output["action_counts"]["retries"] == 0
        assert output["action_counts"]["processes"] == 0
        assert output["retention_projection"]["raw_material_retained_bytes"] == 0
        assert output["retention_projection"]["sanitized_result_only"] is True
        assert output["gate_effect"]["machine_action_authorized"] is False
        assert output["gate_effect"]["python_machine_fallback"] is False
        assert output["gate_effect"]["retry_authorized"] is False
        assert output["gate_effect"]["U3T_preflight_authorized"] is False
        assert output["gate_effect"]["U3K_authorized"] is False
        assert output["gate_effect"]["deployment_authorized"] is False


def test_accepted_u3s_and_five_prior_inputs_remain_byte_exact() -> None:
    for relative, expected in IMMUTABLE_HASHES.items():
        assert _sha256(ROOT / relative) == expected, relative


def test_h1_package_binds_exact_source_test_evidence_and_review() -> None:
    package = _read(PACKAGE)
    assert package["owner_acceptance_decision_id"] == (
        "D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-ACCEPTANCE"
    )
    assert package["core_file_count"] == len(package["core_files"])
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    effect = package["current_gate_effect"]
    assert effect["H1_source_implementation_complete"] is True
    assert effect["compatibility_test_allowlist_amendment_pending"] is True
    assert effect["owner_H1_source_implementation_acceptance_pending"] is False
    assert effect["PowerShell_parse_import_or_execution_authorized"] is False
    assert effect["U3T_R1_attempt_U3R_retry_or_U3K_authorized"] is False
    assert REVIEW.is_file()


def test_ledgers_and_docs_expose_the_same_acceptance_gate() -> None:
    package_digest = _sha256(PACKAGE)
    key = "quarantine_runtime_controller_u3t_preflight_r0_H1_implementation_package"
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)[key]
        assert state["package_digest_sha256"] == package_digest
        assert state["compatibility_test_allowlist_amendment_pending"] is True
        assert state["owner_H1_source_implementation_acceptance_pending"] is False
        assert state["PowerShell_parse_import_or_execution_authorized"] is False
        assert state["U3T_R1_attempt_U3R_retry_or_U3K_authorized"] is False

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
        assert DECISION in text
        assert package_digest in text


def test_new_h1_paths_are_lf_and_registered() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (HARNESS, VECTORS, Path(__file__), EVIDENCE, PACKAGE, REVIEW):
        relative = path.as_posix().removeprefix(ROOT.as_posix() + "/")
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()
