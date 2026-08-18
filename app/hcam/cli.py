from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from hcam.camera_registry.importer import RegistryImportError, RegistryImporter
from hcam.database import Database
from hcam.operations.database_backup import (
    DatabaseBackupError,
    create_sqlite_backup,
    restore_sqlite_backup,
    verify_sqlite_backup,
)
from hcam.operations.recovery_drill import run_sqlite_recovery_drill
from hcam.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="H-CAM backend utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    import_parser = subparsers.add_parser(
        "import-registry", help="Import a local hcam.camera_registry.seed.v1 file"
    )
    import_parser.add_argument("seed_file")
    backup_parser = subparsers.add_parser(
        "backup-database",
        help="Create a verified online backup of the configured SQLite database",
    )
    backup_parser.add_argument("destination")
    verify_parser = subparsers.add_parser(
        "verify-backup",
        help="Verify a SQLite backup against its integrity manifest",
    )
    verify_parser.add_argument("backup_file")
    restore_parser = subparsers.add_parser(
        "restore-backup",
        help="Restore a verified SQLite backup into a new database file",
    )
    restore_parser.add_argument("backup_file")
    restore_parser.add_argument("destination")
    drill_parser = subparsers.add_parser(
        "recovery-drill",
        help="Run a measured backup, restore, and readiness drill for SQLite",
    )
    drill_parser.add_argument("destination")
    drill_parser.add_argument(
        "--max-recovery-seconds",
        type=float,
        default=60.0,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_environment()
    exit_code = 0
    try:
        if args.command == "import-registry":
            database = Database(settings.database_url)
            try:
                result = RegistryImporter(database.session_factory).import_file(
                    args.seed_file
                )
            finally:
                database.dispose()
            output = result.model_dump(mode="json")
        elif args.command == "backup-database":
            output = create_sqlite_backup(
                settings.database_url,
                args.destination,
            ).to_dict()
        elif args.command == "verify-backup":
            output = verify_sqlite_backup(args.backup_file).to_dict()
        elif args.command == "restore-backup":
            output = restore_sqlite_backup(
                args.backup_file,
                args.destination,
                active_database_url=settings.database_url,
            ).to_dict()
        elif args.command == "recovery-drill":
            report = run_sqlite_recovery_drill(
                settings.database_url,
                args.destination,
                max_recovery_seconds=args.max_recovery_seconds,
            )
            output = report.to_dict()
            exit_code = 0 if report.passed else 1
        else:
            return 2
        print(json.dumps(output, indent=2, sort_keys=True))
        return exit_code
    except (RegistryImportError, DatabaseBackupError) as exc:
        operation = (
            "registry import" if args.command == "import-registry" else args.command
        )
        print(f"{operation} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
