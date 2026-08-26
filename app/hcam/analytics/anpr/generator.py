from __future__ import annotations

import hashlib
import json
from typing import Literal

from hcam.analytics.anpr.contracts import (
    ANPR_GENERATOR_VERSION,
    ANPR_SPLIT_POLICY_VERSION,
    ANPR_TOKEN_POLICY_VERSION,
    AnprLayout,
    AnprSplit,
    EphemeralSyntheticTokenV1,
    GeneratedTokenRequestV1,
    SealedSyntheticSplitManifestV1,
    SyntheticAnprExecutionPolicyV1,
    SyntheticCorpusPlanV1,
    SyntheticSplitManifestContentV1,
    SyntheticSplitManifestEntryV1,
    seal_split_manifest,
)
from hcam.analytics.anpr.guardrails import (
    authorize_generated_request,
    validate_ephemeral_synthetic_token,
)


AnprGenerationCode = Literal[
    "deterministic_token_collision",
    "generator_version_mismatch",
    "policy_version_mismatch",
    "sample_index_out_of_range",
    "split_unknown",
    "split_policy_version_mismatch",
]

SPLIT_ORDER: tuple[AnprSplit, ...] = (
    "contract_fixture",
    "development",
    "validation",
    "final_test",
)

_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_DIGITS = "0123456789"
_ALPHANUMERIC = _LETTERS + _DIGITS


class AnprGenerationViolation(ValueError):
    def __init__(self, code: AnprGenerationCode) -> None:
        super().__init__(f"P3.5 deterministic generation failed: {code}")
        self.code = code


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _domain_digest(domain: str, value: object) -> bytes:
    hasher = hashlib.sha256()
    domain_bytes = domain.encode("ascii")
    payload = _canonical_bytes(value)
    hasher.update(len(domain_bytes).to_bytes(2, "big"))
    hasher.update(domain_bytes)
    hasher.update(len(payload).to_bytes(8, "big"))
    hasher.update(payload)
    return hasher.digest()


def _digest_string(domain: str, value: object) -> str:
    return f"sha256:{_domain_digest(domain, value).hex()}"


def _identifier(prefix: str, domain: str, value: object) -> str:
    return f"{prefix}_{_domain_digest(domain, value).hex()[:32]}"


def _split_count(plan: SyntheticCorpusPlanV1, split: AnprSplit) -> int:
    if split not in SPLIT_ORDER:
        raise AnprGenerationViolation("split_unknown")
    return int(getattr(plan.counts, split))


def _split_material(
    plan: SyntheticCorpusPlanV1,
    split: AnprSplit,
    sample_index: int,
) -> dict[str, object]:
    return {
        "generator_version": plan.generator_version,
        "plan_id": plan.plan_id,
        "root_seed": plan.root_seed,
        "sample_index": sample_index,
        "seed_namespace": f"p35w3:{split}:v1",
        "source_id": plan.source_id,
        "split_policy_version": plan.split_policy_version,
    }


def derive_generated_request(
    plan: SyntheticCorpusPlanV1,
    split: AnprSplit,
    sample_index: int,
) -> GeneratedTokenRequestV1:
    if plan.generator_version != ANPR_GENERATOR_VERSION:
        raise AnprGenerationViolation("generator_version_mismatch")
    if plan.policy_version != ANPR_TOKEN_POLICY_VERSION:
        raise AnprGenerationViolation("policy_version_mismatch")
    if plan.split_policy_version != ANPR_SPLIT_POLICY_VERSION:
        raise AnprGenerationViolation("split_policy_version_mismatch")
    if not 0 <= sample_index < _split_count(plan, split):
        raise AnprGenerationViolation("sample_index_out_of_range")

    material = _split_material(plan, split, sample_index)
    digest = _domain_digest("hcam.anpr.p35w3.request.v1", material)
    layout: AnprLayout = "single_line" if digest[20] % 2 == 0 else "two_line"
    return GeneratedTokenRequestV1(
        request_id=_identifier(
            "anprreq",
            "hcam.anpr.p35w3.request-id.v1",
            material,
        ),
        generator_version=plan.generator_version,
        policy_version=plan.policy_version,
        seed=int.from_bytes(digest[:4], "big"),
        sample_index=sample_index,
        layout=layout,
    )


def generate_ephemeral_token(
    request: GeneratedTokenRequestV1,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
) -> EphemeralSyntheticTokenV1:
    if request.generator_version != ANPR_GENERATOR_VERSION:
        raise AnprGenerationViolation("generator_version_mismatch")
    if request.policy_version != ANPR_TOKEN_POLICY_VERSION:
        raise AnprGenerationViolation("policy_version_mismatch")
    approved = authorize_generated_request(
        request.model_dump(mode="json"),
        policy=policy,
    )
    digest = _domain_digest(
        "hcam.anpr.p35w3.non-issuable-token.v1",
        approved.model_dump(mode="json"),
    )
    payload = [_ALPHANUMERIC[value % len(_ALPHANUMERIC)] for value in digest[:8]]
    letter_position = digest[8] % len(payload)
    digit_position = digest[9] % (len(payload) - 1)
    if digit_position >= letter_position:
        digit_position += 1
    payload[letter_position] = _LETTERS[digest[10] % len(_LETTERS)]
    payload[digit_position] = _DIGITS[digest[11] % len(_DIGITS)]
    token = f"SYN-{''.join(payload[:4])}-{''.join(payload[4:])}"
    return validate_ephemeral_synthetic_token(
        {
            "request_id": approved.request_id,
            "token": token,
            "layout": approved.layout,
        }
    )


def generate_ephemeral_split(
    plan: SyntheticCorpusPlanV1,
    split: AnprSplit,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
) -> tuple[EphemeralSyntheticTokenV1, ...]:
    return tuple(
        generate_ephemeral_token(
            derive_generated_request(plan, split, sample_index),
            policy=policy,
        )
        for sample_index in range(_split_count(plan, split))
    )


def _holdout_partitions(
    split: AnprSplit,
    sample_index: int,
    split_count: int,
) -> tuple[Literal["primary", "holdout"], Literal["primary", "holdout"]]:
    if split != "final_test":
        return "primary", "primary"
    generator_profile: Literal["primary", "holdout"] = (
        "holdout" if sample_index == 0 else "primary"
    )
    font_holdout_index = 0 if split_count == 1 else 1
    font_partition: Literal["primary", "holdout"] = (
        "holdout" if sample_index == font_holdout_index else "primary"
    )
    return generator_profile, font_partition


def build_sealed_split_manifest(
    plan: SyntheticCorpusPlanV1,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
) -> SealedSyntheticSplitManifestV1:
    entries: list[SyntheticSplitManifestEntryV1] = []
    observed_tokens: set[str] = set()
    for split in SPLIT_ORDER:
        split_count = _split_count(plan, split)
        for sample_index in range(split_count):
            request = derive_generated_request(plan, split, sample_index)
            ephemeral = generate_ephemeral_token(request, policy=policy)
            if ephemeral.token in observed_tokens:
                raise AnprGenerationViolation("deterministic_token_collision")
            observed_tokens.add(ephemeral.token)
            generator_profile, font_partition = _holdout_partitions(
                split,
                sample_index,
                split_count,
            )
            sample_spec = {
                "font_partition": font_partition,
                "generator_profile": generator_profile,
                "request": request.model_dump(mode="json"),
                "seed_namespace": f"p35w3:{split}:v1",
                "split": split,
            }
            sample_spec_digest = _digest_string(
                "hcam.anpr.p35w3.sample-spec.v1",
                sample_spec,
            )
            entries.append(
                SyntheticSplitManifestEntryV1(
                    sample_id=f"anprsample_{sample_spec_digest[7:39]}",
                    request_id=request.request_id,
                    sample_spec_digest=sample_spec_digest,
                    split=split,
                    seed_namespace=f"p35w3:{split}:v1",
                    sample_index=sample_index,
                    layout=request.layout,
                    generator_profile=generator_profile,
                    font_partition=font_partition,
                )
            )

    plan_document = plan.model_dump(mode="json")
    content = SyntheticSplitManifestContentV1(
        manifest_id=_identifier(
            "anprmanifest",
            "hcam.anpr.p35w3.manifest-id.v1",
            plan_document,
        ),
        plan_id=plan.plan_id,
        root_seed=plan.root_seed,
        counts=plan.counts,
        entries=tuple(entries),
    )
    return seal_split_manifest(content)


def synthetic_corpus_plan_fixture() -> SyntheticCorpusPlanV1:
    return SyntheticCorpusPlanV1(
        plan_id="anprplan_22222222222222222222222222222222",
        root_seed=2_035_000_003,
        counts={
            "contract_fixture": 4,
            "development": 8,
            "validation": 4,
            "final_test": 4,
        },
    )
