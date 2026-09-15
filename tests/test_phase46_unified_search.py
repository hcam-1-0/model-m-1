from datetime import UTC, datetime

import pytest

from hcam.operations.platform.contracts import SignalProjectionV1
from hcam.operations.platform.unified_search import UnifiedSearchDisabledError, build_disabled_projection, execute_search


def test_unified_projection_is_disabled_sanitized_and_non_authoritative() -> None:
    item = SignalProjectionV1(
        signal_id="ref_" + "1" * 32,
        lane="security",
        department="Generated Department",
        event_type="policy.denied",
        severity="warning",
        occurred_at=datetime(2026, 9, 5, tzinfo=UTC),
        safe_facets={"outcome": "denied"},
    )
    result = build_disabled_projection([item])
    assert result.enabled is False
    assert result.authoritative is False
    assert result.raw_records_retained is False


def test_unified_search_execution_is_impossible() -> None:
    with pytest.raises(UnifiedSearchDisabledError):
        execute_search("generated")
