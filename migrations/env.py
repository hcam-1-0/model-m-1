from __future__ import annotations

from collections.abc import Callable
from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

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

IncludeObject = Callable[[Any, str, str, bool, Any], bool]


def _extension_owned_relations(connection: Connection) -> set[tuple[str, str]]:
    """Return relations managed by installed PostGIS-family extensions."""
    if connection.dialect.name != "postgresql":
        return set()
    rows = connection.exec_driver_sql(
        """
        SELECT namespace.nspname, relation.relname
        FROM pg_catalog.pg_depend AS dependency
        JOIN pg_catalog.pg_extension AS extension
          ON extension.oid = dependency.refobjid
        JOIN pg_catalog.pg_class AS relation
          ON relation.oid = dependency.objid
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = relation.relnamespace
        WHERE dependency.deptype = 'e'
          AND extension.extname IN (
            'postgis',
            'postgis_topology',
            'postgis_tiger_geocoder',
            'fuzzystrmatch'
          )
        UNION
        SELECT namespace.nspname, relation.relname
        FROM pg_catalog.pg_extension AS extension
        CROSS JOIN LATERAL unnest(extension.extconfig)
          AS configured(relation_oid)
        JOIN pg_catalog.pg_class AS relation
          ON relation.oid = configured.relation_oid
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = relation.relnamespace
        WHERE extension.extname IN (
          'postgis',
          'postgis_topology',
          'postgis_tiger_geocoder',
          'fuzzystrmatch'
        )
        """
    )
    return {(str(schema), str(name)) for schema, name in rows}


def _include_application_object(
    extension_relations: set[tuple[str, str]],
    default_schema: str,
) -> IncludeObject:
    """Exclude extension-managed relations from Alembic drift comparison."""

    def include_object(
        object_: Any,
        name: str,
        type_: str,
        reflected: bool,
        compare_to: Any,
    ) -> bool:
        del compare_to
        if not reflected:
            return True
        table = object_ if type_ == "table" else getattr(object_, "table", None)
        if table is None:
            return True
        schema = getattr(table, "schema", None) or default_schema
        table_name = getattr(table, "name", None) or name
        return (str(schema), str(table_name)) not in extension_relations

    return include_object


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    # Query extension ownership on a separate connection. PostgreSQL begins a
    # transaction for this catalogue read, and reusing that connection would
    # prevent Alembic from owning and committing its migration transaction.
    with connectable.connect() as inspection_connection:
        extension_relations = _extension_owned_relations(inspection_connection)
    with connectable.connect() as connection:
        default_schema = connection.dialect.default_schema_name or "public"
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=_include_application_object(
                extension_relations,
                default_schema,
            ),
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
