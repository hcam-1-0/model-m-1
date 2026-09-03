from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from collections.abc import Sequence
from pathlib import Path

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
from hcam.streams.network import StreamNetworkPolicy
from hcam.streams.lab import SyntheticLabError, seed_synthetic_lab
from hcam.streams.outbox import (
    LoggingStreamEventSink,
    StreamEventDeliveryError,
    StreamEventOutboxDispatcher,
)
from hcam.streams.probe import FfprobeRunner, ProbeToolError, StreamProbeAdapter
from hcam.streams.worker import StreamHealthWorker
from hcam.streams.capabilities import build_capability_discovery_engine
from hcam.streams.capability_worker import (
    CapabilityRefreshWorker,
    CapabilityWorkerRuntimeError,
)


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
    worker_parser = subparsers.add_parser(
        "stream-worker",
        help="Run the metadata-only stream health worker",
    )
    worker_parser.add_argument(
        "--once",
        action="store_true",
        help="Probe at most one due stream and exit",
    )
    worker_parser.add_argument("--poll-seconds", type=float, default=2.0)
    worker_parser.add_argument("--worker-id")
    capability_worker_parser = subparsers.add_parser(
        "capability-worker",
        help="Run the read-only ONVIF capability refresh worker",
    )
    capability_worker_parser.add_argument("--once", action="store_true")
    capability_worker_parser.add_argument("--poll-seconds", type=float, default=2.0)
    capability_worker_parser.add_argument("--worker-id")
    dispatcher_parser = subparsers.add_parser(
        "stream-event-dispatcher",
        help="Deliver transactional stream events to the configured sink",
    )
    dispatcher_parser.add_argument("--once", action="store_true")
    dispatcher_parser.add_argument("--poll-seconds", type=float, default=2.0)
    lab_parser = subparsers.add_parser(
        "seed-phase2-lab",
        help="Seed the explicitly enabled synthetic-only Phase 2 lab",
    )
    lab_parser.add_argument("--count", type=int, default=50)
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
        elif args.command == "stream-worker":
            if args.poll_seconds <= 0:
                raise ValueError("--poll-seconds must be positive")
            database = Database(settings.database_url)
            worker_id = args.worker_id or f"{socket.gethostname()}:{os.getpid()}"
            worker = StreamHealthWorker(
                database.session_factory,
                StreamProbeAdapter(
                    runner=FfprobeRunner(
                        executable=settings.ffprobe_executable,
                        timeout_seconds=settings.stream_probe_timeout_seconds,
                    ),
                    network_policy=StreamNetworkPolicy(
                        settings.stream_probe_allowed_hosts
                    ),
                    access_token=settings.stream_probe_token,
                ),
                worker_id=worker_id,
            )
            try:
                database.check_ready()
                if args.once:
                    output = {"processed": worker.run_once(), "worker_id": worker_id}
                else:
                    heartbeat = os.getenv("HCAM_STREAM_WORKER_HEARTBEAT_FILE")
                    worker.run(
                        poll_seconds=args.poll_seconds,
                        heartbeat_file=Path(heartbeat) if heartbeat else None,
                    )
                    return 0
            finally:
                database.dispose()
        elif args.command == "seed-phase2-lab":
            if settings.environment not in {"development", "test"}:
                raise SyntheticLabError("synthetic lab seeding is forbidden in production")
            if os.getenv("HCAM_ALLOW_SYNTHETIC_LAB", "").lower() not in {
                "1",
                "true",
            }:
                raise SyntheticLabError("HCAM_ALLOW_SYNTHETIC_LAB=true is required")
            database = Database(settings.database_url)
            try:
                database.check_ready()
                with database.session_factory() as session:
                    output = seed_synthetic_lab(session, count=args.count)
            finally:
                database.dispose()
        elif args.command == "capability-worker":
            if args.poll_seconds <= 0:
                raise ValueError("--poll-seconds must be positive")
            database = Database(settings.database_url)
            worker_id = args.worker_id or f"{socket.gethostname()}:{os.getpid()}"
            worker = CapabilityRefreshWorker(
                database.session_factory,
                build_capability_discovery_engine(settings),
                worker_id=worker_id,
            )
            try:
                database.check_ready()
                if args.once:
                    output = {"processed": worker.run_once(), "worker_id": worker_id}
                else:
                    heartbeat = os.getenv("HCAM_CAPABILITY_WORKER_HEARTBEAT_FILE")
                    worker.run(
                        poll_seconds=args.poll_seconds,
                        heartbeat_file=Path(heartbeat) if heartbeat else None,
                    )
                    return 0
            finally:
                database.dispose()
        elif args.command == "stream-event-dispatcher":
            if args.poll_seconds <= 0:
                raise ValueError("--poll-seconds must be positive")
            database = Database(settings.database_url)
            dispatcher = StreamEventOutboxDispatcher(
                database.session_factory,
                LoggingStreamEventSink(),
            )
            try:
                database.check_ready()
                if args.once:
                    output = {"processed": dispatcher.run_once()}
                else:
                    heartbeat = os.getenv("HCAM_STREAM_DISPATCHER_HEARTBEAT_FILE")
                    dispatcher.run(
                        poll_seconds=args.poll_seconds,
                        heartbeat_file=Path(heartbeat) if heartbeat else None,
                    )
                    return 0
            finally:
                database.dispose()
        else:
            return 2
        print(json.dumps(output, indent=2, sort_keys=True))
        return exit_code
    except (
        RegistryImportError,
        DatabaseBackupError,
        ProbeToolError,
        StreamEventDeliveryError,
        CapabilityWorkerRuntimeError,
        SyntheticLabError,
        ValueError,
    ) as exc:
        operation = (
            "registry import" if args.command == "import-registry" else args.command
        )
        print(f"{operation} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
