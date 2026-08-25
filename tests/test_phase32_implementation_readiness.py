from __future__ import annotations

from tools import phase32_implementation_readiness as readiness


def test_phase32_static_implementation_evidence_remains_accepted() -> None:
    report = readiness.build_report(run_validation=False, artifact_root=None)

    assert report.status == "accepted"
    assert report.failures == 0
    assert report.manual_gates == 0
    assert len(report.package_digest) == 64
    assert report.package_digest == report.package_digest.upper()
    assert {check.name for check in report.checks} == {
        "required_files",
        "owner_records",
        "implementation_bindings",
        "taxonomy",
        "local_e2e",
        "owner_acceptance",
    }
    acceptance = next(
        check for check in report.checks if check.name == "owner_acceptance"
    )
    assert acceptance.evidence == (
        f"accepted_digest={readiness.P3_2_ACCEPTED_PACKAGE_DIGEST}",
    )


def test_phase32_package_digest_is_deterministic_and_path_relative() -> None:
    first_digest, first_manifest = readiness.package_digest()
    second_digest, second_manifest = readiness.package_digest()

    assert first_digest == second_digest
    assert first_manifest == second_manifest
    assert len(first_manifest) == len(readiness.PACKAGE_FILES)
    assert all(":\\" not in item for item in first_manifest)
    assert all(" sha256=" in item and " bytes=" in item for item in first_manifest)
