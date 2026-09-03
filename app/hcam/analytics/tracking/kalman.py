from __future__ import annotations

import numpy as np
import scipy.linalg


# Adapted from FoundationVision/ByteTrack at commit
# d1bf0191adff59bc8fcfeaa0b33d3d1642552a99 under the MIT License.
class BoundingBoxKalmanFilter:
    def __init__(self) -> None:
        dimensions = 4
        self._motion = np.eye(2 * dimensions, dtype=np.float64)
        for index in range(dimensions):
            self._motion[index, dimensions + index] = 1.0
        self._projection = np.eye(dimensions, 2 * dimensions, dtype=np.float64)
        self._position_weight = 1.0 / 20.0
        self._velocity_weight = 1.0 / 160.0

    def initiate(self, measurement: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mean = np.r_[measurement, np.zeros_like(measurement)]
        height = max(float(measurement[3]), 1e-6)
        deviation = np.asarray(
            [
                2 * self._position_weight * height,
                2 * self._position_weight * height,
                1e-2,
                2 * self._position_weight * height,
                10 * self._velocity_weight * height,
                10 * self._velocity_weight * height,
                1e-5,
                10 * self._velocity_weight * height,
            ],
            dtype=np.float64,
        )
        return mean, np.diag(np.square(deviation))

    def predict(
        self,
        mean: np.ndarray,
        covariance: np.ndarray,
        *,
        tracked: bool,
    ) -> tuple[np.ndarray, np.ndarray]:
        predicted_mean = mean.copy()
        if not tracked:
            predicted_mean[7] = 0.0
        height = max(float(predicted_mean[3]), 1e-6)
        position = np.asarray(
            [
                self._position_weight * height,
                self._position_weight * height,
                1e-2,
                self._position_weight * height,
            ]
        )
        velocity = np.asarray(
            [
                self._velocity_weight * height,
                self._velocity_weight * height,
                1e-5,
                self._velocity_weight * height,
            ]
        )
        motion_covariance = np.diag(np.square(np.r_[position, velocity]))
        predicted_mean = predicted_mean @ self._motion.T
        predicted_covariance = (
            self._motion @ covariance @ self._motion.T + motion_covariance
        )
        return predicted_mean, predicted_covariance

    def project(
        self,
        mean: np.ndarray,
        covariance: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        height = max(float(mean[3]), 1e-6)
        deviation = np.asarray(
            [
                self._position_weight * height,
                self._position_weight * height,
                1e-1,
                self._position_weight * height,
            ]
        )
        innovation = np.diag(np.square(deviation))
        return (
            self._projection @ mean,
            self._projection @ covariance @ self._projection.T + innovation,
        )

    def update(
        self,
        mean: np.ndarray,
        covariance: np.ndarray,
        measurement: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        projected_mean, projected_covariance = self.project(mean, covariance)
        factor, lower = scipy.linalg.cho_factor(
            projected_covariance,
            lower=True,
            check_finite=False,
        )
        gain = scipy.linalg.cho_solve(
            (factor, lower),
            (covariance @ self._projection.T).T,
            check_finite=False,
        ).T
        innovation = measurement - projected_mean
        updated_mean = mean + innovation @ gain.T
        updated_covariance = covariance - gain @ projected_covariance @ gain.T
        return updated_mean, updated_covariance
