from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.contracts import (
    CorrelationIngressEventV1,
    CorrelationLane,
    CorrelationProfileV1,
    CorrelationWindowV1,
    LaneCapabilityV1,
    LaneResultV1,
)


DETERMINISTIC_LANE_VERSION = canonical_sha256(
    {"lane": "deterministic_cpu", "policy": "p4.1.generated.evidence-count.v1"}
)


class CorrelationLaneAdapter(Protocol):
    @property
    def capability(self) -> LaneCapabilityV1: ...

    def evaluate(
        self,
        window: CorrelationWindowV1,
        events: Sequence[CorrelationIngressEventV1],
        profile: CorrelationProfileV1,
    ) -> LaneResultV1: ...


def lane_capabilities() -> list[LaneCapabilityV1]:
    optional: tuple[CorrelationLane, ...] = (
        "probabilistic",
        "temporal_graph",
        "model_first_shadow",
        "uncertainty_ensemble",
    )
    capabilities = [
        LaneCapabilityV1(
            lane="deterministic_cpu",
            implementation_version=DETERMINISTIC_LANE_VERSION,
            execution_state="enabled_generated_only",
            resource_class="cpu",
            deterministic=True,
        )
    ]
    capabilities.extend(
        LaneCapabilityV1(
            lane=lane,
            implementation_version=canonical_sha256(
                {"lane": lane, "state": "p4.1.contract-only"}
            ),
            execution_state="unavailable",
            resource_class=(
                "accelerator_optional" if lane != "uncertainty_ensemble" else "contract_only"
            ),
            deterministic=False,
        )
        for lane in optional
    )
    return capabilities


def unavailable_optional_results() -> list[LaneResultV1]:
    return [
        LaneResultV1(
            lane=capability.lane,
            status="unavailable",
            abstained=True,
            failure_code="capability_unavailable",
            lineage_digest=capability.implementation_version,
        )
        for capability in lane_capabilities()
        if capability.lane != "deterministic_cpu"
    ]
