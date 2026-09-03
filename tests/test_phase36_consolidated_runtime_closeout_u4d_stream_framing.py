from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tools/phase36_consolidated_runtime_closeout_u4d_reference.py"
VECTORS = (
    ROOT
    / "contracts/phase-3/p3-6-consolidated-runtime-closeout-u4d-generated-vectors.json"
)


def _load_reference() -> ModuleType:
    spec = importlib.util.spec_from_file_location("u4d_reference_framing", REFERENCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_request() -> dict[str, object]:
    manifest = json.loads(VECTORS.read_text(encoding="utf-8"))
    return copy.deepcopy(manifest["vectors"][0]["request"])


def test_stdout_boundary_is_inclusive_at_4096_and_rejects_4097() -> None:
    module = _load_reference()
    request = _base_request()
    request["observation"]["stdout_bytes"] = 4096
    assert module.classify_process_output(request)["reason_code"] == (
        "process_result_accepted"
    )

    request["observation"]["stdout_bytes"] = 4097
    assert module.classify_process_output(request)["reason_code"] == (
        "process_stdout_limit_exceeded"
    )


def test_empty_output_precedes_line_count_and_BOM_precedes_JSON() -> None:
    module = _load_reference()
    request = _base_request()
    observation = request["observation"]
    observation["stdout_bytes"] = 0
    observation["stdout_line_count"] = 3
    assert module.classify_process_output(request)["reason_code"] == (
        "process_output_empty"
    )

    request = _base_request()
    observation = request["observation"]
    observation["stdout_has_bom"] = True
    observation["json_parse_valid"] = False
    assert module.classify_process_output(request)["reason_code"] == (
        "process_output_BOM_detected"
    )


def test_nonzero_stderr_precedes_result_framing_and_retains_no_stream() -> None:
    module = _load_reference()
    request = _base_request()
    observation = request["observation"]
    observation["stderr_bytes"] = 1
    observation["stdout_line_count"] = 2
    result = module.classify_process_output(request)

    assert result["reason_code"] == "process_stderr_nonzero"
    assert result["retention"]["raw_stdout_retained_bytes"] == 0
    assert result["retention"]["raw_stderr_retained_bytes"] == 0
    serialized = json.dumps(result, separators=(",", ":"), ensure_ascii=True)
    assert "\n" not in serialized
    assert len(serialized.encode("utf-8")) <= 4096
    assert not serialized.startswith("\ufeff")
    assert not serialized.startswith("#< CLIXML")


def test_child_terminal_envelope_is_one_bounded_utf8_JSON_line() -> None:
    envelope = {
        "contract_version": "1.0.0",
        "terminal": True,
        "succeeded": True,
        "stage": "evidence_seal",
        "reason_code": "generated_validation_accepted",
        "required_case_count": 416,
        "accepted_case_count": 416,
        "source_identity_valid": True,
        "raw_retained_bytes": 0,
    }
    serialized = json.dumps(envelope, separators=(",", ":"), ensure_ascii=True)

    assert set(envelope) == {
        "contract_version",
        "terminal",
        "succeeded",
        "stage",
        "reason_code",
        "required_case_count",
        "accepted_case_count",
        "source_identity_valid",
        "raw_retained_bytes",
    }
    assert json.loads(serialized) == envelope
    assert "\n" not in serialized and "\r" not in serialized
    assert len(serialized.encode("utf-8")) <= 4096
