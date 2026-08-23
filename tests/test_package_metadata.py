from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

from hcam import __version__
from hcam.main import create_app


def test_distribution_and_api_versions_match_package() -> None:
    assert version("hcam-core") == __version__
    assert create_app().version == __version__


def test_source_manifest_includes_yaml_and_yml_deployment_contracts() -> None:
    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")
    deploy_rule = next(
        line
        for line in manifest.splitlines()
        if line.startswith("recursive-include deploy")
    )
    assert "*.yaml" in deploy_rule
    assert "*.yml" in deploy_rule
    contract_rule = next(
        line
        for line in manifest.splitlines()
        if line.startswith("recursive-include contracts")
    )
    assert "*.json" in contract_rule
    assert "*.md" in contract_rule


def test_source_manifest_includes_governance_assets_used_by_tests() -> None:
    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")
    assert "include uv.lock" in manifest.splitlines()
    github_rule = next(
        line
        for line in manifest.splitlines()
        if line.startswith("recursive-include .github")
    )

    assert "*.md" in github_rule
    assert "*.yaml" in github_rule
    assert "*.yml" in github_rule

    tests_rule = next(
        line
        for line in manifest.splitlines()
        if line.startswith("recursive-include tests")
    )
    assert "*.py" in tests_rule
    assert "*.json" in tests_rule

    fixture_rule = next(
        line
        for line in manifest.splitlines()
        if line.startswith("recursive-include fixtures")
    )
    assert "*.md" in fixture_rule
    assert ".gitignore" in fixture_rule
