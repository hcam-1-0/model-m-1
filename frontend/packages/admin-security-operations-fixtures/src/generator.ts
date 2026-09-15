import type { AdminResource, ChangeRequest } from "../../admin-contracts/src";
import type {
  AuditReference,
  ComplianceControl,
  DenialActivity,
  ProviderPosture,
  SupplyChainRecord,
} from "../../security-contracts/src";
import type {
  DegradationProjection,
  QueueHealth,
  RecoveryPreview,
  ServiceHealth,
  SloProjection,
  TopologyProjection,
} from "../../operations-contracts/src";

const now = "2026-09-10T09:00:00.000Z";
const truth = (index: number) => ({
  source: "generated_fixture" as const,
  observedAt: now,
  staleAt: index % 7 === 0 ? "2026-09-10T08:30:00.000Z" : "2026-09-10T10:00:00.000Z",
  completeness: index % 9 === 0 ? ("partial" as const) : ("complete" as const),
  limitations: ["Generated projection only", "No operational effect"],
});
const ref = (kind: string, index: number) => `SYN-${kind}-${String(index).padStart(4, "0")}`;

export function generatedAdminResources(count = 25): readonly AdminResource[] {
  const kinds: readonly AdminResource["kind"][] = [
    "organization",
    "department",
    "user",
    "membership",
    "role",
    "permission",
    "policy",
    "camera",
    "stream",
    "provider",
    "configuration",
    "resource_profile",
    "retention_policy",
  ];
  return Array.from({ length: Math.max(0, Math.min(count, 250)) }, (_, index) => ({
    ref: ref("ADMIN", index + 1),
    kind: kinds[index % kinds.length] ?? "policy",
    label: `Generated ${kinds[index % kinds.length] ?? "resource"} ${String(index + 1).padStart(2, "0")}`,
    departmentRef: `SYN-DEPT-${String((index % 10) + 1).padStart(2, "0")}`,
    state: index % 11 === 0 ? "partial" : index % 13 === 0 ? "stale" : "current",
    revision: index + 1,
    etag: `"SYN-P56-ADMIN-${index + 1}"`,
    effective: false,
    truth: truth(index),
    generated: true,
  }));
}
export function generatedChangeRequests(count = 12): readonly ChangeRequest[] {
  const kinds: readonly ChangeRequest["kind"][] = [
    "membership",
    "role_binding",
    "policy_revision",
    "camera_governance",
    "provider_governance",
    "feature_configuration",
    "resource_profile",
    "retention_projection",
  ];
  const states: readonly ChangeRequest["status"][] = [
    "draft",
    "submitted",
    "independent_review",
    "approved_non_effective",
    "rejected",
  ];
  return Array.from({ length: Math.max(0, Math.min(count, 100)) }, (_, index) => ({
    ref: ref("CHANGE", index + 1),
    kind: kinds[index % kinds.length] ?? "policy_revision",
    status: states[index % states.length] ?? "draft",
    departmentRef: "SYN-DEPT-01",
    requesterRef: ref("ACTOR", (index % 4) + 1),
    reviewerRefs: index % 3 ? [ref("ACTOR", 9)] : [],
    requiredApprovals: 2,
    policyRevision: "SYN-POLICY-R7",
    resourceRevision: index + 1,
    etag: `"SYN-P56-CHANGE-${index + 1}"`,
    idempotencyKey: `SYN-IDEMP-CHANGE-${String(index + 1).padStart(4, "0")}`,
    reasonCode: "SYN-GOVERNANCE-REVIEW",
    impactSummary: ["Generated preview", "No effective mutation"],
    effective: false,
    generated: true,
  }));
}
export function generatedDenials(count = 12): readonly DenialActivity[] {
  const categories: readonly DenialActivity["category"][] = [
    "authorization",
    "scope",
    "policy",
    "session",
    "input",
  ];
  return Array.from({ length: count }, (_, index) => ({
    ref: ref("DENIAL", index + 1),
    lane: "security",
    category: categories[index % categories.length] ?? "authorization",
    reasonCode: `SYN-DENY-${String((index % 5) + 1).padStart(2, "0")}`,
    actorClass: "generated_operator",
    departmentRef: "SYN-DEPT-01",
    recordedAt: now,
    rawPayloadRetained: false,
    generated: true,
  }));
}
export function generatedAuditReferences(count = 10): readonly AuditReference[] {
  const outcomes: readonly AuditReference["outcome"][] = [
    "allowed",
    "denied",
    "conflict",
    "unknown",
  ];
  return Array.from({ length: count }, (_, index) => ({
    ref: ref("AUDIT", index + 1),
    lane: "audit",
    actionClass: "generated_governance_review",
    outcome: outcomes[index % outcomes.length] ?? "unknown",
    actorRef: ref("ACTOR", index + 1),
    targetRef: ref("CHANGE", index + 1),
    sequence: index + 1,
    immutable: true,
    generated: true,
  }));
}
export function generatedComplianceControls(count = 8): readonly ComplianceControl[] {
  return Array.from({ length: count }, (_, index) => ({
    ref: ref("CONTROL", index + 1),
    framework: "SYN-CONTROL-SET",
    title: `Generated control ${index + 1}`,
    state: index % 4 === 0 ? "partial" : "current",
    evidenceRefs: [ref("EVIDENCE-REF", index + 1)],
    exceptionRef: index % 5 === 0 ? ref("EXCEPTION", index + 1) : null,
    attested: false,
    generated: true,
  }));
}
export function generatedSupplyChain(count = 8): readonly SupplyChainRecord[] {
  return Array.from({ length: count }, (_, index) => ({
    ref: ref("COMPONENT", index + 1),
    component: `generated-component-${index + 1}`,
    version: `0.${index + 1}.0`,
    licenseState: index % 5 === 0 ? "review_required" : "recorded",
    vulnerabilityState: index % 4 === 0 ? "stale" : "current",
    provenanceState: index % 3 === 0 ? "unverified" : "verified_reference",
    sbomRef: ref("SBOM", index + 1),
    scannerExecuted: false,
    generated: true,
  }));
}
export function generatedProviderPosture(count = 6): readonly ProviderPosture[] {
  return Array.from({ length: count }, (_, index) => ({
    ref: ref("PROVIDER", index + 1),
    destinationRuleRef: ref("DESTINATION-RULE", index + 1),
    secretRefPresent: index % 2 === 0,
    secretValueAvailable: false,
    certificateState: index % 3 === 0 ? "stale" : "declared",
    networkContacted: false,
    generated: true,
  }));
}
export function generatedServices(count = 12): readonly ServiceHealth[] {
  const states: readonly ServiceHealth["state"][] = [
    "healthy",
    "healthy",
    "degraded",
    "stale",
    "recovering",
    "unknown",
  ];
  return Array.from({ length: count }, (_, index) => ({
    ref: ref("SERVICE", index + 1),
    label: `Generated service ${String(index + 1).padStart(2, "0")}`,
    domain: ["camera", "intelligence", "evidence", "platform"][index % 4] ?? "platform",
    state: states[index % states.length] ?? "unknown",
    dependencyRefs: index ? [ref("SERVICE", index)] : [],
    latencyBucket: index % 5 === 0 ? "lt2000" : "lt500",
    saturationBand: index % 6 === 0 ? "high" : "moderate",
    truth: { ...truth(index), productionClaim: false },
    generated: true,
  }));
}
export function generatedQueues(count = 10): readonly QueueHealth[] {
  return Array.from({ length: count }, (_, index) => ({
    ref: ref("QUEUE", index + 1),
    label: `Generated queue ${index + 1}`,
    depthBand: index % 6 === 0 ? "high" : "low",
    oldestAgeBand: index % 7 === 0 ? "lt10m" : "lt2m",
    leaseState: index % 9 === 0 ? "expired" : index % 5 === 0 ? "recovering" : "current",
    retryBand: index % 6 === 0 ? "elevated" : "low",
    deadLetterBand: index % 9 === 0 ? "present" : "none",
    generated: true,
  }));
}
export function generatedSlos(count = 6): readonly SloProjection[] {
  return Array.from({ length: count }, (_, index) => ({
    ref: ref("SLO", index + 1),
    label: `Generated objective ${index + 1}`,
    indicator: ["availability", "latency", "freshness"][index % 3] ?? "availability",
    objective: "Generated threshold; not a production target",
    window: "generated_30d_projection",
    budgetState: index % 5 === 0 ? "exhausted" : index % 3 === 0 ? "watch" : "healthy",
    targetAuthority: "generated_non_production",
    generated: true,
  }));
}
export const generatedDegradation: DegradationProjection = {
  ref: ref("DEGRADATION", 1),
  state: "constrained",
  affectedDomains: ["generated_provider", "generated_search"],
  limitations: ["Generated projection", "No kill-switch action available"],
  killSwitchAvailable: false,
  generated: true,
};
export function generatedRecoveryPreviews(): readonly RecoveryPreview[] {
  return ["backup", "restore", "failover", "maintenance", "disaster_recovery"].map(
    (kind, index) => ({
      ref: ref("RECOVERY", index + 1),
      class: kind as RecoveryPreview["class"],
      state: "preview_only",
      lastEvidenceRef: index % 2 ? null : ref("EVIDENCE-REF", index + 1),
      rpo: "not_selected",
      rto: "not_selected",
      executable: false,
      generated: true,
    }),
  );
}
export function generatedTopologies(): readonly TopologyProjection[] {
  return [
    "low_resource",
    "enhanced_workstation",
    "control_room",
    "owned_GPU_lab",
    "future_server",
    "future_Kubernetes",
  ].map((profile, index) => ({
    ref: ref("TOPOLOGY", index + 1),
    profile: profile as TopologyProjection["profile"],
    nodes: [{ ref: ref("NODE", index + 1), role: "generated_projection", state: "not_deployed" }],
    deploymentActive: false,
    generated: true,
  }));
}
