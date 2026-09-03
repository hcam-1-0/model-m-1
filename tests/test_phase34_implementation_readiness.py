from __future__ import annotations

from pathlib import Path

from tools import phase34_implementation_readiness as readiness


def test_phase34_implementation_evidence_passes_technical_gates() -> None:
    checks = (
        readiness.check_start_authorization(),
        readiness.check_supply_chain(),
        readiness.check_c10_evidence(),
        readiness.check_structural_boundaries(),
        readiness.check_migration_contract(),
        readiness.check_contract_snapshots(),
        readiness.check_validation_evidence(),
    )
    assert all(check.status != readiness.FAIL for check in checks)


def test_phase34_static_package_is_accepted() -> None:
    report = readiness.build_report(require_clean_source=False)

    assert report.status == "accepted"
    assert report.failures == 0
    assert report.manual_gates == 0
    acceptance = next(
        check for check in report.checks if check.name == "owner_acceptance"
    )
    assert acceptance.status == readiness.PASS
    assert acceptance.evidence == (
        f"accepted_digest={readiness.P3_4_ACCEPTED_PACKAGE_DIGEST}",
        f"accepted_repository_head={readiness.P3_4_ACCEPTED_REPOSITORY_HEAD}",
    )


def test_phase34_acceptance_rejects_a_different_digest(monkeypatch) -> None:
    original_json = readiness._json

    def load(path: Path) -> dict[str, object]:
        record = original_json(path)
        if path == readiness.ACCEPTANCE_PATH:
            record["evidence_package_digest"] = "0" * 64
        return record

    monkeypatch.setattr(readiness, "_json", load)

    check = readiness.check_owner_acceptance()

    assert check.status == readiness.FAIL
    assert "does not match" in check.detail


def test_phase34_acceptance_rejects_a_different_repository_head(monkeypatch) -> None:
    original_json = readiness._json

    def load(path: Path) -> dict[str, object]:
        record = original_json(path)
        if path == readiness.ACCEPTANCE_PATH:
            record["accepted_repository_head"] = "0" * 40
        return record

    monkeypatch.setattr(readiness, "_json", load)

    assert readiness.check_owner_acceptance().status == readiness.FAIL
