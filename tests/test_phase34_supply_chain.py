from __future__ import annotations

import hashlib
import json
from pathlib import Path

import tools.phase34_supply_chain as supply_chain
from tools.phase34_supply_chain import (
    CONTAINER_REVIEW,
    DEPENDENCIES,
    SBOM,
    build_dependencies,
    validate_container_review,
    validate_dependencies,
    validate_sbom,
)


ROOT = Path(__file__).resolve().parents[1]


def test_phase34_dependency_record_binds_lock_and_native_runtime() -> None:
    document = build_dependencies()
    recorded = json.loads(DEPENDENCIES.read_text(encoding="utf-8"))
    assert validate_dependencies(document) == []
    assert document == recorded
    assert document["postgis"]["postgis_runtime_version"] == "3.6.4"
    assert document["postgis"]["geos_runtime_version"] == "3.14.1"
    assert document["audit_boundary"]["container_vulnerability_scan_included"] is True


def test_phase34_lock_digest_is_stable_across_windows_line_endings(
    monkeypatch, tmp_path: Path
) -> None:
    lock = tmp_path / "uv.lock"
    source_lock = (ROOT / "uv.lock").read_bytes().replace(b"\r\n", b"\n")
    lock.write_bytes(source_lock.replace(b"\n", b"\r\n"))
    monkeypatch.setattr(supply_chain, "ROOT", tmp_path)

    document = supply_chain.build_dependencies()

    assert document["lockfile"]["sha256"] == hashlib.sha256(
        source_lock
    ).hexdigest()


def test_phase34_sbom_normalization_is_deterministic_and_complete() -> None:
    document = json.loads(SBOM.read_text(encoding="utf-8"))
    assert validate_sbom(document) == []
    assert document["vulnerabilities"] == []


def test_phase34_supply_chain_validation_rejects_tampering() -> None:
    document = build_dependencies()
    document["postgis"]["container_index_digest"] = "sha256:" + "0" * 64
    assert "postgis" in validate_dependencies(document)
    assert "content_digest" in validate_dependencies(document)


def test_phase34_container_review_preserves_findings_and_blocks_deployment() -> None:
    review = json.loads(CONTAINER_REVIEW.read_text(encoding="utf-8"))
    assert validate_container_review(review) == []
    assert review["severity_counts"]["CRITICAL"] == 2
    assert review["severity_counts"]["HIGH"] == 21
    assert review["finding_count"] == 54
    assert review["deployment_gate"].startswith("blocked_")
