from __future__ import annotations

from datetime import timedelta

from hcam.intelligence.integrations.catalogue import CatalogueHistory, build_catalogue_snapshot
from tests.test_phase44_contracts import NOW, manifest


def test_catalogue_deduplicates_unchanged_observations_and_preserves_first_seen() -> None:
    provider = manifest()
    records = [{"record_key": "gen_record_001", "category": "gen_category_a"}]
    first = build_catalogue_snapshot(
        provider_version_id=provider.provider_version_id,
        department=provider.department,
        records=records,
        observed_at=NOW,
    )
    second = build_catalogue_snapshot(
        provider_version_id=provider.provider_version_id,
        department=provider.department,
        records=records,
        observed_at=NOW + timedelta(hours=2),
    )
    history = CatalogueHistory()
    assert history.observe(first)[1] is True
    refreshed, changed = history.observe(second)
    assert changed is False
    assert refreshed.first_observed_at == NOW
    assert refreshed.last_observed_at == NOW + timedelta(hours=2)
    assert refreshed.stale_at == NOW + timedelta(hours=38)
    assert history.latest(provider.provider_version_id) == refreshed
    assert len(history.history(provider.provider_version_id)) == 1
