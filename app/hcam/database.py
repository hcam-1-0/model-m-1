from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Request
from sqlalchemy import DateTime, Engine, create_engine, event, inspect, text
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator


PHASE3_SCHEMA_REVISION = "0011_geometry_events"
CURRENT_SCHEMA_REVISION = "0018_operations_security_scale"
PHASE3_SCHEMA_BASE_REVISION = PHASE3_SCHEMA_REVISION
REQUIRED_CAMERA_COLUMNS = frozenset(
    {
        "camera_id",
        "version_id",
        "source_id",
        "external_id",
        "display_name",
        "latitude",
        "longitude",
        "geometry",
        "duration_seconds",
        "provenance",
        "created_at",
        "updated_at",
    }
)
REQUIRED_AUDIT_COLUMNS = frozenset(
    {
        "event_id",
        "actor_id",
        "action",
        "target_type",
        "target_id",
        "occurred_at",
        "source",
        "reason",
        "outcome",
        "context",
    }
)
REQUIRED_STREAM_COLUMNS = frozenset(
    {
        "stream_id",
        "camera_id",
        "version_id",
        "adapter_kind",
        "protocol",
        "locator",
        "is_primary",
        "probe_due_at",
        "lease_until",
        "management_locator",
        "onvif_auth_mode",
        "capability_refresh_enabled",
        "capability_due_at",
        "onvif_control_enabled",
        "onvif_max_velocity",
        "onvif_max_move_seconds",
    }
)
REQUIRED_ANALYTICS_ASSIGNMENT_COLUMNS = frozenset(
    {
        "assignment_id",
        "version_id",
        "department",
        "stream_id",
        "camera_id",
        "capability",
        "desired_state",
        "lifecycle_state",
        "reason_code",
        "execution_scope",
        "configuration_digest",
        "approval_record_id",
        "created_at",
        "updated_at",
    }
)
REQUIRED_INTELLIGENCE_RULE_COLUMNS = frozenset(
    {
        "rule_id",
        "version_id",
        "department",
        "stream_id",
        "camera_id",
        "status",
        "authority_class",
        "operational",
        "generated_only",
        "definition",
        "configuration_digest",
        "created_at",
        "updated_at",
        "authoring_digest",
        "semantic_digest",
        "compilation_id",
        "schedule_digest",
    }
)
REQUIRED_REFERENCE_PROVIDER_COLUMNS = frozenset(
    {
        "provider_id",
        "version_id",
        "department",
        "provider_kind",
        "status",
        "enabled",
        "transport_state",
        "credential_state",
        "definition",
        "configuration_digest",
        "created_at",
        "updated_at",
    }
)
REQUIRED_CORRELATION_RUN_COLUMNS = frozenset(
    {
        "run_id",
        "department",
        "status",
        "execution_scope",
        "reason_code",
        "generated_only",
        "profile_id",
        "profile_version",
        "result_digest",
        "replay_binding",
        "input_count",
        "accepted_count",
        "duplicate_count",
        "rejected_count",
        "attempt_count",
        "lease_owner",
        "lease_until",
        "watermark_at",
        "created_at",
        "updated_at",
    }
)
REQUIRED_CORRELATION_HYPOTHESIS_COLUMNS = frozenset(
    {
        "hypothesis_id",
        "version_id",
        "department",
        "run_id",
        "hypothesis_key",
        "profile_id",
        "profile_version",
        "partition_digest",
        "revision",
        "state",
        "authority_class",
        "operational",
        "generated_only",
        "graph_digest",
        "arbitration_digest",
        "projection",
    }
)
REQUIRED_ALERT_COLUMNS = frozenset(
    {
        "alert_id",
        "version_id",
        "department",
        "hypothesis_id",
        "dedupe_key",
        "semantic_key",
        "delivery_key",
        "source_evaluation_id",
        "source_evaluation_revision",
        "source_evaluation_digest",
        "incident_key",
        "domain",
        "state",
        "authority_class",
        "operational",
        "generated_only",
        "severity",
        "priority",
        "confidence",
        "certainty",
        "chronology_confidence",
        "disposition",
        "assigned_to",
        "suppression_code",
        "merged_into",
        "policy_digest",
        "payload",
        "content_digest",
        "retention_class",
        "created_at",
        "updated_at",
    }
)
REQUIRED_REFERENCE_INTEGRATION_COLUMNS = {
    "reference_provider_versions": frozenset(
        {
            "provider_version_id",
            "provider_id",
            "department",
            "status",
            "manifest_digest",
            "payload",
            "version_id",
            "generated_only",
            "operational",
        }
    ),
    "reference_catalogue_snapshots": frozenset(
        {
            "snapshot_id",
            "provider_version_id",
            "department",
            "fingerprint",
            "payload",
            "stale_at",
            "raw_response_retained",
        }
    ),
    "reference_query_jobs": frozenset(
        {
            "job_id",
            "query_id",
            "provider_version_id",
            "department",
            "state",
            "attempt_count",
            "lease_owner",
            "lease_until",
            "semantic_key",
            "delivery_key",
            "intent_payload",
            "plan_payload",
            "generated_only",
            "operational",
        }
    ),
    "reference_candidate_sets": frozenset(
        {
            "candidate_set_id",
            "query_id",
            "department",
            "outcome",
            "identity_state",
            "mandatory_review",
            "payload",
            "generated_only",
            "operational",
        }
    ),
    "reference_control_revisions": frozenset(
        {
            "revision_id",
            "department",
            "scope",
            "scope_key",
            "state",
            "version",
            "actor_id",
            "reason",
            "generated_only",
        }
    ),
}
REQUIRED_PLATFORM_COLUMNS = {
    "platform_service_objectives": frozenset(
        {"objective_id", "department", "service_class", "target_state", "revision", "content_digest", "payload"}
    ),
    "platform_error_budgets": frozenset(
        {"budget_id", "objective_id", "department", "status", "content_digest", "payload", "observed_at"}
    ),
    "platform_degradation_states": frozenset(
        {"degradation_id", "department", "state", "revision", "content_digest", "payload", "recorded_at"}
    ),
    "platform_circuit_states": frozenset(
        {"circuit_id", "department", "dependency_class", "state", "content_digest", "payload", "updated_at"}
    ),
    "platform_kill_switch_revisions": frozenset(
        {"record_id", "switch_id", "department", "scope", "scope_key", "state", "revision", "content_digest"}
    ),
    "platform_recovery_results": frozenset(
        {"result_id", "plan_id", "department", "outcome", "content_digest", "payload", "recorded_at"}
    ),
    "platform_capacity_results": frozenset(
        {"run_id", "department", "profile_id", "scale", "mode", "status", "content_digest", "payload"}
    ),
    "platform_supply_chain_inventories": frozenset(
        {"inventory_id", "department", "freshness", "source_digest", "content_digest", "payload", "observed_at"}
    ),
    "platform_security_evidence": frozenset(
        {"evidence_id", "department", "evidence_type", "outcome", "content_digest", "payload", "recorded_at"}
    ),
    "platform_operations_outbox": frozenset(
        {"event_id", "department", "event_type", "state", "attempt_count", "idempotency_key", "payload", "available_at"}
    ),
}


class Base(DeclarativeBase):
    pass


class DatabaseNotReadyError(RuntimeError):
    pass


class UTCDateTime(TypeDecorator[datetime]):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, _dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def process_result_value(
        self, value: datetime | None, _dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


def ensure_sqlite_parent(database_url: str) -> None:
    if (
        not database_url.startswith("sqlite:///")
        or database_url == "sqlite:///:memory:"
    ):
        return

    path_text = database_url.removeprefix("sqlite:///")
    if path_text.startswith("file:"):
        return
    Path(path_text).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _is_sqlite(database_url: str) -> bool:
    return urlsplit(database_url).scheme.startswith("sqlite")


def build_engine(
    database_url: str,
    *,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: float = 30.0,
    pool_recycle: int = 1800,
) -> Engine:
    ensure_sqlite_parent(database_url)
    connect_args = {"check_same_thread": False} if _is_sqlite(database_url) else {}
    engine_options: dict[str, object] = {
        "connect_args": connect_args,
        "pool_pre_ping": True,
    }
    if not _is_sqlite(database_url):
        engine_options.update(
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
        )
    engine = create_engine(database_url, **engine_options)

    if _is_sqlite(database_url):

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

    return engine


class Database:
    def __init__(
        self,
        database_url: str,
        *,
        allow_unversioned_schema: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: int = 1800,
    ) -> None:
        self.engine = build_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
        )
        self.allow_unversioned_schema = allow_unversioned_schema
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=Session,
            expire_on_commit=False,
        )

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def check_ready(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            inspector = inspect(connection)
            table_names = set(inspector.get_table_names())
            camera_columns = (
                {column["name"] for column in inspector.get_columns("cameras")}
                if "cameras" in table_names
                else set()
            )
            audit_columns = (
                {column["name"] for column in inspector.get_columns("audit_events")}
                if "audit_events" in table_names
                else set()
            )
            stream_columns = (
                {column["name"] for column in inspector.get_columns("stream_endpoints")}
                if "stream_endpoints" in table_names
                else set()
            )
            analytics_assignment_columns = (
                {
                    column["name"]
                    for column in inspector.get_columns("analytics_assignments")
                }
                if "analytics_assignments" in table_names
                else set()
            )
            intelligence_rule_columns = (
                {
                    column["name"]
                    for column in inspector.get_columns("intelligence_rules")
                }
                if "intelligence_rules" in table_names
                else set()
            )
            reference_provider_columns = (
                {
                    column["name"]
                    for column in inspector.get_columns("reference_providers")
                }
                if "reference_providers" in table_names
                else set()
            )
            correlation_run_columns = (
                {column["name"] for column in inspector.get_columns("correlation_runs")}
                if "correlation_runs" in table_names
                else set()
            )
            correlation_hypothesis_columns = (
                {
                    column["name"]
                    for column in inspector.get_columns("correlation_hypotheses")
                }
                if "correlation_hypotheses" in table_names
                else set()
            )
            alert_columns = (
                {column["name"] for column in inspector.get_columns("alerts")}
                if "alerts" in table_names
                else set()
            )
            reference_integration_columns = {
                table: (
                    {column["name"] for column in inspector.get_columns(table)}
                    if table in table_names
                    else set()
                )
                for table in REQUIRED_REFERENCE_INTEGRATION_COLUMNS
            }
            platform_columns = {
                table: (
                    {column["name"] for column in inspector.get_columns(table)}
                    if table in table_names
                    else set()
                )
                for table in REQUIRED_PLATFORM_COLUMNS
            }
        required_tables = {
            "cameras",
            "audit_events",
            "stream_endpoints",
            "stream_health_current",
            "stream_probe_runs",
            "stream_event_outbox",
            "playback_sessions",
            "stream_capability_snapshots",
            "stream_capability_refreshes",
            "onvif_control_leases",
            "onvif_operation_runs",
            "analytics_assignments",
            "analytics_assignment_revisions",
            "analytics_generated_runs",
            "analytics_observations",
            "analytics_tracking_runs",
            "analytics_tracker_epochs",
            "analytics_tracks",
            "analytics_track_lifecycle",
            "analytics_geometries",
            "analytics_geometry_rules",
            "analytics_geometry_evaluator_runs",
            "analytics_track_rule_states",
            "analytics_events",
            "intelligence_rules",
            "correlation_runs",
            "correlation_hypotheses",
            "hypothesis_evidence_refs",
            "reference_providers",
            "reference_queries",
            "alerts",
            "alert_revisions",
            "investigation_timelines",
            "timeline_entries",
            "correlation_event_receipts",
            "correlation_partition_checkpoints",
            "correlation_window_events",
            "correlation_lane_results",
            "correlation_hypothesis_revisions",
            "alert_command_receipts",
            "alert_lifecycle_events",
            "alert_review_quorum_policies",
            "alert_review_decisions",
            "alert_assignment_events",
            "alert_suppression_events",
            "alert_merge_relations",
            "alert_budget_policies",
            "alert_budget_counters",
            "alert_timer_intents",
            "alert_workflow_executions",
            "reference_provider_versions",
            "reference_catalogue_snapshots",
            "reference_catalogue_records",
            "reference_query_jobs",
            "reference_query_attempts",
            "reference_candidate_sets",
            "reference_review_handoffs",
            "reference_control_revisions",
            "reference_circuit_states",
            "reference_integration_outbox",
            "investigation_timelines_v2",
            "investigation_timeline_revisions",
            "investigation_timeline_entries_v2",
            "investigation_evidence_references",
            "investigation_integrity_assessments",
            "investigation_provenance_bundles",
            "investigation_corrections",
            "investigation_correction_impacts",
            "investigation_reviews",
            "investigation_relationships",
            "investigation_hold_overlays",
            "investigation_retention_evaluations",
            "investigation_deletion_receipts",
            "investigation_export_manifests",
            "investigation_impact_jobs",
            "investigation_command_receipts",
            "investigation_outbox",
            "platform_service_objectives",
            "platform_error_budgets",
            "platform_degradation_states",
            "platform_circuit_states",
            "platform_kill_switch_revisions",
            "platform_recovery_results",
            "platform_capacity_results",
            "platform_supply_chain_inventories",
            "platform_security_evidence",
            "platform_operations_outbox",
        }
        missing_tables = required_tables - table_names
        missing_columns = REQUIRED_CAMERA_COLUMNS - camera_columns
        missing_audit_columns = REQUIRED_AUDIT_COLUMNS - audit_columns
        missing_stream_columns = REQUIRED_STREAM_COLUMNS - stream_columns
        missing_analytics_assignment_columns = (
            REQUIRED_ANALYTICS_ASSIGNMENT_COLUMNS - analytics_assignment_columns
        )
        missing_intelligence_rule_columns = (
            REQUIRED_INTELLIGENCE_RULE_COLUMNS - intelligence_rule_columns
        )
        missing_reference_provider_columns = (
            REQUIRED_REFERENCE_PROVIDER_COLUMNS - reference_provider_columns
        )
        missing_correlation_run_columns = (
            REQUIRED_CORRELATION_RUN_COLUMNS - correlation_run_columns
        )
        missing_correlation_hypothesis_columns = (
            REQUIRED_CORRELATION_HYPOTHESIS_COLUMNS - correlation_hypothesis_columns
        )
        missing_alert_columns = REQUIRED_ALERT_COLUMNS - alert_columns
        missing_reference_integration_columns = {
            table: required - reference_integration_columns[table]
            for table, required in REQUIRED_REFERENCE_INTEGRATION_COLUMNS.items()
            if required - reference_integration_columns[table]
        }
        missing_platform_columns = {
            table: required - platform_columns[table]
            for table, required in REQUIRED_PLATFORM_COLUMNS.items()
            if required - platform_columns[table]
        }
        if (
            missing_tables
            or missing_columns
            or missing_audit_columns
            or missing_stream_columns
            or missing_analytics_assignment_columns
            or missing_intelligence_rule_columns
            or missing_reference_provider_columns
            or missing_correlation_run_columns
            or missing_correlation_hypothesis_columns
            or missing_alert_columns
            or missing_reference_integration_columns
            or missing_platform_columns
        ):
            raise DatabaseNotReadyError("database migrations are not current")
        if self.allow_unversioned_schema:
            return
        if "alembic_version" not in table_names:
            raise DatabaseNotReadyError("database migration revision is unavailable")
        with self.engine.connect() as connection:
            revisions = set(
                connection.execute(text("SELECT version_num FROM alembic_version"))
                .scalars()
                .all()
            )
        if revisions != {CURRENT_SCHEMA_REVISION}:
            raise DatabaseNotReadyError("database migration revision is not current")

    def dispose(self) -> None:
        self.engine.dispose()


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.database.session_factory() as session:
        yield session


# Alembic imports this module directly, so Phase 4 tables must register here.
from hcam.intelligence import models as _intelligence_models  # noqa: E402,F401
from hcam.intelligence.integrations import persistence as _integration_models  # noqa: E402,F401
from hcam.intelligence.investigations import persistence as _investigation_models  # noqa: E402,F401
from hcam.operations.platform import models as _platform_models  # noqa: E402,F401
