import pytest

from hcam.operations.platform.canonical import digest
from hcam.operations.platform.capacity import simulate_capacity
from hcam.operations.platform.contracts import CapabilityProfileV1


def _profile() -> CapabilityProfileV1:
    payload = {"profile": "generated", "cpu": 8, "memory": 16384}
    return CapabilityProfileV1(
        profile_id="ref_" + "1" * 32,
        profile_class="developer_laptop",
        state="declared",
        cpu_units=8,
        memory_mib=16384,
        accelerator_units=0,
        capabilities=frozenset({"cpu:generic"}),
        profile_digest=digest(payload),
    )


@pytest.mark.parametrize("scale", ["C1", "C10", "C50"])
@pytest.mark.parametrize("mode", ["latency", "balanced", "throughput"])
def test_capacity_matrix_is_deterministic_and_generated(scale: str, mode: str) -> None:
    first = simulate_capacity(_profile(), scale=scale, mode=mode)
    second = simulate_capacity(_profile(), scale=scale, mode=mode)
    assert first == second
    assert first.status == "complete"
    assert first.hardware_tested is False


def test_incomplete_run_does_not_publish_measurements() -> None:
    result = simulate_capacity(_profile(), scale="C50", mode="throughput", fail_after=10)
    assert result.status == "incomplete"
    assert result.latency_ms_p95 is None
    assert result.throughput_per_second is None


@pytest.mark.parametrize(
    ("scale", "mode", "steps"),
    [
        ("C2", "balanced", 100),
        ("C1", "unbounded", 100),
        ("C1", "balanced", 0),
        ("C1", "balanced", 100_001),
    ],
)
def test_capacity_rejects_unknown_or_unbounded_scenarios(scale: str, mode: str, steps: int) -> None:
    with pytest.raises(ValueError):
        simulate_capacity(_profile(), scale=scale, mode=mode, steps=steps)


def test_capacity_clamps_interrupted_progress() -> None:
    assert simulate_capacity(_profile(), scale="C1", mode="latency", fail_after=-1).completed_steps == 0
