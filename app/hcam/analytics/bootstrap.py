from __future__ import annotations

from hcam.analytics.artifacts import DET_R0_SHA256
from hcam.analytics.generated import GeneratedFrameLeaseStore
from hcam.analytics.runtime import (
    AnalyticsRuntimeAdapter,
    GuardedAnalyticsRuntimeAdapter,
    RuntimeAdapterDescriptorV1,
    UnavailableAnalyticsRuntimeAdapter,
)
from hcam.analytics.yolox import build_yolox_cpu_adapter
from hcam.settings import Settings


def build_analytics_runtime(
    settings: Settings,
) -> tuple[AnalyticsRuntimeAdapter, GeneratedFrameLeaseStore]:
    leases = GeneratedFrameLeaseStore()
    if not settings.analytics_generated_runtime_enabled:
        unavailable = UnavailableAnalyticsRuntimeAdapter(
            RuntimeAdapterDescriptorV1(
                adapter_id="hcam.yolox_tiny.onnxruntime_cpu",
                adapter_version=f"sha256:{DET_R0_SHA256.lower()}",
                supported_capabilities=["object_detection"],
                maximum_batch_size=1,
                configured=False,
            )
        )
        return GuardedAnalyticsRuntimeAdapter(unavailable), leases
    if settings.analytics_artifact_root is None:
        raise RuntimeError("analytics artifact root is required")
    adapter = build_yolox_cpu_adapter(
        artifact_root=settings.analytics_artifact_root,
        relative_model_path=settings.analytics_model_relative_path,
        frame_resolver=leases,
    )
    return GuardedAnalyticsRuntimeAdapter(adapter), leases
