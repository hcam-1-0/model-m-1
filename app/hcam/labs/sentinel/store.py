from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from hcam.labs.sentinel import ADAPTER_KIND, LAB_SCHEMA_VERSION
from hcam.labs.sentinel.models import CatalogEndpoint, NormalizedCatalog


class CatalogStoreError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class CatalogSourceConfig:
    source_id: str
    catalog_locator: str
    department_scope: str
    auth_mode: str
    secret_ref: str | None
    enabled: bool
    auto_apply: bool
    etag: str | None


def _timestamp(value: datetime | None = None) -> str:
    moment = value or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS lab_schema (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS catalog_sources (
    source_id TEXT PRIMARY KEY,
    adapter_kind TEXT NOT NULL,
    catalog_locator TEXT NOT NULL,
    department_scope TEXT NOT NULL,
    auth_mode TEXT NOT NULL,
    secret_ref TEXT,
    enabled INTEGER NOT NULL,
    auto_apply INTEGER NOT NULL,
    etag TEXT,
    state TEXT NOT NULL,
    latest_snapshot_id TEXT,
    latest_applied_snapshot_id TEXT,
    rollback_snapshot_id TEXT,
    last_refresh_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS catalog_refreshes (
    refresh_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES catalog_sources(source_id),
    status TEXT NOT NULL,
    requester TEXT NOT NULL,
    reason TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    safe_failure_code TEXT,
    response_bytes INTEGER,
    record_count INTEGER,
    snapshot_id TEXT,
    requested_at TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_catalog_refresh_source_status
    ON catalog_refreshes(source_id, status, requested_at);
CREATE TABLE IF NOT EXISTS catalog_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES catalog_sources(source_id),
    fingerprint TEXT NOT NULL,
    canonical_json TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    warning_count INTEGER NOT NULL,
    completeness TEXT NOT NULL,
    first_observed_at TEXT NOT NULL,
    last_observed_at TEXT NOT NULL,
    UNIQUE(source_id, fingerprint)
);
CREATE TABLE IF NOT EXISTS catalog_memberships (
    source_id TEXT NOT NULL REFERENCES catalog_sources(source_id),
    external_camera_id TEXT NOT NULL,
    camera_id TEXT NOT NULL,
    name TEXT,
    location TEXT,
    profile_id TEXT,
    advertised_live INTEGER NOT NULL,
    lifecycle_state TEXT NOT NULL,
    observed_health TEXT NOT NULL DEFAULT 'unknown',
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
);
CREATE TABLE IF NOT EXISTS catalog_events (
    event_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    action TEXT NOT NULL,
    outcome TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_catalog_events_source_created
    ON catalog_events(source_id, created_at);
"""


class CatalogStore:
    """Standalone Phase 2.5 state store; no H-CAM product database dependency."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)
            membership_columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(catalog_memberships)"
                ).fetchall()
            }
            if "observed_health" not in membership_columns:
                connection.execute(
                    "ALTER TABLE catalog_memberships "
                    "ADD COLUMN observed_health TEXT NOT NULL DEFAULT 'unknown'"
                )
            connection.execute(
                """
                INSERT INTO lab_schema(singleton, schema_version, updated_at)
                VALUES (1, ?, ?)
                ON CONFLICT(singleton) DO UPDATE SET
                    schema_version=excluded.schema_version,
                    updated_at=excluded.updated_at
                """,
                (LAB_SCHEMA_VERSION, _timestamp()),
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 10000")
            connection.execute("PRAGMA journal_mode = WAL")
            yield connection
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def upsert_source(
        self,
        *,
        source_id: str,
        catalog_locator: str,
        department_scope: str = "Engineering Lab",
        auth_mode: str = "none",
        secret_ref: str | None = None,
        enabled: bool = True,
        auto_apply: bool = True,
        now: datetime | None = None,
    ) -> dict[str, object]:
        if not source_id or len(source_id) > 120:
            raise CatalogStoreError("invalid_source_id")
        if auth_mode not in {"none", "bearer", "basic"}:
            raise CatalogStoreError("invalid_auth_mode")
        if auth_mode != "none" and not secret_ref:
            raise CatalogStoreError("secret_ref_required")
        if auth_mode == "none" and secret_ref is not None:
            raise CatalogStoreError("secret_ref_not_allowed")
        observed_at = _timestamp(now)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO catalog_sources(
                    source_id, adapter_kind, catalog_locator, department_scope,
                    auth_mode, secret_ref, enabled, auto_apply, state,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    catalog_locator=excluded.catalog_locator,
                    department_scope=excluded.department_scope,
                    auth_mode=excluded.auth_mode,
                    secret_ref=excluded.secret_ref,
                    enabled=excluded.enabled,
                    auto_apply=excluded.auto_apply,
                    updated_at=excluded.updated_at
                """,
                (
                    source_id,
                    ADAPTER_KIND,
                    catalog_locator,
                    department_scope,
                    auth_mode,
                    secret_ref,
                    int(enabled),
                    int(auto_apply),
                    observed_at,
                    observed_at,
                ),
            )
            self._event(
                connection, source_id, "stream_catalog.source.update", "success", {}
            )
            connection.commit()
        source = self.get_source(source_id)
        assert source is not None
        return source

    def get_source(self, source_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM catalog_sources WHERE source_id = ?", (source_id,)
            ).fetchone()
        return self._source_document(row) if row is not None else None

    def get_source_config(self, source_id: str) -> CatalogSourceConfig | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM catalog_sources WHERE source_id = ?", (source_id,)
            ).fetchone()
        if row is None:
            return None
        return CatalogSourceConfig(
            source_id=row["source_id"],
            catalog_locator=row["catalog_locator"],
            department_scope=row["department_scope"],
            auth_mode=row["auth_mode"],
            secret_ref=row["secret_ref"],
            enabled=bool(row["enabled"]),
            auto_apply=bool(row["auto_apply"]),
            etag=row["etag"],
        )

    def begin_refresh(
        self,
        source_id: str,
        *,
        requester: str,
        reason: str,
        now: datetime | None = None,
    ) -> str:
        if not requester.strip() or not reason.strip():
            raise CatalogStoreError("refresh_context_required")
        refresh_id = f"p25r_{uuid4().hex}"
        requested_at = _timestamp(now)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            source = connection.execute(
                "SELECT enabled FROM catalog_sources WHERE source_id = ?", (source_id,)
            ).fetchone()
            if source is None:
                connection.rollback()
                raise CatalogStoreError("source_not_found")
            if not source["enabled"]:
                connection.rollback()
                raise CatalogStoreError("source_disabled")
            active = connection.execute(
                """
                SELECT refresh_id FROM catalog_refreshes
                WHERE source_id = ? AND status IN ('queued', 'running')
                LIMIT 1
                """,
                (source_id,),
            ).fetchone()
            if active is not None:
                connection.rollback()
                raise CatalogStoreError("refresh_already_active")
            connection.execute(
                """
                INSERT INTO catalog_refreshes(
                    refresh_id, source_id, status, requester, reason,
                    requested_at, started_at
                ) VALUES (?, ?, 'running', ?, ?, ?, ?)
                """,
                (
                    refresh_id,
                    source_id,
                    requester.strip(),
                    reason.strip(),
                    requested_at,
                    requested_at,
                ),
            )
            self._event(
                connection, source_id, "stream_catalog.refresh.queue", "success", {}
            )
            connection.commit()
        return refresh_id

    def complete_refresh(
        self,
        refresh_id: str,
        *,
        snapshot_id: str | None,
        response_bytes: int,
        record_count: int,
        etag: str | None,
        unchanged: bool = False,
        now: datetime | None = None,
    ) -> None:
        completed_at = _timestamp(now)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT source_id, status FROM catalog_refreshes WHERE refresh_id = ?",
                (refresh_id,),
            ).fetchone()
            if row is None or row["status"] != "running":
                connection.rollback()
                raise CatalogStoreError("refresh_not_running")
            connection.execute(
                """
                UPDATE catalog_refreshes SET status='succeeded', snapshot_id=?,
                    response_bytes=?, record_count=?, completed_at=?
                WHERE refresh_id=?
                """,
                (snapshot_id, response_bytes, record_count, completed_at, refresh_id),
            )
            connection.execute(
                """
                UPDATE catalog_sources SET etag=COALESCE(?, etag), state=?,
                    last_refresh_at=?, updated_at=? WHERE source_id=?
                """,
                (
                    etag,
                    "unchanged" if unchanged else "ready",
                    completed_at,
                    completed_at,
                    row["source_id"],
                ),
            )
            self._event(
                connection,
                row["source_id"],
                "stream_catalog.refresh.complete",
                "unchanged" if unchanged else "success",
                {"record_count": record_count},
            )
            connection.commit()

    def fail_refresh(
        self, refresh_id: str, code: str, *, now: datetime | None = None
    ) -> None:
        completed_at = _timestamp(now)
        safe_code = (
            code if code.replace("_", "").isalnum() else "catalog_refresh_failed"
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT source_id, status FROM catalog_refreshes WHERE refresh_id = ?",
                (refresh_id,),
            ).fetchone()
            if row is None or row["status"] != "running":
                connection.rollback()
                raise CatalogStoreError("refresh_not_running")
            connection.execute(
                """
                UPDATE catalog_refreshes SET status='failed', safe_failure_code=?,
                    completed_at=? WHERE refresh_id=?
                """,
                (safe_code, completed_at, refresh_id),
            )
            connection.execute(
                "UPDATE catalog_sources SET state='degraded', updated_at=? WHERE source_id=?",
                (completed_at, row["source_id"]),
            )
            self._event(
                connection,
                row["source_id"],
                "stream_catalog.refresh.fail",
                "failed",
                {"code": safe_code},
            )
            connection.commit()

    def apply_snapshot(
        self,
        source_id: str,
        catalog: NormalizedCatalog,
        *,
        candidate_health: Mapping[str, bool] | None = None,
        missing_grace_observations: int = 3,
        missing_grace_seconds: int = 300,
        max_change_ratio: float = 0.75,
        now: datetime | None = None,
    ) -> dict[str, object]:
        if not 1 <= missing_grace_observations <= 100 or missing_grace_seconds < 0:
            raise CatalogStoreError("invalid_missing_grace")
        if not 0 < max_change_ratio <= 1:
            raise CatalogStoreError("invalid_change_ratio")
        observed_at = _timestamp(now)
        moment = _parse_timestamp(observed_at)
        assert moment is not None
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            source = connection.execute(
                "SELECT * FROM catalog_sources WHERE source_id=?", (source_id,)
            ).fetchone()
            if source is None:
                connection.rollback()
                raise CatalogStoreError("source_not_found")
            existing_rows = connection.execute(
                "SELECT * FROM catalog_memberships WHERE source_id=?", (source_id,)
            ).fetchall()
            existing = {row["external_camera_id"]: row for row in existing_rows}
            incoming = {camera.external_id: camera for camera in catalog.cameras}
            changed_ids = set(existing) ^ set(incoming)
            for external_id in set(existing) & set(incoming):
                if existing[external_id]["semantic_json"] != _json(
                    incoming[external_id].canonical()
                ):
                    changed_ids.add(external_id)
            denominator = max(len(existing), 1)
            if existing and len(changed_ids) / denominator > max_change_ratio:
                self._event(
                    connection,
                    source_id,
                    "stream_catalog.reconciliation.apply",
                    "rejected",
                    {
                        "code": "catalog_change_anomaly",
                        "change_count": len(changed_ids),
                    },
                )
                connection.commit()
                raise CatalogStoreError("catalog_change_anomaly")
            prior_snapshot_id = source["latest_applied_snapshot_id"]
            snapshot = connection.execute(
                """
                SELECT snapshot_id FROM catalog_snapshots
                WHERE source_id=? AND fingerprint=?
                """,
                (source_id, catalog.fingerprint),
            ).fetchone()
            if snapshot is None:
                snapshot_id = f"p25s_{uuid4().hex}"
                completeness = "complete" if catalog.warning_count == 0 else "partial"
                connection.execute(
                    """
                    INSERT INTO catalog_snapshots(
                        snapshot_id, source_id, fingerprint, canonical_json,
                        record_count, warning_count, completeness,
                        first_observed_at, last_observed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        source_id,
                        catalog.fingerprint,
                        catalog.canonical_json,
                        len(catalog.cameras),
                        catalog.warning_count,
                        completeness,
                        observed_at,
                        observed_at,
                    ),
                )
            else:
                snapshot_id = snapshot["snapshot_id"]
                connection.execute(
                    "UPDATE catalog_snapshots SET last_observed_at=? WHERE snapshot_id=?",
                    (observed_at, snapshot_id),
                )
            promoted = 0
            rolled_back = 0
            recovered = 0
            created = 0
            for camera in catalog.cameras:
                previous = existing.get(camera.external_id)
                endpoint_json = _json(camera.endpoint_document())
                semantic_json = _json(camera.canonical())
                candidate_ok = (
                    True
                    if candidate_health is None
                    else candidate_health.get(camera.external_id, False)
                )
                if not camera.advertised_live:
                    candidate_ok = True
                if not camera.advertised_live:
                    observed_health = "offline"
                elif candidate_health is None:
                    observed_health = (
                        "unknown" if previous is None else previous["observed_health"]
                    )
                else:
                    observed_health = (
                        "online"
                        if candidate_health.get(camera.external_id, False)
                        else "offline"
                    )
                if previous is None:
                    camera_id = self._camera_id(source_id, camera.external_id)
                    lifecycle = "active" if camera.advertised_live else "inactive"
                    current_endpoints = endpoint_json if candidate_ok else "[]"
                    candidate_status = "promoted" if candidate_ok else "rejected"
                    failure_code = None if candidate_ok else "candidate_health_failed"
                    connection.execute(
                        """
                        INSERT INTO catalog_memberships(
                            source_id, external_camera_id, camera_id, name, location,
                            profile_id, advertised_live, lifecycle_state,
                            observed_health,
                            first_seen_at, last_seen_at, latest_snapshot_id,
                            semantic_json, current_endpoints_json,
                            candidate_endpoints_json, candidate_status,
                            candidate_failure_code, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            source_id,
                            camera.external_id,
                            camera_id,
                            camera.name,
                            camera.location,
                            camera.profile_id,
                            int(camera.advertised_live),
                            lifecycle,
                            observed_health,
                            observed_at,
                            observed_at,
                            snapshot_id,
                            semantic_json,
                            current_endpoints,
                            endpoint_json,
                            candidate_status,
                            failure_code,
                            observed_at,
                        ),
                    )
                    created += 1
                else:
                    was_missing = previous["lifecycle_state"] in {
                        "missing",
                        "tombstoned",
                    }
                    lifecycle = "active" if camera.advertised_live else "inactive"
                    recovered_at = (
                        observed_at if was_missing else previous["recovered_at"]
                    )
                    recovered += int(was_missing)
                    if candidate_ok:
                        current_endpoints = endpoint_json
                        candidate_status = "promoted"
                        failure_code = None
                        promoted += int(
                            previous["current_endpoints_json"] != endpoint_json
                        )
                    else:
                        current_endpoints = previous["current_endpoints_json"]
                        candidate_status = "rolled_back"
                        failure_code = "candidate_health_failed"
                        rolled_back += 1
                    connection.execute(
                        """
                        UPDATE catalog_memberships SET name=?, location=?, profile_id=?,
                            advertised_live=?, lifecycle_state=?, observed_health=?, last_seen_at=?,
                            missing_since=NULL, missing_observations=0, recovered_at=?,
                            latest_snapshot_id=?, semantic_json=?, current_endpoints_json=?,
                            candidate_endpoints_json=?, candidate_status=?,
                            candidate_failure_code=?, updated_at=?
                        WHERE source_id=? AND external_camera_id=?
                        """,
                        (
                            camera.name,
                            camera.location,
                            camera.profile_id,
                            int(camera.advertised_live),
                            lifecycle,
                            observed_health,
                            observed_at,
                            recovered_at,
                            snapshot_id,
                            semantic_json,
                            current_endpoints,
                            endpoint_json,
                            candidate_status,
                            failure_code,
                            observed_at,
                            source_id,
                            camera.external_id,
                        ),
                    )
            missing = 0
            tombstoned = 0
            for external_id in set(existing) - set(incoming):
                previous = existing[external_id]
                count = int(previous["missing_observations"]) + 1
                missing_since = previous["missing_since"] or observed_at
                missing_at = _parse_timestamp(missing_since) or moment
                elapsed = moment - missing_at
                should_tombstone = (
                    count >= missing_grace_observations
                    and elapsed >= timedelta(seconds=missing_grace_seconds)
                )
                lifecycle = "tombstoned" if should_tombstone else "missing"
                missing += 1
                tombstoned += int(should_tombstone)
                connection.execute(
                    """
                    UPDATE catalog_memberships SET lifecycle_state=?, observed_health='offline',
                        missing_since=?, missing_observations=?, updated_at=?
                    WHERE source_id=? AND external_camera_id=?
                    """,
                    (
                        lifecycle,
                        missing_since,
                        count,
                        observed_at,
                        source_id,
                        external_id,
                    ),
                )
            connection.execute(
                """
                UPDATE catalog_sources SET latest_snapshot_id=?,
                    latest_applied_snapshot_id=?, rollback_snapshot_id=?,
                    state='ready', updated_at=? WHERE source_id=?
                """,
                (snapshot_id, snapshot_id, prior_snapshot_id, observed_at, source_id),
            )
            detail = {
                "created": created,
                "missing": missing,
                "promoted": promoted,
                "record_count": len(catalog.cameras),
                "recovered": recovered,
                "rolled_back": rolled_back,
                "tombstoned": tombstoned,
            }
            self._event(
                connection,
                source_id,
                "stream_catalog.reconciliation.apply",
                "success",
                detail,
            )
            connection.commit()
        return {
            "snapshot_id": snapshot_id,
            "fingerprint": catalog.fingerprint,
            **detail,
        }

    def summary(self, source_id: str) -> dict[str, object]:
        source = self.get_source(source_id)
        if source is None:
            raise CatalogStoreError("source_not_found")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT lifecycle_state, advertised_live, candidate_status, COUNT(*) AS count
                FROM catalog_memberships WHERE source_id=?
                GROUP BY lifecycle_state, advertised_live, candidate_status
                """,
                (source_id,),
            ).fetchall()
            health_rows = connection.execute(
                """
                SELECT observed_health, COUNT(*) AS count
                FROM catalog_memberships WHERE source_id=?
                GROUP BY observed_health
                """,
                (source_id,),
            ).fetchall()
            latest = connection.execute(
                """
                SELECT snapshot_id, fingerprint, record_count, warning_count,
                    completeness, first_observed_at, last_observed_at
                FROM catalog_snapshots WHERE source_id=?
                ORDER BY last_observed_at DESC LIMIT 1
                """,
                (source_id,),
            ).fetchone()
        counts = {
            "total": 0,
            "advertised_live": 0,
            "active": 0,
            "inactive": 0,
            "missing": 0,
            "tombstoned": 0,
            "candidate_failures": 0,
        }
        for row in rows:
            count = int(row["count"])
            counts["total"] += count
            counts["advertised_live"] += count if row["advertised_live"] else 0
            state = row["lifecycle_state"]
            if state in counts:
                counts[state] += count
            if row["candidate_status"] in {"rejected", "rolled_back"}:
                counts["candidate_failures"] += count
        return {
            "schema": LAB_SCHEMA_VERSION,
            "classification": "generated-only",
            "source": source,
            "counts": counts,
            "observed_health_counts": {
                row["observed_health"]: int(row["count"]) for row in health_rows
            },
            "latest_snapshot": dict(latest) if latest is not None else None,
        }

    def list_cameras(
        self, source_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[dict[str, object]]:
        if not 1 <= limit <= 500 or offset < 0:
            raise CatalogStoreError("invalid_pagination")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM catalog_memberships WHERE source_id=?
                ORDER BY external_camera_id LIMIT ? OFFSET ?
                """,
                (source_id, limit, offset),
            ).fetchall()
        return [self._membership_document(row) for row in rows]

    def get_camera(self, source_id: str, external_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM catalog_memberships
                WHERE source_id=? AND external_camera_id=?
                """,
                (source_id, external_id),
            ).fetchone()
        return self._membership_document(row) if row is not None else None

    def get_camera_endpoint(
        self, source_id: str, external_id: str, *, role: str
    ) -> CatalogEndpoint | None:
        """Return one trusted runtime endpoint without exposing it through API documents."""
        if role not in {"inference", "preview", "fallback"}:
            raise CatalogStoreError("invalid_transport_role")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT current_endpoints_json FROM catalog_memberships
                WHERE source_id=? AND external_camera_id=?
                """,
                (source_id, external_id),
            ).fetchone()
        if row is None:
            return None
        try:
            endpoints = json.loads(row["current_endpoints_json"])
            endpoint = next(
                item
                for item in endpoints
                if isinstance(item, dict) and item.get("role") == role
            )
            return CatalogEndpoint.model_validate(endpoint)
        except (json.JSONDecodeError, StopIteration, TypeError, ValueError) as exc:
            if isinstance(exc, StopIteration):
                return None
            raise CatalogStoreError("stored_transport_invalid") from exc

    def list_events(
        self, source_id: str, *, limit: int = 50
    ) -> list[dict[str, object]]:
        if not 1 <= limit <= 200:
            raise CatalogStoreError("invalid_pagination")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id, action, outcome, detail_json, created_at
                FROM catalog_events WHERE source_id=?
                ORDER BY created_at DESC, event_id DESC LIMIT ?
                """,
                (source_id, limit),
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "action": row["action"],
                "outcome": row["outcome"],
                "detail": json.loads(row["detail_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    @staticmethod
    def _camera_id(source_id: str, external_id: str) -> str:
        digest = hashlib.sha256(
            f"{source_id}:{external_id}".encode("utf-8")
        ).hexdigest()[:24]
        return f"p25cam_{digest}"

    @staticmethod
    def _event(
        connection: sqlite3.Connection,
        source_id: str,
        action: str,
        outcome: str,
        detail: dict[str, object],
    ) -> None:
        connection.execute(
            """
            INSERT INTO catalog_events(event_id, source_id, action, outcome, detail_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                f"p25e_{uuid4().hex}",
                source_id,
                action,
                outcome,
                _json(detail),
                _timestamp(),
            ),
        )

    @staticmethod
    def _source_document(row: sqlite3.Row) -> dict[str, object]:
        return {
            "source_id": row["source_id"],
            "adapter_kind": row["adapter_kind"],
            "catalog_locator": row["catalog_locator"],
            "department_scope": row["department_scope"],
            "auth_mode": row["auth_mode"],
            "secret_configured": row["secret_ref"] is not None,
            "enabled": bool(row["enabled"]),
            "auto_apply": bool(row["auto_apply"]),
            "state": row["state"],
            "latest_snapshot_id": row["latest_snapshot_id"],
            "latest_applied_snapshot_id": row["latest_applied_snapshot_id"],
            "rollback_snapshot_id": row["rollback_snapshot_id"],
            "last_refresh_at": row["last_refresh_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _membership_document(row: sqlite3.Row) -> dict[str, object]:
        semantic = json.loads(row["semantic_json"])
        endpoints = json.loads(row["current_endpoints_json"])
        return {
            "external_camera_id": row["external_camera_id"],
            "camera_id": row["camera_id"],
            "name": row["name"],
            "location": row["location"],
            "profile_id": row["profile_id"],
            "advertised_live": bool(row["advertised_live"]),
            "lifecycle_state": row["lifecycle_state"],
            "observed_health": row["observed_health"],
            "missing_observations": row["missing_observations"],
            "candidate_status": row["candidate_status"],
            "candidate_failure_code": row["candidate_failure_code"],
            "media": {
                "codec": semantic.get("advertised_codec"),
                "width": semantic.get("width"),
                "height": semantic.get("height"),
                "fps": semantic.get("fps"),
                "bitrate_kbps": semantic.get("bitrate_kbps"),
            },
            "transports": [
                {"role": endpoint["role"], "protocol": endpoint["protocol"]}
                for endpoint in endpoints
            ],
            "updated_at": row["updated_at"],
        }
