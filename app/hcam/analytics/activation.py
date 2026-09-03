from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from hcam.analytics.models import AnalyticsAssignment


P3_2_APPROVAL_RECORD_ID = "D-P3.2-START"
P3_2_CAPABILITY = "object_detection"
P3_2_EXECUTION_SCOPE = "generated_only"
P3_2_MODEL_ID = "DET-R0-ONNX-UPSTREAM-0.1.1RC0"
P3_2_MODEL_VERSION = (
    "sha256:427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7"
)
P3_2_PIPELINE_ID = "hcam.det-r0.generated"
P3_2_PIPELINE_VERSION = (
    "sha256:8254f905921bc04bc42074a2353efcac81a0004bd2ffd2173f473b65dd9b47f7"
)
P3_2_POLICY_VERSION = (
    "sha256:ba36957e4bf3207952e7f01ab584c960710dee2097c2e65cc7881f648ec93140"
)
P3_2_GENERATOR_ID = "hcam.det-r0.generated-frame"
P3_2_GENERATOR_VERSION = (
    "sha256:910d7083976055269029733d90f70cafc0f3fe3046716c2c9d683732fc181f64"
)
P3_2_PREPROCESSING_VERSION = (
    "sha256:f99b0b1568dafde0acd99f0a1e27a33644885349834d55a9dc632fe691ee352d"
)
P3_2_POSTPROCESSING_VERSION = (
    "sha256:e1d6e1d263691ac15fdaa4f891efa83707da4af0fd895be122459105df3ee601"
)
P3_2_TAXONOMY_VERSION = "hcam.objects.tier_a.v1"
P3_2_AUTHORIZATION_EXPIRES_ON = date(2026, 9, 24)
P3_3_APPROVAL_RECORD_ID = "D-P3.3-WORK-AUTH"
P3_3_CAPABILITY = "stream_local_tracking"
P3_3_TRACKER_ID = "TRK-R0-BYTETRACK-D1BF0191"
P3_3_TRACKER_VERSION = (
    "sha256:12bb7ce90e1089a1e160d5a15cd0c268f27a3083e4df37aef2cd042ae1160438"
)
P3_3_PIPELINE_ID = "hcam.trk-r0.generated"
P3_3_PIPELINE_VERSION = (
    "sha256:8dfd2fd221a9736cab33124f3fef4c1a2f65de7c74d0965a0d60b5fe750fe0e3"
)
P3_3_POLICY_VERSION = (
    "sha256:30e1940b2e74bb86629833499e27fb2c5bc204ddf56a5010071d086bbab1d0cc"
)
P3_3_CONFIGURATION_VERSION = (
    "sha256:f7149f15f3682d12638af5e92ac4a81730831977e19f992456630e1e64afd5be"
)
P3_3_TAXONOMY_VERSION = P3_2_TAXONOMY_VERSION
P3_3_AUTHORIZATION_EXPIRES_ON = date(2026, 9, 24)


@dataclass(frozen=True, slots=True)
class ActivationAssessment:
    eligible: bool
    blocking_reasons: tuple[str, ...]


def assess_generated_activation(
    assignment: AnalyticsAssignment,
    *,
    runtime_configured: bool,
    tracking_runtime_configured: bool = False,
    now: datetime | None = None,
) -> ActivationAssessment:
    if assignment.capability == P3_3_CAPABILITY:
        return _assess_generated_tracking_activation(
            assignment,
            runtime_configured=tracking_runtime_configured,
            now=now,
        )
    blockers: list[str] = []
    expected_model = {"id": P3_2_MODEL_ID, "version": P3_2_MODEL_VERSION}
    scope_unapproved = (
        assignment.execution_scope != P3_2_EXECUTION_SCOPE
        or assignment.capability != P3_2_CAPABILITY
        or assignment.pipeline_id != P3_2_PIPELINE_ID
        or assignment.pipeline_version != P3_2_PIPELINE_VERSION
        or assignment.models != [expected_model]
        or assignment.approval_record_id != P3_2_APPROVAL_RECORD_ID
    )
    if not runtime_configured:
        blockers.append("runtime_unconfigured")
    observed_now = now or datetime.now(UTC)
    if observed_now.date() > P3_2_AUTHORIZATION_EXPIRES_ON:
        blockers.append("authorization_expired")
    if assignment.taxonomy_version != P3_2_TAXONOMY_VERSION:
        blockers.append("taxonomy_unapproved")
    if (
        assignment.policy_version != P3_2_POLICY_VERSION
        or assignment.retention_class != "derived.analytics.standard"
        or assignment.geometry_refs
        or assignment.sampling_fps > 1
        or assignment.maximum_queue_age_ms > 1_000
    ):
        blockers.append("retention_policy_unapproved")
    if scope_unapproved and not blockers:
        blockers.append("implementation_scope_unapproved")
    return ActivationAssessment(not blockers, tuple(blockers))


def _assess_generated_tracking_activation(
    assignment: AnalyticsAssignment,
    *,
    runtime_configured: bool,
    now: datetime | None,
) -> ActivationAssessment:
    blockers: list[str] = []
    expected_tracker = {"id": P3_3_TRACKER_ID, "version": P3_3_TRACKER_VERSION}
    scope_unapproved = (
        assignment.execution_scope != P3_2_EXECUTION_SCOPE
        or assignment.pipeline_id != P3_3_PIPELINE_ID
        or assignment.pipeline_version != P3_3_PIPELINE_VERSION
        or assignment.models != [expected_tracker]
        or assignment.approval_record_id != P3_3_APPROVAL_RECORD_ID
        or assignment.configuration_digest != P3_3_CONFIGURATION_VERSION
    )
    if not runtime_configured:
        blockers.append("runtime_unconfigured")
    observed_now = now or datetime.now(UTC)
    if observed_now.date() > P3_3_AUTHORIZATION_EXPIRES_ON:
        blockers.append("authorization_expired")
    if assignment.taxonomy_version != P3_3_TAXONOMY_VERSION:
        blockers.append("taxonomy_unapproved")
    if (
        assignment.policy_version != P3_3_POLICY_VERSION
        or assignment.retention_class != "derived.analytics.standard"
        or assignment.geometry_refs
        or assignment.minimum_confidence != 0.25
        or assignment.sampling_fps > 1
        or assignment.maximum_queue_age_ms > 1_000
    ):
        blockers.append("retention_policy_unapproved")
    if scope_unapproved and not blockers:
        blockers.append("implementation_scope_unapproved")
    return ActivationAssessment(not blockers, tuple(blockers))
