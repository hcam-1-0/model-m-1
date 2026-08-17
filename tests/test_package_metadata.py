from __future__ import annotations

from importlib.metadata import version

from hcam import __version__
from hcam.main import create_app


def test_distribution_and_api_versions_match_package() -> None:
    assert version("hcam-core") == __version__
    assert create_app().version == __version__
