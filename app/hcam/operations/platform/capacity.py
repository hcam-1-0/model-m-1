from __future__ import annotations

from hcam.operations.platform.canonical import stable_id
from hcam.operations.platform.contracts import CapacityRunV1, CapabilityProfileV1
from hcam.operations.platform.registry import CAPACITY_SCALES


MODE_WEIGHTS = {
    "latency": (0.75, 0.55),
    "balanced": (1.0, 1.0),
    "throughput": (1.35, 1.6),
}


def simulate_capacity(
    profile: CapabilityProfileV1,
    *,
    scale: str,
    mode: str,
    steps: int = 100,
    fail_after: int | None = None,
) -> CapacityRunV1:
    if scale not in CAPACITY_SCALES or mode not in MODE_WEIGHTS:
        raise ValueError("capacity scenario is not registered")
    if not 1 <= steps <= 100_000:
        raise ValueError("capacity step count is outside bounds")
    completed = steps if fail_after is None else max(0, min(fail_after, steps - 1))
    status = "complete" if completed == steps else "incomplete"
    streams = CAPACITY_SCALES[scale]
    latency_weight, throughput_weight = MODE_WEIGHTS[mode]
    compute = profile.cpu_units + profile.accelerator_units * 16
    pressure = streams / max(compute, 1)
    saturation = min(1.0, pressure * latency_weight)
    loss = 0 if saturation < 0.95 else int(streams * saturation)
    if status == "complete":
        p50 = round(8.0 + 120.0 * pressure * latency_weight, 3)
        p95 = round(p50 * 1.8, 3)
        throughput = round(compute * throughput_weight / max(streams, 1), 3)
    else:
        p50 = p95 = throughput = None
    return CapacityRunV1(
        run_id=stable_id("ref", profile.profile_id, scale, mode, steps, completed),
        profile_id=profile.profile_id,
        scale=scale,
        mode=mode,
        steps=steps,
        completed_steps=completed,
        latency_ms_p50=p50,
        latency_ms_p95=p95,
        throughput_per_second=throughput,
        backlog_high_water=max(0, int(streams * saturation * 4)),
        saturation_ratio=saturation,
        loss_count=loss,
        recovery_steps=max(0, int(saturation * 10)),
        resource_projection={
            "cpu_units": float(profile.cpu_units),
            "memory_mib": float(profile.memory_mib),
            "accelerator_units": float(profile.accelerator_units),
        },
        limitations=["capacity.generated_simulation_only", "capacity.hardware_not_tested"],
        status=status,
    )
