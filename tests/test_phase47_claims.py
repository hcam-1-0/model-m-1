import pytest

from hcam.acceptance.canonical import stable_id
from hcam.acceptance.claims import (
    ClaimValidationError,
    build_registers,
    validate_registers,
)


def test_generated_claims_are_evidence_bound_and_limited() -> None:
    component = stable_id("p47", "evidence", "scenario-results")
    claims, limitations = build_registers((component,))
    validate_registers(claims, limitations, component_ids={component})
    assert all(item.status == "limited" for item in claims.claims)
    assert all(item.status == "accepted" for item in limitations.limitations)


def test_claims_reject_missing_evidence_and_prohibited_interpretation() -> None:
    component = stable_id("p47", "evidence", "scenario-results")
    claims, limitations = build_registers((component,))
    with pytest.raises(ClaimValidationError):
        validate_registers(claims, limitations, component_ids=set())
    bad = claims.claims[0].model_copy(
        update={"statement": "This system is production ready for every environment."}
    )
    with pytest.raises(ClaimValidationError):
        validate_registers(
            claims.model_copy(update={"claims": (bad,)}),
            limitations,
            component_ids={component},
        )


def test_claim_builder_requires_evidence() -> None:
    with pytest.raises(ClaimValidationError):
        build_registers(())


def test_claim_cross_references_and_unique_ids_fail_closed() -> None:
    component = stable_id("p47", "evidence", "scenario-results")
    claims, limitations = build_registers((component,))
    with pytest.raises(ClaimValidationError):
        validate_registers(
            claims.model_copy(update={"claims": (claims.claims[0], claims.claims[0])}),
            limitations,
            component_ids={component},
        )
    no_support = claims.claims[0].model_copy(update={"supporting_component_ids": ()})
    with pytest.raises(ClaimValidationError):
        validate_registers(
            claims.model_copy(update={"claims": (no_support,)}),
            limitations,
            component_ids={component},
        )
    missing_limitation = claims.claims[0].model_copy(
        update={"limitation_ids": (stable_id("p47", "limitation", "missing"),)}
    )
    with pytest.raises(ClaimValidationError):
        validate_registers(
            claims.model_copy(update={"claims": (missing_limitation,)}),
            limitations,
            component_ids={component},
        )
    missing_claim = limitations.limitations[0].model_copy(
        update={"affected_claim_ids": (stable_id("p47", "claim", "missing"),)}
    )
    with pytest.raises(ClaimValidationError):
        validate_registers(
            claims,
            limitations.model_copy(update={"limitations": (missing_claim,)}),
            component_ids={component},
        )
