#!/usr/bin/env python3
"""Generate and verify deterministic H-CAM API and database contracts."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from hcam.main import create_app
from hcam.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "phase-2"
OPENAPI_SNAPSHOT = CONTRACT_ROOT / "openapi.json"
DATABASE_SNAPSHOT = CONTRACT_ROOT / "database.json"
_MAX_DIFF_LINES = 240


def _normalized_text(value: object) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", str(value)).strip()


def _sorted_records(
    records: list[dict[str, Any]], *keys: str
) -> list[dict[str, Any]]:
    return sorted(
        records,
        key=lambda item: tuple(str(item.get(key) or "") for key in keys),
    )


def render_openapi_contract() -> dict[str, object]:
    application = create_app(
        Settings(
            database_url="sqlite:///:memory:",
            create_schema=False,
            dev_auth_enabled=True,
            environment="test",
            access_log_enabled=False,
        )
    )
    try:
        schema = application.openapi()
    finally:
        application.state.database.dispose()
    return {
        "contract_format": "hcam.openapi.contract.v1",
        "schema": schema,
    }


def _database_table_contract(inspector, table_name: str) -> dict[str, object]:
    columns = [
        {
            "name": column["name"],
            "type": str(column["type"]),
            "nullable": bool(column["nullable"]),
            "default": _normalized_text(column.get("default")),
            "primary_key_position": int(column.get("primary_key") or 0),
        }
        for column in inspector.get_columns(table_name)
    ]
    foreign_keys = [
        {
            "name": item.get("name"),
            "columns": list(item.get("constrained_columns") or ()),
            "referred_schema": item.get("referred_schema"),
            "referred_table": item.get("referred_table"),
            "referred_columns": list(item.get("referred_columns") or ()),
            "ondelete": (item.get("options") or {}).get("ondelete"),
            "onupdate": (item.get("options") or {}).get("onupdate"),
        }
        for item in inspector.get_foreign_keys(table_name)
    ]
    indexes = [
        {
            "name": item.get("name"),
            "columns": list(item.get("column_names") or ()),
            "unique": bool(item.get("unique")),
        }
        for item in inspector.get_indexes(table_name)
    ]
    unique_constraints = [
        {
            "name": item.get("name"),
            "columns": list(item.get("column_names") or ()),
        }
        for item in inspector.get_unique_constraints(table_name)
    ]
    check_constraints = [
        {
            "name": item.get("name"),
            "sql": _normalized_text(item.get("sqltext")),
        }
        for item in inspector.get_check_constraints(table_name)
    ]
    primary_key = inspector.get_pk_constraint(table_name)
    return {
        "name": table_name,
        "columns": columns,
        "primary_key": {
            "name": primary_key.get("name"),
            "columns": list(primary_key.get("constrained_columns") or ()),
        },
        "foreign_keys": _sorted_records(
            foreign_keys, "name", "referred_table", "columns"
        ),
        "indexes": _sorted_records(indexes, "name", "columns"),
        "unique_constraints": _sorted_records(
            unique_constraints, "name", "columns"
        ),
        "check_constraints": _sorted_records(
            check_constraints, "name", "sql"
        ),
    }


def render_database_contract() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="hcam-release-contract-") as temp:
        database_path = (Path(temp) / "contract.db").as_posix()
        database_url = f"sqlite:///{database_path}"
        config = Config(str(ROOT / "alembic.ini"))
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")
        script = ScriptDirectory.from_config(config)
        engine = create_engine(database_url)
        try:
            inspector = inspect(engine)
            tables = [
                _database_table_contract(inspector, table_name)
                for table_name in sorted(inspector.get_table_names())
            ]
        finally:
            engine.dispose()
    return {
        "contract_format": "hcam.database.contract.v1",
        "alembic_heads": sorted(script.get_heads()),
        "dialect": "sqlite",
        "tables": tables,
    }


def render_contracts() -> dict[Path, dict[str, object]]:
    return {
        OPENAPI_SNAPSHOT: render_openapi_contract(),
        DATABASE_SNAPSHOT: render_database_contract(),
    }


def serialized_contract(document: dict[str, object]) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def contract_digest(document: dict[str, object]) -> str:
    return hashlib.sha256(serialized_contract(document).encode("utf-8")).hexdigest()


def contract_diff(path: Path, expected: str, actual: str) -> list[str]:
    lines = list(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile=f"tracked/{path.name}",
            tofile=f"current/{path.name}",
            lineterm="",
        )
    )
    if len(lines) > _MAX_DIFF_LINES:
        omitted = len(lines) - _MAX_DIFF_LINES
        return [*lines[:_MAX_DIFF_LINES], f"... {omitted} diff lines omitted"]
    return lines


def check_contracts() -> int:
    failures = 0
    for path, document in render_contracts().items():
        actual = serialized_contract(document)
        try:
            expected = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[fail] {path.relative_to(ROOT)}: {exc}")
            failures += 1
            continue
        if expected != actual:
            print(f"[fail] {path.relative_to(ROOT)} drifted")
            for line in contract_diff(path, expected, actual):
                print(line)
            failures += 1
            continue
        print(
            f"[pass] {path.relative_to(ROOT)} "
            f"sha256={contract_digest(document)}"
        )
    return 1 if failures else 0


def write_contracts(*, acknowledged: bool) -> int:
    if not acknowledged:
        print(
            "Refusing to rewrite release contracts without "
            "--acknowledge-reviewed-change"
        )
        return 2
    CONTRACT_ROOT.mkdir(parents=True, exist_ok=True)
    for path, document in render_contracts().items():
        path.write_text(serialized_contract(document), encoding="utf-8", newline="\n")
        print(
            f"[write] {path.relative_to(ROOT)} "
            f"sha256={contract_digest(document)}"
        )
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify reviewed H-CAM OpenAPI and database contracts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="Fail when current contracts drift")
    write = subparsers.add_parser(
        "write", help="Rewrite snapshots after explicit contract review"
    )
    write.add_argument("--acknowledge-reviewed-change", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "check":
        return check_contracts()
    return write_contracts(acknowledged=args.acknowledge_reviewed_change)


if __name__ == "__main__":
    raise SystemExit(main())
