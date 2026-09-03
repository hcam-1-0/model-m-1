from __future__ import annotations

import copy
import hashlib
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
    spec = importlib.util.spec_from_file_location("u4d_reference", REFERENCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest().upper()


def test_all_384_generated_vectors_match_reference_and_hashes() -> None:
    module = _load_reference()
    manifest = json.loads(VECTORS.read_text(encoding="utf-8"))

    assert manifest["vector_count"] == len(manifest["vectors"]) == 384
    assert len(manifest["group_counts"]) == 16
    assert set(manifest["group_counts"].values()) == {24}
    for vector in manifest["vectors"]:
        actual = module.classify_process_output(copy.deepcopy(vector["request"]))
        assert actual == vector["expected_result"], vector["id"]
        assert actual["reason_code"] == vector["expected_reason_code"]
        assert _canonical_sha256(actual) == vector["expected_result_sha256"]


def test_vectors_cover_every_reason_and_zero_retention_result() -> None:
    manifest = json.loads(VECTORS.read_text(encoding="utf-8"))
    reasons = {item["expected_reason_code"] for item in manifest["vectors"]}

    assert reasons == {
        "terminal_default_deny_internal_failure",
        "process_start_failed",
        "process_timeout",
        "process_exit_nonzero",
        "process_stdout_limit_exceeded",
        "process_stderr_nonzero",
        "process_output_empty",
        "process_output_multiple_lines",
        "process_output_JSON_invalid",
        "process_output_BOM_detected",
        "process_output_CLIXML_detected",
        "process_output_schema_invalid",
        "process_output_identity_invalid",
        "process_result_accepted",
    }
    for vector in manifest["vectors"]:
        result = vector["expected_result"]
        retention = result["retention"]
        assert retention["raw_stdout_retained_bytes"] == 0
        assert retention["raw_stderr_retained_bytes"] == 0
        assert not any(
            value for key, value in retention.items() if key.endswith("_retained")
        )


def test_reference_is_machine_disabled_and_has_no_fallback_surface() -> None:
    source = REFERENCE.read_text(encoding="utf-8")
    prohibited = (
        "import os",
        "import pathlib",
        "import subprocess",
        "import socket",
        "import requests",
        "import httpx",
        "ctypes",
        "winreg",
        "os.environ",
        "Path(",
        "open(",
        "subprocess.",
    )

    for token in prohibited:
        assert token not in source
    assert "machine-disabled" in source.lower()
    assert "def classify_process_output" in source
    assert "def canonical_projection" in source
