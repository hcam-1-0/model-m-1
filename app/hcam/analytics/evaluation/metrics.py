from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Annotated

from pydantic import Field

from hcam.analytics.contracts import NormalizedBoundingBox
from hcam.analytics.evaluation.contracts import (
    ApprovalRecordV1,
    HardGateResultV1,
    MetricReportV1,
    MetricValueV1,
    PopulationDefinitionV1,
    seal_record,
)
from hcam.analytics.evaluation.fixtures import (
    DetectionFixtureV1,
    SyntheticPlateFixtureV1,
    TrackingFixtureV1,
)
from hcam.analytics.evaluation.contracts import EvaluationContractModel


class DetectionMetricSummaryV1(EvaluationContractModel):
    truth_count: Annotated[int, Field(ge=0)]
    prediction_count: Annotated[int, Field(ge=0)]
    true_positives: Annotated[int, Field(ge=0)]
    false_positives: Annotated[int, Field(ge=0)]
    false_negatives: Annotated[int, Field(ge=0)]
    invalid_case_count: Annotated[int, Field(ge=0)]
    precision: Annotated[float, Field(ge=0, le=1)]
    recall: Annotated[float, Field(ge=0, le=1)]
    f1: Annotated[float, Field(ge=0, le=1)]
    map50: Annotated[float, Field(ge=0, le=1)]
    per_class_ap50: dict[str, Annotated[float, Field(ge=0, le=1)]]
    confusion: dict[str, int]


class TrackingMetricSummaryV1(EvaluationContractModel):
    truth_associations: Annotated[int, Field(ge=0)]
    predicted_associations: Annotated[int, Field(ge=0)]
    matched_associations: Annotated[int, Field(ge=0)]
    id_precision: Annotated[float, Field(ge=0, le=1)]
    id_recall: Annotated[float, Field(ge=0, le=1)]
    idf1: Annotated[float, Field(ge=0, le=1)]
    identity_switches: Annotated[int, Field(ge=0)]
    fragments: Annotated[int, Field(ge=0)]
    epoch_reset_cases: Annotated[int, Field(ge=0)]


class GeometryMetricSummaryV1(EvaluationContractModel):
    expected_events: Annotated[int, Field(ge=0)]
    predicted_events: Annotated[int, Field(ge=0)]
    true_positives: Annotated[int, Field(ge=0)]
    false_positives: Annotated[int, Field(ge=0)]
    false_negatives: Annotated[int, Field(ge=0)]
    duplicate_events: Annotated[int, Field(ge=0)]
    precision: Annotated[float, Field(ge=0, le=1)]
    recall: Annotated[float, Field(ge=0, le=1)]
    duplicate_rate: Annotated[float, Field(ge=0, le=1)]
    onset_error_ms: Annotated[float, Field(ge=0)]
    termination_error_ms: Annotated[float, Field(ge=0)]


class PlateMetricSummaryV1(EvaluationContractModel):
    evaluated_count: Annotated[int, Field(ge=0)]
    abstention_count: Annotated[int, Field(ge=0)]
    exact_match_count: Annotated[int, Field(ge=0)]
    top_k_match_count: Annotated[int, Field(ge=0)]
    character_errors: Annotated[int, Field(ge=0)]
    character_count: Annotated[int, Field(ge=0)]
    exact_match_rate: Annotated[float, Field(ge=0, le=1)]
    top_k_coverage: Annotated[float, Field(ge=0, le=1)]
    character_error_rate: Annotated[float, Field(ge=0, le=1)]
    script_counts: dict[str, Annotated[int, Field(ge=0)]]


def _ratio(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _f1(precision: float, recall: float) -> float:
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def intersection_over_union(
    left: NormalizedBoundingBox,
    right: NormalizedBoundingBox,
) -> float:
    left_x2 = left.x + left.width
    left_y2 = left.y + left.height
    right_x2 = right.x + right.width
    right_y2 = right.y + right.height
    intersection_width = max(0.0, min(left_x2, right_x2) - max(left.x, right.x))
    intersection_height = max(0.0, min(left_y2, right_y2) - max(left.y, right.y))
    intersection = intersection_width * intersection_height
    union = left.width * left.height + right.width * right.height - intersection
    return 0.0 if union <= 0 else intersection / union


def _average_precision(matches: list[bool], truth_count: int) -> float:
    if truth_count == 0:
        return 0.0
    true_positives = 0
    false_positives = 0
    recalls: list[float] = []
    precisions: list[float] = []
    for matched in matches:
        if matched:
            true_positives += 1
        else:
            false_positives += 1
        recalls.append(true_positives / truth_count)
        precisions.append(true_positives / (true_positives + false_positives))
    points = [(0.0, 1.0), *zip(recalls, precisions, strict=True), (1.0, 0.0)]
    recall_values = [point[0] for point in points]
    precision_values = [point[1] for point in points]
    for index in range(len(precision_values) - 2, -1, -1):
        precision_values[index] = max(precision_values[index], precision_values[index + 1])
    area = 0.0
    for index in range(1, len(recall_values)):
        delta = recall_values[index] - recall_values[index - 1]
        if delta > 0:
            area += delta * precision_values[index]
    return area


def evaluate_detection(
    fixtures: list[DetectionFixtureV1],
    *,
    iou_threshold: float = 0.5,
) -> DetectionMetricSummaryV1:
    if not 0 < iou_threshold <= 1:
        raise ValueError("IoU threshold must be within (0, 1]")
    valid = [fixture for fixture in fixtures if fixture.expected_outcome != "reject"]
    invalid_count = len(fixtures) - len(valid)
    truth_count = sum(len(fixture.truths) for fixture in valid)
    prediction_count = sum(len(fixture.predictions) for fixture in valid)
    matched_truths: set[tuple[str, str]] = set()
    true_positives = 0
    false_positives = 0
    confusion: Counter[str] = Counter()

    class_truths: dict[str, int] = Counter(
        truth.class_id for fixture in valid for truth in fixture.truths
    )
    ranked_by_class: dict[str, list[tuple[float, bool]]] = defaultdict(list)
    for fixture in valid:
        for prediction in sorted(
            fixture.predictions,
            key=lambda value: (-value.confidence, value.prediction_id),
        ):
            candidates = [
                truth
                for truth in fixture.truths
                if truth.class_id == prediction.class_id
                and (fixture.case_id, truth.object_id) not in matched_truths
            ]
            best = max(
                candidates,
                key=lambda truth: intersection_over_union(truth.bbox, prediction.bbox),
                default=None,
            )
            matched = bool(
                best
                and intersection_over_union(best.bbox, prediction.bbox) >= iou_threshold
            )
            ranked_by_class[prediction.class_id].append((prediction.confidence, matched))
            if matched and best is not None:
                matched_truths.add((fixture.case_id, best.object_id))
                true_positives += 1
                confusion[f"{best.class_id}->{prediction.class_id}"] += 1
            else:
                false_positives += 1
                confusion[f"background->{prediction.class_id}"] += 1

    for fixture in valid:
        for truth in fixture.truths:
            if (fixture.case_id, truth.object_id) not in matched_truths:
                confusion[f"{truth.class_id}->missed"] += 1
    false_negatives = truth_count - true_positives
    precision = _ratio(true_positives, true_positives + false_positives)
    recall = _ratio(true_positives, true_positives + false_negatives)
    class_ap = {
        class_id: _average_precision(
            [matched for _confidence, matched in sorted(values, reverse=True)],
            class_truths[class_id],
        )
        for class_id, values in sorted(ranked_by_class.items())
        if class_truths[class_id] > 0
    }
    for class_id in class_truths:
        class_ap.setdefault(class_id, 0.0)
    return DetectionMetricSummaryV1(
        truth_count=truth_count,
        prediction_count=prediction_count,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        invalid_case_count=invalid_count,
        precision=precision,
        recall=recall,
        f1=_f1(precision, recall),
        map50=sum(class_ap.values()) / len(class_ap) if class_ap else 0.0,
        per_class_ap50=dict(sorted(class_ap.items())),
        confusion=dict(sorted(confusion.items())),
    )


def evaluate_tracking(fixtures: list[TrackingFixtureV1]) -> TrackingMetricSummaryV1:
    truth_associations = 0
    predicted_associations = 0
    matches = 0
    identity_switches = 0
    fragments = 0
    epoch_resets = 0
    for fixture in fixtures:
        previous: dict[str, str] = {}
        previous_visible: dict[str, bool] = {}
        if fixture.expected_outcome == "reset":
            epoch_resets += 1
        for association in fixture.associations:
            truth = association.truth_track_id
            predicted = association.predicted_track_id
            truth_associations += truth is not None
            predicted_associations += predicted is not None
            if truth is not None and predicted is not None:
                matches += 1
                prior = previous.get(truth)
                if prior is not None and prior != predicted:
                    identity_switches += 1
                previous[truth] = predicted
                was_visible = previous_visible.get(truth)
                if was_visible is False and association.visible:
                    fragments += 1
                previous_visible[truth] = association.visible
    id_precision = _ratio(matches, predicted_associations)
    id_recall = _ratio(matches, truth_associations)
    return TrackingMetricSummaryV1(
        truth_associations=truth_associations,
        predicted_associations=predicted_associations,
        matched_associations=matches,
        id_precision=id_precision,
        id_recall=id_recall,
        idf1=_f1(id_precision, id_recall),
        identity_switches=identity_switches,
        fragments=fragments,
        epoch_reset_cases=epoch_resets,
    )


def evaluate_geometry(
    expected_by_case: dict[str, list[str]],
    predicted_by_case: dict[str, list[str]],
    *,
    onset_errors_ms: list[float],
    termination_errors_ms: list[float],
) -> GeometryMetricSummaryV1:
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    duplicates = 0
    expected_count = 0
    predicted_count = 0
    for case_id, expected_values in expected_by_case.items():
        expected = Counter(expected_values)
        predicted = Counter(predicted_by_case.get(case_id, []))
        expected_count += sum(expected.values())
        predicted_count += sum(predicted.values())
        true_positives += sum(min(count, predicted[event]) for event, count in expected.items())
        false_negatives += sum(max(0, count - predicted[event]) for event, count in expected.items())
        false_positives += sum(
            max(0, count - expected[event]) for event, count in predicted.items()
        )
        duplicates += sum(max(0, count - 1) for count in predicted.values())
    for case_id, predicted_values in predicted_by_case.items():
        if case_id not in expected_by_case:
            predicted_count += len(predicted_values)
            false_positives += len(predicted_values)
            duplicates += sum(max(0, count - 1) for count in Counter(predicted_values).values())
    precision = _ratio(true_positives, true_positives + false_positives)
    recall = _ratio(true_positives, true_positives + false_negatives)
    return GeometryMetricSummaryV1(
        expected_events=expected_count,
        predicted_events=predicted_count,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        duplicate_events=duplicates,
        precision=precision,
        recall=recall,
        duplicate_rate=_ratio(duplicates, predicted_count),
        onset_error_ms=(sum(onset_errors_ms) / len(onset_errors_ms) if onset_errors_ms else 0),
        termination_error_ms=(
            sum(termination_errors_ms) / len(termination_errors_ms)
            if termination_errors_ms
            else 0
        ),
    )


def _edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_character in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_character != right_character),
                )
            )
        previous = current
    return previous[-1]


def evaluate_synthetic_plates(
    fixtures: list[SyntheticPlateFixtureV1],
) -> PlateMetricSummaryV1:
    evaluated = [fixture for fixture in fixtures if fixture.valid_format]
    non_abstained = [fixture for fixture in evaluated if not fixture.abstained]
    exact = 0
    top_k = 0
    character_errors = 0
    character_count = 0
    scripts: Counter[str] = Counter()
    for fixture in evaluated:
        scripts[fixture.script] += 1
        character_count += len(fixture.truth_text)
        if fixture.abstained:
            character_errors += len(fixture.truth_text)
            continue
        texts = [alternative.text for alternative in fixture.alternatives]
        exact += bool(texts and texts[0] == fixture.truth_text)
        top_k += fixture.truth_text in texts
        character_errors += _edit_distance(fixture.truth_text, texts[0])
    return PlateMetricSummaryV1(
        evaluated_count=len(evaluated),
        abstention_count=len(evaluated) - len(non_abstained),
        exact_match_count=exact,
        top_k_match_count=top_k,
        character_errors=character_errors,
        character_count=character_count,
        exact_match_rate=_ratio(exact, len(non_abstained)),
        top_k_coverage=_ratio(top_k, len(non_abstained)),
        character_error_rate=_ratio(character_errors, character_count),
        script_counts=dict(sorted(scripts.items())),
    )


def build_golden_metric_report(
    detection: DetectionMetricSummaryV1,
    tracking: TrackingMetricSummaryV1,
    geometry: GeometryMetricSummaryV1,
    plates: PlateMetricSummaryV1,
) -> MetricReportV1:
    populations = [
        PopulationDefinitionV1(
            population_id="detection-generated",
            description="All valid generated detection cases",
            sample_count=detection.truth_count,
        ),
        PopulationDefinitionV1(
            population_id="tracking-generated",
            description="All generated tracking associations",
            sample_count=tracking.truth_associations,
        ),
        PopulationDefinitionV1(
            population_id="geometry-generated",
            description="All generated expected geometry events",
            sample_count=geometry.expected_events,
        ),
        PopulationDefinitionV1(
            population_id="synthetic-anpr-generated",
            description="Valid generated plate strings only",
            sample_count=plates.evaluated_count,
        ),
    ]
    metrics = [
        MetricValueV1(
            metric_name="detection.precision",
            domain="detection",
            population_id="detection-generated",
            value=detection.precision,
            unit="ratio",
            numerator=detection.true_positives,
            denominator=detection.true_positives + detection.false_positives,
            outcome="reported",
        ),
        MetricValueV1(
            metric_name="detection.recall",
            domain="detection",
            population_id="detection-generated",
            value=detection.recall,
            unit="ratio",
            numerator=detection.true_positives,
            denominator=detection.truth_count,
            outcome="reported",
        ),
        MetricValueV1(
            metric_name="detection.map50",
            domain="detection",
            population_id="detection-generated",
            value=detection.map50,
            unit="ratio",
            outcome="reported",
        ),
        MetricValueV1(
            metric_name="tracking.idf1",
            domain="tracking",
            population_id="tracking-generated",
            value=tracking.idf1,
            unit="ratio",
            outcome="reported",
        ),
        MetricValueV1(
            metric_name="tracking.identity_switches",
            domain="tracking",
            population_id="tracking-generated",
            value=float(tracking.identity_switches),
            unit="count",
            outcome="reported",
        ),
        MetricValueV1(
            metric_name="geometry.precision",
            domain="geometry",
            population_id="geometry-generated",
            value=geometry.precision,
            unit="ratio",
            numerator=geometry.true_positives,
            denominator=geometry.true_positives + geometry.false_positives,
            outcome="reported",
        ),
        MetricValueV1(
            metric_name="geometry.recall",
            domain="geometry",
            population_id="geometry-generated",
            value=geometry.recall,
            unit="ratio",
            numerator=geometry.true_positives,
            denominator=geometry.expected_events,
            outcome="reported",
        ),
        MetricValueV1(
            metric_name="synthetic_anpr.exact_match",
            domain="synthetic_anpr",
            population_id="synthetic-anpr-generated",
            value=plates.exact_match_rate,
            unit="ratio",
            numerator=plates.exact_match_count,
            denominator=plates.evaluated_count - plates.abstention_count,
            outcome="reported",
        ),
        MetricValueV1(
            metric_name="synthetic_anpr.character_error_rate",
            domain="synthetic_anpr",
            population_id="synthetic-anpr-generated",
            value=plates.character_error_rate,
            unit="ratio",
            numerator=plates.character_errors,
            denominator=plates.character_count,
            outcome="reported",
        ),
    ]
    proposals = [
        HardGateResultV1(
            gate_id="proposal-generated-detection-f1",
            metric_name="detection.f1",
            comparator="gte",
            threshold=0.5,
            observed=detection.f1,
            outcome="proposal_only",
            owner_approved=False,
        ),
        HardGateResultV1(
            gate_id="proposal-generated-tracking-idf1",
            metric_name="tracking.idf1",
            comparator="gte",
            threshold=0.9,
            observed=tracking.idf1,
            outcome="proposal_only",
            owner_approved=False,
        ),
    ]
    return seal_record(
        MetricReportV1,
        {
            "report_id": "p31-generated-golden-metrics-v1",
            "semantic_version": "1.0.0",
            "metric_suite_id": "p31-generated-metrics",
            "metric_suite_version": "1.0.0",
            "generated_at": datetime(2026, 8, 24, 12, 40, tzinfo=UTC),
            "populations": [value.model_dump(mode="json") for value in populations],
            "metrics": [value.model_dump(mode="json") for value in metrics],
            "invalid_prediction_handling": (
                "Reject malformed records and count them outside valid metric populations"
            ),
            "abstention_handling": (
                "Count abstentions explicitly and exclude them from exact-match denominator"
            ),
            "missing_prediction_handling": "Count unmatched truth records as false negatives",
            "baseline_report": None,
            "regressions": [],
            "hard_gates": [value.model_dump(mode="json") for value in proposals],
            "failed_gates": [],
            "approval": ApprovalRecordV1(
                record_id="D-P3.1-001",
                owner_id="mayank-admin",
                status="owner_recorded",
                decided_at=datetime(2026, 8, 24, 12, 0, tzinfo=UTC),
                reason="Record generated metric baseline without approving promotion gates",
            ).model_dump(mode="json"),
        },
    )
