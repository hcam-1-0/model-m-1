from __future__ import annotations

import difflib
import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_R0 = ROOT / "tools/phase36_quarantine_transaction_runner.ps1"
RUNNER_R1 = ROOT / "tools/phase36_quarantine_transaction_runner_r1.ps1"
PACKAGE = ROOT / (
    "contracts/phase-3/"
    "p3-6-consolidated-runtime-closeout-r4-storage-execution-package.json"
)
REQUEST = ROOT / (
    "contracts/phase-3/p3-6-consolidated-runtime-closeout-r4-storage-request.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_r1_runner_is_a_narrow_date_parsing_successor() -> None:
    before = RUNNER_R0.read_text(encoding="utf-8").splitlines()
    after = RUNNER_R1.read_text(encoding="utf-8").splitlines()
    changed = [line for line in difflib.ndiff(before, after) if line[:2] in {"- ", "+ "}]

    assert changed == [
        "+ ",
        "+ # Phase 3.6 additive R1 runner: preserve ISO timestamp strings during JSON parsing.",
        "-         contract_id                 = 'P36-QUARANTINE-TRANSACTION-RUNNER-R0-1.0.0'",
        "+         contract_id                 = 'P36-QUARANTINE-TRANSACTION-RUNNER-R1-1.1.0'",
        "- $script:ContractId = 'P36-QUARANTINE-TRANSACTION-RUNNER-R0-1.0.0'",
        "+ $script:ContractId = 'P36-QUARANTINE-TRANSACTION-RUNNER-R1-1.1.0'",
        "- $request = $StorageRequestJson | ConvertFrom-Json -AsHashtable -Depth 24",
        "+ $request = $StorageRequestJson | ConvertFrom-Json -AsHashtable -Depth 24 -DateKind String",
    ]
    assert _sha256(RUNNER_R0) == (
        "22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A"
    )
    assert _sha256(RUNNER_R1) == (
        "5198332518A88A8605540F3449B88B8EDDD50C51A19C4332C67A3255B9CA8538"
    )


def test_request_binds_package_and_every_repository_source() -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    request = json.loads(REQUEST.read_text(encoding="utf-8"))

    assert request["execution_package_digest_sha256"] == _sha256(PACKAGE)
    assert request["execution_package_files"] == [
        {
            "path": str(PACKAGE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256(PACKAGE),
        }
    ]
    for binding in request["source_binding_files"]:
        assert _sha256(ROOT / binding["path"]) == binding["sha256"]
    assert package["exact_sources"][0] == {
        "path": "tools/phase36_quarantine_transaction_runner_r1.ps1",
        "sha256": _sha256(RUNNER_R1),
    }


def test_request_timestamps_are_literal_round_trip_strings() -> None:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    not_before = datetime.fromisoformat(request["authorization_not_before"])
    expires_at = datetime.fromisoformat(request["authorization_expires_at"])
    runtime_until = datetime.fromisoformat(request["runtime_binding"]["valid_until"])

    assert expires_at == runtime_until
    assert 4 * 60 * 60 <= (expires_at - not_before).total_seconds() <= 5 * 60 * 60
    assert request["authorization_window_current"] is True
    assert request["attempt_unused"] is True


def test_request_keeps_the_exact_bounded_target_and_closed_surfaces() -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    request = json.loads(REQUEST.read_text(encoding="utf-8"))

    assert request["candidate_volume"] == "F:"
    assert request["candidate_root"] == r"F:\HCAM-Quarantine"
    assert request["probe_bytes"] == 4096
    assert request["per_action_timeout_seconds"] == 30
    assert request["total_timeout_seconds"] == 120
    assert len(request["action_ids"]) == 10
    assert len(request["output_paths"]) == 3
    assert package["transaction"]["maximum_attempts"] == 1
    assert package["transaction"]["automatic_retry"] is False
    assert package["authority"]["security_bypass_or_privilege_escalation"] is False
    assert package["authority"]["remote_Git"] is False
