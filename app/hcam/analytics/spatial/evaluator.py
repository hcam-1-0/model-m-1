from __future__ import annotations

import hashlib
import heapq
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from shapely import LineString, Point
from shapely.geometry.base import BaseGeometry

from hcam.analytics.geometry import GeometryDefinitionV1
from hcam.analytics.spatial.cel_policy import (
    CheckedCelExpression,
    ConstrainedCelEnvironment,
)
from hcam.analytics.spatial.contracts import GeometryRuleV1, RuleGraphV1
from hcam.analytics.spatial.geometry_engine import (
    CanonicalGeometry,
    canonicalize_geometry,
    signed_line_distance,
    zone_regions,
)


MAX_RULES = 64
MAX_CANDIDATES = 16
MAX_TRACK_RULE_STATES = 16_384
MAX_REORDER_INPUTS = 64
ALLOWED_LATENESS = timedelta(seconds=2)


class EvaluatorBoundaryError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class LifecycleInput:
    lifecycle_id: str
    department: str
    assignment_id: str
    stream_id: str
    camera_id: str
    epoch_id: str
    track_id: str
    class_id: str
    state: Literal["started", "updated", "lost", "ended"]
    reason: str
    observed_at: datetime
    source_sequence: int
    latest_observation_id: str
    bbox: tuple[float, float, float, float]
    confidence: float
    lineage: dict[str, object]
    retention_class: str

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("lifecycle timestamp must be timezone-aware")
        if self.source_sequence < 0:
            raise ValueError("lifecycle sequence must be non-negative")
        if not 0 <= self.confidence <= 1:
            raise ValueError("lifecycle confidence must be normalized")
        x, y, width, height = self.bbox
        if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > 1 or y + height > 1:
            raise ValueError("lifecycle bounding box must be normalized")

    @property
    def digest(self) -> str:
        payload = json.dumps(
            {
                "bbox": self.bbox,
                "class_id": self.class_id,
                "confidence": self.confidence,
                "epoch_id": self.epoch_id,
                "lifecycle_id": self.lifecycle_id,
                "observed_at": self.observed_at.astimezone(UTC).isoformat(),
                "source_sequence": self.source_sequence,
                "state": self.state,
                "track_id": self.track_id,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class AnalyticPrimitiveEvent:
    event_id: str
    event_kind: str
    occurred_at: datetime
    department: str
    assignment_id: str
    stream_id: str
    camera_id: str
    epoch_id: str
    track_id: str | None
    lifecycle_id: str
    source_sequence: int
    rule_id: str
    rule_version: int
    rule_digest: str
    geometry_id: str
    geometry_version: int
    geometry_digest: str
    state_cycle_id: str
    direction: str | None
    count: int | None
    dwell_ms: int | None
    confidence: float
    lineage: dict[str, object]
    retention_class: str
    alert_state: Literal["not_evaluated"] = "not_evaluated"

    def document(self) -> dict[str, object]:
        return {
            "alert_state": self.alert_state,
            "assignment_id": self.assignment_id,
            "camera_id": self.camera_id,
            "confidence": self.confidence,
            "count": self.count,
            "department": self.department,
            "direction": self.direction,
            "dwell_ms": self.dwell_ms,
            "epoch_id": self.epoch_id,
            "event_id": self.event_id,
            "event_kind": self.event_kind,
            "geometry": {
                "digest": self.geometry_digest,
                "id": self.geometry_id,
                "version": self.geometry_version,
            },
            "lifecycle_id": self.lifecycle_id,
            "lineage": self.lineage,
            "occurred_at": self.occurred_at.astimezone(UTC).isoformat(),
            "retention_class": self.retention_class,
            "rule": {
                "digest": self.rule_digest,
                "id": self.rule_id,
                "version": self.rule_version,
            },
            "source_sequence": self.source_sequence,
            "state_cycle_id": self.state_cycle_id,
            "stream_id": self.stream_id,
            "track_id": self.track_id,
        }


@dataclass(frozen=True, slots=True)
class CompiledGeometryRule:
    definition: GeometryRuleV1
    geometry_definition: GeometryDefinitionV1
    geometry: CanonicalGeometry
    checked_cel: CheckedCelExpression
    inner_region: BaseGeometry | None = None
    outer_region: BaseGeometry | None = None

    @classmethod
    def build(
        cls,
        definition: GeometryRuleV1,
        geometry_definition: GeometryDefinitionV1,
        geometry: CanonicalGeometry,
        cel_environment: ConstrainedCelEnvironment,
    ) -> CompiledGeometryRule:
        if definition.geometry_id != geometry_definition.geometry_id:
            raise ValueError("rule geometry identifier does not match")
        if definition.geometry_version != geometry_definition.version:
            raise ValueError("rule geometry version does not match")
        if any(
            left != right
            for left, right in (
                (definition.department, geometry_definition.department),
                (definition.stream_id, geometry_definition.stream_id),
                (definition.camera_id, geometry_definition.camera_id),
            )
        ):
            raise ValueError("rule and geometry scopes do not match")
        expected_geometry = canonicalize_geometry(geometry_definition.shape)
        if (
            geometry.kind != expected_geometry.kind
            or geometry.digest != expected_geometry.digest
            or geometry.canonical_wkb != expected_geometry.canonical_wkb
        ):
            raise ValueError("canonical geometry does not match its definition")
        event_is_line = definition.event_kind == "hcam.analytics.line.crossing.v1"
        if event_is_line != (geometry.kind == "line"):
            raise ValueError("rule event kind does not match geometry kind")
        inner: BaseGeometry | None = None
        outer: BaseGeometry | None = None
        if geometry.kind == "zone":
            inner, outer = zone_regions(
                geometry.geometry,
                definition.zone_hysteresis or 0.0,
            )
        return cls(
            definition=definition,
            geometry_definition=geometry_definition,
            geometry=geometry,
            checked_cel=cel_environment.compile(definition.cel_condition),
            inner_region=inner,
            outer_region=outer,
        )


@dataclass(slots=True)
class _TrackRuleState:
    stable_side: int | None = None
    stable_anchor: tuple[float, float] | None = None
    armed: bool = True
    zone_state: Literal["unknown", "outside", "inside", "grace_lost"] = "unknown"
    entered_at: datetime | None = None
    lost_at: datetime | None = None
    dwell_emitted: bool = False
    cycle_id: str = ""
    graph_state: dict[str, object] = field(default_factory=dict)


class BoundedEventBuffer:
    def __init__(self) -> None:
        self._items: list[tuple[int, datetime, str, LifecycleInput]] = []
        self._seen: dict[int, str] = {}
        self._maximum_observed_at: datetime | None = None
        self._committed_watermark: datetime | None = None

    @property
    def depth(self) -> int:
        return len(self._items)

    def push(self, item: LifecycleInput) -> Literal["accepted", "duplicate", "late"]:
        known = self._seen.get(item.source_sequence)
        if known is not None:
            if known == item.digest:
                return "duplicate"
            raise EvaluatorBoundaryError("sequence_conflict")
        if self._committed_watermark is not None and item.observed_at <= self._committed_watermark:
            return "late"
        if len(self._items) >= MAX_REORDER_INPUTS:
            raise EvaluatorBoundaryError("reorder_buffer_overflow")
        self._seen[item.source_sequence] = item.digest
        self._maximum_observed_at = max(
            item.observed_at,
            self._maximum_observed_at or item.observed_at,
        )
        heapq.heappush(
            self._items,
            (item.source_sequence, item.observed_at, item.lifecycle_id, item),
        )
        return "accepted"

    def pop_ready(self) -> tuple[LifecycleInput, ...]:
        if self._maximum_observed_at is None:
            return ()
        watermark = self._maximum_observed_at - ALLOWED_LATENESS
        ready = [entry for entry in self._items if entry[1] <= watermark]
        if not ready:
            return ()
        ready_set = {(entry[0], entry[2]) for entry in ready}
        self._items = [
            entry for entry in self._items if (entry[0], entry[2]) not in ready_set
        ]
        heapq.heapify(self._items)
        self._committed_watermark = max(
            watermark,
            self._committed_watermark or watermark,
        )
        return tuple(entry[3] for entry in sorted(ready))

    def drain(self) -> tuple[LifecycleInput, ...]:
        ready = tuple(entry[3] for entry in sorted(self._items))
        self._items.clear()
        if ready:
            final_time = max(item.observed_at for item in ready)
            self._committed_watermark = max(
                final_time,
                self._committed_watermark or final_time,
            )
        return ready


class GeometryEventEvaluator:
    def __init__(
        self,
        rules: tuple[CompiledGeometryRule, ...],
        *,
        cel_environment: ConstrainedCelEnvironment | None = None,
    ) -> None:
        if not 1 <= len(rules) <= MAX_RULES:
            raise ValueError("evaluator requires between one and 64 rules")
        scopes = {
            (
                item.definition.department,
                item.definition.assignment_id,
                item.definition.stream_id,
                item.definition.camera_id,
            )
            for item in rules
        }
        if len(scopes) != 1:
            raise ValueError("evaluator rules must share one local scope")
        self.rules = tuple(sorted(rules, key=lambda item: (item.definition.rule_id, item.definition.version)))
        self.cel_environment = cel_environment or ConstrainedCelEnvironment()
        self._states: dict[tuple[str, int, str], _TrackRuleState] = {}
        self._occupancy_members: dict[tuple[str, int], set[str]] = {}
        self._occupancy_above: dict[tuple[str, int], bool] = {}

    @property
    def state_count(self) -> int:
        return len(self._states)

    def state_snapshots(self) -> tuple[dict[str, object], ...]:
        snapshots: list[dict[str, object]] = []
        for (rule_id, rule_version, track_id), state in sorted(self._states.items()):
            snapshots.append(
                {
                    "armed": state.armed,
                    "cycle_id": state.cycle_id,
                    "dwell_emitted": state.dwell_emitted,
                    "entered_at": (
                        state.entered_at.astimezone(UTC).isoformat()
                        if state.entered_at is not None
                        else None
                    ),
                    "graph_state": _json_state(state.graph_state),
                    "lost_at": (
                        state.lost_at.astimezone(UTC).isoformat()
                        if state.lost_at is not None
                        else None
                    ),
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "stable_anchor": state.stable_anchor,
                    "stable_side": state.stable_side,
                    "track_id": track_id,
                    "zone_state": state.zone_state,
                }
            )
        return tuple(snapshots)

    def evaluate(self, sample: LifecycleInput) -> tuple[AnalyticPrimitiveEvent, ...]:
        scope = (
            sample.department,
            sample.assignment_id,
            sample.stream_id,
            sample.camera_id,
        )
        expected = next(iter({
            (
                rule.definition.department,
                rule.definition.assignment_id,
                rule.definition.stream_id,
                rule.definition.camera_id,
            )
            for rule in self.rules
        }))
        if scope != expected:
            raise EvaluatorBoundaryError("scope_mismatch")
        candidates = [
            rule for rule in self.rules if sample.class_id in rule.definition.class_filter
        ]
        if len(candidates) > MAX_CANDIDATES:
            raise EvaluatorBoundaryError("candidate_limit")
        events: list[AnalyticPrimitiveEvent] = []
        for rule in candidates:
            if not self._is_effective(rule, sample.observed_at):
                self._clear_track(rule, sample.track_id)
                continue
            key = (rule.definition.rule_id, rule.definition.version, sample.track_id)
            state = self._states.get(key)
            if state is None:
                if len(self._states) >= MAX_TRACK_RULE_STATES:
                    raise EvaluatorBoundaryError("state_limit")
                state = _TrackRuleState()
                self._states[key] = state
            if sample.state in {"lost", "ended"}:
                events.extend(self._handle_non_visible(rule, sample, state))
                if sample.state == "ended":
                    self._states.pop(key, None)
                continue
            anchor = self._anchor(rule.definition.anchor_policy, sample.bbox)
            if rule.geometry.kind == "line":
                event = self._line(rule, sample, state, anchor)
                if event is not None:
                    events.append(event)
            else:
                events.extend(self._zone(rule, sample, state, anchor))
        return tuple(events)

    def _is_effective(self, rule: CompiledGeometryRule, occurred_at: datetime) -> bool:
        definition = rule.definition
        if definition.status != "approved" or occurred_at < definition.effective_from:
            return False
        if definition.effective_until is not None and occurred_at >= definition.effective_until:
            return False
        schedule = rule.geometry_definition.schedule
        if schedule.mode == "always":
            return True
        try:
            local = occurred_at.astimezone(ZoneInfo(schedule.timezone))
        except ZoneInfoNotFoundError as exc:
            raise EvaluatorBoundaryError("timezone_unavailable") from exc
        day = local.strftime("%A").lower()
        minute = local.hour * 60 + local.minute
        return any(
            day in window.days and window.start_minute <= minute < window.end_minute
            for window in schedule.windows
        )

    @staticmethod
    def _anchor(policy: str, bbox: tuple[float, float, float, float]) -> tuple[float, float]:
        x, y, width, height = bbox
        return (
            x + width / 2,
            y + height if policy == "bottom_center" else y + height / 2,
        )

    def _line(
        self,
        rule: CompiledGeometryRule,
        sample: LifecycleInput,
        state: _TrackRuleState,
        anchor: tuple[float, float],
    ) -> AnalyticPrimitiveEvent | None:
        distance = signed_line_distance(rule.geometry.geometry, anchor)
        deadband = rule.definition.deadband or 0.0
        epsilon = 1e-12
        side = (
            1
            if distance > deadband + epsilon
            else -1
            if distance < -deadband - epsilon
            else 0
        )
        if side == 0:
            return None
        if state.stable_side is None:
            state.stable_side = side
            state.stable_anchor = anchor
            return None
        if not state.armed and abs(distance) >= (rule.definition.rearm_distance or deadband):
            state.armed = True
        previous_side = state.stable_side
        previous_anchor = state.stable_anchor
        state.stable_side = side
        state.stable_anchor = anchor
        if previous_side == side or previous_anchor is None or not state.armed:
            return None
        movement = LineString([previous_anchor, anchor])
        if not movement.crosses(rule.geometry.geometry):
            return None
        direction = "a_to_b" if previous_side > side else "b_to_a"
        if rule.definition.line_direction not in {"both", direction}:
            return None
        state.armed = False
        state.cycle_id = _stable_id(
            "cycle",
            sample.epoch_id,
            sample.track_id,
            rule.definition.rule_id,
            rule.definition.version,
            sample.source_sequence,
        )
        signals = _signals(line_crossing=True)
        if not self._gate(rule, state, sample, signals, direction=direction, count=0):
            return None
        return self._event(
            rule,
            sample,
            state.cycle_id,
            direction=direction,
            count=None,
            dwell_ms=None,
        )

    def _zone(
        self,
        rule: CompiledGeometryRule,
        sample: LifecycleInput,
        state: _TrackRuleState,
        anchor: tuple[float, float],
    ) -> list[AnalyticPrimitiveEvent]:
        assert rule.inner_region is not None and rule.outer_region is not None
        point = Point(anchor)
        inclusive = rule.definition.boundary_policy == "inside_inclusive"
        inner_inside = (
            rule.inner_region.covers(point) if inclusive else rule.inner_region.contains(point)
        )
        outer_inside = (
            rule.outer_region.covers(point) if inclusive else rule.outer_region.contains(point)
        )
        now = sample.observed_at
        events: list[AnalyticPrimitiveEvent] = []
        entered = False
        exited = False
        recovered = state.zone_state == "grace_lost"
        if recovered:
            grace = timedelta(milliseconds=rule.definition.occlusion_grace_ms)
            if state.lost_at is None or now - state.lost_at > grace or not outer_inside:
                state.zone_state = "outside"
                state.entered_at = None
                state.dwell_emitted = False
                state.cycle_id = ""
            else:
                state.zone_state = "inside"
            state.lost_at = None
        if state.zone_state == "unknown":
            state.zone_state = "inside" if inner_inside else "outside"
            if inner_inside:
                state.entered_at = now
                state.cycle_id = _stable_id(
                    "cycle", sample.epoch_id, sample.track_id, rule.definition.rule_id,
                    rule.definition.version, sample.source_sequence,
                )
        elif state.zone_state == "outside" and inner_inside:
            state.zone_state = "inside"
            state.entered_at = now
            state.dwell_emitted = False
            state.cycle_id = _stable_id(
                "cycle", sample.epoch_id, sample.track_id, rule.definition.rule_id,
                rule.definition.version, sample.source_sequence,
            )
            entered = True
        elif state.zone_state == "inside" and not outer_inside:
            state.zone_state = "outside"
            exited = True

        occupancy_key = (rule.definition.rule_id, rule.definition.version)
        members = self._occupancy_members.setdefault(occupancy_key, set())
        before_count = len(members)
        if state.zone_state == "inside":
            members.add(sample.track_id)
        else:
            members.discard(sample.track_id)
        count = len(members)
        event_kind = rule.definition.event_kind
        signals = _signals(
            zone_entry=entered,
            zone_exit=exited,
            zone_presence=state.zone_state == "inside",
        )
        if event_kind == "hcam.analytics.zone.entry.v1" and entered:
            if self._gate(rule, state, sample, signals, direction="", count=count):
                events.append(self._event(rule, sample, state.cycle_id, count=count))
        elif event_kind == "hcam.analytics.zone.exit.v1" and exited:
            if self._gate(rule, state, sample, signals, direction="", count=count):
                events.append(self._event(rule, sample, state.cycle_id, count=count))
        elif event_kind == "hcam.analytics.zone.dwell.threshold_met.v1":
            threshold = rule.definition.dwell_threshold_ms or 0
            dwell_ms = (
                int((now - state.entered_at).total_seconds() * 1000)
                if state.zone_state == "inside" and state.entered_at is not None
                else 0
            )
            if dwell_ms >= threshold and not state.dwell_emitted:
                state.dwell_emitted = True
                signals["zone_dwell_threshold"] = True
                if self._gate(rule, state, sample, signals, direction="", count=count):
                    events.append(
                        self._event(
                            rule,
                            sample,
                            state.cycle_id,
                            count=count,
                            dwell_ms=dwell_ms,
                        )
                    )
        elif event_kind.startswith("hcam.analytics.zone.occupancy.") and before_count != count:
            above = self._occupancy_above.get(occupancy_key, False)
            enter_threshold = rule.definition.occupancy_enter_threshold or 1
            reset_threshold = rule.definition.occupancy_reset_threshold or 0
            trigger = False
            if not above and count >= enter_threshold:
                self._occupancy_above[occupancy_key] = True
                signals["zone_occupancy_entered"] = True
                trigger = event_kind.endswith("threshold_entered.v1")
            elif above and count <= reset_threshold:
                self._occupancy_above[occupancy_key] = False
                signals["zone_occupancy_exited"] = True
                trigger = event_kind.endswith("threshold_exited.v1")
            if trigger and self._gate(rule, state, sample, signals, direction="", count=count):
                events.append(
                    self._event(
                        rule,
                        sample,
                        _stable_id("aggregate", sample.epoch_id, rule.definition.rule_id),
                        track_id=None,
                        count=count,
                    )
                )
        if exited:
            state.entered_at = None
            state.dwell_emitted = False
            state.cycle_id = ""
        return events

    def _handle_non_visible(
        self,
        rule: CompiledGeometryRule,
        sample: LifecycleInput,
        state: _TrackRuleState,
    ) -> list[AnalyticPrimitiveEvent]:
        occupancy_key = (rule.definition.rule_id, rule.definition.version)
        members = self._occupancy_members.setdefault(occupancy_key, set())
        before = len(members)
        members.discard(sample.track_id)
        state.zone_state = "grace_lost" if sample.state == "lost" and state.zone_state == "inside" else "outside"
        state.lost_at = sample.observed_at if state.zone_state == "grace_lost" else None
        if sample.state == "ended":
            state.entered_at = None
            state.dwell_emitted = False
        if not rule.definition.event_kind.startswith("hcam.analytics.zone.occupancy."):
            return []
        count = len(members)
        if before == count:
            return []
        above = self._occupancy_above.get(occupancy_key, False)
        reset = rule.definition.occupancy_reset_threshold or 0
        if above and count <= reset:
            self._occupancy_above[occupancy_key] = False
            signals = _signals(zone_occupancy_exited=True)
            if rule.definition.event_kind.endswith("threshold_exited.v1") and self._gate(
                rule, state, sample, signals, direction="", count=count
            ):
                return [
                    self._event(
                        rule,
                        sample,
                        _stable_id("aggregate", sample.epoch_id, rule.definition.rule_id),
                        track_id=None,
                        count=count,
                    )
                ]
        return []

    def _gate(
        self,
        rule: CompiledGeometryRule,
        state: _TrackRuleState,
        sample: LifecycleInput,
        signals: dict[str, bool],
        *,
        direction: str,
        count: int,
    ) -> bool:
        graph_result = _evaluate_graph(rule.definition.graph, state.graph_state, signals, sample.observed_at)
        if not graph_result:
            return False
        context: dict[str, object] = {
            "class_id": sample.class_id,
            "confidence": float(sample.confidence),
            "direction": direction,
            "scheduled": True,
            "count": int(count),
            **signals,
        }
        return self.cel_environment.evaluate(rule.checked_cel, context)

    def _event(
        self,
        rule: CompiledGeometryRule,
        sample: LifecycleInput,
        cycle_id: str,
        *,
        track_id: str | None | object = ...,
        direction: str | None = None,
        count: int | None = None,
        dwell_ms: int | None = None,
    ) -> AnalyticPrimitiveEvent:
        resolved_track_id = sample.track_id if track_id is ... else track_id
        event_id = _stable_id(
            "evt",
            sample.department,
            sample.assignment_id,
            sample.stream_id,
            sample.epoch_id,
            rule.definition.rule_id,
            rule.definition.version,
            rule.definition.event_kind,
            cycle_id,
            sample.source_sequence,
        )
        return AnalyticPrimitiveEvent(
            event_id=event_id,
            event_kind=rule.definition.event_kind,
            occurred_at=sample.observed_at,
            department=sample.department,
            assignment_id=sample.assignment_id,
            stream_id=sample.stream_id,
            camera_id=sample.camera_id,
            epoch_id=sample.epoch_id,
            track_id=resolved_track_id,
            lifecycle_id=sample.lifecycle_id,
            source_sequence=sample.source_sequence,
            rule_id=rule.definition.rule_id,
            rule_version=rule.definition.version,
            rule_digest=rule.definition.configuration_digest,
            geometry_id=rule.geometry_definition.geometry_id,
            geometry_version=rule.geometry_definition.version,
            geometry_digest=rule.geometry.digest,
            state_cycle_id=cycle_id,
            direction=direction,
            count=count,
            dwell_ms=dwell_ms,
            confidence=sample.confidence,
            lineage=sample.lineage,
            retention_class=sample.retention_class,
        )

    def _clear_track(self, rule: CompiledGeometryRule, track_id: str) -> None:
        self._states.pop((rule.definition.rule_id, rule.definition.version, track_id), None)
        self._occupancy_members.setdefault(
            (rule.definition.rule_id, rule.definition.version), set()
        ).discard(track_id)


def _stable_id(prefix: str, *parts: object) -> str:
    payload = "\x00".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(payload).hexdigest()[:32]}"


def _signals(**overrides: bool) -> dict[str, bool]:
    values = {
        "line_crossing": False,
        "zone_entry": False,
        "zone_exit": False,
        "zone_presence": False,
        "zone_dwell_threshold": False,
        "zone_occupancy_entered": False,
        "zone_occupancy_exited": False,
    }
    values.update(overrides)
    return values


def _evaluate_graph(
    graph: RuleGraphV1,
    state: dict[str, object],
    signals: dict[str, bool],
    now: datetime,
) -> bool:
    values: dict[str, bool] = {}
    for node in graph.nodes:
        inputs = [values[item] for item in node.inputs]
        value = False
        if node.kind == "spatial":
            value = bool(signals[node.signal or "zone_presence"])
        elif node.kind == "all":
            value = all(inputs)
        elif node.kind == "any":
            value = any(inputs)
        elif node.kind == "not":
            value = not inputs[0]
        elif node.kind == "within":
            last = state.get(node.node_id)
            if inputs[0]:
                state[node.node_id] = now
                value = True
            elif isinstance(last, datetime):
                value = now - last <= timedelta(milliseconds=node.duration_ms or 0)
        elif node.kind == "for_at_least":
            since = state.get(node.node_id)
            if inputs[0]:
                if not isinstance(since, datetime):
                    since = now
                    state[node.node_id] = since
                value = now - since >= timedelta(milliseconds=node.duration_ms or 0)
            else:
                state.pop(node.node_id, None)
        elif node.kind == "cooldown":
            last = state.get(node.node_id)
            ready = not isinstance(last, datetime) or now - last >= timedelta(
                milliseconds=node.duration_ms or 0
            )
            value = inputs[0] and ready
            if value:
                state[node.node_id] = now
        elif node.kind == "repeat_limit":
            count = int(state.get(node.node_id, 0))
            value = inputs[0] and count < (node.repeat_limit or 1)
            if value:
                state[node.node_id] = count + 1
        elif node.kind == "sequence":
            sequence_state = state.get(node.node_id)
            if not isinstance(sequence_state, tuple):
                sequence_state = (0, now)
            index, started = sequence_state
            if now - started > timedelta(milliseconds=node.duration_ms or 0):
                index, started = 0, now
            if inputs[index]:
                index += 1
            if index >= len(inputs):
                value = True
                index, started = 0, now
            state[node.node_id] = (index, started)
        values[node.node_id] = value
    return values[graph.output_node_id]


def _json_state(value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_state(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_state(item) for key, item in value.items()}
    return value
