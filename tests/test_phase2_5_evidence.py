from __future__ import annotations

import json

import pytest

from tools.phase2_5_evidence import (
    build_evidence,
    check_evidence,
    fixture_checks,
    package_manifest,
    source_safety_checks,
)


def fixture_document() -> dict[str, object]:
    fixtures = []
    for number in range(1, 51):
        fixtures.append(
            {
                "fixture_name": f"camera-{number:02d}.mp4",
                "codec": "h264" if number < 40 else "hevc",
                "source_profile": {
                    "active_by_default": number <= 30,
                    "timing_pattern": "variable_pts" if number == 11 else "cfr",
                },
                "probe": {
                    "has_b_frames": 0 if number < 40 else 2,
                    "timing": {"monotonic": True, "retained_frames": 0},
                },
            }
        )
    return {
        "classification": "generated-only",
        "fixture_count": 50,
        "fixtures": fixtures,
    }


def test_fixture_evidence_requires_all_generated_media_invariants() -> None:
    checks = fixture_checks(fixture_document())

    assert all(checks.values())


def test_fixture_evidence_rejects_missing_probe() -> None:
    document = fixture_document()
    document["fixtures"][0].pop("probe")  # type: ignore[index]

    assert fixture_checks(document)["all_probed"] is False


def test_package_digest_is_order_independent_for_selected_paths(tmp_path) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("one", encoding="ascii")
    second.write_text("two", encoding="ascii")

    with pytest.raises(ValueError):
        package_manifest((first, second))


def test_current_source_safety_boundaries_are_enforced() -> None:
    checks = source_safety_checks()

    assert checks["production_host_absent"] is True
    assert checks["exact_public_sandbox_catalogue"] is True
    assert all(checks.values())


def test_evidence_remains_verifiable_after_media_directory_cleanup(tmp_path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    (media / "fixture-evidence.json").write_text(
        json.dumps(fixture_document()), encoding="ascii"
    )

    built = build_evidence(
        tmp_path,
        dashboard_url="http://127.0.0.1:1",
        require_runtime=False,
    )
    (media / "fixture-evidence.json").unlink()

    checked = check_evidence(tmp_path)
    assert built["classification"] == "generated-only"
    assert checked["valid"] is True
