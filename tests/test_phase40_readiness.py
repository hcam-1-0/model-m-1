from __future__ import annotations

from pathlib import Path

import pytest

from tools import phase40_readiness, phase41_readiness


ROOT = Path(__file__).resolve().parents[1]


def test_phase40_readiness_reports_all_sealed_historical_gates() -> None:
    assert phase41_readiness._p4_0_readiness_passes() is True


def test_phase40_evidence_reads_components_from_accepted_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = phase40_readiness._json(
        ROOT / "contracts/phase-4/p4-0-evidence-package.json"
    )
    original = phase40_readiness._git_bytes
    observed: list[tuple[str, ...]] = []

    def recording_git_bytes(*args: str) -> bytes:
        observed.append(args)
        return original(*args)

    monkeypatch.setattr(phase40_readiness, "_git_bytes", recording_git_bytes)
    assert phase40_readiness._evidence_package_is_exact(package) is True
    assert observed
    assert all(
        args[1].startswith(phase40_readiness.P4_0_IMPLEMENTATION_COMMIT + ":")
        for args in observed
    )


def test_phase40_evidence_fails_closed_on_historical_component_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = phase40_readiness._json(
        ROOT / "contracts/phase-4/p4-0-evidence-package.json"
    )
    original = phase40_readiness._git_bytes
    first_path = package["components"][0]["path"]

    def mismatching_git_bytes(*args: str) -> bytes:
        if args == (
            "show",
            f"{phase40_readiness.P4_0_IMPLEMENTATION_COMMIT}:{first_path}",
        ):
            return b"historical-mismatch\n"
        return original(*args)

    monkeypatch.setattr(phase40_readiness, "_git_bytes", mismatching_git_bytes)
    assert phase40_readiness._evidence_package_is_exact(package) is False
