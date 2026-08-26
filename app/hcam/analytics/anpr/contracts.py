from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, Field, model_validator

from hcam.analytics.contracts import ContractModel, ImmutableDigest


ANPR_GENERATED_SOURCE_ID = "DATA-PLATE-GEN-R0"
ANPR_TOKEN_POLICY_ID = "hcam.anpr.synthetic-non-issuable.v1"
ANPR_TOKEN_PATTERN = r"^SYN-[A-Z0-9]{4}-[A-Z0-9]{4}$"
MAX_ANPR_REQUEST_BYTES = 4 * 1024
MAX_ANPR_DOCUMENT_DEPTH = 8
MAX_ANPR_DOCUMENT_NODES = 256
MAX_ANPR_LOCAL_SAMPLES = 10_000

_TOKEN_PATTERN = re.compile(ANPR_TOKEN_PATTERN, flags=re.ASCII)

AnprRequestId = Annotated[str, Field(pattern=r"^anprreq_[0-9a-f]{32}$")]
AnprScript = Literal["latin"]
AnprLayout = Literal["single_line", "two_line"]
AnprTokenClass = Literal["synthetic_non_issuable"]


def _validate_namespaced_token(value: str) -> str:
    if not value.isascii() or _TOKEN_PATTERN.fullmatch(value) is None:
        raise ValueError("token must use the approved synthetic namespace")
    payload = value.removeprefix("SYN-").replace("-", "")
    if not any(character.isalpha() for character in payload) or not any(
        character.isdigit() for character in payload
    ):
        raise ValueError("synthetic token payload must contain letters and digits")
    return value


SyntheticPlateToken = Annotated[
    str,
    Field(min_length=13, max_length=13, pattern=ANPR_TOKEN_PATTERN),
    AfterValidator(_validate_namespaced_token),
]


class GeneratedTokenRequestV1(ContractModel):
    """Seed-only request; it deliberately has no text, file, media, or URL field."""

    contract_type: Literal["hcam.anpr.generated-token-request.v1"] = (
        "hcam.anpr.generated-token-request.v1"
    )
    request_id: AnprRequestId
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    generator_version: ImmutableDigest
    policy_id: Literal["hcam.anpr.synthetic-non-issuable.v1"] = ANPR_TOKEN_POLICY_ID
    policy_version: ImmutableDigest
    seed: Annotated[int, Field(ge=0, le=4_294_967_295)]
    sample_index: Annotated[int, Field(ge=0, lt=MAX_ANPR_LOCAL_SAMPLES)]
    script: AnprScript = "latin"
    layout: AnprLayout
    token_class: AnprTokenClass = "synthetic_non_issuable"
    input_mode: Literal["deterministic_seed_only"] = "deterministic_seed_only"
    synthetic_only: Literal[True] = True


class EphemeralSyntheticTokenV1(ContractModel):
    """In-memory ground truth that must never enter evidence or persistence."""

    contract_type: Literal["hcam.anpr.ephemeral-synthetic-token.v1"] = (
        "hcam.anpr.ephemeral-synthetic-token.v1"
    )
    request_id: AnprRequestId
    token: SyntheticPlateToken
    token_class: AnprTokenClass = "synthetic_non_issuable"
    script: AnprScript = "latin"
    layout: AnprLayout
    synthetic_only: Literal[True] = True
    persistence: Literal["prohibited"] = "prohibited"


class SyntheticAnprExecutionPolicyV1(ContractModel):
    contract_type: Literal["hcam.anpr.execution-policy.v1"] = (
        "hcam.anpr.execution-policy.v1"
    )
    enabled: bool = False
    environment: Literal["development", "test", "production"] = "development"
    execution_scope: Literal["generated_only"] = "generated_only"
    source_id: Literal["DATA-PLATE-GEN-R0"] = ANPR_GENERATED_SOURCE_ID
    input_mode: Literal["deterministic_seed_only"] = "deterministic_seed_only"
    network_access: Literal["denied"] = "denied"
    artifact_download: Literal["denied"] = "denied"
    plate_text_persistence: Literal["denied"] = "denied"
    arbitrary_input: Literal["denied"] = "denied"
    maximum_request_bytes: Literal[4096] = MAX_ANPR_REQUEST_BYTES

    @model_validator(mode="after")
    def production_is_fail_closed(self) -> SyntheticAnprExecutionPolicyV1:
        if self.enabled and self.environment == "production":
            raise ValueError("generated ANPR execution is forbidden in production")
        return self


def generated_request_fixture() -> GeneratedTokenRequestV1:
    return GeneratedTokenRequestV1(
        request_id="anprreq_11111111111111111111111111111111",
        generator_version="sha256:" + "a" * 64,
        policy_version="sha256:" + "b" * 64,
        seed=1_337,
        sample_index=7,
        layout="single_line",
    )


def anpr_contract_bundle() -> dict[str, Any]:
    return {
        "contract_format": "hcam.anpr.contract-bundle.v1",
        "contracts": {
            "ephemeral_token": EphemeralSyntheticTokenV1.model_json_schema(
                mode="validation"
            ),
            "execution_policy": SyntheticAnprExecutionPolicyV1.model_json_schema(
                mode="validation"
            ),
            "generated_request": GeneratedTokenRequestV1.model_json_schema(
                mode="validation"
            ),
        },
        "source_policy": {
            "allowed_source_id": ANPR_GENERATED_SOURCE_ID,
            "input_mode": "deterministic_seed_only",
            "synthetic_only": True,
            "external_text_allowed": False,
            "file_url_upload_or_media_allowed": False,
        },
        "token_policy": {
            "policy_id": ANPR_TOKEN_POLICY_ID,
            "classification": "synthetic_non_issuable",
            "pattern": ANPR_TOKEN_PATTERN,
            "visible_namespace": "SYN-",
            "production_grammar_strategy": (
                "deny_every_value_outside_the_disjoint_visible_synthetic_namespace"
            ),
            "required_character_classes": ["ascii_uppercase", "ascii_digit"],
            "normalization_or_lookup": "prohibited",
        },
        "resource_limits": {
            "maximum_document_depth": MAX_ANPR_DOCUMENT_DEPTH,
            "maximum_document_nodes": MAX_ANPR_DOCUMENT_NODES,
            "maximum_local_samples": MAX_ANPR_LOCAL_SAMPLES,
            "maximum_request_bytes": MAX_ANPR_REQUEST_BYTES,
        },
        "persistence_policy": {
            "plate_text_retention_hours": 0,
            "token_or_alternative_in_evidence": False,
            "identifier_free_aggregate_evidence_only": True,
        },
    }
