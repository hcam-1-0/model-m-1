from __future__ import annotations

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from hcam import __version__
from hcam.analytics.bootstrap import build_analytics_runtime
from hcam.analytics.tracking import GeneratedTrackingLaneStore
from hcam.analytics import models as _analytics_models  # noqa: F401
from hcam.analytics.routes import router as analytics_router
from hcam.analytics.spatial.routes import router as analytics_spatial_router
from hcam.audit import models as _audit_models  # noqa: F401
from hcam.camera_registry import models as _camera_models  # noqa: F401
from hcam.camera_registry.import_routes import router as import_router
from hcam.camera_registry.gis_routes import router as gis_router
from hcam.camera_registry.routes import router as camera_router
from hcam.database import Database
from hcam.health.routes import router as health_router
from hcam.sandbox_playback import router as sandbox_playback_router
from hcam.intelligence import models as _intelligence_models  # noqa: F401
from hcam.intelligence.alerts.routes import (
    _ProblemException,
    problem_exception_handler,
    router as alert_lifecycle_router,
)
from hcam.intelligence.routes import router as intelligence_router
from hcam.intelligence.integrations.routes import router as reference_integration_router
from hcam.intelligence.integrations.metrics import IntegrationMetrics
from hcam.intelligence.integrations.providers import ProviderRegistry
from hcam.intelligence.integrations.runtime import GeneratedIntegrationRuntime
from hcam.intelligence.investigations import persistence as _investigation_models  # noqa: F401
from hcam.intelligence.investigations.metrics import InvestigationMetrics
from hcam.intelligence.investigations.routes import router as investigation_router
from hcam.intelligence.investigations.runtime import GeneratedInvestigationRuntime
from hcam.metrics import RequestMetrics, router as metrics_router
from hcam.observability import RequestContextMiddleware
from hcam.operations.platform import models as _platform_models  # noqa: F401
from hcam.operations.platform.routes import router as operations_platform_router
from hcam.operations.platform.runtime import GeneratedPlatformRuntime
from hcam.security.auth import build_authenticator
from hcam.security.errors import sanitized_request_validation_error
from hcam.security.request_limits import (
    RequestBodyLimitMiddleware,
    SensitiveResponseHeadersMiddleware,
)
from hcam.settings import Settings
from hcam.streams import models as _stream_models  # noqa: F401
from hcam.streams.routes import router as stream_router


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
        pool_size=resolved_settings.db_pool_size,
        max_overflow=resolved_settings.db_max_overflow,
        pool_timeout=resolved_settings.db_pool_timeout,
        pool_recycle=resolved_settings.db_pool_recycle,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if resolved_settings.create_schema:
            database.create_schema()
        yield
        database.dispose()

    application = FastAPI(
        title=resolved_settings.service_name,
        version=__version__,
        description="H-CAM camera registry and stream management foundation.",
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.state.database = database
    application.state.authenticator = build_authenticator(resolved_settings)
    (
        application.state.analytics_runtime,
        application.state.analytics_frame_leases,
    ) = build_analytics_runtime(resolved_settings)
    application.state.analytics_tracking_lanes = GeneratedTrackingLaneStore()
    application.state.reference_integration_runtime = GeneratedIntegrationRuntime(
        enabled=resolved_settings.intelligence_generated_reference_integrations_enabled,
        environment=resolved_settings.environment,
    )
    application.state.reference_provider_registry = ProviderRegistry()
    application.state.reference_integration_metrics = IntegrationMetrics()
    application.state.investigation_runtime = GeneratedInvestigationRuntime(
        enabled=resolved_settings.intelligence_generated_investigations_enabled,
        environment=resolved_settings.environment,
    )
    application.state.investigation_metrics = InvestigationMetrics()
    application.state.operations_platform_runtime = GeneratedPlatformRuntime(
        enabled=resolved_settings.operations_generated_platform_enabled,
        environment=resolved_settings.environment,
        unified_search_enabled=resolved_settings.operations_unified_search_enabled,
        otel_export_enabled=resolved_settings.operations_otel_export_enabled,
        external_broker_enabled=resolved_settings.operations_external_broker_enabled,
        kubernetes_execution_enabled=resolved_settings.operations_kubernetes_execution_enabled,
    )
    application.state.request_metrics = RequestMetrics(
        service_name=resolved_settings.service_name,
        version=__version__,
    )
    application.add_exception_handler(
        RequestValidationError,
        sanitized_request_validation_error,
    )
    application.add_exception_handler(_ProblemException, problem_exception_handler)
    application.add_middleware(
        RequestBodyLimitMiddleware,
        max_bytes=resolved_settings.max_request_body_bytes,
    )
    application.add_middleware(SensitiveResponseHeadersMiddleware)
    application.add_middleware(
        RequestContextMiddleware,
        access_log_enabled=resolved_settings.access_log_enabled,
        metrics_recorder=application.state.request_metrics,
    )
    if os.getenv("HCAM_ALLOW_LAB_WHEP_SANDBOX", "").lower() == "true":
        # LAB / SANDBOX / LOCAL TEST ONLY. The production application never adds CORS.
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["http://127.0.0.1:3001"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type"],
        )
    application.include_router(health_router)
    application.include_router(sandbox_playback_router)
    application.include_router(metrics_router)
    application.include_router(camera_router)
    application.include_router(gis_router)
    application.include_router(import_router)
    application.include_router(stream_router)
    application.include_router(analytics_router)
    application.include_router(analytics_spatial_router)
    if (
        resolved_settings.intelligence_generated_control_plane_enabled
        or resolved_settings.intelligence_generated_correlation_enabled
        or resolved_settings.intelligence_generated_rule_evaluation_enabled
        or resolved_settings.intelligence_generated_alert_lifecycle_enabled
    ):
        application.include_router(intelligence_router)
    if resolved_settings.intelligence_generated_alert_lifecycle_enabled:
        application.include_router(alert_lifecycle_router)
    if resolved_settings.intelligence_generated_reference_integrations_enabled:
        application.include_router(reference_integration_router)
    if resolved_settings.intelligence_generated_investigations_enabled:
        application.include_router(investigation_router)
    if resolved_settings.operations_generated_platform_enabled:
        application.include_router(operations_platform_router)
    return application


app = create_app()
