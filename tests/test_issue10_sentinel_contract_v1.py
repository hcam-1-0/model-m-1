from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import httpx
import pytest

from hcam.labs.sentinel.adapter import CatalogAdapterError, SentinelCatalogAdapter
from hcam.labs.sentinel.models import (
    CONTRACT_ERROR_CODES,
    CatalogValidationError,
    ExactNetworkPolicy,
    NetworkRule,
    normalize_catalog_document,
)
from hcam.labs.sentinel.store import CatalogStore, CatalogStoreError


FIXTURES = Path(__file__).parent / "fixtures" / "sentinel_contract_v1"
CASES = json.loads((FIXTURES / "catalogues.json").read_text(encoding="utf-8"))


def policy() -> ExactNetworkPolicy:
    return ExactNetworkPolicy(
        (
            NetworkRule("https", "catalog.invalid", 443, "/api/ingest"),
            NetworkRule("rtsp", "contract-media.invalid", 8554, "/hcam/"),
            NetworkRule("http", "contract-media.invalid", 8889, "/hcam/"),
            NetworkRule("http", "contract-media.invalid", 8888, "/hcam/"),
        )
    )


def normalized(case: str, *, maximum: int = 500):
    return normalize_catalog_document(
        CASES[case],
        origin="https://catalog.invalid/api/ingest",
        network_policy=policy(),
        max_records=maximum,
    )


def test_versioned_valid_fixture_has_strict_safe_projections() -> None:
    catalog = normalized("valid")
    camera = catalog.cameras[0]
    assert camera.external_id == "LAB-001"
    assert camera.browser_safe() == {
        "id": "LAB-001",
        "name": "Redacted Lab Camera",
        "advertised_live": True,
        "advertised_codec": None,
        "profile_id": None,
        "preview_compatible": True,
        "registry_state": "catalogued",
    }
    assert camera.gis_safe()["longitude"] == -97.7431
    rendered = json.dumps([camera.browser_safe(), camera.gis_safe(), catalog.canonical_json])
    assert "contract-media.invalid" not in rendered
    assert "rtsp://" not in rendered
    assert "password" not in rendered


def test_additive_fields_are_ignored_without_becoming_a_dto_or_diagnostic() -> None:
    catalog = normalized("additive")
    assert catalog.warning_count == 1
    rendered = json.dumps(catalog.cameras[0].browser_safe())
    assert "vendor_additive" not in rendered


@pytest.mark.parametrize(
    ("case", "code"),
    (
        ("missing_transport", "transport_missing"),
        ("malformed_transport", "invalid_transport"),
        ("duplicate_identifier", "duplicate_identifier"),
        ("invalid_identifier", "invalid_identifier"),
        ("unsafe_locator", "unsafe_locator"),
        ("query_locator", "unsafe_locator"),
        ("fragment_locator", "unsafe_locator"),
        ("unapproved_host", "unsafe_locator"),
        ("unapproved_port", "unsafe_locator"),
        ("invalid_geometry", "invalid_geometry"),
        ("invalid_timestamp", "invalid_timestamp"),
        ("unsupported_version", "schema_version_unsupported"),
        ("schema_drift", "schema_drift"),
        ("over_capacity", "over_capacity"),
    ),
)
def test_fixture_rejections_use_bounded_stable_codes(case: str, code: str) -> None:
    with pytest.raises(CatalogValidationError) as caught:
        normalized(case, maximum=1 if case == "over_capacity" else 500)
    assert caught.value.code == code
    assert caught.value.code in CONTRACT_ERROR_CODES
    assert "contract-media.invalid" not in str(caught.value)


@pytest.mark.parametrize(
    ("document", "code"),
    (
        ({"contract": "sentinel_sandbox_catalog_v1", "schema_version": 1}, "required_field_missing"),
        ({"contract": "sentinel_sandbox_catalog_v1", "schema_version": 1, "cameras": "no"}, "invalid_field_type"),
        ({"contract": "sentinel_sandbox_catalog_v1", "schema_version": 1, "cameras": [{"live": True}]}, "required_field_missing"),
    ),
)
def test_required_and_invalid_field_types_are_stable(document: object, code: str) -> None:
    with pytest.raises(CatalogValidationError) as caught:
        normalize_catalog_document(
            document,
            origin="https://catalog.invalid/api/ingest",
            network_policy=policy(),
        )
    assert caught.value.code == code


def test_snapshot_requires_explicit_reviewed_update_path() -> None:
    digest = hashlib.sha256(normalized("valid").canonical_json.encode("ascii")).hexdigest()
    expected = (FIXTURES / "snapshot.sha256").read_text(encoding="ascii").strip()
    assert digest == expected, "snapshot drift: use `python tools/sentinel_contract_v1.py update --acknowledge`"


def test_real_adapter_preserves_last_known_good_on_schema_rejection_and_recovers(tmp_path) -> None:
    store = CatalogStore(tmp_path / "catalog.db")
    store.initialize()
    store.upsert_source(
        source_id="contract-source",
        catalog_locator="https://catalog.invalid/api/ingest",
    )
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=CASES["valid"] if calls != 2 else CASES["schema_drift"])

    adapter = SentinelCatalogAdapter(
        store, policy(), transport=httpx.MockTransport(handler), retry_delays=(0.0,)
    )
    first = asyncio.run(adapter.refresh("contract-source", requester="test", reason="valid"))
    with pytest.raises(CatalogAdapterError, match="schema_drift"):
        asyncio.run(adapter.refresh("contract-source", requester="test", reason="unsafe"))
    retained = store.summary("contract-source")["latest_snapshot"]
    recovered = asyncio.run(adapter.refresh("contract-source", requester="test", reason="recovery"))

    assert first.snapshot_id == retained["snapshot_id"]  # type: ignore[index]
    assert recovered.snapshot_id == first.snapshot_id
    assert store.get_camera("contract-source", "LAB-001") is not None


def test_missing_and_tombstone_catalogues_never_delete_last_known_good_identity(tmp_path) -> None:
    store = CatalogStore(tmp_path / "catalog.db")
    store.initialize()
    store.upsert_source(source_id="contract-source", catalog_locator="https://catalog.invalid/api/ingest")
    store.apply_snapshot("contract-source", normalized("valid"))
    store.apply_snapshot(
        "contract-source",
        normalized("tombstone"),
        missing_grace_observations=1,
        missing_grace_seconds=0,
        max_change_ratio=1,
    )
    assert store.get_camera("contract-source", "LAB-001") is not None


def test_out_of_order_record_cannot_replace_newer_last_known_good_state(tmp_path) -> None:
    store = CatalogStore(tmp_path / "catalog.db")
    store.initialize()
    store.upsert_source(source_id="contract-source", catalog_locator="https://catalog.invalid/api/ingest")
    newer = json.loads(json.dumps(CASES["valid"]))
    newer["cameras"][0]["updated_at"] = "2026-01-02T00:00:00Z"
    older = json.loads(json.dumps(CASES["valid"]))
    older["cameras"][0]["updated_at"] = "2026-01-01T00:00:00Z"
    store.apply_snapshot(
        "contract-source",
        normalize_catalog_document(newer, origin="https://catalog.invalid/api/ingest", network_policy=policy()),
    )
    with pytest.raises(CatalogStoreError, match="out_of_order_record"):
        store.apply_snapshot(
            "contract-source",
            normalize_catalog_document(older, origin="https://catalog.invalid/api/ingest", network_policy=policy()),
        )
    assert store.get_camera("contract-source", "LAB-001") is not None


def test_contract_fixtures_are_offline_and_redacted() -> None:
    # This parser uses only fixture bytes and an injected policy; it has no HTTP client.
    raw = (FIXTURES / "catalogues.json").read_text(encoding="utf-8")
    forbidden = ("http://live.", "https://live.", "Authorization", "Bearer ", "v=0\\r\\n")
    assert not any(token in raw for token in forbidden)
    for case in ("valid", "additive", "partial", "tombstone"):
        normalized(case)
