from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from hcam.analytics.models import AnalyticsAssignment
from hcam.database import CURRENT_SCHEMA_REVISION, Database
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id


def _upgrade(database_url: str, revision: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, revision)


def _downgrade(database_url: str, revision: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.downgrade(config, revision)


def _check(database_url: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.check(config)


def _assignment(*, desired_state: str = "paused") -> AnalyticsAssignment:
    now = datetime.now(UTC)
    return AnalyticsAssignment(
        assignment_id="ana_" + "a" * 32,
        department="Engineering Lab",
        stream_id=synthetic_stream_id(1),
        camera_id="phase2:cctv-001",
        capability="object_detection",
        desired_state=desired_state,
        lifecycle_state="blocked",
        reason_code="owner_gates_pending",
        pipeline_id="hcam-object-pipeline",
        pipeline_version="sha256:" + "a" * 64,
        models=[{"id": "yolo11n-detector", "version": "sha256:" + "b" * 64}],
        taxonomy_version="hcam.object.v1",
        policy_version="sha256:" + "c" * 64,
        configuration_digest="sha256:" + "d" * 64,
        minimum_confidence=0.65,
        sampling_fps=5.0,
        maximum_queue_age_ms=2_000,
        geometry_refs=[{"id": "synthetic-entry-zone", "version": 1}],
        retention_class="derived.analytics.standard",
        last_actor_id="migration-test",
        last_change_reason="Validate fail-closed assignment database constraints",
        approval_record_id="DR-P3.0-001",
        created_at=now,
        updated_at=now,
    )


def test_analytics_assignment_migration_round_trip_and_constraints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = f"sqlite:///{(tmp_path / 'analytics-migration.db').as_posix()}"
    monkeypatch.setenv("HCAM_DATABASE_URL", database_url)
    _upgrade(database_url, "head")
    database = Database(database_url)
    try:
        database.check_ready()
        _check(database_url)
        inspector = inspect(database.engine)
        tables = set(inspector.get_table_names())
        assert CURRENT_SCHEMA_REVISION == "0010_generated_tracking"
        assert {
            "analytics_assignments",
            "analytics_assignment_revisions",
            "analytics_generated_runs",
            "analytics_observations",
            "analytics_tracking_runs",
            "analytics_tracker_epochs",
            "analytics_tracks",
            "analytics_track_lifecycle",
        }.issubset(tables)
        assignment_columns = {
            column["name"] for column in inspector.get_columns("analytics_assignments")
        }
        assert {
            "assignment_id",
            "version_id",
            "desired_state",
            "lifecycle_state",
            "reason_code",
            "execution_scope",
            "configuration_digest",
            "approval_record_id",
        }.issubset(assignment_columns)
        run_columns = {
            column["name"]
            for column in inspector.get_columns("analytics_generated_runs")
        }
        observation_columns = {
            column["name"] for column in inspector.get_columns("analytics_observations")
        }
        assert {
            "input_sha256",
            "generator_version",
            "failure_code",
            "retention_class",
        }.issubset(run_columns)
        assert {
            "class_id",
            "confidence",
            "event_id",
            "bbox_x",
            "bbox_y",
            "bbox_width",
            "bbox_height",
            "lineage",
        }.issubset(observation_columns)
        prohibited_storage_tokens = {
            "blob",
            "bytes",
            "frame",
            "image",
            "locator",
            "media",
            "path",
            "pixel",
            "url",
        }
        assert not any(
            token in column.lower()
            for column in run_columns | observation_columns
            for token in prohibited_storage_tokens
        )
        run_check_sql = " ".join(
            str(item["sqltext"])
            for item in inspector.get_check_constraints("analytics_generated_runs")
        )
        observation_check_sql = " ".join(
            str(item["sqltext"])
            for item in inspector.get_check_constraints("analytics_observations")
        )
        assert "hcam.det-r0.generated-frame" in run_check_sql
        assert "length(input_sha256) = 64" in run_check_sql
        assert "DET-R0-ONNX-UPSTREAM-0.1.1RC0" in observation_check_sql
        assert "source_width = 416 AND source_height = 416" in observation_check_sql
        check_sql = " ".join(
            str(item["sqltext"])
            for item in inspector.get_check_constraints("analytics_assignments")
        )
        assert "desired_state IN ('paused', 'enabled')" in check_sql
        assert "'running'" in check_sql
        assert "execution_scope = 'generated_only'" in check_sql
        assert "generated_runtime_active" in check_sql

        with database.session_factory() as session:
            seed_synthetic_lab(session, count=1)
        with database.session_factory() as session:
            session.add(_assignment(desired_state="enabled"))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

        _downgrade(database_url, "0008_analytics_assignments")
        downgraded_tables = set(inspect(database.engine).get_table_names())
        assert "analytics_assignments" in downgraded_tables
        assert "analytics_assignment_revisions" in downgraded_tables
        assert "analytics_generated_runs" not in downgraded_tables
        assert "analytics_observations" not in downgraded_tables
        downgraded_assignment_columns = {
            column["name"]
            for column in inspect(database.engine).get_columns("analytics_assignments")
        }
        assert "execution_scope" not in downgraded_assignment_columns

        _upgrade(database_url, "head")
        assert {
            "analytics_assignments",
            "analytics_assignment_revisions",
            "analytics_generated_runs",
            "analytics_observations",
            "analytics_tracking_runs",
            "analytics_tracker_epochs",
            "analytics_tracks",
            "analytics_track_lifecycle",
        }.issubset(set(inspect(database.engine).get_table_names()))
        database.check_ready()
    finally:
        database.dispose()
