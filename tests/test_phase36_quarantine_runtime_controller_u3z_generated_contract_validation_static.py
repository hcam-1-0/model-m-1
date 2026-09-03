from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from tools import phase36_quarantine_runtime_controller_r1_reference as reference


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
HARNESS = ROOT / "tools/phase36_quarantine_runtime_controller_r1_generated_validation.ps1"
SOURCE_VECTORS = CONTRACTS / (
    "p3-6-quarantine-runtime-controller-r1-stage-projection-vectors.json"
)
MATERIALIZED_VECTORS = CONTRACTS / (
    "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-vectors.json"
)
AUTHORIZATION_PACKAGE = CONTRACTS / (
    "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-planning-package.json"
)
U3Y_PACKAGE = CONTRACTS / (
    "p3-6-quarantine-runtime-controller-r1-stage-projection-implementation-package.json"
)
EVIDENCE = CONTRACTS / (
    "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-harness-implementation-evidence.json"
)
IMPLEMENTATION_PACKAGE = CONTRACTS / (
    "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-harness-implementation-package.json"
)
REVIEW = DOCS / (
    "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-harness-evidence-review.md"
)

AUTHORIZATION_DECISION = (
    "D-P3.6-U3Z-CONTROLLER-R1-GENERATED-CONTRACT-VALIDATION-HARNESS-IMPLEMENTATION-AUTH"
)
AUTHORIZATION_PACKAGE_SHA256 = (
    "B9696A95EF14D186C7D2CC8D949EE711C2621E907DAD28AF4FC192B2A1A1F09A"
)
OWNER_STATEMENT_SHA256 = (
    "5136263DC036CD37AAEB7EEBA05076C5567761246F59566EB12B4DBA9AE1DA5C"
)
U3Y_PACKAGE_SHA256 = (
    "ED306CDFAA604675DAC42AF3137C566EC82EC2BEBCA9B68BE60DE4B8D6D1DC78"
)
SOURCE_VECTOR_SHA256 = (
    "D8EDF5C0255B40FB6C28BB014C09DC503D2B53665E69C5AA5AB65C744AEA81E4"
)
CONTROLLER_SHA256 = (
    "787655BAC55DDF563E9D1DC43EC37F010C271AB381E541B0734028E3F2B90B31"
)
CONTRACT_SHA256 = (
    "637C5400122874149D9835CC6BC521E5EEC9160222F4A7AC5CA1F6CD99E1BCC4"
)
PYTHON_REFERENCE_SHA256 = (
    "B5C7328CD666E0A8988F9B616C5B2A914D690A40BF2EA289C1F1C755E42B86F0"
)
OWNER_STATEMENT = (
    "D-P3.6-U3Z-CONTROLLER-R1-GENERATED-CONTRACT-VALIDATION-HARNESS-IMPLEMENTATION-AUTH: "
    "I, mayank-admin, authorize source-only implementation of the U3Z controller R1 generated "
    "contract-validation harness package against digest "
    "B9696A95EF14D186C7D2CC8D949EE711C2621E907DAD28AF4FC192B2A1A1F09A. "
    "Implementation is limited to the exact additive PowerShell harness source, exactly 288 "
    "materialized generated-only vectors with one-to-one provenance from the accepted manifest, "
    "one Python generated/static test module, nonobservational evidence and package, canonical "
    "ledgers, documentation, and line-ending records. The accepted U3Y implementation package "
    "digest ED306CDFAA604675DAC42AF3137C566EC82EC2BEBCA9B68BE60DE4B8D6D1DC78 and all "
    "sixteen core files must remain byte-exact. Python may execute generated fixture "
    "materialization, reference, source-text, and static tests only. PowerShell must not be parsed, "
    "imported, dot-sourced, or executed. This does not authorize Python machine access or fallback; "
    "runtime path, metadata, hash, trust, identity, manifest, hardware, machine, storage, F:, B:, "
    "ACL, probe, cleanup, scanner, network, download, artifact, model, inference, camera, media, "
    "data, container, Kubernetes, profile activation, deployment, another attempt, U3K, commit, "
    "push, or remote Git. Seal the U3Z harness source and generated/static evidence for separate "
    "exact owner acceptance before preparing any runtime-binding or generated-validation attempt "
    "package."
)


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read(path: Path) -> dict[str, object]:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _apply(value: object, mutation: dict[str, object]) -> None:
    operation = mutation["op"]
    if operation == "none":
        return
    if operation == "multi":
        for child in mutation["mutations"]:
            _apply(value, child)
        return
    node = value
    for part in mutation["path"][:-1]:
        node = node[part]
    key = mutation["path"][-1]
    if operation in {"set", "add"}:
        node[key] = copy.deepcopy(mutation["value"])
    elif operation == "delete":
        del node[key]
    elif operation == "swap":
        left, right = mutation["indices"]
        node[key][left], node[key][right] = node[key][right], node[key][left]
    else:
        raise AssertionError(operation)


SOURCE_MANIFEST = _read(SOURCE_VECTORS)
MATERIALIZED_MANIFEST = _read(MATERIALIZED_VECTORS)
SOURCE_BY_ID = {vector["id"]: vector for vector in SOURCE_MANIFEST["vectors"]}


def _compile(vector: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    request = copy.deepcopy(SOURCE_MANIFEST["base_request"])
    kind = vector["kind"]
    if kind == "request":
        _apply(request, vector["mutation"])
        assert reference.evaluate_request(request) == vector["expected_projection"]
    elif kind == "result":
        candidate = copy.deepcopy(SOURCE_MANIFEST["base_success_result"])
        _apply(candidate, vector["mutation"])
        assert reference.validate_result(candidate) is vector["expected_valid"]
        if not vector["expected_valid"]:
            request["input_bindings"]["stage_outcomes"][
                "validate_result_contract"
            ] = "result_contract_invalid"
    elif kind == "contract_projection":
        candidate = reference.contract_projection()
        _apply(candidate, vector["mutation"])
        assert reference.projections_equal(candidate) is vector["expected_equal"]
        if not vector["expected_equal"]:
            request["input_bindings"]["cross_language_match"] = False
    else:
        raise AssertionError(kind)
    return request, reference.evaluate_request(request)


def test_exact_owner_authorization_is_recorded_and_digest_bound() -> None:
    assert _sha256(AUTHORIZATION_PACKAGE) == AUTHORIZATION_PACKAGE_SHA256
    assert len(OWNER_STATEMENT.encode("utf-8")) == 1465
    assert hashlib.sha256(OWNER_STATEMENT.encode("utf-8")).hexdigest().upper() == (
        OWNER_STATEMENT_SHA256
    )
    authorization = MATERIALIZED_MANIFEST["authorization"]
    assert authorization == {
        "decision_id": AUTHORIZATION_DECISION,
        "authorization_package_sha256": AUTHORIZATION_PACKAGE_SHA256,
        "owner_statement_utf8_bytes": 1465,
        "owner_statement_sha256": OWNER_STATEMENT_SHA256,
    }


def test_all_sixteen_accepted_U3Y_core_files_remain_byte_exact() -> None:
    assert _sha256(U3Y_PACKAGE) == U3Y_PACKAGE_SHA256
    package = _read(U3Y_PACKAGE)
    assert package["core_file_count"] == len(package["core_files"]) == 16
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]


def test_materialized_manifest_has_exact_counts_and_closed_policy_scope() -> None:
    manifest = MATERIALIZED_MANIFEST
    assert manifest["vector_count"] == len(manifest["cases"]) == 288
    assert manifest["group_counts"] == SOURCE_MANIFEST["group_counts"]
    assert len(manifest["group_counts"]) == 9
    assert set(manifest["group_counts"].values()) == {32}
    assert manifest["source_kind_counts"] == {
        "contract_projection": 32,
        "request": 96,
        "result": 160,
    }
    assert Counter(case["group"] for case in manifest["cases"]) == Counter(
        manifest["group_counts"]
    )
    assert manifest["source_manifest"]["sha256"] == SOURCE_VECTOR_SHA256
    assert manifest["controller_binding"] == {
        "source_path": "tools/phase36_quarantine_runtime_controller_r1.ps1",
        "source_sha256": CONTROLLER_SHA256,
        "contract_path": "contracts/phase-3/p3-6-quarantine-runtime-controller-r1-stage-projection-contract.json",
        "contract_sha256": CONTRACT_SHA256,
        "python_reference_path": "tools/phase36_quarantine_runtime_controller_r1_reference.py",
        "python_reference_sha256": PYTHON_REFERENCE_SHA256,
        "function": "Invoke-HcamRuntimeControllerR1",
        "request_mode": "Policy",
        "machine_authority": False,
        "python_machine_fallback": False,
        "automatic_retry": False,
    }
    assert len({case["case_id"] for case in manifest["cases"]}) == 288
    assert len({case["source_vector_id"] for case in manifest["cases"]}) == 288


@pytest.mark.parametrize(
    "case", MATERIALIZED_MANIFEST["cases"], ids=lambda case: case["case_id"]
)
def test_each_materialized_case_has_exact_one_to_one_provenance(
    case: dict[str, object],
) -> None:
    source = SOURCE_BY_ID[case["source_vector_id"]]
    request, expected = _compile(source)

    assert SOURCE_MANIFEST["vectors"][case["source_vector_index"]] == source
    assert case["source_vector_sha256"] == reference.canonical_sha256(source)
    assert case["source_kind"] == source["kind"]
    assert case["group"] == source["group"]
    assert case["description"] == source["description"]
    assert case["request"] == request
    assert case["expected_projection"] == expected
    assert case["request_sha256"] == reference.canonical_sha256(request)
    assert case["expected_projection_sha256"] == reference.canonical_sha256(expected)
    assert request["mode"] == "Policy"
    assert request["authorization_binding"]["machine_authority"] is False
    assert request["authorization_binding"]["automatic_retry"] is False
    assert reference.validate_result(expected)


def test_result_and_contract_vectors_compile_to_typed_controller_stages() -> None:
    for case in MATERIALIZED_MANIFEST["cases"]:
        source = SOURCE_BY_ID[case["source_vector_id"]]
        expectation = case["source_expectation"]
        request = case["request"]
        if source["kind"] == "result":
            assert expectation["expected_valid"] is source["expected_valid"]
            expected_failure = not source["expected_valid"]
            assert (
                request["input_bindings"]["stage_outcomes"].get(
                    "validate_result_contract"
                )
                == "result_contract_invalid"
            ) is expected_failure
        elif source["kind"] == "contract_projection":
            assert expectation["expected_equal"] is source["expected_equal"]
            assert (
                request["input_bindings"]["cross_language_match"] is False
            ) is (not source["expected_equal"])


def test_literal_null_success_and_all_failure_mappings_are_materialized() -> None:
    success_cases = [
        case
        for case in MATERIALIZED_MANIFEST["cases"]
        if case["group"] == "policy_valid_exact_null_success"
    ]
    assert len(success_cases) == 32
    assert all(
        case["expected_projection"]["stage_projection"]
        == {
            "completed_actions": 18,
            "failed_action": None,
            "failed_stage": None,
        }
        for case in success_cases
    )

    failure_cases = [
        case
        for case in MATERIALIZED_MANIFEST["cases"]
        if case["group"]
        in {"all_eighteen_failure_actions", "all_eighteen_failure_reasons"}
    ]
    assert len(failure_cases) == 64
    actions = {
        case["expected_projection"]["stage_projection"]["failed_action"]
        for case in failure_cases
    }
    reasons = {case["expected_projection"]["reason_code"] for case in failure_cases}
    assert actions == set(reference.ACTION_ORDER)
    assert reasons == set(reference.ACTION_FAILURE_REASONS.values())
    assert all(
        case["expected_projection"]["stage_projection"]["failed_stage"]
        == case["expected_projection"]["reason_code"]
        for case in failure_cases
    )


def test_harness_is_exact_bound_single_entrypoint_and_default_denied() -> None:
    source = HARNESS.read_text(encoding="utf-8")
    folded = source.casefold()

    assert source.count(". $script:ControllerPath") == 1
    assert source.count("Invoke-HcamRuntimeControllerR1 -Request $case.request") == 1
    assert "[ValidatePattern('^[A-F0-9]{64}$')]" in source
    assert CONTROLLER_SHA256 in source
    assert CONTRACT_SHA256 in source
    assert SOURCE_VECTOR_SHA256 in source
    assert PYTHON_REFERENCE_SHA256 in source
    assert "$script:ExpectedCaseCount = 288" in source
    assert "$script:ExpectedGroupCount = 9" in source
    assert "$script:ExpectedCasesPerGroup = 32" in source
    assert "$case.request.mode -cne 'Policy'" in source
    assert "$case.request.authorization_binding.machine_authority -ne $false" in source
    assert "$case.request.authorization_binding.automatic_retry -ne $false" in source
    assert '"U3K_authorized":false' in source
    assert '"deployment_authorized":false' in source

    forbidden = (
        "invoke-expression",
        "start-process",
        "system.diagnostics.process",
        "add-type",
        "import-module",
        "invoke-webrequest",
        "invoke-restmethod",
        "system.net",
        "get-ciminstance",
        "get-wmiobject",
        "microsoft.win32",
        "convertfrom-json",
        "convertto-json",
        "get-childitem",
        "get-content",
        "set-content",
        "new-item",
        "remove-item",
    )
    assert all(token not in folded for token in forbidden)


def test_harness_emits_only_bounded_sanitized_summary_fields() -> None:
    source = HARNESS.read_text(encoding="utf-8")
    assert "raw_fixture_retained_bytes" in source
    assert "raw_process_material_retained_bytes" in source
    assert "machine_action_count" in source
    assert "network_action_count" in source
    assert "automatic_retry_count" in source
    assert "cases_loaded" in source
    assert "cases_executed" in source
    assert "cases_passed" in source
    assert "cases_failed" in source
    assert "cross_language_projection_difference_count" in source
    assert "Write-HcamGeneratedValidationFailure -Stage 'validation'" in source
    assert "raw_exception" not in source.casefold()
    assert "stack" not in source.casefold()
    assert "stderr" not in source.casefold()
    assert "stdout" not in source.casefold()


def test_evidence_package_review_and_closed_gates_are_sealed() -> None:
    evidence = _read(EVIDENCE)
    package = _read(IMPLEMENTATION_PACKAGE)
    review = REVIEW.read_text(encoding="utf-8")

    assert evidence["authorization"]["package_sha256"] == AUTHORIZATION_PACKAGE_SHA256
    assert evidence["authorization"]["owner_statement_sha256"] == (
        OWNER_STATEMENT_SHA256
    )
    assert evidence["source_result"]["materialized_vector_count"] == 288
    assert evidence["validation"]["PowerShell_parse_import_dot_source_or_execution_count"] == 0
    assert evidence["gate_effect"]["owner_implementation_acceptance_pending"] is True
    assert package["authorization_package_sha256"] == AUTHORIZATION_PACKAGE_SHA256
    assert package["accepted_U3Y_package_sha256"] == U3Y_PACKAGE_SHA256
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["current_gate_effect"]["runtime_binding_package_preparation_authorized"] is False
    assert "PowerShell was not parsed, imported, dot-sourced, or executed" in review
    assert "Exact owner implementation acceptance is pending" in review


def test_ledgers_documentation_and_line_endings_are_synchronized() -> None:
    state_key = (
        "quarantine_runtime_controller_u3z_generated_contract_validation_r0_harness_implementation"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)[state_key]
        assert state["authorization_decision_id"] == AUTHORIZATION_DECISION
        assert state["authorization_package_sha256"] == AUTHORIZATION_PACKAGE_SHA256
        assert state["source_implementation_complete"] is True
        assert state["owner_implementation_acceptance_pending"] is True
        assert state["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
        assert state["runtime_binding_or_generated_validation_attempt_authorized"] is False
        assert state["U3K_deployment_commit_push_or_remote_git_authorized"] is False

    human_records = (
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
    )
    for path in human_records:
        text = path.read_text(encoding="utf-8")
        assert AUTHORIZATION_DECISION in text
        assert AUTHORIZATION_PACKAGE_SHA256 in text
        assert OWNER_STATEMENT_SHA256 in text

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (
        HARNESS,
        MATERIALIZED_VECTORS,
        Path(__file__),
        EVIDENCE,
        IMPLEMENTATION_PACKAGE,
        REVIEW,
    ):
        relative = path.relative_to(ROOT).as_posix()
        assert f"{relative} text eol=lf" in attributes
        payload = path.read_bytes()
        assert payload.endswith(b"\n")
        assert b"\r\n" not in payload
