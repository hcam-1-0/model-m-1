from __future__ import annotations

from dataclasses import dataclass

from hcam.intelligence.integrations.contracts import DestinationPolicyV1


class DestinationPolicyError(RuntimeError):
    reason_code = "destination_policy_denied"


@dataclass(frozen=True, slots=True)
class CompiledDestination:
    destination_id: str
    route_id: str
    transport: str = "in_process_generated"
    network_allowed: bool = False


def compile_destination(policy: DestinationPolicyV1) -> CompiledDestination:
    if (
        policy.transport != "in_process_generated"
        or policy.network_allowed
        or policy.redirects_allowed
        or policy.environment_proxies_allowed
    ):
        raise DestinationPolicyError("only the generated in-process destination is allowed")
    return CompiledDestination(
        destination_id=policy.destination_id,
        route_id=policy.route_id,
    )
