from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select

from hcam.audit.models import AuditEvent
from hcam.camera_registry.importer import RegistryImporter
from hcam.camera_registry.models import Camera
from hcam.database import CURRENT_SCHEMA_REVISION, Database
from hcam.operations.database_backup import (
    BACKUP_FORMAT,
    DatabaseBackupError,
    create_sqlite_backup,
    inspect_database_file,
    manifest_path_for,
    restore_sqlite_backup,
    sqlite_database_path,
    verify_sqlite_backup,
)


def _migrated_database(tmp_path: Path, monkeypatch) -> tuple[str, Path]:
    database_path = tmp_path / "source.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("HCAM_DATABASE_URL", database_url)
    command.upgrade(Config("alembic.ini"), "head")
    return database_url, database_path


def _import_seed(database_url: str, seed_file: Path) -> None:
    database = Database(database_url)
    try:
        RegistryImporter(database.session_factory).import_file(seed_file)
    finally:
        database.dispose()


def test_backup_verify_and_restore_recovery_cycle(
    tmp_path: Path,
    monkeypatch,
    seed_file: Path,
) -> None:
    database_url, source_path = _migrated_database(tmp_path, monkeypatch)
    _import_seed(database_url, seed_file)
    backup_path = tmp_path / "recovery" / "phase1.db"

    created = create_sqlite_backup(database_url, backup_path)
    verified = verify_sqlite_backup(backup_path)
    restored_path = tmp_path / "restored" / "phase1-restored.db"
    restored = restore_sqlite_backup(
        backup_path,
        restored_path,
        active_database_url=database_url,
    )

    assert created.backup.camera_count == 2
    assert created.backup.audit_event_count == 1
    assert created.backup.schema_revision == CURRENT_SCHEMA_REVISION
    assert created.backup.sha256 == verified.backup.sha256
    assert created.manifest_path == str(manifest_path_for(backup_path.resolve()))
    assert restored.restored.camera_count == 2
    assert restored.restored.audit_event_count == 1
    assert source_path.is_file()
    assert backup_path.is_file()
    assert restored_path.is_file()

    restored_database = Database(f"sqlite:///{restored_path.as_posix()}")
    try:
        restored_database.check_ready()
        with restored_database.session_factory() as session:
            assert session.scalar(select(func.count()).select_from(Camera)) == 2
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
    finally:
        restored_database.dispose()


def test_backup_manifest_contains_only_integrity_metadata(
    tmp_path: Path,
    monkeypatch,
    seed_file: Path,
) -> None:
    database_url, _ = _migrated_database(tmp_path, monkeypatch)
    _import_seed(database_url, seed_file)
    backup_path = tmp_path / "backup.db"

    create_sqlite_backup(database_url, backup_path)
    manifest = json.loads(
        manifest_path_for(backup_path).read_text(encoding="utf-8")
    )

    assert manifest["format"] == BACKUP_FORMAT
    assert manifest["backup"]["camera_count"] == 2
    assert "database_url" not in json.dumps(manifest)
    assert "display_name" not in json.dumps(manifest)
    assert str(tmp_path) not in json.dumps(manifest)
    if os.name != "nt":
        assert backup_path.stat().st_mode & 0o777 == 0o600
        assert manifest_path_for(backup_path).stat().st_mode & 0o777 == 0o600


def test_modified_backup_is_rejected(
    tmp_path: Path,
    monkeypatch,
    seed_file: Path,
) -> None:
    database_url, _ = _migrated_database(tmp_path, monkeypatch)
    _import_seed(database_url, seed_file)
    backup_path = tmp_path / "backup.db"
    create_sqlite_backup(database_url, backup_path)

    with backup_path.open("ab") as handle:
        handle.write(b"tampered")

    with pytest.raises(DatabaseBackupError, match="integrity manifest"):
        verify_sqlite_backup(backup_path)


def test_modified_manifest_is_rejected(
    tmp_path: Path,
    monkeypatch,
    seed_file: Path,
) -> None:
    database_url, _ = _migrated_database(tmp_path, monkeypatch)
    _import_seed(database_url, seed_file)
    backup_path = tmp_path / "backup.db"
    create_sqlite_backup(database_url, backup_path)
    manifest_path = manifest_path_for(backup_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backup"]["camera_count"] = 999
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(DatabaseBackupError, match="integrity manifest"):
        verify_sqlite_backup(backup_path)


@pytest.mark.parametrize("created_at", ["not-a-date", "2026-08-18T12:00:00"])
def test_manifest_requires_timezone_aware_creation_time(
    tmp_path: Path,
    monkeypatch,
    seed_file: Path,
    created_at: str,
) -> None:
    database_url, _ = _migrated_database(tmp_path, monkeypatch)
    _import_seed(database_url, seed_file)
    backup_path = tmp_path / "backup.db"
    create_sqlite_backup(database_url, backup_path)
    manifest_path = manifest_path_for(backup_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["created_at"] = created_at
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(DatabaseBackupError, match="creation time is invalid"):
        verify_sqlite_backup(backup_path)


def test_backup_rejects_incomplete_current_revision_schema(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _, database_path = _migrated_database(tmp_path, monkeypatch)
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("ALTER TABLE audit_events DROP COLUMN reason")
        connection.commit()

    with pytest.raises(DatabaseBackupError, match="schema is incomplete"):
        inspect_database_file(database_path)


def test_backup_refuses_existing_outputs_without_modifying_them(
    tmp_path: Path,
    monkeypatch,
    seed_file: Path,
) -> None:
    database_url, _ = _migrated_database(tmp_path, monkeypatch)
    _import_seed(database_url, seed_file)
    backup_path = tmp_path / "existing.db"
    backup_path.write_text("preserve", encoding="utf-8")

    with pytest.raises(DatabaseBackupError, match="output already exists"):
        create_sqlite_backup(database_url, backup_path)

    assert backup_path.read_text(encoding="utf-8") == "preserve"


def test_restore_refuses_active_or_existing_destination(
    tmp_path: Path,
    monkeypatch,
    seed_file: Path,
) -> None:
    database_url, source_path = _migrated_database(tmp_path, monkeypatch)
    _import_seed(database_url, seed_file)
    backup_path = tmp_path / "backup.db"
    create_sqlite_backup(database_url, backup_path)

    with pytest.raises(DatabaseBackupError, match="active database"):
        restore_sqlite_backup(
            backup_path,
            source_path,
            active_database_url=database_url,
        )

    existing = tmp_path / "existing.db"
    existing.write_text("preserve", encoding="utf-8")
    with pytest.raises(DatabaseBackupError, match="output already exists"):
        restore_sqlite_backup(
            backup_path,
            existing,
            active_database_url=database_url,
        )
    assert existing.read_text(encoding="utf-8") == "preserve"


def test_backup_rejects_unsupported_or_stale_databases(tmp_path: Path) -> None:
    with pytest.raises(DatabaseBackupError, match="URL is invalid"):
        sqlite_database_path("not a database url://[")
    with pytest.raises(DatabaseBackupError, match="SQLite databases only"):
        sqlite_database_path("postgresql+psycopg://localhost/hcam")
    with pytest.raises(DatabaseBackupError, match="file-backed"):
        sqlite_database_path("sqlite:///:memory:")
    with pytest.raises(DatabaseBackupError, match="URI-mode"):
        sqlite_database_path("sqlite:///file:phase1.db?uri=true")
    with pytest.raises(DatabaseBackupError, match="does not exist"):
        inspect_database_file(tmp_path / "missing.db")

    stale_path = tmp_path / "stale.db"
    with closing(sqlite3.connect(stale_path)) as connection:
        connection.execute("CREATE TABLE cameras (camera_id TEXT PRIMARY KEY)")
        connection.commit()
    with pytest.raises(DatabaseBackupError, match="schema is incomplete"):
        inspect_database_file(stale_path)


def test_backup_rejects_stale_revision_and_source_destination_collision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_url, database_path = _migrated_database(tmp_path, monkeypatch)
    with pytest.raises(DatabaseBackupError, match="must differ"):
        create_sqlite_backup(database_url, database_path)

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            "UPDATE alembic_version SET version_num = '0002_camera_version'"
        )
        connection.commit()
    with pytest.raises(DatabaseBackupError, match="revision is not current"):
        inspect_database_file(database_path)


def test_backup_rejects_existing_manifest_and_preserves_it(
    tmp_path: Path,
    monkeypatch,
    seed_file: Path,
) -> None:
    database_url, _ = _migrated_database(tmp_path, monkeypatch)
    _import_seed(database_url, seed_file)
    backup_path = tmp_path / "reserved.db"
    manifest_path = manifest_path_for(backup_path)
    manifest_path.write_text("preserve", encoding="utf-8")

    with pytest.raises(DatabaseBackupError, match="output already exists"):
        create_sqlite_backup(database_url, backup_path)

    assert not backup_path.exists()
    assert manifest_path.read_text(encoding="utf-8") == "preserve"


@pytest.mark.parametrize(
    ("manifest", "message"),
    [
        ("not-json", "could not be read"),
        (json.dumps({"format": "wrong", "backup": {}}), "format is invalid"),
    ],
)
def test_verify_rejects_invalid_manifest(
    tmp_path: Path,
    manifest: str,
    message: str,
) -> None:
    backup_path = tmp_path / "backup.db"
    backup_path.write_bytes(b"not-used-before-manifest-validation")
    manifest_path_for(backup_path).write_text(manifest, encoding="utf-8")

    with pytest.raises(DatabaseBackupError, match=message):
        verify_sqlite_backup(backup_path)


def test_verify_requires_manifest(tmp_path: Path) -> None:
    backup_path = tmp_path / "backup.db"
    backup_path.write_bytes(b"placeholder")

    with pytest.raises(DatabaseBackupError, match="manifest does not exist"):
        verify_sqlite_backup(backup_path)


def test_restore_rejects_backup_as_destination(
    tmp_path: Path,
    monkeypatch,
    seed_file: Path,
) -> None:
    database_url, _ = _migrated_database(tmp_path, monkeypatch)
    _import_seed(database_url, seed_file)
    backup_path = tmp_path / "backup.db"
    create_sqlite_backup(database_url, backup_path)

    with pytest.raises(DatabaseBackupError, match="differ from the backup"):
        restore_sqlite_backup(
            backup_path,
            backup_path,
            active_database_url=database_url,
        )


def test_backup_reports_uncreatable_output_parent(
    tmp_path: Path,
    monkeypatch,
    seed_file: Path,
) -> None:
    database_url, _ = _migrated_database(tmp_path, monkeypatch)
    _import_seed(database_url, seed_file)
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("preserve", encoding="utf-8")

    with pytest.raises(DatabaseBackupError, match="output cannot be created"):
        create_sqlite_backup(database_url, parent_file / "backup.db")
