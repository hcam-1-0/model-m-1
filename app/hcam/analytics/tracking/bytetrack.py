from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np

from hcam.analytics.tracking.kalman import BoundingBoxKalmanFilter
from hcam.analytics.tracking.matching import (
    bounded_linear_assignment,
    fuse_detection_scores,
    iou_cost,
)
from hcam.analytics.tracking.types import (
    ClosedEpoch,
    TIER_A_CLASSES,
    TrackTransition,
    TrackerConfiguration,
    TrackerFrameResult,
    TrackingDetection,
    TrackingFrame,
    TrackingResourceError,
    TransitionReason,
    TrackState,
    VisibleTrack,
)


# The association flow is adapted from FoundationVision/ByteTrack commit
# d1bf0191adff59bc8fcfeaa0b33d3d1642552a99 under the MIT License. H-CAM
# removes detector, image, appearance, ReID, Torch, OpenCV, and global-ID paths.
class _State(Enum):
    TENTATIVE = "tentative"
    TRACKED = "tracked"
    LOST = "lost"
    REMOVED = "removed"


def _xywh_to_xyah(box: tuple[float, float, float, float]) -> np.ndarray:
    x, y, width, height = box
    return np.asarray(
        [x + width / 2.0, y + height / 2.0, width / height, height],
        dtype=np.float64,
    )


def _xyah_to_xywh(value: np.ndarray) -> tuple[float, float, float, float]:
    center_x, center_y, aspect, height = (float(item) for item in value[:4])
    width = max(1e-9, aspect * height)
    height = max(1e-9, height)
    x = max(0.0, min(1.0 - 1e-9, center_x - width / 2.0))
    y = max(0.0, min(1.0 - 1e-9, center_y - height / 2.0))
    return (x, y, min(1.0 - x, width), min(1.0 - y, height))


@dataclass(slots=True)
class _Track:
    local_number: int
    class_id: str
    mean: np.ndarray
    covariance: np.ndarray
    state: _State
    confidence: float
    latest_observation_id: str
    first_sequence: int
    first_observed_at: datetime
    last_sequence: int
    last_visible_at: datetime
    age_frames: int = 1
    visible_frames: int = 1
    missed_frames: int = 0
    confirmations: int = 1

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return _xyah_to_xywh(self.mean)

    def predict(self, kalman: BoundingBoxKalmanFilter) -> None:
        self.mean, self.covariance = kalman.predict(
            self.mean,
            self.covariance,
            tracked=self.state is _State.TRACKED,
        )
        self.age_frames += 1
        self.missed_frames += 1

    def update(
        self,
        kalman: BoundingBoxKalmanFilter,
        detection: TrackingDetection,
        sequence: int,
        observed_at: datetime,
    ) -> _State:
        previous = self.state
        self.mean, self.covariance = kalman.update(
            self.mean,
            self.covariance,
            _xywh_to_xyah(detection.bbox),
        )
        self.state = _State.TRACKED
        self.confidence = detection.confidence
        self.latest_observation_id = detection.observation_id
        self.last_sequence = sequence
        self.last_visible_at = observed_at
        self.visible_frames += 1
        self.missed_frames = 0
        self.confirmations += 1
        return previous


@dataclass(frozen=True, slots=True)
class _LocalTransition:
    track: _Track
    state: TrackState
    reason: TransitionReason


class _ClassByteTracker:
    def __init__(
        self,
        class_id: str,
        configuration: TrackerConfiguration,
        next_number,
    ) -> None:
        self.class_id = class_id
        self.configuration = configuration
        self._next_number = next_number
        self._kalman = BoundingBoxKalmanFilter()
        self._tracks: dict[int, _Track] = {}

    @property
    def live_tracks(self) -> tuple[_Track, ...]:
        return tuple(
            sorted(
                (
                    track
                    for track in self._tracks.values()
                    if track.state in {_State.TRACKED, _State.LOST}
                    and track.confirmations >= self.configuration.minimum_confirmations
                ),
                key=lambda item: item.local_number,
            )
        )

    @property
    def visible_tracks(self) -> tuple[_Track, ...]:
        return tuple(
            track for track in self.live_tracks if track.state is _State.TRACKED
        )

    def update(
        self,
        detections: tuple[TrackingDetection, ...],
        sequence: int,
        observed_at: datetime,
    ) -> list[_LocalTransition]:
        transitions: list[_LocalTransition] = []
        ordered = sorted(detections, key=lambda item: item.observation_id)
        high = [
            item
            for item in ordered
            if item.confidence >= self.configuration.high_confidence_threshold
        ]
        low = [
            item
            for item in ordered
            if self.configuration.low_confidence_floor
            <= item.confidence
            < self.configuration.high_confidence_threshold
        ]

        confirmed = sorted(
            (
                track
                for track in self._tracks.values()
                if track.state in {_State.TRACKED, _State.LOST}
                and track.confirmations >= self.configuration.minimum_confirmations
            ),
            key=lambda item: item.local_number,
        )
        tentative = sorted(
            (
                track
                for track in self._tracks.values()
                if track.state is _State.TENTATIVE
            ),
            key=lambda item: item.local_number,
        )
        for track in confirmed + tentative:
            track.predict(self._kalman)

        first_cost = iou_cost(
            [track.bbox for track in confirmed],
            [item.bbox for item in high],
        )
        first_cost = fuse_detection_scores(
            first_cost,
            [item.confidence for item in high],
        )
        first_matches, unmatched_confirmed, unmatched_high = (
            bounded_linear_assignment(
                first_cost,
                self.configuration.first_match_cost_limit,
            )
        )
        for track_index, detection_index in first_matches:
            track = confirmed[track_index]
            previous = track.update(
                self._kalman,
                high[detection_index],
                sequence,
                observed_at,
            )
            transitions.append(
                _LocalTransition(
                    track,
                    "updated",
                    "recovered" if previous is _State.LOST else "matched",
                )
            )

        second_pool = [
            confirmed[index]
            for index in unmatched_confirmed
            if confirmed[index].state is _State.TRACKED
        ]
        second_cost = iou_cost(
            [track.bbox for track in second_pool],
            [item.bbox for item in low],
        )
        second_matches, unmatched_second, _ = bounded_linear_assignment(
            second_cost,
            self.configuration.second_match_cost_limit,
        )
        for track_index, detection_index in second_matches:
            track = second_pool[track_index]
            track.update(
                self._kalman,
                low[detection_index],
                sequence,
                observed_at,
            )
            transitions.append(_LocalTransition(track, "updated", "matched"))
        for track_index in unmatched_second:
            track = second_pool[track_index]
            track.state = _State.LOST
            transitions.append(
                _LocalTransition(track, "lost", "temporarily_unmatched")
            )

        unmatched_lost = [
            confirmed[index]
            for index in unmatched_confirmed
            if confirmed[index].state is _State.LOST
        ]
        for track in unmatched_lost:
            if sequence - track.last_sequence > self.configuration.maximum_lost_frames:
                track.state = _State.REMOVED
                transitions.append(_LocalTransition(track, "ended", "lost_timeout"))

        remaining_high = [high[index] for index in unmatched_high]
        tentative_cost = iou_cost(
            [track.bbox for track in tentative],
            [item.bbox for item in remaining_high],
        )
        tentative_cost = fuse_detection_scores(
            tentative_cost,
            [item.confidence for item in remaining_high],
        )
        tentative_matches, unmatched_tentative, unmatched_remaining = (
            bounded_linear_assignment(
                tentative_cost,
                self.configuration.tentative_match_cost_limit,
            )
        )
        for track_index, detection_index in tentative_matches:
            track = tentative[track_index]
            track.update(
                self._kalman,
                remaining_high[detection_index],
                sequence,
                observed_at,
            )
            if track.confirmations >= self.configuration.minimum_confirmations:
                transitions.append(_LocalTransition(track, "started", "confirmed"))
        for track_index in unmatched_tentative:
            tentative[track_index].state = _State.REMOVED

        new_threshold = min(
            1.0,
            self.configuration.high_confidence_threshold
            + self.configuration.new_track_margin,
        )
        for detection_index in unmatched_remaining:
            detection = remaining_high[detection_index]
            if detection.confidence < new_threshold:
                continue
            if self._state_count() >= self.configuration.maximum_tracks_per_class:
                raise TrackingResourceError("tracker state limit exceeded")
            number = self._next_number()
            mean, covariance = self._kalman.initiate(_xywh_to_xyah(detection.bbox))
            state = (
                _State.TRACKED
                if self.configuration.minimum_confirmations == 1
                else _State.TENTATIVE
            )
            track = _Track(
                local_number=number,
                class_id=self.class_id,
                mean=mean,
                covariance=covariance,
                state=state,
                confidence=detection.confidence,
                latest_observation_id=detection.observation_id,
                first_sequence=sequence,
                first_observed_at=observed_at,
                last_sequence=sequence,
                last_visible_at=observed_at,
            )
            self._tracks[number] = track
            if state is _State.TRACKED:
                transitions.append(_LocalTransition(track, "started", "confirmed"))

        self._remove_terminal_state()
        return transitions

    def close(self, reason: TransitionReason) -> list[_LocalTransition]:
        transitions: list[_LocalTransition] = []
        for track in self.live_tracks:
            track.state = _State.REMOVED
            transitions.append(_LocalTransition(track, "ended", reason))
        self._remove_terminal_state()
        return transitions

    def _state_count(self) -> int:
        return sum(
            track.state is not _State.REMOVED for track in self._tracks.values()
        )

    def _remove_terminal_state(self) -> None:
        self._tracks = {
            number: track
            for number, track in self._tracks.items()
            if track.state is not _State.REMOVED
        }


class StreamLocalTracker:
    def __init__(
        self,
        *,
        department: str,
        assignment_id: str,
        camera_id: str,
        stream_id: str,
        configuration: TrackerConfiguration,
        execution_id: str | None = None,
    ) -> None:
        self.department = department
        self.assignment_id = assignment_id
        self.camera_id = camera_id
        self.stream_id = stream_id
        self.configuration = configuration
        self.execution_id = execution_id or assignment_id
        self._epoch_index = 0
        self._epoch_id: str | None = None
        self._epoch_started_at: datetime | None = None
        self._last_sequence: int | None = None
        self._last_observed_at: datetime | None = None
        self._last_digest: str | None = None
        self._counter = 0
        self._trackers: dict[str, _ClassByteTracker] = {}

    def update(self, frame: TrackingFrame) -> TrackerFrameResult:
        if len(frame.detections) > self.configuration.maximum_detections_per_frame:
            raise TrackingResourceError("tracking frame exceeds detection limit")
        closed: list[ClosedEpoch] = []
        transitions: list[TrackTransition] = []
        if frame.reset_before is not None and self._epoch_id is not None:
            ended, closure = self._close_epoch(
                frame.reset_before,
                frame.observed_at,
                frame.sequence,
            )
            transitions.extend(ended)
            closed.append(closure)

        if self._last_sequence is not None:
            if frame.sequence == self._last_sequence and frame.digest == self._last_digest:
                return TrackerFrameResult(
                    epoch_id=self._require_epoch_id(),
                    epoch_started=False,
                    replayed=True,
                    transitions=(),
                    visible_tracks=self._visible_tracks(),
                    closed_epochs=(),
                )
            reason: TransitionReason | None = None
            if frame.sequence <= self._last_sequence:
                reason = "sequence_regression"
            elif self._last_observed_at is not None and frame.observed_at <= self._last_observed_at:
                reason = "timestamp_regression"
            elif self._last_observed_at is not None:
                gap_ms = (frame.observed_at - self._last_observed_at).total_seconds() * 1000
                if gap_ms > self.configuration.maximum_gap_ms:
                    reason = "sequence_gap"
            if reason is not None and self._epoch_id is not None:
                ended, closure = self._close_epoch(
                    reason,
                    frame.observed_at,
                    frame.sequence,
                )
                transitions.extend(ended)
                closed.append(closure)

        epoch_started = self._epoch_id is None
        if epoch_started:
            self._start_epoch(frame)
        grouped = {class_id: [] for class_id in TIER_A_CLASSES}
        for detection in frame.detections:
            grouped[detection.class_id].append(detection)
        for class_id in TIER_A_CLASSES:
            local = self._trackers[class_id].update(
                tuple(grouped[class_id]),
                frame.sequence,
                frame.observed_at,
            )
            transitions.extend(
                self._to_transition(item, frame.observed_at, frame.sequence)
                for item in local
            )
        self._last_sequence = frame.sequence
        self._last_observed_at = frame.observed_at
        self._last_digest = frame.digest
        return TrackerFrameResult(
            epoch_id=self._require_epoch_id(),
            epoch_started=epoch_started,
            replayed=False,
            transitions=tuple(transitions),
            visible_tracks=self._visible_tracks(),
            closed_epochs=tuple(closed),
        )

    def close(
        self,
        reason: TransitionReason,
        observed_at: datetime,
        sequence: int,
    ) -> TrackerFrameResult | None:
        if self._epoch_id is None:
            return None
        transitions, closure = self._close_epoch(reason, observed_at, sequence)
        return TrackerFrameResult(
            epoch_id=closure.epoch_id,
            epoch_started=False,
            replayed=False,
            transitions=tuple(transitions),
            visible_tracks=(),
            closed_epochs=(closure,),
        )

    def _start_epoch(self, frame: TrackingFrame) -> None:
        self._epoch_index += 1
        material = "\x00".join(
            (
                self.department,
                self.assignment_id,
                self.camera_id,
                self.stream_id,
                self.execution_id,
                self.configuration.digest,
                str(self._epoch_index),
                str(frame.sequence),
                frame.observed_at.isoformat(),
            )
        ).encode("utf-8")
        self._epoch_id = f"epoch_{hashlib.sha256(material).hexdigest()[:32]}"
        self._epoch_started_at = frame.observed_at
        self._last_sequence = None
        self._last_observed_at = None
        self._last_digest = None
        self._counter = 0
        self._trackers = {
            class_id: _ClassByteTracker(
                class_id,
                self.configuration,
                self._next_track_number,
            )
            for class_id in TIER_A_CLASSES
        }

    def _close_epoch(
        self,
        reason: TransitionReason,
        observed_at: datetime,
        sequence: int,
    ) -> tuple[list[TrackTransition], ClosedEpoch]:
        epoch_id = self._require_epoch_id()
        transitions = [
            self._to_transition(item, observed_at, sequence)
            for class_id in TIER_A_CLASSES
            for item in self._trackers[class_id].close(reason)
        ]
        closure = ClosedEpoch(
            epoch_id=epoch_id,
            reason=reason,
            ended_at=observed_at,
            end_sequence=sequence,
        )
        self._epoch_id = None
        self._epoch_started_at = None
        self._trackers = {}
        self._last_sequence = None
        self._last_observed_at = None
        self._last_digest = None
        return transitions, closure

    def _to_transition(
        self,
        item: _LocalTransition,
        observed_at: datetime,
        sequence: int,
    ) -> TrackTransition:
        epoch_id = self._require_epoch_id()
        track_id = self._track_id(epoch_id, item.track.local_number)
        return TrackTransition(
            epoch_id=epoch_id,
            track_id=track_id,
            local_track_number=item.track.local_number,
            class_id=item.track.class_id,
            state=item.state,
            reason=item.reason,
            first_observed_at=item.track.first_observed_at,
            first_sequence=item.track.first_sequence,
            observed_at=observed_at,
            source_sequence=sequence,
            last_visible_at=item.track.last_visible_at,
            last_visible_sequence=item.track.last_sequence,
            latest_observation_id=item.track.latest_observation_id,
            bbox=item.track.bbox,
            confidence=item.track.confidence,
            age_frames=item.track.age_frames,
            visible_frames=item.track.visible_frames,
            missed_frames=item.track.missed_frames,
        )

    def _visible_tracks(self) -> tuple[VisibleTrack, ...]:
        if self._epoch_id is None:
            return ()
        epoch_id = self._epoch_id
        return tuple(
            VisibleTrack(
                epoch_id=epoch_id,
                track_id=self._track_id(epoch_id, track.local_number),
                class_id=track.class_id,
                bbox=track.bbox,
                confidence=track.confidence,
            )
            for class_id in TIER_A_CLASSES
            for track in self._trackers[class_id].visible_tracks
        )

    def _next_track_number(self) -> int:
        self._counter += 1
        return self._counter

    @staticmethod
    def _track_id(epoch_id: str, local_number: int) -> str:
        material = f"{epoch_id}\x00{local_number}".encode("utf-8")
        return f"trk_{hashlib.sha256(material).hexdigest()[:32]}"

    def _require_epoch_id(self) -> str:
        if self._epoch_id is None:
            raise RuntimeError("tracker epoch is not active")
        return self._epoch_id
