from __future__ import annotations

import json
from pathlib import Path

from hcam.cli import main
from hcam.database import Database
from hcam.operations.database_backup import manifest_path_for


def _create_cli_database(database_url: str) -> None:
    database = Database(database_url, allow_unversioned_schema=True)
    try:
        database.create_schema()
    finally:
        database.dispose()


def test_cli_imports_registry_seed(
    tmp_path: Path,
    seed_file: Path,
    monkeypatch,
    capsys,
) -> None:
    database_url = f"sqlite:///{(tmp_path / 'cli.db').as_posix()}"
    _create_cli_database(database_url)
    monkeypatch.setenv("HCAM_DATABASE_URL", database_url)

    exit_code = main(["import-registry", str(seed_file)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["created"] == 2
    assert output["total"] == 2


def test_cli_reports_missing_registry_seed(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    database_url = f"sqlite:///{(tmp_path / 'cli.db').as_posix()}"
    _create_cli_database(database_url)
    monkeypatch.setenv("HCAM_DATABASE_URL", database_url)

    exit_code = main(["import-registry", str(tmp_path / "missing.json")])
    error = capsys.readouterr().err

    assert exit_code == 1
    assert "registry import failed" in error
    assert "missing.json" in error


def test_cli_backup_verify_and_restore_commands(
    tmp_path: Path,
    seed_file: Path,
    monkeypatch,
    capsys,
) -> None:
    from alembic import command
    from alembic.config import Config

    database_path = tmp_path / "cli-migrated.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("HCAM_DATABASE_URL", database_url)
    command.upgrade(Config("alembic.ini"), "head")
    assert main(["import-registry", str(seed_file)]) == 0
    capsys.readouterr()

    backup_path = tmp_path / "cli-backup.db"
    assert main(["backup-database", str(backup_path)]) == 0
    backup_output = json.loads(capsys.readouterr().out)
    assert backup_output["backup"]["camera_count"] == 2
    assert manifest_path_for(backup_path).is_file()

    assert main(["verify-backup", str(backup_path)]) == 0
    verify_output = json.loads(capsys.readouterr().out)
    assert verify_output["backup"]["sha256"] == backup_output["backup"]["sha256"]

    restored_path = tmp_path / "cli-restored.db"
    assert main(["restore-backup", str(backup_path), str(restored_path)]) == 0
    restore_output = json.loads(capsys.readouterr().out)
    assert restore_output["restored"]["camera_count"] == 2

    drill_path = tmp_path / "cli-recovery-drill"
    assert main(["recovery-drill", str(drill_path)]) == 0
    drill_output = json.loads(capsys.readouterr().out)
    assert drill_output["schema"] == "hcam.phase1.recovery-drill.v1"
    assert drill_output["passed"] is True
    assert (drill_path / "report.json").is_file()


def test_cli_capability_worker_once_is_safe_when_queue_is_empty(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    from alembic import command
    from alembic.config import Config

    database_url = f"sqlite:///{(tmp_path / 'capability-worker.db').as_posix()}"
    monkeypatch.setenv("HCAM_DATABASE_URL", database_url)
    monkeypatch.setenv("HCAM_ENVIRONMENT", "test")
    command.upgrade(Config("alembic.ini"), "head")

    assert main(["capability-worker", "--once", "--worker-id", "cli-test"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output == {"processed": False, "worker_id": "cli-test"}
    assert main(["capability-worker", "--poll-seconds", "0"]) == 1
    assert "must be positive" in capsys.readouterr().err
