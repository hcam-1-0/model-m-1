#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "hcam.phase2.publication-evidence.v2"
REPOSITORY = "mayankthakor227/h-cam-2.0"
POSTGRES_GATE = "P2-G1"
COMPOSE_GATE = "P2-G2"
FAILED = 1
BLOCKED = 2
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_MAX_EVIDENCE_BYTES = 1024 * 1024
_DEFAULT_MAX_AGE_DAYS = 7
_FUTURE_TOLERANCE = timedelta(minutes=5)
_DATABASE_USERINFO = re.compile(
    r"(?i)\b(postgresql(?:\+[a-z0-9_]+)?://)([^@\s]+)@"
)
_SENSITIVE_JSON_VALUE = re.compile(
    r'(?i)"(?:password|authorization|proxy-authorization)"\s*:\s*"(?!\[redacted\])[^"\r\n]+"'
)
_AUTHORIZATION_VALUE = re.compile(r"(?i)\bauthorization\s*[:=]\s*(?:basic|bearer)\s+\S+")
_GITHUB_TOKEN_VALUE = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"
)
_ACTIONS_RUN_URL = re.compile(
    r"^https://github\.com/mayankthakor227/h-cam-2\.0/actions/runs/"
    r"(?P<run_id>[1-9][0-9]*)/?$"
)
_GITHUB_API_VERSION = "2026-03-10"
_WORKFLOW_PATH = ".github/workflows/python-ci.yml"
_WORKFLOW_NAME = "Python CI"
_EXPECTED_GITHUB_JOBS = {
    POSTGRES_GATE: "PostgreSQL 18 integration",
    COMPOSE_GATE: "Phase 2 synthetic 50-stream lab",
}
_EXPECTED_ARTIFACT_PAYLOADS = {
    POSTGRES_GATE: "p2-g1.json",
    COMPOSE_GATE: "p2-g2.json",
}
_EXPECTED_GATE_CHECKS = {
    POSTGRES_GATE: (
        "verify_postgres_18",
        "upgrade_to_head",
        "verify_schema_drift",
        "postgres_integration_tests",
        "downgrade_to_base",
        "restore_upgrade_to_head",
        "verify_restored_schema_drift",
    ),
    COMPOSE_GATE: (
        "prepare_synthetic_secrets",
        "validate_compose_model",
        "start_synthetic_stack",
        "verify_c50_security_and_health",
        "verify_outage_recovery",
        "stop_and_remove_synthetic_stack",
    ),
}
_EXPECTED_GATE_SAFETY = {
    POSTGRES_GATE: {
        "uses_only_postgres_test_url": True,
        "requires_disposable_confirmation": True,
        "contacts_cameras": False,
        "captures_images": False,
        "records_video": False,
    },
    COMPOSE_GATE: {
        "synthetic_lab_only": True,
        "contacts_cameras": False,
        "captures_images": False,
        "records_video": False,
        "stops_stack_after_start_attempt": True,
    },
}
_POSTGRES_VERSION_COMMAND = """import os
from sqlalchemy import create_engine

engine = create_engine(os.environ["HCAM_POSTGRES_TEST_URL"])
try:
    with engine.connect() as connection:
        version = int(connection.exec_driver_sql("SHOW server_version_num").scalar_one())
finally:
    engine.dispose()
if not 180000 <= version < 190000:
    raise SystemExit(f"PostgreSQL 18 required; server_version_num={version}")
print("PostgreSQL major version 18 confirmed")
"""
_EXPECTED_COMMAND_TAILS = {
    "verify_postgres_18": ("-c", _POSTGRES_VERSION_COMMAND),
    "upgrade_to_head": ("-m", "alembic", "upgrade", "head"),
    "verify_schema_drift": ("-m", "alembic", "check"),
    "postgres_integration_tests": (
        "-m",
        "pytest",
        "-q",
        "-m",
        "postgres",
        "tests/test_postgres_integration.py",
    ),
    "downgrade_to_base": ("-m", "alembic", "downgrade", "base"),
    "restore_upgrade_to_head": ("-m", "alembic", "upgrade", "head"),
    "verify_restored_schema_drift": ("-m", "alembic", "check"),
    "prepare_synthetic_secrets": ("tools/phase2_lab.py", "prepare", "--force"),
    "validate_compose_model": ("tools/phase2_lab.py", "config"),
    "start_synthetic_stack": ("tools/phase2_lab.py", "start"),
    "verify_c50_security_and_health": (
        "tools/phase2_lab.py",
        "verify",
        "--timeout",
        "360",
    ),
    "verify_outage_recovery": (
        "tools/phase2_failure_drill.py",
        "--transition-timeout",
        "60",
    ),
    "stop_and_remove_synthetic_stack": ("tools/phase2_lab.py", "stop"),
}


Executor = Callable[
    [list[str], dict[str, str] | None, float], subprocess.CompletedProcess[str]
]


def _default_executor(
    command: list[str], environment: dict[str, str] | None, timeout: float
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _capture(
    executor: Executor,
    command: list[str],
    *,
    environment: dict[str, str] | None = None,
    timeout: float = 30,
) -> tuple[int | None, str, str, float]:
    started = monotonic()
    try:
        completed = executor(command, environment, timeout)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return None, stdout, stderr or "command timed out", monotonic() - started
    except OSError as exc:
        return None, "", str(exc), monotonic() - started
    return (
        completed.returncode,
        completed.stdout or "",
        completed.stderr or "",
        monotonic() - started,
    )


def _secret_values(database_url: str | None) -> list[str]:
    if not database_url:
        return []
    values = [database_url]
    try:
        password = urlsplit(database_url).password
    except ValueError:
        password = None
    if password:
        values.append(password)
    return sorted(values, key=len, reverse=True)


def _redact(value: str, secret_values: Sequence[str] = ()) -> str:
    redacted = value
    for secret in secret_values:
        if secret:
            redacted = redacted.replace(secret, "[redacted]")
    redacted = _DATABASE_USERINFO.sub(r"\1[redacted]@", redacted)
    return _GITHUB_TOKEN_VALUE.sub("[redacted]", redacted)


def _failure_detail(
    stdout: str, stderr: str, *, secret_values: Sequence[str] = ()
) -> str:
    detail = (stderr.strip() or stdout.strip() or "command failed")[-1500:]
    return _redact(detail, secret_values)


def _canonical_text_sha256(path: Path) -> str | None:
    try:
        content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        return hashlib.sha256(content).hexdigest()
    except OSError:
        return None


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(UTC)


def _source_identity() -> tuple[dict[str, str | None], dict[str, str | None]]:
    contracts = {
        "openapi_sha256": _canonical_text_sha256(
            ROOT / "contracts/phase-2/openapi.json"
        ),
        "database_sha256": _canonical_text_sha256(
            ROOT / "contracts/phase-2/database.json"
        ),
    }
    dependencies = {
        "uv_lock_sha256": _canonical_text_sha256(ROOT / "uv.lock")
    }
    return contracts, dependencies


def _command_matches(name: object, command: object) -> bool:
    if not isinstance(name, str) or not isinstance(command, list) or not command:
        return False
    if not all(isinstance(part, str) for part in command):
        return False
    executable = re.split(r"[\\/]", command[0])[-1].lower()
    if not executable.startswith("python"):
        return False
    expected_tail = _EXPECTED_COMMAND_TAILS.get(name)
    return expected_tail is not None and tuple(command[1:]) == expected_tail


def _artifact_json(path: Path) -> tuple[dict[str, object] | None, list[str]]:
    errors: list[str] = []
    try:
        if path.is_symlink():
            return None, ["evidence artifact must not be a symbolic link"]
        metadata = path.stat()
    except OSError as exc:
        return None, [f"evidence artifact is unavailable: {exc}"]
    if not stat.S_ISREG(metadata.st_mode):
        return None, ["evidence artifact must be a regular file"]
    if metadata.st_size > _MAX_EVIDENCE_BYTES:
        return None, [f"evidence artifact exceeds {_MAX_EVIDENCE_BYTES} bytes"]
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return None, [f"evidence artifact cannot be read as UTF-8: {exc}"]
    try:
        candidate = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"evidence artifact is not valid JSON: {exc.msg}"]
    if not isinstance(candidate, dict):
        errors.append("evidence artifact root must be an object")
        return None, errors
    return candidate, errors


def verify_evidence_artifact(
    path: Path,
    *,
    expected_gate: str | None = None,
    expected_commit: str | None = None,
    now: datetime | None = None,
    max_age_days: int = _DEFAULT_MAX_AGE_DAYS,
) -> dict[str, object]:
    """Validate a generated publication report without executing any gate."""
    errors: list[str] = []
    report, read_errors = _artifact_json(path)
    errors.extend(read_errors)
    if max_age_days < 1:
        errors.append("maximum evidence age must be at least one day")
    if expected_gate is not None and expected_gate not in _EXPECTED_GATE_CHECKS:
        errors.append("expected gate must be P2-G1 or P2-G2")
    normalized_expected_commit = (
        expected_commit.strip().lower() if isinstance(expected_commit, str) else None
    )
    if normalized_expected_commit is not None and not _COMMIT_PATTERN.fullmatch(
        normalized_expected_commit
    ):
        errors.append("expected commit must be a full 40-character Git SHA")

    gate: str | None = None
    commit: str | None = None
    generated_at: str | None = None
    if report is not None:
        if report.get("schema") != SCHEMA:
            errors.append(f"schema must be {SCHEMA}")
        if report.get("kind") != "publication-gate":
            errors.append("kind must be publication-gate")
        candidate_gate = report.get("gate")
        gate = candidate_gate if isinstance(candidate_gate, str) else None
        if gate not in _EXPECTED_GATE_CHECKS:
            errors.append("gate must be P2-G1 or P2-G2")
        elif expected_gate is not None and gate != expected_gate:
            errors.append(f"gate does not match expected {expected_gate}")
        if report.get("status") != "passed":
            errors.append("publication gate status must be passed")
        if report.get("blocked_reasons") != []:
            errors.append("blocked_reasons must be empty")

        generated_value = report.get("generated_at")
        generated_at = generated_value if isinstance(generated_value, str) else None
        observed_at = _parse_timestamp(generated_value)
        current_time = (now or datetime.now(UTC)).astimezone(UTC)
        if observed_at is None:
            errors.append("generated_at must be a timezone-aware ISO timestamp")
        else:
            if observed_at > current_time + _FUTURE_TOLERANCE:
                errors.append("evidence timestamp is in the future")
            if observed_at < current_time - timedelta(days=max_age_days):
                errors.append(f"evidence is older than {max_age_days} days")

        source = report.get("source")
        if not isinstance(source, dict):
            errors.append("source must be an object")
        else:
            candidate_commit = source.get("commit")
            commit = candidate_commit if isinstance(candidate_commit, str) else None
            if commit is None or _COMMIT_PATTERN.fullmatch(commit) is None:
                errors.append("source commit must be a full lowercase Git SHA")
            elif (
                normalized_expected_commit is not None
                and commit != normalized_expected_commit
            ):
                errors.append("source commit does not match the expected commit")
            if source.get("worktree_clean") is not True:
                errors.append("source worktree_clean must be true")
            if source.get("eligible") is not True:
                errors.append("source eligible must be true")
            if source.get("errors") != []:
                errors.append("source errors must be empty")
            if not isinstance(source.get("branch"), str) or not source.get("branch"):
                errors.append("source branch must be recorded")
            contracts = source.get("contracts")
            expected_contracts, expected_dependencies = _source_identity()
            if None in expected_contracts.values():
                errors.append("current Phase 2 contract files are unavailable")
            elif contracts != expected_contracts:
                errors.append("contract hashes do not match the current repository")
            dependencies = source.get("dependencies")
            if None in expected_dependencies.values():
                errors.append("current dependency lock is unavailable")
            elif dependencies != expected_dependencies:
                errors.append(
                    "dependency lock hash does not match the current repository"
                )

        checks = report.get("checks")
        expected_checks = _EXPECTED_GATE_CHECKS.get(gate or "", ())
        if not isinstance(checks, list):
            errors.append("checks must be an array")
        else:
            names = [
                check.get("name") if isinstance(check, dict) else None
                for check in checks
            ]
            if tuple(names) != expected_checks:
                errors.append("checks do not match the required gate sequence")
            for check in checks:
                if not isinstance(check, dict):
                    errors.append("every check must be an object")
                    continue
                if check.get("status") != "passed" or check.get("exit_code") != 0:
                    errors.append(f"check {check.get('name', '<unknown>')} did not pass")
                if not _command_matches(check.get("name"), check.get("command")):
                    errors.append(
                        f"check {check.get('name', '<unknown>')} command is not approved"
                    )
                if check.get("detail") != "completed":
                    errors.append(
                        f"check {check.get('name', '<unknown>')} has incomplete detail"
                    )
                duration = check.get("duration_ms")
                if (
                    isinstance(duration, bool)
                    or not isinstance(duration, int | float)
                    or not math.isfinite(duration)
                    or duration < 0
                ):
                    errors.append(
                        f"check {check.get('name', '<unknown>')} has invalid duration"
                    )

        safety = report.get("safety")
        expected_safety = _EXPECTED_GATE_SAFETY.get(gate or "", {})
        if not isinstance(safety, dict):
            errors.append("safety must be an object")
        else:
            for name, expected_value in expected_safety.items():
                if safety.get(name) is not expected_value:
                    errors.append(f"safety declaration {name} must be {expected_value}")

        if gate == COMPOSE_GATE:
            docker = report.get("docker")
            server = docker.get("server") if isinstance(docker, dict) else None
            if not isinstance(docker, dict) or docker.get("ready") is not True:
                errors.append("Compose evidence requires a ready Docker environment")
            if not isinstance(server, dict) or server.get("os") != "linux":
                errors.append("Compose evidence requires a Docker Linux server")
            if not isinstance(server, dict) or not server.get("version"):
                errors.append("Compose evidence requires a Docker server version")
            if not isinstance(docker, dict) or not docker.get("compose_version"):
                errors.append("Compose evidence requires a Docker Compose version")

        encoded = json.dumps(report, sort_keys=True)
        if (
            _DATABASE_USERINFO.search(encoded)
            or _SENSITIVE_JSON_VALUE.search(encoded)
            or _AUTHORIZATION_VALUE.search(encoded)
        ):
            errors.append("evidence artifact contains a credential-like value")

    return {
        "schema": "hcam.phase2.publication-evidence-verification.v1",
        "kind": "verification",
        "status": "valid" if not errors else "invalid",
        "artifact": str(path),
        "gate": gate,
        "commit": commit,
        "generated_at": generated_at,
        "max_age_days": max_age_days,
        "errors": errors,
        "safety": {
            "executes_gate_commands": False,
            "contacts_cameras": False,
            "captures_images": False,
            "records_video": False,
        },
    }


def source_state(executor: Executor = _default_executor) -> dict[str, object]:
    commit_code, commit_out, commit_err, _ = _capture(
        executor, ["git", "rev-parse", "HEAD"]
    )
    branch_code, branch_out, branch_err, _ = _capture(
        executor, ["git", "branch", "--show-current"]
    )
    status_code, status_out, status_err, _ = _capture(
        executor, ["git", "status", "--porcelain", "--untracked-files=normal"]
    )
    commit = commit_out.strip().lower()
    branch = branch_out.strip()
    if not branch:
        branch = os.environ.get("GITHUB_HEAD_REF", "").strip()
    if not branch:
        branch = os.environ.get("GITHUB_REF_NAME", "").strip()
    errors = [
        item.strip()
        for code, item in (
            (commit_code, commit_err),
            (branch_code, branch_err),
            (status_code, status_err),
        )
        if code != 0 and item.strip()
    ]
    contracts, dependencies = _source_identity()
    if None in contracts.values():
        errors.append("required Phase 2 contract identity files are unavailable")
    if None in dependencies.values():
        errors.append("required dependency lock uv.lock is unavailable")
    valid_commit = commit_code == 0 and _COMMIT_PATTERN.fullmatch(commit) is not None
    clean = status_code == 0 and not status_out.strip()
    valid_branch = bool(branch) and len(branch) <= 255 and not any(
        character in branch for character in "\r\n\0"
    )
    return {
        "commit": commit if valid_commit else None,
        "branch": branch if branch_code == 0 and valid_branch else None,
        "worktree_clean": clean,
        "eligible": valid_commit and valid_branch and clean and not errors,
        "errors": [_redact(item) for item in errors],
        "contracts": contracts,
        "dependencies": dependencies,
    }


def _github_api_json(
    endpoint: str,
    *,
    executor: Executor,
) -> tuple[dict[str, object] | None, str | None]:
    command = [
        "gh",
        "api",
        "-H",
        "Accept: application/vnd.github+json",
        "-H",
        f"X-GitHub-Api-Version: {_GITHUB_API_VERSION}",
        endpoint,
    ]
    code, stdout, stderr, _ = _capture(executor, command, timeout=30)
    if code != 0:
        return None, _failure_detail(stdout, stderr)
    try:
        candidate = json.loads(stdout)
    except json.JSONDecodeError:
        return None, "GitHub API returned invalid JSON"
    if not isinstance(candidate, dict):
        return None, "GitHub API response must be an object"
    return candidate, None


def _github_verification_report(
    *,
    status: str,
    gate: str | None,
    expected_commit: str | None,
    source: dict[str, object],
    run: dict[str, object] | None = None,
    job: dict[str, object] | None = None,
    artifact: dict[str, object] | None = None,
    payload: dict[str, object] | None = None,
    errors: Sequence[str] = (),
    blocked_reasons: Sequence[str] = (),
) -> dict[str, object]:
    return {
        "schema": "hcam.phase2.github-run-verification.v1",
        "kind": "github-run-verification",
        "status": status,
        "gate": gate,
        "expected_commit": expected_commit,
        "verified_at": datetime.now(UTC).isoformat(),
        "source": source,
        "run": run,
        "job": job,
        "artifact": artifact,
        "payload": payload,
        "errors": list(errors),
        "blocked_reasons": list(blocked_reasons),
        "safety": {
            "github_read_only": True,
            "downloads_to_temporary_directory": True,
            "retains_downloaded_artifact": False,
            "reads_action_logs": False,
            "contacts_cameras": False,
            "captures_images": False,
            "records_video": False,
        },
    }


def _downloaded_artifact_payload(
    directory: Path,
    expected_filename: str,
) -> tuple[Path | None, list[str]]:
    errors: list[str] = []
    files: list[Path] = []
    for parent, directories, filenames in os.walk(directory, followlinks=False):
        parent_path = Path(parent)
        for name in [*directories, *filenames]:
            candidate = parent_path / name
            if candidate.is_symlink():
                errors.append("downloaded artifact must not contain symbolic links")
        for name in filenames:
            candidate = parent_path / name
            if candidate.is_file() and not candidate.is_symlink():
                files.append(candidate)
    expected = directory / expected_filename
    if not expected.is_file() or expected.is_symlink():
        errors.append(f"downloaded artifact must contain {expected_filename} at its root")
    if len(files) != 1 or (files and files[0].resolve() != expected.resolve()):
        errors.append("downloaded artifact must contain exactly one expected JSON file")
    return (expected if not errors else None), errors


def verify_github_run(
    run_url: str,
    *,
    expected_gate: str,
    expected_commit: str,
    executor: Executor = _default_executor,
    now: datetime | None = None,
    max_age_days: int = _DEFAULT_MAX_AGE_DAYS,
) -> dict[str, object]:
    """Verify a GitHub Actions run and its publication artifact read-only."""
    errors: list[str] = []
    blocked_reasons: list[str] = []
    gate = expected_gate if expected_gate in _EXPECTED_GATE_CHECKS else None
    commit = expected_commit.strip().lower()
    url_match = _ACTIONS_RUN_URL.fullmatch(run_url.strip())
    run_id = int(url_match.group("run_id")) if url_match is not None else None
    source = source_state(executor)
    current_time = (now or datetime.now(UTC)).astimezone(UTC)

    if gate is None:
        errors.append("expected gate must be P2-G1 or P2-G2")
    if _COMMIT_PATTERN.fullmatch(commit) is None:
        errors.append("expected commit must be a full lowercase Git SHA")
    if run_id is None:
        errors.append(f"run URL must identify an Actions run in {REPOSITORY}")
    if max_age_days < 1:
        errors.append("maximum evidence age must be at least one day")
    if source.get("eligible") is not True:
        blocked_reasons.append("verification requires a clean committed worktree")
    elif source.get("commit") != commit:
        blocked_reasons.append("local HEAD must equal the expected commit")
    if errors or blocked_reasons:
        return _github_verification_report(
            status="blocked" if blocked_reasons and not errors else "invalid",
            gate=gate,
            expected_commit=commit or None,
            source=source,
            errors=errors,
            blocked_reasons=blocked_reasons,
        )

    assert run_id is not None
    assert gate is not None
    run_response, api_error = _github_api_json(
        f"repos/{REPOSITORY}/actions/runs/{run_id}", executor=executor
    )
    if api_error is not None or run_response is None:
        return _github_verification_report(
            status="blocked",
            gate=gate,
            expected_commit=commit,
            source=source,
            blocked_reasons=[f"GitHub run query failed: {api_error or 'unknown error'}"],
        )

    repository = run_response.get("repository")
    run_started_at = _parse_timestamp(run_response.get("run_started_at"))
    expected_run_url = f"https://github.com/{REPOSITORY}/actions/runs/{run_id}"
    run_summary = {
        "id": run_response.get("id"),
        "url": run_response.get("html_url"),
        "workflow": run_response.get("name"),
        "workflow_path": run_response.get("path"),
        "event": run_response.get("event"),
        "attempt": run_response.get("run_attempt"),
        "status": run_response.get("status"),
        "conclusion": run_response.get("conclusion"),
        "head_branch": run_response.get("head_branch"),
        "head_sha": run_response.get("head_sha"),
        "started_at": run_response.get("run_started_at"),
    }
    if run_response.get("id") != run_id:
        errors.append("GitHub run ID does not match the linked run")
    if run_response.get("html_url") != expected_run_url:
        errors.append("GitHub run URL does not match the expected repository")
    if not isinstance(repository, dict) or repository.get("full_name") != REPOSITORY:
        errors.append("GitHub run repository does not match H-CAM")
    if run_response.get("name") != _WORKFLOW_NAME:
        errors.append(f"GitHub run workflow must be {_WORKFLOW_NAME}")
    if run_response.get("path") != _WORKFLOW_PATH:
        errors.append(f"GitHub run workflow path must be {_WORKFLOW_PATH}")
    if run_response.get("status") != "completed" or run_response.get("conclusion") != "success":
        errors.append("GitHub run must be completed successfully")
    if run_response.get("head_sha") != commit:
        errors.append("GitHub run head SHA does not match the expected commit")
    if run_response.get("event") not in {"pull_request", "push", "workflow_dispatch"}:
        errors.append("GitHub run event is not approved for publication evidence")
    if (
        isinstance(run_response.get("run_attempt"), bool)
        or not isinstance(run_response.get("run_attempt"), int)
        or run_response["run_attempt"] < 1
    ):
        errors.append("GitHub run attempt is invalid")
    if run_started_at is None:
        errors.append("GitHub run start time is invalid")
    elif run_started_at > current_time + _FUTURE_TOLERANCE:
        errors.append("GitHub run start time is in the future")
    elif run_started_at < current_time - timedelta(days=max_age_days):
        errors.append(f"GitHub run is older than {max_age_days} days")
    if errors:
        return _github_verification_report(
            status="invalid",
            gate=gate,
            expected_commit=commit,
            source=source,
            run=run_summary,
            errors=errors,
        )

    jobs_response, api_error = _github_api_json(
        f"repos/{REPOSITORY}/actions/runs/{run_id}/jobs?filter=latest&per_page=100",
        executor=executor,
    )
    if api_error is not None or jobs_response is None:
        return _github_verification_report(
            status="blocked",
            gate=gate,
            expected_commit=commit,
            source=source,
            run=run_summary,
            blocked_reasons=[f"GitHub jobs query failed: {api_error or 'unknown error'}"],
        )
    jobs = jobs_response.get("jobs")
    expected_job_name = _EXPECTED_GITHUB_JOBS[gate]
    matching_jobs = (
        [item for item in jobs if isinstance(item, dict) and item.get("name") == expected_job_name]
        if isinstance(jobs, list)
        else []
    )
    job_summary: dict[str, object] | None = None
    if len(matching_jobs) != 1:
        errors.append(f"GitHub run must contain exactly one {expected_job_name} job")
    else:
        selected_job = matching_jobs[0]
        job_summary = {
            "id": selected_job.get("id"),
            "name": selected_job.get("name"),
            "status": selected_job.get("status"),
            "conclusion": selected_job.get("conclusion"),
            "url": selected_job.get("html_url"),
        }
        expected_job_url_prefix = f"{expected_run_url}/job/"
        if (
            isinstance(selected_job.get("id"), bool)
            or not isinstance(selected_job.get("id"), int)
            or selected_job["id"] < 1
        ):
            errors.append(f"GitHub job {expected_job_name} ID is invalid")
        if not str(selected_job.get("html_url", "")).startswith(
            expected_job_url_prefix
        ):
            errors.append(f"GitHub job {expected_job_name} URL is invalid")
        if selected_job.get("status") != "completed" or selected_job.get("conclusion") != "success":
            errors.append(f"GitHub job {expected_job_name} must complete successfully")
    if errors:
        return _github_verification_report(
            status="invalid",
            gate=gate,
            expected_commit=commit,
            source=source,
            run=run_summary,
            job=job_summary,
            errors=errors,
        )

    artifacts_response, api_error = _github_api_json(
        f"repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100",
        executor=executor,
    )
    if api_error is not None or artifacts_response is None:
        return _github_verification_report(
            status="blocked",
            gate=gate,
            expected_commit=commit,
            source=source,
            run=run_summary,
            job=job_summary,
            blocked_reasons=[f"GitHub artifacts query failed: {api_error or 'unknown error'}"],
        )
    expected_artifact_name = f"phase2-{gate.lower()}-{commit}"
    artifacts = artifacts_response.get("artifacts")
    matching_artifacts = (
        [
            item
            for item in artifacts
            if isinstance(item, dict) and item.get("name") == expected_artifact_name
        ]
        if isinstance(artifacts, list)
        else []
    )
    artifact_summary: dict[str, object] | None = None
    if len(matching_artifacts) != 1:
        errors.append("GitHub run must contain exactly one commit-named gate artifact")
    else:
        selected_artifact = matching_artifacts[0]
        workflow_run = selected_artifact.get("workflow_run")
        created_at = _parse_timestamp(selected_artifact.get("created_at"))
        expires_at = _parse_timestamp(selected_artifact.get("expires_at"))
        digest = selected_artifact.get("digest")
        size = selected_artifact.get("size_in_bytes")
        artifact_summary = {
            "id": selected_artifact.get("id"),
            "name": selected_artifact.get("name"),
            "size_in_bytes": size,
            "digest": digest,
            "expired": selected_artifact.get("expired"),
            "created_at": selected_artifact.get("created_at"),
            "expires_at": selected_artifact.get("expires_at"),
        }
        if (
            isinstance(selected_artifact.get("id"), bool)
            or not isinstance(selected_artifact.get("id"), int)
            or selected_artifact["id"] < 1
        ):
            errors.append("GitHub publication artifact ID is invalid")
        if selected_artifact.get("expired") is not False:
            errors.append("GitHub publication artifact is expired")
        if (
            isinstance(size, bool)
            or not isinstance(size, int)
            or not 0 < size <= _MAX_EVIDENCE_BYTES
        ):
            errors.append("GitHub publication artifact size is invalid")
        if not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
            errors.append("GitHub publication artifact digest is invalid")
        if not isinstance(workflow_run, dict) or workflow_run.get("id") != run_id:
            errors.append("GitHub artifact is not bound to the linked run")
        if not isinstance(workflow_run, dict) or workflow_run.get("head_sha") != commit:
            errors.append("GitHub artifact head SHA does not match the expected commit")
        if created_at is None or run_started_at is None:
            errors.append("GitHub artifact creation time is invalid")
        elif created_at + _FUTURE_TOLERANCE < run_started_at:
            errors.append("GitHub artifact predates the workflow run attempt")
        elif created_at > current_time + _FUTURE_TOLERANCE:
            errors.append("GitHub artifact creation time is in the future")
        if expires_at is None or expires_at <= current_time:
            errors.append("GitHub artifact expiry time is invalid or elapsed")
    if errors:
        return _github_verification_report(
            status="invalid",
            gate=gate,
            expected_commit=commit,
            source=source,
            run=run_summary,
            job=job_summary,
            artifact=artifact_summary,
            errors=errors,
        )

    payload_summary: dict[str, object] | None = None
    with tempfile.TemporaryDirectory(prefix="hcam-phase2-github-evidence-") as temporary:
        command = [
            "gh",
            "run",
            "download",
            str(run_id),
            "--repo",
            REPOSITORY,
            "--name",
            expected_artifact_name,
            "--dir",
            temporary,
        ]
        code, stdout, stderr, _ = _capture(executor, command, timeout=120)
        if code != 0:
            blocked_reasons.append(
                f"GitHub artifact download failed: {_failure_detail(stdout, stderr)}"
            )
        else:
            payload_path, payload_errors = _downloaded_artifact_payload(
                Path(temporary), _EXPECTED_ARTIFACT_PAYLOADS[gate]
            )
            errors.extend(payload_errors)
            if payload_path is not None:
                payload_summary = verify_evidence_artifact(
                    payload_path,
                    expected_gate=gate,
                    expected_commit=commit,
                    now=current_time,
                    max_age_days=max_age_days,
                )
                if payload_summary.get("status") != "valid":
                    payload_errors = payload_summary.get("errors")
                    if isinstance(payload_errors, list):
                        errors.extend(
                            f"artifact payload: {item}" for item in payload_errors
                        )
                    else:
                        errors.append("artifact payload verification failed")

    status = "blocked" if blocked_reasons else "invalid" if errors else "valid"
    return _github_verification_report(
        status=status,
        gate=gate,
        expected_commit=commit,
        source=source,
        run=run_summary,
        job=job_summary,
        artifact=artifact_summary,
        payload=payload_summary,
        errors=errors,
        blocked_reasons=blocked_reasons,
    )


def docker_state(executor: Executor = _default_executor) -> dict[str, object]:
    code, stdout, stderr, _ = _capture(
        executor,
        ["docker", "version", "--format", "{{json .Server}}"],
        timeout=30,
    )
    parsed_server: dict[str, object] | None = None
    server: dict[str, object] | None = None
    if code == 0:
        try:
            candidate = json.loads(stdout.strip())
        except json.JSONDecodeError:
            candidate = None
        if isinstance(candidate, dict) and candidate.get("Version"):
            parsed_server = candidate
            if candidate.get("Os") == "linux":
                server = candidate
    compose_code, compose_out, compose_err, _ = _capture(
        executor, ["docker", "compose", "version", "--short"], timeout=30
    )
    compose_version = compose_out.strip() if compose_code == 0 else ""
    ready = server is not None and bool(compose_version)
    details: list[str] = []
    if server is None:
        if parsed_server is not None:
            details.append("Docker server OS must be linux")
        else:
            details.append(
                _failure_detail(
                    stdout,
                    stderr,
                )
                if stdout.strip() or stderr.strip()
                else "Docker returned no structured server data"
            )
    if not compose_version:
        details.append(
            _failure_detail(compose_out, compose_err)
            if compose_out.strip() or compose_err.strip()
            else "Docker Compose version is unavailable"
        )
    return {
        "ready": ready,
        "server": (
            {
                "version": server.get("Version"),
                "os": server.get("Os"),
                "arch": server.get("Arch"),
            }
            if server is not None
            else None
        ),
        "compose_version": compose_version or None,
        "detail": "; ".join(details) if details else None,
    }


def postgres_state(environment: dict[str, str] | None = None) -> dict[str, object]:
    resolved = environment if environment is not None else os.environ
    database_url = resolved.get("HCAM_POSTGRES_TEST_URL", "").strip()
    valid = database_url.startswith("postgresql+psycopg://")
    return {
        "configured": bool(database_url),
        "valid_test_scheme": valid,
        "ready": bool(database_url) and valid,
    }


def github_state(
    branch: str | None, executor: Executor = _default_executor
) -> dict[str, object]:
    auth_code, _auth_out, auth_err, _ = _capture(
        executor, ["gh", "auth", "status"], timeout=20
    )
    if auth_code != 0 or not branch:
        return {
            "authenticated": False,
            "pull_requests": [],
            "detail": _redact(auth_err.strip()) if auth_err.strip() else None,
        }
    code, stdout, stderr, _ = _capture(
        executor,
        [
            "gh",
            "pr",
            "list",
            "--repo",
            REPOSITORY,
            "--state",
            "all",
            "--head",
            branch,
            "--json",
            "number,state,url",
        ],
        timeout=30,
    )
    pull_requests: list[object] = []
    if code == 0:
        try:
            candidate = json.loads(stdout)
        except json.JSONDecodeError:
            candidate = None
        if isinstance(candidate, list):
            pull_requests = candidate
    return {
        "authenticated": True,
        "pull_requests": pull_requests,
        "detail": (
            _failure_detail(stdout, stderr) if code != 0 else None
        ),
    }


def preflight_report(
    *,
    executor: Executor = _default_executor,
    environment: dict[str, str] | None = None,
    include_github: bool = True,
) -> dict[str, object]:
    source = source_state(executor)
    postgres = postgres_state(environment)
    docker = docker_state(executor)
    github = (
        github_state(source.get("branch") if isinstance(source.get("branch"), str) else None, executor)
        if include_github
        else {"authenticated": None, "pull_requests": [], "detail": "not checked"}
    )
    gates = {
        POSTGRES_GATE: {
            "status": "ready" if source["eligible"] and postgres["ready"] else "blocked",
            "requires": ["clean_commit", "HCAM_POSTGRES_TEST_URL"],
        },
        COMPOSE_GATE: {
            "status": "ready" if source["eligible"] and docker["ready"] else "blocked",
            "requires": ["clean_commit", "docker_linux_server", "docker_compose"],
        },
        "P2-G3": {
            "status": "pending" if not github["pull_requests"] else "review",
            "requires": ["reviewable_pull_request", "green_required_checks"],
        },
        "P2-G4": {
            "status": "pending",
            "requires": ["explicit_owner_acceptance"],
        },
    }
    ready = all(gates[gate]["status"] == "ready" for gate in (POSTGRES_GATE, COMPOSE_GATE))
    return {
        "schema": SCHEMA,
        "kind": "preflight",
        "status": "ready" if ready else "blocked",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": source,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "postgres": postgres,
            "docker": docker,
            "github": github,
        },
        "gates": gates,
        "safety": {
            "contacts_cameras": False,
            "captures_images": False,
            "records_video": False,
            "changes_system_services": False,
        },
    }


def _run_step(
    name: str,
    command: list[str],
    *,
    executor: Executor,
    environment: dict[str, str] | None,
    timeout: float,
    secret_values: Sequence[str] = (),
) -> dict[str, object]:
    code, stdout, stderr, duration = _capture(
        executor,
        command,
        environment=environment,
        timeout=timeout,
    )
    return {
        "name": name,
        "status": "passed" if code == 0 else "failed",
        "command": command,
        "exit_code": code,
        "duration_ms": round(duration * 1000, 3),
        "detail": (
            "completed"
            if code == 0
            else _failure_detail(stdout, stderr, secret_values=secret_values)
        ),
    }


def _blocked_report(
    gate: str,
    source: dict[str, object],
    reasons: list[str],
    *,
    safety: dict[str, bool],
) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "kind": "publication-gate",
        "gate": gate,
        "status": "blocked",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": source,
        "checks": [],
        "blocked_reasons": reasons,
        "safety": safety,
    }


def run_postgres_gate(
    *,
    confirmed_disposable: bool,
    executor: Executor = _default_executor,
    environment: dict[str, str] | None = None,
) -> dict[str, object]:
    resolved = dict(environment if environment is not None else os.environ)
    source = source_state(executor)
    database_url = resolved.get("HCAM_POSTGRES_TEST_URL", "").strip()
    postgres = postgres_state(resolved)
    reasons: list[str] = []
    if not source["eligible"]:
        reasons.append("publication evidence requires a clean committed worktree")
    if not confirmed_disposable:
        reasons.append("--confirm-disposable-database is required")
    if not postgres["ready"]:
        reasons.append("HCAM_POSTGRES_TEST_URL must be a PostgreSQL test URL")
    safety = {
        "uses_only_postgres_test_url": True,
        "requires_disposable_confirmation": True,
        "contacts_cameras": False,
        "captures_images": False,
        "records_video": False,
    }
    if reasons:
        return _blocked_report(POSTGRES_GATE, source, reasons, safety=safety)

    resolved["HCAM_DATABASE_URL"] = database_url
    secrets = _secret_values(database_url)
    commands = [
        (
            "verify_postgres_18",
            [sys.executable, "-c", _POSTGRES_VERSION_COMMAND],
            60,
        ),
        ("upgrade_to_head", [sys.executable, "-m", "alembic", "upgrade", "head"], 180),
        ("verify_schema_drift", [sys.executable, "-m", "alembic", "check"], 120),
        (
            "postgres_integration_tests",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-m",
                "postgres",
                "tests/test_postgres_integration.py",
            ],
            600,
        ),
    ]
    checks: list[dict[str, object]] = []
    for name, command, timeout in commands:
        check = _run_step(
            name,
            command,
            executor=executor,
            environment=resolved,
            timeout=timeout,
            secret_values=secrets,
        )
        checks.append(check)
        if check["status"] != "passed":
            break

    if all(check["status"] == "passed" for check in checks) and len(checks) == len(commands):
        downgrade = _run_step(
            "downgrade_to_base",
            [sys.executable, "-m", "alembic", "downgrade", "base"],
            executor=executor,
            environment=resolved,
            timeout=180,
            secret_values=secrets,
        )
        checks.append(downgrade)
        restore = _run_step(
            "restore_upgrade_to_head",
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            executor=executor,
            environment=resolved,
            timeout=180,
            secret_values=secrets,
        )
        checks.append(restore)
        restored_check = _run_step(
            "verify_restored_schema_drift",
            [sys.executable, "-m", "alembic", "check"],
            executor=executor,
            environment=resolved,
            timeout=120,
            secret_values=secrets,
        )
        checks.append(restored_check)

    passed = len(checks) == 7 and all(check["status"] == "passed" for check in checks)
    return {
        "schema": SCHEMA,
        "kind": "publication-gate",
        "gate": POSTGRES_GATE,
        "status": "passed" if passed else "failed",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": source,
        "checks": checks,
        "blocked_reasons": [],
        "safety": safety,
    }


def run_compose_gate(
    *,
    confirmed_synthetic: bool,
    executor: Executor = _default_executor,
    environment: dict[str, str] | None = None,
) -> dict[str, object]:
    resolved = dict(environment if environment is not None else os.environ)
    source = source_state(executor)
    docker = docker_state(executor)
    reasons: list[str] = []
    if not source["eligible"]:
        reasons.append("publication evidence requires a clean committed worktree")
    if not confirmed_synthetic:
        reasons.append("--confirm-synthetic-lab is required")
    if not docker["ready"]:
        reasons.append("a structured Docker Linux server and Compose are required")
    safety = {
        "synthetic_lab_only": True,
        "contacts_cameras": False,
        "captures_images": False,
        "records_video": False,
        "stops_stack_after_start_attempt": True,
    }
    if reasons:
        report = _blocked_report(COMPOSE_GATE, source, reasons, safety=safety)
        report["docker"] = docker
        return report

    commands = [
        (
            "prepare_synthetic_secrets",
            [sys.executable, "tools/phase2_lab.py", "prepare", "--force"],
            60,
        ),
        (
            "validate_compose_model",
            [sys.executable, "tools/phase2_lab.py", "config"],
            120,
        ),
        (
            "start_synthetic_stack",
            [sys.executable, "tools/phase2_lab.py", "start"],
            900,
        ),
        (
            "verify_c50_security_and_health",
            [sys.executable, "tools/phase2_lab.py", "verify", "--timeout", "360"],
            600,
        ),
        (
            "verify_outage_recovery",
            [
                sys.executable,
                "tools/phase2_failure_drill.py",
                "--transition-timeout",
                "60",
            ],
            600,
        ),
    ]
    checks: list[dict[str, object]] = []
    start_attempted = False
    for name, command, timeout in commands:
        if name == "start_synthetic_stack":
            start_attempted = True
        check = _run_step(
            name,
            command,
            executor=executor,
            environment=resolved,
            timeout=timeout,
        )
        checks.append(check)
        if check["status"] != "passed":
            break
    if start_attempted:
        checks.append(
            _run_step(
                "stop_and_remove_synthetic_stack",
                [sys.executable, "tools/phase2_lab.py", "stop"],
                executor=executor,
                environment=resolved,
                timeout=300,
            )
        )
    expected_checks = 6
    passed = (
        len(checks) == expected_checks
        and all(check["status"] == "passed" for check in checks)
    )
    return {
        "schema": SCHEMA,
        "kind": "publication-gate",
        "gate": COMPOSE_GATE,
        "status": "passed" if passed else "failed",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": source,
        "docker": docker,
        "checks": checks,
        "blocked_reasons": [],
        "safety": safety,
    }


def _default_output(gate: str) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_gate = gate.lower().replace("-", "_")
    return ROOT / "var" / "evidence" / f"phase2_{safe_gate}_{timestamp}.json"


def _write_report(report: dict[str, object], output: Path | None) -> None:
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output is not None:
        resolved = output.resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate sanitized, source-bound Phase 2 publication evidence"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight = subparsers.add_parser("preflight", help="inspect publication prerequisites")
    preflight.add_argument("--output", type=Path)
    preflight.add_argument("--skip-github", action="store_true")
    preflight.add_argument("--strict", action="store_true")

    postgres = subparsers.add_parser(
        "postgres", help="run the disposable PostgreSQL 18 publication gate"
    )
    postgres.add_argument("--confirm-disposable-database", action="store_true")
    postgres.add_argument("--output", type=Path)

    compose = subparsers.add_parser(
        "compose", help="run the synthetic-only Compose publication gate"
    )
    compose.add_argument("--confirm-synthetic-lab", action="store_true")
    compose.add_argument("--output", type=Path)

    verify = subparsers.add_parser(
        "verify", help="validate an existing publication evidence artifact"
    )
    verify.add_argument("artifact", type=Path)
    verify.add_argument("--gate", choices=(POSTGRES_GATE, COMPOSE_GATE), required=True)
    verify.add_argument("--expected-commit")
    verify.add_argument("--max-age-days", type=int, default=_DEFAULT_MAX_AGE_DAYS)

    verify_run = subparsers.add_parser(
        "verify-run", help="verify a GitHub Actions run and gate artifact"
    )
    verify_run.add_argument("run_url")
    verify_run.add_argument(
        "--gate", choices=(POSTGRES_GATE, COMPOSE_GATE), required=True
    )
    verify_run.add_argument("--expected-commit", required=True)
    verify_run.add_argument("--max-age-days", type=int, default=_DEFAULT_MAX_AGE_DAYS)
    verify_run.add_argument("--output", type=Path)
    return parser


def _exit_code(report: dict[str, object]) -> int:
    status = report.get("status")
    if status in {"ready", "passed"}:
        return 0
    if status == "blocked":
        return BLOCKED
    return FAILED


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "preflight":
        report = preflight_report(include_github=not args.skip_github)
        _write_report(report, args.output)
        return _exit_code(report) if args.strict else 0
    if args.command == "postgres":
        report = run_postgres_gate(
            confirmed_disposable=args.confirm_disposable_database
        )
        _write_report(report, args.output or _default_output(POSTGRES_GATE))
        return _exit_code(report)
    if args.command == "compose":
        report = run_compose_gate(confirmed_synthetic=args.confirm_synthetic_lab)
        _write_report(report, args.output or _default_output(COMPOSE_GATE))
        return _exit_code(report)
    if args.command == "verify-run":
        report = verify_github_run(
            args.run_url,
            expected_gate=args.gate,
            expected_commit=args.expected_commit,
            max_age_days=args.max_age_days,
        )
        _write_report(report, args.output)
        return 0 if report["status"] == "valid" else _exit_code(report)
    report = verify_evidence_artifact(
        args.artifact,
        expected_gate=args.gate,
        expected_commit=args.expected_commit,
        max_age_days=args.max_age_days,
    )
    _write_report(report, None)
    return 0 if report["status"] == "valid" else FAILED


if __name__ == "__main__":
    raise SystemExit(main())
