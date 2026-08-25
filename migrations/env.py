from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, engine_from_config, pool, text
from sqlalchemy.dialects.postgresql.base import ischema_names

from hcam.analytics import models as _analytics_models  # noqa: F401
from hcam.analytics.spatial.sql_types import PostGISImageGeometry
from hcam.audit import models as _audit_models  # noqa: F401
from hcam.camera_registry import models as _camera_models  # noqa: F401
from hcam.database import Base, ensure_sqlite_parent
from hcam.settings import database_url_from_environment
from hcam.streams import models as _stream_models  # noqa: F401


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

database_url = database_url_from_environment(config.get_main_option("sqlalchemy.url"))
config.set_main_option("sqlalchemy.url", database_url)
ensure_sqlite_parent(database_url)
target_metadata = Base.metadata
extension_owned_table_names: frozenset[str] = frozenset()

# PostgreSQL exposes PostGIS as a user-defined type. Registering it here keeps
# migration reflection exact without adding a runtime GeoAlchemy dependency.
ischema_names.setdefault("geometry", PostGISImageGeometry)


def include_name(
    name: str | None,
    type_: str,
    _parent_names: dict[str, str | None],
) -> bool:
    """Keep extension-owned tables out of H-CAM migration comparisons."""

    if type_ == "table" and name not in target_metadata.tables:
        return name not in extension_owned_table_names
    return True


def include_object(
    object_: object,
    _name: str | None,
    _type: str,
    reflected: bool,
    _compare_to: object | None,
) -> bool:
    """Exclude metadata objects that do not apply to the active dialect."""

    if reflected:
        return True
    info = getattr(object_, "info", {})
    dialects = info.get("hcam_autogenerate_dialects", ())
    return not dialects or context.get_context().dialect.name in dialects


def load_extension_owned_table_names(connection: Connection) -> frozenset[str]:
    """Return PostgreSQL table names owned by installed extensions."""

    if connection.dialect.name != "postgresql":
        return frozenset()
    rows = connection.execute(
        text(
            "SELECT c.relname FROM pg_catalog.pg_depend AS d "
            "JOIN pg_catalog.pg_extension AS e ON e.oid = d.refobjid "
            "JOIN pg_catalog.pg_class AS c ON c.oid = d.objid "
            "WHERE d.deptype = 'e' AND c.relkind IN ('r', 'p')"
        )
    )
    return frozenset(str(row[0]) for row in rows)


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_name=include_name,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    global extension_owned_table_names

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_name=include_name,
            include_object=include_object,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            extension_owned_table_names = load_extension_owned_table_names(connection)
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
