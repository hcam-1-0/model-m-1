from __future__ import annotations

from tools.phase1_performance import REPORT_SCHEMA, main, run_performance_smoke


def test_synthetic_performance_smoke_passes_with_small_dataset() -> None:
    report = run_performance_smoke(
        camera_count=50,
        iterations=5,
        max_p95_ms=2000,
        max_import_seconds=10,
    )

    assert report["schema"] == REPORT_SCHEMA
    assert report["passed"] is True
    assert report["dataset"] == {
        "camera_count": 50,
        "synthetic_only": True,
        "video_used": False,
    }
    assert report["import"]["created"] == 50


def test_performance_smoke_rejects_invalid_configuration(capsys) -> None:
    assert main(["--cameras", "0"]) == 2
    assert "must be positive" in capsys.readouterr().err
