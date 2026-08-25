#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from phase2_publication_evidence import verify_evidence_artifact
except ModuleNotFoundError:
    from tools.phase2_publication_evidence import verify_evidence_artifact


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_COMMAND_TIMEOUT_SECONDS = 600
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"
PUBLICATION_GATE_IDS = ("P2-G1", "P2-G2", "P2-G3", "P2-G4")
_PUBLICATION_GATE_PATTERN = re.compile(
    r"^- \[(?P<mark>[ xX])\] `(?P<gate_id>P2-G\d+)` (?P<title>.+)$",
    re.MULTILINE,
)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+)\)")
_ACTIONS_RUN_URL_PATTERN = re.compile(
    r"^https://github\.com/mayankthakor227/h-cam-2\.0/actions/runs/[1-9]\d*/?$"
)
_PULL_REQUEST_URL_PATTERN = re.compile(
    r"^https://github\.com/mayankthakor227/h-cam-2\.0/pull/\d+"
    r"(?:/(?:checks|commits|files))?(?:\?[^#\s]*)?(?:#[^\s]*)?$"
)

REQUIRED_FILES = [
    "uv.lock",
    "app/hcam/streams/models.py",
    "app/hcam/streams/schemas.py",
    "app/hcam/streams/repository.py",
    "app/hcam/streams/service.py",
    "app/hcam/streams/routes.py",
    "app/hcam/streams/network.py",
    "app/hcam/streams/probe.py",
    "app/hcam/streams/worker.py",
    "app/hcam/streams/onvif.py",
    "app/hcam/streams/onvif_operations.py",
    "app/hcam/streams/onvif_discovery.py",
    "app/hcam/streams/onvif_simulator.py",
    "app/hcam/streams/capabilities.py",
    "app/hcam/streams/capability_worker.py",
    "app/hcam/streams/secrets.py",
    "app/hcam/streams/outbox.py",
    "app/hcam/streams/playback.py",
    "app/hcam/streams/lab.py",
    "app/hcam/streams/lab_publisher.py",
    "migrations/versions/0004_stream_management.py",
    "migrations/versions/0005_playback_sessions.py",
    "migrations/versions/0006_onvif_capability_management.py",
    "migrations/versions/0007_onvif_operations.py",
    "contracts/phase-2/README.md",
    "contracts/phase-2/openapi.json",
    "contracts/phase-2/database.json",
    "deploy/compose.phase2.yaml",
    "deploy/mediamtx.phase2.yml",
    "deploy/onvif-egress.phase2.json",
    "deploy/observability/hcam-phase2-streams.json",
    "deploy/observability/hcam-phase2-alerts.yml",
    "tools/phase2_lab.py",
    "tools/phase2_failure_drill.py",
    "tools/phase2_private_camera.py",
    "tools/phase2_publication_evidence.py",
    "tools/phase2_readiness.py",
    "tools/release_contracts.py",
    "docs/phase-2/README.md",
    "docs/phase-2/architecture-and-contracts.md",
    "docs/phase-2/adapters-and-health.md",
    "docs/phase-2/capability-management.md",
    "docs/phase-2/onvif-operations.md",
    "docs/phase-2/private-camera-validation.md",
    "docs/phase-2/publication-evidence.md",
    "docs/phase-2/playback-security.md",
    "docs/phase-2/synthetic-lab.md",
    "docs/phase-2/operations-and-observability.md",
    "docs/phase-2/safety-and-governance.md",
    "docs/phase-2/build-and-test.md",
    "docs/phase-2/acceptance-checklist.md",
    "docs/phase-2/extension-publication-checklist.md",
    "docs/phase-2/readiness-report.md",
    "docs/phase-2/owner-review.md",
    "tests/test_stream_management_api.py",
    "tests/test_stream_migration.py",
    "tests/test_stream_probe.py",
    "tests/test_stream_worker.py",
    "tests/test_stream_outbox.py",
    "tests/test_onvif_simulator.py",
    "tests/test_authenticated_onvif.py",
    "tests/test_onvif_operations.py",
    "tests/test_onvif_discovery.py",
    "tests/test_capability_management.py",
    "tests/test_capability_security.py",
    "tests/test_postgres_integration.py",
    "tests/test_playback_sessions.py",
    "tests/test_phase2_lab.py",
    "tests/test_phase2_publication_ci.py",
    "tests/test_phase2_publication_evidence.py",
    "tests/test_phase2_readiness.py",
    "tests/test_release_contracts.py",
]


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str
    evidence: list[str]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _contract_check(name: str, files: list[str], terms: list[str]) -> Check:
    content = "\n".join(_read(path) for path in files)
    missing = [term for term in terms if term not in content]
    if missing:
        return Check(name, FAIL, f"missing terms: {', '.join(missing)}", files)
    return Check(name, PASS, "Required contracts are present.", files)


def check_files() -> Check:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        return Check("required_files", FAIL, f"missing: {', '.join(missing)}", missing)
    return Check(
        "required_files",
        PASS,
        f"{len(REQUIRED_FILES)} Phase 2 implementation and evidence files are present.",
        REQUIRED_FILES,
    )


def check_acceptance() -> Check:
    path = "docs/phase-2/acceptance-checklist.md"
    unchecked = re.findall(r"^- \[ \] (.+)$", _read(path), re.MULTILINE)
    if unchecked == [
        "Owner reviews the Phase 2 evidence and explicitly accepts or rejects it"
    ]:
        return Check(
            "owner_gate",
            MANUAL,
            "Explicit Phase 2 owner acceptance is pending.",
            [path],
        )
    if unchecked:
        return Check(
            "owner_gate", FAIL, "Unexpected incomplete checklist items.", unchecked
        )
    return Check("owner_gate", PASS, "Owner gate is accepted.", [path])


def _current_head() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    commit = completed.stdout.strip().lower()
    if completed.returncode != 0 or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        return None
    return commit


def _remote_evidence_error(gate_id: str, target: str) -> str | None:
    if gate_id in {"P2-G1", "P2-G2"}:
        if _ACTIONS_RUN_URL_PATTERN.fullmatch(target) is None:
            return f"{gate_id} HTTPS evidence must link this repository's Actions run"
        return None
    if gate_id in {"P2-G3", "P2-G4"}:
        if _PULL_REQUEST_URL_PATTERN.fullmatch(target) is None:
            return f"{gate_id} HTTPS evidence must link this repository's pull request"
        return None
    return f"{gate_id} is not a recognized publication gate"


def _local_evidence_error(gate_id: str, candidate: Path) -> str | None:
    if gate_id in {"P2-G1", "P2-G2"}:
        if candidate.suffix.lower() != ".json":
            return f"{gate_id} local evidence must be a JSON publication artifact"
        head = _current_head()
        if head is None:
            return f"{gate_id} cannot resolve the current Git commit"
        verification = verify_evidence_artifact(
            candidate,
            expected_gate=gate_id,
            expected_commit=head,
        )
        if verification["status"] != "valid":
            errors = verification.get("errors")
            detail = errors[0] if isinstance(errors, list) and errors else "verification failed"
            return f"{gate_id} publication artifact is invalid: {detail}"
        return None
    if gate_id == "P2-G3":
        return "P2-G3 evidence must link this repository's pull request"
    expected_owner_review = (ROOT / "docs/phase-2/owner-review.md").resolve()
    if gate_id == "P2-G4" and candidate != expected_owner_review:
        return "P2-G4 local evidence must link owner-review.md"
    return None


def check_extension_publication() -> Check:
    path = "docs/phase-2/extension-publication-checklist.md"
    content = _read(path)
    status_match = re.search(r"^Status: `(?P<status>[^`]+)`$", content, re.MULTILINE)
    matches = list(_PUBLICATION_GATE_PATTERN.finditer(content))
    gate_ids = [match.group("gate_id") for match in matches]
    structural_errors: list[str] = []
    if gate_ids != list(PUBLICATION_GATE_IDS):
        structural_errors.append(
            "publication gates must appear exactly once and in order: "
            + ", ".join(PUBLICATION_GATE_IDS)
        )

    gates: list[tuple[str, bool, str, str | None]] = []
    for index, match in enumerate(matches):
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        block = content[match.end() : block_end]
        evidence_match = re.search(r"^  Evidence: (?P<evidence>.+)$", block, re.MULTILINE)
        evidence = evidence_match.group("evidence").strip() if evidence_match else None
        if evidence is None:
            structural_errors.append(f"{match.group('gate_id')} is missing Evidence")
        gates.append(
            (
                match.group("gate_id"),
                match.group("mark").lower() == "x",
                match.group("title").strip(),
                evidence,
            )
        )

    invalid_evidence: list[str] = []
    for gate_id, checked, _title, evidence in gates:
        if not checked:
            continue
        if evidence is None or evidence == "`pending`":
            invalid_evidence.append(f"{gate_id} has no completed evidence reference")
            continue
        targets = [item.group("target").strip() for item in _MARKDOWN_LINK_PATTERN.finditer(evidence)]
        if not targets:
            invalid_evidence.append(f"{gate_id} evidence must contain a Markdown link")
            continue
        for target in targets:
            if target.startswith("https://"):
                remote_error = _remote_evidence_error(gate_id, target)
                if remote_error is not None:
                    invalid_evidence.append(remote_error)
                    break
                continue
            if (
                "://" in target
                or target.startswith(("/", "\\"))
                or re.match(r"^[A-Za-z]:[\\/]", target)
                or ".." in Path(target.split("#", 1)[0]).parts
            ):
                invalid_evidence.append(f"{gate_id} evidence contains an unsafe link")
                break
            relative_target = target.split("#", 1)[0]
            if not relative_target:
                invalid_evidence.append(
                    f"{gate_id} evidence must identify a file or HTTPS URL"
                )
                break
            candidate = (ROOT / "docs/phase-2" / relative_target).resolve()
            try:
                candidate.relative_to(ROOT.resolve())
            except ValueError:
                invalid_evidence.append(f"{gate_id} evidence escapes the repository")
                break
            if not candidate.is_file():
                invalid_evidence.append(f"{gate_id} evidence file does not exist")
                break
            local_error = _local_evidence_error(gate_id, candidate)
            if local_error is not None:
                invalid_evidence.append(local_error)
                break

    if structural_errors or invalid_evidence:
        return Check(
            "extension_publication_gate",
            FAIL,
            "; ".join([*structural_errors, *invalid_evidence]),
            [path],
        )

    unchecked = [f"{gate_id}: {title}" for gate_id, checked, title, _ in gates if not checked]
    declared_status = status_match.group("status") if status_match else None
    if unchecked:
        if declared_status != "pending":
            return Check(
                "extension_publication_gate",
                FAIL,
                "publication checklist status must be `pending` while gates remain",
                [path],
            )
        return Check(
            "extension_publication_gate",
            MANUAL,
            f"{len(unchecked)} controlled ONVIF extension publication gates remain.",
            [path, *unchecked],
        )
    if declared_status != "accepted":
        return Check(
            "extension_publication_gate",
            FAIL,
            "publication checklist status must be `accepted` after every gate passes",
            [path],
        )
    return Check(
        "extension_publication_gate",
        PASS,
        "Controlled ONVIF extension publication is accepted.",
        [path],
    )


def _run(
    command: list[str], *, env: dict[str, str] | None = None
) -> tuple[str, str | None]:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=VALIDATION_COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return " ".join(command), str(exc)
    evidence = f"{' '.join(command)} -> exit {completed.returncode}"
    if completed.returncode == 0:
        return evidence, None
    detail = completed.stderr.strip() or completed.stdout.strip()
    return evidence, detail[-2000:]


def validation() -> Check:
    evidence: list[str] = []
    failures: list[str] = []
    commands = [
        ["uv", "lock", "--check"],
        [sys.executable, "-m", "compileall", "-q", "app", "tools", "migrations"],
        [sys.executable, "-m", "ruff", "check", "app", "tests", "tools", "migrations"],
        [sys.executable, "tools/release_contracts.py", "check"],
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "tools/phase1_readiness.py", "--json"],
        ["git", "diff", "--check"],
    ]
    for command in commands:
        item, failure = _run(command)
        evidence.append(item)
        if failure:
            failures.append(failure)
    with tempfile.TemporaryDirectory(prefix="hcam-phase2-readiness-") as temp:
        database_url = f"sqlite:///{(Path(temp) / 'migration.db').as_posix()}"
        environment = {**os.environ, "HCAM_DATABASE_URL": database_url}
        for arguments in (["upgrade", "head"], ["check"]):
            item, failure = _run(
                [sys.executable, "-m", "alembic", *arguments], env=environment
            )
            evidence.append(item)
            if failure:
                failures.append(failure)
        secret_root = Path(temp) / "lab-secrets"
        for arguments in (
            ["--secret-root", str(secret_root), "prepare", "--force"],
            ["--secret-root", str(secret_root), "config"],
        ):
            item, failure = _run([sys.executable, "tools/phase2_lab.py", *arguments])
            evidence.append(item)
            if failure:
                failures.append(failure)
    if failures:
        return Check("validation", FAIL, "; ".join(failures), evidence)
    return Check("validation", PASS, "Offline Phase 2 validation passed.", evidence)


def build_report(run_validation: bool) -> dict[str, object]:
    checks = [
        check_files(),
        _contract_check(
            "release_contract_drift",
            [
                "tools/release_contracts.py",
                "contracts/phase-2/README.md",
                ".github/workflows/python-ci.yml",
                "tests/test_release_contracts.py",
            ],
            [
                "render_openapi_contract",
                "render_database_contract",
                "--acknowledge-reviewed-change",
                "release_contracts.py check",
                "test_tracked_release_contracts_match_current_application",
            ],
        ),
        _contract_check(
            "stream_control_plane",
            [
                "app/hcam/streams/models.py",
                "app/hcam/streams/routes.py",
                "app/hcam/streams/service.py",
                "migrations/versions/0004_stream_management.py",
            ],
            [
                "StreamEndpoint",
                "StreamHealthCurrent",
                "StreamProbeRun",
                "StreamEventOutbox",
                "If-Match",
                "X-HCAM-Reason",
                "allowed_departments",
            ],
        ),
        _contract_check(
            "health_worker",
            [
                "app/hcam/streams/probe.py",
                "app/hcam/streams/worker.py",
                "app/hcam/streams/network.py",
            ],
            [
                "shell=False",
                "network_policy_denied",
                "with_for_update(skip_locked=True)",
                "hcam.stream.health.changed.v1",
                "timedelta(days=7)",
            ],
        ),
        _contract_check(
            "adapter_egress_hardening",
            [
                "app/hcam/streams/network.py",
                "app/hcam/streams/onvif.py",
                "app/hcam/streams/probe.py",
                "tests/test_onvif_simulator.py",
                "tests/test_stream_probe.py",
            ],
            [
                "stream hostname must be explicitly allowlisted",
                "ProxyHandler({})",
                "_NoRedirectHandler",
                "onvif_redirect_denied",
                "_run_bounded_process",
                "test_bounded_process_terminates_during_output_flood",
                "test_onvif_resolver_does_not_follow_redirects",
            ],
        ),
        _contract_check(
            "camera_capability_management",
            [
                "app/hcam/streams/onvif.py",
                "app/hcam/streams/network.py",
                "app/hcam/streams/onvif_simulator.py",
                "app/hcam/streams/capabilities.py",
                "app/hcam/streams/capability_worker.py",
                "app/hcam/streams/secrets.py",
                "app/hcam/metrics.py",
                "app/hcam/streams/routes.py",
                "app/hcam/streams/schemas.py",
                "app/hcam/streams/models.py",
                "migrations/versions/0006_onvif_capability_management.py",
                "deploy/compose.phase2.yaml",
                "deploy/onvif-egress.phase2.json",
                "deploy/observability/hcam-phase2-alerts.yml",
                "tools/phase2_private_camera.py",
                "tests/test_authenticated_onvif.py",
                "tests/test_capability_management.py",
                "tests/test_capability_security.py",
                "tests/test_postgres_integration.py",
                "tests/test_stream_management_api.py",
            ],
            [
                "GetDeviceInformation",
                "GetSystemDateAndTime",
                "GetServices",
                "GetServiceCapabilities",
                "GetProfiles",
                "wsse_password_digest",
                "http_digest",
                "CameraSecretProvider",
                "with_for_update(skip_locked=True)",
                "hcam.stream.capabilities.changed.v1",
                "hcam_capability_refresh_expired_leases_total",
                "hcam_capability_refresh_lease_recoveries_recent_total",
                "stream.capability_refresh.lease_recovered",
                "timedelta(days=90)",
                "/streams/{stream_id}/capability-refreshes",
                "/capability-refreshes/{refresh_id}",
                "/streams/{stream_id}/capability-snapshots",
                "/streams/{stream_id}/capabilities/discover",
                "capability-worker",
                "HCAM_ONVIF_EGRESS_RULES_FILE",
                "HCAM_PRIVATE_CAMERA_LAB_ENABLED",
                "AuthorizedOnvifTarget",
                'extensions = {"sni_hostname": target.sni_hostname}',
                "stream.capabilities.discover.requested",
                "capability_discover_sync",
                "OnvifOperationRun",
                "test_secret_rotation_is_used_without_restarting_provider",
                "test_transport_pins_approved_dns_and_validates_private_ca_sni",
                "test_capability_discovery_fails_closed_before_network_when_intent_audit_fails",
                "test_capability_discovery_leaves_pending_intent_when_completion_audit_fails",
                "test_capability_discovery_sanitizes_unexpected_adapter_failure",
                "test_capability_refresh_conflict_reuses_winning_active_job",
                "test_worker_prunes_expired_capability_history_but_keeps_latest_inventory",
                "test_worker_audits_missing_stream_preflight_without_contacting_engine",
                "test_postgres_capability_workers_claim_distinct_jobs_concurrently",
                "test_postgres_concurrent_capability_queue_reuses_single_active_job",
                "test_postgres_capability_history_retention_preserves_latest_snapshot",
                "test_scheduled_capability_load_processes_50_streams",
                "test_scheduled_refresh_fails_closed_when_queue_audit_is_unavailable",
                "test_expired_lease_recovery_fails_closed_when_audit_is_unavailable",
                "HcamCapabilityWorkerLeaseRecovery",
            ],
        ),
        _contract_check(
            "controlled_onvif_operations",
            [
                "app/hcam/security/auth.py",
                "app/hcam/settings.py",
                "app/hcam/streams/onvif_operations.py",
                "app/hcam/streams/onvif_discovery.py",
                "app/hcam/streams/onvif_simulator.py",
                "app/hcam/streams/routes.py",
                "app/hcam/streams/models.py",
                "app/hcam/metrics.py",
                "migrations/versions/0007_onvif_operations.py",
                "deploy/observability/hcam-phase2-alerts.yml",
                "tests/test_onvif_operations.py",
                "tests/test_onvif_operation_failures.py",
                "tests/test_onvif_discovery.py",
            ],
            [
                "camera.controller",
                "HCAM_ONVIF_CONTROL_ENABLED",
                "HCAM_ONVIF_DISCOVERY_ENABLED",
                "GetImagingSettings",
                "CreatePullPointSubscription",
                "PullMessages",
                "ContinuousMove",
                "OnvifControlLease",
                "onvif_operation_runs",
                "/streams/{stream_id}/onvif/ptz-commands",
                "/onvif/discovery-runs",
                "hcam_onvif_operations_retained_total",
                "hcam_onvif_operation_failures_recent_total",
                "HcamOnvifControlLeaseSustained",
                "HcamOnvifOperationPending",
                'outcome="pending"',
                ".requested",
                ".completed",
                "test_onvif_operations_execute_against_synthetic_services",
                "test_operation_completion_failure_preserves_pending_intent",
                "test_ws_discovery_is_bounded_and_filters_unapproved_xaddrs",
            ],
        ),
        _contract_check(
            "event_delivery",
            [
                "app/hcam/streams/outbox.py",
                "deploy/compose.phase2.yaml",
                "tests/test_stream_outbox.py",
            ],
            [
                "StreamEventOutboxDispatcher",
                "StreamEventDeliveryError",
                "with_for_update(skip_locked=True)",
                "stream-event-dispatcher",
                "published_at",
            ],
        ),
        _contract_check(
            "playback_security",
            [
                "app/hcam/streams/playback.py",
                "deploy/mediamtx.phase2.yml",
                "docs/phase-2/playback-security.md",
            ],
            [
                "ES256",
                "P-256",
                "mediamtx_permissions",
                '"action": "read"',
                "no-store",
                "record: false",
            ],
        ),
        _contract_check(
            "synthetic_safety",
            [
                "deploy/compose.phase2.yaml",
                "tools/phase2_lab.py",
                "docs/phase-2/safety-and-governance.md",
            ],
            [
                "50",
                "127.0.0.1",
                "HCAM_ALLOW_SYNTHETIC_LAB",
                "real-person footage",
                "Government data",
                "biometrics",
            ],
        ),
        _contract_check(
            "publication_evidence_governance",
            [
                ".github/workflows/python-ci.yml",
                "tools/phase2_readiness.py",
                "tools/phase2_publication_evidence.py",
                "docs/phase-2/extension-publication-checklist.md",
                "docs/phase-2/publication-evidence.md",
                "tests/test_phase2_readiness.py",
                "tests/test_phase2_publication_ci.py",
                "tests/test_phase2_publication_evidence.py",
            ],
            [
                "PUBLICATION_GATE_IDS",
                "hcam.phase2.publication-evidence.v2",
                "hcam.phase2.publication-evidence-verification.v1",
                "hcam.phase2.github-run-verification.v1",
                "verify_evidence_artifact",
                "verify_github_run",
                "verify-run",
                "uv_lock_sha256",
                "uv sync --locked",
                "astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9",
                "--output",
                "_GITHUB_API_VERSION",
                "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
                "phase2-p2-g1-${{ github.event.pull_request.head.sha || github.sha }}",
                "phase2-p2-g2-${{ github.event.pull_request.head.sha || github.sha }}",
                "retention-days: 7",
                "P2-G1",
                "P2-G2",
                "P2-G3",
                "P2-G4",
                "evidence must contain a Markdown link",
                "test_phase2_extension_gate_rejects_checked_gate_without_evidence",
                "test_phase2_extension_gate_accepts_complete_linked_evidence",
                "test_preflight_rejects_empty_docker_server_even_with_zero_exit",
                "test_docker_state_rejects_non_linux_server",
                "test_postgres_gate_restores_head_after_downgrade_failure",
                "test_compose_gate_cleans_up_after_verification_failure",
                "test_verify_accepts_current_complete_postgres_artifact",
                "test_source_state_binds_dependency_lock_hash",
                "test_source_state_fails_closed_without_dependency_lock",
                "test_verify_rejects_dependency_lock_drift",
                "test_python_jobs_use_pinned_uv_and_the_reviewed_lock",
                "test_package_job_builds_and_installs_from_locked_hashes",
                "test_verify_github_run_accepts_successful_commit_bound_artifact",
                "test_verify_github_run_rejects_wrong_run_commit_before_download",
                "test_verify_github_run_rejects_noncanonical_run_url_without_api_access",
                "test_verify_github_run_rejects_failed_expected_job",
                "test_verify_github_run_rejects_expired_artifact",
                "test_verify_github_run_rejects_future_dated_artifact",
                "test_verify_github_run_rejects_extra_downloaded_payload_file",
                "test_verify_github_run_redacts_token_when_api_is_unavailable",
                "test_phase2_extension_gate_rejects_unrelated_https_evidence",
                "test_postgres_job_generates_commit_named_p2_g1_artifact",
                "test_compose_job_generates_evidence_and_keeps_defensive_cleanup",
            ],
        ),
        check_acceptance(),
        check_extension_publication(),
    ]
    if run_validation:
        checks.append(validation())
    failures = sum(check.status == FAIL for check in checks)
    manual = sum(check.status == MANUAL for check in checks)
    manual_names = {check.name for check in checks if check.status == MANUAL}
    if failures:
        status = "not_ready"
    elif "owner_gate" in manual_names:
        status = "ready_for_owner_review"
    elif "extension_publication_gate" in manual_names:
        status = "accepted_core_extension_pending"
    else:
        status = "complete"
    return {
        "status": status,
        "failures": failures,
        "manual_gates": manual,
        "checks": [asdict(check) for check in checks],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify H-CAM Phase 2 readiness")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--run-validation", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.run_validation)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Phase 2 readiness: {report['status']}")
        print(f"Failures: {report['failures']}")
        print(f"Manual gates: {report['manual_gates']}")
        for check in report["checks"]:
            print(f"[{check['status']}] {check['name']}: {check['detail']}")
    if report["failures"]:
        return 1
    if args.strict and report["manual_gates"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
