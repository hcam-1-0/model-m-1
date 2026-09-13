from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

from tools.phase52 import verify_p52
from tools.phase53 import verify_p53


ACCEPTED_PACKAGE_SHA256 = (
    "6C58CFA4AB5076A28A1E6E43D8E9AD670D74C9398678402F11E5E7BF16E8B024"
)
ACCEPTED_COMMIT = "eb08c3758733676d72678535d27c8512e75f9407"
P53_ADDITIVE_PACKAGES = {
    "camera-live-domain",
    "media-adapters",
    "media-edge-contracts",
}
P54_ADDITIVE_PACKAGES = {
    "intelligence-contracts",
    "intelligence-domain",
    "intelligence-fixtures",
    "relationship-renderers",
    "review-workflows",
}
P55_ADDITIVE_PACKAGES = {
    "evidence-domain",
    "investigation-contracts",
    "investigation-domain",
    "investigation-fixtures",
}
P56_ADDITIVE_PACKAGES = {
    "admin-contracts",
    "admin-security-operations-fixtures",
    "governance-domain",
    "operations-contracts",
    "platform-operations-domain",
    "security-contracts",
}
P57_ADDITIVE_PACKAGES = {
    "quality-contracts",
    "quality-domain",
    "quality-fixtures",
    "quality-harness",
}
P55_AUTHORIZED_SHARED_EXTENSIONS = {
    "frontend/packages/command-domain/src/projections.ts",
}
P52_IMMUTABLE_PREFIXES = (
    "contracts/phase-5/p5-2-",
    "contracts/phase-5/p5-2/",
    "docs/phase-5/p5-2/",
    "fixtures/phase-5/p5-2/",
    "frontend/apps/command-center/",
    "frontend/apps/gis-center/",
    "frontend/evidence/p5-2-",
    "frontend/packages/command-domain/",
    "frontend/packages/gis-contracts/",
    "frontend/packages/gis-domain/",
    "frontend/packages/gis-renderers/",
    "tools/phase52/",
)


def _accepted_context() -> tuple[str, dict[str, object]]:
    acceptance = verify_p52.read_json(
        verify_p52.ROOT / "contracts/phase-5/p5-2-acceptance.json"
    )
    assert acceptance["effective"] is True
    package_path = verify_p52.ROOT / str(acceptance["evidence_package"]["path"])
    assert verify_p52.sha256(package_path) == ACCEPTED_PACKAGE_SHA256
    return ACCEPTED_COMMIT, verify_p52.read_json(package_path)


def _git_objects(commit: str, paths: list[str]) -> dict[str, bytes]:
    process = subprocess.run(
        ["git", "archive", "--format=tar", commit, "--", *paths],
        cwd=verify_p52.ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert process.returncode == 0
    assert process.stderr == b""
    result: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(process.stdout), mode="r:") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            extracted = archive.extractfile(member)
            assert extracted is not None
            result[member.name] = extracted.read()
    return result


def _canonical_text(content: bytes) -> bytes:
    return content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _accepted_paths(commit: str) -> list[str]:
    process = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit],
        cwd=verify_p52.ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert process.returncode == 0
    assert process.stderr == ""
    return [
        path
        for path in process.stdout.splitlines()
        if path.startswith(P52_IMMUTABLE_PREFIXES)
    ]


def test_phase52_accepted_package_components_remain_exact() -> None:
    _, package = _accepted_context()
    components = package["components"]
    assert isinstance(components, list)
    assert len(components) == 137
    rendered = "\n".join(
        f"{item['path']}|{item['bytes']}|{item['sha256']}"
        for item in sorted(components, key=lambda value: str(value["path"]))
    )
    assert (
        hashlib.sha256(rendered.encode()).hexdigest().upper()
        == package["canonical_component_digest"]
    )


def test_phase52_dedicated_artifacts_remain_byte_exact() -> None:
    acceptance_commit, package = _accepted_context()
    paths = _accepted_paths(acceptance_commit)
    accepted = _git_objects(acceptance_commit, paths)
    package_path = "contracts/phase-5/p5-2-evidence-package.json"
    process = subprocess.run(
        ["git", "show", f"{acceptance_commit}:{package_path}"],
        cwd=verify_p52.ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert len(paths) >= 100
    assert set(accepted) == set(paths)
    assert process.returncode == 0
    assert process.stderr == b""
    assert hashlib.sha256(process.stdout).hexdigest().upper() == ACCEPTED_PACKAGE_SHA256
    component_paths = {
        str(item["path"])
        for item in package["components"]
        if isinstance(item, dict) and "path" in item
    }
    assert P55_AUTHORIZED_SHARED_EXTENSIONS <= component_paths
    for path in paths:
        if path in P55_AUTHORIZED_SHARED_EXTENSIONS:
            continue
        current = (verify_p52.ROOT / path).read_bytes()
        assert _canonical_text(current) == _canonical_text(accepted[path])


def test_phase52_topology_is_exact_at_acceptance_and_additive_now() -> None:
    seal_commit, _ = _accepted_context()
    for group, expected in (
        ("apps", verify_p52.EXPECTED_APPS),
        ("packages", verify_p52.EXPECTED_PACKAGES),
    ):
        process = subprocess.run(
            ["git", "ls-tree", "--name-only", f"{seal_commit}:frontend/{group}"],
            cwd=verify_p52.ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert process.returncode == 0
        assert process.stderr == ""
        assert set(process.stdout.splitlines()) == expected
    assert verify_p52._workspace_names("apps") == verify_p52.EXPECTED_APPS
    assert verify_p52._workspace_names("packages") == (
        verify_p52.EXPECTED_PACKAGES
        | P53_ADDITIVE_PACKAGES
        | P54_ADDITIVE_PACKAGES
        | P55_ADDITIVE_PACKAGES
        | P56_ADDITIVE_PACKAGES
        | P57_ADDITIVE_PACKAGES
    )


def test_phase52_behavior_and_current_generated_boundaries_pass() -> None:
    assert verify_p52._routes_and_shared_domain_pass()
    assert verify_p52._generated_fixtures_pass()
    assert verify_p52._producer_and_renderer_boundaries_pass()
    assert verify_p52._generated_outputs_untracked()
    result = verify_p53.verify(verify_p52.ROOT)
    assert result["status"] == "pass", json.dumps(result, indent=2)


def test_current_phase53_cli_emits_bounded_json() -> None:
    process = subprocess.run(
        [sys.executable, str(Path(verify_p53.__file__))],
        cwd=verify_p52.ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    payload = json.loads(process.stdout)
    assert process.returncode == 0
    assert process.stderr == ""
    assert payload["status"] == "pass"
    assert payload["failures"] == []
