from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.engine import make_url

from hcam.database import (
    CURRENT_SCHEMA_REVISION,
    REQUIRED_AUDIT_COLUMNS,
    REQUIRED_CAMERA_COLUMNS,
)


BACKUP_FORMAT = "hcam.sqlite-backup.v1"


class DatabaseBackupError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DatabaseFileReport:
    path: str
    schema_revision: str
    camera_count: int
    audit_event_count: int
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BackupReport:
    backup: DatabaseFileReport
    manifest_path: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "format": BACKUP_FORMAT,
            "created_at": self.created_at,
            "manifest_path": self.manifest_path,
            "backup": self.backup.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class RestoreReport:
    backup_path: str
    restored: DatabaseFileReport

    def to_dict(self) -> dict[str, object]:
        return {
            "format": BACKUP_FORMAT,
            "backup_path": self.backup_path,
            "restored": self.restored.to_dict(),
        }


def sqlite_database_path(database_url: str) -> Path:
    try:
        url = make_url(database_url)
    except Exception as exc:
        raise DatabaseBackupError("database URL is invalid") from exc
    if url.get_backend_name() != "sqlite":
        raise DatabaseBackupError("backup commands support SQLite databases only")
    if not url.database or url.database == ":memory:":
        raise DatabaseBackupError("backup commands require a file-backed SQLite database")
    if url.query.get("uri", "false").lower() == "true":
        raise DatabaseBackupError("SQLite URI-mode databases are not supported for backup")
    return Path(url.database).expanduser().resolve()


def manifest_path_for(backup_path: Path) -> Path:
    return backup_path.with_name(f"{backup_path.name}.manifest.json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_only_connection(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise DatabaseBackupError(f"SQLite database file does not exist: {path}")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        connection.execute("PRAGMA query_only=ON")
        return connection
    except sqlite3.Error as exc:
        if connection is not None:
            connection.close()
        raise DatabaseBackupError("SQLite database could not be opened read-only") from exc


def inspect_database_file(path: str | Path) -> DatabaseFileReport:
    resolved = Path(path).expanduser().resolve()
    try:
        with closing(_read_only_connection(resolved)) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchall()
            if integrity != [("ok",)]:
                raise DatabaseBackupError("SQLite integrity check failed")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise DatabaseBackupError("SQLite foreign-key check failed")
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            if not {"alembic_version", "cameras", "audit_events"}.issubset(tables):
                raise DatabaseBackupError("database schema is incomplete")
            camera_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(cameras)")
            }
            audit_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(audit_events)")
            }
            if not REQUIRED_CAMERA_COLUMNS.issubset(
                camera_columns
            ) or not REQUIRED_AUDIT_COLUMNS.issubset(audit_columns):
                raise DatabaseBackupError("database schema is incomplete")
            revision_row = connection.execute(
                "SELECT version_num FROM alembic_version"
            ).fetchone()
            if revision_row is None or revision_row[0] != CURRENT_SCHEMA_REVISION:
                raise DatabaseBackupError("database migration revision is not current")
            camera_count = int(
                connection.execute("SELECT COUNT(*) FROM cameras").fetchone()[0]
            )
            audit_event_count = int(
                connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
            )
    except DatabaseBackupError:
        raise
    except sqlite3.Error as exc:
        raise DatabaseBackupError("database schema could not be verified") from exc

    return DatabaseFileReport(
        path=str(resolved),
        schema_revision=CURRENT_SCHEMA_REVISION,
        camera_count=camera_count,
        audit_event_count=audit_event_count,
        size_bytes=resolved.stat().st_size,
        sha256=_sha256(resolved),
    )


def _reserve_output(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DatabaseBackupError(f"output cannot be created: {path}") from exc
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise DatabaseBackupError(f"output already exists: {path}") from exc
    except OSError as exc:
        raise DatabaseBackupError(f"output cannot be created: {path}") from exc
    os.close(descriptor)


def _temporary_path(destination: Path) -> Path:
    return destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")


def _restrict_permissions(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError as exc:
        raise DatabaseBackupError(
            f"output permissions cannot be restricted: {path}"
        ) from exc


def _copy_sqlite_database(source: Path, destination: Path) -> None:
    try:
        with closing(_read_only_connection(source)) as source_connection:
            with closing(sqlite3.connect(destination)) as destination_connection:
                source_connection.backup(destination_connection)
    except DatabaseBackupError:
        raise
    except sqlite3.Error as exc:
        raise DatabaseBackupError("SQLite online backup failed") from exc


def create_sqlite_backup(
    database_url: str,
    destination: str | Path,
) -> BackupReport:
    source = sqlite_database_path(database_url)
    destination_path = Path(destination).expanduser().resolve()
    manifest_path = manifest_path_for(destination_path)
    if source == destination_path:
        raise DatabaseBackupError("backup destination must differ from the source database")

    inspect_database_file(source)
    _reserve_output(destination_path)
    try:
        _reserve_output(manifest_path)
    except BaseException:
        destination_path.unlink(missing_ok=True)
        raise

    temporary_backup = _temporary_path(destination_path)
    temporary_manifest = _temporary_path(manifest_path)
    try:
        _copy_sqlite_database(source, temporary_backup)
        backup_file = inspect_database_file(temporary_backup)
        backup_file = DatabaseFileReport(
            path=str(destination_path),
            schema_revision=backup_file.schema_revision,
            camera_count=backup_file.camera_count,
            audit_event_count=backup_file.audit_event_count,
            size_bytes=backup_file.size_bytes,
            sha256=backup_file.sha256,
        )
        report = BackupReport(
            backup=backup_file,
            manifest_path=str(manifest_path),
            created_at=datetime.now(UTC).isoformat(),
        )
        manifest_payload = report.to_dict()
        manifest_payload["manifest_path"] = manifest_path.name
        manifest_payload["backup"]["path"] = destination_path.name
        temporary_manifest.write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _restrict_permissions(temporary_backup)
        _restrict_permissions(temporary_manifest)
        os.replace(temporary_backup, destination_path)
        os.replace(temporary_manifest, manifest_path)
        return report
    except BaseException:
        destination_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise
    finally:
        temporary_backup.unlink(missing_ok=True)
        temporary_manifest.unlink(missing_ok=True)


def verify_sqlite_backup(backup_path: str | Path) -> BackupReport:
    resolved_backup = Path(backup_path).expanduser().resolve()
    resolved_manifest = manifest_path_for(resolved_backup)
    if not resolved_manifest.is_file():
        raise DatabaseBackupError(f"backup manifest does not exist: {resolved_manifest}")
    try:
        manifest = json.loads(resolved_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatabaseBackupError("backup manifest could not be read") from exc
    if manifest.get("format") != BACKUP_FORMAT or not isinstance(
        manifest.get("backup"), dict
    ):
        raise DatabaseBackupError("backup manifest format is invalid")

    actual = inspect_database_file(resolved_backup)
    expected = manifest["backup"]
    comparisons = {
        "schema_revision": actual.schema_revision,
        "camera_count": actual.camera_count,
        "audit_event_count": actual.audit_event_count,
        "size_bytes": actual.size_bytes,
        "sha256": actual.sha256,
    }
    if any(expected.get(field) != value for field, value in comparisons.items()):
        raise DatabaseBackupError("backup does not match its integrity manifest")
    created_at = manifest.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        raise DatabaseBackupError("backup manifest creation time is invalid")
    try:
        parsed_created_at = datetime.fromisoformat(created_at)
    except ValueError as exc:
        raise DatabaseBackupError("backup manifest creation time is invalid") from exc
    if parsed_created_at.tzinfo is None:
        raise DatabaseBackupError("backup manifest creation time is invalid")
    return BackupReport(
        backup=actual,
        manifest_path=str(resolved_manifest),
        created_at=created_at,
    )


def restore_sqlite_backup(
    backup_path: str | Path,
    destination: str | Path,
    *,
    active_database_url: str,
) -> RestoreReport:
    verified = verify_sqlite_backup(backup_path)
    source = Path(verified.backup.path).resolve()
    destination_path = Path(destination).expanduser().resolve()
    active_path = sqlite_database_path(active_database_url)
    if destination_path == active_path:
        raise DatabaseBackupError(
            "restore destination must not be the configured active database"
        )
    if destination_path == source:
        raise DatabaseBackupError("restore destination must differ from the backup")

    _reserve_output(destination_path)
    temporary_restore = _temporary_path(destination_path)
    try:
        _copy_sqlite_database(source, temporary_restore)
        restored_file = inspect_database_file(temporary_restore)
        if (
            restored_file.camera_count != verified.backup.camera_count
            or restored_file.audit_event_count != verified.backup.audit_event_count
        ):
            raise DatabaseBackupError("restored database record counts do not match")
        _restrict_permissions(temporary_restore)
        os.replace(temporary_restore, destination_path)
        final_report = inspect_database_file(destination_path)
        return RestoreReport(
            backup_path=str(source),
            restored=final_report,
        )
    except BaseException:
        destination_path.unlink(missing_ok=True)
        raise
    finally:
        temporary_restore.unlink(missing_ok=True)
