from __future__ import annotations

from copy import deepcopy

import pytest

from hcam.intelligence.alerts.contracts import ProposedAlertCommandV1
from hcam.intelligence.alerts.identity import (
    AlertIdentityConflict,
    assert_same_identity_material,
    derive_alert_identity,
)
from tests.test_phase43_contracts import proposal


def test_semantic_identity_is_distinct_from_delivery_idempotency() -> None:
    first = ProposedAlertCommandV1.model_validate(proposal())
    redelivery = ProposedAlertCommandV1.model_validate(
        {**proposal(), "delivery_id": "generated.delivery.2"}
    )
    a = derive_alert_identity(first)
    b = derive_alert_identity(redelivery)
    assert a.alert_id == b.alert_id
    assert a.semantic_key == b.semantic_key
    assert a.delivery_key != b.delivery_key
    assert a.occurrence_digest == b.occurrence_digest


def test_semantic_material_change_produces_a_different_identity() -> None:
    first = derive_alert_identity(ProposedAlertCommandV1.model_validate(proposal()))
    changed = deepcopy(proposal())
    changed["incident_key"] = "generated.incident.2"
    second = derive_alert_identity(ProposedAlertCommandV1.model_validate(changed))
    assert first.alert_id != second.alert_id
    with pytest.raises(AlertIdentityConflict):
        assert_same_identity_material(first, second)


def test_same_alert_id_with_different_occurrence_material_fails_closed() -> None:
    identity = derive_alert_identity(ProposedAlertCommandV1.model_validate(proposal()))
    changed = identity.model_copy(update={"occurrence_digest": "sha256:" + "f" * 64})
    with pytest.raises(AlertIdentityConflict, match="different occurrence"):
        assert_same_identity_material(identity, changed)
