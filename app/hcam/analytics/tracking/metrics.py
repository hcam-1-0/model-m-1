from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

from hcam.analytics.tracking.matching import pairwise_iou
from hcam.analytics.tracking.types import (
    GeneratedTrackingScenario,
    TIER_A_CLASSES,
    TrackerFrameResult,
    TrackingClassMetric,
    TrackingMetricResult,
)


# HOTA and identity calculations are adapted from TrackEval commit
# 12c8791b303e0a0b50f753af204249e622d0281a under the MIT License.
_ALPHAS = np.arange(0.05, 0.99, 0.05)


@dataclass(frozen=True, slots=True)
class _SequenceData:
    truth_ids: tuple[np.ndarray, ...]
    tracker_ids: tuple[np.ndarray, ...]
    similarities: tuple[np.ndarray, ...]
    truth_identity_count: int
    tracker_identity_count: int
    truth_detection_count: int
    tracker_detection_count: int


def _sequence_data(
    scenario: GeneratedTrackingScenario,
    results: tuple[TrackerFrameResult, ...],
    class_id: str,
) -> _SequenceData:
    truth_names = sorted(
        {
            item.truth_track_id
            for generated in scenario.frames
            for item in generated.ground_truth
            if item.class_id == class_id
        }
    )
    tracker_names = sorted(
        {
            item.track_id
            for result in results
            for item in result.visible_tracks
            if item.class_id == class_id
        }
    )
    truth_indexes = {name: index for index, name in enumerate(truth_names)}
    tracker_indexes = {name: index for index, name in enumerate(tracker_names)}
    truth_ids: list[np.ndarray] = []
    tracker_ids: list[np.ndarray] = []
    similarities: list[np.ndarray] = []
    truth_detection_count = 0
    tracker_detection_count = 0
    for generated, result in zip(scenario.frames, results, strict=True):
        truth = sorted(
            (item for item in generated.ground_truth if item.class_id == class_id),
            key=lambda item: item.truth_track_id,
        )
        predicted = sorted(
            (item for item in result.visible_tracks if item.class_id == class_id),
            key=lambda item: item.track_id,
        )
        truth_ids.append(
            np.asarray(
                [truth_indexes[item.truth_track_id] for item in truth],
                dtype=np.int64,
            )
        )
        tracker_ids.append(
            np.asarray(
                [tracker_indexes[item.track_id] for item in predicted],
                dtype=np.int64,
            )
        )
        similarities.append(
            pairwise_iou(
                [item.bbox for item in truth],
                [item.bbox for item in predicted],
            )
        )
        truth_detection_count += len(truth)
        tracker_detection_count += len(predicted)
    return _SequenceData(
        truth_ids=tuple(truth_ids),
        tracker_ids=tuple(tracker_ids),
        similarities=tuple(similarities),
        truth_identity_count=len(truth_names),
        tracker_identity_count=len(tracker_names),
        truth_detection_count=truth_detection_count,
        tracker_detection_count=tracker_detection_count,
    )


def _hota(data: _SequenceData) -> tuple[float, float, float, float]:
    true_positives = np.zeros(len(_ALPHAS), dtype=np.float64)
    false_negatives = np.zeros(len(_ALPHAS), dtype=np.float64)
    false_positives = np.zeros(len(_ALPHAS), dtype=np.float64)
    localization = np.zeros(len(_ALPHAS), dtype=np.float64)
    if data.tracker_detection_count == 0:
        false_negatives[:] = data.truth_detection_count
        return 0.0, 0.0, 0.0, 1.0
    if data.truth_detection_count == 0:
        false_positives[:] = data.tracker_detection_count
        return 0.0, 0.0, 0.0, 1.0

    potential = np.zeros(
        (data.truth_identity_count, data.tracker_identity_count),
        dtype=np.float64,
    )
    truth_counts = np.zeros((data.truth_identity_count, 1), dtype=np.float64)
    tracker_counts = np.zeros((1, data.tracker_identity_count), dtype=np.float64)
    for truth_ids, tracker_ids, similarity in zip(
        data.truth_ids,
        data.tracker_ids,
        data.similarities,
        strict=True,
    ):
        denominator = (
            similarity.sum(axis=0)[None, :]
            + similarity.sum(axis=1)[:, None]
            - similarity
        )
        normalized = np.zeros_like(similarity)
        mask = denominator > np.finfo(float).eps
        normalized[mask] = similarity[mask] / denominator[mask]
        potential[truth_ids[:, None], tracker_ids[None, :]] += normalized
        truth_counts[truth_ids] += 1
        tracker_counts[0, tracker_ids] += 1
    alignment = potential / np.maximum(
        np.finfo(float).eps,
        truth_counts + tracker_counts - potential,
    )
    match_counts = [np.zeros_like(potential) for _ in _ALPHAS]

    for truth_ids, tracker_ids, similarity in zip(
        data.truth_ids,
        data.tracker_ids,
        data.similarities,
        strict=True,
    ):
        if len(truth_ids) == 0:
            false_positives += len(tracker_ids)
            continue
        if len(tracker_ids) == 0:
            false_negatives += len(truth_ids)
            continue
        score = alignment[truth_ids[:, None], tracker_ids[None, :]] * similarity
        rows, columns = linear_sum_assignment(-score)
        for alpha_index, alpha in enumerate(_ALPHAS):
            mask = similarity[rows, columns] >= alpha - np.finfo(float).eps
            matched_rows = rows[mask]
            matched_columns = columns[mask]
            match_count = len(matched_rows)
            true_positives[alpha_index] += match_count
            false_negatives[alpha_index] += len(truth_ids) - match_count
            false_positives[alpha_index] += len(tracker_ids) - match_count
            if match_count:
                localization[alpha_index] += float(
                    similarity[matched_rows, matched_columns].sum()
                )
                match_counts[alpha_index][
                    truth_ids[matched_rows], tracker_ids[matched_columns]
                ] += 1

    association = np.zeros(len(_ALPHAS), dtype=np.float64)
    for alpha_index, counts in enumerate(match_counts):
        association_score = counts / np.maximum(
            1.0,
            truth_counts + tracker_counts - counts,
        )
        association[alpha_index] = float(
            np.sum(counts * association_score)
            / max(1.0, true_positives[alpha_index])
        )
    detection = true_positives / np.maximum(
        1.0,
        true_positives + false_negatives + false_positives,
    )
    hota = np.sqrt(detection * association)
    localization = np.maximum(1e-10, localization) / np.maximum(
        1e-10,
        true_positives,
    )
    return (
        float(np.mean(hota)),
        float(np.mean(detection)),
        float(np.mean(association)),
        float(np.mean(localization)),
    )


def _identity(
    data: _SequenceData,
) -> tuple[float, float, float, int, int, int]:
    if data.tracker_detection_count == 0:
        return 0.0, 0.0, 0.0, 0, 0, data.truth_detection_count
    if data.truth_detection_count == 0:
        return 0.0, 0.0, 0.0, 0, data.tracker_detection_count, 0
    potential = np.zeros(
        (data.truth_identity_count, data.tracker_identity_count),
        dtype=np.float64,
    )
    truth_counts = np.zeros(data.truth_identity_count, dtype=np.float64)
    tracker_counts = np.zeros(data.tracker_identity_count, dtype=np.float64)
    for truth_ids, tracker_ids, similarity in zip(
        data.truth_ids,
        data.tracker_ids,
        data.similarities,
        strict=True,
    ):
        truth_match, tracker_match = np.nonzero(similarity >= 0.5)
        potential[truth_ids[truth_match], tracker_ids[tracker_match]] += 1
        truth_counts[truth_ids] += 1
        tracker_counts[tracker_ids] += 1

    truth_count = data.truth_identity_count
    tracker_count = data.tracker_identity_count
    size = truth_count + tracker_count
    false_positive_matrix = np.zeros((size, size), dtype=np.float64)
    false_negative_matrix = np.zeros((size, size), dtype=np.float64)
    false_positive_matrix[truth_count:, :tracker_count] = 1e10
    false_negative_matrix[:truth_count, tracker_count:] = 1e10
    for truth_id in range(truth_count):
        false_negative_matrix[truth_id, :tracker_count] = truth_counts[truth_id]
        false_negative_matrix[truth_id, tracker_count + truth_id] = truth_counts[
            truth_id
        ]
    for tracker_id in range(tracker_count):
        false_positive_matrix[:truth_count, tracker_id] = tracker_counts[tracker_id]
        false_positive_matrix[truth_count + tracker_id, tracker_id] = tracker_counts[
            tracker_id
        ]
    false_negative_matrix[:truth_count, :tracker_count] -= potential
    false_positive_matrix[:truth_count, :tracker_count] -= potential
    rows, columns = linear_sum_assignment(
        false_negative_matrix + false_positive_matrix
    )
    false_negatives = int(false_negative_matrix[rows, columns].sum())
    false_positives = int(false_positive_matrix[rows, columns].sum())
    true_positives = int(truth_counts.sum()) - false_negatives
    recall = true_positives / max(1.0, true_positives + false_negatives)
    precision = true_positives / max(1.0, true_positives + false_positives)
    idf1 = true_positives / max(
        1.0,
        true_positives + 0.5 * false_positives + 0.5 * false_negatives,
    )
    return (
        float(idf1),
        float(precision),
        float(recall),
        true_positives,
        false_positives,
        false_negatives,
    )


def _identity_switches(data: _SequenceData) -> int:
    previous: dict[int, int] = {}
    switches = 0
    for truth_ids, tracker_ids, similarity in zip(
        data.truth_ids,
        data.tracker_ids,
        data.similarities,
        strict=True,
    ):
        if not len(truth_ids) or not len(tracker_ids):
            continue
        rows, columns = linear_sum_assignment(-similarity)
        for row, column in zip(rows, columns, strict=True):
            if similarity[row, column] < 0.5:
                continue
            truth_id = int(truth_ids[row])
            tracker_id = int(tracker_ids[column])
            if truth_id in previous and previous[truth_id] != tracker_id:
                switches += 1
            previous[truth_id] = tracker_id
    return switches


def _class_metric(data: _SequenceData) -> TrackingClassMetric:
    hota, detection, association, localization = _hota(data)
    idf1, precision, recall, true_positive, false_positive, false_negative = (
        _identity(data)
    )
    return TrackingClassMetric(
        hota=hota,
        detection_accuracy=detection,
        association_accuracy=association,
        localization_accuracy=localization,
        idf1=idf1,
        id_precision=precision,
        id_recall=recall,
        id_true_positives=true_positive,
        id_false_positives=false_positive,
        id_false_negatives=false_negative,
        identity_switches=_identity_switches(data),
    )


def evaluate_tracking_sequence(
    scenario: GeneratedTrackingScenario,
    results: tuple[TrackerFrameResult, ...],
) -> TrackingMetricResult:
    if len(scenario.frames) != len(results):
        raise ValueError("tracking results do not match generated sequence length")
    per_class = {
        class_id: _class_metric(_sequence_data(scenario, results, class_id))
        for class_id in TIER_A_CLASSES
        if any(
            item.class_id == class_id
            for generated in scenario.frames
            for item in generated.ground_truth
        )
        or any(
            item.class_id == class_id
            for result in results
            for item in result.visible_tracks
        )
    }
    if not per_class:
        return TrackingMetricResult(
            hota=0.0,
            detection_accuracy=0.0,
            association_accuracy=0.0,
            localization_accuracy=1.0,
            idf1=0.0,
            id_precision=0.0,
            id_recall=0.0,
            id_true_positives=0,
            id_false_positives=0,
            id_false_negatives=0,
            identity_switches=0,
            per_class={},
        )
    weight = sum(
        metric.id_true_positives
        + metric.id_false_positives
        + metric.id_false_negatives
        for metric in per_class.values()
    )

    def weighted(field: str) -> float:
        if weight == 0:
            return 0.0
        return sum(
            getattr(metric, field)
            * (
                metric.id_true_positives
                + metric.id_false_positives
                + metric.id_false_negatives
            )
            for metric in per_class.values()
        ) / weight

    true_positive = sum(item.id_true_positives for item in per_class.values())
    false_positive = sum(item.id_false_positives for item in per_class.values())
    false_negative = sum(item.id_false_negatives for item in per_class.values())
    return TrackingMetricResult(
        hota=weighted("hota"),
        detection_accuracy=weighted("detection_accuracy"),
        association_accuracy=weighted("association_accuracy"),
        localization_accuracy=weighted("localization_accuracy"),
        idf1=true_positive
        / max(1.0, true_positive + 0.5 * false_positive + 0.5 * false_negative),
        id_precision=true_positive / max(1.0, true_positive + false_positive),
        id_recall=true_positive / max(1.0, true_positive + false_negative),
        id_true_positives=true_positive,
        id_false_positives=false_positive,
        id_false_negatives=false_negative,
        identity_switches=sum(item.identity_switches for item in per_class.values()),
        per_class=per_class,
    )
