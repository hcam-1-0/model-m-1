#!/usr/bin/env python3
"""Verify the planning-only P3.5 synthetic ANPR package."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PASS = "pass"
FAIL = "fail"
MANUAL = "manual"

AUTHORIZATION_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-planning-authorization.json"
)
ENTRY_GATES_PATH = ROOT / "contracts" / "phase-3" / "p3-5-entry-gates.json"
ARTIFACT_PROPOSAL_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-artifact-review-proposal.json"
)
ARTIFACT_RESEARCH_AUTHORIZATION_PATH = (
    ROOT
    / "contracts"
    / "phase-3"
    / "p3-5-artifact-research-authorization.json"
)
OWNER_DECISIONS_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-owner-decisions.json"
)
START_AUTHORIZATION_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-start-authorization.json"
)
RESEARCH_PATH = ROOT / "contracts" / "phase-3" / "p3-5-research-sources.json"
P3_4_ACCEPTANCE_PATH = ROOT / "contracts" / "phase-3" / "p3-4-acceptance.json"

P3_4_ACCEPTED_PACKAGE_DIGEST = (
    "11CCD757E2308F56EE5912B70861B8A977DBD8B7CEE8DBD434265A28988EF8AF"
)
P3_4_ACCEPTED_REPOSITORY_HEAD = "092127fcdefa74a0264b9f02d4eee87db3a6c6b8"
P3_5_BASELINE_REPOSITORY_HEAD = "ce8917343ce6752de35af8d7167878edc6e8d46a"

PACKAGE_FILES = (
    ".github/workflows/python-ci.yml",
    "README.md",
    "contracts/phase-3/README.md",
    "contracts/phase-3/p3-4-acceptance.json",
    "contracts/phase-3/p3-5-artifact-review-proposal.json",
    "contracts/phase-3/p3-5-artifact-research-authorization.json",
    "contracts/phase-3/p3-5-entry-gates.json",
    "contracts/phase-3/p3-5-planning-authorization.json",
    "contracts/phase-3/p3-5-owner-decisions.json",
    "contracts/phase-3/p3-5-research-sources.json",
    "contracts/phase-3/p3-5-start-authorization.json",
    "docs/phase-3/README.md",
    "docs/phase-3/acceptance-checklist.md",
    "docs/phase-3/decision-register.md",
    "docs/phase-3/implementation-backlog.md",
    "docs/phase-3/p3-5-decision-packet.md",
    "docs/phase-3/p3-5-artifact-research-authorization.md",
    "docs/phase-3/p3-5-artifact-review-proposal.md",
    "docs/phase-3/p3-5-owner-decisions.md",
    "docs/phase-3/p3-5-plan.md",
    "docs/phase-3/p3-5-planning-authorization.md",
    "docs/phase-3/p3-5-planning-readiness-report.md",
    "docs/phase-3/p3-5-research-record.md",
    "docs/phase-3/p3-5-start-intent.md",
    "tests/test_phase35_readiness.py",
    "tools/phase35_readiness.py",
)

CANDIDATE_PATHS = (
    "contracts/phase-3/p3-1/candidates/candidate-plate-d0.json",
    "contracts/phase-3/p3-1/candidates/candidate-ocr-l0.json",
    "contracts/phase-3/p3-1/candidates/candidate-ocr-l1.json",
    "contracts/phase-3/p3-1/candidates/candidate-ocr-d0.json",
    "contracts/phase-3/p3-1/candidates/candidate-ocr-g0.json",
    "contracts/phase-3/p3-1/candidates/candidate-ocr-g1.json",
)

DECISION_IDS = (
    "D-P3.5-001",
    "D-P3.5-002",
    "D-P3.5-003",
    "D-P3.5-004",
    "D-P3.5-START",
)

ALLOWED_SOURCE_HOSTS = {
    "github.com",
    "openaccess.thecvf.com",
    "upload.indiacode.nic.in",
    "www.paddleocr.ai",
    "www.unicode.org",
}

PROPOSED_ARTIFACT_HOSTS = {
    "paddle-model-ecology.bj.bcebos.com",
    "raw.githubusercontent.com",
}


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    status: str
    detail: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Report:
    status: str
    scope: str
    package_digest: str
    package_file_count: int
    failures: int
    manual_gates: int
    checks: tuple[Check, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scope": self.scope,
            "package_digest": self.package_digest,
            "package_file_count": self.package_file_count,
            "failures": self.failures,
            "manual_gates": self.manual_gates,
            "checks": [asdict(check) for check in self.checks],
        }


def _json(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain an object")
    return document


def _text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def package_digest() -> tuple[str, tuple[str, ...]]:
    digest = hashlib.sha256()
    manifest: list[str] = []
    for relative_path in sorted(PACKAGE_FILES):
        payload = (ROOT / relative_path).read_bytes().replace(b"\r\n", b"\n")
        file_digest = hashlib.sha256(payload).hexdigest()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
        manifest.append(
            f"{relative_path} sha256={file_digest} bytes={len(payload)}"
        )
    return digest.hexdigest().upper(), tuple(manifest)


def check_required_files() -> Check:
    missing = tuple(path for path in PACKAGE_FILES if not (ROOT / path).is_file())
    if missing:
        return Check("required_files", FAIL, "P3.5 planning files are missing.", missing)
    return Check(
        "required_files",
        PASS,
        f"All {len(PACKAGE_FILES)} P3.5 planning package files exist.",
    )


def check_planning_authorization() -> Check:
    try:
        record = _json(AUTHORIZATION_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("planning_authorization", FAIL, str(exc))

    expected = {
        "decision_id": "D-P3.5-PLAN-AUTH",
        "record_id": "D-P3.5-PLAN-AUTH",
        "status": "authorized",
        "authorized_by": "mayank-admin",
        "owner_statement_received": "authorized so continue",
        "scope": "phase3.p3_5.synthetic_anpr.planning_only",
        "baseline_repository_head": P3_5_BASELINE_REPOSITORY_HEAD,
        "planning_authorized": True,
        "implementation_authorized": False,
        "next_milestone_authorized": False,
    }
    required_deliverables = {
        "synthetic_non_issuable_plate_corpus_and_generator_design",
        "plate_localization_and_multilingual_ocr_candidate_plan",
        "raw_normalized_abstention_and_temporal_consensus_contracts",
        "zero_retention_privacy_rbac_and_audit_design",
        "generated_only_evaluation_resource_and_supply_chain_plan",
        "primary_source_research_record",
        "owner_decision_packet_and_separate_implementation_start_gate",
    }
    required_prohibitions = {
        "p3_5_runtime_or_product_implementation",
        "model_weight_font_dataset_or_source_artifact_download",
        "dependency_lockfile_container_or_environment_change",
        "application_migration_api_worker_or_storage_change",
        "synthetic_image_generation_training_finetuning_or_inference_execution",
        "physical_camera_onvif_media_or_sentinel_stream_access",
        "real_public_private_government_police_or_scraped_plate_media",
        "real_registration_mark_owner_vehicle_or_government_record_processing",
        "identity_biometric_reidentification_or_cross_camera_linkage",
        "watchlist_matching_operational_alerting_autonomous_action_or_enforcement",
        "pilot_production_or_statewide_deployment",
        "remote_git_push_pull_request_or_merge",
        "p3_6_or_later_work",
    }
    failures = [key for key, value in expected.items() if record.get(key) != value]
    if not required_deliverables.issubset(set(record.get("planning_deliverables", []))):
        failures.append("planning_deliverables")
    if not required_prohibitions.issubset(set(record.get("prohibited_actions", []))):
        failures.append("prohibited_actions")
    if failures:
        return Check(
            "planning_authorization",
            FAIL,
            "D-P3.5-PLAN-AUTH boundary changed.",
            tuple(failures),
        )
    return Check(
        "planning_authorization",
        PASS,
        "P3.5 planning is authorized while implementation and artifacts remain prohibited.",
    )


def check_accepted_p3_4_dependency() -> Check:
    try:
        record = _json(P3_4_ACCEPTANCE_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("accepted_p3_4_dependency", FAIL, str(exc))
    if (
        record.get("decision_id") != "D-P3.4-ACCEPTANCE"
        or record.get("status") != "accepted"
        or record.get("accepted_by") != "mayank-admin"
        or record.get("evidence_package_digest") != P3_4_ACCEPTED_PACKAGE_DIGEST
        or record.get("accepted_repository_head") != P3_4_ACCEPTED_REPOSITORY_HEAD
        or record.get("next_phase_authorized") is not False
    ):
        return Check(
            "accepted_p3_4_dependency",
            FAIL,
            "P3.5 planning is not bound to the immutable accepted P3.4 package.",
        )
    return Check(
        "accepted_p3_4_dependency",
        PASS,
        "P3.5 planning is independently authorized on the accepted P3.4 package.",
        (
            f"accepted_digest={P3_4_ACCEPTED_PACKAGE_DIGEST}",
            f"accepted_repository_head={P3_4_ACCEPTED_REPOSITORY_HEAD}",
        ),
    )


def check_candidate_boundary() -> Check:
    failures: list[str] = []
    found: list[str] = []
    for relative_path in CANDIDATE_PATHS:
        try:
            record = _json(ROOT / relative_path)
        except (OSError, ValueError, json.JSONDecodeError):
            failures.append(relative_path)
            continue
        candidate_id = str(record.get("candidate_id", "missing"))
        found.append(candidate_id)
        approval = record.get("approval")
        artifact = record.get("artifact_identity")
        if (
            not isinstance(approval, dict)
            or approval.get("status") != "pending"
            or record.get("eligibility") != "blocked"
            or not isinstance(artifact, dict)
            or artifact.get("state") != "unresolved"
        ):
            failures.append(candidate_id)
    if failures:
        return Check(
            "candidate_boundary",
            FAIL,
            "A P3.5 model candidate was silently approved or changed.",
            tuple(failures),
        )
    return Check(
        "candidate_boundary",
        PASS,
        "All six plate/OCR candidates remain pending, blocked, and artifact-unresolved.",
        tuple(found),
    )


def check_existing_contract_foundation() -> Check:
    required = {
        "app/hcam/analytics/evaluation/candidates.py": (
            "PLATE-D0",
            "OCR-L0",
            "OCR-L1",
            "OCR-D0",
            "OCR-G0",
            "OCR-G1",
        ),
        "app/hcam/analytics/evaluation/metrics.py": (
            "synthetic_anpr.exact_match",
            "synthetic_anpr.character_error_rate",
        ),
        "docs/phase-3/event-contracts.md": (
            "ANPR stays an observation extension rather than a vehicle identity",
            "Owner details, registration records, watchlist state",
        ),
        "contracts/phase-3/p3-0-owner-decisions.json": (
            '"classification": "derived.analytics.plate_text"',
            '"maximum_retention_hours": 0',
        ),
    }
    missing: list[str] = []
    for relative_path, tokens in required.items():
        try:
            content = _text(relative_path)
        except OSError:
            missing.append(relative_path)
            continue
        missing.extend(
            f"{relative_path}:{token}" for token in tokens if token not in content
        )
    if missing:
        return Check(
            "existing_contract_foundation",
            FAIL,
            "Existing ANPR metrics, identity boundary, or zero-retention policy changed.",
            tuple(missing),
        )
    return Check(
        "existing_contract_foundation",
        PASS,
        "Existing candidate, metric, observation-only, and zero-retention contracts remain intact.",
    )


def check_research_sources() -> Check:
    try:
        record = _json(RESEARCH_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("primary_source_research", FAIL, str(exc))
    sources = record.get("sources")
    failures: list[str] = []
    if (
        record.get("research_scope") != "planning_metadata_and_primary_sources_only"
        or record.get("artifact_downloads_performed") is not False
        or record.get("dataset_downloads_performed") is not False
        or record.get("model_downloads_performed") is not False
        or not isinstance(sources, list)
        or len(sources) < 10
    ):
        failures.append("research_boundary")
    if isinstance(sources, list):
        reference_ids: set[str] = set()
        for source in sources:
            if not isinstance(source, dict):
                failures.append("non_object_source")
                continue
            reference_id = str(source.get("reference_id", ""))
            host = urlparse(str(source.get("url", ""))).hostname
            if not reference_id or reference_id in reference_ids:
                failures.append(f"duplicate_or_missing_reference:{reference_id}")
            reference_ids.add(reference_id)
            if host not in ALLOWED_SOURCE_HOSTS:
                failures.append(f"unapproved_host:{host}")
            if not source.get("supports") or not source.get("limitations"):
                failures.append(f"unbounded_claim:{reference_id}")
    if failures:
        return Check(
            "primary_source_research",
            FAIL,
            "P3.5 research sources or no-download boundary changed.",
            tuple(failures),
        )
    return Check(
        "primary_source_research",
        PASS,
        "Ten primary sources are recorded on approved hosts with explicit limitations and no downloads.",
    )


def check_plan_contract() -> Check:
    required = {
        "docs/phase-3/p3-5-plan.md": (
            "synthetic_non_issuable",
            "derived.analytics.plate_text",
            "maximum retention: zero hours",
            "NFC canonical normalization",
            "extended grapheme clusters",
            "D-P3.5-START",
            "P3.6",
        ),
        "docs/phase-3/p3-5-decision-packet.md": (
            "D-P3.5-001",
            "D-P3.5-002",
            "D-P3.5-003",
            "D-P3.5-004",
            "D-P3.5-START",
            "Recommended",
        ),
        "docs/phase-3/p3-5-research-record.md": (
            "synthetic-to-real domain gap",
            "Gujarati and Devanagari",
            "no artifact, model, font",
        ),
    }
    missing: list[str] = []
    for relative_path, tokens in required.items():
        try:
            content = _text(relative_path)
        except OSError:
            missing.append(relative_path)
            continue
        missing.extend(
            f"{relative_path}:{token}" for token in tokens if token not in content
        )
    if missing:
        return Check(
            "plan_contract",
            FAIL,
            "P3.5 pipeline, Unicode, privacy, evidence, or owner gates are incomplete.",
            tuple(missing),
        )
    return Check(
        "plan_contract",
        PASS,
        "P3.5 data, pipeline, OCR, normalization, consensus, privacy, resources, and evidence are explicit.",
    )


def check_planning_only_package() -> Check:
    prohibited_prefixes = ("app/", "migrations/", "deploy/")
    prohibited_suffixes = (
        ".avi",
        ".bin",
        ".engine",
        ".jpg",
        ".jpeg",
        ".onnx",
        ".png",
        ".pt",
        ".pth",
        ".tflite",
        ".traineddata",
        ".weights",
    )
    prohibited = tuple(
        path
        for path in PACKAGE_FILES
        if path.startswith(prohibited_prefixes) or path.lower().endswith(prohibited_suffixes)
    )
    if prohibited:
        return Check(
            "planning_only_package",
            FAIL,
            "P3.5 planning package contains runtime, migration, deployment, model, or media files.",
            prohibited,
        )
    return Check(
        "planning_only_package",
        PASS,
        "The package contains planning, governance, CI, verifier, and test files only.",
    )


def check_owner_gates() -> Check:
    try:
        record = _json(ENTRY_GATES_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("owner_decisions", FAIL, str(exc))
    decisions = record.get("decisions")
    if not isinstance(decisions, list):
        return Check("owner_decisions", FAIL, "P3.5 decisions must be a list.")
    actual_ids = tuple(str(item.get("decision_id")) for item in decisions if isinstance(item, dict))
    technical = decisions[:-1]
    start = decisions[-1] if decisions and isinstance(decisions[-1], dict) else {}
    if (
        actual_ids != DECISION_IDS
        or any(
            not isinstance(item, dict)
            or item.get("status") != "owner_approved"
            or item.get("selected_option") != "A"
            for item in technical
        )
        or start.get("decision_id") != "D-P3.5-START"
        or start.get("status") != "received_prerequisites_pending"
        or start.get("owner_statement_received") != "D-P3.5-START"
        or start.get("effective") is not False
        or record.get("status") != "artifact_research_authorized"
        or record.get("scope")
        != "phase3.p3_5.synthetic_anpr.pre_implementation_research"
        or record.get("manual_gate_count") != 1
        or record.get("owner_decisions_completed") != 4
        or record.get("owner_decisions_record") != "p3-5-owner-decisions.json"
        or record.get("artifact_research_authorization_record")
        != "p3-5-artifact-research-authorization.json"
        or record.get("implementation_authorized") is not False
    ):
        return Check(
            "owner_decisions",
            FAIL,
            "P3.5 owner gates were changed without an explicit decision record.",
        )
    return Check(
        "owner_decisions",
        MANUAL,
        "The four technical choices are approved; final digest-bound D-P3.5-START remains manual.",
        ("D-P3.5-START",),
    )


def check_owner_decisions_record() -> Check:
    try:
        record = _json(OWNER_DECISIONS_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("owner_decision_record", FAIL, str(exc))
    decisions = record.get("decisions")
    expected_values = (
        "strict_procedural_non_issuable_synthetic_corpus",
        "staged_plate_detector_latin_primary_and_auxiliary_script_portfolio",
        "raw_preserving_nfc_grapheme_aware_abstaining_consensus",
        "ephemeral_plate_text_aggregate_evidence_and_zero_retention",
    )
    actual = (
        tuple(
            (
                item.get("decision_id"),
                item.get("selected_option"),
                item.get("selected_value"),
                item.get("status"),
            )
            for item in decisions
            if isinstance(item, dict)
        )
        if isinstance(decisions, list)
        else ()
    )
    expected = tuple(
        (decision_id, "A", value, "owner_approved")
        for decision_id, value in zip(DECISION_IDS[:-1], expected_values, strict=True)
    )
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.owner-decisions.v1"
        or record.get("accepted_by") != "mayank-admin"
        or record.get("status") != "owner_approved"
        or record.get("technical_decisions_completed") != 4
        or record.get("implementation_authorized") is not False
        or actual != expected
    ):
        return Check(
            "owner_decision_record",
            FAIL,
            "The four owner-selected P3.5 technical decisions are incomplete or changed.",
        )
    return Check(
        "owner_decision_record",
        PASS,
        "D-P3.5-001 through D-P3.5-004 select the recommended A baseline without implementation authority.",
        DECISION_IDS[:-1],
    )


def check_start_intent() -> Check:
    try:
        record = _json(START_AUTHORIZATION_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("start_intent", FAIL, str(exc))
    prerequisites = record.get("prerequisites")
    if not isinstance(prerequisites, list):
        return Check("start_intent", FAIL, "P3.5 start prerequisites must be a list.")
    prerequisite_statuses = tuple(
        str(item.get("status"))
        for item in prerequisites
        if isinstance(item, dict)
    )
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.start-authorization.v1"
        or record.get("decision_id") != "D-P3.5-START"
        or record.get("owner_statement_received") != "D-P3.5-START"
        or record.get("status") != "received_prerequisites_pending"
        or record.get("effective") is not False
        or record.get("implementation_authorized") is not False
        or record.get("allowed_artifacts") != []
        or record.get("allowed_network_actions") != []
        or prerequisite_statuses
        != (
            "owner_approved",
            "owner_approved",
            "owner_approved",
            "owner_approved",
            "quarantine_research_authorized",
        )
    ):
        return Check(
            "start_intent",
            FAIL,
            "The early D-P3.5-START statement was widened or made effective before its prerequisites.",
        )
    return Check(
        "start_intent",
        PASS,
        "The exact D-P3.5-START statement is preserved as non-effective intent with no artifact or network authority.",
    )


def check_artifact_proposal() -> Check:
    try:
        record = _json(ARTIFACT_PROPOSAL_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("artifact_proposal", FAIL, str(exc))
    artifacts = record.get("artifacts")
    if not isinstance(artifacts, list):
        return Check("artifact_proposal", FAIL, "P3.5 artifacts must be a list.")
    expected_candidates = (
        "OCR-L0",
        "OCR-L1",
        "OCR-D0",
        "OCR-G0",
        "OCR-G1",
        "FONT-G0",
        "FONT-D0",
        "PLATE-D0",
    )
    actual_candidates = tuple(
        str(artifact.get("candidate_id"))
        for artifact in artifacts
        if isinstance(artifact, dict)
    )
    invalid: list[str] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            invalid.append("non-object-artifact")
            continue
        artifact_id = str(artifact.get("artifact_id"))
        source_url = artifact.get("proposed_source_url")
        if artifact.get("expected_sha256") is not None:
            invalid.append(f"{artifact_id}:premature-sha256")
        if not str(artifact.get("status", "")).startswith("blocked_"):
            invalid.append(f"{artifact_id}:not-blocked")
        expected_bytes = artifact.get("expected_bytes")
        maximum_bytes = artifact.get("maximum_bytes")
        if expected_bytes is not None and (
            not isinstance(expected_bytes, int)
            or not isinstance(maximum_bytes, int)
            or expected_bytes <= 0
            or expected_bytes > maximum_bytes
        ):
            invalid.append(f"{artifact_id}:invalid-size-bound")
        if source_url is not None:
            parsed = urlparse(str(source_url))
            if (
                parsed.scheme != "https"
                or parsed.hostname not in PROPOSED_ARTIFACT_HOSTS
                or parsed.username is not None
                or parsed.password is not None
            ):
                invalid.append(f"{artifact_id}:invalid-source-url")
    choices = record.get("applies_only_if_owner_selects")
    quarantine = record.get("proposed_quarantine_gate")
    environment = record.get("environment_observations")
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.artifact-review-proposal.v1"
        or record.get("status") != "proposal_prepared_blocked"
        or record.get("scope") != "metadata_only_non_approved_acquisition_proposal"
        or record.get("download_performed") is not False
        or record.get("acquisition_authorized") is not False
        or record.get("implementation_authorized") is not False
        or record.get("model_execution_performed") is not False
        or record.get("allowed_network_actions") != []
        or choices
        != {
            "D-P3.5-001": "A",
            "D-P3.5-002": "A",
            "D-P3.5-003": "A",
            "D-P3.5-004": "A",
        }
        or actual_candidates != expected_candidates
        or set(record.get("proposed_source_hosts", [])) != PROPOSED_ARTIFACT_HOSTS
        or not isinstance(quarantine, dict)
        or quarantine.get("decision_id") != "D-P3.5-ARTIFACT-RESEARCH"
        or quarantine.get("status") != "not_authorized"
        or not isinstance(environment, dict)
        or environment.get("tesseract_executable") != "not_installed"
        or invalid
    ):
        return Check(
            "artifact_proposal",
            FAIL,
            "The metadata-only proposal is incomplete, widened, executable, or prematurely approved.",
            tuple(invalid),
        )
    return Check(
        "artifact_proposal",
        PASS,
        "Eight proposed artifact slots have bounded metadata; all SHA-256 values, acquisition, and execution remain blocked.",
        actual_candidates,
    )


def check_artifact_research_authorization() -> Check:
    try:
        record = _json(ARTIFACT_RESEARCH_AUTHORIZATION_PATH)
        proposal = _json(ARTIFACT_PROPOSAL_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("artifact_research_authorization", FAIL, str(exc))
    proposal_digest = hashlib.sha256(ARTIFACT_PROPOSAL_PATH.read_bytes()).hexdigest().upper()
    allowed = record.get("allowed_artifacts")
    proposed = proposal.get("artifacts")
    if not isinstance(allowed, list) or not isinstance(proposed, list):
        return Check(
            "artifact_research_authorization",
            FAIL,
            "Artifact authorization and proposal entries must be lists.",
        )
    proposed_by_id = {
        str(item.get("artifact_id")): item
        for item in proposed
        if isinstance(item, dict) and item.get("proposed_source_url") is not None
    }
    invalid: list[str] = []
    for item in allowed:
        if not isinstance(item, dict):
            invalid.append("non-object")
            continue
        artifact_id = str(item.get("artifact_id"))
        proposal_item = proposed_by_id.get(artifact_id)
        if proposal_item is None:
            invalid.append(f"{artifact_id}:not-proposed")
            continue
        if (
            item.get("source_url") != proposal_item.get("proposed_source_url")
            or item.get("expected_bytes") != proposal_item.get("expected_bytes")
            or item.get("maximum_bytes") != proposal_item.get("maximum_bytes")
        ):
            invalid.append(f"{artifact_id}:proposal-mismatch")
        filename = str(item.get("filename", ""))
        if not filename or Path(filename).name != filename or "\\" in filename:
            invalid.append(f"{artifact_id}:unsafe-filename")
        source = urlparse(str(item.get("source_url", "")))
        if source.scheme != "https" or source.hostname not in PROPOSED_ARTIFACT_HOSTS:
            invalid.append(f"{artifact_id}:unsafe-url")
    limits = record.get("limits")
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.artifact-research-authorization.v1"
        or record.get("authorization_id") != "D-P3.5-ARTIFACT-RESEARCH"
        or record.get("authorized_by") != "mayank-admin"
        or record.get("owner_statement_received") != "D-P3.5-ARTIFACT-RESEARCH"
        or record.get("proposal_id")
        != "P3.5-EXACT-ARTIFACT-REVIEW-PROPOSAL-R0"
        or record.get("proposal_sha256") != proposal_digest
        or record.get("status") != "owner_approved_restricted"
        or record.get("implementation_authorized") is not False
        or record.get("allowed_network_actions")
        != ["https_get_exact_allowlisted_urls_only"]
        or len(allowed) != 7
        or set(proposed_by_id) != {
            str(item.get("artifact_id")) for item in allowed if isinstance(item, dict)
        }
        or not isinstance(limits, dict)
        or limits.get("maximum_redirects") != 0
        or limits.get("environment_proxies") is not False
        or limits.get("runtime_loading_from_quarantine") is not False
        or invalid
    ):
        return Check(
            "artifact_research_authorization",
            FAIL,
            "The quarantine authorization is not exactly bound, bounded, or non-executable.",
            tuple(invalid),
        )
    return Check(
        "artifact_research_authorization",
        PASS,
        "D-P3.5-ARTIFACT-RESEARCH authorizes exactly seven non-runtime quarantine downloads bound to proposal R0.",
        tuple(str(item["artifact_id"]) for item in allowed),
    )


def check_documentation_sync() -> Check:
    required = {
        "README.md": ("P3.5", "tools/phase35_readiness.py"),
        "contracts/phase-3/README.md": (
            "p3-5-artifact-review-proposal.json",
            "p3-5-artifact-research-authorization.json",
            "p3-5-owner-decisions.json",
            "p3-5-planning-authorization.json",
            "p3-5-entry-gates.json",
            "p3-5-start-authorization.json",
        ),
        "docs/phase-3/README.md": (
            "[P3.5 artifact research authorization](p3-5-artifact-research-authorization.md)",
            "[P3.5 artifact review proposal](p3-5-artifact-review-proposal.md)",
            "[P3.5 owner decisions](p3-5-owner-decisions.md)",
            "[P3.5 plan](p3-5-plan.md)",
            "[P3.5 owner decision packet](p3-5-decision-packet.md)",
            "[P3.5 start intent](p3-5-start-intent.md)",
        ),
        "docs/phase-3/decision-register.md": (
            "DR-0035",
            "DR-0037",
            "D-P3.5-PLAN-AUTH",
            "D-P3.5-ARTIFACT-RESEARCH",
            "D-P3.5-START",
        ),
        "docs/phase-3/implementation-backlog.md": (
            "D-P3.4-ACCEPTANCE",
            "D-P3.5-PLAN-AUTH",
        ),
        ".github/workflows/python-ci.yml": (
            "python tools/phase35_readiness.py --strict",
        ),
    }
    missing: list[str] = []
    for relative_path, tokens in required.items():
        try:
            content = _text(relative_path)
        except OSError:
            missing.append(relative_path)
            continue
        missing.extend(
            f"{relative_path}:{token}" for token in tokens if token not in content
        )
    if missing:
        return Check(
            "documentation_sync",
            FAIL,
            "P3.5 status, indexes, backlog, decision register, or CI are out of sync.",
            tuple(missing),
        )
    return Check(
        "documentation_sync",
        PASS,
        "Root, indexes, backlog, decision register, and CI are synchronized.",
    )


def check_clean_source() -> Check:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--", *PACKAGE_FILES],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if completed.returncode != 0:
        return Check("clean_source", FAIL, "Git clean-source check failed.")
    dirty = tuple(line for line in completed.stdout.splitlines() if line.strip())
    if dirty:
        return Check(
            "clean_source",
            FAIL,
            "P3.5 planning package files are not committed cleanly.",
            dirty,
        )
    return Check("clean_source", PASS, "P3.5 planning files are clean in Git.")


def build_report(*, require_clean_source: bool = False) -> Report:
    checks = [
        check_required_files(),
        check_planning_authorization(),
        check_accepted_p3_4_dependency(),
        check_candidate_boundary(),
        check_existing_contract_foundation(),
        check_research_sources(),
        check_plan_contract(),
        check_planning_only_package(),
        check_artifact_proposal(),
        check_owner_decisions_record(),
        check_artifact_research_authorization(),
        check_start_intent(),
        check_documentation_sync(),
    ]
    if require_clean_source:
        checks.append(check_clean_source())
    checks.append(check_owner_gates())
    failures = sum(check.status == FAIL for check in checks)
    manual_gates = sum(
        len(check.evidence) if check.name == "owner_decisions" and check.status == MANUAL else 1
        for check in checks
        if check.status == MANUAL
    )
    status = (
        "invalid"
        if failures
        else "artifact_research_authorized"
        if manual_gates
        else "implementation_authorized_generated_only"
    )
    try:
        digest, _ = package_digest()
    except OSError:
        digest = "UNAVAILABLE"
    return Report(
        status=status,
        scope="phase3.p3_5.synthetic_anpr.pre_implementation_research",
        package_digest=digest,
        package_file_count=len(PACKAGE_FILES),
        failures=failures,
        manual_gates=manual_gates,
        checks=tuple(checks),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-clean-source", action="store_true")
    parser.add_argument("--require-decisions", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(require_clean_source=args.require_clean_source)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(
            f"P3.5 planning: {report.status}; failures={report.failures}; "
            f"manual_gates={report.manual_gates}; digest={report.package_digest}"
        )
        for check in report.checks:
            print(f"[{check.status}] {check.name}: {check.detail}")
    if report.failures and args.strict:
        return 1
    if report.manual_gates and args.require_decisions:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
