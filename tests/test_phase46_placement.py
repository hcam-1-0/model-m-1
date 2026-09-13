from hcam.operations.platform.canonical import digest
from hcam.operations.platform.contracts import CapabilityProfileV1, PlacementRequestV1, PlacementServiceV1
from hcam.operations.platform.kubernetes_projection import project_kubernetes
from hcam.operations.platform.placement import build_placement_plan
from hcam.operations.platform.standalone_projection import project_standalone


def _profile(identifier: str, profile_class: str, capabilities: set[str], accelerator: int = 0) -> CapabilityProfileV1:
    return CapabilityProfileV1(
        profile_id="ref_" + identifier * 32,
        profile_class=profile_class,
        state="declared",
        cpu_units=16,
        memory_mib=32768,
        accelerator_units=accelerator,
        capabilities=frozenset(capabilities),
        profile_digest=digest({"id": identifier}),
    )


def test_placement_prefers_capable_accelerated_profile_and_bypasses_optional_lane() -> None:
    request = PlacementRequestV1(
        request_id="ref_" + "9" * 32,
        profiles=[
            _profile("1", "developer_laptop", {"cpu:generic"}),
            _profile("2", "owned_gpu_lab", {"cpu:generic", "gpu:generated"}, 1),
        ],
        services=[
            PlacementServiceV1(service_id="generated:core", cpu_units=2, memory_mib=1024, accelerator_units=1, mandatory_capabilities=frozenset({"gpu:generated"})),
            PlacementServiceV1(service_id="generated:optional", cpu_units=2, memory_mib=1024, accelerator_units=0, mandatory_capabilities=frozenset({"future:missing"}), optional=True),
        ],
    )
    plan = build_placement_plan(request)
    assert [item.reason for item in plan.decisions] == ["placed", "optional_lane_bypassed"]
    standalone = project_standalone(plan)
    kubernetes = project_kubernetes(plan)
    assert standalone["process_execution_enabled"] is False
    assert kubernetes["spec"]["apply"] is False
    assert kubernetes["spec"]["scheduler_execution"] is False


def test_placement_reports_unknown_missing_and_exhausted_requirements() -> None:
    unknown_profile = _profile("3", "server_node", {"cpu:generic"}).model_copy(
        update={"state": "unknown"}
    )
    small_profile = _profile("4", "developer_laptop", {"cpu:generic"}).model_copy(
        update={"cpu_units": 1, "memory_mib": 256}
    )
    request = PlacementRequestV1(
        request_id="ref_" + "8" * 32,
        profiles=[unknown_profile, small_profile],
        services=[
            PlacementServiceV1(
                service_id="generated:unknown",
                cpu_units=1,
                memory_mib=256,
                accelerator_units=0,
                mandatory_capabilities=frozenset({"future:unknown"}),
            ),
            PlacementServiceV1(
                service_id="generated:exhausted",
                cpu_units=2,
                memory_mib=512,
                accelerator_units=0,
                mandatory_capabilities=frozenset({"cpu:generic"}),
            ),
        ],
    )
    assert [item.reason for item in build_placement_plan(request).decisions] == [
        "capacity_exhausted",
        "capability_unknown",
    ]
    unsupported_request = request.model_copy(
        update={
            "profiles": [unknown_profile.model_copy(update={"state": "unsupported"})],
            "services": [request.services[0]],
        }
    )
    assert build_placement_plan(unsupported_request).decisions[0].reason == "mandatory_capability_missing"
