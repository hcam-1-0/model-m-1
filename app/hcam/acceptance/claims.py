from __future__ import annotations

from collections.abc import Sequence

from hcam.acceptance.canonical import stable_id
from hcam.acceptance.contracts import (
    ClaimRecordV1,
    ClaimRegisterV1,
    EvidenceIndexV1,
    LimitationRecordV1,
    LimitationRegisterV1,
)


PROHIBITED_CLAIM_TERMS = (
    "production ready",
    "operationally ready",
    "standards compliant",
    "legally admissible",
    "real-world accuracy",
)


class ClaimValidationError(ValueError):
    """Raised when a claim exceeds generated-only evidence."""


def _claim_id(name: str) -> str:
    return stable_id("p47", "claim", name)


def _limitation_id(name: str) -> str:
    return stable_id("p47", "limitation", name)


def build_registers(
    component_ids: Sequence[str],
) -> tuple[ClaimRegisterV1, LimitationRegisterV1]:
    support = tuple(sorted(component_ids))
    if not support:
        raise ClaimValidationError("at least one evidence component is required")
    runtime_limitation = _limitation_id("generated-runtime")
    external_limitation = _limitation_id("external-systems")
    accessibility_limitation = _limitation_id("accessibility")
    claims = (
        ClaimRecordV1(
            claim_id=_claim_id("determinism"),
            statement="The mandatory generated scenarios replay deterministically under the pinned manifest.",
            scope="p4.7.generated_replay",
            evidence_class="generated_scenario",
            supporting_component_ids=support,
            limitation_ids=(runtime_limitation,),
            status="limited",
            prohibited_interpretations=(
                "production_performance",
                "external_system_behavior",
            ),
        ),
        ClaimRecordV1(
            claim_id=_claim_id("side-effects"),
            statement="The generated scenario boundary records zero prohibited external side effects.",
            scope="p4.7.generated_boundary",
            evidence_class="generated_scenario",
            supporting_component_ids=support,
            limitation_ids=(external_limitation,),
            status="limited",
            prohibited_interpretations=("network_validation", "provider_validation"),
        ),
        ClaimRecordV1(
            claim_id=_claim_id("handoff"),
            statement="The Phase 5 handoff catalogues are internally complete for the declared generated contract scope.",
            scope="p4.7.consumer_handoff",
            evidence_class="generated_contract",
            supporting_component_ids=support,
            limitation_ids=(accessibility_limitation,),
            status="limited",
            prohibited_interpretations=(
                "ui_implementation",
                "accessibility_conformance",
            ),
        ),
    )
    limitations = (
        LimitationRecordV1(
            limitation_id=runtime_limitation,
            statement="Validation uses deterministic generated state and does not measure a deployed runtime.",
            impact="high",
            mitigation="Keep all claims explicitly bounded to generated scenario evidence.",
            required_future_evidence=(
                "owned_runtime_validation",
                "accepted_capacity_targets",
            ),
            owner="mayank-admin",
            affected_claim_ids=(_claim_id("determinism"),),
            status="accepted",
        ),
        LimitationRecordV1(
            limitation_id=external_limitation,
            statement="No provider, network, camera, media, model, or operational system is exercised.",
            impact="high",
            mitigation="Retain default-off adapters and require later scoped integration authorization.",
            required_future_evidence=(
                "owned_integration_validation",
                "approved_data_governance",
            ),
            owner="mayank-admin",
            affected_claim_ids=(_claim_id("side-effects"),),
            status="accepted",
        ),
        LimitationRecordV1(
            limitation_id=accessibility_limitation,
            statement="Accessibility requirements are handoff contracts and have no implemented user interface evidence.",
            impact="medium",
            mitigation="Require Phase 5 component, keyboard, screen-reader, contrast, and motion validation.",
            required_future_evidence=("implemented_ui", "manual_accessibility_review"),
            owner="mayank-admin",
            affected_claim_ids=(_claim_id("handoff"),),
            status="accepted",
        ),
    )
    registers = (
        ClaimRegisterV1(claims=claims),
        LimitationRegisterV1(limitations=limitations),
    )
    validate_registers(*registers, component_ids=set(support))
    return registers


def validate_registers(
    claims: ClaimRegisterV1,
    limitations: LimitationRegisterV1,
    *,
    component_ids: set[str],
) -> None:
    limitation_by_id = {item.limitation_id: item for item in limitations.limitations}
    claim_ids = {item.claim_id for item in claims.claims}
    if len(claim_ids) != len(claims.claims) or len(limitation_by_id) != len(
        limitations.limitations
    ):
        raise ClaimValidationError("claim and limitation IDs must be unique")
    for claim in claims.claims:
        normalized = claim.statement.lower()
        if any(term in normalized for term in PROHIBITED_CLAIM_TERMS):
            raise ClaimValidationError(
                "claim uses a prohibited operational interpretation"
            )
        if (
            claim.status in {"supported", "limited"}
            and not claim.supporting_component_ids
        ):
            raise ClaimValidationError("supported claims require evidence")
        if set(claim.supporting_component_ids) - component_ids:
            raise ClaimValidationError("claim references missing evidence")
        if set(claim.limitation_ids) - set(limitation_by_id):
            raise ClaimValidationError("claim references a missing limitation")
    for limitation in limitations.limitations:
        if set(limitation.affected_claim_ids) - claim_ids:
            raise ClaimValidationError("limitation references a missing claim")


def validate_against_evidence(
    claims: ClaimRegisterV1,
    limitations: LimitationRegisterV1,
    evidence: EvidenceIndexV1,
) -> None:
    validate_registers(
        claims,
        limitations,
        component_ids={item.component_id for item in evidence.components},
    )
