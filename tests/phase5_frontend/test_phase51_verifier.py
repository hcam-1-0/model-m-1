from __future__ import annotations

import hashlib
import subprocess

from tools.phase51 import verify_p51


ACCEPTED_PACKAGE_SHA256 = "74953D5E9239A17E8A4173B72CF7A485BC4B7FDBC0503A31787F2EFE9C1767BC"


def _accepted_context() -> tuple[str, dict[str, object]]:
    acceptance = verify_p51.read_json(verify_p51.ROOT / "contracts/phase-5/p5-1-acceptance.json")
    assert acceptance["effective"] is True
    seal_commit = str(acceptance["accepted_evidence_seal_commit"])
    package_path = verify_p51.ROOT / str(acceptance["evidence_package"]["path"])
    assert verify_p51.sha256(package_path) == ACCEPTED_PACKAGE_SHA256
    return seal_commit, verify_p51.read_json(package_path)


def _git_object(commit: str, path: str) -> bytes:
    process = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=verify_p51.ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert process.returncode == 0
    assert process.stderr == b""
    return process.stdout


def test_phase51_accepted_commit_components_remain_exact() -> None:
    seal_commit, package = _accepted_context()
    components = package["components"]
    assert isinstance(components, list)
    assert len(components) == 133
    for item in components:
        assert isinstance(item, dict)
        content = _git_object(seal_commit, str(item["path"]))
        assert len(content) == item["bytes"]
        assert hashlib.sha256(content).hexdigest().upper() == item["sha256"]


def test_phase51_contract_and_toolchain_packages_remain_exact() -> None:
    assert verify_p51.sha256(verify_p51.START_PACKAGE) == verify_p51.EXPECTED_START_SHA256
    assert verify_p51.sha256(verify_p51.TOOLCHAIN_PACKAGE) == verify_p51.EXPECTED_TOOLCHAIN_SHA256


def test_phase51_workspace_topology_is_exact_at_accepted_commit() -> None:
    seal_commit, _ = _accepted_context()
    for group, expected in (
        ("apps", verify_p51.EXPECTED_APPS),
        ("packages", verify_p51.EXPECTED_PACKAGES),
    ):
        process = subprocess.run(
            ["git", "ls-tree", "--name-only", f"{seal_commit}:frontend/{group}"],
            cwd=verify_p51.ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert process.returncode == 0
        assert process.stderr == ""
        assert set(process.stdout.splitlines()) == expected


def test_phase51_acceptance_canonical_component_digest_remains_exact() -> None:
    _, package = _accepted_context()
    components = package["components"]
    assert isinstance(components, list)
    rendered = "\n".join(
        f"{item['path']}|{item['bytes']}|{item['sha256']}"
        for item in sorted(components, key=lambda value: value["path"])
    )
    assert (
        hashlib.sha256(rendered.encode("utf-8")).hexdigest().upper()
        == package["canonical_component_digest"]
    )


def test_phase51_operational_runtime_boundaries_remain_closed() -> None:
    assert verify_p51._network_and_import_boundaries_pass()
    assert verify_p51._source_adoption_is_reference_only()
    assert verify_p51._fixtures_are_safe()
    assert verify_p51._generated_outputs_untracked()
