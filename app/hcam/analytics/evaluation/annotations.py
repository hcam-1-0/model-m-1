from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from hcam.analytics.contracts import NormalizedBoundingBox
from hcam.analytics.evaluation.contracts import (
    AnnotationSpecificationV1,
    ClassId,
    Digest,
    DigestBoundRecord,
    EvaluationContractModel,
    StableId,
    UtcDateTime,
    seal_record,
)


class AnnotationObjectV1(EvaluationContractModel):
    annotation_id: StableId
    task: Literal["detection", "tracking", "geometry", "synthetic_plate"]
    class_id: ClassId | None = None
    bbox: NormalizedBoundingBox | None = None
    track_id: StableId | None = None
    geometry_id: StableId | None = None
    plate_text: Annotated[str, Field(min_length=1, max_length=32)] | None = None
    plate_script: Literal["Latin", "Devanagari", "Gujarati"] | None = None
    ignore: bool = False
    uncertain: bool = False
    occlusion: Literal["none", "partial", "heavy", "unknown"] = "unknown"
    truncated: bool = False
    attributes: Annotated[dict[StableId, str | int | float | bool], Field(max_length=64)] = (
        Field(default_factory=dict)
    )

    @model_validator(mode="after")
    def task_fields_are_consistent(self) -> AnnotationObjectV1:
        if self.task in {"detection", "tracking"}:
            if self.class_id is None or self.bbox is None:
                raise ValueError("detection/tracking annotation requires class and bbox")
        if self.task == "tracking" and self.track_id is None:
            raise ValueError("tracking annotation requires track_id")
        if self.task == "geometry" and self.geometry_id is None:
            raise ValueError("geometry annotation requires geometry_id")
        if self.task == "synthetic_plate":
            if self.plate_text is None or self.plate_script is None or self.bbox is None:
                raise ValueError("synthetic plate annotation requires text, script, and bbox")
        elif self.plate_text is not None or self.plate_script is not None:
            raise ValueError("plate fields are limited to synthetic_plate annotations")
        return self


class AnnotationItemV1(EvaluationContractModel):
    item_id: StableId
    sequence_id: StableId
    frame_sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    split: Literal["train", "validation", "test"]
    generator_family: StableId
    seed_group: StableId
    template_group: StableId
    annotations: Annotated[list[AnnotationObjectV1], Field(max_length=1_000)] = Field(
        default_factory=list
    )
    annotator_id: StableId
    tool_version: StableId
    normalization_version: StableId
    annotated_at: UtcDateTime


class AnnotationQaIssueV1(EvaluationContractModel):
    issue_code: StableId
    severity: Literal["error", "warning"]
    item_id: StableId
    annotation_id: StableId | None = None


class AnnotationQaReportV1(DigestBoundRecord):
    digest_field = "report_digest"
    contract_type: Literal["hcam.analytics.annotation-qa-report.v1"] = (
        "hcam.analytics.annotation-qa-report.v1"
    )
    report_id: StableId
    report_digest: Digest
    specification_digest: Digest
    generated_at: UtcDateTime
    item_count: Annotated[int, Field(ge=0, le=10_000_000)]
    annotation_count: Annotated[int, Field(ge=0, le=100_000_000)]
    invalid_item_count: Annotated[int, Field(ge=0, le=10_000_000)]
    corrected_item_count: Annotated[int, Field(ge=0, le=10_000_000)]
    disagreement_count: Annotated[int, Field(ge=0, le=10_000_000)]
    issue_counts: Annotated[dict[StableId, int], Field(max_length=256)]
    issues: Annotated[list[AnnotationQaIssueV1], Field(max_length=10_000)]
    unresolved_blockers: Annotated[list[StableId], Field(max_length=256)]
    status: Literal["pass", "fail"]

    @model_validator(mode="after")
    def qa_counts_are_consistent(self) -> AnnotationQaReportV1:
        if self.corrected_item_count > self.invalid_item_count:
            raise ValueError("corrected item count cannot exceed invalid item count")
        counted = Counter(issue.issue_code for issue in self.issues)
        if dict(sorted(counted.items())) != dict(sorted(self.issue_counts.items())):
            raise ValueError("QA issue counts do not match issue records")
        has_error = any(issue.severity == "error" for issue in self.issues)
        if self.status == "pass" and (has_error or self.unresolved_blockers):
            raise ValueError("passing QA report cannot contain errors or blockers")
        if self.status == "fail" and not (has_error or self.unresolved_blockers):
            raise ValueError("failed QA report requires an error or blocker")
        return self


def _issue(
    code: str,
    item: AnnotationItemV1,
    *,
    annotation: AnnotationObjectV1 | None = None,
    severity: Literal["error", "warning"] = "error",
) -> AnnotationQaIssueV1:
    return AnnotationQaIssueV1(
        issue_code=code,
        severity=severity,
        item_id=item.item_id,
        annotation_id=annotation.annotation_id if annotation else None,
    )


def validate_annotations(
    items: list[AnnotationItemV1],
    specification: AnnotationSpecificationV1,
    *,
    approved_classes: set[str],
    generated_at: datetime | None = None,
) -> AnnotationQaReportV1:
    issues: list[AnnotationQaIssueV1] = []
    seen_items: set[str] = set()
    sequence_frames: dict[str, list[int]] = defaultdict(list)
    required_attributes = {
        attribute.name for attribute in specification.attributes if attribute.required
    }
    allowed_attributes = {attribute.name for attribute in specification.attributes}

    for item in items:
        if item.item_id in seen_items:
            issues.append(_issue("duplicate-item-id", item))
        seen_items.add(item.item_id)
        sequence_frames[item.sequence_id].append(item.frame_sequence)

        annotation_ids: set[str] = set()
        tracks_in_frame: set[str] = set()
        for annotation in item.annotations:
            if annotation.annotation_id in annotation_ids:
                issues.append(_issue("duplicate-annotation-id", item, annotation=annotation))
            annotation_ids.add(annotation.annotation_id)
            if annotation.task not in specification.tasks:
                issues.append(_issue("task-not-in-specification", item, annotation=annotation))
            if annotation.class_id and annotation.class_id not in approved_classes:
                issues.append(_issue("class-not-in-taxonomy", item, annotation=annotation))
            keys = set(annotation.attributes)
            if not required_attributes.issubset(keys):
                issues.append(_issue("required-attribute-missing", item, annotation=annotation))
            if not keys.issubset(allowed_attributes):
                issues.append(_issue("unknown-attribute", item, annotation=annotation))
            if annotation.track_id:
                if annotation.track_id in tracks_in_frame:
                    issues.append(_issue("duplicate-track-in-frame", item, annotation=annotation))
                tracks_in_frame.add(annotation.track_id)

    for sequence_id, frame_sequences in sequence_frames.items():
        if frame_sequences != sorted(frame_sequences) or len(frame_sequences) != len(
            set(frame_sequences)
        ):
            item = next(value for value in items if value.sequence_id == sequence_id)
            issues.append(_issue("sequence-order-invalid", item))

    invalid_items = {issue.item_id for issue in issues if issue.severity == "error"}
    counts = dict(sorted(Counter(issue.issue_code for issue in issues).items()))
    timestamp = generated_at or datetime(2026, 8, 24, 12, 30, tzinfo=UTC)
    document = {
        "report_id": "p31-generated-annotation-qa-v1",
        "specification_digest": specification.specification_digest,
        "generated_at": timestamp,
        "item_count": len(items),
        "annotation_count": sum(len(item.annotations) for item in items),
        "invalid_item_count": len(invalid_items),
        "corrected_item_count": 0,
        "disagreement_count": 0,
        "issue_counts": counts,
        "issues": [issue.model_dump(mode="json") for issue in issues],
        "unresolved_blockers": sorted(counts) if invalid_items else [],
        "status": "fail" if invalid_items else "pass",
    }
    return seal_record(AnnotationQaReportV1, document)
