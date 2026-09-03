from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import HealthCheck, settings
from hypothesis.stateful import (
    RuleBasedStateMachine,
    initialize,
    invariant,
    rule,
    run_state_machine_as_test,
)

from hcam.analytics.geometry import (
    GeometryDefinitionV1,
    GeometryScheduleV1,
    LineGeometryV1,
    NormalizedPoint,
    WeeklyWindowV1,
    ZoneGeometryV1,
)
from hcam.analytics.spatial import (
    BoundedEventBuffer,
    CompiledGeometryRule,
    ConstrainedCelEnvironment,
    GeometryEventEvaluator,
    GeometryRuleV1,
    LifecycleInput,
    RuleGraphV1,
    RuleNodeV1,
    canonicalize_geometry,
)
from hcam.analytics.spatial import evaluator as evaluator_module
from hcam.analytics.spatial.evaluator import (
    EvaluatorBoundaryError,
    _evaluate_graph,
    _json_state,
)
from hcam.analytics.spatial.generated import build_generated_lifecycle_scenario


NOW = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
ASSIGNMENT_ID = "ana_" + "2" * 32
STREAM_ID = "str_" + "1" * 32
CAMERA_ID = "synthetic:cam-c10"
TRACK_ID = "trk_" + "3" * 32


def _line_shape() -> LineGeometryV1:
    return LineGeometryV1(
        start=NormalizedPoint(x=0.5, y=0.1),
        end=NormalizedPoint(x=0.5, y=0.9),
    )


def _zone_shape() -> ZoneGeometryV1:
    return ZoneGeometryV1(
        vertices=[
            NormalizedPoint(x=0.2, y=0.2),
            NormalizedPoint(x=0.8, y=0.2),
            NormalizedPoint(x=0.8, y=0.8),
            NormalizedPoint(x=0.2, y=0.8),
        ]
    )


def _geometry(
    shape: LineGeometryV1 | ZoneGeometryV1,
    *,
    geometry_id: str = "c10-geometry",
    department: str = "traffic",
    stream_id: str = STREAM_ID,
    camera_id: str = CAMERA_ID,
    schedule: GeometryScheduleV1 | None = None,
) -> GeometryDefinitionV1:
    return GeometryDefinitionV1(
        geometry_id=geometry_id,
        version=1,
        department=department,
        stream_id=stream_id,
        camera_id=camera_id,
        status="approved",
        shape=shape,
        schedule=schedule or GeometryScheduleV1(),
        intended_use="Generated-only P3.4 C10 validation",
        policy_version=DIGEST_A,
        owner_id="mayank-admin",
        approval_record_id="D-P3.4-START",
        created_at=NOW,
        updated_at=NOW,
    )


def _graph(signal: str) -> RuleGraphV1:
    return RuleGraphV1(
        nodes=[RuleNodeV1(node_id="primitive", kind="spatial", signal=signal)],
        output_node_id="primitive",
    )


def _rule(
    geometry: GeometryDefinitionV1,
    *,
    rule_id: str = "c10-rule",
    event_kind: str = "hcam.analytics.zone.entry.v1",
    signal: str = "zone_entry",
    **overrides: object,
) -> GeometryRuleV1:
    values: dict[str, object] = {
        "rule_id": rule_id,
        "version": 1,
        "status": "approved",
        "department": geometry.department,
        "assignment_id": ASSIGNMENT_ID,
        "stream_id": geometry.stream_id,
        "camera_id": geometry.camera_id,
        "geometry_id": geometry.geometry_id,
        "geometry_version": geometry.version,
        "event_kind": event_kind,
        "class_filter": ["vehicle.car"],
        "cel_condition": "true",
        "graph": _graph(signal),
        "configuration_digest": DIGEST_B,
        "retention_class": "derived.analytics.standard",
        "owner_id": "mayank-admin",
        "approval_record_id": "D-P3.4-START",
        "effective_from": NOW - timedelta(days=7),
        "created_at": NOW,
        "updated_at": NOW,
    }
    if event_kind == "hcam.analytics.line.crossing.v1":
        values.update(
            line_direction="both",
            deadband=0.01,
            rearm_distance=0.04,
        )
    else:
        values["zone_hysteresis"] = 0.01
    values.update(overrides)
    return GeometryRuleV1.model_validate(values)


def _compiled(
    geometry: GeometryDefinitionV1,
    definition: GeometryRuleV1,
) -> CompiledGeometryRule:
    cel = ConstrainedCelEnvironment()
    return CompiledGeometryRule.build(
        definition,
        geometry,
        canonicalize_geometry(geometry.shape),
        cel,
    )


def _sample(
    sequence: int,
    x: float,
    y: float = 0.5,
    *,
    track_id: str = TRACK_ID,
    state: str = "updated",
    observed_at: datetime | None = None,
    department: str = "traffic",
    assignment_id: str = ASSIGNMENT_ID,
    stream_id: str = STREAM_ID,
    camera_id: str = CAMERA_ID,
    class_id: str = "vehicle.car",
) -> LifecycleInput:
    return LifecycleInput(
        lifecycle_id=f"lfc_{sequence:032x}",
        department=department,
        assignment_id=assignment_id,
        stream_id=stream_id,
        camera_id=camera_id,
        epoch_id="epoch_" + "4" * 32,
        track_id=track_id,
        class_id=class_id,
        state=state,
        reason="generated_transition",
        observed_at=observed_at or NOW + timedelta(seconds=sequence),
        source_sequence=sequence,
        latest_observation_id=f"obs_{sequence:032x}",
        bbox=(x - 0.01, y - 0.02, 0.02, 0.02),
        confidence=0.9,
        lineage={"execution_scope": "generated_only"},
        retention_class="derived.analytics.standard",
    )


@pytest.mark.parametrize(
    "changes,match",
    [
        ({"observed_at": NOW.replace(tzinfo=None)}, "timezone-aware"),
        ({"source_sequence": -1}, "non-negative"),
        ({"confidence": 1.1}, "normalized"),
        ({"bbox": (0.0, 0.0, 0.0, 0.2)}, "bounding box"),
        ({"bbox": (0.9, 0.9, 0.2, 0.2)}, "bounding box"),
    ],
)
def test_c10_lifecycle_input_rejects_invalid_values(
    changes: dict[str, object], match: str
) -> None:
    valid = _sample(1, 0.5)
    with pytest.raises(ValueError, match=match):
        replace(valid, **changes)


def test_c10_compile_rejects_geometry_identity_scope_and_kind_drift() -> None:
    line = _geometry(_line_shape(), geometry_id="c10-line")
    line_rule = _rule(
        line,
        event_kind="hcam.analytics.line.crossing.v1",
        signal="line_crossing",
    )
    cel = ConstrainedCelEnvironment()
    canonical = canonicalize_geometry(line.shape)
    cases = (
        (line_rule.model_copy(update={"geometry_id": "other"}), line, "identifier"),
        (line_rule.model_copy(update={"geometry_version": 2}), line, "version"),
        (
            line_rule.model_copy(update={"department": "other"}),
            line,
            "scopes",
        ),
        (
            line_rule,
            _geometry(_zone_shape(), geometry_id="c10-line"),
            "canonical geometry",
        ),
    )
    for definition, geometry, message in cases:
        with pytest.raises(ValueError, match=message):
            CompiledGeometryRule.build(definition, geometry, canonical, cel)


def test_c10_buffer_empty_late_overflow_and_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buffer = BoundedEventBuffer()
    assert buffer.pop_ready() == ()
    assert buffer.drain() == ()
    first = _sample(1, 0.2, observed_at=NOW)
    future = _sample(2, 0.3, observed_at=NOW + timedelta(seconds=4))
    assert buffer.push(first) == "accepted"
    assert buffer.push(future) == "accepted"
    assert [item.source_sequence for item in buffer.pop_ready()] == [1]
    assert buffer.push(_sample(0, 0.1, observed_at=NOW)) == "late"
    conflict = replace(first, lifecycle_id="lfc_" + "f" * 32, confidence=0.8)
    with pytest.raises(EvaluatorBoundaryError, match="sequence_conflict"):
        buffer.push(conflict)

    monkeypatch.setattr(evaluator_module, "MAX_REORDER_INPUTS", 2)
    full = BoundedEventBuffer()
    full.push(_sample(10, 0.2))
    full.push(_sample(11, 0.2))
    with pytest.raises(EvaluatorBoundaryError, match="reorder_buffer_overflow"):
        full.push(_sample(12, 0.2))


def test_c10_evaluator_enforces_rule_scope_candidate_and_state_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="between one and 64"):
        GeometryEventEvaluator(())

    zone = _geometry(_zone_shape())
    first = _compiled(zone, _rule(zone, rule_id="first"))
    other_definition = _rule(zone, rule_id="other").model_copy(
        update={"assignment_id": "ana_" + "9" * 32}
    )
    other = _compiled(zone, other_definition)
    with pytest.raises(ValueError, match="one local scope"):
        GeometryEventEvaluator((first, other))

    evaluator = GeometryEventEvaluator((first,))
    with pytest.raises(EvaluatorBoundaryError, match="scope_mismatch"):
        evaluator.evaluate(_sample(1, 0.1, department="other"))

    second = _compiled(zone, _rule(zone, rule_id="second"))
    monkeypatch.setattr(evaluator_module, "MAX_CANDIDATES", 1)
    with pytest.raises(EvaluatorBoundaryError, match="candidate_limit"):
        GeometryEventEvaluator((first, second)).evaluate(_sample(2, 0.1))

    monkeypatch.setattr(evaluator_module, "MAX_CANDIDATES", 16)
    monkeypatch.setattr(evaluator_module, "MAX_TRACK_RULE_STATES", 1)
    limited = GeometryEventEvaluator((first,))
    limited.evaluate(_sample(3, 0.1, track_id="trk_" + "1" * 32))
    with pytest.raises(EvaluatorBoundaryError, match="state_limit"):
        limited.evaluate(_sample(4, 0.1, track_id="trk_" + "2" * 32))


def test_c10_schedule_closes_state_and_handles_time_windows() -> None:
    schedule = GeometryScheduleV1(
        mode="weekly",
        timezone="Asia/Kolkata",
        windows=[
            WeeklyWindowV1(
                days=["monday"],
                start_minute=600,
                end_minute=660,
            )
        ],
    )
    zone = _geometry(_zone_shape(), schedule=schedule)
    definition = _rule(
        zone,
        effective_from=datetime(2026, 8, 1, tzinfo=UTC),
        effective_until=datetime(2026, 9, 1, tzinfo=UTC),
    )
    compiled = _compiled(zone, definition)
    evaluator = GeometryEventEvaluator((compiled,))
    monday_open = datetime(2026, 8, 24, 5, 0, tzinfo=UTC)
    monday_closed = datetime(2026, 8, 24, 6, 0, tzinfo=UTC)
    assert evaluator._is_effective(compiled, monday_open) is True
    evaluator.evaluate(_sample(1, 0.1, observed_at=monday_open))
    assert evaluator.state_count == 1
    assert evaluator._is_effective(compiled, monday_closed) is False
    evaluator.evaluate(_sample(2, 0.5, observed_at=monday_closed))
    assert evaluator.state_count == 0
    assert evaluator._is_effective(compiled, datetime(2026, 9, 1, tzinfo=UTC)) is False
    draft = _compiled(zone, definition.model_copy(update={"status": "draft"}))
    assert evaluator._is_effective(draft, monday_open) is False


def test_c10_line_direction_endpoint_deadband_and_cel_gate() -> None:
    line = _geometry(_line_shape(), geometry_id="c10-line")
    a_to_b_only = _compiled(
        line,
        _rule(
            line,
            event_kind="hcam.analytics.line.crossing.v1",
            signal="line_crossing",
            line_direction="a_to_b",
        ),
    )
    evaluator = GeometryEventEvaluator((a_to_b_only,))
    evaluator.evaluate(_sample(1, 0.7))
    assert evaluator.evaluate(_sample(2, 0.3)) == ()

    endpoint = GeometryEventEvaluator((a_to_b_only,))
    endpoint.evaluate(_sample(3, 0.3, y=0.1))
    assert endpoint.evaluate(_sample(4, 0.5, y=0.1)) == ()

    gated = _compiled(
        line,
        _rule(
            line,
            rule_id="gated-line",
            event_kind="hcam.analytics.line.crossing.v1",
            signal="line_crossing",
            cel_condition="confidence > 0.95",
        ),
    )
    gated_evaluator = GeometryEventEvaluator((gated,))
    gated_evaluator.evaluate(_sample(5, 0.3))
    assert gated_evaluator.evaluate(_sample(6, 0.7)) == ()

    deadband = GeometryEventEvaluator((a_to_b_only,))
    assert deadband.evaluate(_sample(7, 0.5)) == ()


def test_c10_zone_exit_occlusion_recovery_expiry_and_boundary_policy() -> None:
    zone = _geometry(_zone_shape())
    exit_rule = _compiled(
        zone,
        _rule(
            zone,
            event_kind="hcam.analytics.zone.exit.v1",
            signal="zone_exit",
        ),
    )
    evaluator = GeometryEventEvaluator((exit_rule,))
    evaluator.evaluate(_sample(1, 0.5, observed_at=NOW))
    event = evaluator.evaluate(
        _sample(2, 0.9, observed_at=NOW + timedelta(seconds=1))
    )[0]
    assert event.event_kind == "hcam.analytics.zone.exit.v1"
    assert event.document()["alert_state"] == "not_evaluated"

    dwell = _compiled(
        zone,
        _rule(
            zone,
            rule_id="dwell-grace",
            event_kind="hcam.analytics.zone.dwell.threshold_met.v1",
            signal="zone_dwell_threshold",
            dwell_threshold_ms=2_000,
            occlusion_grace_ms=1_500,
        ),
    )
    recovered = GeometryEventEvaluator((dwell,))
    recovered.evaluate(_sample(10, 0.5, observed_at=NOW))
    recovered.evaluate(
        _sample(11, 0.5, state="lost", observed_at=NOW + timedelta(seconds=1))
    )
    resumed = recovered.evaluate(
        _sample(12, 0.5, observed_at=NOW + timedelta(seconds=2))
    )
    assert resumed[0].dwell_ms == 2_000

    expired = GeometryEventEvaluator((dwell,))
    expired.evaluate(_sample(20, 0.5, observed_at=NOW))
    expired.evaluate(
        _sample(21, 0.5, state="lost", observed_at=NOW + timedelta(seconds=1))
    )
    assert expired.evaluate(
        _sample(22, 0.5, observed_at=NOW + timedelta(seconds=3))
    ) == ()

    exclusive = _compiled(
        zone,
        _rule(zone, rule_id="exclusive", boundary_policy="inside_exclusive"),
    )
    exclusive_evaluator = GeometryEventEvaluator((exclusive,))
    exclusive_evaluator.evaluate(_sample(30, 0.1))
    assert exclusive_evaluator.evaluate(_sample(31, 0.19)) == ()


def test_c10_occupancy_enter_exit_and_track_end_are_aggregate() -> None:
    zone = _geometry(_zone_shape())
    entered = _compiled(
        zone,
        _rule(
            zone,
            rule_id="occupancy-enter",
            event_kind="hcam.analytics.zone.occupancy.threshold_entered.v1",
            signal="zone_occupancy_entered",
            occupancy_enter_threshold=2,
            occupancy_reset_threshold=0,
        ),
    )
    exited = _compiled(
        zone,
        _rule(
            zone,
            rule_id="occupancy-exit",
            event_kind="hcam.analytics.zone.occupancy.threshold_exited.v1",
            signal="zone_occupancy_exited",
            occupancy_enter_threshold=2,
            occupancy_reset_threshold=0,
        ),
    )
    evaluator = GeometryEventEvaluator((entered, exited))
    track_a = "trk_" + "a" * 32
    track_b = "trk_" + "b" * 32
    evaluator.evaluate(_sample(1, 0.5, track_id=track_a))
    events = evaluator.evaluate(_sample(2, 0.6, track_id=track_b))
    assert [(item.track_id, item.count) for item in events] == [(None, 2)]
    assert evaluator.evaluate(_sample(3, 0.6, track_id=track_b, state="ended")) == ()
    events = evaluator.evaluate(_sample(4, 0.5, track_id=track_a, state="ended"))
    assert [(item.track_id, item.count) for item in events] == [(None, 0)]
    assert evaluator.state_count == 0


def test_c10_typed_rule_graph_nodes_are_bounded_and_deterministic() -> None:
    graph = RuleGraphV1(
        nodes=[
            RuleNodeV1(node_id="entry", kind="spatial", signal="zone_entry"),
            RuleNodeV1(node_id="present", kind="spatial", signal="zone_presence"),
            RuleNodeV1(node_id="both", kind="all", inputs=["entry", "present"]),
            RuleNodeV1(node_id="either", kind="any", inputs=["entry", "present"]),
            RuleNodeV1(node_id="negated", kind="not", inputs=["entry"]),
            RuleNodeV1(
                node_id="within", kind="within", inputs=["entry"], duration_ms=1_000
            ),
            RuleNodeV1(
                node_id="held",
                kind="for_at_least",
                inputs=["present"],
                duration_ms=1_000,
            ),
            RuleNodeV1(
                node_id="cooldown",
                kind="cooldown",
                inputs=["entry"],
                duration_ms=1_000,
            ),
            RuleNodeV1(
                node_id="limited",
                kind="repeat_limit",
                inputs=["entry"],
                repeat_limit=1,
            ),
            RuleNodeV1(
                node_id="ordered",
                kind="sequence",
                inputs=["entry", "present"],
                duration_ms=2_000,
            ),
        ],
        output_node_id="ordered",
    )
    state: dict[str, object] = {}
    first = evaluator_module._signals(zone_entry=True, zone_presence=False)
    second = evaluator_module._signals(zone_entry=False, zone_presence=True)
    assert _evaluate_graph(graph, state, first, NOW) is False
    assert _evaluate_graph(graph, state, second, NOW + timedelta(seconds=1)) is True
    assert _evaluate_graph(graph, state, second, NOW + timedelta(seconds=3)) is False
    serialized = _json_state(
        {"at": NOW, "sequence": (1, NOW), "value": True}
    )
    assert serialized == {
        "at": NOW.isoformat(),
        "sequence": [1, NOW.isoformat()],
        "value": True,
    }


def test_c10_generated_scenarios_are_sealed_and_replay_stable() -> None:
    scenario_ids = (
        "c10-line-crossing",
        "c10-zone-lifecycle",
        "c10-dwell",
        "c10-occupancy",
        "c10-out-of-order",
    )
    for scenario_id in scenario_ids:
        first = build_generated_lifecycle_scenario(
            scenario_id,
            seed=34,
            observed_at=NOW,
            department="traffic",
            assignment_id=ASSIGNMENT_ID,
            stream_id=STREAM_ID,
            camera_id=CAMERA_ID,
        )
        assert first.digest == build_generated_lifecycle_scenario(
            scenario_id,
            seed=34,
            observed_at=NOW,
            department="traffic",
            assignment_id=ASSIGNMENT_ID,
            stream_id=STREAM_ID,
            camera_id=CAMERA_ID,
        ).digest
        assert all(item.lineage["execution_scope"] == "generated_only" for item in first.inputs)
    with pytest.raises(ValueError, match="unsupported generated geometry scenario"):
        build_generated_lifecycle_scenario(
            "unsealed",
            seed=0,
            observed_at=NOW,
            department="traffic",
            assignment_id=ASSIGNMENT_ID,
            stream_id=STREAM_ID,
            camera_id=CAMERA_ID,
        )


class ZoneTransitionMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        geometry = _geometry(_zone_shape(), geometry_id="state-machine-zone")
        self.evaluator = GeometryEventEvaluator(
            (_compiled(geometry, _rule(geometry, rule_id="state-machine-entry")),)
        )
        self.sequence = 0
        self.expected_inside = False
        self.expected_entries = 0
        self.actual_entries = 0

    def _move(self, x: float) -> None:
        self.sequence += 1
        events = self.evaluator.evaluate(_sample(self.sequence, x))
        self.actual_entries += len(events)
        next_inside = 0.21 <= x <= 0.79
        if not self.expected_inside and next_inside and self.sequence > 1:
            self.expected_entries += 1
        self.expected_inside = next_inside

    @initialize()
    def start_outside(self) -> None:
        self._move(0.1)

    @rule()
    def remain_outside(self) -> None:
        self._move(0.1)

    @rule()
    def enter_or_remain_inside(self) -> None:
        self._move(0.5)

    @rule()
    def exit(self) -> None:
        self._move(0.9)

    @invariant()
    def entries_are_transition_only(self) -> None:
        assert self.actual_entries == self.expected_entries


def test_c10_hypothesis_zone_transition_state_machine() -> None:
    run_settings = settings(
        max_examples=25,
        stateful_step_count=30,
        deadline=None,
        derandomize=True,
        suppress_health_check=[HealthCheck.too_slow],
        database=None,
    )
    run_state_machine_as_test(ZoneTransitionMachine, settings=run_settings)
