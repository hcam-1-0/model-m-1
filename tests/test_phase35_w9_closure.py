from __future__ import annotations

import json

import pytest

from tools import phase35_w9_closure as closure


def test_w9_authorization_is_exact_and_non_accepting() -> None:
    authorization, changed = closure._load_authorization()

    assert authorization["decision_id"] == "D-P3.5-W9-START"
    assert authorization["owner_statement_received"] == "D-P3.5-W9-START: A"
    assert authorization["selected_option"] == "A"
    assert authorization["implementation_authorized"] is True
    assert authorization["acceptance_authorized"] is False
    assert authorization["w10_authorized"] is False
    assert authorization["allowed_network_actions"] == []
    assert set(changed).issubset(closure.ALLOWED_PATHS)
    assert closure.CLOSURE_HEAD == "1611922b4f410aa0cdbce369e4f3c8838f53e19f"


def test_w9_resource_stress_is_bounded_deterministic_and_abstaining() -> None:
    first = closure.run_resource_stress()
    second = closure.run_resource_stress()

    assert first == second
    assert first["observation_count"] == 10_000
    assert first["closed_result_count"] == 2_208
    assert first["abstained_result_count"] == 2_208
    assert first["maximum_active_state_count"] == 256
    assert first["overload_result_count"] == 4
    assert first["default_off_rejection_count"] == 1
    assert first["blocked_network_attempt_count"] == 1
    assert first["elapsed_limit_passed"] is True
    assert first["memory_limit_passed"] is True


def test_w9_archive_summary_rejects_unsafe_or_prohibited_entries() -> None:
    with pytest.raises(closure.ClosureToolError, match="unsafe archive entry"):
        closure._summarize_entries(
            "wheel", (("../escape", b"payload"),), raw_archive=b"archive"
        )

    with pytest.raises(closure.ClosureToolError, match="prohibited payload"):
        closure._summarize_entries(
            "wheel", (("package/model.onnx", b"payload"),), raw_archive=b"archive"
        )


def test_w9_sdist_digest_excludes_only_canonical_self_evidence_content() -> None:
    first = closure._summarize_entries(
        "sdist",
        (
            ("hcam/contracts/phase-3/p3-5-w9-closure-evidence.json", b"first"),
            ("hcam/app/hcam/__init__.py", b"version"),
        ),
        raw_archive=b"first archive",
    )
    second = closure._summarize_entries(
        "sdist",
        (
            ("hcam/contracts/phase-3/p3-5-w9-closure-evidence.json", b"second"),
            ("hcam/app/hcam/__init__.py", b"version"),
        ),
        raw_archive=b"second archive",
    )

    assert first.canonical_content_sha256 == second.canonical_content_sha256
    assert first.canonical_uncompressed_bytes == second.canonical_uncompressed_bytes
    assert first.self_evidence_exclusion_count == 1
    assert first.raw_archive_sha256 is None
    assert first.raw_archive_bytes is None


def test_w9_evidence_writer_requires_explicit_acknowledgment() -> None:
    assert closure.main(["write"]) == 2


def test_w9_tracked_evidence_is_canonical() -> None:
    assert closure.check_evidence() == 0
    assert closure._sha256_file(closure.EVIDENCE_PATH) == (
        closure.ACCEPTED_EVIDENCE_SHA256
    )


def test_w9_evidence_has_no_retained_text_identifiers_or_external_paths() -> None:
    rendered = closure.EVIDENCE_PATH.read_text(encoding="utf-8")
    document = json.loads(rendered)

    assert document["status"] == "validated_generated_only_closure"
    assert document["security_evidence"]["retained_sensitive_text_value_count"] == 0
    assert document["security_evidence"]["retained_identifier_value_count"] == 0
    assert document["security_evidence"]["model_or_font_execution_count"] == 0
    assert document["security_evidence"]["external_runtime_access_count"] == 0
    assert document["security_evidence"]["package_build_network_guard_probe_count"] == 1
    assert document["acceptance_authorized"] is False
    assert document["w10_authorized"] is False
    assert "SYN-" not in rendered
    assert '"stream_id":' not in rendered
    assert '"track_id":' not in rendered
    assert "B:\\" not in rendered
    assert "E:\\" not in rendered
