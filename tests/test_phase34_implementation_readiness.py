from __future__ import annotations

from tools.phase34_implementation_readiness import (
    FAIL,
    MANUAL,
    check_c10_evidence,
    check_contract_snapshots,
    check_migration_contract,
    check_owner_acceptance,
    check_start_authorization,
    check_structural_boundaries,
    check_supply_chain,
    check_validation_evidence,
)


def test_phase34_implementation_evidence_passes_technical_gates() -> None:
    checks = (
        check_start_authorization(),
        check_supply_chain(),
        check_c10_evidence(),
        check_structural_boundaries(),
        check_migration_contract(),
        check_contract_snapshots(),
        check_validation_evidence(),
    )
    assert all(check.status != FAIL for check in checks)


def test_phase34_final_acceptance_remains_manual() -> None:
    assert check_owner_acceptance().status == MANUAL
