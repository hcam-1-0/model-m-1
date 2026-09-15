from __future__ import annotations

import pytest

from hcam.intelligence.integrations.contracts import DestinationPolicyV1
from hcam.intelligence.integrations.destinations import compile_destination
from hcam.intelligence.integrations.transport import DisabledLoopbackTransport, GeneratedTransportEnvelope
from hcam.intelligence.integrations.policy import compile_query_plan
from tests.test_phase44_contracts import intent, manifest


def test_only_in_process_generated_destination_compiles() -> None:
    destination = DestinationPolicyV1(
        destination_id="generated.destination.local.v1",
        route_id="generated.route.lookup.v1",
    )
    compiled = compile_destination(destination)
    assert compiled.network_allowed is False
    assert compiled.transport == "in_process_generated"


def test_loopback_transport_is_explicitly_disabled() -> None:
    provider = manifest()
    envelope = GeneratedTransportEnvelope(
        plan=compile_query_plan(intent(provider), provider, control_enabled=True),
        parameters={"record_key": "gen_record_001"},
    )
    with pytest.raises(RuntimeError, match="disabled"):
        DisabledLoopbackTransport().execute(envelope)
