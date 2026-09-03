#!/usr/bin/env python3
"""Generate and verify the bounded P3.5 W9 closure evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import tracemalloc
import zipfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterator


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from hcam.analytics.anpr import (  # noqa: E402
    BoundedSyntheticConsensus,
    ConsensusViolation,
    EphemeralConsensusObservationV1,
    EphemeralPlateNormalizationV1,
    SyntheticAnprExecutionPolicyV1,
    SyntheticConsensusPolicyV1,
    derive_generated_request,
    generate_ephemeral_token,
    synthetic_corpus_plan_fixture,
)
from hcam.analytics.anpr.guardrails import canonical_anpr_evidence_json  # noqa: E402


EVIDENCE_PATH = ROOT / "contracts" / "phase-3" / "p3-5-w9-closure-evidence.json"
AUTHORIZATION_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-w9-start-authorization.json"
)
PROPOSAL_PATH = ROOT / "contracts" / "phase-3" / "p3-5-w9-scope-proposal.json"

AUTHORIZATION_HEAD = "6d546fbe1a074e4090fa6d006a67421a27746afe"
CLOSURE_HEAD = "1611922b4f410aa0cdbce369e4f3c8838f53e19f"
ACCEPTED_EVIDENCE_SHA256 = (
    "A64ACE72ED33E0734D87D43A871BB1FB73B593296A681771600C3A1F42899E55"
)
PLANNING_PACKAGE_DIGEST = (
    "9BCC9E9C068E03E94E5461AABDE3B50A4766498406643EE253AF66ECAD8A9B7B"
)
PROPOSAL_SHA256 = (
    "62B711EAF2C1EDD21CBCD07751D9A30EF6FA61C11E9ECB190CE6614FE67AB796"
)
SOURCE_DATE_EPOCH = 1_787_838_586
RESOURCE_OBSERVATIONS = 10_000
RESOURCE_REPLAY_RUNS = 2
RESOURCE_ELAPSED_LIMIT_SECONDS = 30
RESOURCE_MEMORY_LIMIT_BYTES = 128 * 1024 * 1024
MAX_EVIDENCE_BYTES = 128 * 1024
MAX_EVIDENCE_NODES = 8_192
SELF_EVIDENCE_SUFFIX = "contracts/phase-3/p3-5-w9-closure-evidence.json"

ALLOWED_PATHS = (
    ".github/workflows/python-ci.yml",
    "README.md",
    "contracts/phase-3/README.md",
    "contracts/phase-3/p3-5-w9-closure-evidence.json",
    "contracts/phase-3/p3-5-w9-scope-proposal.json",
    "contracts/phase-3/p3-5-w9-start-authorization.json",
    "docs/phase-3/README.md",
    "docs/phase-3/decision-register.md",
    "docs/phase-3/implementation-backlog.md",
    "docs/phase-3/p3-5-w9-closure.md",
    "docs/phase-3/p3-5-w9-decision-packet.md",
    "docs/phase-3/p3-5-w9-start-authorization.md",
    "tests/test_phase35_readiness.py",
    "tests/test_phase35_w9_closure.py",
    "tools/phase35_readiness.py",
    "tools/phase35_w9_closure.py",
)

ALLOWED_ACTIONS = frozenset(
    {
        "consolidate_existing_W1_through_W8_aggregate_evidence",
        "add_stdlib_only_aggregate_evidence_and_manifest_checker",
        "prove_zero_retention_and_prohibited_payload_absence",
        "run_bounded_deterministic_generated_contract_fixture_resource_stress_without_model_execution",
        "build_and_inspect_local_wheel_and_sdist",
        "record_only_aggregate_package_counts_and_cryptographic_digests",
        "prove_default_off_behavior_and_document_local_rollback",
        "update_tests_CI_readiness_documentation_and_backlog",
        "prepare_clean_source_package_for_separate_W10_acceptance",
    }
)

PROHIBITED_ACTIONS = frozenset(
    {
        "external_E_runtime_or_artifact_execution_under_option_A",
        "B_drive_access_except_static_source_denial_assertions",
        "model_font_or_Tesseract_execution_under_option_A",
        "network_download_or_external_service_access",
        "final_test_sample_opening_or_holdout_tuning",
        "quality_threshold_selection_or_model_promotion",
        "new_dependency_lockfile_container_migration_API_worker_database_or_persistent_storage_change",
        "raw_OCR_normalized_text_alternative_pixel_media_stream_track_owner_vehicle_or_government_data_in_tracked_evidence",
        "physical_camera_ONVIF_media_or_Sentinel_stream_access",
        "real_public_private_government_police_or_scraped_plate_media",
        "identity_biometric_reidentification_cross_camera_linkage_watchlist_alert_action_or_enforcement",
        "training_finetuning_PLATE_D0_OCR_G0_or_OCR_G1_execution",
        "pilot_production_statewide_deployment_or_P3_6_and_later_work",
        "remote_git_push_pull_request_or_merge",
        "W10_acceptance_without_separate_clean_source_evidence_and_owner_decision",
    }
)

SOURCE_EVIDENCE = (
    ("P35-W1-contracts", "contracts/phase-3/p3-5-anpr-contracts.json"),
    ("P35-W3-splits", "contracts/phase-3/fixtures/p3-5-sealed-splits-v1.json"),
    (
        "P35-W4-ground-truth-crop",
        "contracts/phase-3/fixtures/p3-5-ground-truth-crop-v1.json",
    ),
    ("P35-W5-latin", "contracts/phase-3/p3-5-latin-ocr-evaluation.json"),
    (
        "P35-W6-auxiliary",
        "contracts/phase-3/p3-5-auxiliary-script-evaluation.json",
    ),
    (
        "P35-W7-normalization",
        "contracts/phase-3/p3-5-normalization-evaluation.json",
    ),
    ("P35-W8-consensus", "contracts/phase-3/p3-5-consensus-evaluation.json"),
)

_PROHIBITED_PACKAGE_SUFFIXES = (
    ".avi",
    ".bmp",
    ".gif",
    ".h264",
    ".h265",
    ".jpeg",
    ".jpg",
    ".mkv",
    ".mov",
    ".mp4",
    ".onnx",
    ".otf",
    ".pdiparams",
    ".pdmodel",
    ".png",
    ".pt",
    ".pth",
    ".traineddata",
    ".ttf",
    ".webp",
    ".weights",
)


class ClosureToolError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PackageSummary:
    archive_kind: str
    entry_count: int
    canonical_uncompressed_bytes: int
    canonical_content_sha256: str
    prohibited_payload_count: int
    unsafe_entry_count: int
    self_evidence_exclusion_count: int
    raw_archive_sha256: str | None
    raw_archive_bytes: int | None


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_json(path: Path) -> dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ClosureToolError("W9 authorization or evidence cannot be read") from exc
    if not isinstance(document, dict):
        raise ClosureToolError("W9 authorization or evidence must be an object")
    return document


def _run_git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        raise ClosureToolError("W9 Git boundary check failed")
    return completed.stdout


def _changed_paths() -> tuple[str, ...]:
    committed = {
        item.strip().replace("\\", "/")
        for item in _run_git(
            "diff", "--name-only", AUTHORIZATION_HEAD, CLOSURE_HEAD, "--"
        ).splitlines()
        if item.strip()
    }
    return tuple(sorted(committed))


def _load_authorization() -> tuple[dict[str, object], tuple[str, ...]]:
    proposal = _load_json(PROPOSAL_PATH)
    authorization = _load_json(AUTHORIZATION_PATH)
    changed = _changed_paths()
    if (
        _sha256_file(PROPOSAL_PATH) != PROPOSAL_SHA256
        or proposal.get("decision_id") != "D-P3.5-W9-START"
        or proposal.get("recommended_option") != "A"
        or authorization.get("contract_format")
        != "hcam.phase3.p3_5.w9-start-authorization.v1"
        or authorization.get("decision_id") != "D-P3.5-W9-START"
        or authorization.get("owner_statement_received")
        != "D-P3.5-W9-START: A"
        or authorization.get("selected_option") != "A"
        or authorization.get("scope")
        != "phase3.p3_5.w9.narrow_generated_only_closure"
        or authorization.get("status")
        != "owner_authorized_narrow_generated_only_closure"
        or authorization.get("authorized_by") != "mayank-admin"
        or authorization.get("authorization_repository_head") != AUTHORIZATION_HEAD
        or authorization.get("planning_package_digest") != PLANNING_PACKAGE_DIGEST
        or authorization.get("proposal_sha256") != PROPOSAL_SHA256
        or authorization.get("effective") is not True
        or authorization.get("implementation_authorized") is not True
        or authorization.get("acceptance_authorized") is not False
        or authorization.get("w10_authorized") is not False
        or authorization.get("external_runtime_access") is not False
        or authorization.get("model_or_font_execution_authorized") is not False
        or authorization.get("allowed_network_actions") != []
        or tuple(authorization.get("allowed_paths", [])) != ALLOWED_PATHS
        or set(authorization.get("allowed_actions", [])) != ALLOWED_ACTIONS
        or set(authorization.get("prohibited_actions", [])) != PROHIBITED_ACTIONS
        or any(path not in ALLOWED_PATHS for path in changed)
    ):
        raise ClosureToolError("W9 authorization is missing, widened, or out of scope")
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", CLOSURE_HEAD, "HEAD"],
        cwd=ROOT,
        check=False,
        timeout=10,
    )
    if completed.returncode != 0:
        raise ClosureToolError("Accepted W9 closure head is not an ancestor")
    return authorization, changed


def _source_evidence() -> tuple[tuple[dict[str, object], ...], str]:
    digest = hashlib.sha256()
    records: list[dict[str, object]] = []
    for evidence_id, relative_path in SOURCE_EVIDENCE:
        payload = (ROOT / relative_path).read_bytes().replace(b"\r\n", b"\n")
        item_digest = _sha256_bytes(payload)
        digest.update(evidence_id.encode("ascii"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
        records.append({"evidence_id": evidence_id, "sha256": item_digest})
    return tuple(records), digest.hexdigest().upper()


def _identifier(prefix: str, value: int) -> str:
    return f"{prefix}_{value:032x}"


def _normalization(value: str) -> EphemeralPlateNormalizationV1:
    return EphemeralPlateNormalizationV1(
        candidate_id="OCR-L0",
        script_lane="latin",
        raw_hypothesis_digest="sha256:" + hashlib.sha256(value.encode()).hexdigest(),
        nfc_value=value,
        graphemes=tuple(value),
        normalized_display_candidate=value,
        raw_scalar_count=len(value),
        nfc_scalar_count=len(value),
        grapheme_count=len(value),
        format_family="synthetic_non_issuable",
        validation_outcomes=(
            "allowlist_valid",
            "graphemes_segmented",
            "nfc_derived",
            "synthetic_grammar_valid",
            "unicode_scalar_valid",
            "utf8_valid",
        ),
        nfc_transform_performed=False,
        case_transform_performed=False,
        raw_confidence=0.8,
        calibrated_confidence=0.8,
        abstention_reason="quality_threshold_unapproved",
    )


def _observation(
    sequence: int,
    *,
    track: int,
    normalization: EphemeralPlateNormalizationV1,
    stream: int = 1,
    epoch: int = 1,
) -> EphemeralConsensusObservationV1:
    return EphemeralConsensusObservationV1(
        stream_id=_identifier("str", stream),
        tracker_epoch=_identifier("epoch", epoch),
        track_id=_identifier("trk", track),
        event_time_ms=sequence * 100,
        source_sequence=sequence,
        normalization=normalization,
    )


@contextmanager
def _network_denied() -> Iterator[None]:
    original_create_connection = socket.create_connection
    original_connect = socket.socket.connect

    def deny_create(*_args: object, **_kwargs: object) -> socket.socket:
        raise PermissionError("network denied by P3.5 W9")

    def deny_connect(
        _instance: socket.socket, *_args: object, **_kwargs: object
    ) -> None:
        raise PermissionError("network denied by P3.5 W9")

    socket.create_connection = deny_create
    socket.socket.connect = deny_connect
    try:
        yield
    finally:
        socket.create_connection = original_create_connection
        socket.socket.connect = original_connect


def run_resource_stress() -> dict[str, object]:
    plan = synthetic_corpus_plan_fixture()
    policy = SyntheticAnprExecutionPolicyV1(enabled=True, environment="test")
    token = generate_ephemeral_token(
        derive_generated_request(plan, "contract_fixture", 0),
        policy=policy,
    ).token
    normalization = _normalization(token)

    disabled = BoundedSyntheticConsensus()
    default_off_rejections = 0
    try:
        disabled.observe(_observation(1, track=1, normalization=normalization))
    except ConsensusViolation as exc:
        if exc.code != "runtime_disabled":
            raise
        default_off_rejections = 1

    tracemalloc.start()
    started = time.perf_counter()
    engine = BoundedSyntheticConsensus(
        SyntheticConsensusPolicyV1(enabled=True, environment="test")
    )
    closed_results = 0
    abstained_results = 0
    overload_results = 0
    maximum_active_states = 0
    blocked_network_attempts = 0

    with _network_denied():
        try:
            socket.create_connection(("127.0.0.1", 9), timeout=0.01)
        except PermissionError:
            blocked_network_attempts = 1

        for track in range(1, 1_949):
            for sequence in range(1, 6):
                results = engine.observe(
                    _observation(
                        sequence,
                        track=track,
                        normalization=normalization,
                    )
                )
                closed_results += len(results)
                abstained_results += sum(result.abstain for result in results)

        for track in range(2_001, 2_257):
            results = engine.observe(
                _observation(
                    1,
                    track=track,
                    normalization=normalization,
                    stream=2,
                    epoch=2,
                )
            )
            if results:
                raise ClosureToolError("W9 active-state fill closed unexpectedly")
        maximum_active_states = engine.active_state_count(_identifier("str", 2))

        for track in range(2_257, 2_261):
            results = engine.observe(
                _observation(
                    1,
                    track=track,
                    normalization=normalization,
                    stream=2,
                    epoch=2,
                )
            )
            overload_results += sum(
                result.close_reason == "overload" for result in results
            )
            closed_results += len(results)
            abstained_results += sum(result.abstain for result in results)

        reset = engine.reset_epoch(_identifier("str", 2), _identifier("epoch", 2))
        closed_results += len(reset)
        abstained_results += sum(result.abstain for result in reset)

    elapsed = time.perf_counter() - started
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if (
        blocked_network_attempts != 1
        or default_off_rejections != 1
        or maximum_active_states != 256
        or overload_results != 4
        or closed_results != 2_208
        or abstained_results != closed_results
        or engine.active_state_count() != 0
    ):
        raise ClosureToolError("W9 bounded resource invariants failed")
    if elapsed > RESOURCE_ELAPSED_LIMIT_SECONDS:
        raise ClosureToolError("W9 resource stress exceeded its elapsed limit")
    if peak_memory > RESOURCE_MEMORY_LIMIT_BYTES:
        raise ClosureToolError("W9 resource stress exceeded its memory limit")

    return {
        "abstained_result_count": abstained_results,
        "blocked_network_attempt_count": blocked_network_attempts,
        "closed_result_count": closed_results,
        "default_off_rejection_count": default_off_rejections,
        "elapsed_limit_passed": True,
        "elapsed_limit_seconds": RESOURCE_ELAPSED_LIMIT_SECONDS,
        "maximum_active_state_count": maximum_active_states,
        "memory_limit_bytes": RESOURCE_MEMORY_LIMIT_BYTES,
        "memory_limit_passed": True,
        "observation_count": RESOURCE_OBSERVATIONS,
        "overload_result_count": overload_results,
    }


def _source_paths() -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        raise ClosureToolError("W9 source inventory failed")
    paths = tuple(
        sorted(
            item.decode("utf-8").replace("\\", "/")
            for item in completed.stdout.split(b"\0")
            if item
        )
    )
    if not paths:
        raise ClosureToolError("W9 source inventory is empty")
    return paths


def _stage_source(destination: Path) -> None:
    for relative_path in _source_paths():
        source = (ROOT / relative_path).resolve()
        try:
            source.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ClosureToolError("W9 source path escaped the repository") from exc
        if source.is_symlink() or not source.is_file():
            raise ClosureToolError("W9 source inventory contains an unsafe entry")
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        os.utime(target, (SOURCE_DATE_EPOCH, SOURCE_DATE_EPOCH))


def _safe_archive_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or pure.is_absolute()
        or ".." in pure.parts
        or any(":" in part for part in pure.parts)
    ):
        raise ClosureToolError("W9 package contains an unsafe archive entry")
    return normalized


def _summarize_entries(
    archive_kind: str,
    entries: tuple[tuple[str, bytes], ...],
    *,
    raw_archive: bytes,
) -> PackageSummary:
    digest = hashlib.sha256()
    canonical_bytes = 0
    prohibited = 0
    self_exclusions = 0
    for name, payload in sorted(entries):
        safe_name = _safe_archive_name(name)
        if safe_name.lower().endswith(_PROHIBITED_PACKAGE_SUFFIXES):
            prohibited += 1
        if safe_name.endswith(SELF_EVIDENCE_SUFFIX):
            canonical_payload = b"<W9-SELF-EVIDENCE-EXCLUDED>"
            self_exclusions += 1
        else:
            canonical_payload = payload
        digest.update(safe_name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(canonical_payload)
        digest.update(b"\0")
        canonical_bytes += len(canonical_payload)
    if prohibited:
        raise ClosureToolError("W9 package contains a prohibited payload")
    retain_raw = archive_kind == "wheel"
    return PackageSummary(
        archive_kind=archive_kind,
        entry_count=len(entries),
        canonical_uncompressed_bytes=canonical_bytes,
        canonical_content_sha256=digest.hexdigest().upper(),
        prohibited_payload_count=prohibited,
        unsafe_entry_count=0,
        self_evidence_exclusion_count=self_exclusions,
        raw_archive_sha256=_sha256_bytes(raw_archive) if retain_raw else None,
        raw_archive_bytes=len(raw_archive) if retain_raw else None,
    )


def summarize_archive(path: Path, archive_kind: str) -> PackageSummary:
    raw_archive = path.read_bytes()
    if archive_kind == "wheel":
        with zipfile.ZipFile(path) as archive:
            entries = tuple(
                (item.filename, archive.read(item))
                for item in archive.infolist()
                if not item.is_dir()
            )
    elif archive_kind == "sdist":
        with tarfile.open(path, mode="r:gz") as archive:
            records: list[tuple[str, bytes]] = []
            for item in archive.getmembers():
                if item.isdir():
                    continue
                if not item.isfile():
                    raise ClosureToolError("W9 sdist contains a non-file entry")
                extracted = archive.extractfile(item)
                if extracted is None:
                    raise ClosureToolError("W9 sdist entry cannot be read")
                records.append((item.name, extracted.read()))
            entries = tuple(records)
    else:
        raise ValueError("archive kind must be wheel or sdist")
    return _summarize_entries(archive_kind, entries, raw_archive=raw_archive)


def build_package_summaries() -> tuple[PackageSummary, PackageSummary]:
    with tempfile.TemporaryDirectory(prefix="hcam-p35-w9-") as temporary:
        temporary_root = Path(temporary)
        source_root = temporary_root / "source"
        output_root = temporary_root / "dist"
        guard_root = temporary_root / "network-guard"
        source_root.mkdir()
        output_root.mkdir()
        guard_root.mkdir()
        _stage_source(source_root)
        guard = guard_root / "sitecustomize.py"
        guard.write_text(
            "import socket\n"
            "def _hcam_w9_denied(*args, **kwargs):\n"
            "    raise PermissionError('network denied by P3.5 W9 build guard')\n"
            "socket.create_connection = _hcam_w9_denied\n"
            "socket.socket.connect = _hcam_w9_denied\n",
            encoding="utf-8",
            newline="\n",
        )
        os.utime(guard, (SOURCE_DATE_EPOCH, SOURCE_DATE_EPOCH))

        environment = os.environ.copy()
        for name in (
            "ALL_PROXY",
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "all_proxy",
            "http_proxy",
            "https_proxy",
        ):
            environment.pop(name, None)
        environment.update(
            {
                "NO_PROXY": "*",
                "PIP_NO_INDEX": "1",
                "PYTHONPATH": str(guard_root),
                "PYTHONHASHSEED": "0",
                "SOURCE_DATE_EPOCH": str(SOURCE_DATE_EPOCH),
                "UV_OFFLINE": "1",
            }
        )
        network_probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import socket; "
                    "\ntry: socket.create_connection(('127.0.0.1', 9), 0.01)"
                    "\nexcept PermissionError: raise SystemExit(0)"
                    "\nraise SystemExit(1)"
                ),
            ],
            cwd=source_root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if network_probe.returncode != 0:
            raise ClosureToolError("W9 package-build network guard failed")
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--no-isolation",
                "--outdir",
                str(output_root),
                str(source_root),
            ],
            cwd=source_root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        if completed.returncode != 0:
            raise ClosureToolError("W9 offline source package build failed")
        wheels = tuple(output_root.glob("*.whl"))
        sdists = tuple(output_root.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            raise ClosureToolError("W9 package build produced an unexpected archive set")
        return (
            summarize_archive(wheels[0], "wheel"),
            summarize_archive(sdists[0], "sdist"),
        )


def _render(document: dict[str, object]) -> str:
    rendered = canonical_anpr_evidence_json(
        document,
        maximum_bytes=MAX_EVIDENCE_BYTES,
        maximum_nodes=MAX_EVIDENCE_NODES,
    )
    prohibited_tokens = (
        "SYN-",
        '"stream_id":',
        '"tracker_epoch":',
        '"track_id":',
        '"raw_text":',
        '"normalized_text":',
        '"winning_candidate":',
        '"ranked_votes":',
        '"owner_record":',
        '"government_record":',
        "B:\\",
        "E:\\",
    )
    if any(token in rendered for token in prohibited_tokens):
        raise ClosureToolError("W9 evidence contains a prohibited retained value")
    return rendered


def build_evidence() -> dict[str, object]:
    authorization, changed = _load_authorization()
    source_records, source_digest = _source_evidence()
    first_stress = run_resource_stress()
    second_stress = run_resource_stress()
    if first_stress != second_stress:
        raise ClosureToolError("W9 resource replay is not deterministic")
    wheel, sdist = build_package_summaries()
    authorization_digest = _sha256_file(AUTHORIZATION_PATH)
    return {
        "acceptance_authorized": False,
        "aggregate_source_evidence": list(source_records),
        "aggregate_source_evidence_count": len(source_records),
        "aggregate_source_evidence_sha256": source_digest,
        "authorization_sha256": authorization_digest,
        "contract_format": "hcam.phase3.p3_5.w9-closure-evidence.v1",
        "decision_id": "D-P3.5-W9-START",
        "execution_scope": "generated_contract_fixtures_only",
        "implementation_changed_path_count": len(changed),
        "implementation_path_violation_count": 0,
        "package_evidence": [asdict(wheel), asdict(sdist)],
        "planning_package_digest": PLANNING_PACKAGE_DIGEST,
        "proposal_sha256": PROPOSAL_SHA256,
        "resource_replay_count": RESOURCE_REPLAY_RUNS,
        "resource_replay_deterministic": True,
        "resource_stress": first_stress,
        "rollback_evidence": {
            "application_file_change_count": 0,
            "database_or_migration_change_count": 0,
            "dependency_or_lockfile_change_count": 0,
            "local_rollback_documented": True,
            "runtime_activation_change_count": 0,
        },
        "security_evidence": {
            "accepted_value_count": 0,
            "artifact_download_count": 0,
            "b_drive_access_count": 0,
            "camera_or_external_input_count": 0,
            "external_runtime_access_count": 0,
            "final_test_open_count": 0,
            "model_or_font_execution_count": 0,
            "network_access_count": 0,
            "operational_event_count": 0,
            "package_build_network_guard_probe_count": 1,
            "retained_identifier_value_count": 0,
            "retained_pixel_or_content_value_count": 0,
            "retained_sensitive_text_value_count": 0,
        },
        "selected_option": authorization["selected_option"],
        "status": "validated_generated_only_closure",
        "w10_authorized": False,
    }


def write_evidence() -> int:
    if _run_git("rev-parse", "HEAD").strip() != CLOSURE_HEAD:
        raise ClosureToolError("Accepted W9 evidence is immutable after W10")
    original = EVIDENCE_PATH.read_bytes() if EVIDENCE_PATH.exists() else None
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text("{}\n", encoding="utf-8", newline="\n")
    try:
        rendered = _render(build_evidence())
        temporary = EVIDENCE_PATH.with_suffix(".json.tmp")
        temporary.write_text(rendered, encoding="utf-8", newline="\n")
        temporary.replace(EVIDENCE_PATH)
    except Exception:
        if original is None:
            EVIDENCE_PATH.unlink(missing_ok=True)
        else:
            EVIDENCE_PATH.write_bytes(original)
        raise
    print(f"[pass] {EVIDENCE_PATH.relative_to(ROOT)} sha256={_sha256_file(EVIDENCE_PATH)}")
    return 0


def check_evidence() -> int:
    _load_authorization()
    completed = subprocess.run(
        ["git", "show", f"{CLOSURE_HEAD}:{EVIDENCE_PATH.relative_to(ROOT).as_posix()}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        timeout=10,
    )
    current = EVIDENCE_PATH.read_bytes()
    if (
        completed.returncode != 0
        or current != completed.stdout
        or _sha256_bytes(current) != ACCEPTED_EVIDENCE_SHA256
    ):
        print("[fail] P3.5 W9 closure evidence drifted", file=sys.stderr)
        return 1
    print(f"[pass] {EVIDENCE_PATH.relative_to(ROOT)} sha256={_sha256_file(EVIDENCE_PATH)}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    write = subparsers.add_parser("write")
    write.add_argument("--acknowledge-generated-only-closure", action="store_true")
    subparsers.add_parser("check-evidence")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "write":
            if not args.acknowledge_generated_only_closure:
                print(
                    "[fail] writing W9 evidence requires explicit acknowledgment",
                    file=sys.stderr,
                )
                return 2
            return write_evidence()
        return check_evidence()
    except (ClosureToolError, OSError, subprocess.SubprocessError) as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
