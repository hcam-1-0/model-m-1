from __future__ import annotations

import copy
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hcam.analytics.contracts import NormalizedBoundingBox
from hcam.analytics.evaluation.annotations import (
    AnnotationItemV1,
    AnnotationObjectV1,
    validate_annotations,
)
from hcam.analytics.evaluation.baseline import (
    approved_annotation_specification,
    build_baseline_evidence,
    bytes_digest,
    generated_annotation_items,
    generated_annotation_qa_report,
    generated_evaluation_run,
    generated_split_items,
    generated_split_report,
    rendered_json_bytes,
)
from hcam.analytics.evaluation.candidates import (
    CANDIDATES,
    REPOSITORIES,
    SourceResearchDossierV1,
    candidate_manifests,
    research_references,
    source_research_dossier,
)
from hcam.analytics.evaluation.contracts import canonical_digest, seal_record
from hcam.analytics.evaluation.fixtures import (
    APPROVED_EMITTED_CLASSES,
    FIXTURE_SEED,
    SyntheticPlateFixtureV1,
    TrackingAssociationV1,
    TrackingFixtureV1,
    fixture_document_digest,
    generated_detection_fixtures,
    generated_fixture_documents,
    generated_geometry_fixtures,
    generated_misuse_fixtures,
    generated_plate_fixtures,
    generated_tracking_fixtures,
)
from hcam.analytics.evaluation.metrics import (
    evaluate_detection,
    evaluate_geometry,
    evaluate_synthetic_plates,
    evaluate_tracking,
    intersection_over_union,
)
from hcam.analytics.evaluation.splits import (
    FinalTestAccessV1,
    SplitItemV1,
    SplitValidationReportV1,
    deterministic_split,
    validate_splits,
)


DIGEST = f"sha256:{'2' * 64}"
COMMIT = "2" * 40


@pytest.fixture(scope="module")
def evidence() -> dict[str, object]:
    return build_baseline_evidence(
        source_commit=COMMIT,
        dirty_worktree=True,
        generator_code_digest=DIGEST,
        dependency_lock_digest=DIGEST,
        container_profile_digest=None,
    )


def test_generated_fixture_matrix_is_deterministic_and_complete() -> None:
    first = generated_fixture_documents()
    second = generated_fixture_documents()

    assert first == second
    assert {name: len(document["records"]) for name, document in first.items()} == {
        "detection-v1.json": 15,
        "geometry-v1.json": 10,
        "misuse-v1.json": 11,
        "synthetic-plate-v1.json": 5,
        "tracking-v1.json": 10,
    }
    assert all(document["seed"] == FIXTURE_SEED for document in first.values())
    assert all(document["generated_only"] for document in first.values())
    assert all(document["external_inputs"] == [] for document in first.values())
    assert fixture_document_digest(first) == fixture_document_digest(second)


def test_detection_fixtures_cover_taxonomy_and_required_slices() -> None:
    fixtures = generated_detection_fixtures()
    classes = {truth.class_id for fixture in fixtures for truth in fixture.truths}
    scenarios = {fixture.scenario for fixture in fixtures}

    assert classes == set(APPROVED_EMITTED_CLASSES)
    assert {
        "empty-scene",
        "overlap",
        "truncation",
        "occlusion",
        "small-object",
        "low-contrast",
        "false-positive",
        "malformed-prediction",
    } <= scenarios
    assert generated_detection_fixtures() == generated_detection_fixtures(FIXTURE_SEED)
    assert generated_detection_fixtures(99) != fixtures


def test_tracking_geometry_plate_and_misuse_suites_cover_required_cases() -> None:
    tracking = generated_tracking_fixtures()
    geometry = generated_geometry_fixtures()
    plates = generated_plate_fixtures()
    misuse = generated_misuse_fixtures()

    assert {fixture.scenario for fixture in tracking} == {
        "bounded-state",
        "crossing-tracks",
        "discontinuity",
        "duplicate-detection",
        "missed-frames",
        "occlusion",
        "reconnect",
        "start",
        "update",
        "end",
    }
    assert {fixture.geometry_kind for fixture in geometry} == {
        "line",
        "ordering",
        "schedule",
        "zone",
    }
    assert {fixture.script for fixture in plates} == {"Latin", "Devanagari", "Gujarati"}
    assert any(fixture.abstained for fixture in plates)
    assert any(not fixture.valid_format for fixture in plates)
    assert {fixture.payload_kind for fixture in misuse} == {
        "biometric",
        "credential",
        "government",
        "invalid_digest",
        "media",
        "oversized",
        "owner",
        "path",
        "url",
        "watchlist",
    }
    assert all(not fixture.contains_sensitive_value for fixture in misuse)


def test_fixture_models_reject_invalid_tracking_and_plate_states() -> None:
    with pytest.raises(ValidationError, match="requires a truth or predicted track"):
        TrackingAssociationV1(frame_sequence=0, visible=False)

    association = TrackingAssociationV1(
        frame_sequence=1,
        truth_track_id="truth-001",
        predicted_track_id="predicted-001",
        visible=True,
    )
    earlier = association.model_copy(update={"frame_sequence": 0})
    with pytest.raises(ValidationError, match="must be ordered"):
        TrackingFixtureV1(
            case_id="tracking-invalid-order",
            scenario="invalid-order",
            tracker_epoch="epoch-001",
            associations=[association, earlier],
            expected_identity_switches=0,
            expected_fragments=0,
            expected_outcome="reject",
        )

    box = NormalizedBoundingBox(x=0.1, y=0.1, width=0.2, height=0.2)
    with pytest.raises(ValidationError, match="cannot contain alternatives"):
        SyntheticPlateFixtureV1(
            case_id="plate-invalid-abstention",
            scenario="invalid-abstention",
            script="Latin",
            truth_text="GJ01AA0001",
            alternatives=[{"text": "GJ01AA0001", "confidence": 1.0}],
            abstained=True,
            valid_format=True,
            region_bbox=box,
            expected_outcome="reject",
        )
    with pytest.raises(ValidationError, match="requires alternatives"):
        SyntheticPlateFixtureV1(
            case_id="plate-invalid-empty",
            scenario="invalid-empty",
            script="Latin",
            truth_text="GJ01AA0001",
            alternatives=[],
            abstained=False,
            valid_format=True,
            region_bbox=box,
            expected_outcome="reject",
        )


def test_annotation_calibration_passes_for_all_four_tasks() -> None:
    specification = approved_annotation_specification()
    items = generated_annotation_items()
    report = generated_annotation_qa_report(specification)

    assert {annotation.task for item in items for annotation in item.annotations} == {
        "detection",
        "geometry",
        "synthetic_plate",
        "tracking",
    }
    assert report.status == "pass"
    assert report.item_count == 4
    assert report.annotation_count == 4
    assert report.issue_counts == {}
    assert report.unresolved_blockers == []


def _annotation_item(
    *,
    item_id: str,
    sequence_id: str,
    frame_sequence: int,
    annotations: list[AnnotationObjectV1],
) -> AnnotationItemV1:
    return AnnotationItemV1(
        item_id=item_id,
        sequence_id=sequence_id,
        frame_sequence=frame_sequence,
        split="validation",
        generator_family="generated-qa-negative",
        seed_group="seed-negative",
        template_group="template-negative",
        annotations=annotations,
        annotator_id="generator-p31",
        tool_version="hcam-generated-annotation-v1",
        normalization_version="hcam-normalization-v1",
        annotated_at=datetime(2026, 8, 24, 13, 0, tzinfo=UTC),
    )


def test_annotation_validator_reports_duplicates_taxonomy_attributes_and_order() -> None:
    specification = approved_annotation_specification()
    box = NormalizedBoundingBox(x=0.1, y=0.1, width=0.2, height=0.2)
    first = AnnotationObjectV1(
        annotation_id="negative-object-001",
        task="tracking",
        class_id="vehicle.car",
        bbox=box,
        track_id="negative-track-001",
        attributes={"unknown-attribute": True},
    )
    second = first.model_copy(update={"annotation_id": "negative-object-002"})
    late = _annotation_item(
        item_id="negative-item-001",
        sequence_id="negative-sequence",
        frame_sequence=2,
        annotations=[first, second, second],
    )
    early = _annotation_item(
        item_id="negative-item-002",
        sequence_id="negative-sequence",
        frame_sequence=1,
        annotations=[],
    )

    report = validate_annotations(
        [late, early, early],
        specification,
        approved_classes={"object.person"},
    )

    assert report.status == "fail"
    assert {
        "class-not-in-taxonomy",
        "duplicate-annotation-id",
        "duplicate-item-id",
        "duplicate-track-in-frame",
        "required-attribute-missing",
        "sequence-order-invalid",
        "unknown-attribute",
    } <= set(report.issue_counts)
    assert report.invalid_item_count == 2
    assert set(report.unresolved_blockers) == set(report.issue_counts)


def test_annotation_validator_detects_task_not_in_specification() -> None:
    specification = approved_annotation_specification()
    document = specification.model_dump(mode="json")
    document["tasks"] = ["detection", "tracking", "synthetic_plate"]
    document["status"] = "draft"
    reduced = seal_record(type(specification), document)

    report = validate_annotations(
        generated_annotation_items(),
        reduced,
        approved_classes=set(APPROVED_EMITTED_CLASSES),
    )

    assert report.status == "fail"
    assert report.issue_counts["task-not-in-specification"] == 1


def test_annotation_object_fields_are_task_specific() -> None:
    box = NormalizedBoundingBox(x=0.1, y=0.1, width=0.2, height=0.2)
    with pytest.raises(ValidationError, match="requires class and bbox"):
        AnnotationObjectV1(annotation_id="invalid-detection", task="detection")
    with pytest.raises(ValidationError, match="requires track_id"):
        AnnotationObjectV1(
            annotation_id="invalid-tracking",
            task="tracking",
            class_id="vehicle.car",
            bbox=box,
        )
    with pytest.raises(ValidationError, match="requires geometry_id"):
        AnnotationObjectV1(annotation_id="invalid-geometry", task="geometry")
    with pytest.raises(ValidationError, match="requires text"):
        AnnotationObjectV1(
            annotation_id="invalid-plate",
            task="synthetic_plate",
            bbox=box,
        )
    with pytest.raises(ValidationError, match="limited to synthetic_plate"):
        AnnotationObjectV1(
            annotation_id="invalid-plate-fields",
            task="detection",
            class_id="vehicle.car",
            bbox=box,
            plate_text="GJ01AA0001",
            plate_script="Latin",
        )


def test_split_assignment_is_deterministic_and_baseline_has_all_splits() -> None:
    items = generated_split_items()
    report = generated_split_report(items)

    assert deterministic_split("stable-group") == deterministic_split("stable-group")
    assert {item.split for item in items} == {"train", "validation", "test"}
    assert all(
        deterministic_split(item.group_values["generator-group"]) == item.split
        for item in items
    )
    assert report.status == "pass"
    assert report.split_counts == {"train": 2, "validation": 2, "test": 2}
    assert report.exact_duplicate_count == 0
    assert report.cross_split_group_count == 0
    assert report.missing_group_key_count == 0


def test_split_validator_fails_on_duplicates_groups_and_missing_keys() -> None:
    items = generated_split_items()
    train = items[0]
    test = items[-1]
    duplicate = SplitItemV1(
        item_id="leakage-duplicate",
        content_digest=train.content_digest,
        split="test",
        group_values={
            "generator-group": train.group_values["generator-group"],
            "seed-group": "leakage-seed",
        },
    )
    report = validate_splits(
        [train, test, duplicate],
        required_group_keys=["generator-group", "seed-group", "template-group"],
        final_test_frozen=True,
    )

    assert report.status == "fail"
    assert report.exact_duplicate_count == 1
    assert report.cross_split_group_count == 1
    assert report.missing_group_key_count == 1
    assert {issue.issue_code for issue in report.issues} == {
        "exact-duplicate-cross-split",
        "group-crosses-splits",
        "required-group-key-missing",
    }


def test_split_report_and_final_test_access_are_fail_closed() -> None:
    with pytest.raises(ValidationError):
        FinalTestAccessV1(
            access_id="access-invalid",
            actor_id="mayank-admin",
            reason="Attempted tuning",
            accessed_at=datetime(2026, 8, 24, tzinfo=UTC),
            tuning_use=True,
        )

    report = generated_split_report(generated_split_items())
    document = report.model_dump(mode="json")
    document["exact_duplicate_count"] = 1
    with pytest.raises(ValidationError, match="count does not match"):
        seal_record(SplitValidationReportV1, document)

    document = report.model_dump(mode="json")
    document["status"] = "fail"
    with pytest.raises(ValidationError, match="requires leakage evidence"):
        seal_record(SplitValidationReportV1, document)


def test_detection_metric_golden_values_and_threshold_validation() -> None:
    summary = evaluate_detection(generated_detection_fixtures())

    assert summary.truth_count == 13
    assert summary.prediction_count == 8
    assert summary.true_positives == 7
    assert summary.false_positives == 1
    assert summary.false_negatives == 6
    assert summary.invalid_case_count == 1
    assert summary.precision == pytest.approx(0.875)
    assert summary.recall == pytest.approx(7 / 13)
    assert summary.f1 == pytest.approx(2 * 0.875 * (7 / 13) / (0.875 + (7 / 13)))
    assert set(summary.per_class_ap50) == set(APPROVED_EMITTED_CLASSES)
    with pytest.raises(ValueError, match="IoU threshold"):
        evaluate_detection(generated_detection_fixtures(), iou_threshold=0)


def test_iou_and_empty_detection_metrics_cover_boundary_cases() -> None:
    box = NormalizedBoundingBox(x=0.1, y=0.1, width=0.2, height=0.2)
    separate = NormalizedBoundingBox(x=0.8, y=0.8, width=0.1, height=0.1)
    overlap = NormalizedBoundingBox(x=0.2, y=0.1, width=0.2, height=0.2)

    assert intersection_over_union(box, box) == pytest.approx(1.0)
    assert intersection_over_union(box, separate) == 0.0
    assert intersection_over_union(box, overlap) == pytest.approx(1 / 3)
    empty = evaluate_detection([])
    assert empty.precision == 0
    assert empty.recall == 0
    assert empty.map50 == 0


def test_tracking_geometry_and_plate_metric_goldens() -> None:
    tracking = evaluate_tracking(generated_tracking_fixtures())
    assert tracking.idf1 == 1.0
    assert tracking.identity_switches == 1
    assert tracking.fragments == 2
    assert tracking.epoch_reset_cases == 2

    fixtures = generated_geometry_fixtures()
    expected = {fixture.case_id: list(fixture.expected_events) for fixture in fixtures}
    predicted = copy.deepcopy(expected)
    predicted[next(iter(predicted))].append("duplicate-event")
    predicted["unknown-case"] = ["unexpected-event", "unexpected-event"]
    geometry = evaluate_geometry(
        expected,
        predicted,
        onset_errors_ms=[10.0, 20.0],
        termination_errors_ms=[30.0],
    )
    assert geometry.false_positives == 3
    assert geometry.duplicate_events == 1
    assert geometry.onset_error_ms == 15.0
    assert geometry.termination_error_ms == 30.0

    plates = evaluate_synthetic_plates(generated_plate_fixtures())
    assert plates.evaluated_count == 4
    assert plates.abstention_count == 1
    assert plates.exact_match_count == 2
    assert plates.top_k_match_count == 3
    assert plates.character_errors == 11
    assert plates.character_count == 38
    assert plates.script_counts == {"Devanagari": 1, "Gujarati": 1, "Latin": 2}


def test_candidate_portfolio_is_metadata_only_blocked_and_complete() -> None:
    manifests = candidate_manifests()
    references = research_references()
    dossier = source_research_dossier(manifests)

    assert set(manifests) == {candidate.candidate_id for candidate in CANDIDATES}
    assert set(references) == set(REPOSITORIES)
    assert len(manifests) == 11
    assert all(manifest.eligibility == "blocked" for manifest in manifests.values())
    assert all(manifest.blockers for manifest in manifests.values())
    assert all(manifest.approval.status == "pending" for manifest in manifests.values())
    assert dossier.downloaded_artifacts == []
    assert dossier.owner_decision_required_before_download is True
    assert dossier.unresolved_blockers
    assert source_research_dossier(manifests).dossier_digest == dossier.dossier_digest


def test_source_dossier_rejects_duplicate_references_and_candidates() -> None:
    dossier = source_research_dossier()
    document = dossier.model_dump(mode="json")
    document["references"].append(copy.deepcopy(document["references"][0]))
    with pytest.raises(ValidationError, match="references must be unique"):
        seal_record(SourceResearchDossierV1, document)

    document = dossier.model_dump(mode="json")
    document["candidates"].append(copy.deepcopy(document["candidates"][0]))
    with pytest.raises(ValidationError, match="candidates must be unique"):
        seal_record(SourceResearchDossierV1, document)


def test_baseline_evidence_binds_every_artifact_and_keeps_p3_2_blocked(
    evidence: dict[str, object],
) -> None:
    index = evidence["evidence-index.json"]
    run = evidence["evaluation-run-v1.json"]
    fixture_manifest = evidence["fixture-manifest-v1.json"]
    generated = evidence["generated"]

    assert index["assertions"] == {  # type: ignore[index]
        "candidate_count": 11,
        "candidate_eligible_count": 0,
        "external_downloads": 0,
        "generated_only": True,
        "gpu_required": False,
        "media_artifacts": 0,
        "model_artifacts": 0,
        "network_required": False,
        "secrets_required": False,
        "unresolved_candidate_blockers": len(
            evidence["source-research-dossier-v1.json"].unresolved_blockers  # type: ignore[attr-defined]
        ),
    }
    assert index["p3_2_status"] == "blocked_pending_exact_artifact_and_dataset_approval"  # type: ignore[index]
    assert index["owner_acceptance"]["status"] == "pending"  # type: ignore[index]
    assert run.command.network_access == "denied"  # type: ignore[attr-defined]
    assert run.command.gpu_access == "denied"  # type: ignore[attr-defined]
    assert run.candidate is None  # type: ignore[attr-defined]
    assert run.reproducibility_status == "pass"  # type: ignore[attr-defined]
    assert any("dirty" in warning for warning in run.warnings)  # type: ignore[attr-defined]
    assert len(fixture_manifest.files) == len(generated)  # type: ignore[attr-defined,arg-type]
    expected_hashes = {
        name: bytes_digest(rendered_json_bytes(document))
        for name, document in generated.items()  # type: ignore[union-attr]
    }
    assert {
        file.artifact_name: file.digest for file in fixture_manifest.files  # type: ignore[attr-defined]
    } == expected_hashes

    digest = index["index_digest"]  # type: ignore[index]
    without_digest = copy.deepcopy(index)
    without_digest.pop("index_digest")  # type: ignore[union-attr]
    assert digest == canonical_digest(without_digest)


def test_clean_baseline_omits_dirty_warning(evidence: dict[str, object]) -> None:
    clean = generated_evaluation_run(
        source_commit=COMMIT,
        dirty_worktree=False,
        dependency_lock_digest=DIGEST,
        container_profile_digest=None,
        dataset=evidence["dataset-manifest-v1.json"],  # type: ignore[arg-type]
        fixtures=evidence["fixture-manifest-v1.json"],  # type: ignore[arg-type]
        annotation_qa=evidence["annotation-qa-report-v1.json"],  # type: ignore[arg-type]
        split_report=evidence["split-validation-report-v1.json"],  # type: ignore[arg-type]
        metric_report=evidence["metric-report-v1.json"],  # type: ignore[arg-type]
        source_dossier=evidence["source-research-dossier-v1.json"],  # type: ignore[arg-type]
    )

    assert not any("dirty" in warning for warning in clean.warnings)
