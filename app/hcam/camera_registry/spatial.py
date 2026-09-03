from __future__ import annotations

from sqlalchemy import LargeBinary, func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import TypeEngine, UserDefinedType


class PostGISWGS84Point(UserDefinedType[bytes]):
    """A PostGIS WGS84 point exposed to Python as canonical WKB."""

    cache_ok = True

    def get_col_spec(self, **_kw: object) -> str:
        return "geometry(Point,4326)"

    def bind_expression(self, bindvalue):
        return func.ST_GeomFromWKB(bindvalue, 4326)

    def column_expression(self, column):
        return func.ST_AsBinary(column, type_=LargeBinary())


@compiles(PostGISWGS84Point, "sqlite")
def _compile_sqlite(
    _type: PostGISWGS84Point,
    _compiler,
    **_kw: object,
) -> str:
    return "BLOB"


def wgs84_point_type() -> TypeEngine[bytes]:
    return LargeBinary().with_variant(PostGISWGS84Point(), "postgresql")
