from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from hcam.intelligence.rules.bounds import MAX_EVENTS_PER_WINDOW, RuleLimitError
from hcam.intelligence.rules.contracts import RuleScheduleV1


class TemporalEvaluationError(ValueError):
    """Raised when deterministic temporal truth cannot be established safely."""


@dataclass(frozen=True, slots=True)
class TemporalToken:
    input_id: str
    occurred_at: datetime
    stream_id: str

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise TemporalEvaluationError("temporal token must use an aware timestamp")


@dataclass(frozen=True, slots=True)
class TemporalResult:
    matched: bool
    pending: bool
    reason_code: str
    evidence: tuple[TemporalToken, ...] = ()
    suppressed_count: int = 0


def ordered_sequence(
    candidates: list[tuple[TemporalToken, ...]],
    *,
    maximum_span_ms: int,
) -> TemporalResult:
    if not candidates or any(not group for group in candidates):
        return TemporalResult(False, True, "sequence_pending")
    selected: list[TemporalToken] = []
    lower_bound: tuple[datetime, str] | None = None
    for group in candidates:
        ordered = sorted(group, key=lambda item: (item.occurred_at, item.input_id))
        token = next(
            (
                item
                for item in ordered
                if lower_bound is None
                or (item.occurred_at, item.input_id) > lower_bound
            ),
            None,
        )
        if token is None:
            return TemporalResult(False, True, "sequence_pending", tuple(selected))
        selected.append(token)
        lower_bound = (token.occurred_at, token.input_id)
    span_ms = int(
        (selected[-1].occurred_at - selected[0].occurred_at).total_seconds() * 1000
    )
    if span_ms > maximum_span_ms:
        return TemporalResult(False, False, "sequence_window_exceeded", tuple(selected))
    return TemporalResult(True, False, "sequence_matched", tuple(selected))


def within(tokens: tuple[TemporalToken, ...], *, duration_ms: int) -> TemporalResult:
    if not tokens:
        return TemporalResult(False, True, "within_pending")
    ordered = tuple(sorted(tokens, key=lambda item: (item.occurred_at, item.input_id)))
    span = (ordered[-1].occurred_at - ordered[0].occurred_at).total_seconds() * 1000
    return TemporalResult(
        span <= duration_ms,
        False,
        "within_matched" if span <= duration_ms else "within_expired",
        ordered,
    )


def until(
    candidate: tuple[TemporalToken, ...],
    stop: tuple[TemporalToken, ...],
    *,
    duration_ms: int,
) -> TemporalResult:
    if not candidate:
        return TemporalResult(False, True, "until_pending")
    first = min(candidate, key=lambda item: (item.occurred_at, item.input_id))
    deadline = first.occurred_at + timedelta(milliseconds=duration_ms)
    blockers = [
        item for item in stop if first.occurred_at <= item.occurred_at <= deadline
    ]
    if blockers:
        blocker = min(blockers, key=lambda item: (item.occurred_at, item.input_id))
        return TemporalResult(False, False, "until_stopped", (first, blocker))
    return TemporalResult(True, False, "until_matched", (first,))


def for_at_least(
    tokens: tuple[TemporalToken, ...], *, duration_ms: int
) -> TemporalResult:
    if not tokens:
        return TemporalResult(False, True, "duration_pending")
    ordered = tuple(sorted(tokens, key=lambda item: (item.occurred_at, item.input_id)))
    observed_ms = (
        ordered[-1].occurred_at - ordered[0].occurred_at
    ).total_seconds() * 1000
    return TemporalResult(
        observed_ms >= duration_ms,
        observed_ms < duration_ms,
        "duration_matched" if observed_ms >= duration_ms else "duration_pending",
        ordered,
    )


def absence(
    tokens: tuple[TemporalToken, ...],
    *,
    interval_start: datetime,
    watermark_at: datetime,
    duration_ms: int,
) -> TemporalResult:
    if interval_start.tzinfo is None or watermark_at.tzinfo is None:
        raise TemporalEvaluationError("absence timestamps must be aware")
    deadline = interval_start + timedelta(milliseconds=duration_ms)
    observed = tuple(
        item for item in tokens if interval_start <= item.occurred_at <= deadline
    )
    if observed:
        return TemporalResult(False, False, "absence_disproved", observed)
    if watermark_at < deadline:
        return TemporalResult(False, True, "absence_pending")
    return TemporalResult(True, False, "absence_watermark_closed")


def threshold_count(
    tokens: tuple[TemporalToken, ...], *, threshold: int
) -> TemporalResult:
    if len(tokens) > MAX_EVENTS_PER_WINDOW:
        raise RuleLimitError("temporal count exceeds the event window limit")
    matched = len(tokens) >= threshold
    return TemporalResult(
        matched,
        not matched,
        "count_matched" if matched else "count_pending",
        tokens,
    )


def threshold_rate(
    tokens: tuple[TemporalToken, ...], *, duration_ms: int, rate_per_minute: float
) -> TemporalResult:
    if len(tokens) > MAX_EVENTS_PER_WINDOW:
        raise RuleLimitError("temporal rate exceeds the event window limit")
    denominator_minutes = duration_ms / 60_000
    rate = len(tokens) / denominator_minutes
    matched = rate >= rate_per_minute
    return TemporalResult(
        matched,
        not matched,
        "rate_matched" if matched else "rate_pending",
        tokens,
    )


def distinct_stream_count(
    tokens: tuple[TemporalToken, ...], *, threshold: int
) -> TemporalResult:
    matched = len({item.stream_id for item in tokens}) >= threshold
    return TemporalResult(
        matched,
        not matched,
        "distinct_streams_matched" if matched else "distinct_streams_pending",
        tokens,
    )


def schedule_is_open(schedule: RuleScheduleV1, instant: datetime) -> bool:
    if instant.tzinfo is None:
        raise TemporalEvaluationError("schedule instant must be aware")
    try:
        zone = ZoneInfo(schedule.timezone)
    except ZoneInfoNotFoundError as exc:
        raise TemporalEvaluationError("schedule timezone is unavailable") from exc
    local = instant.astimezone(zone)
    minute = local.hour * 60 + local.minute
    return any(
        item.weekday == local.weekday()
        and item.start_minute <= minute < item.end_minute
        for item in schedule.intervals
    )


def apply_cooldown(
    result: TemporalResult,
    *,
    now: datetime,
    previous_match_at: datetime | None,
    duration_ms: int,
    prior_suppressed_count: int = 0,
) -> TemporalResult:
    if not result.matched:
        return result
    if previous_match_at is not None and now < previous_match_at + timedelta(
        milliseconds=duration_ms
    ):
        return TemporalResult(
            False,
            False,
            "cooldown_suppressed",
            result.evidence,
            prior_suppressed_count + 1,
        )
    return TemporalResult(True, False, "cooldown_open", result.evidence)


def apply_repeat_limit(
    result: TemporalResult, *, emitted_count: int, maximum: int
) -> TemporalResult:
    if not result.matched:
        return result
    if emitted_count >= maximum:
        return TemporalResult(
            False,
            False,
            "repeat_limit_exhausted",
            result.evidence,
            result.suppressed_count + 1,
        )
    return TemporalResult(True, False, "repeat_limit_open", result.evidence)


def utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise TemporalEvaluationError("timestamp must be aware")
    return value.astimezone(UTC)
