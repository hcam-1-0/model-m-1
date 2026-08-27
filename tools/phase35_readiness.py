#!/usr/bin/env python3
"""Verify the authorized staged P3.5 synthetic ANPR package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
ARTIFACT_REVIEW_EVIDENCE_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-artifact-review-evidence.json"
)
ARTIFACT_REVIEW_ACCEPTANCE_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-artifact-review-acceptance.json"
)
ARTIFACT_SBOM_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-artifact-sbom.cdx.json"
)
ARTIFACT_MODEL_CARDS_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-artifact-model-cards.json"
)
OWNER_DECISIONS_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-owner-decisions.json"
)
START_AUTHORIZATION_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-start-authorization.json"
)
RESEARCH_PATH = ROOT / "contracts" / "phase-3" / "p3-5-research-sources.json"
RUNTIME_REVIEW_PROPOSAL_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-runtime-review-proposal.json"
)
RUNTIME_RESEARCH_AUTHORIZATION_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-runtime-research-authorization.json"
)
RUNTIME_RESEARCH_EVIDENCE_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-runtime-research-evidence.json"
)
RUNTIME_SBOM_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-runtime-sbom.cdx.json"
)
RUNTIME_LICENSE_REVIEW_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-runtime-license-review.json"
)
P3_4_ACCEPTANCE_PATH = ROOT / "contracts" / "phase-3" / "p3-4-acceptance.json"

P3_4_ACCEPTED_PACKAGE_DIGEST = (
    "11CCD757E2308F56EE5912B70861B8A977DBD8B7CEE8DBD434265A28988EF8AF"
)
P3_4_ACCEPTED_REPOSITORY_HEAD = "092127fcdefa74a0264b9f02d4eee87db3a6c6b8"
P3_5_BASELINE_REPOSITORY_HEAD = "ce8917343ce6752de35af8d7167878edc6e8d46a"
P3_5_ACCEPTED_ARTIFACT_PACKAGE_DIGEST = (
    "54B02B80169604904C9945C1C6E692500CA8AA79253EEC27A63B4C4DB00B395C"
)
P3_5_ACCEPTED_ARTIFACT_REPOSITORY_HEAD = (
    "7052d502d7862cfd1f9f60565e5e169bd6c4e047"
)
P3_5_ARTIFACT_EVIDENCE_SHA256 = (
    "57453CB21F19DF4A0EDFC48784B721D35382F1B4E883C3C89052289EBF8A1BED"
)
P3_5_RUNTIME_PROPOSAL_SHA256 = (
    "3788950DFA0477DE59B1B135AA1AACDA7584A368C1219B3266F0265E6174A5F1"
)
P3_5_RUNTIME_SBOM_SHA256 = (
    "07EE71F79BBD1368F620B7D915E4BF753E23DCC76696862C5E4ADB3CB23ED6DE"
)
P3_5_RUNTIME_EVIDENCE_PACKAGE_DIGEST = (
    "915F5E9246A7A656DF528DD54DA6018D7489C6875BF3A77D1A551BAD6EF9AF4D"
)
P3_5_RUNTIME_EVIDENCE_REPOSITORY_HEAD = (
    "1edfd0a13208d9b359cc5e563bbc406bba214e26"
)
P3_5_W5_EVIDENCE_SHA256 = (
    "3AEA54734015CCE7E6C8CCABFDBE02310F028268393EACD9A31B4BA6DFA42A20"
)
P3_5_W6_EVIDENCE_SHA256 = (
    "1E58A84AD522EB852F6EECFDCF1BAF38FCDC4337B414836B64EBCD4DADBCB955"
)
P3_5_W7_EVIDENCE_SHA256 = (
    "1F233E044976B0B28BD0261CA5B6324403C45B2A158C852B34DCBB7A0144EE8A"
)
P3_5_W8_EVIDENCE_SHA256 = (
    "58E7E4479DEB554D4B99F0CC1868B4DA61E9DED292E3F11942B740AEF02FC124"
)

PACKAGE_FILES = (
    ".github/workflows/python-ci.yml",
    "README.md",
    "app/hcam/analytics/anpr/__init__.py",
    "app/hcam/analytics/anpr/auxiliary.py",
    "app/hcam/analytics/anpr/consensus.py",
    "app/hcam/analytics/anpr/contracts.py",
    "app/hcam/analytics/anpr/generator.py",
    "app/hcam/analytics/anpr/guardrails.py",
    "app/hcam/analytics/anpr/localization.py",
    "app/hcam/analytics/anpr/normalization.py",
    "app/hcam/analytics/anpr/ocr.py",
    "contracts/phase-3/README.md",
    "contracts/phase-3/fixtures/p3-5-generated-request-v1.json",
    "contracts/phase-3/fixtures/p3-5-ground-truth-crop-v1.json",
    "contracts/phase-3/fixtures/p3-5-sealed-splits-v1.json",
    "contracts/phase-3/p3-4-acceptance.json",
    "contracts/phase-3/p3-5-artifact-review-proposal.json",
    "contracts/phase-3/p3-5-artifact-review-evidence.json",
    "contracts/phase-3/p3-5-artifact-review-acceptance.json",
    "contracts/phase-3/p3-5-artifact-model-cards.json",
    "contracts/phase-3/p3-5-artifact-research-authorization.json",
    "contracts/phase-3/p3-5-artifact-sbom.cdx.json",
    "contracts/phase-3/p3-5-anpr-contracts.json",
    "contracts/phase-3/p3-5-auxiliary-script-evaluation.json",
    "contracts/phase-3/p3-5-consensus-evaluation.json",
    "contracts/phase-3/p3-5-entry-gates.json",
    "contracts/phase-3/p3-5-latin-ocr-evaluation.json",
    "contracts/phase-3/p3-5-normalization-evaluation.json",
    "contracts/phase-3/p3-5-planning-authorization.json",
    "contracts/phase-3/p3-5-owner-decisions.json",
    "contracts/phase-3/p3-5-research-sources.json",
    "contracts/phase-3/p3-5-runtime-review-proposal.json",
    "contracts/phase-3/p3-5-runtime-research-authorization.json",
    "contracts/phase-3/p3-5-runtime-research-evidence.json",
    "contracts/phase-3/p3-5-runtime-sbom.cdx.json",
    "contracts/phase-3/p3-5-runtime-license-review.json",
    "contracts/phase-3/p3-5-start-authorization.json",
    "docs/phase-3/README.md",
    "docs/phase-3/acceptance-checklist.md",
    "docs/phase-3/decision-register.md",
    "docs/phase-3/implementation-backlog.md",
    "docs/phase-3/p3-5-decision-packet.md",
    "docs/phase-3/p3-5-artifact-model-cards.md",
    "docs/phase-3/p3-5-artifact-review-evidence.md",
    "docs/phase-3/p3-5-artifact-review-acceptance.md",
    "docs/phase-3/p3-5-artifact-research-authorization.md",
    "docs/phase-3/p3-5-artifact-review-proposal.md",
    "docs/phase-3/p3-5-owner-decisions.md",
    "docs/phase-3/p3-5-plan.md",
    "docs/phase-3/p3-5-planning-authorization.md",
    "docs/phase-3/p3-5-planning-readiness-report.md",
    "docs/phase-3/p3-5-research-record.md",
    "docs/phase-3/p3-5-runtime-review-proposal.md",
    "docs/phase-3/p3-5-runtime-research-authorization.md",
    "docs/phase-3/p3-5-runtime-research-evidence.md",
    "docs/phase-3/p3-5-start-authorization.md",
    "docs/phase-3/p3-5-start-intent.md",
    "docs/phase-3/p3-5-w1-contracts-guardrails.md",
    "docs/phase-3/p3-5-w3-generator-splits.md",
    "docs/phase-3/p3-5-w4-ground-truth-crop.md",
    "docs/phase-3/p3-5-w5-latin-ocr.md",
    "docs/phase-3/p3-5-w6-auxiliary-scripts.md",
    "docs/phase-3/p3-5-w7-normalization-abstention.md",
    "docs/phase-3/p3-5-w8-bounded-consensus.md",
    "tests/test_analytics_anpr_auxiliary.py",
    "tests/test_analytics_anpr_consensus.py",
    "tests/test_analytics_anpr_generator.py",
    "tests/test_analytics_anpr_guardrails.py",
    "tests/test_analytics_anpr_localization.py",
    "tests/test_analytics_anpr_normalization.py",
    "tests/test_analytics_anpr_ocr.py",
    "tests/test_phase35_contracts.py",
    "tests/test_phase35_consensus.py",
    "tests/test_phase35_latin_ocr.py",
    "tests/test_phase35_normalization.py",
    "tests/test_phase35_auxiliary_ocr.py",
    "tests/test_phase35_readiness.py",
    "tests/test_phase35_artifact_research.py",
    "tests/test_phase35_artifact_inspect.py",
    "tests/test_phase35_runtime_research.py",
    "tools/phase35_artifact_research.py",
    "tools/phase35_artifact_inspect.py",
    "tools/phase35_contracts.py",
    "tools/phase35_consensus.py",
    "tools/phase35_latin_ocr.py",
    "tools/phase35_latin_ocr_worker.py",
    "tools/phase35_normalization.py",
    "tools/phase35_auxiliary_ocr.py",
    "tools/phase35_auxiliary_ocr_worker.py",
    "tools/phase35_runtime_research.py",
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

TECHNICAL_DECISION_IDS = (
    "D-P3.5-001",
    "D-P3.5-002",
    "D-P3.5-003",
    "D-P3.5-004",
)

DECISION_IDS = (
    *TECHNICAL_DECISION_IDS,
    "D-P3.5-RUNTIME-RESEARCH",
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

REVIEWED_ARTIFACT_SHA256 = {
    "OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED": "DA460F968CE9F88325AC3A34FA302077D6E9B0DCEFB16BA3137CD7796F879D06",
    "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED": "4EECC1C6A4623765042E6FC15446DA0DA110B7D875B6B72B2D351D2B2DBD4DA6",
    "OCR-D0-PPOCRV5-DEVANAGARI-INFER-PROPOSED": "AC8279D27FC7E8CDA559364F9A3C506F43984CF6BA5E1B7A06450458BFE07DFB",
    "OCR-G0-TESSDATA-FAST-GUJ-PROPOSED": "FA69658614B4946A9AFAE8853D67E0689838803DFA3D12C2E35EC53EE6F8DF34",
    "OCR-G1-TESSDATA-BEST-GUJ-PROPOSED": "8CBB1D139B63434B9E1154A3B51930A74EC1C9A6251B95D86D74D7F1CD706ED6",
    "FONT-G0-NOTO-SANS-GUJARATI-VARIABLE-PROPOSED": "9901D8552F1DD5D2C50DBD4CAA6F6E174E74E8264F06594AB259AE6E7B1AC428",
    "FONT-D0-NOTO-SANS-DEVANAGARI-VARIABLE-PROPOSED": "9CE7B04F60E363D8870E5997744CF85CF69D38A4D7D129D364D92A3B14B461D7",
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
        f"All {len(PACKAGE_FILES)} P3.5 authorization and W1/W3/W4/W5/W6/W7/W8 package files exist.",
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
        "The original P3.5 planning authorization remains intact; later bounded "
        "implementation authority is validated separately by D-P3.5-START.",
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
        "All six P3.1 candidate-promotion records remain blocked; exact P3.5 generated-only artifact execution is governed independently.",
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


def check_authorized_w1_w3_w4_package() -> Check:
    allowed_application_files = {
        "app/hcam/analytics/anpr/__init__.py",
        "app/hcam/analytics/anpr/auxiliary.py",
        "app/hcam/analytics/anpr/consensus.py",
        "app/hcam/analytics/anpr/contracts.py",
        "app/hcam/analytics/anpr/generator.py",
        "app/hcam/analytics/anpr/guardrails.py",
        "app/hcam/analytics/anpr/localization.py",
        "app/hcam/analytics/anpr/normalization.py",
        "app/hcam/analytics/anpr/ocr.py",
    }
    prohibited_prefixes = ("migrations/", "deploy/")
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
        if path.startswith(prohibited_prefixes)
        or path.lower().endswith(prohibited_suffixes)
        or (path.startswith("app/") and path not in allowed_application_files)
    )
    if prohibited:
        return Check(
            "authorized_w1_w3_w4_package",
            FAIL,
            "P3.5 W1/W3/W4/W5/W6/W7/W8 contains an unapproved application, migration, deployment, model, or media file.",
            prohibited,
        )
    return Check(
        "authorized_w1_w3_w4_package",
        PASS,
        "P3.5 application scope is limited to generated-only contracts, guardrails, deterministic token/rendering, sealed splits, ground-truth localization, ephemeral crops, exact external Latin/Devanagari OCR adapters, Gujarati rendering-only evidence, ephemeral normalization/calibration/abstention logic, and bounded in-memory consensus; no migration, model, media, API, or persistence file is present.",
    )


def check_w1_contract_snapshot() -> Check:
    try:
        record = _json(ROOT / "contracts/phase-3/p3-5-anpr-contracts.json")
        fixture = _json(
            ROOT / "contracts/phase-3/fixtures/p3-5-generated-request-v1.json"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("w1_contract_snapshot", FAIL, str(exc))
    contracts = record.get("contracts")
    source_policy = record.get("source_policy")
    token_policy = record.get("token_policy")
    persistence = record.get("persistence_policy")
    generated_request = (
        contracts.get("generated_request") if isinstance(contracts, dict) else None
    )
    properties = (
        generated_request.get("properties")
        if isinstance(generated_request, dict)
        else None
    )
    prohibited_request_fields = {
        "camera_id",
        "file",
        "frame_bytes",
        "image",
        "owner_record",
        "path",
        "plate_text",
        "stream_id",
        "text",
        "token",
        "upload",
        "url",
        "vehicle_record",
        "watchlist",
    }
    if (
        record.get("contract_format") != "hcam.anpr.contract-bundle.v1"
        or not isinstance(source_policy, dict)
        or source_policy.get("allowed_source_id") != "DATA-PLATE-GEN-R0"
        or source_policy.get("input_mode") != "deterministic_seed_only"
        or source_policy.get("external_text_allowed") is not False
        or source_policy.get("file_url_upload_or_media_allowed") is not False
        or not isinstance(token_policy, dict)
        or token_policy.get("classification") != "synthetic_non_issuable"
        or token_policy.get("pattern") != r"^SYN-[A-Z0-9]{4}-[A-Z0-9]{4}$"
        or not isinstance(persistence, dict)
        or persistence.get("plate_text_retention_hours") != 0
        or persistence.get("token_or_alternative_in_evidence") is not False
        or not isinstance(properties, dict)
        or prohibited_request_fields.intersection(properties)
        or fixture.get("source_id") != "DATA-PLATE-GEN-R0"
        or fixture.get("input_mode") != "deterministic_seed_only"
        or prohibited_request_fields.intersection(fixture)
    ):
        return Check(
            "w1_contract_snapshot",
            FAIL,
            "P3.5 W1 contracts permit unapproved input, token grammar, or retention behavior.",
        )
    return Check(
        "w1_contract_snapshot",
        PASS,
        "P3.5 W1 fixes seed-only generated provenance, the visible SYN namespace, and zero plate-text retention.",
    )


def check_w3_split_manifest() -> Check:
    try:
        record = _json(
            ROOT / "contracts/phase-3/fixtures/p3-5-sealed-splits-v1.json"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("w3_split_manifest", FAIL, str(exc))
    content = record.get("content")
    if not isinstance(content, dict):
        return Check("w3_split_manifest", FAIL, "W3 manifest content is missing.")
    entries = content.get("entries")
    counts = content.get("counts")
    serialized = json.dumps(record, separators=(",", ":"), sort_keys=True)
    canonical_content = json.dumps(
        content,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    expected_digest = f"sha256:{hashlib.sha256(canonical_content).hexdigest()}"
    if not isinstance(entries, list) or not isinstance(counts, dict):
        return Check("w3_split_manifest", FAIL, "W3 entries or counts are missing.")
    actual_counts = {
        split: sum(entry.get("split") == split for entry in entries if isinstance(entry, dict))
        for split in ("contract_fixture", "development", "validation", "final_test")
    }
    non_final = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("split") != "final_test"
    ]
    final = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("split") == "final_test"
    ]
    if (
        record.get("contract_type") != "hcam.anpr.sealed-split-manifest.v1"
        or record.get("manifest_digest") != expected_digest
        or content.get("sealed") is not True
        or content.get("final_test_frozen") is not True
        or content.get("final_test_tuning_allowed") is not False
        or content.get("final_test_access_count") != 0
        or content.get("external_input_count") != 0
        or content.get("duplicate_token_count") != 0
        or content.get("token_text_persisted") is not False
        or content.get("token_commitment_persisted") is not False
        or counts != {
            "contract_fixture": 4,
            "development": 8,
            "final_test": 4,
            "validation": 4,
        }
        or actual_counts != counts
        or len(entries) != 20
        or '"token"' in serialized
        or "SYN-" in serialized
        or any(
            entry.get("generator_profile") != "primary"
            or entry.get("font_partition") != "primary"
            for entry in non_final
        )
        or not any(entry.get("generator_profile") == "holdout" for entry in final)
        or not any(entry.get("font_partition") == "holdout" for entry in final)
    ):
        return Check(
            "w3_split_manifest",
            FAIL,
            "P3.5 W3 split sealing, holdout isolation, determinism, or zero-retention boundary changed.",
        )
    return Check(
        "w3_split_manifest",
        PASS,
        "P3.5 W3 seals 20 token-free entries across independent namespaces with final-test-only holdouts.",
    )


def check_w4_ground_truth_crop() -> Check:
    try:
        record = _json(
            ROOT / "contracts/phase-3/fixtures/p3-5-ground-truth-crop-v1.json"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("w4_ground_truth_crop", FAIL, str(exc))
    localization = record.get("localization")
    crop = record.get("crop")
    if not isinstance(localization, dict) or not isinstance(crop, dict):
        return Check(
            "w4_ground_truth_crop",
            FAIL,
            "W4 localization result or crop descriptor is missing.",
        )
    hypotheses = localization.get("hypotheses")
    serialized = json.dumps(record, separators=(",", ":"), sort_keys=True)

    def all_keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value).union(*(all_keys(item) for item in value.values()))
        if isinstance(value, list):
            return set().union(*(all_keys(item) for item in value))
        return set()

    prohibited_keys = {
        "bgr_bytes",
        "bytes",
        "frame_bytes",
        "image_bytes",
        "image_path",
        "media_url",
        "path",
        "plate_text",
        "token",
        "url",
    }
    digests = (
        localization.get("source_frame_digest"),
        crop.get("source_frame_digest"),
        crop.get("region_digest"),
        crop.get("crop_digest"),
    )
    digest_pattern = re.compile(r"^sha256:[0-9a-f]{64}$")
    first_hypothesis = (
        hypotheses[0]
        if isinstance(hypotheses, list)
        and len(hypotheses) == 1
        and isinstance(hypotheses[0], dict)
        else {}
    )
    if (
        record.get("contract_type")
        != "hcam.anpr.ground-truth-crop-evidence.v1"
        or record.get("source_id") != "DATA-PLATE-GEN-R0"
        or record.get("generated_only") is not True
        or record.get("external_input_count") != 0
        or record.get("model_execution_performed") is not False
        or record.get("weights_loaded") is not False
        or record.get("frame_pixels_persisted") is not False
        or record.get("crop_pixels_persisted") is not False
        or record.get("plate_text_persisted") is not False
        or localization.get("contract_type")
        != "hcam.anpr.plate-localization-result.v1"
        or localization.get("source_id") != "DATA-PLATE-GEN-R0"
        or localization.get("execution_mode") != "generated_ground_truth_only"
        or localization.get("candidate_id") is not None
        or localization.get("model_execution_performed") is not False
        or localization.get("weights_loaded") is not False
        or localization.get("hypothesis_count") != 1
        or len(first_hypothesis) == 0
        or first_hypothesis.get("class_id")
        != "vehicle.registration_plate_region"
        or first_hypothesis.get("confidence") != 1.0
        or first_hypothesis.get("region_digest") != crop.get("region_digest")
        or crop.get("contract_type")
        != "hcam.anpr.ground-truth-crop-descriptor.v1"
        or crop.get("source_id") != "DATA-PLATE-GEN-R0"
        or crop.get("source_frame_digest")
        != localization.get("source_frame_digest")
        or crop.get("pixels_ephemeral") is not True
        or crop.get("pixels_persisted") is not False
        or crop.get("token_text_in_contract") is not False
        or crop.get("model_execution_performed") is not False
        or not isinstance(crop.get("width"), int)
        or not 1 <= crop["width"] <= 512
        or not isinstance(crop.get("height"), int)
        or not 1 <= crop["height"] <= 128
        or not isinstance(crop.get("transform_matrix"), list)
        or len(crop["transform_matrix"]) != 9
        or any(
            not isinstance(value, str) or not digest_pattern.fullmatch(value)
            for value in digests
        )
        or prohibited_keys.intersection(all_keys(record))
        or '"token"' in serialized
        or "SYN-" in serialized
    ):
        return Check(
            "w4_ground_truth_crop",
            FAIL,
            "P3.5 W4 generated-only provenance, localization, crop, or zero-retention boundary changed.",
        )
    return Check(
        "w4_ground_truth_crop",
        PASS,
        "P3.5 W4 records one model-free generated ground-truth region and an ephemeral bounded crop without pixels or plate text in evidence.",
    )


def check_w5_latin_ocr_evidence() -> Check:
    path = ROOT / "contracts/phase-3/p3-5-latin-ocr-evaluation.json"
    try:
        payload = path.read_bytes()
        record = json.loads(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("w5_latin_ocr_evidence", FAIL, str(exc))
    canonical = (
        json.dumps(
            record,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    observed_sha256 = hashlib.sha256(payload).hexdigest().upper()
    serialized = payload.decode("utf-8", errors="strict")
    candidates = record.get("candidate_evaluations")
    candidate_map = {
        item.get("candidate_id"): item
        for item in candidates
        if isinstance(item, dict)
    } if isinstance(candidates, list) else {}
    expected = {
        "OCR-L0": {
            "artifact_id": "OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED",
            "artifact_sha256": "sha256:da460f968ce9f88325ac3a34fa302077d6e9b0dcefb16ba3137cd7796f879d06",
            "inventory": "sha256:692cd53d9fb002538e81c9e0b91a6636ade0a82dc9a914809c3598cec686bf84",
            "exact_matches": 7,
            "raw_edit_distance": 18,
        },
        "OCR-L1": {
            "artifact_id": "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED",
            "artifact_sha256": "sha256:4eecc1c6a4623765042e6fc15446da0da110b7d875b6b72b2d351d2b2dbd4da6",
            "inventory": "sha256:7a12028567618504b96caf997e7afdf77ceea54dbab142c09299e3844d53fb6f",
            "exact_matches": 9,
            "raw_edit_distance": 15,
        },
    }
    candidate_failures: list[str] = []
    for candidate_id, expected_item in expected.items():
        item = candidate_map.get(candidate_id, {})
        slices = item.get("slices") if isinstance(item, dict) else None
        slice_map = {
            value.get("layout"): value
            for value in slices
            if isinstance(value, dict)
        } if isinstance(slices, list) else {}
        failure_counts = item.get("failure_counts", {}) if isinstance(item, dict) else {}
        if (
            item.get("artifact_id") != expected_item["artifact_id"]
            or item.get("artifact_sha256") != expected_item["artifact_sha256"]
            or item.get("extracted_inventory_sha256") != expected_item["inventory"]
            or item.get("sample_count") != 12
            or item.get("succeeded") != 12
            or item.get("failed") != 0
            or item.get("exact_matches") != expected_item["exact_matches"]
            or item.get("raw_edit_distance") != expected_item["raw_edit_distance"]
            or sum(failure_counts.values()) != 0
            or item.get("replay_runs") != 20
            or item.get("replay_output_deterministic") is not True
            or item.get("network_attempt_count") != 1
            or item.get("network_access_performed") is not False
            or item.get("final_test_used") is not False
            or item.get("raw_output_persisted") is not False
            or item.get("alternatives_persisted") is not False
            or item.get("identifiers_persisted") is not False
            or item.get("promotion_authorized") is not False
            or slice_map.get("single_line", {}).get("sample_count") != 9
            or slice_map.get("two_line", {}).get("sample_count") != 3
            or slice_map.get("two_line", {}).get("exact_matches") != 0
        ):
            candidate_failures.append(candidate_id)
    if (
        payload != canonical
        or observed_sha256 != P3_5_W5_EVIDENCE_SHA256
        or record.get("contract_type")
        != "hcam.phase3.p3_5.latin-ocr-generated-evaluation.v1"
        or record.get("work_package")
        != "P35-W5_exact_Latin_Paddle_OCR_adapters_and_generated_evaluation"
        or record.get("source_id") != "DATA-PLATE-GEN-R0"
        or record.get("generated_sample_plan")
        != "development_then_validation_no_final_test"
        or record.get("external_input_count") != 0
        or record.get("model_download_count") != 0
        or record.get("camera_or_media_input_count") != 0
        or record.get("real_registration_mark_count") != 0
        or record.get("raw_output_persisted") is not False
        or record.get("alternatives_persisted") is not False
        or record.get("sample_or_region_identifiers_persisted") is not False
        or record.get("plate_text_retention_hours") != 0
        or record.get("quality_threshold_decided") is not False
        or record.get("promotion_authorized") is not False
        or record.get("deployment_authorized") is not False
        or set(candidate_map) != set(expected)
        or candidate_failures
        or "SYN-" in serialized
        or '"raw_text"' in serialized
        or '"alternatives":' in serialized
        or "anprsample_" in serialized
        or "anprregion_" in serialized
        or "B:\\" in serialized
    ):
        return Check(
            "w5_latin_ocr_evidence",
            FAIL,
            "P3.5 W5 exact artifacts, generated-only metrics, replay, final-test isolation, network denial, or zero-retention evidence changed.",
            tuple(candidate_failures),
        )
    return Check(
        "w5_latin_ocr_evidence",
        PASS,
        "P3.5 W5 pins exact L0/L1 inventories and identifier-free 12-sample generated baselines with deterministic replay, no final-test use, and no retained OCR output.",
    )


def check_w6_auxiliary_script_evidence() -> Check:
    path = ROOT / "contracts/phase-3/p3-5-auxiliary-script-evaluation.json"
    try:
        payload = path.read_bytes()
        record = json.loads(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("w6_auxiliary_script_evidence", FAIL, str(exc))
    canonical = (
        json.dumps(
            record,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    observed_sha256 = hashlib.sha256(payload).hexdigest().upper()
    serialized = payload.decode("utf-8", errors="strict")
    devanagari = record.get("devanagari_ocr")
    if not isinstance(devanagari, dict):
        devanagari = {}
    slices = devanagari.get("slices")
    slice_map = (
        {
            item.get("degradation"): item
            for item in slices
            if isinstance(item, dict)
        }
        if isinstance(slices, list)
        else {}
    )
    expected_slices = {
        "clean": (4, 4, 0, 4, 0),
        "low_contrast": (4, 4, 0, 3, 1),
        "downscaled": (4, 4, 0, 3, 1),
    }
    slice_failures = tuple(
        name
        for name, expected in expected_slices.items()
        if (
            slice_map.get(name, {}).get("sample_count"),
            slice_map.get(name, {}).get("succeeded"),
            slice_map.get(name, {}).get("failed"),
            slice_map.get(name, {}).get("exact_matches"),
            slice_map.get(name, {}).get("raw_edit_distance"),
        )
        != expected
    )
    font_rendering = record.get("font_rendering")
    font_map = (
        {
            item.get("candidate_id"): item
            for item in font_rendering
            if isinstance(item, dict)
        }
        if isinstance(font_rendering, list)
        else {}
    )
    expected_fonts = {
        "FONT-D0": (
            "devanagari",
            "sha256:9ce7b04f60e363d8870e5997744cf85cf69d38a4d7d129d364d92a3b14b461d7",
            True,
        ),
        "FONT-G0": (
            "gujarati",
            "sha256:9901d8552f1dd5d2c50dbd4caa6f6e174e74e8264f06594ab259ae6e7b1ac428",
            False,
        ),
    }
    font_failures: list[str] = []
    for candidate_id, (script, digest, ocr_performed) in expected_fonts.items():
        item = font_map.get(candidate_id, {})
        font_slices = item.get("slices") if isinstance(item, dict) else None
        if (
            item.get("script_lane") != script
            or item.get("artifact_sha256") != digest
            or item.get("sample_count") != 12
            or item.get("generated_grapheme_count") != 48
            or item.get("succeeded") != 12
            or item.get("failed") != 0
            or item.get("replay_runs") != 20
            or item.get("replay_pixels_deterministic") is not True
            or item.get("shaping_backend") != "basic_freetype_no_raqm"
            or item.get("complex_shaping_available") is not False
            or item.get("complex_shaping_used") is not False
            or item.get("standalone_graphemes_only") is not True
            or item.get("ocr_execution_performed") is not ocr_performed
            or item.get("generated_text_persisted") is not False
            or item.get("rendered_pixels_persisted") is not False
            or not isinstance(font_slices, list)
            or len(font_slices) != 3
            or any(
                value.get("sample_count") != 4
                or value.get("succeeded") != 4
                or value.get("failed") != 0
                for value in font_slices
                if isinstance(value, dict)
            )
        ):
            font_failures.append(candidate_id)
    failure_counts = devanagari.get("failure_counts", {})
    prohibited = (
        '"raw_text"',
        '"bgr_bytes"',
        '"sample_id"',
        '"region_id"',
        "anprauxsample_",
        "anprauxregion_",
        "B:\\",
    )
    if (
        payload != canonical
        or observed_sha256 != P3_5_W6_EVIDENCE_SHA256
        or record.get("contract_type")
        != "hcam.phase3.p3_5.auxiliary-script-generated-evaluation.v1"
        or record.get("work_package")
        != "P35-W6_exact_Devanagari_Paddle_OCR_lane_and_Gujarati_font_rendering_only"
        or record.get("source_id") != "DATA-PLATE-GEN-R0"
        or record.get("generated_sample_plan")
        != "internal_vocabulary_no_final_test"
        or devanagari.get("candidate_id") != "OCR-D0"
        or devanagari.get("artifact_sha256")
        != "sha256:ac8279d27fc7e8cda559364f9a3c506f43984cf6ba5e1b7a06450458bfe07dfb"
        or devanagari.get("extracted_inventory_sha256")
        != "sha256:e7f6b0b7cf6e937e56540ba5254d6aed9a1958e5b3bca3a3e7c41b29673a2cb6"
        or devanagari.get("sample_count") != 12
        or devanagari.get("reference_grapheme_count") != 48
        or devanagari.get("succeeded") != 12
        or devanagari.get("failed") != 0
        or devanagari.get("exact_matches") != 10
        or devanagari.get("raw_edit_distance") != 2
        or sum(failure_counts.values()) != 0
        or devanagari.get("replay_runs") != 20
        or devanagari.get("replay_output_deterministic") is not True
        or devanagari.get("network_attempt_count") != 1
        or devanagari.get("network_access_performed") is not False
        or devanagari.get("final_test_used") is not False
        or devanagari.get("raw_output_persisted") is not False
        or devanagari.get("alternatives_persisted") is not False
        or devanagari.get("identifiers_persisted") is not False
        or devanagari.get("modifies_registration_mark") is not False
        or devanagari.get("transliteration_performed") is not False
        or slice_failures
        or set(font_map) != set(expected_fonts)
        or font_failures
        or record.get("external_text_input_count") != 0
        or record.get("model_download_count") != 0
        or record.get("camera_or_media_input_count") != 0
        or record.get("real_registration_mark_count") != 0
        or record.get("gujarati_ocr_execution_count") != 0
        or record.get("tesseract_execution_count") != 0
        or record.get("raw_output_persisted") is not False
        or record.get("generated_text_persisted") is not False
        or record.get("rendered_pixels_persisted") is not False
        or record.get("sample_or_region_identifiers_persisted") is not False
        or record.get("plate_text_retention_hours") != 0
        or record.get("modifies_registration_mark") is not False
        or record.get("transliteration_performed") is not False
        or record.get("promotion_authorized") is not False
        or record.get("deployment_authorized") is not False
        or any(value in serialized for value in prohibited)
    ):
        return Check(
            "w6_auxiliary_script_evidence",
            FAIL,
            "P3.5 W6 exact artifact, script isolation, generated-only metrics, network denial, Gujarati rendering-only boundary, or zero-retention evidence changed.",
            (*slice_failures, *font_failures),
        )
    return Check(
        "w6_auxiliary_script_evidence",
        PASS,
        "P3.5 W6 pins exact OCR-D0/FONT-D0/FONT-G0 artifacts, records an identifier-free 12-sample Devanagari baseline and deterministic Gujarati rendering-only evidence, and executes no Gujarati OCR or Tesseract path.",
    )


def check_w7_normalization_evidence() -> Check:
    path = ROOT / "contracts/phase-3/p3-5-normalization-evaluation.json"
    try:
        payload = path.read_bytes()
        record = json.loads(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("w7_normalization_evidence", FAIL, str(exc))
    canonical = (
        json.dumps(
            record,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    observed_sha256 = hashlib.sha256(payload).hexdigest().upper()
    serialized = payload.decode("utf-8", errors="strict")
    slices = record.get("slices")
    slice_map = (
        {
            item.get("script_lane"): item
            for item in slices
            if isinstance(item, dict)
        }
        if isinstance(slices, list)
        else {}
    )
    expected_slices = {
        "latin": (12, 12, 12, 12, 9, 3, 4, 156, 156, 153, 153, 35, 35),
        "devanagari": (12, 12, 12, 12, 0, 12, 0, 48, 48, 45, 45, 3, 3),
        "gujarati": (12, 0, 0, 0, 0, 0, 0, 48, 48, 0, 0, 0, 0),
    }
    slice_failures = tuple(
        name
        for name, expected in expected_slices.items()
        if (
            slice_map.get(name, {}).get("sample_count"),
            slice_map.get(name, {}).get("hypothesis_count"),
            slice_map.get(name, {}).get("normalized_count"),
            slice_map.get(name, {}).get("abstained_count"),
            slice_map.get(name, {}).get("synthetic_format_count"),
            slice_map.get(name, {}).get("unrecognized_format_count"),
            slice_map.get(name, {}).get("case_transform_count"),
            slice_map.get(name, {}).get("reference_scalar_count"),
            slice_map.get(name, {}).get("reference_grapheme_count"),
            slice_map.get(name, {}).get("observed_scalar_count"),
            slice_map.get(name, {}).get("observed_grapheme_count"),
            slice_map.get(name, {}).get("code_point_edit_distance"),
            slice_map.get(name, {}).get("grapheme_edit_distance"),
        )
        != expected
        or slice_map.get(name, {}).get("separator_transform_count") != 0
        or slice_map.get(name, {}).get("ocr_execution_performed") is not False
    )
    calibrations = record.get("calibration_evaluations")
    calibration_map = (
        {
            item.get("candidate_id"): item
            for item in calibrations
            if isinstance(item, dict)
        }
        if isinstance(calibrations, list)
        else {}
    )
    expected_calibrations = {
        "OCR-L0": (10, 6, 0.34, 0.3325),
        "OCR-L1": (10, 7, 0.36, 0.3625),
        "OCR-D0": (10, 7, 0.28, 0.3025),
    }
    calibration_failures: list[str] = []
    for candidate_id, expected in expected_calibrations.items():
        item = calibration_map.get(candidate_id, {})
        bins = item.get("bins") if isinstance(item, dict) else None
        if (
            (
                item.get("sample_count"),
                item.get("correct_count"),
                item.get("expected_calibration_error"),
                item.get("brier_score"),
            )
            != expected
            or item.get("fixture_kind")
            != "deterministic_contract_semantics_not_model_quality"
            or item.get("method")
            != "identity_generated_baseline_five_equal_width_bins"
            or item.get("quality_threshold_approved") is not False
            or item.get("promotion_authorized") is not False
            or not isinstance(bins, list)
            or len(bins) != 5
            or any(
                not isinstance(bin_item, dict)
                or bin_item.get("bin_index") != index
                or bin_item.get("sample_count") != 2
                for index, bin_item in enumerate(bins)
            )
        ):
            calibration_failures.append(candidate_id)
    prohibited = (
        '"raw_text"',
        '"nfc_value"',
        '"normalized_display_candidate"',
        '"graphemes"',
        '"raw_hypothesis_digest"',
        '"sample_id"',
        '"region_id"',
        '"result_id"',
        "SYN-",
        "anprsample_",
        "anprauxsample_",
        "B:\\",
    )
    if (
        payload != canonical
        or observed_sha256 != P3_5_W7_EVIDENCE_SHA256
        or record.get("contract_type")
        != "hcam.phase3.p3_5.normalization-generated-evaluation.v1"
        or record.get("work_package")
        != "P35-W7_normalization_grapheme_metrics_calibration_and_abstention"
        or record.get("source_id") != "DATA-PLATE-GEN-R0"
        or record.get("runtime_id") != "cpython-3.12.13-windows-x86_64"
        or record.get("python_version") != "3.12.13"
        or record.get("regex_version") != "2026.7.19"
        or record.get("unicode_version") != "15.0.0"
        or record.get("replay_runs") != 20
        or record.get("replay_output_deterministic") is not True
        or record.get("network_attempt_count") != 1
        or record.get("network_access_performed") is not False
        or set(slice_map) != set(expected_slices)
        or slice_failures
        or set(calibration_map) != set(expected_calibrations)
        or calibration_failures
        or record.get("model_execution_count") != 0
        or record.get("model_download_count") != 0
        or record.get("external_text_input_count") != 0
        or record.get("camera_or_media_input_count") != 0
        or record.get("real_registration_mark_count") != 0
        or record.get("gujarati_ocr_execution_count") != 0
        or record.get("tesseract_execution_count") != 0
        or record.get("consensus_execution_count") != 0
        or record.get("operational_acceptance_count") != 0
        or record.get("raw_output_persisted") is not False
        or record.get("normalized_output_persisted") is not False
        or record.get("grapheme_values_persisted") is not False
        or record.get("alternatives_persisted") is not False
        or record.get("sample_region_or_result_identifiers_persisted") is not False
        or record.get("plate_text_retention_hours") != 0
        or record.get("quality_threshold_decided") is not False
        or record.get("promotion_authorized") is not False
        or record.get("deployment_authorized") is not False
        or any(value in serialized for value in prohibited)
    ):
        return Check(
            "w7_normalization_evidence",
            FAIL,
            "P3.5 W7 runtime pins, raw-preserving normalization, grapheme metrics, candidate-local calibration, mandatory abstention, or zero-retention evidence changed.",
            (*slice_failures, *calibration_failures),
        )
    return Check(
        "w7_normalization_evidence",
        PASS,
        "P3.5 W7 pins Python/Unicode/regex semantics, records identifier-free normalization and calibration contract fixtures, keeps every result abstained while quality thresholds remain unapproved, and persists no text or grapheme values.",
    )


def check_w8_consensus_evidence() -> Check:
    path = ROOT / "contracts/phase-3/p3-5-consensus-evaluation.json"
    try:
        payload = path.read_bytes()
        record = json.loads(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("w8_consensus_evidence", FAIL, str(exc))
    canonical = (
        json.dumps(
            record,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    observed_sha256 = hashlib.sha256(payload).hexdigest().upper()
    serialized = payload.decode("utf-8", errors="strict")
    scenarios = record.get("scenario_evaluations")
    scenario_map = (
        {
            item.get("scenario"): item
            for item in scenarios
            if isinstance(item, dict)
        }
        if isinstance(scenarios, list)
        else {}
    )
    expected_scenarios = {
        "agreement": (5, 1, 1, 0),
        "cross_boundary_isolation": (4, 4, 4, 0),
        "disagreement": (5, 1, 1, 0),
        "duplicate_rejection": (2, 1, 1, 1),
        "epoch_reset": (2, 2, 2, 0),
        "event_time_window": (2, 1, 1, 0),
        "out_of_order_rejection": (2, 1, 1, 1),
        "overload": (257, 257, 257, 0),
        "track_end": (2, 1, 1, 0),
    }
    scenario_failures = tuple(
        name
        for name, expected in expected_scenarios.items()
        if (
            scenario_map.get(name, {}).get("execution_count"),
            scenario_map.get(name, {}).get("closed_result_count"),
            scenario_map.get(name, {}).get("abstained_result_count"),
            scenario_map.get(name, {}).get("violation_count"),
        )
        != expected
    )
    prohibited = (
        '"nfc_value":',
        '"normalized_display_candidate":',
        '"raw_hypothesis_digest":',
        '"ranked_votes":',
        '"stream_id":',
        '"track_id":',
        '"tracker_epoch":',
        '"winning_candidate":',
        "SYN-",
        "anprsample_",
        "anprregion_",
        "str_000000",
        "epoch_000000",
        "trk_000000",
        "B:\\",
    )
    if (
        payload != canonical
        or observed_sha256 != P3_5_W8_EVIDENCE_SHA256
        or record.get("contract_type")
        != "hcam.phase3.p3_5.consensus-generated-evaluation.v1"
        or record.get("work_package")
        != "P35-W8_bounded_synthetic_track_local_consensus"
        or record.get("source_id") != "DATA-PLATE-GEN-R0"
        or record.get("grouping_key") != "stream_id_tracker_epoch_track_id"
        or record.get("voting_method") != "exact_string_confidence_weighted"
        or record.get("replay_runs") != 20
        or record.get("replay_output_deterministic") is not True
        or record.get("maximum_observations") != 5
        or record.get("maximum_event_time_window_ms") != 2_000
        or record.get("maximum_active_states_per_stream") != 256
        or record.get("maximum_active_states_observed") != 256
        or record.get("consensus_execution_count") != 281
        or record.get("consensus_closed_result_count") != 269
        or record.get("consensus_abstained_result_count") != 269
        or record.get("duplicate_rejection_count") != 1
        or record.get("out_of_order_rejection_count") != 1
        or record.get("cross_stream_epoch_or_track_merge_count") != 0
        or set(scenario_map) != set(expected_scenarios)
        or scenario_failures
        or record.get("network_attempt_count") != 1
        or record.get("network_access_performed") is not False
        or record.get("model_execution_count") != 0
        or record.get("model_download_count") != 0
        or record.get("external_text_input_count") != 0
        or record.get("camera_or_media_input_count") != 0
        or record.get("real_registration_mark_count") != 0
        or record.get("accepted_value_count") != 0
        or record.get("operational_event_count") != 0
        or record.get("threshold_configuration_approved") is not False
        or record.get("minimum_support") is not None
        or record.get("minimum_margin") is not None
        or record.get("plate_or_normalized_text_persisted") is not False
        or record.get("ranked_votes_persisted") is not False
        or record.get("stream_epoch_or_track_identifiers_persisted") is not False
        or record.get("plate_text_retention_hours") != 0
        or record.get("promotion_authorized") is not False
        or record.get("deployment_authorized") is not False
        or any(value in serialized for value in prohibited)
    ):
        return Check(
            "w8_consensus_evidence",
            FAIL,
            "P3.5 W8 bounds, deterministic exact-string voting, anonymous grouping, mandatory abstention, or zero-retention evidence changed.",
            scenario_failures,
        )
    return Check(
        "w8_consensus_evidence",
        PASS,
        "P3.5 W8 records 20/20 deterministic bounded consensus replay, rejects duplicate and out-of-order observations, keeps stream/epoch/track state isolated, and emits only abstaining identifier-free aggregate evidence while thresholds remain unapproved.",
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
    technical = decisions[: len(TECHNICAL_DECISION_IDS)]
    runtime_research = (
        decisions[-2] if len(decisions) >= 2 and isinstance(decisions[-2], dict) else {}
    )
    start = decisions[-1] if decisions and isinstance(decisions[-1], dict) else {}
    if (
        actual_ids != DECISION_IDS
        or any(
            not isinstance(item, dict)
            or item.get("status") != "owner_approved"
            or item.get("selected_option") != "A"
            for item in technical
        )
        or runtime_research.get("decision_id") != "D-P3.5-RUNTIME-RESEARCH"
        or runtime_research.get("status")
        != "owner_accepted_restricted_evidence_complete"
        or start.get("decision_id") != "D-P3.5-START"
        or start.get("status") != "owner_authorized_generated_only_staged"
        or start.get("selected_option") != "A"
        or start.get("owner_statement_received") != "D-P3.5-START"
        or start.get("effective") is not True
        or record.get("status")
        != "implementation_authorized_generated_only_staged"
        or record.get("scope")
        != "phase3.p3_5.synthetic_anpr.generated_only_local_implementation"
        or record.get("manual_gate_count") != 0
        or record.get("owner_decisions_completed") != 5
        or record.get("owner_decisions_record") != "p3-5-owner-decisions.json"
        or record.get("artifact_research_authorization_record")
        != "p3-5-artifact-research-authorization.json"
        or record.get("artifact_review_evidence_record")
        != "p3-5-artifact-review-evidence.json"
        or record.get("artifact_review_acceptance_record")
        != "p3-5-artifact-review-acceptance.json"
        or record.get("runtime_research_authorization_record")
        != "p3-5-runtime-research-authorization.json"
        or record.get("runtime_research_evidence_record")
        != "p3-5-runtime-research-evidence.json"
        or record.get("runtime_sbom_record") != "p3-5-runtime-sbom.cdx.json"
        or record.get("runtime_license_review_record")
        != "p3-5-runtime-license-review.json"
        or record.get("runtime_review_proposal_record")
        != "p3-5-runtime-review-proposal.json"
        or record.get("implementation_authorized") is not True
    ):
        return Check(
            "owner_decisions",
            FAIL,
            "P3.5 owner gates were changed without an explicit decision record.",
        )
    return Check(
        "owner_decisions",
        PASS,
        "Artifact and runtime evidence are accepted and D-P3.5-START authorizes only the staged generated-only implementation boundary.",
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
        for decision_id, value in zip(
            TECHNICAL_DECISION_IDS, expected_values, strict=True
        )
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
        TECHNICAL_DECISION_IDS,
    )


def check_start_authorization() -> Check:
    try:
        record = _json(START_AUTHORIZATION_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("start_authorization", FAIL, str(exc))
    prerequisites = record.get("prerequisites")
    if not isinstance(prerequisites, list):
        return Check(
            "start_authorization", FAIL, "P3.5 start prerequisites must be a list."
        )
    prerequisite_statuses = tuple(
        str(item.get("status"))
        for item in prerequisites
        if isinstance(item, dict)
    )
    runtime_prerequisite = (
        prerequisites[-1]
        if prerequisites and isinstance(prerequisites[-1], dict)
        else {}
    )
    artifacts = record.get("allowed_artifacts")
    artifact_records = (
        {
            str(item.get("artifact_id")): item
            for item in artifacts
            if isinstance(item, dict)
        }
        if isinstance(artifacts, list)
        else {}
    )
    paddle_actions = [
        "safe_extract_in_external_local_quarantine",
        "load_for_generated_only_local_inference",
    ]
    font_actions = ["load_for_deterministic_generated_rendering"]
    expected_artifacts = {
        "OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED": ("OCR-L0", paddle_actions),
        "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED": ("OCR-L1", paddle_actions),
        "OCR-D0-PPOCRV5-DEVANAGARI-INFER-PROPOSED": ("OCR-D0", paddle_actions),
        "FONT-G0-NOTO-SANS-GUJARATI-VARIABLE-PROPOSED": ("FONT-G0", font_actions),
        "FONT-D0-NOTO-SANS-DEVANAGARI-VARIABLE-PROPOSED": ("FONT-D0", font_actions),
    }
    blocked_artifacts = record.get("blocked_reviewed_artifacts")
    blocked_records = (
        {
            str(item.get("artifact_id")): item
            for item in blocked_artifacts
            if isinstance(item, dict)
        }
        if isinstance(blocked_artifacts, list)
        else {}
    )
    allowed_runtime = record.get("allowed_runtime")
    expected_work_packages = {
        "P35-W1_contracts_token_policy_and_prohibited_input_guardrails",
        "P35-W3_deterministic_non_issuable_generator_and_sealed_splits",
        "P35-W4_plate_localization_contract_and_generated_ground_truth_crop_path_only",
        "P35-W5_exact_Latin_Paddle_OCR_adapters_and_generated_evaluation",
        "P35-W6_exact_Devanagari_Paddle_OCR_lane_and_Gujarati_font_rendering_only",
        "P35-W7_normalization_confidence_abstention_and_bounded_consensus",
        "P35-W8_zero_retention_aggregate_evidence_security_and_documentation",
    }
    required_prohibitions = {
        "unlisted_model_weight_font_dataset_dictionary_or_source_artifact_use",
        "any_artifact_or_dependency_network_download",
        "repository_dependency_lockfile_or_container_change",
        "application_migration_public_api_background_worker_or_persistent_plate_storage_change",
        "model_training_finetuning_or_PLATE-D0_checkpoint_creation",
        "OCR-G0_or_OCR-G1_Tesseract_loading_or_execution",
        "arbitrary_file_URL_upload_or_external_text_input",
        "physical_camera_onvif_media_or_sentinel_stream_access",
        "real_public_private_government_police_or_scraped_plate_media",
        "real_registration_mark_owner_vehicle_or_government_record_processing",
        "identity_biometric_reidentification_or_cross_camera_linkage",
        "watchlist_matching_operational_alerting_autonomous_action_or_enforcement",
        "pilot_production_or_statewide_deployment",
        "remote_git_push_pull_request_or_merge",
        "p3_6_or_later_work",
    }
    expected_runtime_actions = [
        "install_from_exact_local_wheelhouse",
        "import_exact_reviewed_packages",
        "execute_exact_paddle_artifacts_on_generated_inputs_only",
    ]
    expected_blocked = {
        "OCR-G0-TESSDATA-FAST-GUJ-PROPOSED": "OCR-G0",
        "OCR-G1-TESSDATA-BEST-GUJ-PROPOSED": "OCR-G1",
    }
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.start-authorization.v1"
        or record.get("decision_id") != "D-P3.5-START"
        or record.get("owner_statement_received") != "D-P3.5-START"
        or record.get("status") != "owner_authorized_generated_only_staged"
        or record.get("scope")
        != "phase3.p3_5.synthetic_anpr.generated_only_local_implementation"
        or record.get("requested_option")
        != "staged_generated_only_start_after_exact_artifact_review"
        or record.get("authorized_by") != "mayank-admin"
        or not record.get("authorized_at")
        or record.get("effective") is not True
        or record.get("implementation_authorized") is not True
        or record.get("evidence_package_digest")
        != P3_5_RUNTIME_EVIDENCE_PACKAGE_DIGEST
        or record.get("evidence_repository_head")
        != P3_5_RUNTIME_EVIDENCE_REPOSITORY_HEAD
        or record.get("allowed_network_actions") != []
        or set(artifact_records) != set(expected_artifacts)
        or any(
            artifact_records[artifact_id].get("candidate_id") != candidate_id
            or artifact_records[artifact_id].get("sha256")
            != REVIEWED_ARTIFACT_SHA256[artifact_id]
            or artifact_records[artifact_id].get("allowed_actions") != actions
            for artifact_id, (candidate_id, actions) in expected_artifacts.items()
        )
        or set(blocked_records) != set(expected_blocked)
        or any(
            blocked_records[artifact_id].get("candidate_id") != candidate_id
            or blocked_records[artifact_id].get("sha256")
            != REVIEWED_ARTIFACT_SHA256[artifact_id]
            or blocked_records[artifact_id].get("reason")
            != "exact_Tesseract_5_engine_and_native_SBOM_unresolved"
            for artifact_id, candidate_id in expected_blocked.items()
        )
        or not isinstance(allowed_runtime, dict)
        or allowed_runtime.get("python_version") != "3.12.13"
        or allowed_runtime.get("external_runtime_root")
        != "E:\\h-cam-research-cache\\phase-3\\p3-5-runtime"
        or allowed_runtime.get("runtime_sbom_sha256") != P3_5_RUNTIME_SBOM_SHA256
        or allowed_runtime.get("network_access") is not False
        or allowed_runtime.get("repository_dependency_or_lockfile_change") is not False
        or allowed_runtime.get("tesseract_runtime_authorized") is not False
        or allowed_runtime.get("permitted_actions") != expected_runtime_actions
        or allowed_runtime.get("direct_packages")
        != [
            "paddleocr==3.7.0",
            "paddlepaddle==3.3.1",
            "pillow==12.3.0",
            "regex==2026.7.19",
        ]
        or set(record.get("allowed_work_packages", [])) != expected_work_packages
        or set(record.get("prohibited_actions", [])) != required_prohibitions
        or prerequisite_statuses
        != (
            "owner_approved",
            "owner_approved",
            "owner_approved",
            "owner_approved",
            "owner_accepted",
            "owner_accepted",
        )
        or runtime_prerequisite.get("evidence_record")
        != "p3-5-runtime-research-evidence.json"
        or runtime_prerequisite.get("sbom_record")
        != "p3-5-runtime-sbom.cdx.json"
        or runtime_prerequisite.get("license_review_record")
        != "p3-5-runtime-license-review.json"
    ):
        return Check(
            "start_authorization",
            FAIL,
            "D-P3.5-START is unbound, widened, network-enabled, or missing a prerequisite or continuing block.",
        )
    return Check(
        "start_authorization",
        PASS,
        "D-P3.5-START is digest-bound to five loadable artifacts, two blocked Tesseract artifacts, the exact external runtime, and zero network actions.",
        ("D-P3.5-START",),
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


def check_artifact_review_evidence() -> Check:
    try:
        record = _json(ARTIFACT_REVIEW_EVIDENCE_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("artifact_review_evidence", FAIL, str(exc))
    artifacts = record.get("artifacts")
    observed = (
        {
            str(item.get("artifact_id")): str(item.get("sha256"))
            for item in artifacts
            if isinstance(item, dict)
        }
        if isinstance(artifacts, list)
        else {}
    )
    inspection = record.get("inspection")
    scan = record.get("defender_scan")
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.artifact-review-evidence.v1"
        or record.get("evidence_id") != "P3.5-EXACT-ARTIFACT-REVIEW-R1"
        or record.get("authorization_id") != "D-P3.5-ARTIFACT-RESEARCH"
        or record.get("proposal_sha256")
        != "8A027E0C8310C900C7DCA7BDFF0144B9E4E003BCAC1A31853C501226165EAD69"
        or record.get("status")
        != "artifact_evidence_complete_runtime_research_pending"
        or record.get("artifact_count") != 7
        or observed != REVIEWED_ARTIFACT_SHA256
        or record.get("implementation_authorized") is not False
        or not isinstance(inspection, dict)
        or inspection.get("artifact_bytes") != 117617083
        or inspection.get("passive_structure_status") != "pass"
        or inspection.get("archive_extraction_performed") is not False
        or inspection.get("runtime_execution_performed") is not False
        or not isinstance(scan, dict)
        or scan.get("engine") != "Microsoft Defender"
        or scan.get("exit_code") != 0
        or scan.get("finding") != "no_threats_found"
    ):
        return Check(
            "artifact_review_evidence",
            FAIL,
            "Exact artifact hashes, passive inspection, or Defender evidence changed.",
        )
    return Check(
        "artifact_review_evidence",
        PASS,
        "Seven exact artifacts are hashed, passively inspected, and locally scanned without extraction or execution.",
        tuple(REVIEWED_ARTIFACT_SHA256),
    )


def check_artifact_review_acceptance() -> Check:
    try:
        record = _json(ARTIFACT_REVIEW_ACCEPTANCE_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("artifact_review_acceptance", FAIL, str(exc))
    evidence_sha256 = hashlib.sha256(
        ARTIFACT_REVIEW_EVIDENCE_PATH.read_bytes()
    ).hexdigest().upper()
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.artifact-review-acceptance.v1"
        or record.get("decision_id") != "P3.5-EXACT-ARTIFACT-REVIEW-R1"
        or record.get("artifact_evidence_id")
        != "P3.5-EXACT-ARTIFACT-REVIEW-R1"
        or record.get("accepted_by") != "mayank-admin"
        or record.get("accepted_repository_head")
        != P3_5_ACCEPTED_ARTIFACT_REPOSITORY_HEAD
        or record.get("evidence_package_digest")
        != P3_5_ACCEPTED_ARTIFACT_PACKAGE_DIGEST
        or record.get("artifact_evidence_sha256")
        != P3_5_ARTIFACT_EVIDENCE_SHA256
        or evidence_sha256 != P3_5_ARTIFACT_EVIDENCE_SHA256
        or record.get("documented_limitations_accepted") is not True
        or record.get("implementation_authorized") is not False
        or record.get("status") != "accepted"
    ):
        return Check(
            "artifact_review_acceptance",
            FAIL,
            "The exact artifact evidence acceptance is missing, changed, or widened.",
        )
    return Check(
        "artifact_review_acceptance",
        PASS,
        "mayank-admin accepted artifact evidence R1 at its exact historical package digest without implementation authority.",
        (P3_5_ACCEPTED_ARTIFACT_PACKAGE_DIGEST,),
    )


def check_artifact_sbom() -> Check:
    try:
        record = _json(ARTIFACT_SBOM_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("artifact_sbom", FAIL, str(exc))
    components = record.get("components")
    observed: dict[str, str] = {}
    runtime_flags: list[str] = []
    licenses: set[str] = set()
    if isinstance(components, list):
        for component in components:
            if not isinstance(component, dict):
                continue
            hashes = component.get("hashes")
            properties = component.get("properties")
            component_licenses = component.get("licenses")
            if isinstance(hashes, list):
                for item in hashes:
                    if isinstance(item, dict) and item.get("alg") == "SHA-256":
                        observed[str(component.get("bom-ref"))] = str(
                            item.get("content")
                        )
            if isinstance(properties, list):
                runtime_flags.extend(
                    str(item.get("value"))
                    for item in properties
                    if isinstance(item, dict)
                    and item.get("name") == "hcam:runtimeAuthorized"
                )
            if isinstance(component_licenses, list):
                for item in component_licenses:
                    if isinstance(item, dict) and isinstance(item.get("license"), dict):
                        licenses.add(str(item["license"].get("id")))
    expected = {
        f"hcam:p3.5:{candidate}": digest
        for candidate, digest in zip(
            ("OCR-L0", "OCR-L1", "OCR-D0", "OCR-G0", "OCR-G1", "FONT-G0", "FONT-D0"),
            REVIEWED_ARTIFACT_SHA256.values(),
            strict=True,
        )
    }
    component_count = len(components) if isinstance(components, list) else -1
    if (
        record.get("bomFormat") != "CycloneDX"
        or record.get("specVersion") != "1.6"
        or component_count != 7
        or observed != expected
        or runtime_flags != ["false"] * 7
        or licenses != {"Apache-2.0", "OFL-1.1"}
    ):
        return Check(
            "artifact_sbom",
            FAIL,
            "P3.5 exact artifact SBOM is incomplete or widened for runtime use.",
        )
    return Check(
        "artifact_sbom",
        PASS,
        "CycloneDX 1.6 records all seven exact artifacts, hashes, licenses, and blocked runtime state.",
    )


def check_artifact_model_cards() -> Check:
    try:
        record = _json(ARTIFACT_MODEL_CARDS_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("artifact_model_cards", FAIL, str(exc))
    cards = record.get("cards")
    candidate_ids = (
        tuple(str(card.get("candidate_id")) for card in cards if isinstance(card, dict))
        if isinstance(cards, list)
        else ()
    )
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.artifact-model-cards.v1"
        or record.get("status") != "artifact_identity_reviewed_runtime_blocked"
        or record.get("model_execution_performed") is not False
        or candidate_ids != ("OCR-L0", "OCR-L1", "OCR-D0", "OCR-G0", "OCR-G1")
        or not all(
            isinstance(card, dict)
            and card.get("runtime_status") == "blocked"
            and card.get("known_limitations")
            for card in cards or []
        )
    ):
        return Check(
            "artifact_model_cards",
            FAIL,
            "Artifact model cards are missing limitations or permit execution.",
        )
    return Check(
        "artifact_model_cards",
        PASS,
        "Five OCR artifact cards record intended generated-only roles and unresolved evidence.",
        candidate_ids,
    )


def check_runtime_review_proposal() -> Check:
    try:
        record = _json(RUNTIME_REVIEW_PROPOSAL_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("runtime_review_proposal", FAIL, str(exc))
    packages = record.get("proposed_python_packages")
    versions = (
        {
            str(item.get("name")): str(item.get("version"))
            for item in packages
            if isinstance(item, dict)
        }
        if isinstance(packages, list)
        else {}
    )
    next_decision = record.get("next_decision")
    python_runtime = record.get("proposed_python_runtime")
    tesseract = record.get("proposed_tesseract_runtime")
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.runtime-review-proposal.v1"
        or record.get("status") != "proposal_prepared_owner_authorization_pending"
        or record.get("package_downloads_performed") is not False
        or record.get("dependency_or_lockfile_change_performed") is not False
        or record.get("implementation_authorized") is not False
        or record.get("allowed_network_actions") != []
        or versions
        != {
            "paddleocr": "3.7.0",
            "paddlepaddle": "3.3.1",
            "Pillow": "12.3.0",
            "regex": "2026.7.19",
        }
        or not isinstance(next_decision, dict)
        or next_decision.get("decision_id") != "D-P3.5-RUNTIME-RESEARCH"
        or next_decision.get("status") != "pending_owner_authorization"
        or not isinstance(python_runtime, dict)
        or python_runtime.get("selected_version") != "3.12.13"
        or not isinstance(tesseract, dict)
        or tesseract.get("status") != "unresolved"
    ):
        return Check(
            "runtime_review_proposal",
            FAIL,
            "P3.5 runtime proposal is incomplete, executable, or prematurely authorized.",
        )
    return Check(
        "runtime_review_proposal",
        PASS,
        "Python 3.12 and four package versions are proposed; dependency and Tesseract execution remain blocked.",
    )


def check_runtime_research_authorization() -> Check:
    try:
        record = _json(RUNTIME_RESEARCH_AUTHORIZATION_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("runtime_research_authorization", FAIL, str(exc))
    proposal_sha256 = hashlib.sha256(
        RUNTIME_REVIEW_PROPOSAL_PATH.read_bytes()
    ).hexdigest().upper()
    packages = record.get("allowed_direct_packages")
    versions = (
        {
            str(item.get("name")): str(item.get("version"))
            for item in packages
            if isinstance(item, dict)
        }
        if isinstance(packages, list)
        else {}
    )
    limits = record.get("limits")
    expected_network = [
        "resolve_and_download_binary_python_packages_from_exact_PyPI_hosts",
        "query_PyPI_vulnerability_metadata_for_the_resolved_environment",
    ]
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.runtime-research-authorization.v1"
        or record.get("authorization_id") != "D-P3.5-RUNTIME-RESEARCH"
        or record.get("authorized_by") != "mayank-admin"
        or record.get("accepted_artifact_evidence_id")
        != "P3.5-EXACT-ARTIFACT-REVIEW-R1"
        or record.get("accepted_evidence_package_digest")
        != P3_5_ACCEPTED_ARTIFACT_PACKAGE_DIGEST
        or record.get("proposal_id") != "P3.5-RUNTIME-REVIEW-PROPOSAL-R0"
        or record.get("proposal_sha256") != P3_5_RUNTIME_PROPOSAL_SHA256
        or proposal_sha256 != P3_5_RUNTIME_PROPOSAL_SHA256
        or record.get("status") != "owner_approved_restricted"
        or record.get("implementation_authorized") is not False
        or record.get("dependency_or_lockfile_change_authorized") is not False
        or record.get("tesseract_runtime_authorized") is not False
        or record.get("allowed_network_actions") != expected_network
        or set(record.get("allowed_source_hosts", []))
        != {"files.pythonhosted.org", "pypi.org"}
        or versions
        != {
            "paddleocr": "3.7.0",
            "paddlepaddle": "3.3.1",
            "Pillow": "12.3.0",
            "regex": "2026.7.19",
        }
        or not isinstance(limits, dict)
        or limits.get("python_version") != "3.12.13"
        or limits.get("binary_wheels_only") is not True
        or limits.get("package_source_builds") is not False
        or limits.get("repository_environment_changes") is not False
        or limits.get("environment_proxies") is not False
        or limits.get("import_network_access") is not False
        or limits.get("model_font_media_or_traineddata_loading") is not False
        or limits.get("runtime_constructors_or_inference") is not False
        or limits.get("external_quarantine_root")
        != "E:\\h-cam-research-cache\\phase-3\\p3-5-runtime"
    ):
        return Check(
            "runtime_research_authorization",
            FAIL,
            "The runtime research authorization is not exactly bound, external, or non-runtime.",
        )
    return Check(
        "runtime_research_authorization",
        PASS,
        "D-P3.5-RUNTIME-RESEARCH authorizes four exact direct roots and their binary closure outside Git without model runtime authority.",
        tuple(f"{name}=={version}" for name, version in versions.items()),
    )


def check_runtime_research_evidence() -> Check:
    try:
        record = _json(RUNTIME_RESEARCH_EVIDENCE_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("runtime_research_evidence", FAIL, str(exc))
    inventory = record.get("inventory")
    imports = record.get("import_check")
    defender = record.get("defender_scan")
    audit = record.get("vulnerability_audit")
    python_runtime = record.get("python_runtime")
    direct_packages = record.get("direct_packages")
    package_versions = (
        {
            str(item.get("name")).lower(): str(item.get("version"))
            for item in direct_packages
            if isinstance(item, dict)
        }
        if isinstance(direct_packages, list)
        else {}
    )
    external_hashes = record.get("external_evidence_sha256")
    required_external_files = {
        "defender-scan.json",
        "import-check.json",
        "installed-environment.json",
        "runtime-research-result.json",
        "runtime-sbom.cdx.json",
        "vulnerability-audit.json",
        "wheelhouse.json",
    }
    hashes_are_exact = (
        isinstance(external_hashes, dict)
        and set(external_hashes) == required_external_files
        and all(
            isinstance(value, str)
            and len(value) == 64
            and value == value.upper()
            for value in external_hashes.values()
        )
        and external_hashes.get("runtime-sbom.cdx.json")
        == P3_5_RUNTIME_SBOM_SHA256
    )
    required_blocks = {
        "exact_Tesseract_5_engine_and_native_SBOM_unresolved",
        "OCR-G0_and_OCR-G1_execution_blocked",
        "reviewed_model_and_font_artifacts_not_authorized_for_extraction_or_loading",
        "PLATE-D0_internal_detector_not_built_or_authorized",
        "synthetic_generation_training_and_inference_not_authorized",
        "runtime_license_metadata_not_a_legal_or_redistribution_approval",
        "final_digest_bound_D-P3.5-START_confirmation_pending",
    }
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.runtime-research-evidence.v1"
        or record.get("evidence_id") != "P3.5-RUNTIME-RESEARCH-EVIDENCE-R1"
        or record.get("authorization_id") != "D-P3.5-RUNTIME-RESEARCH"
        or record.get("accepted_artifact_evidence_id")
        != "P3.5-EXACT-ARTIFACT-REVIEW-R1"
        or record.get("accepted_artifact_package_digest")
        != P3_5_ACCEPTED_ARTIFACT_PACKAGE_DIGEST
        or record.get("status") != "complete_pass_final_owner_review_pending"
        or record.get("external_quarantine_root")
        != "E:\\h-cam-research-cache\\phase-3\\p3-5-runtime"
        or record.get("implementation_authorized") is not False
        or record.get("dependency_or_lockfile_change_performed") is not False
        or record.get("model_artifact_extraction_or_loading_performed") is not False
        or not isinstance(python_runtime, dict)
        or python_runtime.get("implementation") != "CPython"
        or python_runtime.get("version") != "3.12.13"
        or package_versions
        != {
            "paddleocr": "3.7.0",
            "paddlepaddle": "3.3.1",
            "pillow": "12.3.0",
            "regex": "2026.7.19",
        }
        or not isinstance(inventory, dict)
        or inventory.get("package_count") != 67
        or inventory.get("wheel_count") != 67
        or inventory.get("wheel_bytes") != 213980084
        or inventory.get("native_file_count") != 185
        or inventory.get("packaged_sensitive_asset_count") != 6
        or inventory.get("packaged_sensitive_assets")
        != [
            {
                "name": "networkx",
                "paths": [
                    "networkx/drawing/tests/baseline/test_display_complex.png",
                    "networkx/drawing/tests/baseline/test_display_empty_graph.png",
                    "networkx/drawing/tests/baseline/test_display_house_with_colors.png",
                    "networkx/drawing/tests/baseline/test_display_labels_and_colors.png",
                    "networkx/drawing/tests/baseline/test_display_shortest_path.png",
                    "networkx/drawing/tests/baseline/test_house_with_colors.png",
                ],
                "version": "3.6.1",
            }
        ]
        or inventory.get("license_metadata_missing_count") != 0
        or not isinstance(imports, dict)
        or imports.get("status") != "pass_with_all_network_attempts_blocked"
        or imports.get("network_access_performed") is not False
        or imports.get("model_font_or_media_loaded") is not False
        or imports.get("runtime_constructors_or_inference_performed") is not False
        or len(imports.get("blocked_network_attempts", [])) != 1
        or not isinstance(defender, dict)
        or defender.get("exit_code") != 0
        or defender.get("finding") != "no_threats_found"
        or not defender.get("engine_version")
        or not defender.get("signature_version")
        or not isinstance(audit, dict)
        or audit.get("dependency_count") != 67
        or audit.get("vulnerability_count") != 0
        or audit.get("status") != "pass_no_known_vulnerabilities"
        or not hashes_are_exact
        or set(record.get("remaining_blocks", [])) != required_blocks
    ):
        return Check(
            "runtime_research_evidence",
            FAIL,
            "P3.5 runtime evidence is incomplete, changed, executable, or not bound to the accepted artifact packet.",
        )
    return Check(
        "runtime_research_evidence",
        PASS,
        "The exact 67-wheel closure, scans, audit, and network-denied imports pass without implementation or model-runtime authority.",
        ("P3.5-RUNTIME-RESEARCH-EVIDENCE-R1",),
    )


def _component_properties(component: dict[str, object]) -> dict[str, str]:
    properties = component.get("properties")
    if not isinstance(properties, list):
        return {}
    return {
        str(item.get("name")): str(item.get("value"))
        for item in properties
        if isinstance(item, dict)
    }


def check_runtime_sbom() -> Check:
    try:
        record = _json(RUNTIME_SBOM_PATH)
        evidence = _json(RUNTIME_RESEARCH_EVIDENCE_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("runtime_sbom", FAIL, str(exc))
    components = record.get("components")
    metadata = record.get("metadata")
    if not isinstance(components, list) or not all(
        isinstance(component, dict) for component in components
    ):
        return Check("runtime_sbom", FAIL, "Runtime SBOM components are invalid.")
    typed_components = [component for component in components if isinstance(component, dict)]
    package_components = [
        component for component in typed_components if component.get("type") == "library"
    ]
    file_components = [
        component for component in typed_components if component.get("type") == "file"
    ]
    wheel_components = [
        component
        for component in file_components
        if "hcam:bytes" in _component_properties(component)
    ]
    native_components = [
        component
        for component in file_components
        if "hcam:distribution" in _component_properties(component)
    ]
    evidence_inventory = evidence.get("inventory")
    expected_package_names = (
        sorted(
            str(item.get("name")).lower()
            for item in evidence_inventory.get("packages", [])
            if isinstance(item, dict)
        )
        if isinstance(evidence_inventory, dict)
        else []
    )
    actual_package_names = sorted(
        str(component.get("name")).lower() for component in package_components
    )
    metadata_properties = (
        _component_properties(metadata)
        if isinstance(metadata, dict)
        else {}
    )
    sbom_sha256 = hashlib.sha256(RUNTIME_SBOM_PATH.read_bytes()).hexdigest().upper()
    if (
        record.get("bomFormat") != "CycloneDX"
        or record.get("specVersion") != "1.6"
        or sbom_sha256 != P3_5_RUNTIME_SBOM_SHA256
        or len(typed_components) != 319
        or len(package_components) != 67
        or len(wheel_components) != 67
        or len(native_components) != 185
        or actual_package_names != expected_package_names
        or any(
            _component_properties(component).get("hcam:runtimeAuthorized")
            != "false"
            for component in typed_components
        )
        or metadata_properties.get("hcam:authorizationId")
        != "D-P3.5-RUNTIME-RESEARCH"
        or metadata_properties.get("hcam:modelLoadingPerformed") != "false"
        or metadata_properties.get("hcam:implementationAuthorized") != "false"
    ):
        return Check(
            "runtime_sbom",
            FAIL,
            "The runtime SBOM is incomplete, changed, or marks a component executable.",
        )
    return Check(
        "runtime_sbom",
        PASS,
        "CycloneDX records 67 packages, 67 wheels, and 185 native files; all 319 components remain runtime unauthorized.",
    )


def check_runtime_license_review() -> Check:
    try:
        record = _json(RUNTIME_LICENSE_REVIEW_PATH)
        evidence = _json(RUNTIME_RESEARCH_EVIDENCE_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Check("runtime_license_review", FAIL, str(exc))
    packages = record.get("packages")
    inventory = evidence.get("inventory")
    if not isinstance(packages, list) or not isinstance(inventory, dict):
        return Check(
            "runtime_license_review", FAIL, "Runtime license inventory is invalid."
        )
    inventory_names = sorted(
        str(item.get("name")).lower()
        for item in inventory.get("packages", [])
        if isinstance(item, dict)
    )
    license_names = sorted(
        str(item.get("name")).lower()
        for item in packages
        if isinstance(item, dict)
    )
    if (
        record.get("contract_format")
        != "hcam.phase3.p3_5.runtime-license-review.v1"
        or record.get("evidence_id") != "P3.5-RUNTIME-LICENSE-REVIEW-R1"
        or record.get("authorization_id") != "D-P3.5-RUNTIME-RESEARCH"
        or record.get("status") != "metadata_complete_legal_review_deferred"
        or record.get("package_count") != 67
        or record.get("metadata_missing_count") != 0
        or record.get("legal_approval_performed") is not False
        or record.get("implementation_or_redistribution_authorized") is not False
        or len(packages) != 67
        or license_names != inventory_names
        or any(
            not isinstance(item, dict)
            or not item.get("license_summary")
            or "raw_license" in item
            or not isinstance(item.get("review_flags"), list)
            for item in packages
        )
    ):
        return Check(
            "runtime_license_review",
            FAIL,
            "Runtime license metadata is incomplete or incorrectly grants legal, redistribution, or implementation approval.",
        )
    return Check(
        "runtime_license_review",
        PASS,
        "License metadata covers all 67 packages while legal and redistribution approval remain explicitly deferred.",
    )


def check_documentation_sync() -> Check:
    required = {
        "README.md": (
            "P3.5",
            "tools/phase35_artifact_research.py",
            "tools/phase35_runtime_research.py",
            "tools/phase35_readiness.py",
            "tools/phase35_latin_ocr.py",
            "tools/phase35_auxiliary_ocr.py",
            "tools/phase35_normalization.py",
            "tools/phase35_consensus.py",
        ),
        "contracts/phase-3/README.md": (
            "p3-5-anpr-contracts.json",
            "p3-5-ground-truth-crop-v1.json",
            "p3-5-latin-ocr-evaluation.json",
            "p3-5-auxiliary-script-evaluation.json",
            "p3-5-normalization-evaluation.json",
            "p3-5-consensus-evaluation.json",
            "p3-5-sealed-splits-v1.json",
            "p3-5-artifact-review-evidence.json",
            "p3-5-artifact-review-acceptance.json",
            "p3-5-artifact-model-cards.json",
            "p3-5-artifact-review-proposal.json",
            "p3-5-artifact-research-authorization.json",
            "p3-5-artifact-sbom.cdx.json",
            "p3-5-owner-decisions.json",
            "p3-5-planning-authorization.json",
            "p3-5-entry-gates.json",
            "p3-5-start-authorization.json",
            "p3-5-runtime-review-proposal.json",
            "p3-5-runtime-research-authorization.json",
            "p3-5-runtime-research-evidence.json",
            "p3-5-runtime-sbom.cdx.json",
            "p3-5-runtime-license-review.json",
        ),
        "docs/phase-3/README.md": (
            "[P3.5 W1 contracts and guardrails](p3-5-w1-contracts-guardrails.md)",
            "[P3.5 W3 deterministic generator and sealed splits](p3-5-w3-generator-splits.md)",
            "[P3.5 W4 ground-truth localization and crop](p3-5-w4-ground-truth-crop.md)",
            "[P3.5 W5 exact Latin PaddleOCR baseline](p3-5-w5-latin-ocr.md)",
            "[P3.5 W6 auxiliary scripts](p3-5-w6-auxiliary-scripts.md)",
            "[P3.5 W7 normalization and abstention](p3-5-w7-normalization-abstention.md)",
            "[P3.5 W8 bounded consensus](p3-5-w8-bounded-consensus.md)",
            "[P3.5 artifact model cards](p3-5-artifact-model-cards.md)",
            "[P3.5 exact artifact review evidence](p3-5-artifact-review-evidence.md)",
            "[P3.5 exact artifact review acceptance](p3-5-artifact-review-acceptance.md)",
            "[P3.5 artifact research authorization](p3-5-artifact-research-authorization.md)",
            "[P3.5 artifact review proposal](p3-5-artifact-review-proposal.md)",
            "[P3.5 owner decisions](p3-5-owner-decisions.md)",
            "[P3.5 plan](p3-5-plan.md)",
            "[P3.5 owner decision packet](p3-5-decision-packet.md)",
            "[P3.5 generated-only start authorization](p3-5-start-authorization.md)",
            "[P3.5 start intent](p3-5-start-intent.md)",
            "[P3.5 runtime review proposal](p3-5-runtime-review-proposal.md)",
            "[P3.5 runtime research authorization](p3-5-runtime-research-authorization.md)",
            "[P3.5 runtime research evidence](p3-5-runtime-research-evidence.md)",
        ),
        "docs/phase-3/decision-register.md": (
            "DR-0035",
            "DR-0037",
            "DR-0039",
            "DR-0040",
            "DR-0041",
            "D-P3.5-PLAN-AUTH",
            "D-P3.5-ARTIFACT-RESEARCH",
            "D-P3.5-START",
        ),
        "docs/phase-3/implementation-backlog.md": (
            "D-P3.4-ACCEPTANCE",
            "D-P3.5-PLAN-AUTH",
            "guarded import evidence are complete",
            "implementation_authorized_generated_only_staged",
            "P35-W1",
            "P35-W3",
            "P35-W4",
            "P35-W5",
            "P35-W6",
            "P35-W7",
            "validated_generated_contract_fixture",
            "P35-W8",
            "58E7E4479DEB554D4B99F0CC1868B4DA61E9DED292E3F11942B740AEF02FC124",
            "P35-W9",
            "not_started",
            "validated_generated_baseline",
            "validated_complete",
        ),
        "docs/phase-3/p3-5-runtime-research-evidence.md": (
            "P3.5-RUNTIME-RESEARCH-EVIDENCE-R1",
            "67 files, 213,980,084 bytes",
            "One IPv6 socket attempt blocked",
            "NetworkX 3.6.1 contains six packaged",
            "D-P3.5-START",
            "RaiDrive",
        ),
        "docs/phase-3/p3-5-start-authorization.md": (
            "915F5E9246A7A656DF528DD54DA6018D7489C6875BF3A77D1A551BAD6EF9AF4D",
            "five exact reviewed artifacts",
            "No artifact download is authorized",
            "Runtime network access is denied",
            "OCR-G0",
            "OCR-G1",
        ),
        "docs/phase-3/p3-5-w1-contracts-guardrails.md": (
            "P35-W1",
            "SYN-XXXX-XXXX",
            "deterministic_seed_only",
            "plate_text_persistence_prohibited",
            "No generator, OCR runtime, model loading, or API",
        ),
        "docs/phase-3/p3-5-w3-generator-splits.md": (
            "P35-W3",
            "20 exact replay runs",
            "p35w3:final_test:v1",
            "token_commitment_persisted",
            "No rendering, OCR, model, artifact, media, API",
        ),
        "docs/phase-3/p3-5-w4-ground-truth-crop.md": (
            "P35-W4",
            "GT-PLATE-R0",
            "procedural geometry marker",
            "512 x 128",
            "Pixels remain ephemeral",
            "PLATE-D0 remains blocked",
        ),
        "docs/phase-3/p3-5-w5-latin-ocr.md": (
            "P35-W5",
            "OCR-L0",
            "OCR-L1",
            "12/12",
            "20/20",
            "0/3",
            "No W5 path uses `B:`",
            "No quality threshold or model-promotion decision has been made",
        ),
        "docs/phase-3/p3-5-w6-auxiliary-scripts.md": (
            "P35-W6",
            "OCR-D0",
            "FONT-D0",
            "FONT-G0",
            "10/12",
            "basic_freetype_no_raqm",
            "Gujarati OCR execution stayed at zero",
            "No W6 path uses `B:`",
        ),
        "docs/phase-3/p3-5-w7-normalization-abstention.md": (
            "P35-W7",
            "validated_generated_contract_fixture",
            "1F233E044976B0B28BD0261CA5B6324403C45B2A158C852B34DCBB7A0144EE8A",
            "regex==2026.7.19",
            "20/20",
            "mandatory abstention",
            "No W7 path uses `B:`",
            "P35-W8",
            "separate validated generated-only package",
        ),
        "docs/phase-3/p3-5-w8-bounded-consensus.md": (
            "P35-W8",
            "validated_generated_contract_fixture",
            "58E7E4479DEB554D4B99F0CC1868B4DA61E9DED292E3F11942B740AEF02FC124",
            "five observations",
            "two seconds",
            "256 active states",
            "20/20",
            "mandatory abstention",
            "No W8 path uses `B:`",
            "P35-W9",
            "not started",
        ),
        ".github/workflows/python-ci.yml": (
            "python tools/phase35_readiness.py --strict",
            "python tools/phase35_contracts.py check",
            "python tools/phase35_latin_ocr.py check-evidence",
            "python tools/phase35_auxiliary_ocr.py check-evidence",
            "python tools/phase35_normalization.py check-evidence",
            "python tools/phase35_consensus.py check-evidence",
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
        check_authorized_w1_w3_w4_package(),
        check_w1_contract_snapshot(),
        check_w3_split_manifest(),
        check_w4_ground_truth_crop(),
        check_w5_latin_ocr_evidence(),
        check_w6_auxiliary_script_evidence(),
        check_w7_normalization_evidence(),
        check_w8_consensus_evidence(),
        check_artifact_proposal(),
        check_owner_decisions_record(),
        check_artifact_research_authorization(),
        check_artifact_review_evidence(),
        check_artifact_review_acceptance(),
        check_artifact_sbom(),
        check_artifact_model_cards(),
        check_runtime_review_proposal(),
        check_runtime_research_authorization(),
        check_runtime_research_evidence(),
        check_runtime_sbom(),
        check_runtime_license_review(),
        check_start_authorization(),
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
        "invalid" if failures else "implementation_authorized_generated_only_staged"
    )
    try:
        digest, _ = package_digest()
    except OSError:
        digest = "UNAVAILABLE"
    return Report(
        status=status,
        scope="phase3.p3_5.synthetic_anpr.generated_only_local_implementation",
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
