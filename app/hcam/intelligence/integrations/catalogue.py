from __future__ import annotations

from datetime import datetime, timedelta

from hcam.intelligence.integrations.canonical import digest, stable_id
from hcam.intelligence.integrations.contracts import (
    CatalogueRecordV1,
    CatalogueSnapshotV1,
)


def build_catalogue_snapshot(
    *,
    provider_version_id: str,
    department: str,
    records: list[dict[str, str]],
    observed_at: datetime,
    completeness: str = "complete",
    stale_after: timedelta = timedelta(hours=36),
    first_observed_at: datetime | None = None,
) -> CatalogueSnapshotV1:
    normalized: list[CatalogueRecordV1] = []
    for fields in records:
        record_digest = digest(fields)
        normalized.append(
            CatalogueRecordV1(
                record_id=stable_id("grec", provider_version_id, record_digest),
                fields=fields,
                record_digest=record_digest,
            )
        )
    normalized.sort(key=lambda item: item.record_id)
    fingerprint = digest(
        {
            "provider_version_id": provider_version_id,
            "records": [item.model_dump(mode="json") for item in normalized],
            "completeness": completeness,
        }
    )
    first = first_observed_at or observed_at
    return CatalogueSnapshotV1(
        snapshot_id=stable_id("rcat", provider_version_id, fingerprint),
        provider_version_id=provider_version_id,
        department=department,
        records=normalized,
        fingerprint=fingerprint,
        completeness=completeness,
        first_observed_at=first,
        last_observed_at=observed_at,
        observed_at=observed_at,
        stale_at=observed_at + stale_after,
    )


class CatalogueHistory:
    def __init__(self) -> None:
        self._snapshots: dict[str, list[CatalogueSnapshotV1]] = {}

    def observe(self, snapshot: CatalogueSnapshotV1) -> tuple[CatalogueSnapshotV1, bool]:
        history = self._snapshots.setdefault(snapshot.provider_version_id, [])
        if history and history[-1].fingerprint == snapshot.fingerprint:
            prior = history[-1]
            refreshed = snapshot.model_copy(
                update={"first_observed_at": prior.first_observed_at}
            )
            history[-1] = CatalogueSnapshotV1.model_validate(
                refreshed.model_dump(mode="json")
            )
            return history[-1], False
        history.append(snapshot)
        return snapshot, True

    def latest(self, provider_version_id: str) -> CatalogueSnapshotV1 | None:
        history = self._snapshots.get(provider_version_id, [])
        return history[-1] if history else None

    def history(self, provider_version_id: str) -> list[CatalogueSnapshotV1]:
        return list(self._snapshots.get(provider_version_id, []))
