"""Generated-only Phase 4.1 correlation foundation."""

from hcam.intelligence.correlation.arbitration import arbitrate_lane_results
from hcam.intelligence.correlation.contracts import (
    CorrelationBatchResultV1,
    CorrelationHypothesisV2,
    CorrelationIngressEventV1,
    CorrelationProfileV1,
    CorrelationReceiptV1,
    LaneResultV1,
)
from hcam.intelligence.correlation.runtime import run_generated_batch

__all__ = [
    "CorrelationBatchResultV1",
    "CorrelationHypothesisV2",
    "CorrelationIngressEventV1",
    "CorrelationProfileV1",
    "CorrelationReceiptV1",
    "LaneResultV1",
    "arbitrate_lane_results",
    "run_generated_batch",
]
