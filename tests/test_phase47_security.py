import ast
from pathlib import Path

import pytest

from hcam.acceptance.bounds import (
    GeneratedBoundaryError,
    bounded_text,
    validate_generated_document,
)
from hcam.acceptance.scenarios import GeneratedScenarioRuntime, ScenarioRuntimeError
from tools.phase47_readiness import PROHIBITED_IMPORTS


ROOT = Path(__file__).resolve().parents[1]


def test_acceptance_sources_do_not_import_prohibited_runtimes() -> None:
    found: set[str] = set()
    for path in (ROOT / "app/hcam/acceptance").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(item.name.partition(".")[0] for item in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module.partition(".")[0])
    assert not (found & PROHIBITED_IMPORTS)


def test_generated_boundary_rejects_secrets_locators_depth_and_types() -> None:
    for value in (
        {"password": "generated"},
        {"value": "https://example.invalid"},
        {"value": object()},
    ):
        with pytest.raises(GeneratedBoundaryError):
            validate_generated_document(value)
    value: object = "end"
    for _ in range(18):
        value = {"level": value}
    with pytest.raises(GeneratedBoundaryError):
        validate_generated_document(value)


def test_generated_boundary_enforces_text_key_and_collection_bounds() -> None:
    for value in (" generated", "x" * 4_097):
        with pytest.raises(GeneratedBoundaryError):
            bounded_text(value)
    with pytest.raises(GeneratedBoundaryError):
        validate_generated_document({1: "value"})
    with pytest.raises(GeneratedBoundaryError):
        validate_generated_document({str(index): index for index in range(10_001)})
    with pytest.raises(GeneratedBoundaryError):
        validate_generated_document(list(range(10_001)))


def test_runtime_boundary_is_default_off_and_production_forbidden() -> None:
    with pytest.raises(ScenarioRuntimeError):
        GeneratedScenarioRuntime().require_enabled()
    with pytest.raises(ScenarioRuntimeError):
        GeneratedScenarioRuntime(enabled=True, environment="prod").require_enabled()
