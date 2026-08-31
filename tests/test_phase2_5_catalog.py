from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime, timedelta
import sqlite3

import pytest

from hcam.labs.sentinel.fixtures import generated_catalog_document, generated_media_profiles
from hcam.labs.sentinel.models import (
    CatalogValidationError,
    ExactNetworkPolicy,
    NetworkRule,
    normalize_catalog_document,
)
from hcam.labs.sentinel.store import CatalogStore, CatalogStoreError


def lab_policy() -> ExactNetworkPolicy:
    return ExactNetworkPolicy(
        (
            NetworkRule("http", "catalog-simulator", 8090, "/api/ingest"),
            NetworkRule("rtsp", "mediamtx", 8554, "/hcam/"),
            NetworkRule("rtsp", "rtsp-fault-proxy", 8555, "/hcam/"),
            NetworkRule("http", "mediamtx", 8889, "/hcam/"),
            NetworkRule("http", "mediamtx", 8888, "/hcam/"),
        )
    )


def normalized(scenario: str = "base"):
    return normalize_catalog_document(
        generated_catalog_document(scenario=scenario),
        origin="http://catalog-simulator:8090/api/ingest",
        network_policy=lab_policy(),
    )


def test_generated_manifest_has_unique_dynamic_profiles() -> None:
    profiles = generated_media_profiles()

    assert len(profiles) == 50
    assert len({profile.profile_id for profile in profiles}) == 50
    assert len({profile.fixture_name for profile in profiles}) == 50
    assert sum(profile.active_by_default for profile in profiles) == 30
    assert {profile.actual_codec for profile in profiles} == {"h264", "hevc"}
    assert len({(profile.width, profile.height, profile.fps) for profile in profiles}) >= 8
    assert sum(not profile.expected_reachable for profile in profiles) == 3


def test_catalog_normalization_is_order_independent_and_sanitized() -> None:
    base = normalized()
    reordered = normalized("reordered")

    assert base.fingerprint == reordered.fingerprint
    assert len(base.cameras) == 50
    assert sum(camera.advertised_live for camera in base.cameras) == 30
    assert "rtsp://" not in base.canonical_json
    assert "mediamtx" not in base.canonical_json
    assert all(camera.endpoints for camera in base.cameras)
    assert any(camera.advertised_codec is None for camera in base.cameras)


def test_catalogue_mutations_cover_unknown_new_endpoint_and_codec_changes() -> None:
    baseline = normalized()
    unknown = normalized("unknown")
    endpoint = normalized("endpoint")
    codec = normalized("codec")
    added = normalize_catalog_document(
        generated_catalog_document(mode="compatibility", scenario="new"),
        origin="http://catalog-simulator:8090/api/ingest",
        network_policy=lab_policy(),
    )

    assert unknown.warning_count > baseline.warning_count
    assert endpoint.fingerprint != baseline.fingerprint
    assert codec.fingerprint != baseline.fingerprint
    assert len(added.cameras) == 13


def test_malformed_catalogue_value_is_rejected() -> None:
    with pytest.raises(CatalogValidationError, match="invalid_live_state"):
        normalized("malformed")


def test_empty_catalogue_is_a_valid_bounded_snapshot() -> None:
    empty = normalized("empty")

    assert empty.cameras == ()
    assert empty.warning_count == 0


@pytest.mark.parametrize(
    ("scenario", "code"),
    (("duplicate", "duplicate_camera_id"), ("hostile", "credential_bearing_url")),
)
def test_catalog_rejects_ambiguous_or_hostile_records(scenario: str, code: str) -> None:
    with pytest.raises(CatalogValidationError, match=code) as caught:
        normalized(scenario)

    assert caught.value.code == code


def test_catalog_enforces_record_limit() -> None:
    with pytest.raises(CatalogValidationError, match="catalog_record_limit_exceeded"):
        normalize_catalog_document(
            generated_catalog_document(),
            origin="http://catalog-simulator:8090/api/ingest",
            network_policy=lab_policy(),
            max_records=12,
        )


def test_store_deduplicates_snapshots_and_never_deletes_memberships(tmp_path) -> None:
    store = CatalogStore(tmp_path / "phase2-5.db")
    store.initialize()
    store.upsert_source(
        source_id="generated-sentinel",
        catalog_locator="http://catalog-simulator:8090/api/ingest",
    )
    started = datetime(2026, 8, 28, tzinfo=UTC)
    first = store.apply_snapshot("generated-sentinel", normalized(), now=started)
    second = store.apply_snapshot(
        "generated-sentinel", normalized("reordered"), now=started + timedelta(seconds=1)
    )

    assert first["snapshot_id"] == second["snapshot_id"]
    assert store.summary("generated-sentinel")["counts"] == {
        "total": 50,
        "advertised_live": 30,
        "active": 30,
        "inactive": 20,
        "missing": 0,
        "tombstoned": 0,
        "candidate_failures": 0,
    }
    assert store.summary("generated-sentinel")["observed_health_counts"] == {
        "unknown": 30,
        "offline": 20,
    }

    missing = normalized("missing")
    for offset in (2, 3, 4):
        store.apply_snapshot(
            "generated-sentinel",
            missing,
            missing_grace_seconds=0,
            now=started + timedelta(seconds=offset),
        )
    absent = store.get_camera("generated-sentinel", "C01")
    assert absent is not None
    assert absent["lifecycle_state"] == "tombstoned"
    assert absent["observed_health"] == "offline"
    assert absent["missing_observations"] == 3
    assert store.summary("generated-sentinel")["counts"]["total"] == 50

    store.apply_snapshot("generated-sentinel", normalized(), now=started + timedelta(seconds=5))
    recovered = store.get_camera("generated-sentinel", "C01")
    assert recovered is not None
    assert recovered["lifecycle_state"] == "active"
    assert recovered["missing_observations"] == 0


def test_store_migrates_existing_lab_database_with_observed_health(tmp_path) -> None:
    path = tmp_path / "old-lab.db"
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            """
            CREATE TABLE catalog_memberships (
                source_id TEXT NOT NULL,
                external_camera_id TEXT NOT NULL,
                camera_id TEXT NOT NULL,
                name TEXT,
                location TEXT,
                profile_id TEXT,
                advertised_live INTEGER NOT NULL,
                lifecycle_state TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                missing_since TEXT,
                missing_observations INTEGER NOT NULL DEFAULT 0,
                recovered_at TEXT,
                latest_snapshot_id TEXT,
                semantic_json TEXT NOT NULL,
                current_endpoints_json TEXT NOT NULL,
                candidate_endpoints_json TEXT,
                candidate_status TEXT NOT NULL,
                candidate_failure_code TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(source_id, external_camera_id),
                UNIQUE(camera_id)
            )
            """
        )
        connection.commit()

    CatalogStore(path).initialize()

    with closing(sqlite3.connect(path)) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(catalog_memberships)")
        }
    assert "observed_health" in columns


def test_store_rolls_back_failed_candidate_without_exposing_locator(tmp_path) -> None:
    store = CatalogStore(tmp_path / "phase2-5.db")
    store.initialize()
    store.upsert_source(
        source_id="generated-sentinel",
        catalog_locator="http://catalog-simulator:8090/api/ingest",
    )
    store.apply_snapshot("generated-sentinel", normalized())
    result = store.apply_snapshot(
        "generated-sentinel",
        normalized("updated"),
        candidate_health={camera.external_id: camera.external_id != "C01" for camera in normalized("updated").cameras},
    )
    camera = store.get_camera("generated-sentinel", "C01")

    assert result["rolled_back"] == 1
    assert camera is not None
    assert camera["candidate_status"] == "rolled_back"
    assert camera["observed_health"] == "offline"
    assert "locator" not in str(camera)
    assert {transport["role"] for transport in camera["transports"]} == {
        "inference",
        "preview",
        "fallback",
    }


def test_store_rejects_mass_change_after_baseline(tmp_path) -> None:
    store = CatalogStore(tmp_path / "phase2-5.db")
    store.initialize()
    store.upsert_source(
        source_id="generated-sentinel",
        catalog_locator="http://catalog-simulator:8090/api/ingest",
    )
    store.apply_snapshot("generated-sentinel", normalized())
    compatibility = normalize_catalog_document(
        generated_catalog_document(mode="compatibility"),
        origin="http://catalog-simulator:8090/api/ingest",
        network_policy=lab_policy(),
    )

    with pytest.raises(CatalogStoreError, match="catalog_change_anomaly"):
        store.apply_snapshot("generated-sentinel", compatibility)


def test_source_auth_configuration_fails_closed(tmp_path) -> None:
    store = CatalogStore(tmp_path / "phase2-5.db")
    store.initialize()

    with pytest.raises(CatalogStoreError, match="secret_ref_required"):
        store.upsert_source(
            source_id="generated-sentinel",
            catalog_locator="http://catalog-simulator:8090/api/ingest",
            auth_mode="bearer",
        )
