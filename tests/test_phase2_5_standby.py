from __future__ import annotations

from hcam.labs.sentinel import standby


def test_standby_fails_closed_without_explicit_sandbox_flag(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.delenv("HCAM_ALLOW_SENTINEL_SANDBOX", raising=False)

    assert standby.main(["--heartbeat-file", str(tmp_path / "heartbeat")]) == 2
