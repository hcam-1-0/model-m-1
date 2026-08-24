from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from typing import Literal

from hcam.analytics.contracts import NormalizedBoundingBox
from hcam.analytics.evaluation.annotations import (
    AnnotationItemV1,
    AnnotationObjectV1,
    AnnotationQaReportV1,
    validate_annotations,
)
from hcam.analytics.evaluation.candidates import (
    SourceResearchDossierV1,
    candidate_manifests,
    source_research_dossier,
)
from hcam.analytics.evaluation.contracts import (
    AnnotationSpecificationV1,
    ApprovalRecordV1,
    AttributeDefinitionV1,
    CandidateArtifactManifestV1,
    DatasetManifestV1,
    DigestBoundRecord,
    EvaluationRunManifestV1,
    FileHashV1,
    FixtureCoverageV1,
    FixtureManifestV1,
    GeneratorIdentityV1,
    ManifestReferenceV1,
    MetricReportV1,
    RetentionPolicyV1,
    SourceEvidenceV1,
    SplitPolicyV1,
    canonical_digest,
    evaluation_contract_bundle,
    seal_record,
)
from hcam.analytics.evaluation.fixtures import (
    APPROVED_EMITTED_CLASSES,
    FIXTURE_SEED,
    generated_detection_fixtures,
    generated_fixture_documents,
    generated_geometry_fixtures,
    generated_plate_fixtures,
    generated_tracking_fixtures,
)
from hcam.analytics.evaluation.metrics import (
    build_golden_metric_report,
    evaluate_detection,
    evaluate_geometry,
    evaluate_synthetic_plates,
    evaluate_tracking,
)
from hcam.analytics.evaluation.splits import (
    SplitItemV1,
    SplitValidationReportV1,
    deterministic_split,
    validate_splits,
)


BASELINE_AT = datetime(2026, 8, 24, 13, 0, tzinfo=UTC)
AUTHORIZATION_AT = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
REVIEW_DUE_ON = date(2026, 11, 22)
BASELINE_VERSION = "1.0.0"
REQUIRED_GROUP_KEYS = ["generator-group", "seed-group", "template-group"]


def rendered_json_bytes(document: object) -> bytes:
    return (
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")


def bytes_digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _approval(
    *,
    record_id: str = "D-P3.1-001",
    status: Literal["pending", "owner_recorded", "owner_approved"],
    reason: str,
) -> ApprovalRecordV1:
    return ApprovalRecordV1(
        record_id=record_id,
        owner_id="mayank-admin",
        status=status,
        decided_at=AUTHORIZATION_AT if status != "pending" else None,
        reason=reason,
    )


def approved_annotation_specification() -> AnnotationSpecificationV1:
    return seal_record(
        AnnotationSpecificationV1,
        {
            "specification_id": "p31-generated-annotation-specification-v1",
            "semantic_version": BASELINE_VERSION,
            "status": "approved",
            "taxonomy_version": "hcam.analytics.taxonomy.v1",
            "tasks": ["detection", "tracking", "geometry", "synthetic_plate"],
            "rules": {
                "coordinate_system": "normalized_top_left",
                "geometry_types": ["bounding_box", "line", "polygon", "text_region"],
                "ignore_rules": [
                    "Ignore generated objects whose declared visibility is zero",
                    "Do not convert uncertain generated labels into accepted truth",
                ],
                "uncertain_rule": (
                    "Mark ambiguous generated truth uncertain and exclude it from promotion evidence"
                ),
                "occlusion_values": ["none", "partial", "heavy", "unknown"],
                "truncated_rule": (
                    "Mark truncated when generated geometry touches a declared frame boundary"
                ),
                "track_lifecycle_rules": [
                    "Track identifiers are unique within one generated sequence epoch",
                    "Reconnect and discontinuity create an explicit new tracker epoch",
                    "A track ends after the fixture-declared terminal observation",
                ],
                "synthetic_plate_rules": [
                    "Only deterministic generated strings are transcribed",
                    "Preserve declared Latin Devanagari or Gujarati script",
                    "Record alternatives in ranked order and preserve abstention",
                    "Do not add identity owner registry or watchlist attributes",
                ],
                "normalization_rules": [
                    "Serialize keys in canonical sorted order",
                    "Use normalized top-left coordinates in the closed unit interval",
                    "Preserve Unicode text and compare normalized generated strings exactly",
                    "Reject unknown fields and non-finite numeric values",
                ],
            },
            "attributes": [
                AttributeDefinitionV1(
                    name="source-generated",
                    value_type="boolean",
                    required=True,
                ).model_dump(mode="json"),
                AttributeDefinitionV1(
                    name="visibility",
                    value_type="enum",
                    required=False,
                    allowed_values=["full", "partial", "heavy"],
                ).model_dump(mode="json"),
                AttributeDefinitionV1(
                    name="event-expected",
                    value_type="boolean",
                    required=False,
                ).model_dump(mode="json"),
            ],
            "import_format": "hcam.analytics.generated-annotation.v1",
            "export_format": "hcam.analytics.generated-annotation.v1",
            "quality_policy": {
                "automated_checks": [
                    "class-taxonomy-membership",
                    "geometry-bounds",
                    "sequence-order",
                    "track-id-uniqueness",
                    "required-attributes",
                    "unknown-attributes",
                    "synthetic-plate-fields",
                ],
                "qa_sample_basis_points": 10_000,
                "duplicate_annotation_basis_points": 0,
                "adjudication_required": False,
                "proposed_error_rate_ceiling": 0.0,
                "calibration_evidence_required": True,
            },
            "approval": _approval(
                status="owner_approved",
                reason=(
                    "Authorize this generated-only annotation specification under the "
                    "bounded D-P3.1-001 implementation scope"
                ),
            ).model_dump(mode="json"),
            "version_history": [],
            "created_at": BASELINE_AT,
        },
    )


def generated_annotation_items() -> list[AnnotationItemV1]:
    common = {
        "split": "validation",
        "generator_family": "p31-generated-annotation",
        "seed_group": "seed-31001",
        "annotator_id": "generator-p31",
        "tool_version": "hcam-generated-annotation-v1",
        "normalization_version": "hcam-normalization-v1",
        "annotated_at": BASELINE_AT,
    }
    box = NormalizedBoundingBox(x=0.1, y=0.2, width=0.3, height=0.4)
    return [
        AnnotationItemV1(
            **common,
            item_id="annotation-detection-001",
            sequence_id="annotation-sequence-detection",
            frame_sequence=0,
            template_group="template-detection",
            annotations=[
                AnnotationObjectV1(
                    annotation_id="annotation-object-person-001",
                    task="detection",
                    class_id="object.person",
                    bbox=box,
                    occlusion="none",
                    attributes={"source-generated": True, "visibility": "full"},
                )
            ],
        ),
        AnnotationItemV1(
            **common,
            item_id="annotation-tracking-001",
            sequence_id="annotation-sequence-tracking",
            frame_sequence=0,
            template_group="template-tracking",
            annotations=[
                AnnotationObjectV1(
                    annotation_id="annotation-object-track-001",
                    task="tracking",
                    class_id="vehicle.car",
                    bbox=box,
                    track_id="track-generated-001",
                    occlusion="partial",
                    attributes={"source-generated": True, "visibility": "partial"},
                )
            ],
        ),
        AnnotationItemV1(
            **common,
            item_id="annotation-geometry-001",
            sequence_id="annotation-sequence-geometry",
            frame_sequence=0,
            template_group="template-geometry",
            annotations=[
                AnnotationObjectV1(
                    annotation_id="annotation-object-geometry-001",
                    task="geometry",
                    geometry_id="zone-generated-001",
                    attributes={"source-generated": True, "event-expected": True},
                )
            ],
        ),
        AnnotationItemV1(
            **common,
            item_id="annotation-plate-001",
            sequence_id="annotation-sequence-plate",
            frame_sequence=0,
            template_group="template-plate",
            annotations=[
                AnnotationObjectV1(
                    annotation_id="annotation-object-plate-001",
                    task="synthetic_plate",
                    bbox=box,
                    plate_text="GJ01AB1234",
                    plate_script="Latin",
                    attributes={"source-generated": True},
                )
            ],
        ),
    ]


def generated_annotation_qa_report(
    specification: AnnotationSpecificationV1,
) -> AnnotationQaReportV1:
    return validate_annotations(
        generated_annotation_items(),
        specification,
        approved_classes=set(APPROVED_EMITTED_CLASSES),
        generated_at=BASELINE_AT,
    )


def _groups_for_split(
    split: Literal["train", "validation", "test"],
    *,
    count: int,
) -> list[str]:
    values: list[str] = []
    index = 0
    while len(values) < count:
        value = f"p31-{split}-group-{index:03d}"
        if deterministic_split(value) == split:
            values.append(value)
        index += 1
    return values


def generated_split_items() -> list[SplitItemV1]:
    items: list[SplitItemV1] = []
    for split in ("train", "validation", "test"):
        for index, group in enumerate(_groups_for_split(split, count=2), start=1):
            item_id = f"p31-{split}-item-{index:02d}"
            items.append(
                SplitItemV1(
                    item_id=item_id,
                    content_digest=canonical_digest(
                        {
                            "item_id": item_id,
                            "group": group,
                            "source": "generated-only",
                        }
                    ),
                    split=split,
                    group_values={
                        "generator-group": group,
                        "seed-group": f"{group}-seed",
                        "template-group": f"{group}-template",
                    },
                )
            )
    return items


def generated_split_report(items: list[SplitItemV1]) -> SplitValidationReportV1:
    return validate_splits(
        items,
        required_group_keys=REQUIRED_GROUP_KEYS,
        final_test_frozen=True,
        final_test_accesses=[],
        generated_at=BASELINE_AT,
    )


def _fixture_outcome(domain: str, record: dict[str, object]) -> str:
    if domain == "misuse":
        return "reject"
    outcome = record["expected_outcome"]
    if outcome == "reject":
        return "reject"
    if domain == "synthetic_plate" and outcome == "abstain":
        return "abstain"
    if domain == "geometry" and outcome == "inactive":
        return "abstain"
    return "pass"


def _fixture_coverage(documents: dict[str, object]) -> list[FixtureCoverageV1]:
    coverage: list[FixtureCoverageV1] = []
    domains = {
        "detection-v1.json": "detection",
        "tracking-v1.json": "tracking",
        "geometry-v1.json": "geometry",
        "synthetic-plate-v1.json": "synthetic_plate",
        "misuse-v1.json": "misuse",
    }
    for name, domain in domains.items():
        document = documents[name]
        assert isinstance(document, dict)
        records = document["records"]
        assert isinstance(records, list)
        for record in records:
            assert isinstance(record, dict)
            class_id = None
            if domain == "detection":
                truths = record["truths"]
                assert isinstance(truths, list)
                if truths:
                    truth = truths[0]
                    assert isinstance(truth, dict)
                    class_id = truth["class_id"]
            coverage.append(
                FixtureCoverageV1(
                    domain=domain,
                    scenario=str(record.get("scenario", record.get("prohibited_field"))),
                    expected_outcome=_fixture_outcome(domain, record),
                    class_id=str(class_id) if class_id is not None else None,
                    script=(
                        str(record["script"])
                        if domain == "synthetic_plate"
                        else None
                    ),
                )
            )
    return coverage


def generated_fixture_manifest(
    documents: dict[str, object],
    *,
    generator_code_digest: str,
) -> FixtureManifestV1:
    file_hashes = [
        FileHashV1(
            artifact_name=name,
            digest=bytes_digest(rendered_json_bytes(document)),
            bytes=len(rendered_json_bytes(document)),
            record_count=len(document["records"]),
        )
        for name, document in sorted(documents.items())
    ]
    template_digests = [
        canonical_digest(document) for _, document in sorted(documents.items())
    ]
    configuration_digest = canonical_digest(
        {"seed": FIXTURE_SEED, "suites": sorted(documents)}
    )
    return seal_record(
        FixtureManifestV1,
        {
            "fixture_suite_id": "p31-generated-fixtures-v1",
            "semantic_version": BASELINE_VERSION,
            "generator": GeneratorIdentityV1(
                generator_id="hcam-p31-generated-fixtures",
                generator_version=BASELINE_VERSION,
                code_digest=generator_code_digest,
                configuration_digest=configuration_digest,
                external_inputs=[],
            ).model_dump(mode="json"),
            "seeds": [FIXTURE_SEED],
            "template_digests": template_digests,
            "expected_contracts": [
                "hcam.analytics.generated-fixture-suite.v1",
                "hcam.analytics.evaluation-contract-bundle.v1",
            ],
            "expected_failure_codes": [
                "prohibited-field",
                "prohibited-sensitive-value",
                "binary-data",
                "local-filesystem-path",
                "payload-too-large",
                "invalid-digest",
            ],
            "coverage": [value.model_dump(mode="json") for value in _fixture_coverage(documents)],
            "declared_omissions": [
                "No external datasets fonts checkpoints weights or model artifacts",
                "No real people real plates cameras video images crops or clips",
                "No inference decoding training GPU execution or performance claim",
            ],
            "generated_only": True,
            "prohibited_sources_absent": True,
            "files": [value.model_dump(mode="json") for value in file_hashes],
            "approval": _approval(
                status="owner_approved",
                reason=(
                    "Authorize deterministic S0 fixture generation under D-P3.1-001; "
                    "this is not P3.1 exit acceptance"
                ),
            ).model_dump(mode="json"),
            "created_at": BASELINE_AT,
        },
    )


def generated_dataset_manifest(
    documents: dict[str, object],
    specification: AnnotationSpecificationV1,
    split_items: list[SplitItemV1],
    split_report: SplitValidationReportV1,
) -> DatasetManifestV1:
    inventory: list[dict[str, object]] = []
    fixture_classes = list(APPROVED_EMITTED_CLASSES)
    for name, document in sorted(documents.items()):
        assert isinstance(document, dict)
        inventory.append(
            {
                "item_id": f"fixture-{name.removesuffix('.json')}",
                "content_type": "generated_metadata",
                "artifact_name": name,
                "digest": bytes_digest(rendered_json_bytes(document)),
                "count": len(document["records"]),
                "split": "none",
                "class_ids": fixture_classes if name == "detection-v1.json" else [],
                "slices": [str(document["suite"]), "generated-only"],
            }
        )
    for item in split_items:
        inventory.append(
            {
                "item_id": item.item_id,
                "content_type": "generated_metadata",
                "artifact_name": f"{item.item_id}.json",
                "digest": item.content_digest,
                "count": 1,
                "split": item.split,
                "sequence_id": item.item_id,
                "group_key": item.group_values["template-group"],
                "class_ids": [],
                "slices": ["split-validation", "generated-only"],
            }
        )
    source = SourceEvidenceV1(
        source_id="p31-generated-s0",
        source_tier="S0",
        source_version=BASELINE_VERSION,
        method="deterministic_generation",
        authorization_state="authorized",
        authorization_record_id="D-P3.1-001",
        license_id="hcam-generated-internal-v1",
        allowed_uses=["contract-validation", "offline-metric-goldens", "ci-testing"],
        prohibited_uses=["training", "inference", "production-use"],
        privacy_classification="generated_non_personal",
        no_external_input=True,
        no_download_performed=True,
        references=[],
    )
    return seal_record(
        DatasetManifestV1,
        {
            "dataset_id": "p31-generated-evaluation-dataset-v1",
            "semantic_version": BASELINE_VERSION,
            "status": "approved",
            "purpose": (
                "Offline generated-only contract validation metric goldens and QA calibration"
            ),
            "sources": [source.model_dump(mode="json")],
            "inventory": inventory,
            "taxonomy_version": "hcam.analytics.taxonomy.v1",
            "annotation_specification": ManifestReferenceV1(
                record_id=specification.specification_id,
                version=specification.semantic_version,
                digest=specification.specification_digest,
            ).model_dump(mode="json"),
            "transformations": [],
            "parents": [],
            "retention": RetentionPolicyV1(
                data_class="generated.analytics.fixture",
                maximum_retention_hours=2_160,
                access_roles=["analytics.developer", "analytics.reviewer"],
                export_allowed=False,
                training_reuse_allowed=False,
                deletion_proof="audited_metadata_only",
            ).model_dump(mode="json"),
            "split_policy": SplitPolicyV1(
                allowed_splits=["train", "validation", "test"],
                required_group_keys=REQUIRED_GROUP_KEYS,
                final_test_frozen=split_report.final_test_frozen,
                final_test_access_count=len(split_report.final_test_accesses),
                exact_duplicate_count=split_report.exact_duplicate_count,
                cross_split_group_count=split_report.cross_split_group_count,
                leakage_status=split_report.status,
            ).model_dump(mode="json"),
            "known_gaps": [
                "Generated fixtures do not establish real-world model accuracy",
                "Generated fixtures do not establish camera codec lighting weather or geography coverage",
                "No candidate model has been downloaded executed or compared",
            ],
            "exclusions": [
                "real-person-media",
                "real-plate-media",
                "camera-media",
                "government-data",
                "private-data",
                "scraped-content",
            ],
            "approval": _approval(
                status="owner_approved",
                reason=(
                    "Authorize the deterministic S0 dataset under D-P3.1-001; "
                    "this does not authorize training inference or external data"
                ),
            ).model_dump(mode="json"),
            "created_at": BASELINE_AT,
            "review_due_on": REVIEW_DUE_ON,
        },
    )


def golden_metric_report() -> MetricReportV1:
    detection = evaluate_detection(generated_detection_fixtures())
    tracking = evaluate_tracking(generated_tracking_fixtures())
    geometry_fixtures = generated_geometry_fixtures()
    expected_geometry = {
        fixture.case_id: list(fixture.expected_events) for fixture in geometry_fixtures
    }
    geometry = evaluate_geometry(
        expected_geometry,
        expected_geometry,
        onset_errors_ms=[0.0],
        termination_errors_ms=[0.0],
    )
    plates = evaluate_synthetic_plates(generated_plate_fixtures())
    return build_golden_metric_report(detection, tracking, geometry, plates)


def generated_evaluation_run(
    *,
    source_commit: str,
    dirty_worktree: bool,
    dependency_lock_digest: str,
    container_profile_digest: str | None,
    dataset: DatasetManifestV1,
    fixtures: FixtureManifestV1,
    annotation_qa: AnnotationQaReportV1,
    split_report: SplitValidationReportV1,
    metric_report: MetricReportV1,
    source_dossier: SourceResearchDossierV1,
) -> EvaluationRunManifestV1:
    result_records = (
        ("annotation-qa-report-v1.json", annotation_qa.report_digest),
        ("split-validation-report-v1.json", split_report.report_digest),
        ("metric-report-v1.json", metric_report.report_digest),
        ("fixture-manifest-v1.json", fixtures.manifest_digest),
        ("dataset-manifest-v1.json", dataset.manifest_digest),
        ("source-research-dossier-v1.json", source_dossier.dossier_digest),
    )
    return seal_record(
        EvaluationRunManifestV1,
        {
            "run_id": "p31-generated-baseline-v1",
            "semantic_version": BASELINE_VERSION,
            "executed_at": BASELINE_AT,
            "source": {"commit": source_commit, "dirty_worktree": dirty_worktree},
            "operator_id": "mayank-admin",
            "command": {
                "executable": "python",
                "arguments": ["tools/phase31_contracts.py", "check"],
                "network_access": "denied",
                "gpu_access": "denied",
                "secrets_required": False,
            },
            "seed": FIXTURE_SEED,
            "dataset": ManifestReferenceV1(
                record_id=dataset.dataset_id,
                version=dataset.semantic_version,
                digest=dataset.manifest_digest,
            ).model_dump(mode="json"),
            "fixture_suite": ManifestReferenceV1(
                record_id=fixtures.fixture_suite_id,
                version=fixtures.semantic_version,
                digest=fixtures.manifest_digest,
            ).model_dump(mode="json"),
            "candidate": None,
            "pipeline_digest": canonical_digest(
                {
                    "pipeline": "p31-generated-offline-baseline",
                    "stages": [
                        "fixture-generation",
                        "annotation-qa",
                        "split-validation",
                        "metric-goldens",
                        "candidate-metadata-validation",
                    ],
                }
            ),
            "taxonomy_version": "hcam.analytics.taxonomy.v1",
            "metric_suite_digest": canonical_digest(
                {
                    "metric_suite_id": metric_report.metric_suite_id,
                    "metric_suite_version": metric_report.metric_suite_version,
                    "metric_names": [metric.metric_name for metric in metric_report.metrics],
                }
            ),
            "configuration_digest": canonical_digest(
                {"seed": FIXTURE_SEED, "iou_threshold": 0.5, "offline": True}
            ),
            "hardware": {
                "profile_id": "LAB-LAPTOP-01",
                "cpu": "Intel Core i5-8365U",
                "logical_processors": 8,
                "memory_mib": 7_373,
                "gpu": "Intel UHD Graphics 620 no discrete accelerator",
                "os": "Microsoft Windows 10 Pro 10.0.19045 build 19045",
                "python_version": "3.14.6",
                "container_engine": "Docker Engine 28.5.2",
                "authorized_claims": [
                    "contract-correctness",
                    "generated-fixture-determinism",
                    "metric-golden-correctness",
                    "small-cpu-baseline",
                ],
                "prohibited_claims": [
                    "production-throughput",
                    "gpu-parity",
                    "c10-c50-capacity",
                    "real-camera-performance",
                    "statewide-sizing",
                ],
            },
            "dependency_lock_digest": dependency_lock_digest,
            "container_profile_digest": container_profile_digest,
            "precision": "not_applicable",
            "warmup_iterations": 0,
            "repetitions": 2,
            "batch_size": 1,
            "concurrency": 1,
            "timeout_seconds": 120,
            "maximum_memory_mib": 2_048,
            "result_artifacts": [
                {"artifact_name": name, "digest": digest, "media_free": True}
                for name, digest in result_records
            ],
            "failed_gates": [],
            "warnings": [
                "Generated-only baseline has no external-validity or model-performance claim",
                "No candidate model data media decoder inference or GPU runtime was used",
                "P3.2 remains blocked pending exact artifact and dataset owner approval",
                *(
                    ["Baseline source worktree was dirty and must be rerun from the accepted commit"]
                    if dirty_worktree
                    else []
                ),
            ],
            "reproducibility_status": "pass",
            "approval": _approval(
                status="owner_recorded",
                reason=(
                    "Record generated baseline evidence without accepting P3.1 or approving "
                    "numeric promotion gates"
                ),
            ).model_dump(mode="json"),
        },
    )


def _record_entry(
    artifact_name: str,
    record: DigestBoundRecord,
    digest_field: str,
) -> dict[str, object]:
    payload = record.model_dump(mode="json")
    return {
        "artifact_name": artifact_name,
        "contract_type": payload["contract_type"],
        "record_id": next(
            payload[field]
            for field in (
                "dataset_id",
                "fixture_suite_id",
                "specification_id",
                "candidate_id",
                "run_id",
                "report_id",
                "dossier_id",
            )
            if field in payload
        ),
        "record_digest": payload[digest_field],
    }


def evidence_index(
    *,
    source_commit: str,
    dirty_worktree: bool,
    dataset: DatasetManifestV1,
    fixtures: FixtureManifestV1,
    specification: AnnotationSpecificationV1,
    annotation_qa: AnnotationQaReportV1,
    split_report: SplitValidationReportV1,
    metric_report: MetricReportV1,
    evaluation_run: EvaluationRunManifestV1,
    candidates: dict[str, CandidateArtifactManifestV1],
    source_dossier: SourceResearchDossierV1,
) -> dict[str, object]:
    records = [
        _record_entry("dataset-manifest-v1.json", dataset, "manifest_digest"),
        _record_entry("fixture-manifest-v1.json", fixtures, "manifest_digest"),
        _record_entry(
            "annotation-specification-v1.json",
            specification,
            "specification_digest",
        ),
        _record_entry("annotation-qa-report-v1.json", annotation_qa, "report_digest"),
        _record_entry("split-validation-report-v1.json", split_report, "report_digest"),
        _record_entry("metric-report-v1.json", metric_report, "report_digest"),
        _record_entry("evaluation-run-v1.json", evaluation_run, "manifest_digest"),
        _record_entry(
            "source-research-dossier-v1.json",
            source_dossier,
            "dossier_digest",
        ),
    ]
    records.extend(
        _record_entry(
            f"candidate-{candidate_id.lower()}.json",
            candidate,
            "manifest_digest",
        )
        for candidate_id, candidate in sorted(candidates.items())
    )
    document = {
        "contract_format": "hcam.analytics.p3-1-evidence-index.v1",
        "baseline_version": BASELINE_VERSION,
        "generated_at": BASELINE_AT.isoformat().replace("+00:00", "Z"),
        "source_commit": source_commit,
        "dirty_worktree": dirty_worktree,
        "records": records,
        "assertions": {
            "generated_only": True,
            "external_downloads": 0,
            "model_artifacts": 0,
            "media_artifacts": 0,
            "network_required": False,
            "gpu_required": False,
            "secrets_required": False,
            "candidate_count": len(candidates),
            "candidate_eligible_count": sum(
                candidate.eligibility == "eligible" for candidate in candidates.values()
            ),
            "unresolved_candidate_blockers": len(source_dossier.unresolved_blockers),
        },
        "known_limitations": [
            "Generated evidence does not establish real-world model accuracy",
            "No model artifact dataset font or media source was downloaded",
            "Numeric gates remain proposal only",
            "P3.2 remains blocked until an exact detector artifact and dataset are approved",
        ],
        "p3_2_status": "blocked_pending_exact_artifact_and_dataset_approval",
        "owner_acceptance": {
            "status": "pending",
            "required_record": "D-P3.1-ACCEPTANCE",
        },
    }
    document["index_digest"] = canonical_digest(document)
    return document


def build_baseline_evidence(
    *,
    source_commit: str,
    dirty_worktree: bool,
    generator_code_digest: str,
    dependency_lock_digest: str,
    container_profile_digest: str | None,
) -> dict[str, object]:
    documents = generated_fixture_documents()
    specification = approved_annotation_specification()
    annotation_items = generated_annotation_items()
    documents["annotation-items-v1.json"] = {
        "contract_type": "hcam.analytics.generated-annotation-suite.v1",
        "suite": "annotation-items-v1",
        "seed": FIXTURE_SEED,
        "generated_only": True,
        "external_inputs": [],
        "records": [item.model_dump(mode="json") for item in annotation_items],
    }
    annotation_qa = validate_annotations(
        annotation_items,
        specification,
        approved_classes=set(APPROVED_EMITTED_CLASSES),
        generated_at=BASELINE_AT,
    )
    split_items = generated_split_items()
    documents["split-items-v1.json"] = {
        "contract_type": "hcam.analytics.generated-split-suite.v1",
        "suite": "split-items-v1",
        "seed": FIXTURE_SEED,
        "generated_only": True,
        "external_inputs": [],
        "records": [item.model_dump(mode="json") for item in split_items],
    }
    split_report = generated_split_report(split_items)
    fixtures = generated_fixture_manifest(
        documents,
        generator_code_digest=generator_code_digest,
    )
    dataset = generated_dataset_manifest(
        documents,
        specification,
        split_items,
        split_report,
    )
    metric_report = golden_metric_report()
    candidates = candidate_manifests()
    dossier = source_research_dossier(candidates)
    evaluation_run = generated_evaluation_run(
        source_commit=source_commit,
        dirty_worktree=dirty_worktree,
        dependency_lock_digest=dependency_lock_digest,
        container_profile_digest=container_profile_digest,
        dataset=dataset,
        fixtures=fixtures,
        annotation_qa=annotation_qa,
        split_report=split_report,
        metric_report=metric_report,
        source_dossier=dossier,
    )
    index = evidence_index(
        source_commit=source_commit,
        dirty_worktree=dirty_worktree,
        dataset=dataset,
        fixtures=fixtures,
        specification=specification,
        annotation_qa=annotation_qa,
        split_report=split_report,
        metric_report=metric_report,
        evaluation_run=evaluation_run,
        candidates=candidates,
        source_dossier=dossier,
    )
    return {
        "evaluation-contracts.json": evaluation_contract_bundle(),
        "annotation-specification-v1.json": specification,
        "annotation-qa-report-v1.json": annotation_qa,
        "split-validation-report-v1.json": split_report,
        "fixture-manifest-v1.json": fixtures,
        "dataset-manifest-v1.json": dataset,
        "metric-report-v1.json": metric_report,
        "evaluation-run-v1.json": evaluation_run,
        "source-research-dossier-v1.json": dossier,
        "evidence-index.json": index,
        "generated": documents,
        "candidates": candidates,
    }
