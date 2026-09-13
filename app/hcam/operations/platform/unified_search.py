from __future__ import annotations

from hcam.operations.platform.canonical import digest
from hcam.operations.platform.contracts import SignalProjectionV1, UnifiedSearchProjectionV1


class UnifiedSearchDisabledError(RuntimeError):
    pass


def build_disabled_projection(items: list[SignalProjectionV1]) -> UnifiedSearchProjectionV1:
    ordered = sorted(items, key=lambda item: (item.occurred_at, item.lane, item.signal_id))
    identity = {"profile": "hcam.unified-signal-search.generated.v1", "items": [item.model_dump(mode="json") for item in ordered]}
    return UnifiedSearchProjectionV1(items=ordered, result_digest=digest(identity))


def execute_search(*_args, **_kwargs) -> None:
    raise UnifiedSearchDisabledError("the unified signal search projection is disabled")
