from __future__ import annotations

import json
from pathlib import Path

from hcam.cli import main
from hcam.database import Database


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
