from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Request
from sqlalchemy import DateTime, Engine, create_engine, event, inspect, text
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator


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
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(
        self, value: datetime | None, _dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


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
            cursor.close()

    return engine


class Database:
    def __init__(self, database_url: str) -> None:
        self.engine = build_engine(database_url)
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
            table_names = set(inspect(connection).get_table_names())
        required_tables = {"cameras", "audit_events"}
        missing_tables = required_tables - table_names
        if missing_tables:
            raise DatabaseNotReadyError("database migrations are not current")

    def dispose(self) -> None:
        self.engine.dispose()


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.database.session_factory() as session:
        yield session
