from hcam.acceptance.assertions import evaluate_assertions
from hcam.acceptance.contracts import SideEffectLedgerV1
from hcam.acceptance.fixtures import build_manifest
from hcam.acceptance.scenarios import ScenarioEngine


def test_assertion_families_pass_independently() -> None:
    manifest = build_manifest()
    run = ScenarioEngine(enabled=True).run(
        manifest, manifest.scenarios[0], replay_index=1
    )
    assert len(run.assertions) == 12
    assert all(item.status == "passed" for item in run.assertions)


def test_assertions_fail_closed_on_incomplete_snapshot() -> None:
    scenario = build_manifest().scenarios[0]
    results = evaluate_assertions(
        scenario, (), {"generated_only": False}, SideEffectLedgerV1()
    )
    assert any(item.status == "failed" for item in results)
    assert {item.family for item in results} == {
        "schema",
        "authorization",
        "chronology",
        "identity",
        "rule",
        "review",
        "integrity",
        "redaction",
        "recovery",
        "side_effect",
        "handoff",
        "accessibility",
    }


def test_assertions_reject_prohibited_content_and_nonzero_side_effects() -> None:
    scenario = build_manifest().scenarios[0]
    side_effects = SideEffectLedgerV1.model_construct(network_attempts=1)
    results = evaluate_assertions(
        scenario,
        (),
        {
            "generated_only": True,
            "operational": False,
            "password": "generated",
            "external_effects": 1,
            "direct_persistence_attempts": 0,
        },
        side_effects,
    )
    by_family = {item.family: item.status for item in results}
    assert by_family["redaction"] == "failed"
    assert by_family["side_effect"] == "failed"
