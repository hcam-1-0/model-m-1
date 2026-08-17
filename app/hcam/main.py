from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from hcam import __version__
from hcam.audit import models as _audit_models  # noqa: F401
from hcam.camera_registry import models as _camera_models  # noqa: F401
from hcam.camera_registry.import_routes import router as import_router
from hcam.camera_registry.routes import router as camera_router
from hcam.database import Database
from hcam.health.routes import router as health_router
from hcam.security.auth import build_authenticator
from hcam.security.request_limits import (
    RequestBodyLimitMiddleware,
    SensitiveResponseHeadersMiddleware,
)
from hcam.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_environment()
    if (
        resolved_settings.create_schema
        and resolved_settings.environment.strip().lower() == "production"
    ):
        raise RuntimeError("Automatic schema creation is forbidden in production")
    database = Database(
        resolved_settings.database_url,
        allow_unversioned_schema=resolved_settings.create_schema,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if resolved_settings.create_schema:
            database.create_schema()
        yield
        database.dispose()

    application = FastAPI(
        title="H-CAM Core API",
        version=__version__,
        description="Phase 1 camera registry backend foundation.",
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.state.database = database
    application.state.authenticator = build_authenticator(resolved_settings)
    application.add_middleware(
        RequestBodyLimitMiddleware,
        max_bytes=resolved_settings.max_request_body_bytes,
    )
    application.add_middleware(SensitiveResponseHeadersMiddleware)
    application.include_router(health_router)
    application.include_router(camera_router)
    application.include_router(import_router)
    return application


app = create_app()
