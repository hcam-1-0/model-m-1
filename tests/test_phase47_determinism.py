from datetime import UTC, datetime

import pytest

from hcam.acceptance.determinism import (
    DeterminismError,
    IdentifierProvider,
    LogicalClock,
    compare_replays,
)
from hcam.acceptance.fixtures import build_manifest
from hcam.acceptance.scenarios import ScenarioEngine


def test_logical_clock_and_identifiers_are_deterministic() -> None:
    clock = LogicalClock(datetime(2026, 1, 1, tzinfo=UTC))
    assert clock.advance(1_000).isoformat() == "2026-01-01T00:00:01+00:00"
    provider = IdentifierProvider("generated.p47", 1)
    assert provider.issue("a") == provider.issue("a")
    with pytest.raises(DeterminismError):
        clock.advance(-1)
    with pytest.raises(DeterminismError):
        clock.advance(86_400_001)


def test_replay_comparison_rejects_wrong_order_and_scenario() -> None:
    manifest = build_manifest()
    engine = ScenarioEngine(enabled=True)
    first = engine.run(manifest, manifest.scenarios[0], replay_index=1)
    second = engine.run(manifest, manifest.scenarios[0], replay_index=2)
    assert compare_replays(first, second).equal is True
    with pytest.raises(DeterminismError):
        compare_replays(second, first)
    other = engine.run(manifest, manifest.scenarios[1], replay_index=2)
    with pytest.raises(DeterminismError):
        compare_replays(first, other)
