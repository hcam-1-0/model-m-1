from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from hcam.analytics.anpr.contracts import (
    MAX_ANPR_CONSENSUS_OBSERVATIONS,
    MAX_ANPR_CONSENSUS_STATES_PER_STREAM,
    MAX_ANPR_CONSENSUS_WINDOW_MS,
    ConsensusCloseReason,
    EphemeralConsensusObservationV1,
    EphemeralConsensusResultV1,
    EphemeralConsensusVoteV1,
    SyntheticConsensusPolicyV1,
)


ConsensusViolationCode = Literal[
    "duplicate_observation",
    "out_of_order_observation",
    "runtime_disabled",
]


class ConsensusViolation(ValueError):
    """Fail-closed consensus error that never includes identifiers or text."""

    def __init__(self, code: ConsensusViolationCode) -> None:
        super().__init__(f"P3.5 synthetic consensus rejected input: {code}")
        self.code = code


@dataclass(frozen=True, slots=True, order=True)
class _ConsensusKey:
    stream_id: str
    tracker_epoch: str
    track_id: str


@dataclass(slots=True)
class _ConsensusState:
    observations: list[EphemeralConsensusObservationV1] = field(default_factory=list)


@dataclass(slots=True)
class _VoteAccumulator:
    observation_count: int = 0
    confidence_weight: Decimal = Decimal(0)
    first_event_time_ms: int = 0
    first_source_sequence: int = 0


class BoundedSyntheticConsensus:
    """Generated-only, anonymous, stream-local temporal consensus state machine."""

    def __init__(self, policy: SyntheticConsensusPolicyV1 | None = None) -> None:
        self.policy = policy or SyntheticConsensusPolicyV1()
        self._states: dict[_ConsensusKey, _ConsensusState] = {}

    def active_state_count(self, stream_id: str | None = None) -> int:
        if stream_id is None:
            return len(self._states)
        return sum(key.stream_id == stream_id for key in self._states)

    def observe(
        self, observation: EphemeralConsensusObservationV1
    ) -> tuple[EphemeralConsensusResultV1, ...]:
        self._require_enabled()
        key = self._key(observation)
        state = self._states.get(key)
        if state is None:
            if (
                self.active_state_count(observation.stream_id)
                >= MAX_ANPR_CONSENSUS_STATES_PER_STREAM
            ):
                return (self._build_result((observation,), "overload"),)
            state = _ConsensusState()
            self._states[key] = state
        else:
            last = state.observations[-1]
            if observation.source_sequence == last.source_sequence:
                raise ConsensusViolation("duplicate_observation")
            if (
                observation.source_sequence < last.source_sequence
                or observation.event_time_ms < last.event_time_ms
            ):
                raise ConsensusViolation("out_of_order_observation")
            if (
                observation.event_time_ms - state.observations[0].event_time_ms
                >= MAX_ANPR_CONSENSUS_WINDOW_MS
            ):
                return (self._close(key, "event_time_window"),)

        state.observations.append(observation)
        if len(state.observations) == MAX_ANPR_CONSENSUS_OBSERVATIONS:
            return (self._close(key, "count_limit"),)
        return ()

    def expire(
        self, stream_id: str, *, at_event_time_ms: int
    ) -> tuple[EphemeralConsensusResultV1, ...]:
        self._require_enabled()
        if at_event_time_ms < 0:
            raise ValueError("consensus event time must be non-negative")
        keys = sorted(
            key
            for key, state in self._states.items()
            if key.stream_id == stream_id
            and at_event_time_ms - state.observations[0].event_time_ms
            >= MAX_ANPR_CONSENSUS_WINDOW_MS
        )
        return tuple(self._close(key, "event_time_window") for key in keys)

    def close_track(
        self,
        stream_id: str,
        tracker_epoch: str,
        track_id: str,
    ) -> tuple[EphemeralConsensusResultV1, ...]:
        self._require_enabled()
        key = _ConsensusKey(stream_id, tracker_epoch, track_id)
        if key not in self._states:
            return ()
        return (self._close(key, "track_end"),)

    def reset_epoch(
        self, stream_id: str, tracker_epoch: str
    ) -> tuple[EphemeralConsensusResultV1, ...]:
        self._require_enabled()
        keys = sorted(
            key
            for key in self._states
            if key.stream_id == stream_id and key.tracker_epoch == tracker_epoch
        )
        return tuple(self._close(key, "epoch_reset") for key in keys)

    def _require_enabled(self) -> None:
        if not self.policy.enabled:
            raise ConsensusViolation("runtime_disabled")

    @staticmethod
    def _key(observation: EphemeralConsensusObservationV1) -> _ConsensusKey:
        return _ConsensusKey(
            observation.stream_id,
            observation.tracker_epoch,
            observation.track_id,
        )

    def _close(
        self, key: _ConsensusKey, reason: ConsensusCloseReason
    ) -> EphemeralConsensusResultV1:
        state = self._states.pop(key)
        return self._build_result(tuple(state.observations), reason)

    def _build_result(
        self,
        observations: tuple[EphemeralConsensusObservationV1, ...],
        reason: ConsensusCloseReason,
    ) -> EphemeralConsensusResultV1:
        if not observations:
            raise ValueError("consensus cannot close an empty state")
        votes: dict[str, _VoteAccumulator] = {}
        for observation in observations:
            candidate = observation.normalization.normalized_display_candidate
            vote = votes.get(candidate)
            if vote is None:
                vote = _VoteAccumulator(
                    first_event_time_ms=observation.event_time_ms,
                    first_source_sequence=observation.source_sequence,
                )
                votes[candidate] = vote
            vote.observation_count += 1
            vote.confidence_weight += Decimal(
                str(observation.normalization.calibrated_confidence)
            )

        ranked = sorted(
            votes.items(),
            key=lambda item: (
                -item[1].confidence_weight,
                -item[1].observation_count,
                item[0],
            ),
        )
        ranked_votes = tuple(
            EphemeralConsensusVoteV1(
                normalized_display_candidate=candidate,
                observation_count=vote.observation_count,
                confidence_weight=float(vote.confidence_weight),
                first_event_time_ms=vote.first_event_time_ms,
                first_source_sequence=vote.first_source_sequence,
            )
            for candidate, vote in ranked
        )
        winner = ranked_votes[0]
        runner_up_weight = (
            Decimal(str(ranked_votes[1].confidence_weight))
            if len(ranked_votes) > 1
            else Decimal(0)
        )
        margin = Decimal(str(winner.confidence_weight)) - runner_up_weight
        first = observations[0]
        return EphemeralConsensusResultV1(
            stream_id=first.stream_id,
            tracker_epoch=first.tracker_epoch,
            track_id=first.track_id,
            close_reason=reason,
            first_event_time_ms=first.event_time_ms,
            last_event_time_ms=observations[-1].event_time_ms,
            observation_count=len(observations),
            unique_candidate_count=len(ranked_votes),
            ranked_votes=ranked_votes,
            winning_candidate=winner.normalized_display_candidate,
            winning_support=winner.observation_count,
            winning_confidence_weight=winner.confidence_weight,
            confidence_margin=float(margin),
            abstention_reason=(
                "overload_fail_closed"
                if reason == "overload"
                else "consensus_thresholds_unapproved"
            ),
        )
