from __future__ import annotations

import io
import subprocess
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import phase31_contracts


def test_tracked_p3_1_evidence_matches_deterministic_generator() -> None:
    assert phase31_contracts.check_contracts(require_clean_source=False) == 0


def test_rendered_package_has_expected_bounded_shape() -> None:
    rendered = phase31_contracts.render_contracts()

    assert len(rendered) == 28
    assert all(path.suffix == ".json" for path in rendered)
    assert all(len(document.encode("utf-8")) <= 1024 * 1024 for document in rendered.values())
    assert sum("candidates" in path.parts for path in rendered) == 11
    assert sum("generated" in path.parts for path in rendered) == 7


def test_writer_requires_explicit_generated_only_acknowledgment() -> None:
    assert phase31_contracts.write_contracts(acknowledged=False) == 2


def test_clean_source_gate_rejects_current_dirty_evidence(monkeypatch) -> None:
    monkeypatch.setattr(
        phase31_contracts,
        "source_state",
        lambda: ("a" * 40, True),
    )
    monkeypatch.setattr(
        phase31_contracts,
        "recorded_source_state",
        lambda: ("a" * 40, True),
    )
    monkeypatch.setattr(phase31_contracts, "render_contracts", lambda **_kwargs: {})

    assert phase31_contracts.check_contracts(require_clean_source=True) == 1


def test_check_reports_missing_drift_and_unexpected_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path
    contract_root = root / "contracts" / "phase-3" / "p3-1"
    expected_path = contract_root / "expected.json"
    unexpected_path = contract_root / "unexpected.json"
    contract_root.mkdir(parents=True)
    expected_path.write_text('{"state":"old"}\n', encoding="utf-8")
    unexpected_path.write_text('{"state":"unexpected"}\n', encoding="utf-8")

    monkeypatch.setattr(phase31_contracts, "ROOT", root)
    monkeypatch.setattr(phase31_contracts, "CONTRACT_ROOT", contract_root)
    monkeypatch.setattr(
        phase31_contracts,
        "source_state",
        lambda: ("b" * 40, False),
    )
    monkeypatch.setattr(
        phase31_contracts,
        "recorded_source_state",
        lambda: ("b" * 40, False),
    )
    monkeypatch.setattr(
        phase31_contracts,
        "render_contracts",
        lambda **_kwargs: {
            expected_path: '{"state":"current"}\n',
            contract_root / "missing.json": '{"state":"missing"}\n',
        },
    )

    output = io.StringIO()
    with redirect_stdout(output):
        result = phase31_contracts.check_contracts(require_clean_source=False)

    assert result == 1
    assert "unexpected P3.1 JSON artifact" in output.getvalue()
    assert "drifted" in output.getvalue()
    assert "missing.json" in output.getvalue()


@pytest.mark.parametrize(
    "relative_path,document,expected",
    [
        ("hidden/.record.json", "{}\n", "visible JSON"),
        ("record.txt", "{}\n", "visible JSON"),
        ("record.json", "", "one MiB"),
        ("record.json", "x" * (1024 * 1024 + 1), "one MiB"),
        ("record.json", "not-json\n", "valid JSON"),
        ("record.json", "[]\n", "root must be an object"),
    ],
    ids=["hidden", "suffix", "empty", "oversized", "invalid-json", "non-object"],
)
def test_artifact_validator_rejects_unsafe_output(
    relative_path: str,
    document: str,
    expected: str,
) -> None:
    failures = phase31_contracts._validate_artifact(
        phase31_contracts.CONTRACT_ROOT / relative_path,
        document,
    )

    assert any(expected in failure for failure in failures)


def test_artifact_validator_rejects_escape() -> None:
    failures = phase31_contracts._validate_artifact(
        phase31_contracts.CONTRACT_ROOT.parent / "escaped.json",
        "{}\n",
    )

    assert failures == ["artifact escapes the P3.1 contract root"]


def test_writer_creates_reviewed_artifacts_in_a_temporary_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path
    contract_root = root / "contracts" / "phase-3" / "p3-1"
    path = contract_root / "record.json"
    monkeypatch.setattr(phase31_contracts, "ROOT", root)
    monkeypatch.setattr(phase31_contracts, "CONTRACT_ROOT", contract_root)
    monkeypatch.setattr(
        phase31_contracts,
        "source_state",
        lambda: ("d" * 40, False),
    )
    monkeypatch.setattr(
        phase31_contracts,
        "render_contracts",
        lambda **_kwargs: {path: '{"generated_only":true}\n'},
    )

    assert phase31_contracts.write_contracts(acknowledged=True) == 0
    assert path.read_text(encoding="utf-8") == '{"generated_only":true}\n'


def test_writer_refuses_invalid_rendered_artifact(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    contract_root = root / "contracts" / "phase-3" / "p3-1"
    path = contract_root / "record.json"
    monkeypatch.setattr(phase31_contracts, "ROOT", root)
    monkeypatch.setattr(phase31_contracts, "CONTRACT_ROOT", contract_root)
    monkeypatch.setattr(
        phase31_contracts,
        "source_state",
        lambda: ("e" * 40, False),
    )
    monkeypatch.setattr(
        phase31_contracts,
        "render_contracts",
        lambda **_kwargs: {path: "[]\n"},
    )

    assert phase31_contracts.write_contracts(acknowledged=True) == 1
    assert not path.exists()


def test_file_digest_and_git_errors_are_sanitized(tmp_path: Path, monkeypatch) -> None:
    with pytest.raises(phase31_contracts.EvidenceGenerationError, match="unavailable"):
        phase31_contracts._file_digest(tmp_path / "missing.lock")

    monkeypatch.setattr(
        phase31_contracts.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr="secret"),
    )
    with pytest.raises(phase31_contracts.EvidenceGenerationError, match="command failed"):
        phase31_contracts._git_output(["rev-parse", "HEAD"])


def test_git_timeout_and_invalid_commit_are_fail_closed(monkeypatch) -> None:
    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("git", 20)

    monkeypatch.setattr(phase31_contracts.subprocess, "run", timeout)
    with pytest.raises(phase31_contracts.EvidenceGenerationError, match="unavailable"):
        phase31_contracts._git_output(["status"])

    monkeypatch.setattr(phase31_contracts, "_git_output", lambda _arguments: "not-a-commit")
    with pytest.raises(phase31_contracts.EvidenceGenerationError, match="source commit is invalid"):
        phase31_contracts.source_state()


def test_check_and_write_report_generation_failures(monkeypatch) -> None:
    def fail_state() -> tuple[str, bool]:
        raise phase31_contracts.EvidenceGenerationError("local metadata unavailable")

    monkeypatch.setattr(phase31_contracts, "source_state", fail_state)
    assert phase31_contracts.check_contracts(require_clean_source=False) == 1

    def fail_render(**_kwargs) -> dict[Path, str]:
        raise phase31_contracts.EvidenceGenerationError("local input unavailable")

    monkeypatch.setattr(phase31_contracts, "render_contracts", fail_render)
    assert phase31_contracts.write_contracts(acknowledged=True) == 1


def test_cli_routes_check_and_write_modes(monkeypatch) -> None:
    monkeypatch.setattr(
        phase31_contracts,
        "check_contracts",
        lambda *, require_clean_source: 7 if require_clean_source else 6,
    )
    monkeypatch.setattr(
        phase31_contracts,
        "write_contracts",
        lambda *, acknowledged: 9 if acknowledged else 8,
    )

    assert phase31_contracts.main(["check"]) == 6
    assert phase31_contracts.main(["check", "--require-clean-source"]) == 7
    assert phase31_contracts.main(["write"]) == 8
    assert phase31_contracts.main(
        ["write", "--acknowledge-generated-only-evidence"]
    ) == 9
