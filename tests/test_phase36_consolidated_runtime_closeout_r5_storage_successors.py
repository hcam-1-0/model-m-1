from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
CONTRACTS = ROOT / "contracts/phase-3"

ADAPTER_R0 = TOOLS / "phase36_quarantine_windows_storage_adapter.psm1"
ADAPTER_R1 = TOOLS / "phase36_quarantine_windows_storage_adapter_r1.psm1"
HANDLER_R0 = TOOLS / "phase36_quarantine_machine_handlers.psm1"
HANDLER_R1 = TOOLS / "phase36_quarantine_machine_handlers_r1.psm1"
RUNNER_R1 = TOOLS / "phase36_quarantine_transaction_runner_r1.ps1"
RUNNER_R2 = TOOLS / "phase36_quarantine_transaction_runner_r2.ps1"
HARNESS_R5 = TOOLS / "phase36_quarantine_generated_validation_r5.ps1"
VECTORS_R0 = CONTRACTS / "p3-6-quarantine-generated-powershell-validation-r0-vectors.json"
VECTORS_R5 = CONTRACTS / "p3-6-quarantine-generated-powershell-validation-r5-vectors.json"

R2_OUTPUT = "p3-6-quarantine-storage-r2-"
R5_OUTPUT = "p3-6-quarantine-storage-r5-"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_r1_adapter_is_only_the_uint32_and_output_history_successor() -> None:
    restored = _text(ADAPTER_R1).replace(R5_OUTPUT, R2_OUTPUT).replace(
        "[uint32]::MaxValue", "[uint32] 0xFFFFFFFF"
    )
    assert restored == _text(ADAPTER_R0)
    assert _text(ADAPTER_R1).count("[uint32]::MaxValue") == 2
    assert _sha256(ADAPTER_R1) == (
        "96C8AFAFBA6C74728E2596753EB2DD198F25D526FDB7A2619FF8763C8E83CD51"
    )


def test_r1_handler_only_redirects_outputs_to_new_attempt_records() -> None:
    restored = _text(HANDLER_R1).replace(R5_OUTPUT, R2_OUTPUT)
    assert restored == _text(HANDLER_R0)
    assert _sha256(HANDLER_R1) == (
        "65D4756315B31CA6F8C7195B28173CD2AEC3977E968441434F66D05DBF67F16B"
    )


def test_r2_runner_is_a_bounded_r5_successor_of_r1() -> None:
    restored = (
        _text(RUNNER_R2)
        .replace(
            "# Phase 3.6 additive R2 runner: preserve ISO strings and R5 evidence history.",
            "# Phase 3.6 additive R1 runner: preserve ISO timestamp strings during JSON parsing.",
        )
        .replace("RUNNER-R2-1.2.0", "RUNNER-R1-1.1.0")
        .replace("phase36_quarantine_machine_handlers_r1.psm1", "phase36_quarantine_machine_handlers.psm1")
        .replace("phase36_quarantine_windows_storage_adapter_r1.psm1", "phase36_quarantine_windows_storage_adapter.psm1")
        .replace(R5_OUTPUT, R2_OUTPUT)
    )
    assert restored == _text(RUNNER_R1)
    assert "ConvertFrom-Json -AsHashtable -Depth 24 -DateKind String" in _text(RUNNER_R2)
    assert _sha256(RUNNER_R2) == (
        "8C3BB5A4CB473954251DDD4B24375AFDEE698FBA4F295A228B1E5898FA6F7189"
    )


def test_r5_vectors_only_redirect_generated_outputs() -> None:
    assert _text(VECTORS_R5).replace(R5_OUTPUT, R2_OUTPUT) == _text(VECTORS_R0)
    assert _sha256(VECTORS_R5) == (
        "59966906B91D3AABFD0648F3B82F911EF1718E1EC9E2F9A6BB035A25346AAC09"
    )


def test_r5_harness_binds_exact_successors_and_disables_storage() -> None:
    text = _text(HARNESS_R5)
    bindings = {
        "phase36_quarantine_transaction_runner_r2.ps1": _sha256(RUNNER_R2),
        "phase36_quarantine_machine_handlers_r1.psm1": _sha256(HANDLER_R1),
        "phase36_quarantine_windows_storage_adapter_r1.psm1": _sha256(ADAPTER_R1),
    }
    for path, digest in bindings.items():
        assert path in text
        assert digest in text
    assert VECTORS_R5.name in text
    assert "ExpectedVectorManifestSha256" in text
    assert "storage_attempt_authorized = $false" in text
    assert "runner_storage_invocation_count = 0" in text
    assert "windows_adapter_import_or_execution_count = 0" in text
    assert _sha256(HARNESS_R5) == (
        "BABECAF519D5F4DB961E12646AD47C6A6D52A1AFD65B2DAD0E0CFF9FFC1BFBB3"
    )


def test_r5_outputs_are_separate_from_preserved_r4_records() -> None:
    for kind in ("authorization", "result", "evidence"):
        assert (CONTRACTS / f"p3-6-quarantine-storage-r2-{kind}.json").is_file()
        assert (CONTRACTS / f"p3-6-quarantine-storage-r5-{kind}.json").is_file()
