from __future__ import annotations

from hcam.intelligence.alerts.canonical import digest, stable_id
from hcam.intelligence.alerts.contracts import AlertIdentityV1, ProposedAlertCommandV1


class AlertIdentityConflict(ValueError):
    pass


def derive_alert_identity(command: ProposedAlertCommandV1) -> AlertIdentityV1:
    occurrence = {
        "evaluation_id": command.evaluation_id,
        "evaluation_revision": command.evaluation_revision,
        "evaluation_digest": command.evaluation_digest,
        "rule_record_id": command.rule_record_id,
        "compilation_id": command.compilation_id,
        "department": command.department,
        "partition_digest": command.partition_digest,
        "domain": command.domain,
        "incident_key": command.incident_key,
        "evidence_refs": sorted(command.evidence_refs),
    }
    occurrence_digest = digest(occurrence)
    semantic_key = digest(
        {
            "contract": "hcam.p4-3.semantic-alert-identity.v1",
            "occurrence_digest": occurrence_digest,
        }
    )
    delivery_key = digest(
        {
            "contract": "hcam.p4-3.delivery-idempotency.v1",
            "department": command.department,
            "delivery_id": command.delivery_id,
        }
    )
    return AlertIdentityV1(
        alert_id=stable_id("alt", command.department, semantic_key),
        semantic_key=semantic_key,
        delivery_key=delivery_key,
        occurrence_digest=occurrence_digest,
    )


def assert_same_identity_material(
    existing: AlertIdentityV1, candidate: AlertIdentityV1
) -> None:
    if existing.alert_id != candidate.alert_id:
        raise AlertIdentityConflict("semantic identity does not match")
    if existing.occurrence_digest != candidate.occurrence_digest:
        raise AlertIdentityConflict("same identity has different occurrence material")
