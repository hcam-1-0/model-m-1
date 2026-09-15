from __future__ import annotations

from hcam.operations.platform.contracts import FailureV1
from hcam.operations.platform.registry import FAILURE_REGISTRY


def failure(code: str, *, safe_parameters: dict[str, str | int | bool] | None = None) -> FailureV1:
    failure_class, retry = FAILURE_REGISTRY.get(code, FAILURE_REGISTRY["state.unknown"])
    normalized_code = code if code in FAILURE_REGISTRY else "state.unknown"
    return FailureV1(
        code=normalized_code,
        failure_class=failure_class,
        retry=retry,
        safe_parameters=safe_parameters or {},
    )


def may_retry(record: FailureV1, *, attempt_count: int, maximum_attempts: int = 3) -> bool:
    return record.retry == "bounded" and 0 <= attempt_count < min(maximum_attempts, 3)
