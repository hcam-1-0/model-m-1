from __future__ import annotations

from tools.phase1_load import REPORT_SCHEMA, main, run_concurrent_load_smoke


def test_concurrent_load_smoke_uses_loopback_synthetic_data() -> None:
    report = run_concurrent_load_smoke(
        camera_count=25,
        request_count=20,
        concurrency=4,
        max_p95_ms=3000,
        max_error_rate=0,
    )

    assert report["schema"] == REPORT_SCHEMA
    assert report["passed"] is True
    assert report["load"]["request_count"] == 20
    assert report["load"]["errors"] == 0
    assert report["scope"] == {
        "transport": "loopback-http",
        "synthetic_only": True,
        "video_used": False,
        "external_network_used": False,
    }


def test_concurrent_load_smoke_rejects_invalid_configuration(capsys) -> None:
    assert main(["--requests", "2", "--concurrency", "3"]) == 2
    assert "must not exceed" in capsys.readouterr().err
    assert main(["--max-p95-ms", "nan"]) == 2
    assert "thresholds are invalid" in capsys.readouterr().err
