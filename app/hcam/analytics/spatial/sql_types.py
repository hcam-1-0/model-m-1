from __future__ import annotations

from sqlalchemy import LargeBinary, func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import TypeEngine, UserDefinedType


class PostGISImageGeometry(UserDefinedType[bytes]):
    """A normalized, SRID-less 2D PostGIS geometry exposed as canonical WKB."""

    cache_ok = True

    def get_col_spec(self, **_kw: object) -> str:
        return "geometry(Geometry,0)"

    def bind_expression(self, bindvalue):
        return func.ST_GeomFromWKB(bindvalue, 0)

    def column_expression(self, column):
        return func.ST_AsBinary(column, type_=LargeBinary())


@compiles(PostGISImageGeometry, "sqlite")
def _compile_sqlite(_type: PostGISImageGeometry, _compiler, **_kw: object) -> str:
    return "BLOB"


def image_geometry_type() -> TypeEngine[bytes]:
    return LargeBinary().with_variant(PostGISImageGeometry(), "postgresql")
