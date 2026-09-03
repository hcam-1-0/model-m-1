#!/usr/bin/env python3
"""Verify the evidence-bound, generated-only P3.2 start authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PASS = "pass"
FAIL = "fail"
EXPECTED_RECORD_DIGEST = (
    "4F9CD7645EE20E09FCB27CF13F23B2699724FC87335F209BEC7BFC6DC6A96F4F"
)
EXPECTED_RESEARCH_AUTHORIZATION_DIGEST = (
    "F4F61149EDF838C633ADD6B5D2B3E2828F206E83CDE21E7B1C625215EFD44893"
)
EXPECTED_RESEARCH_MANIFEST_DIGEST = (
    "357317737EDBC2C9320B75F36D42957C016EA056E84459ABA4296BCF1792D8ED"
)
EXPECTED_RESEARCH_EVIDENCE_DIGEST = (
    "81F7C35FF07C4E1C978F87D975510D7D0E7952713BA425166CA0C7FB1FC35035"
)
ACCEPTED_P31_DIGEST = "956F6521E21BF0FB43741F97768194617DE881B1BD1644E03DDC33ED5FDC0618"
EXPECTED_MODEL_CARD_DIGEST = (
    "116FF491EA48679A074AA5A3C4FD011C64B802DAFFA6BF8897D9D51BE18A8559"
)
EXPECTED_SBOM_DIGEST = (
    "369551AB2C04462BB88F555420BF85D8189B65EEC8F87A6290B466D7C56E0F9D"
)
EXPECTED_MODEL_APPROVAL_DIGEST = (
    "56808A8C5F9FCC388A025DD718E7D1972E24403ADE2616C9E333BB81D52F8186"
)
EXPECTED_DATASET_APPROVAL_DIGEST = (
    "910D7083976055269029733D90F70CAFC0F3FE3046716C2C9D683732FC181F64"
)
EXPECTED_RUNTIME_APPROVAL_DIGEST = (
    "8254F905921BC04BC42074A2353EFCAC81A0004BD2FFD2173F473B65DD9B47F7"
)
EXPECTED_START_AUTHORIZATION_DIGEST = (
    "BA36957E4BF3207952E7F01AB584C960710DEE2097C2E65CC7881F648EC93140"
)
MODEL_SHA256 = "427CC366D34E27FF7A03E2899B5E3671425C262EA2291F88BB942BC1CC70B0F7"
MODEL_CARD = "contracts/phase-3/p3-2-model-card.json"
SBOM = "contracts/phase-3/p3-2-sbom.spdx.json"
MODEL_APPROVAL = "contracts/phase-3/p3-2-model-approval.json"
DATASET_APPROVAL = "contracts/phase-3/p3-2-dataset-approval.json"
RUNTIME_APPROVAL = "contracts/phase-3/p3-2-runtime-approval.json"
START_AUTHORIZATION = "contracts/phase-3/p3-2-start-authorization.json"
START_DOCUMENT = "docs/phase-3/p3-2-start-authorization.md"
ENTRY_RECORD = "contracts/phase-3/p3-2-entry-gates.json"
PACKET = "docs/phase-3/p3-2-entry-decision-packet.md"
CANDIDATE = "contracts/phase-3/p3-1/candidates/candidate-det-r0.json"
RESEARCH_AUTHORIZATION = "contracts/phase-3/p3-2-research-authorization.json"
RESEARCH_MANIFEST = "contracts/phase-3/p3-2-research-artifacts.json"
RESEARCH_EVIDENCE = "contracts/phase-3/p3-2-research-evidence.json"
REQUIRED_FILES = (
    ENTRY_RECORD,
    PACKET,
    CANDIDATE,
    RESEARCH_AUTHORIZATION,
    RESEARCH_MANIFEST,
    RESEARCH_EVIDENCE,
    MODEL_CARD,
    SBOM,
    MODEL_APPROVAL,
    DATASET_APPROVAL,
    RUNTIME_APPROVAL,
    START_AUTHORIZATION,
    "contracts/phase-3/p3-2-research-requirements.in",
    "contracts/phase-3/p3-2-research-requirements.lock",
    "contracts/phase-3/p3-0-owner-decisions.json",
    "contracts/phase-3/p3-1-acceptance.json",
    "docs/phase-3/README.md",
    "docs/phase-3/implementation-backlog.md",
    "docs/phase-3/decision-register.md",
    "docs/phase-3/p3-2-research-record.md",
    START_DOCUMENT,
    "tools/phase32_entry_readiness.py",
    "tools/phase32_research_acquire.py",
    "tools/phase32_offline_experiment.py",
    "tests/test_phase32_entry_readiness.py",
    "tests/test_phase32_research_acquire.py",
    "MANIFEST.in",
    ".github/workflows/python-ci.yml",
)
EXPECTED_DECISIONS = [
    ("D-P3.2-001", "owner_authorized"),
    ("D-P3.2-002", "owner_approved_restricted"),
    ("D-P3.2-003", "owner_approved_generated_only"),
    ("D-P3.2-004", "owner_approved_cpu_reference"),
    ("D-P3.2-START", "owner_authorized"),
]
EXPECTED_NON_AUTHORIZATION = {
    "p3_2_work_outside_authorized_start_scope",
    "uncontrolled_or_unmanifested_artifact_acquisition",
    "training_finetuning_or_model_modification",
    "decoder_or_gpu_execution_outside_approved_cpu_reference",
    "networked_inference_or_inference_outside_generated_only_scope",
    "physical_camera_onvif_media_or_sentinel_stream_access",
    "real_team_owned_public_private_government_police_or_scraped_media",
    "public_dataset_download_or_accuracy_evaluation",
    "face_biometric_identity_reidentification_watchlist_or_vehicle_owner_lookup",
    "sensitive_trait_intent_criminality_or_predictive_risk_inference",
    "operational_alerting_or_autonomous_action",
    "pilot_production_or_statewide_deployment",
    "model_or_artifact_redistribution",
    "remote_git_push_pull_request_or_merge",
}
EXPECTED_STILL_PROHIBITED = {
    "physical_camera_onvif_media_or_sentinel_stream_access",
    "real_team_owned_public_private_government_police_or_scraped_media",
    "public_dataset_download_or_accuracy_evaluation",
    "training_finetuning_or_model_modification",
    "face_biometric_identity_reidentification_watchlist_or_vehicle_owner_lookup",
    "sensitive_trait_intent_criminality_or_predictive_risk_inference",
    "operational_alerting_autonomous_action_or_enforcement",
    "pilot_production_statewide_deployment_or_performance_claim",
    "model_or_artifact_redistribution",
    "remote_git_push_pull_request_or_merge",
}
EXPECTED_CLASSES = {
    "object.person",
    "vehicle.bicycle",
    "vehicle.motorcycle",
    "vehicle.car",
    "vehicle.bus",
    "vehicle.truck",
    "object.unknown",
}


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str
    evidence: list[str]


@dataclass(frozen=True)
class EntryReadinessReport:
    status: str
    scope: str
    record_digest: str
    failures: int
    manual_gates: int
    checks: list[CheckResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scope": self.scope,
            "record_digest": self.record_digest,
            "failures": self.failures,
            "manual_gates": self.manual_gates,
            "checks": [asdict(check) for check in self.checks],
        }


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _read_json(relative_path: str) -> dict[str, Any]:
    value = json.loads(_read(relative_path))
    if not isinstance(value, dict):
        raise ValueError(f"{relative_path} must contain a JSON object")
    return value


def canonical_digest(document: dict[str, Any]) -> str:
    canonical = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest().upper()


def check_required_files() -> CheckResult:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        return CheckResult(
            "required_files", FAIL, "Required files are missing.", missing
        )
    return CheckResult(
        "required_files",
        PASS,
        f"All {len(REQUIRED_FILES)} P3.2 start-governance files exist.",
        list(REQUIRED_FILES),
    )


def check_entry_record() -> CheckResult:
    try:
        record = _read_json(ENTRY_RECORD)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("entry_record", FAIL, f"Entry record is invalid: {exc}", [])

    failures: list[str] = []
    digest = canonical_digest(record)
    if digest != EXPECTED_RECORD_DIGEST:
        failures.append("canonical entry record changed without verifier review")
    if record.get("contract_format") != "hcam.phase3.p3_2.entry-gates.v2":
        failures.append("contract format changed")
    if record.get("record_id") != "P3.2-ENTRY-2026-08-24":
        failures.append("record identifier changed")
    if record.get("prepared_on") != "2026-08-24":
        failures.append("prepared date changed")
    if record.get("accountable_owner_id") != "mayank-admin":
        failures.append("accountable owner changed")
    if record.get("status") != "implementation_authorized_generated_only":
        failures.append("P3.2 generated-only authorization state changed")
    expected_start = {
        "expires_on": "2026-09-24",
        "record": START_AUTHORIZATION,
        "status": "authorized_generated_only",
    }
    if record.get("start_authorization") != expected_start:
        failures.append("P3.2 start authorization reference changed")

    decisions = record.get("decisions")
    decision_pairs = (
        [(item.get("decision_id"), item.get("status")) for item in decisions]
        if isinstance(decisions, list)
        and all(isinstance(item, dict) for item in decisions)
        else []
    )
    if decision_pairs != EXPECTED_DECISIONS:
        failures.append("ordered decision inventory or approval states changed")
    start = decisions[-1] if decision_pairs == EXPECTED_DECISIONS else {}
    if start.get("requires") != [item[0] for item in EXPECTED_DECISIONS[:-1]]:
        failures.append("P3.2 start dependencies changed")

    non_authorization = record.get("non_authorization")
    if (
        not isinstance(non_authorization, list)
        or len(non_authorization) != len(EXPECTED_NON_AUTHORIZATION)
        or set(non_authorization) != EXPECTED_NON_AUTHORIZATION
    ):
        failures.append("non-authorization boundary changed or contains duplicates")

    expected_reference = {
        "artifact_eligibility": "approved_restricted",
        "artifact_execution": "offline_research_only_completed",
        "candidate_id": "DET-R0",
        "dataset_candidate_id": "DATA-GEN-R0",
        "family": "YOLOX-Tiny",
        "input_size": 416,
        "model_artifact_downloads": 1,
        "runtime": "onnxruntime_cpu",
        "runtime_status": "owner_approved_cpu_reference",
        "source_evidence_downloads": 4,
    }
    if record.get("planned_reference") != expected_reference:
        failures.append("planned reference boundary changed")

    if failures:
        return CheckResult("entry_record", FAIL, "; ".join(failures), [ENTRY_RECORD])
    return CheckResult(
        "entry_record",
        PASS,
        "All entry decisions authorize only the bounded generated-only P3.2 start.",
        [ENTRY_RECORD, f"canonical_sha256={digest}"],
    )


def check_research_authorization() -> CheckResult:
    files = [RESEARCH_AUTHORIZATION, RESEARCH_MANIFEST]
    try:
        authorization = _read_json(files[0])
        manifest = _read_json(files[1])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("research_authorization", FAIL, str(exc), files)

    failures: list[str] = []
    digest = canonical_digest(authorization)
    manifest_digest = canonical_digest(manifest)
    if digest != EXPECTED_RESEARCH_AUTHORIZATION_DIGEST:
        failures.append("research authorization changed without verifier review")
    if manifest_digest != EXPECTED_RESEARCH_MANIFEST_DIGEST:
        failures.append("research artifact manifest changed without verifier review")
    if authorization.get("decision_id") != "D-P3.2-001":
        failures.append("research decision identity changed")
    if authorization.get("authorized_by") != "mayank-admin":
        failures.append("research accountable owner changed")
    if authorization.get("status") != "owner_authorized":
        failures.append("research authorization is not owner-authorized")
    if (
        authorization.get("authorization_effect")
        != "research_only_no_p3_2_implementation"
    ):
        failures.append("research-only effect changed")
    controls = authorization.get("execution_controls")
    if not isinstance(controls, dict):
        failures.append("research execution controls are missing")
    else:
        expected_controls = {
            "maximum_artifact_bytes": 536870912,
            "cumulative_artifact_limit_bytes": 2147483648,
            "experiment_network_access": "prohibited",
            "training_or_finetuning": "prohibited",
        }
        if any(controls.get(key) != value for key, value in expected_controls.items()):
            failures.append("research size, network, or training controls changed")
    if manifest.get("authorization_id") != authorization.get("record_id"):
        failures.append("research manifest is not bound to the authorization")
    artifacts = manifest.get("artifacts")
    expected_artifact = {
        "artifact_id": "DET-R0-ONNX-UPSTREAM-0.1.1RC0",
        "expected_bytes": 20219662,
        "expected_sha256": "427CC366D34E27FF7A03E2899B5E3671425C262EA2291F88BB942BC1CC70B0F7",
    }
    if not isinstance(artifacts, list) or not any(
        isinstance(item, dict)
        and all(item.get(key) == value for key, value in expected_artifact.items())
        and item.get("research_status")
        == "authorized_for_quarantine_and_offline_research_not_approved_for_hcam"
        for item in artifacts
    ):
        failures.append(
            "exact research artifact identity or non-promotion state changed"
        )
    expected_source_evidence = {
        "SRC-YOLOX-LICENSE-6DDFF482": (
            11371,
            "0EC3668D3274BCF29E8A29E9576D5A2CD96FC78D3C5BEC4387355A796E5D9088",
        ),
        "SRC-YOLOX-ONNX-DEMO-6DDFF482": (
            2536,
            "C51AA9E9A86D8561FE9E318E119A4FBE80D1F93639527B039F403D6ADC65D68F",
        ),
        "SRC-YOLOX-PREPROCESS-6DDFF482": (
            7360,
            "F99B0B1568DAFDE0ACD99F0A1E27A33644885349834D55A9DC632FE691EE352D",
        ),
        "SRC-YOLOX-POSTPROCESS-6DDFF482": (
            5101,
            "E1D6E1D263691AC15FDAA4F891EFA83707DA4AF0FD895BE122459105DF3EE601",
        ),
    }
    observed_source_evidence = {
        item.get("artifact_id"): (
            item.get("expected_bytes"),
            item.get("expected_sha256"),
        )
        for item in artifacts or []
        if isinstance(item, dict)
        and item.get("research_status") == "authorized_source_evidence_not_executable"
        and item.get("source_revision") == "6ddff4824372906469a7fae2dc3206c7aa4bbaee"
    }
    if observed_source_evidence != expected_source_evidence:
        failures.append("immutable license or algorithm evidence changed")
    datasets = manifest.get("dataset_candidates")
    if not isinstance(datasets, list) or not any(
        isinstance(item, dict)
        and item.get("candidate_id") == "DATA-PUB-R0"
        and item.get("status") == "blocked_pending_exact_source_review"
        for item in datasets
    ):
        failures.append("public dataset gate is not fail-closed")
    if failures:
        return CheckResult(
            "research_authorization",
            FAIL,
            "; ".join(failures),
            files,
        )
    return CheckResult(
        "research_authorization",
        PASS,
        "D-P3.2-001 and its immutable research evidence remain bounded; public dataset use stays blocked.",
        [
            *files,
            f"authorization_sha256={digest}",
            f"manifest_sha256={manifest_digest}",
        ],
    )


def check_research_evidence() -> CheckResult:
    files = [
        RESEARCH_EVIDENCE,
        "contracts/phase-3/p3-2-research-requirements.in",
        "contracts/phase-3/p3-2-research-requirements.lock",
        "MANIFEST.in",
    ]
    try:
        evidence = _read_json(RESEARCH_EVIDENCE)
        lock = _read(files[2])
        package_manifest = _read(files[3])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("research_evidence", FAIL, str(exc), files)

    failures: list[str] = []
    digest = canonical_digest(evidence)
    if digest != EXPECTED_RESEARCH_EVIDENCE_DIGEST:
        failures.append("research evidence changed without verifier review")
    artifact = evidence.get("artifact")
    experiment = evidence.get("experiment")
    dataset = evidence.get("dataset")
    security = evidence.get("security_review")
    if (
        not isinstance(artifact, dict)
        or artifact.get("status") != "research_only_not_approved_for_hcam"
    ):
        failures.append("artifact research-only state changed")
    if not isinstance(experiment, dict) or (
        experiment.get("status") != "completed_research_only"
        or experiment.get("accuracy") != "not_measured"
        or experiment.get("deployment_readiness") != "not_assessed"
        or experiment.get("output_sha256") != experiment.get("repeat_output_sha256")
    ):
        failures.append("offline experiment evidence or claim boundary changed")
    if not isinstance(dataset, dict) or (
        dataset.get("public_candidate_status") != "blocked_pending_exact_source_review"
        or dataset.get("public_dataset_downloads") != 0
    ):
        failures.append("public dataset remains insufficiently blocked")
    if (
        not isinstance(security, dict)
        or security.get("result") != "no_known_vulnerabilities_found"
    ):
        failures.append("research dependency audit evidence changed")
    malware_scan = (
        security.get("model_malware_scan") if isinstance(security, dict) else None
    )
    if (
        not isinstance(malware_scan, dict)
        or malware_scan.get("result") != "no_model_threat_detections"
    ):
        failures.append("model malware scan evidence changed")
    required_locks = (
        "numpy==2.5.2",
        "onnx==1.22.0",
        "onnxruntime==1.29.0",
        "--hash=sha256:",
    )
    if any(term not in lock for term in required_locks):
        failures.append("research dependency lock is not version and hash bound")
    if "recursive-include contracts *.md *.json *.in *.lock" not in package_manifest:
        failures.append("research evidence locks are absent from source packages")
    if failures:
        return CheckResult(
            "research_evidence",
            FAIL,
            "; ".join(failures),
            files,
        )
    return CheckResult(
        "research_evidence",
        PASS,
        "One exact artifact completed repeatable generated-input CPU research; accuracy and public dataset claims remain blocked.",
        [*files, f"canonical_sha256={digest}"],
    )


def check_accepted_dependencies() -> CheckResult:
    files = [
        "contracts/phase-3/p3-0-owner-decisions.json",
        "contracts/phase-3/p3-1-acceptance.json",
        ENTRY_RECORD,
    ]
    try:
        p30 = _read_json(files[0])
        p31 = _read_json(files[1])
        entry = _read_json(files[2])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("accepted_dependencies", FAIL, str(exc), files)

    failures: list[str] = []
    if p30.get("status") != "p3_0_accepted":
        failures.append("P3.0 is not accepted")
    if (
        p31.get("record_id") != "D-P3.1-ACCEPTANCE"
        or p31.get("status") != "accepted"
        or p31.get("evidence_package_digest") != ACCEPTED_P31_DIGEST
    ):
        failures.append("P3.1 acceptance identity changed")
    dependencies = entry.get("dependencies")
    expected = {
        "p3_0": {"record_id": "D-P3.0-001", "status": "accepted"},
        "p3_1": {
            "evidence_package_digest": ACCEPTED_P31_DIGEST,
            "record_id": "D-P3.1-ACCEPTANCE",
            "status": "accepted",
        },
    }
    if dependencies != expected:
        failures.append("entry dependency record changed")
    if failures:
        return CheckResult(
            "accepted_dependencies",
            FAIL,
            "; ".join(failures),
            files,
        )
    return CheckResult(
        "accepted_dependencies",
        PASS,
        "P3.0 and the exact digest-bound P3.1 package are accepted dependencies.",
        files,
    )


def check_reference_candidate_blocked() -> CheckResult:
    try:
        candidate = _read_json(CANDIDATE)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("reference_candidate", FAIL, str(exc), [CANDIDATE])

    required_blockers = {
        "exact-checkpoint-unresolved",
        "weight-license-unverified",
        "training-lineage-unverified",
        "model-card-unresolved",
        "sbom-unresolved",
    }
    approval = candidate.get("approval")
    artifact = candidate.get("artifact_identity")
    source = candidate.get("source_reference")
    failures: list[str] = []
    if candidate.get("candidate_id") != "DET-R0":
        failures.append("portable reference candidate changed")
    if candidate.get("eligibility") != "blocked":
        failures.append("DET-R0 is no longer blocked")
    if not isinstance(approval, dict) or approval.get("status") != "pending":
        failures.append("DET-R0 approval is not pending")
    if not isinstance(artifact, dict) or artifact.get("state") != "unresolved":
        failures.append("exact artifact is not unresolved")
    if set(candidate.get("blockers", [])) != required_blockers:
        failures.append("DET-R0 blocker inventory changed")
    if not isinstance(source, dict) or source.get("no_download_performed") is not True:
        failures.append("no-download source evidence changed")
    if failures:
        return CheckResult(
            "reference_candidate",
            FAIL,
            "; ".join(failures),
            [CANDIDATE],
        )
    return CheckResult(
        "reference_candidate",
        PASS,
        "The accepted P3.1 DET-R0 metadata record remains unchanged and blocked; later research evidence is recorded separately.",
        [CANDIDATE, *sorted(required_blockers)],
    )


def check_model_approval() -> CheckResult:
    files = [MODEL_APPROVAL, MODEL_CARD, SBOM]
    try:
        approval, model_card, sbom = (_read_json(path) for path in files)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("model_approval", FAIL, str(exc), files)

    failures: list[str] = []
    expected_digests = {
        MODEL_APPROVAL: EXPECTED_MODEL_APPROVAL_DIGEST,
        MODEL_CARD: EXPECTED_MODEL_CARD_DIGEST,
        SBOM: EXPECTED_SBOM_DIGEST,
    }
    for path, document in zip(files, (approval, model_card, sbom), strict=True):
        if canonical_digest(document) != expected_digests[path]:
            failures.append(f"{path} changed without verifier review")

    artifact = approval.get("artifact")
    expected_artifact = {
        "artifact_id": "DET-R0-ONNX-UPSTREAM-0.1.1RC0",
        "bytes": 20219662,
        "filename": "yolox_tiny.onnx",
        "sha256": MODEL_SHA256,
        "source_release": "0.1.1rc0",
        "source_url": (
            "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/"
            "0.1.1rc0/yolox_tiny.onnx"
        ),
    }
    if (
        approval.get("decision_id") != "D-P3.2-002"
        or approval.get("status") != "owner_approved_restricted"
        or approval.get("approved_by") != "mayank-admin"
        or approval.get("owner_statement") != "d-p3.2 start"
        or artifact != expected_artifact
    ):
        failures.append("exact model approval identity or owner decision changed")

    evidence = approval.get("evidence")
    expected_evidence = {
        "license_sha256": (
            "0EC3668D3274BCF29E8A29E9576D5A2CD96FC78D3C5BEC4387355A796E5D9088"
        ),
        "model_card": MODEL_CARD,
        "research_evidence": RESEARCH_EVIDENCE,
        "sbom": SBOM,
        "source_revision": "6ddff4824372906469a7fae2dc3206c7aa4bbaee",
    }
    if evidence != expected_evidence:
        failures.append("model approval evidence binding changed")
    license_decision = approval.get("license_decision")
    if not isinstance(license_decision, dict) or (
        license_decision.get("local_use") != "approved"
        or license_decision.get("redistribution")
        != "not_authorized_requires_separate_release_review"
    ):
        failures.append("restricted local-use or redistribution boundary changed")

    card_artifact = model_card.get("artifact")
    if (
        model_card.get("candidate_id") != "DET-R0"
        or not isinstance(card_artifact, dict)
        or card_artifact.get("sha256") != MODEL_SHA256
        or set(model_card.get("emitted_taxonomy", [])) != EXPECTED_CLASSES
    ):
        failures.append("model card identity or approved taxonomy changed")
    required_out_of_scope = {
        "accuracy_or_deployment_claims",
        "face_or_biometric_recognition",
        "person_reidentification_or_cross_camera_identity",
        "watchlists_or_government_database_matching",
        "vehicle_owner_lookup",
        "sensitive_trait_intent_or_criminality_inference",
        "autonomous_enforcement_or_operational_alerting",
        "training_finetuning_or_model_modification",
    }
    if set(model_card.get("out_of_scope", [])) != required_out_of_scope:
        failures.append("model-card prohibited-use inventory changed")

    packages = sbom.get("packages")
    model_package = next(
        (
            item
            for item in packages or []
            if isinstance(item, dict) and item.get("SPDXID") == "SPDXRef-Package-DET-R0"
        ),
        None,
    )
    checksums = (
        model_package.get("checksums") if isinstance(model_package, dict) else None
    )
    if (
        sbom.get("spdxVersion") != "SPDX-2.3"
        or not isinstance(packages, list)
        or len(packages) != 9
        or not isinstance(checksums, list)
        or not any(
            item.get("algorithm") == "SHA256"
            and item.get("checksumValue") == MODEL_SHA256
            for item in checksums
            if isinstance(item, dict)
        )
    ):
        failures.append("model SBOM identity or inventory changed")

    if failures:
        return CheckResult("model_approval", FAIL, "; ".join(failures), files)
    return CheckResult(
        "model_approval",
        PASS,
        "D-P3.2-002 binds one exact model artifact to restricted local generated-only use.",
        [*files, f"artifact_sha256={MODEL_SHA256}"],
    )


def check_dataset_approval() -> CheckResult:
    files = [DATASET_APPROVAL]
    try:
        approval = _read_json(DATASET_APPROVAL)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("dataset_approval", FAIL, str(exc), files)

    failures: list[str] = []
    if canonical_digest(approval) != EXPECTED_DATASET_APPROVAL_DIGEST:
        failures.append("generated dataset approval changed without verifier review")
    if (
        approval.get("decision_id") != "D-P3.2-003"
        or approval.get("status") != "owner_approved_generated_only"
        or approval.get("approved_by") != "mayank-admin"
        or approval.get("owner_statement") != "d-p3.2 start"
        or approval.get("candidate_id") != "DATA-GEN-R0"
    ):
        failures.append("generated-only dataset decision changed")
    expected_permitted = {
        "contract_correctness",
        "determinism",
        "runtime_loadability",
        "failure_and_resource_behavior",
        "synthetic_end_to_end_behavior",
    }
    expected_prohibited = {
        "accuracy",
        "fairness",
        "representativeness",
        "real_world_readiness",
        "deployment_readiness",
    }
    if set(approval.get("permitted_claims", [])) != expected_permitted:
        failures.append("generated-only permitted claims changed")
    if set(approval.get("prohibited_claims", [])) != expected_prohibited:
        failures.append("generated-only prohibited claims changed")
    retention = approval.get("retention")
    access = approval.get("access")
    if not isinstance(retention, dict) or (
        retention.get("generated_media_hours") != 0
        or retention.get("raw_media_persistence") != "prohibited"
    ):
        failures.append("zero-media-retention policy changed")
    if not isinstance(access, dict) or access.get("external_sharing") != "prohibited":
        failures.append("generated-input sharing boundary changed")
    if (
        approval.get("consent_or_license")
        != "not_applicable_programmatically_generated_no_external_rightsholder"
    ):
        failures.append("generated-input provenance changed")

    if failures:
        return CheckResult("dataset_approval", FAIL, "; ".join(failures), files)
    return CheckResult(
        "dataset_approval",
        PASS,
        "D-P3.2-003 permits deterministic generated inputs without accuracy or real-world claims.",
        files,
    )


def check_runtime_approval() -> CheckResult:
    files = [RUNTIME_APPROVAL]
    try:
        approval = _read_json(RUNTIME_APPROVAL)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("runtime_approval", FAIL, str(exc), files)

    failures: list[str] = []
    if canonical_digest(approval) != EXPECTED_RUNTIME_APPROVAL_DIGEST:
        failures.append("CPU runtime approval changed without verifier review")
    artifact = approval.get("artifact")
    if (
        approval.get("decision_id") != "D-P3.2-004"
        or approval.get("status") != "owner_approved_cpu_reference"
        or approval.get("approved_by") != "mayank-admin"
        or approval.get("owner_statement") != "d-p3.2 start"
        or not isinstance(artifact, dict)
        or artifact.get("sha256") != MODEL_SHA256
    ):
        failures.append("CPU runtime owner decision or artifact binding changed")

    runtime = approval.get("runtime")
    expected_runtime = {
        "adapter_id": "hcam.yolox_tiny.onnxruntime_cpu",
        "artifact_access": "verified_handle_only",
        "execution_provider": "CPUExecutionProvider",
        "network_access": "denied",
    }
    if runtime != expected_runtime:
        failures.append("CPU-only runtime or network boundary changed")
    input_contract = approval.get("input")
    expected_input = {
        "batch": 1,
        "channel_order": "BGR",
        "dtype": "float32",
        "layout": "NCHW",
        "name": "images",
        "normalization": "none_values_remain_0_to_255",
        "padding": "top_left_letterbox_value_114",
        "resize": "bilinear_ratio_min_416_over_height_416_over_width",
        "shape": [1, 3, 416, 416],
    }
    if input_contract != expected_input:
        failures.append("preprocessing contract changed")
    postprocessing = approval.get("postprocessing")
    expected_mapping = {
        "0": "object.person",
        "1": "vehicle.bicycle",
        "2": "vehicle.car",
        "3": "vehicle.motorcycle",
        "5": "vehicle.bus",
        "7": "vehicle.truck",
        "other": "object.unknown",
    }
    if not isinstance(postprocessing, dict) or (
        postprocessing.get("class_mapping") != expected_mapping
        or postprocessing.get("nms_iou_threshold") != 0.45
        or postprocessing.get("nms_mode") != "class_agnostic"
        or postprocessing.get("score") != "objectness_times_highest_class_probability"
    ):
        failures.append("postprocessing or taxonomy mapping changed")
    parity = approval.get("parity")
    expected_source_hashes = {
        "demo_sha256": (
            "C51AA9E9A86D8561FE9E318E119A4FBE80D1F93639527B039F403D6ADC65D68F"
        ),
        "preprocess_sha256": (
            "F99B0B1568DAFDE0ACD99F0A1E27A33644885349834D55A9DC632FE691EE352D"
        ),
        "postprocess_sha256": (
            "E1D6E1D263691AC15FDAA4F891EFA83707DA4AF0FD895BE122459105DF3EE601"
        ),
    }
    if not isinstance(parity, dict) or any(
        parity.get(key) != value for key, value in expected_source_hashes.items()
    ):
        failures.append("immutable algorithm parity evidence changed")
    limits = approval.get("resource_limits")
    expected_limits = {
        "maximum_batch_size": 1,
        "maximum_candidates_after_nms": 300,
        "maximum_input_pixels": 173056,
        "maximum_resident_memory_bytes": 1073741824,
        "timeout_ms_per_input": 1000,
    }
    if limits != expected_limits:
        failures.append("runtime resource limits changed")
    fail_closed = approval.get("fail_closed")
    if not isinstance(fail_closed, dict) or (
        fail_closed.get("silent_execution_provider_fallback") != "prohibited"
    ):
        failures.append("execution-provider fallback is no longer fail-closed")

    if failures:
        return CheckResult("runtime_approval", FAIL, "; ".join(failures), files)
    return CheckResult(
        "runtime_approval",
        PASS,
        "D-P3.2-004 fixes the CPU-only preprocessing, decoder, taxonomy, and resource contract.",
        files,
    )


def check_start_authorization() -> CheckResult:
    files = [START_AUTHORIZATION]
    try:
        authorization = _read_json(START_AUTHORIZATION)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult("start_authorization", FAIL, str(exc), files)

    failures: list[str] = []
    if canonical_digest(authorization) != EXPECTED_START_AUTHORIZATION_DIGEST:
        failures.append("start authorization changed without verifier review")
    if (
        authorization.get("decision_id") != "D-P3.2-START"
        or authorization.get("status") != "owner_authorized"
        or authorization.get("authorized_by") != "mayank-admin"
        or authorization.get("owner_statement") != "d-p3.2 start"
        or authorization.get("branch") != "codex/phase3-contracts-guardrails"
    ):
        failures.append("explicit start owner decision or branch binding changed")
    expected_entry_decisions = [
        {
            "decision_id": "D-P3.2-001",
            "record": RESEARCH_AUTHORIZATION,
            "status": "owner_authorized",
        },
        {
            "decision_id": "D-P3.2-002",
            "record": MODEL_APPROVAL,
            "status": "owner_approved_restricted",
        },
        {
            "decision_id": "D-P3.2-003",
            "record": DATASET_APPROVAL,
            "status": "owner_approved_generated_only",
        },
        {
            "decision_id": "D-P3.2-004",
            "record": RUNTIME_APPROVAL,
            "status": "owner_approved_cpu_reference",
        },
    ]
    if authorization.get("entry_decisions") != expected_entry_decisions:
        failures.append("start prerequisite decision bindings changed")
    expected_target = {
        "data_source": "DATA-GEN-R0",
        "deployment": "local_development_and_ci_only",
        "hardware_profile": "LAB-LAPTOP-01",
        "model_artifact_id": "DET-R0-ONNX-UPSTREAM-0.1.1RC0",
        "runtime": "onnxruntime_1.29.0_cpu_only",
    }
    if authorization.get("target") != expected_target:
        failures.append("authorized model, data, runtime, or deployment target changed")
    prohibited = authorization.get("still_prohibited")
    if (
        not isinstance(prohibited, list)
        or len(prohibited) != len(EXPECTED_STILL_PROHIBITED)
        or set(prohibited) != EXPECTED_STILL_PROHIBITED
    ):
        failures.append("continuing start prohibitions changed or contain duplicates")
    expected_work = {
        "verified DET-R0 ONNX Runtime CPU adapter behind the existing guarded runtime contract",
        "deterministic generated-frame preprocessing inference postprocessing and approved taxonomy mapping",
        "normalized anonymous observation creation persistence and transactional outbox events",
        "synthetic-lab-only assignment lifecycle activation pause degradation and failure handling",
        "identifier-free metrics audit evidence resource limits fault injection and generated end-to-end tests",
        "documentation packaging and clean-machine validation",
    }
    if set(authorization.get("authorized_work_packages", [])) != expected_work:
        failures.append("authorized work-package inventory changed")
    expires_on = authorization.get("expires_on")
    try:
        expiry = date.fromisoformat(expires_on)
    except (TypeError, ValueError):
        failures.append("start authorization expiry is invalid")
    else:
        if expiry < datetime.now(timezone.utc).date():
            failures.append("start authorization has expired")

    if failures:
        return CheckResult("start_authorization", FAIL, "; ".join(failures), files)
    return CheckResult(
        "start_authorization",
        PASS,
        "D-P3.2-START is valid only for the exact generated-only local CPU work packages.",
        [*files, f"canonical_sha256={EXPECTED_START_AUTHORIZATION_DIGEST}"],
    )


def check_documentation_boundary() -> CheckResult:
    files = [
        PACKET,
        START_DOCUMENT,
        "docs/phase-3/README.md",
        "docs/phase-3/implementation-backlog.md",
        "docs/phase-3/decision-register.md",
    ]
    try:
        packet, start_document, index, backlog, decisions = (
            _read(path) for path in files
        )
    except OSError as exc:
        return CheckResult("documentation_boundary", FAIL, str(exc), files)

    failures: list[str] = []
    required_packet_terms = (
        "Status: `implementation_authorized_generated_only`",
        "Current state: `owner_authorized`.",
        "does not complete P3.2",
        "No physical camera",
    )
    failures.extend(
        f"packet boundary is missing: {term}"
        for term in required_packet_terms
        if term not in packet
    )
    required_start_terms = (
        "Status: `owner_authorized_generated_only_implementation`",
        "Owner statement: `d-p3.2 start`.",
        "It is not P3.2 completion",
        "No physical camera",
    )
    failures.extend(
        f"start document boundary is missing: {term}"
        for term in required_start_terms
        if term not in start_document
    )
    entry_link = "[P3.2 entry decision packet](p3-2-entry-decision-packet.md)"
    start_link = "[P3.2 start authorization](p3-2-start-authorization.md)"
    for name, document in (
        ("Phase 3 index", index),
        ("implementation backlog", backlog),
        ("decision register", decisions),
    ):
        if entry_link not in document or start_link not in document:
            failures.append(f"P3.2 entry/start records are not linked from {name}")
    if failures:
        return CheckResult(
            "documentation_boundary",
            FAIL,
            "; ".join(failures),
            files,
        )
    return CheckResult(
        "documentation_boundary",
        PASS,
        "Live Phase 3 documents expose the bounded start and its continuing prohibitions.",
        files,
    )


def check_ci_integration() -> CheckResult:
    path = ".github/workflows/python-ci.yml"
    command = "python tools/phase32_entry_readiness.py"
    try:
        workflow = _read(path)
    except OSError as exc:
        return CheckResult("ci_integration", FAIL, str(exc), [path])
    lines = {line.strip() for line in workflow.splitlines()}
    if f"run: {command}" not in lines:
        return CheckResult(
            "ci_integration",
            FAIL,
            "CI does not verify the P3.2 start authorization state.",
            [path, command],
        )
    return CheckResult(
        "ci_integration",
        PASS,
        "CI verifies the evidence-bound generated-only P3.2 start authorization.",
        [path, command],
    )


def build_readiness_report() -> EntryReadinessReport:
    try:
        digest = canonical_digest(_read_json(ENTRY_RECORD))
    except (OSError, ValueError, json.JSONDecodeError):
        digest = "unavailable"
    checks = [
        check_required_files(),
        check_entry_record(),
        check_research_authorization(),
        check_research_evidence(),
        check_accepted_dependencies(),
        check_reference_candidate_blocked(),
        check_model_approval(),
        check_dataset_approval(),
        check_runtime_approval(),
        check_start_authorization(),
        check_documentation_boundary(),
        check_ci_integration(),
    ]
    failures = sum(check.status == FAIL for check in checks)
    return EntryReadinessReport(
        status="not_ready" if failures else "implementation_authorized_generated_only",
        scope="phase3.p3_2.portable_detection.generated_only_start",
        record_digest=digest,
        failures=failures,
        manual_gates=0,
        checks=checks,
    )


def print_text_report(report: EntryReadinessReport) -> None:
    print(f"Phase 3 P3.2 entry readiness: {report.status}")
    print(f"Scope: {report.scope}")
    print(f"Entry record digest: {report.record_digest}")
    print(f"Failures: {report.failures}")
    print(f"Manual gates: {report.manual_gates}")
    print()
    for check in report.checks:
        print(f"[{check.status}] {check.name}: {check.detail}")
        for item in check.evidence:
            print(f"  - {item}")
        print()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the H-CAM generated-only P3.2 start authorization."
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_readiness_report()
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print_text_report(report)
    if report.failures:
        return 1
    if args.strict and report.manual_gates:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
