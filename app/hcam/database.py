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


CURRENT_SCHEMA_REVISION = "0007_onvif_operations"
REQUIRED_CAMERA_COLUMNS = frozenset(
    {
        "camera_id",
        "version_id",
        "source_id",
        "external_id",
        "display_name",
        "latitude",
        "longitude",
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
    if not database_url.startswith("sqlite:///") or database_url == "sqlite:///:memory:":
        return

    path_text = database_url.removeprefix("sqlite:///")
    if path_text.startswith("file:"):
        return
    Path(path_text).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _is_sqlite(database_url: str) -> bool:
    return urlsplit(database_url).scheme.startswith("sqlite")


def build_engine(database_url: str) -> Engine:
    ensure_sqlite_parent(database_url)
    connect_args = {"check_same_thread": False} if _is_sqlite(database_url) else {}
    engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)

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
    ) -> None:
        self.engine = build_engine(database_url)
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
        }
        missing_tables = required_tables - table_names
        missing_columns = REQUIRED_CAMERA_COLUMNS - camera_columns
        missing_audit_columns = REQUIRED_AUDIT_COLUMNS - audit_columns
        missing_stream_columns = REQUIRED_STREAM_COLUMNS - stream_columns
        if (
            missing_tables
            or missing_columns
            or missing_audit_columns
            or missing_stream_columns
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
