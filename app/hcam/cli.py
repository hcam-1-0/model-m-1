from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from hcam.camera_registry.importer import RegistryImportError, RegistryImporter
from hcam.database import Database
from hcam.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="H-CAM backend utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    import_parser = subparsers.add_parser(
        "import-registry", help="Import a local hcam.camera_registry.seed.v1 file"
    )
    import_parser.add_argument("seed_file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_environment()
    database = Database(settings.database_url)
    try:
        if args.command == "import-registry":
            result = RegistryImporter(database.session_factory).import_file(args.seed_file)
            print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))
            return 0
    except RegistryImportError as exc:
        print(f"registry import failed: {exc}", file=sys.stderr)
        return 1
    finally:
        database.dispose()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
