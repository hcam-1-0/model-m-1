from __future__ import annotations

import json
from pathlib import Path

from tools import release_contracts


def test_tracked_release_contracts_match_current_application() -> None:
    assert release_contracts.check_contracts() == 0


def test_release_contracts_cover_phase0_to_phase2_boundaries() -> None:
    openapi = json.loads(
        release_contracts.OPENAPI_SNAPSHOT.read_text(encoding="utf-8")
    )
    database = json.loads(
        release_contracts.DATABASE_SNAPSHOT.read_text(encoding="utf-8")
    )

    paths = openapi["schema"]["paths"]
    assert "/health/ready" in paths
    assert "/cameras" in paths
    assert "/streams/{stream_id}/capability-refreshes" in paths
    assert "/streams/{stream_id}/onvif/ptz-commands" in paths

    tables = {table["name"]: table for table in database["tables"]}
    assert {
        "alembic_version",
        "audit_events",
        "cameras",
        "stream_endpoints",
        "stream_capability_refreshes",
        "onvif_operation_runs",
    }.issubset(tables)
    operation_checks = " ".join(
        str(item["sql"])
        for item in tables["onvif_operation_runs"]["check_constraints"]
    )
    assert "capability_discover_sync" in operation_checks


def test_contract_writer_requires_explicit_review_acknowledgment(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(release_contracts, "CONTRACT_ROOT", tmp_path)
    assert release_contracts.write_contracts(acknowledged=False) == 2
    assert list(tmp_path.iterdir()) == []


def test_contract_diff_is_bounded() -> None:
    expected = "\n".join(f"old-{index}" for index in range(500))
    actual = "\n".join(f"new-{index}" for index in range(500))
    diff = release_contracts.contract_diff(Path("contract.json"), expected, actual)
    assert len(diff) == release_contracts._MAX_DIFF_LINES + 1
    assert diff[-1].endswith("diff lines omitted")
