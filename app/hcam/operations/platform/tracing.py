from __future__ import annotations

import re

from hcam.operations.platform.bounds import MAX_TRACE_STATE_BYTES
from hcam.operations.platform.contracts import CorrelationContextV1, TraceContextV1


_TRACE_PARENT = re.compile(
    r"^(?P<version>[0-9a-f]{2})-(?P<trace>[0-9a-f]{32})-"
    r"(?P<parent>[0-9a-f]{16})-(?P<flags>[0-9a-f]{2})$"
)
_TRACE_STATE_MEMBER = re.compile(
    r"^[a-z0-9][_0-9a-z*\-/]{0,255}(?:@[a-z0-9][_0-9a-z*\-/]{0,240})?="
    r"[\x20-\x2b\x2d-\x3c\x3e-\x7e]{1,256}$"
)


class TraceContextError(ValueError):
    pass


def parse_trace_context(traceparent: str, tracestate: str | None = None) -> TraceContextV1:
    match = _TRACE_PARENT.fullmatch(traceparent)
    if match is None or match["version"] == "ff":
        raise TraceContextError("traceparent is invalid")
    if match["trace"] == "0" * 32 or match["parent"] == "0" * 16:
        raise TraceContextError("trace identifiers cannot be all zero")
    flags = int(match["flags"], 16)
    if match["version"] == "00" and flags not in {0, 1}:
        raise TraceContextError("trace flags are invalid for version 00")
    normalized_state = _validate_tracestate(tracestate)
    return TraceContextV1(
        trace_id=match["trace"],
        parent_id=match["parent"],
        sampled=bool(flags & 1),
        tracestate=normalized_state,
    )


def _validate_tracestate(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise TraceContextError("tracestate must be ASCII") from exc
    if not encoded or len(encoded) > MAX_TRACE_STATE_BYTES or value.strip() != value:
        raise TraceContextError("tracestate is outside its bounds")
    members = value.split(",")
    if len(members) > 32 or any(_TRACE_STATE_MEMBER.fullmatch(item) is None for item in members):
        raise TraceContextError("tracestate contains an invalid member")
    keys = [item.partition("=")[0] for item in members]
    if len(keys) != len(set(keys)):
        raise TraceContextError("tracestate keys must be unique")
    return value


def correlation_context(correlation_id: str, causation_id: str | None = None) -> CorrelationContextV1:
    return CorrelationContextV1(
        correlation_id=correlation_id,
        causation_id=causation_id,
        grants_authority=False,
    )
