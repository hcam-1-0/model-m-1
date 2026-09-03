from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "contracts/phase-3/p3-6-consolidated-runtime-closeout-u4d-process-output-contract.json"
)


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read() -> dict[str, object]:
    return json.loads(
        CONTRACT.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates
    )


def test_contract_has_exact_protocol_fields_and_limits() -> None:
    contract = _read()

    assert contract["contract_version"] == "1.0.0"
    assert contract["operation"] == "classify_process_output_v1"
    assert contract["request_fields"] == [
        "contract_version",
        "operation",
        "observation",
        "source_identity",
        "retention",
    ]
    assert len(contract["observation_fields"]) == 17
    assert len(contract["retention_fields"]) == 8
    assert contract["limits"] == {
        "required_generated_case_count": 416,
        "maximum_stdout_bytes": 4096,
        "maximum_stderr_bytes": 0,
        "terminal_stdout_line_count": 1,
        "raw_retained_bytes": 0,
    }


def test_contract_has_complete_typed_parent_taxonomy_and_precedence() -> None:
    contract = _read()
    precedence = contract["parent_reason_precedence"]
    stage_map = contract["parent_reason_stage_map"]

    assert len(precedence) == len(set(precedence)) == 14
    assert set(precedence) == set(stage_map)
    assert precedence[:6] == [
        "terminal_default_deny_internal_failure",
        "process_start_failed",
        "process_timeout",
        "process_exit_nonzero",
        "process_stdout_limit_exceeded",
        "process_stderr_nonzero",
    ]
    assert precedence[-1] == "process_result_accepted"
    assert stage_map["process_result_accepted"] == "evidence_seal"


def test_child_envelope_and_framing_are_strict_and_bounded() -> None:
    contract = _read()

    assert len(contract["child_envelope_fields"]) == 9
    assert len(contract["child_envelope_reason_codes"]) == 8
    framing = contract["framing_protocol"]
    assert framing == {
        "encoding": "UTF-8",
        "byte_order_mark_allowed": False,
        "line_count": 1,
        "maximum_bytes": 4096,
        "emission_API": "System.Console.Out.WriteLine",
        "PowerShell_object_serialization_allowed": False,
        "CLIXML_allowed": False,
        "stderr_bytes": 0,
        "progress_warning_verbose_debug_or_information_output_allowed": False,
    }


def test_contract_is_zero_retention_and_grants_no_machine_authority() -> None:
    contract = _read()

    assert contract["retention_policy"] == {
        "raw_stdout_or_stderr_content_retained": False,
        "raw_stdout_or_stderr_hash_retained": False,
        "exception_type_message_stack_or_path_retained": False,
        "fixture_environment_identity_or_security_material_retained": False,
        "bounded_counts_booleans_stage_and_allowlisted_reason_only": True,
    }
    assert all(value is False for value in contract["machine_authority"].values())
