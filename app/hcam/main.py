from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from hcam.audit import models as _audit_models  # noqa: F401
from hcam.camera_registry import models as _camera_models  # noqa: F401
from hcam.camera_registry.routes import router as camera_router
from hcam.database import Database
from hcam.health.routes import router as health_router
from hcam.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_environment()
    database = Database(resolved_settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if resolved_settings.create_schema:
            database.create_schema()
        yield
        database.dispose()

    application = FastAPI(
        title="H-CAM Core API",
        version="0.1.0",
        description="Phase 1 camera registry backend foundation.",
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.state.database = database
    application.include_router(health_router)
    application.include_router(camera_router)
    return application


app = create_app()
