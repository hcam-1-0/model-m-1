from hcam.acceptance.bounds import REQUIRED_SCENARIO_IDS
from hcam.acceptance.fixtures import build_manifest, fixture_documents, pairwise_cases


def test_fixture_portfolio_is_exact_and_generated_only() -> None:
    manifest = build_manifest()
    assert (
        tuple(item.scenario_id for item in manifest.scenarios) == REQUIRED_SCENARIO_IDS
    )
    assert all(
        item.generated_only and not item.operational for item in manifest.scenarios
    )
    assert len(manifest.fixture_digests) == 9


def test_pairwise_fixture_inventory_is_bounded_and_deterministic() -> None:
    first = pairwise_cases()
    assert len(first) == 512
    assert first == pairwise_cases()
    assert {item["expected"] for item in first} == {"accepted_or_degraded", "denied"}


def test_fixture_documents_are_complete() -> None:
    documents = fixture_documents()
    assert set(documents) == {
        "generated-scenario-manifest-v1.json",
        "generated-scenario-fixtures-v1.json",
        "generated-expected-outcomes-v1.json",
        "generated-pairwise-cases-v1.json",
    }
    assert documents["generated-pairwise-cases-v1.json"]["case_count"] == 512
