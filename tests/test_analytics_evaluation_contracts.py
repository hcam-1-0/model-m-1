from __future__ import annotations

import copy
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from hcam.analytics.evaluation.baseline import build_baseline_evidence
from hcam.analytics.evaluation.candidates import research_references
from hcam.analytics.evaluation.contracts import (
    AnnotationSpecificationV1,
    ApprovalRecordV1,
    CandidateArtifactManifestV1,
    DatasetManifestV1,
    EvaluationContractSafetyError,
    EvaluationRunManifestV1,
    FixtureManifestV1,
    HardGateResultV1,
    MetricReportV1,
    MetricValueV1,
    ResearchReferenceV1,
    ResolutionFieldV1,
    SourceEvidenceV1,
    canonical_digest,
    canonical_evaluation_json,
    evaluation_contract_bundle,
    seal_record,
)


DIGEST = f"sha256:{'1' * 64}"
COMMIT = "1" * 40


@pytest.fixture(scope="module")
def evidence() -> dict[str, object]:
    return build_baseline_evidence(
        source_commit=COMMIT,
        dirty_worktree=True,
        generator_code_digest=DIGEST,
        dependency_lock_digest=DIGEST,
        container_profile_digest=None,
    )


def _document(record: object) -> dict[str, object]:
    return copy.deepcopy(record.model_dump(mode="json"))  # type: ignore[attr-defined]


def test_contract_bundle_versions_all_six_canonical_record_families() -> None:
    bundle = evaluation_contract_bundle()

    assert bundle["contract_format"] == "hcam.analytics.evaluation-contract-bundle.v1"
    assert bundle["maximum_record_bytes"] == 1024 * 1024
    assert set(bundle["records"]) == {
        "hcam.analytics.annotation-specification.v1",
        "hcam.analytics.candidate-artifact-manifest.v1",
        "hcam.analytics.dataset-manifest.v1",
        "hcam.analytics.evaluation-run-manifest.v1",
        "hcam.analytics.fixture-manifest.v1",
        "hcam.analytics.metric-report.v1",
    }


def test_canonical_json_is_order_independent_ascii_and_digest_stable() -> None:
    first = {"z": "ગુજરાતી", "a": [2, 1]}
    second = {"a": [2, 1], "z": "ગુજરાતી"}

    serialized = canonical_evaluation_json(first)

    assert serialized == canonical_evaluation_json(second)
    assert "\\u0a97" in serialized
    assert canonical_digest(first) == canonical_digest(second)


@pytest.mark.parametrize(
    "document",
    [
        {"password": "redacted"},
        {"nested": {"stream_url": "redacted"}},
        {"value": b"binary"},
        {"value": "C:\\private\\artifact.json"},
        {"value": "token=redacted"},
        {"value": "rtsp://example.invalid/live"},
    ],
)
def test_canonical_json_rejects_prohibited_or_sensitive_content(
    document: dict[str, object],
) -> None:
    with pytest.raises(EvaluationContractSafetyError):
        canonical_evaluation_json(document)


def test_canonical_json_rejects_invalid_bounds_and_non_json_values() -> None:
    with pytest.raises(ValueError, match="max_bytes must be positive"):
        canonical_evaluation_json({"value": "ok"}, max_bytes=0)
    with pytest.raises(ValueError, match="exceeds"):
        canonical_evaluation_json({"value": "too-large"}, max_bytes=8)
    with pytest.raises(ValueError, match="canonical JSON"):
        canonical_evaluation_json({"value": object()})


def test_digest_bound_record_rejects_content_tampering(evidence: dict[str, object]) -> None:
    dataset = evidence["dataset-manifest-v1.json"]
    document = _document(dataset)
    document["purpose"] = "Tampered purpose"

    with pytest.raises(ValidationError, match="digest does not match"):
        DatasetManifestV1.model_validate(document)


def test_approval_record_requires_a_timestamp_only_for_decisions() -> None:
    pending = ApprovalRecordV1(
        record_id="approval-pending",
        owner_id="mayank-admin",
        status="pending",
        reason="Pending evidence review",
    )
    assert pending.decided_at is None

    with pytest.raises(ValidationError, match="decision timestamp"):
        ApprovalRecordV1(
            record_id="approval-invalid",
            owner_id="mayank-admin",
            status="owner_approved",
            reason="Missing decision time",
        )
    with pytest.raises(ValidationError, match="cannot have"):
        ApprovalRecordV1(
            record_id="approval-invalid-time",
            owner_id="mayank-admin",
            status="pending",
            decided_at=datetime(2026, 8, 24, tzinfo=UTC),
            reason="Pending with a timestamp",
        )
    with pytest.raises(ValidationError, match="outer whitespace"):
        ApprovalRecordV1(
            record_id="approval-whitespace",
            owner_id="mayank-admin",
            status="pending",
            reason=" leading whitespace",
        )


def test_research_reference_requires_clean_credential_free_https() -> None:
    base = {
        "reference_id": "source-example",
        "title": "Official source",
        "publisher": "Publisher",
        "accessed_on": date(2026, 8, 24),
        "evidence_kind": "official_repository",
        "supports_claim": "Supports a metadata-only claim",
    }
    with pytest.raises(ValidationError, match="credential-free HTTPS"):
        ResearchReferenceV1(url="http://example.com/source", **base)
    with pytest.raises(ValidationError, match="query or fragment"):
        ResearchReferenceV1(url="https://example.com/source?download=1", **base)


def _s0_source() -> dict[str, object]:
    return {
        "source_id": "generated-source",
        "source_tier": "S0",
        "source_version": "1.0.0",
        "method": "deterministic_generation",
        "authorization_state": "authorized",
        "authorization_record_id": "D-P3.1-001",
        "license_id": "hcam-generated-internal-v1",
        "allowed_uses": ["ci-testing"],
        "prohibited_uses": ["production-use"],
        "privacy_classification": "generated_non_personal",
        "no_external_input": True,
        "no_download_performed": True,
        "references": [],
    }


def test_source_tiers_are_fail_closed() -> None:
    assert SourceEvidenceV1.model_validate(_s0_source()).authorization_state == "authorized"

    changed = _s0_source()
    changed["no_external_input"] = False
    with pytest.raises(ValidationError, match="S0 must be generated-only"):
        SourceEvidenceV1.model_validate(changed)

    changed = _s0_source()
    changed["allowed_uses"] = ["ci-testing", "ci-testing"]
    with pytest.raises(ValidationError, match="must be unique"):
        SourceEvidenceV1.model_validate(changed)

    changed = _s0_source()
    changed["prohibited_uses"] = ["ci-testing"]
    with pytest.raises(ValidationError, match="cannot overlap"):
        SourceEvidenceV1.model_validate(changed)

    changed = _s0_source()
    changed["source_tier"] = "S1"
    with pytest.raises(ValidationError, match="authorization policy"):
        SourceEvidenceV1.model_validate(changed)


def test_research_and_prohibited_source_tiers_never_gain_use_authorization() -> None:
    reference = research_references()["yolox"]
    research = SourceEvidenceV1(
        source_id="research-yolox",
        source_tier="S3",
        source_version="captured-2026-08-24",
        method="public_research",
        authorization_state="research_only",
        license_id="research-metadata-only",
        allowed_uses=["source-research"],
        prohibited_uses=["artifact-download"],
        privacy_classification="review_required",
        no_external_input=False,
        no_download_performed=True,
        references=[reference],
    )
    assert research.authorization_record_id is None

    changed = research.model_dump(mode="json")
    changed["no_download_performed"] = False
    with pytest.raises(ValidationError, match="no download"):
        SourceEvidenceV1.model_validate(changed)

    prohibited = {
        "source_id": "prohibited-camera-source",
        "source_tier": "S4",
        "source_version": "not-applicable",
        "method": "private_lab",
        "authorization_state": "prohibited",
        "license_id": "not-authorized",
        "allowed_uses": ["planning-reference"],
        "prohibited_uses": ["media-use"],
        "privacy_classification": "prohibited",
        "no_external_input": False,
        "no_download_performed": True,
        "references": [],
    }
    assert SourceEvidenceV1.model_validate(prohibited).authorization_state == "prohibited"
    prohibited["authorization_record_id"] = "unauthorized-record"
    with pytest.raises(ValidationError, match="cannot have use authorization"):
        SourceEvidenceV1.model_validate(prohibited)


def test_approved_dataset_requires_owner_authorized_sources_and_clean_splits(
    evidence: dict[str, object],
) -> None:
    dataset = evidence["dataset-manifest-v1.json"]

    pending = _document(dataset)
    pending["approval"] = {
        "record_id": "pending-dataset",
        "owner_id": "mayank-admin",
        "status": "pending",
        "decided_at": None,
        "reason": "Pending final review",
    }
    with pytest.raises(ValidationError, match="requires owner approval"):
        seal_record(DatasetManifestV1, pending)

    unapproved_source = _document(dataset)
    research = SourceEvidenceV1(
        source_id="research-source",
        source_tier="S3",
        source_version="captured-2026-08-24",
        method="public_research",
        authorization_state="research_only",
        license_id="metadata-only",
        allowed_uses=["research"],
        prohibited_uses=["download"],
        privacy_classification="review_required",
        no_external_input=False,
        no_download_performed=True,
        references=[research_references()["yolox"]],
    )
    unapproved_source["sources"] = [research.model_dump(mode="json")]
    with pytest.raises(ValidationError, match="unapproved source tiers"):
        seal_record(DatasetManifestV1, unapproved_source)

    leaked = _document(dataset)
    leaked["split_policy"]["exact_duplicate_count"] = 1  # type: ignore[index]
    leaked["split_policy"]["leakage_status"] = "fail"  # type: ignore[index]
    with pytest.raises(ValidationError, match="passing leakage checks"):
        seal_record(DatasetManifestV1, leaked)


def test_fixture_and_annotation_specification_require_bounded_owner_approval(
    evidence: dict[str, object],
) -> None:
    fixture = _document(evidence["fixture-manifest-v1.json"])
    fixture["generator"]["external_inputs"] = ["external-source"]  # type: ignore[index]
    with pytest.raises(ValidationError, match="cannot declare external inputs"):
        seal_record(FixtureManifestV1, fixture)

    fixture = _document(evidence["fixture-manifest-v1.json"])
    fixture["approval"]["status"] = "owner_recorded"  # type: ignore[index]
    with pytest.raises(ValidationError, match="requires owner approval"):
        seal_record(FixtureManifestV1, fixture)

    specification = _document(evidence["annotation-specification-v1.json"])
    specification["tasks"] = ["detection", "detection"]
    with pytest.raises(ValidationError, match="tasks must be unique"):
        seal_record(AnnotationSpecificationV1, specification)

    specification = _document(evidence["annotation-specification-v1.json"])
    specification["approval"]["status"] = "owner_recorded"  # type: ignore[index]
    with pytest.raises(ValidationError, match="requires owner approval"):
        seal_record(AnnotationSpecificationV1, specification)


def test_candidate_records_cannot_claim_unproven_eligibility(
    evidence: dict[str, object],
) -> None:
    candidates = evidence["candidates"]
    candidate = _document(candidates["DET-R0"])  # type: ignore[index]
    candidate["eligibility"] = "eligible"
    with pytest.raises(ValidationError, match="unresolved blockers"):
        seal_record(CandidateArtifactManifestV1, candidate)

    candidate = _document(candidates["DET-R0"])  # type: ignore[index]
    candidate["source_reference"] = None
    with pytest.raises(ValidationError, match="S3 candidate requires"):
        seal_record(CandidateArtifactManifestV1, candidate)

    candidate = _document(candidates["DET-R0"])  # type: ignore[index]
    candidate["source_tier"] = "S0"
    with pytest.raises(ValidationError, match="S0 candidate cannot"):
        seal_record(CandidateArtifactManifestV1, candidate)


def test_resolution_fields_are_explicit() -> None:
    assert ResolutionFieldV1(state="resolved", value="artifact-v1").blocker is None
    assert ResolutionFieldV1(state="unresolved", blocker="artifact-unresolved").value is None
    with pytest.raises(ValidationError, match="requires a value"):
        ResolutionFieldV1(state="resolved")
    with pytest.raises(ValidationError, match="requires only a blocker"):
        ResolutionFieldV1(state="unresolved", value="guessed", blocker="still-unresolved")


def test_generated_run_cannot_hide_candidate_or_gate_state(evidence: dict[str, object]) -> None:
    run = _document(evidence["evaluation-run-v1.json"])
    run["precision"] = "float32"
    with pytest.raises(ValidationError, match="not_applicable precision"):
        seal_record(EvaluationRunManifestV1, run)

    run = _document(evidence["evaluation-run-v1.json"])
    run["failed_gates"] = ["fabricated-failure"]
    with pytest.raises(ValidationError, match="passing run"):
        seal_record(EvaluationRunManifestV1, run)


def test_metric_report_requires_known_populations_and_exact_gate_failures(
    evidence: dict[str, object],
) -> None:
    report = _document(evidence["metric-report-v1.json"])
    report["populations"].append(copy.deepcopy(report["populations"][0]))  # type: ignore[union-attr,index]
    with pytest.raises(ValidationError, match="populations must be unique"):
        seal_record(MetricReportV1, report)

    report = _document(evidence["metric-report-v1.json"])
    report["metrics"][0]["population_id"] = "missing-population"  # type: ignore[index]
    with pytest.raises(ValidationError, match="unknown population"):
        seal_record(MetricReportV1, report)

    report = _document(evidence["metric-report-v1.json"])
    report["failed_gates"] = ["unreported-failure"]
    with pytest.raises(ValidationError, match="must match"):
        seal_record(MetricReportV1, report)


def test_unapproved_numeric_gate_is_proposal_only_and_metric_counts_are_consistent() -> None:
    with pytest.raises(ValidationError, match="proposal_only"):
        HardGateResultV1(
            gate_id="unapproved-gate",
            metric_name="detection.f1",
            comparator="gte",
            threshold=0.5,
            observed=0.75,
            outcome="pass",
            owner_approved=False,
        )
    with pytest.raises(ValidationError, match="appear together"):
        MetricValueV1(
            metric_name="detection.precision",
            domain="detection",
            population_id="generated",
            value=0.5,
            unit="ratio",
            numerator=1,
            outcome="reported",
        )
    with pytest.raises(ValidationError, match="cannot exceed"):
        MetricValueV1(
            metric_name="detection.precision",
            domain="detection",
            population_id="generated",
            value=2.0,
            unit="ratio",
            numerator=2,
            denominator=1,
            outcome="reported",
        )
    with pytest.raises(ValidationError):
        MetricValueV1(
            metric_name="detection.precision",
            domain="detection",
            population_id="generated",
            value=float("nan"),
            unit="ratio",
            outcome="reported",
        )
