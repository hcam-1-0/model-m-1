from __future__ import annotations

from copy import deepcopy

from hcam.intelligence.integrations.bounds import MAX_RESPONSE_BYTES, validate_safe_document
from hcam.intelligence.integrations.canonical import canonical_bytes, digest
from hcam.intelligence.integrations.contracts import GeneratedProviderPayload


class ProviderResponseError(RuntimeError):
    reason_code = "provider_response_invalid"
    transient = False


class ProviderTransientError(ProviderResponseError):
    reason_code = "provider_transient_failure"
    transient = True


def parse_generated_response(
    payload: GeneratedProviderPayload,
    *,
    allowed_fields: list[str],
) -> tuple[list[dict[str, str]], str, str]:
    if payload.fault in {"transient", "slow"}:
        raise ProviderTransientError("generated provider reported a transient failure")
    if payload.fault in {"permanent", "malformed", "oversized", "revoked"}:
        raise ProviderResponseError(f"generated provider failure: {payload.fault}")
    validate_safe_document(payload.records)
    if len(canonical_bytes(payload.records, maximum_bytes=MAX_RESPONSE_BYTES)) > MAX_RESPONSE_BYTES:
        raise ProviderResponseError("generated provider response is oversized")
    minimized: list[dict[str, str]] = []
    for record in payload.records:
        item = {
            key: value
            for key, value in record.items()
            if key in allowed_fields and isinstance(value, str)
        }
        validate_safe_document(item)
        minimized.append(item)
    normalized = deepcopy(minimized)
    return normalized, digest(normalized, maximum_bytes=MAX_RESPONSE_BYTES), payload.completeness
