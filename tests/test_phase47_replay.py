import pytest

from hcam.acceptance.fixtures import build_manifest
from hcam.acceptance.replay import build_reconstruction_manifest, run_portfolio
from hcam.acceptance.scenarios import ScenarioEngine


def test_portfolio_runs_two_clean_replays_and_reconstructs() -> None:
    portfolio = run_portfolio(ScenarioEngine(enabled=True), build_manifest())
    assert portfolio.complete
    assert len(portfolio.runs) == 18
    assert all(item.equal for item in portfolio.comparisons)
    reconstruction = build_reconstruction_manifest(portfolio.runs[0])
    assert reconstruction.chronology_complete
    assert len(reconstruction.entries) == len(portfolio.runs[0].observations)


def test_portfolio_rejects_incomplete_inventory() -> None:
    manifest = build_manifest()
    with pytest.raises(ValueError):
        run_portfolio(
            ScenarioEngine(enabled=True),
            manifest.model_copy(update={"scenarios": manifest.scenarios[:-1]}),
        )
