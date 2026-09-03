from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from hcam.analytics.geometry import (
    GeometryDefinitionV1,
    LineGeometryV1,
    NormalizedPoint,
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
from hcam.analytics.spatial.cel_policy import CelPolicyError
from hcam.analytics.spatial.evaluator import EvaluatorBoundaryError


NOW = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


def _geometry(shape, *, geometry_id: str = "generated-geometry") -> GeometryDefinitionV1:
    return GeometryDefinitionV1(
        geometry_id=geometry_id,
        version=1,
        department="traffic",
        stream_id="str_" + "1" * 32,
        camera_id="synthetic:cam-001",
        status="approved",
        shape=shape,
        intended_use="Generated-only P3.4 predicate validation",
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
    rule_id: str,
    event_kind: str,
    signal: str,
    **overrides,
) -> GeometryRuleV1:
    values = {
        "rule_id": rule_id,
        "version": 1,
        "status": "approved",
        "department": geometry.department,
        "assignment_id": "ana_" + "2" * 32,
        "stream_id": geometry.stream_id,
        "camera_id": geometry.camera_id,
        "geometry_id": geometry.geometry_id,
        "geometry_version": geometry.version,
        "event_kind": event_kind,
        "class_filter": ["vehicle.car"],
        "cel_condition": "confidence >= 0.5 && class_id == 'vehicle.car'",
        "graph": _graph(signal),
        "configuration_digest": DIGEST_B,
        "retention_class": "derived.analytics.standard",
        "owner_id": "mayank-admin",
        "approval_record_id": "D-P3.4-START",
        "effective_from": NOW - timedelta(minutes=1),
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return GeometryRuleV1.model_validate(values)


def _compiled(geometry: GeometryDefinitionV1, rule: GeometryRuleV1):
    cel = ConstrainedCelEnvironment()
    return CompiledGeometryRule.build(
        rule,
        geometry,
        canonicalize_geometry(geometry.shape),
        cel,
    )


def _sample(
    sequence: int,
    x: float,
    y: float,
    *,
    state: str = "updated",
    track_id: str = "trk_" + "3" * 32,
    observed_at: datetime | None = None,
) -> LifecycleInput:
    return LifecycleInput(
        lifecycle_id=f"lfc_{sequence:032x}",
        department="traffic",
        assignment_id="ana_" + "2" * 32,
        stream_id="str_" + "1" * 32,
        camera_id="synthetic:cam-001",
        epoch_id="epoch_" + "4" * 32,
        track_id=track_id,
        class_id="vehicle.car",
        state=state,
        reason="matched",
        observed_at=observed_at or NOW + timedelta(seconds=sequence),
        source_sequence=sequence,
        latest_observation_id=f"obs_{sequence:032x}",
        bbox=(x - 0.01, y - 0.02, 0.02, 0.02),
        confidence=0.9,
        lineage={"execution_scope": "generated_only"},
        retention_class="derived.analytics.standard",
    )


def test_canonical_geometry_is_stable_and_binds_geos() -> None:
    first = canonicalize_geometry(
        ZoneGeometryV1(
            vertices=[
                NormalizedPoint(x=0.2, y=0.2),
                NormalizedPoint(x=0.8, y=0.2),
                NormalizedPoint(x=0.8, y=0.8),
                NormalizedPoint(x=0.2, y=0.8),
            ]
        )
    )
    second = canonicalize_geometry(
        ZoneGeometryV1(
            vertices=[
                NormalizedPoint(x=0.8, y=0.8),
                NormalizedPoint(x=0.2, y=0.8),
                NormalizedPoint(x=0.2, y=0.2),
                NormalizedPoint(x=0.8, y=0.2),
            ]
        )
    )
    assert first.digest == second.digest
    assert first.canonical_wkb == second.canonical_wkb
    assert first.shapely_version == "2.1.2"
    assert first.geos_version == "3.13.1"


def test_constrained_cel_is_typed_serializable_and_fail_closed() -> None:
    environment = ConstrainedCelEnvironment()
    checked = environment.compile("confidence >= 0.75 && scheduled")
    context = {
        "class_id": "vehicle.car",
        "confidence": 0.9,
        "direction": "a_to_b",
        "scheduled": True,
        "count": 1,
        "line_crossing": True,
        "zone_entry": False,
        "zone_exit": False,
        "zone_presence": False,
        "zone_dwell_threshold": False,
        "zone_occupancy_entered": False,
        "zone_occupancy_exited": False,
    }
    assert environment.evaluate(checked, context) is True
    assert checked.digest.startswith("sha256:")
    with pytest.raises(CelPolicyError, match="unapproved identifier"):
        environment.compile("secret_value == 'x'")
    with pytest.raises(CelPolicyError, match="unapproved identifier"):
        environment.compile("camera.owner == 'x'")
    with pytest.raises(CelPolicyError, match="Boolean"):
        environment.compile("confidence + 1.0")


def test_line_crossing_uses_finite_segment_direction_and_rearm() -> None:
    geometry = _geometry(
        LineGeometryV1(
            start=NormalizedPoint(x=0.5, y=0.1),
            end=NormalizedPoint(x=0.5, y=0.9),
        ),
        geometry_id="generated-crossing-line",
    )
    rule = _rule(
        geometry,
        rule_id="generated-line-crossing",
        event_kind="hcam.analytics.line.crossing.v1",
        signal="line_crossing",
        line_direction="both",
        deadband=0.01,
        rearm_distance=0.04,
    )
    evaluator = GeometryEventEvaluator((_compiled(geometry, rule),))
    assert evaluator.evaluate(_sample(1, 0.3, 0.5)) == ()
    first = evaluator.evaluate(_sample(2, 0.7, 0.5))
    assert len(first) == 1
    assert first[0].direction == "a_to_b"
    assert evaluator.evaluate(_sample(3, 0.49, 0.5)) == ()
    assert evaluator.evaluate(_sample(4, 0.7, 0.5)) == ()
    assert evaluator.evaluate(_sample(5, 0.3, 0.5))[0].direction == "b_to_a"

    outside_segment = GeometryEventEvaluator((_compiled(geometry, rule),))
    outside_segment.evaluate(_sample(10, 0.3, 0.96))
    assert outside_segment.evaluate(_sample(11, 0.7, 0.96)) == ()


def test_zone_entry_exit_dwell_and_occupancy_have_transition_semantics() -> None:
    geometry = _geometry(
        ZoneGeometryV1(
            vertices=[
                NormalizedPoint(x=0.2, y=0.2),
                NormalizedPoint(x=0.8, y=0.2),
                NormalizedPoint(x=0.8, y=0.8),
                NormalizedPoint(x=0.2, y=0.8),
            ]
        ),
        geometry_id="generated-zone",
    )
    entry = _rule(
        geometry,
        rule_id="generated-entry",
        event_kind="hcam.analytics.zone.entry.v1",
        signal="zone_entry",
        zone_hysteresis=0.01,
    )
    evaluator = GeometryEventEvaluator((_compiled(geometry, entry),))
    evaluator.evaluate(_sample(1, 0.1, 0.5))
    events = evaluator.evaluate(_sample(2, 0.5, 0.5))
    assert [event.event_kind for event in events] == ["hcam.analytics.zone.entry.v1"]
    assert evaluator.evaluate(_sample(3, 0.6, 0.5)) == ()

    dwell = _rule(
        geometry,
        rule_id="generated-dwell",
        event_kind="hcam.analytics.zone.dwell.threshold_met.v1",
        signal="zone_dwell_threshold",
        zone_hysteresis=0.01,
        dwell_threshold_ms=2_000,
        occlusion_grace_ms=1_500,
    )
    dwell_evaluator = GeometryEventEvaluator((_compiled(geometry, dwell),))
    dwell_evaluator.evaluate(_sample(10, 0.5, 0.5, observed_at=NOW))
    assert dwell_evaluator.evaluate(
        _sample(11, 0.5, 0.5, observed_at=NOW + timedelta(seconds=1))
    ) == ()
    event = dwell_evaluator.evaluate(
        _sample(12, 0.5, 0.5, observed_at=NOW + timedelta(seconds=2))
    )[0]
    assert event.dwell_ms == 2_000
    assert dwell_evaluator.evaluate(
        _sample(13, 0.5, 0.5, observed_at=NOW + timedelta(seconds=3))
    ) == ()

    occupancy = _rule(
        geometry,
        rule_id="generated-occupancy",
        event_kind="hcam.analytics.zone.occupancy.threshold_entered.v1",
        signal="zone_occupancy_entered",
        zone_hysteresis=0.01,
        occupancy_enter_threshold=2,
        occupancy_reset_threshold=0,
    )
    occupancy_evaluator = GeometryEventEvaluator((_compiled(geometry, occupancy),))
    occupancy_evaluator.evaluate(_sample(20, 0.5, 0.5, track_id="trk_" + "5" * 32))
    aggregate = occupancy_evaluator.evaluate(
        _sample(21, 0.6, 0.5, track_id="trk_" + "6" * 32)
    )[0]
    assert aggregate.track_id is None
    assert aggregate.count == 2


def test_event_buffer_orders_deduplicates_and_rejects_conflicts() -> None:
    buffer = BoundedEventBuffer()
    third = _sample(3, 0.3, 0.5, observed_at=NOW + timedelta(seconds=3))
    first = _sample(1, 0.3, 0.5, observed_at=NOW)
    second = _sample(2, 0.3, 0.5, observed_at=NOW + timedelta(seconds=1))
    assert buffer.push(third) == "accepted"
    assert buffer.push(first) == "accepted"
    assert buffer.push(first) == "duplicate"
    assert buffer.push(second) == "accepted"
    assert [item.source_sequence for item in buffer.pop_ready()] == [1, 2]
    assert [item.source_sequence for item in buffer.drain()] == [3]

    conflict = replace(
        first,
        lifecycle_id="lfc_" + "f" * 32,
        confidence=0.8,
    )
    conflicting_buffer = BoundedEventBuffer()
    conflicting_buffer.push(first)
    with pytest.raises(EvaluatorBoundaryError, match="sequence_conflict"):
        conflicting_buffer.push(conflict)
