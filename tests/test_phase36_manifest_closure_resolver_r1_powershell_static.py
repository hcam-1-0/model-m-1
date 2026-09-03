from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/phase36_manifest_closure_resolver_r1.psm1"


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_powershell_source_mirrors_contract_constants_and_exports_narrow_surface() -> None:
    source = _source()

    for literal in (
        "1.1.0",
        "resolve_manifest_closure_v1",
        "67108864",
        "134217728",
        "NestedModules",
        "RequiredAssemblies",
        "manifest_directory",
        "ps_home",
    ):
        assert literal in source
    exports = re.search(r"Export-ModuleMember -Function @\((.*?)\)", source, re.S)
    assert exports is not None
    assert set(re.findall(r"'([^']+)'", exports.group(1))) == {
        "Get-HcamManifestClosureCanonicalProjection",
        "Get-HcamManifestCandidates",
        "Invoke-HcamManifestClosurePolicy",
    }


def test_powershell_source_retains_fail_closed_security_boundaries() -> None:
    source = _source()

    for reason in (
        "manifest_reference_forbidden",
        "manifest_reference_escape",
        "manifest_candidate_ambiguous",
        "load_bearing_target_missing",
        "load_bearing_target_untrusted",
        "duplicate_canonical_target",
        "aggregate_file_bytes_exceeded",
    ):
        assert reason in source
    for prohibited in (
        "Invoke-Expression",
        "Start-Process",
        "System.Diagnostics.Process",
        "Get-ChildItem",
        "PSModulePath",
        "Import-PowerShellDataFile",
        "Import-Module -Name",
        "Invoke-WebRequest",
    ):
        assert prohibited not in source
    assert "raw_path_or_reference_retained = $false" in source
    assert "exception_or_security_material_retained = $false" in source


def test_powershell_source_is_LF_and_has_no_trailing_whitespace() -> None:
    payload = SOURCE.read_bytes()
    assert payload.endswith(b"\n")
    assert b"\r\n" not in payload
    assert all(line == line.rstrip() for line in _source().splitlines())
