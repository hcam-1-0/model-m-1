from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from hcam.database import Database
from hcam.operations.database_backup import (
    DatabaseBackupError,
    create_sqlite_backup,
    restore_sqlite_backup,
    verify_sqlite_backup,
)


RECOVERY_DRILL_FORMAT = "hcam.phase1.recovery-drill.v1"


@dataclass(frozen=True, slots=True)
class RecoveryObjective:
    measured_seconds: float
    maximum_seconds: float
    met: bool


@dataclass(frozen=True, slots=True)
class RecoveryDrillReport:
    started_at: str
    completed_at: str
    passed: bool
    schema_revision: str
    camera_count: int
    audit_event_count: int
    backup_sha256: str
    recovery_objective: RecoveryObjective

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": RECOVERY_DRILL_FORMAT,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "passed": self.passed,
            "scope": {
                "database": "sqlite",
                "metadata_only": True,
                "video_used": False,
            },
            "snapshot": {
                "schema_revision": self.schema_revision,
                "camera_count": self.camera_count,
                "audit_event_count": self.audit_event_count,
                "backup_sha256": self.backup_sha256,
            },
            "recovery_objective": asdict(self.recovery_objective),
            "artifacts": [
                "backup.db",
                "backup.db.manifest.json",
                "restored.db",
                "report.json",
            ],
        }


def _create_private_directory(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.mkdir(mode=0o700)
        path.chmod(0o700)
    except FileExistsError as exc:
        raise DatabaseBackupError(
            "recovery drill destination already exists"
        ) from exc
    except OSError as exc:
        raise DatabaseBackupError(
            "recovery drill destination could not be created"
        ) from exc


def _write_private_report(path: Path, report: RecoveryDrillReport) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = None
            json.dump(report.to_dict(), handle, indent=2, sort_keys=True)
            handle.write("\n")
        path.chmod(0o600)
    except FileExistsError as exc:
        raise DatabaseBackupError("recovery drill report already exists") from exc
    except OSError as exc:
        path.unlink(missing_ok=True)
        raise DatabaseBackupError("recovery drill report could not be written") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def run_sqlite_recovery_drill(
    database_url: str,
    destination: str | Path,
    *,
    max_recovery_seconds: float = 60.0,
) -> RecoveryDrillReport:
    if not math.isfinite(max_recovery_seconds) or max_recovery_seconds <= 0:
        raise DatabaseBackupError("recovery objective must be positive")

    destination_path = Path(destination).expanduser().resolve()
    _create_private_directory(destination_path)
    backup_path = destination_path / "backup.db"
    restored_path = destination_path / "restored.db"
    started_at = datetime.now(UTC)
    started = perf_counter()

    created = create_sqlite_backup(database_url, backup_path)
    verified = verify_sqlite_backup(backup_path)
    restored = restore_sqlite_backup(
        backup_path,
        restored_path,
        active_database_url=database_url,
    )
    restored_database = Database(f"sqlite:///{restored_path.as_posix()}")
    try:
        restored_database.check_ready()
    finally:
        restored_database.dispose()

    if (
        created.backup.sha256 != verified.backup.sha256
        or restored.restored.camera_count != verified.backup.camera_count
        or restored.restored.audit_event_count != verified.backup.audit_event_count
    ):
        raise DatabaseBackupError("recovery drill consistency verification failed")

    elapsed = perf_counter() - started
    completed_at = datetime.now(UTC)
    objective = RecoveryObjective(
        measured_seconds=round(elapsed, 3),
        maximum_seconds=max_recovery_seconds,
        met=elapsed <= max_recovery_seconds,
    )
    report = RecoveryDrillReport(
        started_at=started_at.isoformat(),
        completed_at=completed_at.isoformat(),
        passed=objective.met,
        schema_revision=verified.backup.schema_revision,
        camera_count=verified.backup.camera_count,
        audit_event_count=verified.backup.audit_event_count,
        backup_sha256=verified.backup.sha256,
        recovery_objective=objective,
    )
    _write_private_report(destination_path / "report.json", report)
    return report
