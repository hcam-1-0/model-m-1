from __future__ import annotations

from pathlib import Path

import pytest

from hcam.analytics.bootstrap import build_analytics_runtime
from hcam.settings import Settings


def test_generated_runtime_is_default_off() -> None:
    runtime, leases = build_analytics_runtime(Settings(environment="test"))

    assert runtime.descriptor.configured is False
    assert runtime.descriptor.network_access == "denied"
    assert runtime.descriptor.artifact_access == "verified_handle_only"
    assert leases.active_leases == 0


def test_generated_runtime_requires_artifact_root() -> None:
    with pytest.raises(ValueError, match="ARTIFACT_ROOT"):
        Settings(
            environment="test",
            analytics_generated_runtime_enabled=True,
        )


def test_generated_runtime_is_forbidden_in_production(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="forbidden in production"):
        Settings(
            environment="production",
            database_url="postgresql+psycopg://hcam@db/hcam",
            analytics_generated_runtime_enabled=True,
            analytics_artifact_root=tmp_path,
        )


@pytest.mark.parametrize(
    "relative_path",
    (
        Path("../yolox_tiny.onnx"),
        Path("C:/tmp/yolox_tiny.onnx"),
        Path(r"\\server\share\yolox_tiny.onnx"),
        Path("DET-R0/model.onnx"),
    ),
)
def test_generated_runtime_rejects_unapproved_model_paths(
    tmp_path: Path,
    relative_path: Path,
) -> None:
    with pytest.raises(ValueError, match="approved relative model file"):
        Settings(
            environment="test",
            analytics_artifact_root=tmp_path,
            analytics_model_relative_path=relative_path,
        )
