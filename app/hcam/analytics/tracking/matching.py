from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment


def pairwise_iou(
    first: list[tuple[float, float, float, float]],
    second: list[tuple[float, float, float, float]],
) -> np.ndarray:
    result = np.zeros((len(first), len(second)), dtype=np.float64)
    for row, (ax, ay, aw, ah) in enumerate(first):
        a_right = ax + aw
        a_bottom = ay + ah
        a_area = aw * ah
        for column, (bx, by, bw, bh) in enumerate(second):
            intersection_width = max(0.0, min(a_right, bx + bw) - max(ax, bx))
            intersection_height = max(0.0, min(a_bottom, by + bh) - max(ay, by))
            intersection = intersection_width * intersection_height
            union = a_area + bw * bh - intersection
            result[row, column] = intersection / union if union > 0 else 0.0
    return result


def iou_cost(
    first: list[tuple[float, float, float, float]],
    second: list[tuple[float, float, float, float]],
) -> np.ndarray:
    return 1.0 - pairwise_iou(first, second)


def fuse_detection_scores(cost: np.ndarray, scores: list[float]) -> np.ndarray:
    if cost.size == 0:
        return cost
    score_matrix = np.asarray(scores, dtype=np.float64)[None, :]
    return 1.0 - ((1.0 - cost) * score_matrix)


def bounded_linear_assignment(
    cost: np.ndarray,
    limit: float,
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    rows, columns = cost.shape
    if rows == 0 or columns == 0:
        return [], list(range(rows)), list(range(columns))
    finite_cost = np.where(np.isfinite(cost), cost, limit + 1.0)
    row_indices, column_indices = linear_sum_assignment(finite_cost)
    matches = sorted(
        (int(row), int(column))
        for row, column in zip(row_indices, column_indices, strict=True)
        if finite_cost[row, column] <= limit
    )
    matched_rows = {row for row, _ in matches}
    matched_columns = {column for _, column in matches}
    return (
        matches,
        [row for row in range(rows) if row not in matched_rows],
        [column for column in range(columns) if column not in matched_columns],
    )
