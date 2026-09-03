from __future__ import annotations

import copy
import re
from typing import cast

import pytest
from pydantic import ValidationError

from hcam.analytics.anpr import (
    AnprBoundaryViolation,
    AnprGenerationViolation,
    SealedSyntheticSplitManifestV1,
    SyntheticAnprExecutionPolicyV1,
    SyntheticCorpusPlanV1,
    build_sealed_split_manifest,
    canonical_anpr_evidence_json,
    derive_generated_request,
    generate_ephemeral_split,
    synthetic_corpus_plan_fixture,
)
from hcam.analytics.anpr.contracts import AnprSplit
from hcam.analytics.anpr.generator import SPLIT_ORDER


_TOKEN_PATTERN = re.compile(r"^SYN-[A-Z0-9]{4}-[A-Z0-9]{4}$", re.ASCII)


def _enabled_policy() -> SyntheticAnprExecutionPolicyV1:
    return SyntheticAnprExecutionPolicyV1(enabled=True, environment="test")


def _manifest_json(manifest: SealedSyntheticSplitManifestV1) -> str:
    return canonical_anpr_evidence_json(
        manifest,
        maximum_bytes=8 * 1024 * 1024,
        maximum_nodes=200_000,
    )


def test_generator_and_manifest_replay_exactly_twenty_times() -> None:
    plan = synthetic_corpus_plan_fixture()
    policy = _enabled_policy()
    expected_tokens = tuple(
        token.token
        for split in SPLIT_ORDER
        for token in generate_ephemeral_split(plan, split, policy=policy)
    )
    expected_manifest = build_sealed_split_manifest(plan, policy=policy)

    for _ in range(20):
        actual_tokens = tuple(
            token.token
            for split in SPLIT_ORDER
            for token in generate_ephemeral_split(plan, split, policy=policy)
        )
        actual_manifest = build_sealed_split_manifest(plan, policy=policy)
        assert actual_tokens == expected_tokens
        assert actual_manifest == expected_manifest


def test_generated_tokens_are_unique_visible_and_mixed() -> None:
    plan = synthetic_corpus_plan_fixture()
    tokens = [
        token.token
        for split in SPLIT_ORDER
        for token in generate_ephemeral_split(plan, split, policy=_enabled_policy())
    ]

    assert len(tokens) == plan.counts.total
    assert len(set(tokens)) == len(tokens)
    assert all(_TOKEN_PATTERN.fullmatch(token) for token in tokens)
    assert all(any(character.isalpha() for character in token[4:]) for token in tokens)
    assert all(any(character.isdigit() for character in token[4:]) for token in tokens)


def test_independent_split_namespaces_and_ids_do_not_overlap() -> None:
    plan = synthetic_corpus_plan_fixture()
    requests = {
        split: {
            derive_generated_request(plan, split, index).request_id
            for index in range(getattr(plan.counts, split))
        }
        for split in SPLIT_ORDER
    }

    for index, left in enumerate(SPLIT_ORDER):
        for right in SPLIT_ORDER[index + 1 :]:
            assert requests[left].isdisjoint(requests[right])

    manifest = build_sealed_split_manifest(plan, policy=_enabled_policy())
    assert {
        entry.seed_namespace for entry in manifest.content.entries
    } == {f"p35w3:{split}:v1" for split in SPLIT_ORDER}


def test_manifest_contains_no_token_text_or_token_commitment() -> None:
    plan = synthetic_corpus_plan_fixture()
    ephemeral_tokens = {
        token.token
        for split in SPLIT_ORDER
        for token in generate_ephemeral_split(plan, split, policy=_enabled_policy())
    }
    document = _manifest_json(
        build_sealed_split_manifest(plan, policy=_enabled_policy())
    )

    assert '"token"' not in document
    assert '"plate_text"' not in document
    assert "SYN-" not in document
    assert all(token not in document for token in ephemeral_tokens)
    assert '"token_text_persisted":false' in document
    assert '"token_commitment_persisted":false' in document


def test_final_test_is_frozen_and_holdouts_cannot_leak_to_other_splits() -> None:
    manifest = build_sealed_split_manifest(
        synthetic_corpus_plan_fixture(),
        policy=_enabled_policy(),
    )
    final_entries = [
        entry for entry in manifest.content.entries if entry.split == "final_test"
    ]
    non_final_entries = [
        entry for entry in manifest.content.entries if entry.split != "final_test"
    ]

    assert manifest.content.final_test_frozen is True
    assert manifest.content.final_test_tuning_allowed is False
    assert manifest.content.final_test_access_count == 0
    assert any(entry.generator_profile == "holdout" for entry in final_entries)
    assert any(entry.font_partition == "holdout" for entry in final_entries)
    assert all(entry.generator_profile == "primary" for entry in non_final_entries)
    assert all(entry.font_partition == "primary" for entry in non_final_entries)

    content = manifest.content.model_dump(mode="json")
    entries = content["entries"]
    assert isinstance(entries, list)
    entries[0]["generator_profile"] = "holdout"
    with pytest.raises(ValidationError, match="reserved for final test"):
        type(manifest.content).model_validate(content)


def test_manifest_digest_rejects_content_tampering() -> None:
    manifest = build_sealed_split_manifest(
        synthetic_corpus_plan_fixture(),
        policy=_enabled_policy(),
    )
    changed = manifest.model_dump(mode="json")
    changed["content"]["root_seed"] += 1

    with pytest.raises(ValidationError, match="digest does not match"):
        SealedSyntheticSplitManifestV1.model_validate(changed)


def test_plan_change_changes_requests_tokens_and_manifest_digest() -> None:
    first = synthetic_corpus_plan_fixture()
    second_document = first.model_dump(mode="json")
    second_document["root_seed"] += 1
    second_document["plan_id"] = "anprplan_33333333333333333333333333333333"
    second = SyntheticCorpusPlanV1.model_validate(second_document)
    policy = _enabled_policy()

    first_token = generate_ephemeral_split(
        first, "contract_fixture", policy=policy
    )[0].token
    second_token = generate_ephemeral_split(
        second, "contract_fixture", policy=policy
    )[0].token
    assert first_token != second_token
    assert (
        build_sealed_split_manifest(first, policy=policy).manifest_digest
        != build_sealed_split_manifest(second, policy=policy).manifest_digest
    )


def test_generation_is_default_off_and_production_forbidden() -> None:
    plan = synthetic_corpus_plan_fixture()
    with pytest.raises(AnprBoundaryViolation) as disabled:
        generate_ephemeral_split(
            plan,
            "contract_fixture",
            policy=SyntheticAnprExecutionPolicyV1(),
        )
    assert disabled.value.code == "runtime_disabled"

    with pytest.raises(ValidationError, match="forbidden in production"):
        SyntheticAnprExecutionPolicyV1(enabled=True, environment="production")


def test_invalid_split_and_index_fail_with_bounded_codes() -> None:
    plan = synthetic_corpus_plan_fixture()
    with pytest.raises(AnprGenerationViolation) as index:
        derive_generated_request(plan, "validation", plan.counts.validation)
    assert index.value.code == "sample_index_out_of_range"

    with pytest.raises(AnprGenerationViolation) as split:
        derive_generated_request(plan, cast(AnprSplit, "unknown"), 0)
    assert split.value.code == "split_unknown"


def test_total_sample_ceiling_is_enforced() -> None:
    document = synthetic_corpus_plan_fixture().model_dump(mode="json")
    document["counts"] = {
        "contract_fixture": 4,
        "development": 9_997,
        "validation": 1,
        "final_test": 1,
    }
    with pytest.raises(ValidationError, match="local sample ceiling"):
        SyntheticCorpusPlanV1.model_validate(document)


def test_manifest_is_frozen_and_canonical() -> None:
    manifest = build_sealed_split_manifest(
        synthetic_corpus_plan_fixture(),
        policy=_enabled_policy(),
    )
    changed = copy.copy(manifest)
    with pytest.raises(ValidationError):
        changed.manifest_digest = "sha256:" + "0" * 64

    assert _manifest_json(manifest) == _manifest_json(manifest)


def test_duplicate_token_generation_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    from hcam.analytics.anpr import generator

    original = generator.generate_ephemeral_token
    first_token = original(
        derive_generated_request(
            synthetic_corpus_plan_fixture(),
            "contract_fixture",
            0,
        ),
        policy=_enabled_policy(),
    )

    monkeypatch.setattr(generator, "generate_ephemeral_token", lambda *_args, **_kwargs: first_token)
    with pytest.raises(AnprGenerationViolation) as collision:
        generator.build_sealed_split_manifest(
            synthetic_corpus_plan_fixture(),
            policy=_enabled_policy(),
        )
    assert collision.value.code == "deterministic_token_collision"
