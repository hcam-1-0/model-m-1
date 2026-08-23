from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from hcam.camera_registry.importer import RegistryImporter
from hcam.database import Database
from hcam.operations.database_backup import DatabaseBackupError
from hcam.operations.recovery_drill import (
    RECOVERY_DRILL_FORMAT,
    run_sqlite_recovery_drill,
)


def _migrated_seeded_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    seed_file: Path,
) -> str:
    database_path = tmp_path / "recovery-source.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("HCAM_DATABASE_URL", database_url)
    command.upgrade(Config("alembic.ini"), "head")
    database = Database(database_url)
    try:
        RegistryImporter(database.session_factory).import_file(seed_file)
    finally:
        database.dispose()
    return database_url


def test_recovery_drill_produces_private_machine_readable_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    seed_file: Path,
) -> None:
    database_url = _migrated_seeded_database(tmp_path, monkeypatch, seed_file)
    destination = tmp_path / "drill-001"

    report = run_sqlite_recovery_drill(
        database_url,
        destination,
        max_recovery_seconds=30,
    )
    persisted = json.loads((destination / "report.json").read_text(encoding="utf-8"))

    assert report.passed is True
    assert persisted["schema"] == RECOVERY_DRILL_FORMAT
    assert persisted["snapshot"]["camera_count"] == 2
    assert persisted["snapshot"]["audit_event_count"] == 1
    assert persisted["scope"] == {
        "database": "sqlite",
        "metadata_only": True,
        "video_used": False,
    }
    assert str(tmp_path) not in json.dumps(persisted)
    assert "database_url" not in json.dumps(persisted)
    assert (destination / "backup.db").is_file()
    assert (destination / "backup.db.manifest.json").is_file()
    assert (destination / "restored.db").is_file()
    if os.name != "nt":
        assert destination.stat().st_mode & 0o777 == 0o700
        assert (destination / "report.json").stat().st_mode & 0o777 == 0o600


def test_recovery_drill_never_overwrites_prior_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    seed_file: Path,
) -> None:
    database_url = _migrated_seeded_database(tmp_path, monkeypatch, seed_file)
    destination = tmp_path / "existing-drill"
    destination.mkdir()
    marker = destination / "preserve.txt"
    marker.write_text("preserve", encoding="utf-8")

    with pytest.raises(DatabaseBackupError, match="already exists"):
        run_sqlite_recovery_drill(database_url, destination)

    assert marker.read_text(encoding="utf-8") == "preserve"


def test_recovery_drill_records_unmet_time_objective(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    seed_file: Path,
) -> None:
    database_url = _migrated_seeded_database(tmp_path, monkeypatch, seed_file)
    ticks = iter([10.0, 11.0])
    monkeypatch.setattr(
        "hcam.operations.recovery_drill.perf_counter",
        lambda: next(ticks),
    )

    report = run_sqlite_recovery_drill(
        database_url,
        tmp_path / "slow-drill",
        max_recovery_seconds=0.5,
    )

    assert report.passed is False
    assert report.recovery_objective.measured_seconds == 1.0
    assert report.recovery_objective.met is False


@pytest.mark.parametrize("objective", [0, -1, float("nan"), float("inf")])
def test_recovery_drill_rejects_invalid_objective(
    tmp_path: Path,
    objective: float,
) -> None:
    with pytest.raises(DatabaseBackupError, match="must be positive"):
        run_sqlite_recovery_drill(
            "sqlite:///unused.db",
            tmp_path / "invalid-drill",
            max_recovery_seconds=objective,
        )
