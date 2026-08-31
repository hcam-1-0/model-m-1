from __future__ import annotations

import json

import pytest

from hcam.labs.sentinel.lab_adapters import (
    DEFAULT_LAB_ADAPTER,
    LAB1_HIGH_ADAPTER,
    LAB2_LOW_ADAPTER,
    LabAdapterStateError,
    read_active_lab_adapter,
    write_active_lab_adapter,
)
from hcam.labs.sentinel.publisher import cleanup_requested, publisher_state_document


def test_high_adapter_preserves_full_fidelity_contract() -> None:
    assert DEFAULT_LAB_ADAPTER is LAB1_HIGH_ADAPTER
    assert LAB1_HIGH_ADAPTER.record_count == 50
    assert LAB1_HIGH_ADAPTER.active_stream_count == 30
    assert LAB1_HIGH_ADAPTER.fixture_capacity == 50
    assert LAB1_HIGH_ADAPTER.full_fidelity is True
    assert LAB1_HIGH_ADAPTER.catalog_capacity == 50
    assert LAB1_HIGH_ADAPTER.preview_session_limit == 4
    assert LAB1_HIGH_ADAPTER.quality_policy == "native"


def test_low_adapter_reduces_concurrency_without_reducing_fixture_quality() -> None:
    assert LAB2_LOW_ADAPTER.record_count == 12
    assert LAB2_LOW_ADAPTER.active_stream_count == 4
    assert LAB2_LOW_ADAPTER.fixture_capacity == 50
    assert LAB2_LOW_ADAPTER.full_fidelity is False
    assert LAB2_LOW_ADAPTER.catalog_capacity == 50
    assert LAB2_LOW_ADAPTER.preview_session_limit == 1
    assert LAB2_LOW_ADAPTER.quality_policy == "native"
    state = publisher_state_document(LAB2_LOW_ADAPTER, [])
    assert state["stream_copy"] is True
    assert state["quality_downgraded"] is False


def test_lab_adapter_selection_is_durable_and_fail_closed(tmp_path) -> None:
    state_path = tmp_path / "active-lab-adapter.json"
    assert read_active_lab_adapter(state_path) is LAB1_HIGH_ADAPTER

    write_active_lab_adapter(state_path, "lab2lowadapter")
    assert read_active_lab_adapter(state_path) is LAB2_LOW_ADAPTER

    document = json.loads(state_path.read_text(encoding="ascii"))
    document["adapter_id"] = "external-adapter"
    state_path.write_text(json.dumps(document), encoding="ascii")
    with pytest.raises(LabAdapterStateError, match="lab_adapter_unknown"):
        read_active_lab_adapter(state_path)


def test_generated_fixture_cleanup_requires_explicit_valid_request(tmp_path) -> None:
    request = tmp_path / "cleanup-request.json"

    assert cleanup_requested(None) is True
    assert cleanup_requested(request) is False

    request.write_text(
        '{"classification":"generated-only","cleanup":true}', encoding="ascii"
    )
    assert cleanup_requested(request) is True

    request.write_text('{"classification":"external","cleanup":true}', encoding="ascii")
    assert cleanup_requested(request) is False
