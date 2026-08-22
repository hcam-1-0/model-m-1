from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tools import phase2_publication_evidence as evidence


class FakeExecutor:
    def __init__(
        self,
        responder: Callable[
            [list[str], dict[str, str] | None], subprocess.CompletedProcess[str]
        ],
    ) -> None:
        self.responder = responder
        self.calls: list[tuple[list[str], dict[str, str] | None, float]] = []

    def __call__(
        self,
        command: list[str],
        environment: dict[str, str] | None,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append((command, environment, timeout))
        return self.responder(command, environment)


def _completed(
    command: list[str],
    *,
    code: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, code, stdout, stderr)


def test_default_executor_uses_resilient_utf8_decoding(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def run(command, **kwargs):
        captured.update(kwargs)
        return _completed(command)

    monkeypatch.setattr(evidence.subprocess, "run", run)

    evidence._default_executor(["example"], None, 10)

    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"


def _clean_git_response(
    command: list[str], _environment: dict[str, str] | None
) -> subprocess.CompletedProcess[str] | None:
    if command == ["git", "rev-parse", "HEAD"]:
        return _completed(command, stdout="a" * 40 + "\n")
    if command == ["git", "branch", "--show-current"]:
        return _completed(command, stdout="codex/phase2-test\n")
    if command == ["git", "status", "--porcelain", "--untracked-files=normal"]:
        return _completed(command)
    return None


def _passing_response(
    command: list[str], environment: dict[str, str] | None
) -> subprocess.CompletedProcess[str]:
    clean = _clean_git_response(command, environment)
    if clean is not None:
        return clean
    return _completed(command)


def _write_report(path: Path, report: dict[str, object]) -> None:
    path.write_text(json.dumps(report), encoding="utf-8")


def _valid_postgres_report() -> dict[str, object]:
    return evidence.run_postgres_gate(
        confirmed_disposable=True,
        executor=FakeExecutor(_passing_response),
        environment={
            "HCAM_POSTGRES_TEST_URL": "postgresql+psycopg://hcam:test@db/hcam_test"
        },
    )


def _github_responder(
    report: dict[str, object],
    now: datetime,
    *,
    run_overrides: dict[str, object] | None = None,
    job_overrides: dict[str, object] | None = None,
    artifact_overrides: dict[str, object] | None = None,
    add_extra_payload: bool = False,
) -> tuple[
    Callable[[list[str], dict[str, str] | None], subprocess.CompletedProcess[str]],
    list[Path],
]:
    run_id = 123456
    commit = "a" * 40
    run = {
        "id": run_id,
        "html_url": f"https://github.com/{evidence.REPOSITORY}/actions/runs/{run_id}",
        "repository": {"full_name": evidence.REPOSITORY},
        "name": "Python CI",
        "path": ".github/workflows/python-ci.yml",
        "event": "pull_request",
        "run_attempt": 1,
        "status": "completed",
        "conclusion": "success",
        "head_branch": "codex/phase2-test",
        "head_sha": commit,
        "run_started_at": (now - timedelta(minutes=5)).isoformat(),
    }
    run.update(run_overrides or {})
    job = {
        "id": 987,
        "name": "PostgreSQL 18 integration",
        "status": "completed",
        "conclusion": "success",
        "html_url": f"https://github.com/{evidence.REPOSITORY}/actions/runs/{run_id}/job/987",
    }
    job.update(job_overrides or {})
    artifact = {
        "id": 654,
        "name": f"phase2-p2-g1-{commit}",
        "size_in_bytes": len(json.dumps(report).encode("utf-8")),
        "digest": "sha256:" + "b" * 64,
        "expired": False,
        "created_at": (now - timedelta(minutes=4)).isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
        "workflow_run": {"id": run_id, "head_sha": commit},
    }
    artifact.update(artifact_overrides or {})
    download_directories: list[Path] = []

    def respond(command, environment):
        clean = _clean_git_response(command, environment)
        if clean is not None:
            return clean
        if command[:2] == ["gh", "api"]:
            endpoint = command[-1]
            if endpoint.endswith(f"actions/runs/{run_id}"):
                return _completed(command, stdout=json.dumps(run))
            if "/jobs?" in endpoint:
                return _completed(command, stdout=json.dumps({"jobs": [job]}))
            if "/artifacts?" in endpoint:
                return _completed(
                    command, stdout=json.dumps({"artifacts": [artifact]})
                )
        if command[:3] == ["gh", "run", "download"]:
            directory = Path(command[command.index("--dir") + 1])
            download_directories.append(directory)
            _write_report(directory / "p2-g1.json", report)
            if add_extra_payload:
                (directory / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            return _completed(command)
        raise AssertionError(command)

    return respond, download_directories


def test_redaction_removes_database_url_and_password() -> None:
    database_url = "postgresql+psycopg://hcam:super-secret@db:5432/hcam_test"
    source = f"connection failed for {database_url}; password=super-secret"

    redacted = evidence._redact(source, evidence._secret_values(database_url))

    assert database_url not in redacted
    assert "super-secret" not in redacted
    assert "[redacted]" in redacted


def test_preflight_rejects_empty_docker_server_even_with_zero_exit() -> None:
    def respond(command, environment):
        clean = _clean_git_response(command, environment)
        if clean is not None:
            return clean
        if command[:2] == ["docker", "version"]:
            return _completed(
                command,
                stdout='""\n',
                stderr="request returned 500 Internal Server Error",
            )
        if command[:3] == ["docker", "compose", "version"]:
            return _completed(command, stdout="2.40.3\n")
        raise AssertionError(command)

    report = evidence.preflight_report(
        executor=FakeExecutor(respond),
        environment={},
        include_github=False,
    )

    docker = report["environment"]["docker"]
    assert report["status"] == "blocked"
    assert report["gates"][evidence.COMPOSE_GATE]["status"] == "blocked"
    assert docker["ready"] is False
    assert "500 Internal Server Error" in docker["detail"]
    assert report["environment"]["postgres"]["configured"] is False


def test_source_state_uses_github_branch_for_detached_ci_checkout(monkeypatch) -> None:
    def respond(command, _environment):
        if command == ["git", "rev-parse", "HEAD"]:
            return _completed(command, stdout="a" * 40 + "\n")
        if command == ["git", "branch", "--show-current"]:
            return _completed(command)
        if command == ["git", "status", "--porcelain", "--untracked-files=normal"]:
            return _completed(command)
        raise AssertionError(command)

    monkeypatch.setenv("GITHUB_HEAD_REF", "codex/phase2-evidence")

    state = evidence.source_state(FakeExecutor(respond))

    assert state["branch"] == "codex/phase2-evidence"
    assert state["eligible"] is True


def test_source_state_rejects_unidentified_detached_checkout(monkeypatch) -> None:
    def respond(command, _environment):
        if command == ["git", "rev-parse", "HEAD"]:
            return _completed(command, stdout="a" * 40 + "\n")
        if command == ["git", "branch", "--show-current"]:
            return _completed(command)
        if command == ["git", "status", "--porcelain", "--untracked-files=normal"]:
            return _completed(command)
        raise AssertionError(command)

    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    monkeypatch.delenv("GITHUB_REF_NAME", raising=False)

    state = evidence.source_state(FakeExecutor(respond))

    assert state["branch"] is None
    assert state["eligible"] is False


def test_source_state_binds_dependency_lock_hash() -> None:
    state = evidence.source_state(FakeExecutor(_passing_response))

    assert state["dependencies"] == {
        "uv_lock_sha256": evidence._canonical_text_sha256(evidence.ROOT / "uv.lock")
    }
    assert state["eligible"] is True


def test_source_identity_hashes_are_independent_of_checkout_line_endings(
    monkeypatch, tmp_path: Path
) -> None:
    contracts = tmp_path / "contracts" / "phase-2"
    contracts.mkdir(parents=True)
    (contracts / "openapi.json").write_bytes(b'{\r\n  "openapi": "3.1.0"\r\n}\r\n')
    (contracts / "database.json").write_bytes(b'{\r\n  "tables": []\r\n}\r\n')
    (tmp_path / "uv.lock").write_bytes(b'version = 1\r\nrevision = 3\r\n')
    monkeypatch.setattr(evidence, "ROOT", tmp_path)

    windows_contracts, windows_dependencies = evidence._source_identity()
    for path in (*contracts.iterdir(), tmp_path / "uv.lock"):
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))

    assert evidence._source_identity() == (windows_contracts, windows_dependencies)


def test_source_state_fails_closed_without_dependency_lock(
    monkeypatch, tmp_path: Path
) -> None:
    contracts = tmp_path / "contracts" / "phase-2"
    contracts.mkdir(parents=True)
    (contracts / "openapi.json").write_text("{}", encoding="utf-8")
    (contracts / "database.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(evidence, "ROOT", tmp_path)

    state = evidence.source_state(FakeExecutor(_passing_response))

    assert state["eligible"] is False
    assert state["dependencies"] == {"uv_lock_sha256": None}
    assert "required dependency lock uv.lock is unavailable" in state["errors"]


def test_postgres_gate_requires_clean_source_confirmation_and_test_url() -> None:
    def respond(command, _environment):
        if command == ["git", "rev-parse", "HEAD"]:
            return _completed(command, stdout="a" * 40 + "\n")
        if command == ["git", "branch", "--show-current"]:
            return _completed(command, stdout="codex/phase2-test\n")
        if command == ["git", "status", "--porcelain", "--untracked-files=normal"]:
            return _completed(command, stdout=" M app/hcam/main.py\n")
        raise AssertionError(command)

    report = evidence.run_postgres_gate(
        confirmed_disposable=False,
        executor=FakeExecutor(respond),
        environment={},
    )

    assert report["status"] == "blocked"
    assert report["checks"] == []
    assert len(report["blocked_reasons"]) == 3


def test_postgres_gate_runs_full_round_trip_without_persisting_secrets() -> None:
    database_url = "postgresql+psycopg://hcam:secret-value@db:5432/hcam_test"

    def respond(command, environment):
        clean = _clean_git_response(command, environment)
        if clean is not None:
            return clean
        assert environment is not None
        assert environment["HCAM_DATABASE_URL"] == database_url
        assert environment["HCAM_POSTGRES_TEST_URL"] == database_url
        return _completed(command)

    executor = FakeExecutor(respond)
    report = evidence.run_postgres_gate(
        confirmed_disposable=True,
        executor=executor,
        environment={"HCAM_POSTGRES_TEST_URL": database_url},
    )

    assert report["status"] == "passed"
    assert [check["name"] for check in report["checks"]] == [
        "verify_postgres_18",
        "upgrade_to_head",
        "verify_schema_drift",
        "postgres_integration_tests",
        "downgrade_to_base",
        "restore_upgrade_to_head",
        "verify_restored_schema_drift",
    ]
    encoded = json.dumps(report)
    assert database_url not in encoded
    assert "secret-value" not in encoded


def test_postgres_gate_restores_head_after_downgrade_failure() -> None:
    database_url = "postgresql+psycopg://hcam:test-password@db:5432/hcam_test"

    def respond(command, environment):
        clean = _clean_git_response(command, environment)
        if clean is not None:
            return clean
        if command[-2:] == ["downgrade", "base"]:
            return _completed(command, code=1, stderr=f"failed using {database_url}")
        return _completed(command)

    report = evidence.run_postgres_gate(
        confirmed_disposable=True,
        executor=FakeExecutor(respond),
        environment={"HCAM_POSTGRES_TEST_URL": database_url},
    )

    assert report["status"] == "failed"
    assert report["checks"][-2]["name"] == "restore_upgrade_to_head"
    assert report["checks"][-1]["name"] == "verify_restored_schema_drift"
    assert database_url not in json.dumps(report)
    assert "test-password" not in json.dumps(report)


def test_compose_gate_cleans_up_after_verification_failure() -> None:
    server = json.dumps({"Version": "28.5.2", "Os": "linux", "Arch": "amd64"})

    def respond(command, environment):
        clean = _clean_git_response(command, environment)
        if clean is not None:
            return clean
        if command[:2] == ["docker", "version"]:
            return _completed(command, stdout=server)
        if command[:3] == ["docker", "compose", "version"]:
            return _completed(command, stdout="2.40.3\n")
        if "verify" in command:
            return _completed(command, code=1, stderr="synthetic verification failed")
        return _completed(command)

    executor = FakeExecutor(respond)
    report = evidence.run_compose_gate(
        confirmed_synthetic=True,
        executor=executor,
        environment={},
    )

    assert report["status"] == "failed"
    assert [check["name"] for check in report["checks"]] == [
        "prepare_synthetic_secrets",
        "validate_compose_model",
        "start_synthetic_stack",
        "verify_c50_security_and_health",
        "stop_and_remove_synthetic_stack",
    ]
    commands = [call[0] for call in executor.calls]
    assert not any("phase2_failure_drill.py" in command for command in commands)
    assert any(command[-1:] == ["stop"] for command in commands)


def test_compose_gate_does_not_start_when_docker_server_is_empty() -> None:
    def respond(command, environment):
        clean = _clean_git_response(command, environment)
        if clean is not None:
            return clean
        if command[:2] == ["docker", "version"]:
            return _completed(command, stdout='""', stderr="engine unavailable")
        if command[:3] == ["docker", "compose", "version"]:
            return _completed(command, stdout="2.40.3\n")
        raise AssertionError(command)

    executor = FakeExecutor(respond)
    report = evidence.run_compose_gate(
        confirmed_synthetic=True,
        executor=executor,
        environment={},
    )

    assert report["status"] == "blocked"
    assert report["checks"] == []
    assert not any("phase2_lab.py" in command for command, _, _ in executor.calls)


def test_docker_state_rejects_non_linux_server() -> None:
    server = json.dumps({"Version": "28.5.2", "Os": "windows", "Arch": "amd64"})

    def respond(command, _environment):
        if command[:2] == ["docker", "version"]:
            return _completed(command, stdout=server)
        if command[:3] == ["docker", "compose", "version"]:
            return _completed(command, stdout="2.40.3\n")
        raise AssertionError(command)

    state = evidence.docker_state(FakeExecutor(respond))

    assert state["ready"] is False
    assert state["server"] is None
    assert state["detail"] == "Docker server OS must be linux"


def test_verify_accepts_current_complete_postgres_artifact(tmp_path: Path) -> None:
    report = evidence.run_postgres_gate(
        confirmed_disposable=True,
        executor=FakeExecutor(_passing_response),
        environment={
            "HCAM_POSTGRES_TEST_URL": "postgresql+psycopg://hcam:test@db/hcam_test"
        },
    )
    artifact = tmp_path / "p2-g1.json"
    _write_report(artifact, report)

    verification = evidence.verify_evidence_artifact(
        artifact,
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
    )

    assert verification["status"] == "valid"
    assert verification["errors"] == []
    assert verification["safety"]["executes_gate_commands"] is False


def test_verify_accepts_current_complete_compose_artifact(tmp_path: Path) -> None:
    server = json.dumps({"Version": "28.5.2", "Os": "linux", "Arch": "amd64"})

    def respond(command, environment):
        clean = _clean_git_response(command, environment)
        if clean is not None:
            return clean
        if command[:2] == ["docker", "version"]:
            return _completed(command, stdout=server)
        if command[:3] == ["docker", "compose", "version"]:
            return _completed(command, stdout="2.40.3\n")
        return _completed(command)

    report = evidence.run_compose_gate(
        confirmed_synthetic=True,
        executor=FakeExecutor(respond),
        environment={},
    )
    artifact = tmp_path / "p2-g2.json"
    _write_report(artifact, report)

    verification = evidence.verify_evidence_artifact(
        artifact,
        expected_gate=evidence.COMPOSE_GATE,
        expected_commit="a" * 40,
    )

    assert verification["status"] == "valid"
    assert verification["errors"] == []


def test_verify_rejects_stale_failed_or_mismatched_artifact(tmp_path: Path) -> None:
    report = evidence.run_postgres_gate(
        confirmed_disposable=True,
        executor=FakeExecutor(_passing_response),
        environment={
            "HCAM_POSTGRES_TEST_URL": "postgresql+psycopg://hcam:test@db/hcam_test"
        },
    )
    report["generated_at"] = (datetime.now(UTC) - timedelta(days=8)).isoformat()
    report["status"] = "failed"
    report["source"]["contracts"]["openapi_sha256"] = "0" * 64
    report["checks"][0]["command"] = ["python", "-c", "pass"]
    artifact = tmp_path / "invalid.json"
    _write_report(artifact, report)

    verification = evidence.verify_evidence_artifact(
        artifact,
        expected_gate=evidence.COMPOSE_GATE,
        expected_commit="b" * 40,
    )

    assert verification["status"] == "invalid"
    assert "gate does not match expected P2-G2" in verification["errors"]
    assert "publication gate status must be passed" in verification["errors"]
    assert "evidence is older than 7 days" in verification["errors"]
    assert "source commit does not match the expected commit" in verification["errors"]
    assert "contract hashes do not match the current repository" in verification["errors"]
    assert "check verify_postgres_18 command is not approved" in verification["errors"]


def test_verify_rejects_credential_like_values(tmp_path: Path) -> None:
    report = evidence.run_postgres_gate(
        confirmed_disposable=True,
        executor=FakeExecutor(_passing_response),
        environment={
            "HCAM_POSTGRES_TEST_URL": "postgresql+psycopg://hcam:test@db/hcam_test"
        },
    )
    report["password"] = "leaked-value"
    artifact = tmp_path / "credential.json"
    _write_report(artifact, report)

    verification = evidence.verify_evidence_artifact(artifact)

    assert verification["status"] == "invalid"
    assert "evidence artifact contains a credential-like value" in verification["errors"]


def test_verify_rejects_dependency_lock_drift(tmp_path: Path) -> None:
    report = _valid_postgres_report()
    report["source"]["dependencies"]["uv_lock_sha256"] = "0" * 64
    artifact = tmp_path / "lock-drift.json"
    _write_report(artifact, report)

    verification = evidence.verify_evidence_artifact(
        artifact,
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
    )

    assert verification["status"] == "invalid"
    assert (
        "dependency lock hash does not match the current repository"
        in verification["errors"]
    )


def test_verify_rejects_oversized_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "oversized.json"
    artifact.write_bytes(b" " * (evidence._MAX_EVIDENCE_BYTES + 1))

    verification = evidence.verify_evidence_artifact(artifact)

    assert verification["status"] == "invalid"
    assert verification["errors"] == [
        f"evidence artifact exceeds {evidence._MAX_EVIDENCE_BYTES} bytes"
    ]


def test_verify_github_run_accepts_successful_commit_bound_artifact() -> None:
    now = datetime.now(UTC)
    report = _valid_postgres_report()
    responder, download_directories = _github_responder(report, now)
    executor = FakeExecutor(responder)

    verification = evidence.verify_github_run(
        f"https://github.com/{evidence.REPOSITORY}/actions/runs/123456",
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
        executor=executor,
        now=now,
    )

    assert verification["status"] == "valid"
    assert verification["errors"] == []
    assert verification["blocked_reasons"] == []
    assert verification["run"]["head_sha"] == "a" * 40
    assert verification["job"]["name"] == "PostgreSQL 18 integration"
    assert verification["payload"]["status"] == "valid"
    assert verification["safety"]["github_read_only"] is True
    assert len(download_directories) == 1
    assert not download_directories[0].exists()
    commands = [call[0] for call in executor.calls]
    assert any(
        any(evidence._GITHUB_API_VERSION in argument for argument in command)
        for command in commands
    )
    assert any(command[:3] == ["gh", "run", "download"] for command in commands)


def test_verify_github_run_rejects_wrong_run_commit_before_download() -> None:
    now = datetime.now(UTC)
    report = _valid_postgres_report()
    responder, download_directories = _github_responder(
        report, now, run_overrides={"head_sha": "b" * 40}
    )

    verification = evidence.verify_github_run(
        f"https://github.com/{evidence.REPOSITORY}/actions/runs/123456",
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
        executor=FakeExecutor(responder),
        now=now,
    )

    assert verification["status"] == "invalid"
    assert "GitHub run head SHA does not match the expected commit" in verification[
        "errors"
    ]
    assert download_directories == []


def test_verify_github_run_rejects_noncanonical_run_url_without_api_access() -> None:
    executor = FakeExecutor(_passing_response)

    verification = evidence.verify_github_run(
        f"https://github.com/{evidence.REPOSITORY}/actions/runs/123456?attempt=1",
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
        executor=executor,
    )

    assert verification["status"] == "invalid"
    assert verification["errors"] == [
        f"run URL must identify an Actions run in {evidence.REPOSITORY}"
    ]
    assert not any(call[0][:2] == ["gh", "api"] for call in executor.calls)


def test_verify_github_run_rejects_failed_expected_job() -> None:
    now = datetime.now(UTC)
    report = _valid_postgres_report()
    responder, download_directories = _github_responder(
        report, now, job_overrides={"conclusion": "failure"}
    )

    verification = evidence.verify_github_run(
        f"https://github.com/{evidence.REPOSITORY}/actions/runs/123456",
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
        executor=FakeExecutor(responder),
        now=now,
    )

    assert verification["status"] == "invalid"
    assert "GitHub job PostgreSQL 18 integration must complete successfully" in verification[
        "errors"
    ]
    assert download_directories == []


def test_verify_github_run_rejects_expired_artifact() -> None:
    now = datetime.now(UTC)
    report = _valid_postgres_report()
    responder, download_directories = _github_responder(
        report,
        now,
        artifact_overrides={
            "expired": True,
            "expires_at": (now - timedelta(minutes=1)).isoformat(),
        },
    )

    verification = evidence.verify_github_run(
        f"https://github.com/{evidence.REPOSITORY}/actions/runs/123456",
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
        executor=FakeExecutor(responder),
        now=now,
    )

    assert verification["status"] == "invalid"
    assert "GitHub publication artifact is expired" in verification["errors"]
    assert "GitHub artifact expiry time is invalid or elapsed" in verification["errors"]
    assert download_directories == []


def test_verify_github_run_rejects_future_dated_artifact() -> None:
    now = datetime.now(UTC)
    report = _valid_postgres_report()
    responder, download_directories = _github_responder(
        report,
        now,
        artifact_overrides={
            "created_at": (now + timedelta(minutes=10)).isoformat(),
        },
    )

    verification = evidence.verify_github_run(
        f"https://github.com/{evidence.REPOSITORY}/actions/runs/123456",
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
        executor=FakeExecutor(responder),
        now=now,
    )

    assert verification["status"] == "invalid"
    assert "GitHub artifact creation time is in the future" in verification["errors"]
    assert download_directories == []


def test_verify_github_run_rejects_extra_downloaded_payload_file() -> None:
    now = datetime.now(UTC)
    report = _valid_postgres_report()
    responder, download_directories = _github_responder(
        report, now, add_extra_payload=True
    )

    verification = evidence.verify_github_run(
        f"https://github.com/{evidence.REPOSITORY}/actions/runs/123456",
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
        executor=FakeExecutor(responder),
        now=now,
    )

    assert verification["status"] == "invalid"
    assert (
        "downloaded artifact must contain exactly one expected JSON file"
        in verification["errors"]
    )
    assert len(download_directories) == 1
    assert not download_directories[0].exists()


def test_verify_github_run_blocks_dirty_or_mismatched_local_source() -> None:
    def respond(command, _environment):
        if command == ["git", "rev-parse", "HEAD"]:
            return _completed(command, stdout="b" * 40 + "\n")
        if command == ["git", "branch", "--show-current"]:
            return _completed(command, stdout="codex/other\n")
        if command == ["git", "status", "--porcelain", "--untracked-files=normal"]:
            return _completed(command)
        raise AssertionError(command)

    executor = FakeExecutor(respond)
    verification = evidence.verify_github_run(
        f"https://github.com/{evidence.REPOSITORY}/actions/runs/123456",
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
        executor=executor,
    )

    assert verification["status"] == "blocked"
    assert verification["blocked_reasons"] == [
        "local HEAD must equal the expected commit"
    ]
    assert not any(call[0][:2] == ["gh", "api"] for call in executor.calls)


def test_verify_github_run_redacts_token_when_api_is_unavailable() -> None:
    token = "ghp_" + "sensitivevalue" * 3

    def respond(command, environment):
        clean = _clean_git_response(command, environment)
        if clean is not None:
            return clean
        if command[:2] == ["gh", "api"]:
            return _completed(command, code=1, stderr=f"authentication failed: {token}")
        raise AssertionError(command)

    verification = evidence.verify_github_run(
        f"https://github.com/{evidence.REPOSITORY}/actions/runs/123456",
        expected_gate=evidence.POSTGRES_GATE,
        expected_commit="a" * 40,
        executor=FakeExecutor(respond),
    )

    encoded = json.dumps(verification)
    assert verification["status"] == "blocked"
    assert token not in encoded
    assert "[redacted]" in encoded
