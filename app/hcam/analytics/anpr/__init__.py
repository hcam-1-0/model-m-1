"""Generated-only P3.5 ANPR contracts and fail-closed guardrails."""

from hcam.analytics.anpr.contracts import (
    ANPR_GENERATED_SOURCE_ID,
    ANPR_GENERATOR_VERSION,
    ANPR_SPLIT_POLICY_ID,
    ANPR_SPLIT_POLICY_VERSION,
    ANPR_TOKEN_POLICY_ID,
    ANPR_TOKEN_POLICY_VERSION,
    EphemeralSyntheticTokenV1,
    GeneratedTokenRequestV1,
    SealedSyntheticSplitManifestV1,
    SyntheticAnprExecutionPolicyV1,
    SyntheticCorpusPlanV1,
    anpr_contract_bundle,
)
from hcam.analytics.anpr.generator import (
    AnprGenerationViolation,
    build_sealed_split_manifest,
    derive_generated_request,
    generate_ephemeral_split,
    generate_ephemeral_token,
    synthetic_corpus_plan_fixture,
)
from hcam.analytics.anpr.guardrails import (
    AnprBoundaryViolation,
    authorize_generated_request,
    canonical_anpr_evidence_json,
    validate_ephemeral_synthetic_token,
)

__all__ = [
    "ANPR_GENERATED_SOURCE_ID",
    "ANPR_GENERATOR_VERSION",
    "ANPR_SPLIT_POLICY_ID",
    "ANPR_SPLIT_POLICY_VERSION",
    "ANPR_TOKEN_POLICY_ID",
    "ANPR_TOKEN_POLICY_VERSION",
    "AnprBoundaryViolation",
    "AnprGenerationViolation",
    "EphemeralSyntheticTokenV1",
    "GeneratedTokenRequestV1",
    "SealedSyntheticSplitManifestV1",
    "SyntheticAnprExecutionPolicyV1",
    "SyntheticCorpusPlanV1",
    "anpr_contract_bundle",
    "authorize_generated_request",
    "build_sealed_split_manifest",
    "canonical_anpr_evidence_json",
    "derive_generated_request",
    "generate_ephemeral_split",
    "generate_ephemeral_token",
    "synthetic_corpus_plan_fixture",
    "validate_ephemeral_synthetic_token",
]
