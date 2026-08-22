from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout

from tools import phase2_readiness
from tools import phase2_publication_evidence as publication_evidence


def test_phase2_report_preserves_core_acceptance_and_pending_extension() -> None:
    report = phase2_readiness.build_report(run_validation=False)

    assert report["failures"] == 0
    assert report["manual_gates"] == 1
    assert report["status"] == "accepted_core_extension_pending"


def test_phase2_extension_publication_gate_lists_remaining_evidence() -> None:
    check = phase2_readiness.check_extension_publication()

    assert check.status == phase2_readiness.MANUAL
    assert "4 controlled ONVIF extension publication gates remain" in check.detail
    assert check.evidence[0].endswith("extension-publication-checklist.md")
    assert check.evidence[1].startswith("P2-G1:")


def test_phase2_extension_gate_rejects_checked_gate_without_evidence(
    monkeypatch,
) -> None:
    original_read = phase2_readiness._read
    content = original_read("docs/phase-2/extension-publication-checklist.md")
    content = content.replace("- [ ] `P2-G1`", "- [x] `P2-G1`", 1)

    def read(path: str) -> str:
        if path == "docs/phase-2/extension-publication-checklist.md":
            return content
        return original_read(path)

    monkeypatch.setattr(phase2_readiness, "_read", read)

    check = phase2_readiness.check_extension_publication()

    assert check.status == phase2_readiness.FAIL
    assert "P2-G1 has no completed evidence reference" in check.detail


def test_phase2_extension_gate_rejects_missing_or_reordered_gate(monkeypatch) -> None:
    original_read = phase2_readiness._read
    content = original_read("docs/phase-2/extension-publication-checklist.md")
    content = content.replace("`P2-G2`", "`P2-G5`", 1)

    def read(path: str) -> str:
        if path == "docs/phase-2/extension-publication-checklist.md":
            return content
        return original_read(path)

    monkeypatch.setattr(phase2_readiness, "_read", read)

    check = phase2_readiness.check_extension_publication()

    assert check.status == phase2_readiness.FAIL
    assert "must appear exactly once and in order" in check.detail


def test_phase2_extension_gate_rejects_unsafe_or_missing_local_evidence(
    monkeypatch,
) -> None:
    original_read = phase2_readiness._read
    template = """# Controlled ONVIF Extension Publication Checklist

Status: `accepted`

- [x] `P2-G1` PostgreSQL gate.
  Evidence: [run](https://github.com/mayankthakor227/h-cam-2.0/actions/runs/1)
- [x] `P2-G2` Compose gate.
  Evidence: [run](https://github.com/mayankthakor227/h-cam-2.0/actions/runs/2)
- [x] `P2-G3` Pull request gate.
  Evidence: [PR](https://github.com/mayankthakor227/h-cam-2.0/pull/1)
- [x] `P2-G4` Owner acceptance gate.
  Evidence: [review]({target})
"""

    for target, expected in (
        ("../../outside.md", "contains an unsafe link"),
        ("missing-evidence.md", "evidence file does not exist"),
        ("#self", "must identify a file or HTTPS URL"),
    ):
        content = template.format(target=target)

        def read(path: str, evidence_content: str = content) -> str:
            if path == "docs/phase-2/extension-publication-checklist.md":
                return evidence_content
            return original_read(path)

        monkeypatch.setattr(phase2_readiness, "_read", read)
        check = phase2_readiness.check_extension_publication()
        assert check.status == phase2_readiness.FAIL
        assert expected in check.detail


def test_phase2_extension_gate_accepts_complete_linked_evidence(monkeypatch) -> None:
    content = """# Controlled ONVIF Extension Publication Checklist

Status: `accepted`

- [x] `P2-G1` PostgreSQL gate.
  Evidence: [PostgreSQL run](https://github.com/mayankthakor227/h-cam-2.0/actions/runs/1)
- [x] `P2-G2` Compose gate.
  Evidence: [Compose run](https://github.com/mayankthakor227/h-cam-2.0/actions/runs/2)
- [x] `P2-G3` Pull request gate.
  Evidence: [Pull request](https://github.com/mayankthakor227/h-cam-2.0/pull/1)
- [x] `P2-G4` Owner acceptance gate.
  Evidence: [Owner review](owner-review.md)
"""
    original_read = phase2_readiness._read

    def read(path: str) -> str:
        if path == "docs/phase-2/extension-publication-checklist.md":
            return content
        return original_read(path)

    monkeypatch.setattr(phase2_readiness, "_read", read)

    check = phase2_readiness.check_extension_publication()

    assert check.status == phase2_readiness.PASS


def test_phase2_extension_gate_requires_accepted_status_when_complete(
    monkeypatch,
) -> None:
    content = """# Controlled ONVIF Extension Publication Checklist

Status: `pending`

- [x] `P2-G1` PostgreSQL gate.
  Evidence: [run](https://github.com/mayankthakor227/h-cam-2.0/actions/runs/1)
- [x] `P2-G2` Compose gate.
  Evidence: [run](https://github.com/mayankthakor227/h-cam-2.0/actions/runs/2)
- [x] `P2-G3` Pull request gate.
  Evidence: [PR](https://github.com/mayankthakor227/h-cam-2.0/pull/1)
- [x] `P2-G4` Owner acceptance gate.
  Evidence: [review](owner-review.md)
"""
    original_read = phase2_readiness._read

    def read(path: str) -> str:
        if path == "docs/phase-2/extension-publication-checklist.md":
            return content
        return original_read(path)

    monkeypatch.setattr(phase2_readiness, "_read", read)

    check = phase2_readiness.check_extension_publication()

    assert check.status == phase2_readiness.FAIL
    assert "must be `accepted`" in check.detail


def test_phase2_extension_gate_rejects_unrelated_https_evidence(monkeypatch) -> None:
    content = """# Controlled ONVIF Extension Publication Checklist

Status: `accepted`

- [x] `P2-G1` PostgreSQL gate.
  Evidence: [run](https://github.com/another/repository/actions/runs/1)
- [x] `P2-G2` Compose gate.
  Evidence: [run](https://github.com/mayankthakor227/h-cam-2.0/actions/runs/2)
- [x] `P2-G3` Pull request gate.
  Evidence: [PR](https://github.com/mayankthakor227/h-cam-2.0/pull/1)
- [x] `P2-G4` Owner acceptance gate.
  Evidence: [review](owner-review.md)
"""
    original_read = phase2_readiness._read

    def read(path: str) -> str:
        if path == "docs/phase-2/extension-publication-checklist.md":
            return content
        return original_read(path)

    monkeypatch.setattr(phase2_readiness, "_read", read)

    check = phase2_readiness.check_extension_publication()

    assert check.status == phase2_readiness.FAIL
    assert "P2-G1 HTTPS evidence must link this repository's Actions run" in check.detail


def test_phase2_extension_gate_verifies_local_runtime_artifact(
    monkeypatch, tmp_path
) -> None:
    docs = tmp_path / "docs" / "phase-2"
    docs.mkdir(parents=True)
    artifact = docs / "p2-g1.json"
    source = {
        "commit": "a" * 40,
        "branch": "codex/phase2-test",
        "worktree_clean": True,
        "eligible": True,
        "errors": [],
        "contracts": {
            "openapi_sha256": publication_evidence._sha256(
                publication_evidence.ROOT / "contracts/phase-2/openapi.json"
            ),
            "database_sha256": publication_evidence._sha256(
                publication_evidence.ROOT / "contracts/phase-2/database.json"
            ),
        },
        "dependencies": {
            "uv_lock_sha256": publication_evidence._sha256(
                publication_evidence.ROOT / "uv.lock"
            )
        },
    }
    report = publication_evidence._blocked_report(
        publication_evidence.POSTGRES_GATE,
        source,
        [],
        safety=publication_evidence._EXPECTED_GATE_SAFETY[
            publication_evidence.POSTGRES_GATE
        ],
    )
    report["status"] = "passed"
    report["checks"] = [
        {
            "name": name,
            "status": "passed",
            "command": [
                sys.executable,
                *publication_evidence._EXPECTED_COMMAND_TAILS[name],
            ],
            "exit_code": 0,
            "duration_ms": 1,
            "detail": "completed",
        }
        for name in publication_evidence._EXPECTED_GATE_CHECKS[
            publication_evidence.POSTGRES_GATE
        ]
    ]
    artifact.write_text(json.dumps(report), encoding="utf-8")
    content = """# Controlled ONVIF Extension Publication Checklist

Status: `accepted`

- [x] `P2-G1` PostgreSQL gate.
  Evidence: [artifact](p2-g1.json)
- [x] `P2-G2` Compose gate.
  Evidence: [run](https://github.com/mayankthakor227/h-cam-2.0/actions/runs/2)
- [x] `P2-G3` Pull request gate.
  Evidence: [PR](https://github.com/mayankthakor227/h-cam-2.0/pull/1)
- [x] `P2-G4` Owner acceptance gate.
  Evidence: [review](https://github.com/mayankthakor227/h-cam-2.0/pull/1#issuecomment-1)
"""

    monkeypatch.setattr(phase2_readiness, "ROOT", tmp_path)
    monkeypatch.setattr(phase2_readiness, "_current_head", lambda: "a" * 40)
    monkeypatch.setattr(
        phase2_readiness,
        "_read",
        lambda path: content
        if path == "docs/phase-2/extension-publication-checklist.md"
        else "",
    )

    check = phase2_readiness.check_extension_publication()

    assert check.status == phase2_readiness.PASS


def test_phase2_strict_mode_stops_at_extension_publication_gate() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = phase2_readiness.main(["--strict"])

    assert exit_code == 2
    assert "Phase 2 readiness: accepted_core_extension_pending" in output.getvalue()
    assert "Manual gates: 1" in output.getvalue()


def test_phase2_json_status_is_machine_readable() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = phase2_readiness.main(["--json"])

    assert exit_code == 0
    assert '"status": "accepted_core_extension_pending"' in output.getvalue()
