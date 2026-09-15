from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.intelligence.canonical import (
    CanonicalizationError,
    canonical_json,
    canonical_json_bytes,
    canonical_sha256,
)
from hcam.intelligence.contracts import (
    AdaptiveLaneResultV1,
    AlertAggregateV1,
    AlertLifecycleEventV1,
    ChronologyV1,
    CorrelationHypothesisV1,
    EvidenceReferenceV1,
    GeoJsonProfileV1,
    IntelligenceRuleV1,
    OperatorSurfaceStateV1,
    ProvenanceV1,
    ReferenceProviderV1,
    ReferenceQueryV1,
    RetentionHoldV1,
    ReviewDecisionV1,
    TimelineEntryV1,
)


FIXTURE_ROOT = Path("contracts/phase-4/fixtures")
FIXTURE_MODELS = {
    "adaptive-lane-result-v1.json": AdaptiveLaneResultV1,
    "alert-aggregate-v1.json": AlertAggregateV1,
    "alert-lifecycle-event-v1.json": AlertLifecycleEventV1,
    "chronology-v1.json": ChronologyV1,
    "correlation-hypothesis-v1.json": CorrelationHypothesisV1,
    "evidence-reference-v1.json": EvidenceReferenceV1,
    "geojson-profile-v1.json": GeoJsonProfileV1,
    "intelligence-rule-v1.json": IntelligenceRuleV1,
    "operator-surface-state-v1.json": OperatorSurfaceStateV1,
    "provenance-v1.json": ProvenanceV1,
    "reference-provider-v1.json": ReferenceProviderV1,
    "reference-query-v1.json": ReferenceQueryV1,
    "retention-hold-v1.json": RetentionHoldV1,
    "review-decision-v1.json": ReviewDecisionV1,
    "timeline-entry-v1.json": TimelineEntryV1,
}


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(("name", "model"), FIXTURE_MODELS.items())
def test_fixture_round_trips_canonically(name: str, model: type) -> None:
    payload = _fixture(name)
    parsed = model.model_validate(payload)
    encoded = canonical_json(parsed)
    assert encoded == canonical_json(json.loads(encoded))
    assert canonical_sha256(parsed).startswith("sha256:")
    assert len(canonical_sha256(parsed)) == 71


@pytest.mark.parametrize(("name", "model"), FIXTURE_MODELS.items())
def test_contracts_reject_unknown_fields(name: str, model: type) -> None:
    payload = _fixture(name)
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_canonical_json_is_sorted_ascii_compact_and_bounded() -> None:
    assert canonical_json({"z": "caf\N{LATIN SMALL LETTER E WITH ACUTE}", "a": 1}) == (
        '{"a":1,"z":"caf\\u00e9"}'
    )
    assert canonical_json_bytes([True, None]) == b"[true,null]"
    with pytest.raises(CanonicalizationError):
        canonical_json({"value": float("nan")})
    with pytest.raises(CanonicalizationError):
        canonical_json({"value": object()})
    with pytest.raises(CanonicalizationError):
        canonical_json({"value": "x" * 100}, maximum_bytes=16)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update(observed_at="2026-09-03T09:59:59Z"),
        lambda value: value.update(recorded_at="2026-09-03T10:00:01"),
        lambda value: value.update(corrected_at="2026-09-03T09:59:59Z"),
    ],
)
def test_chronology_fails_closed(mutation) -> None:
    payload = _fixture("chronology-v1.json")
    mutation(payload)
    with pytest.raises(ValidationError):
        ChronologyV1.model_validate(payload)


def test_geojson_enforces_wgs84_and_closed_valid_polygons() -> None:
    point = _fixture("geojson-profile-v1.json")
    point["geometry"]["coordinates"] = [181, 0]
    with pytest.raises(ValidationError):
        GeoJsonProfileV1.model_validate(point)

    polygon = _fixture("geojson-profile-v1.json")
    polygon["geometry"] = {
        "type": "Polygon",
        "coordinates": [[[72, 23], [73, 23], [73, 24], [72, 24]]],
    }
    with pytest.raises(ValidationError):
        GeoJsonProfileV1.model_validate(polygon)
    polygon["geometry"]["coordinates"][0].append([72, 23])
    assert GeoJsonProfileV1.model_validate(polygon).geometry.type == "Polygon"

    polygon["geometry"]["coordinates"] = [
        [[72, 23], [73, 23], [72, 23], [72, 23]]
    ]
    with pytest.raises(ValidationError, match="three unique positions"):
        GeoJsonProfileV1.model_validate(polygon)


@pytest.mark.parametrize("failure", ["duplicate_node", "duplicate_edge", "unknown_node"])
def test_hypothesis_graph_rejects_ambiguous_or_dangling_edges(failure: str) -> None:
    payload = _fixture("correlation-hypothesis-v1.json")
    graph = payload["graph"]
    if failure == "duplicate_node":
        graph["nodes"].append(deepcopy(graph["nodes"][0]))
    elif failure == "duplicate_edge":
        graph["edges"].append(deepcopy(graph["edges"][0]))
    else:
        graph["edges"][0]["source_node_id"] = "unknown-generated-node"
    with pytest.raises(ValidationError):
        CorrelationHypothesisV1.model_validate(payload)


@pytest.mark.parametrize("failure", ["duplicate", "unknown", "cycle", "output"])
def test_rule_graph_validates_identity_references_and_acyclicity(failure: str) -> None:
    payload = _fixture("intelligence-rule-v1.json")
    graph = payload["graph"]
    if failure == "duplicate":
        graph["nodes"].append(deepcopy(graph["nodes"][0]))
    elif failure == "unknown":
        graph["nodes"][-1]["inputs"] = ["not-present"]
    elif failure == "cycle":
        graph["nodes"][0]["inputs"] = [graph["nodes"][-1]["node_id"]]
    else:
        graph["output_node_id"] = "not-present"
    payload["static_cost"] = len(graph["nodes"])
    with pytest.raises(ValidationError):
        IntelligenceRuleV1.model_validate(payload)


@pytest.mark.parametrize(
    ("node", "field", "value"),
    [
        (0, "duration_ms", 100),
        (0, "threshold", 2),
        (1, "field", None),
        (1, "operator", None),
        (1, "value", None),
    ],
)
def test_rule_node_parameters_are_typed_by_node_kind(
    node: int, field: str, value: object
) -> None:
    payload = _fixture("intelligence-rule-v1.json")
    payload["graph"]["nodes"][node][field] = value
    with pytest.raises(ValidationError):
        IntelligenceRuleV1.model_validate(payload)


@pytest.mark.parametrize(
    ("kind", "field", "value"),
    [
        ("event", "field", "event.kind"),
        ("window", "duration_ms", None),
        ("count", "threshold", None),
    ],
)
def test_rule_node_kind_requires_its_exact_parameter_family(
    kind: str, field: str, value: object
) -> None:
    payload = _fixture("intelligence-rule-v1.json")
    node = payload["graph"]["nodes"][0]
    node["kind"] = kind
    node[field] = value
    with pytest.raises(ValidationError):
        IntelligenceRuleV1.model_validate(payload)


def test_rule_cost_and_update_time_are_consistent() -> None:
    payload = _fixture("intelligence-rule-v1.json")
    payload["static_cost"] += 1
    with pytest.raises(ValidationError):
        IntelligenceRuleV1.model_validate(payload)
    payload = _fixture("intelligence-rule-v1.json")
    payload["updated_at"] = "2026-09-03T09:59:59Z"
    with pytest.raises(ValidationError):
        IntelligenceRuleV1.model_validate(payload)


@pytest.mark.parametrize(
    ("status", "score", "failure_code"),
    [
        ("completed", None, None),
        ("skipped", 0.5, None),
        ("failed", None, None),
        ("completed", 0.5, "runtime_disabled"),
    ],
)
def test_adaptive_lane_state_is_consistent(
    status: str, score: float | None, failure_code: str | None
) -> None:
    payload = _fixture("adaptive-lane-result-v1.json")
    payload.update(status=status, score=score, failure_code=failure_code)
    with pytest.raises(ValidationError):
        AdaptiveLaneResultV1.model_validate(payload)


@pytest.mark.parametrize("failure", ["abstention", "projection", "contradiction"])
def test_hypothesis_projection_and_evidence_are_consistent(failure: str) -> None:
    payload = _fixture("correlation-hypothesis-v1.json")
    if failure == "abstention":
        payload["abstained"] = not payload["abstained"]
    elif failure == "projection":
        payload["flat_projection"]["hypothesis_id"] = "hyp_" + "f" * 32
    else:
        payload["contradiction_count"] += 1
    with pytest.raises(ValidationError):
        CorrelationHypothesisV1.model_validate(payload)


def test_provider_and_operator_lists_are_unique() -> None:
    provider = _fixture("reference-provider-v1.json")
    provider["allowed_fields"].append(provider["allowed_fields"][0])
    with pytest.raises(ValidationError):
        ReferenceProviderV1.model_validate(provider)
    surface = _fixture("operator-surface-state-v1.json")
    surface["available_actions"] = ["view", "view"]
    with pytest.raises(ValidationError):
        OperatorSurfaceStateV1.model_validate(surface)
