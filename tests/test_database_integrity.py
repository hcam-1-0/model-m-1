from __future__ import annotations

import pytest
from sqlalchemy import text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from hcam.camera_registry.models import Camera


@pytest.mark.parametrize(
    "values",
    [
        {"latitude": 91.0},
        {"longitude": -181.0},
        {"longitude": None},
        {"duration_seconds": -0.1},
        {"version_id": 0},
    ],
)
def test_database_rejects_invalid_camera_state(imported_app, values: dict) -> None:
    with imported_app.state.database.session_factory() as session:
        with pytest.raises(IntegrityError), session.begin():
            session.execute(
                update(Camera)
                .where(Camera.camera_id == "synthetic:cctv-001")
                .values(**values)
            )


def test_database_optimistic_concurrency_rejects_second_writer(imported_app) -> None:
    first_session = imported_app.state.database.session_factory()
    second_session = imported_app.state.database.session_factory()
    try:
        first = first_session.get(Camera, "synthetic:cctv-001")
        second = second_session.get(Camera, "synthetic:cctv-001")
        assert first is not None
        assert second is not None

        first.display_name = "First Writer"
        first_session.commit()

        second.display_name = "Second Writer"
        with pytest.raises(StaleDataError):
            second_session.commit()
    finally:
        first_session.close()
        second_session.close()


def test_sqlite_connection_has_bounded_write_wait(imported_app) -> None:
    with imported_app.state.database.engine.connect() as connection:
        timeout_ms = connection.scalar(text("PRAGMA busy_timeout"))

    assert timeout_ms == 5000
