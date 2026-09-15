import type { ProblemCode } from "@hcam/contracts";
import { QueryClient } from "@tanstack/react-query";

export type QueryClass =
  "immutable" | "configuration" | "summary" | "queue" | "detail" | "command" | "non_cacheable";
export interface QueryPolicy {
  readonly operationId: string;
  readonly queryClass: QueryClass;
  readonly staleMs: number;
  readonly cacheMs: number;
  readonly retryLimit: number;
  readonly pollMs: number | null;
  readonly persist: false;
}
export type QueryPolicyInput = Omit<QueryPolicy, "persist"> & { readonly persist: boolean };
const nonRetryable = new Set<ProblemCode>([
  "denied",
  "conflict",
  "incompatible",
  "invalid",
  "safe_failure",
]);

export function defineQueryPolicy(policy: QueryPolicyInput): QueryPolicy {
  if (policy.queryClass === "command" && policy.retryLimit !== 0)
    throw new Error("commands_cannot_retry");
  if (
    policy.persist ||
    policy.staleMs < 0 ||
    policy.cacheMs < 0 ||
    policy.retryLimit < 0 ||
    policy.retryLimit > 2
  )
    throw new Error("invalid_query_policy");
  return Object.freeze({ ...policy, persist: false });
}
export function shouldRetry(policy: QueryPolicy, attempt: number, code: ProblemCode): boolean {
  return policy.queryClass !== "command" && !nonRetryable.has(code) && attempt < policy.retryLimit;
}
export function queryKey(
  contract: string,
  departmentRef: string,
  operationId: string,
  resourceRef?: string,
): readonly string[] {
  return resourceRef
    ? [contract, departmentRef, operationId, resourceRef]
    : [contract, departmentRef, operationId];
}
export interface PolicyError {
  readonly code: ProblemCode;
}
export function toQueryDefaults(policy: QueryPolicy) {
  return {
    staleTime: policy.staleMs,
    gcTime: policy.cacheMs,
    retry: (failureCount: number, error: PolicyError) =>
      shouldRetry(policy, failureCount, error.code),
    refetchInterval: policy.pollMs ?? false,
    networkMode: "online" as const,
  };
}
export function createBoundedQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 0,
        gcTime: 0,
        retry: false,
        refetchOnWindowFocus: false,
        networkMode: "online",
      },
      mutations: { retry: false, networkMode: "online" },
    },
  });
}
export const p52GeneratedReadPolicies = Object.freeze({
  commandSummary: defineQueryPolicy({
    operationId: "generatedCommandSummary",
    queryClass: "summary",
    staleMs: 15_000,
    cacheMs: 60_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  viewportFeatures: defineQueryPolicy({
    operationId: "generatedViewportFeatures",
    queryClass: "summary",
    staleMs: 10_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  authoritativeList: defineQueryPolicy({
    operationId: "generatedSpatialList",
    queryClass: "queue",
    staleMs: 10_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  recordDetail: defineQueryPolicy({
    operationId: "generatedSpatialDetail",
    queryClass: "detail",
    staleMs: 30_000,
    cacheMs: 60_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
});
export const p53GeneratedReadPolicies = Object.freeze({
  cameraCatalogue: defineQueryPolicy({
    operationId: "listGeneratedCameras",
    queryClass: "queue",
    staleMs: 10_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  cameraDetail: defineQueryPolicy({
    operationId: "getGeneratedCamera",
    queryClass: "detail",
    staleMs: 15_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  streamDiagnostics: defineQueryPolicy({
    operationId: "getGeneratedStreamDiagnostics",
    queryClass: "detail",
    staleMs: 10_000,
    cacheMs: 20_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  playbackSession: defineQueryPolicy({
    operationId: "requestGeneratedPlayback",
    queryClass: "command",
    staleMs: 0,
    cacheMs: 0,
    retryLimit: 0,
    pollMs: null,
    persist: false,
  }),
});
export const p54GeneratedPolicies = Object.freeze({
  hypothesisQueue: defineQueryPolicy({
    operationId: "listGeneratedHypotheses",
    queryClass: "queue",
    staleMs: 10_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  intelligenceDetail: defineQueryPolicy({
    operationId: "getGeneratedIntelligenceDetail",
    queryClass: "detail",
    staleMs: 15_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  relationshipProjection: defineQueryPolicy({
    operationId: "getGeneratedRelationships",
    queryClass: "detail",
    staleMs: 15_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  reviewPolicy: defineQueryPolicy({
    operationId: "getGeneratedReviewPolicy",
    queryClass: "configuration",
    staleMs: 0,
    cacheMs: 0,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  reviewCommand: defineQueryPolicy({
    operationId: "recordGeneratedReview",
    queryClass: "command",
    staleMs: 0,
    cacheMs: 0,
    retryLimit: 0,
    pollMs: null,
    persist: false,
  }),
});
export const p55GeneratedPolicies = Object.freeze({
  investigationQueue: defineQueryPolicy({
    operationId: "generatedInvestigationQueue",
    queryClass: "queue",
    staleMs: 10_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  timelinePage: defineQueryPolicy({
    operationId: "generatedInvestigationTimeline",
    queryClass: "queue",
    staleMs: 10_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  reconstruction: defineQueryPolicy({
    operationId: "generatedInvestigationReconstruction",
    queryClass: "detail",
    staleMs: 0,
    cacheMs: 0,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  evidenceDetail: defineQueryPolicy({
    operationId: "generatedEvidenceDetail",
    queryClass: "detail",
    staleMs: 15_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  conflictCommand: defineQueryPolicy({
    operationId: "generatedConflictReconsideration",
    queryClass: "command",
    staleMs: 0,
    cacheMs: 0,
    retryLimit: 0,
    pollMs: null,
    persist: false,
  }),
});
export const p56GeneratedPolicies = Object.freeze({
  administrationList: defineQueryPolicy({
    operationId: "generatedAdministrationList",
    queryClass: "queue",
    staleMs: 15_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  securityProjection: defineQueryPolicy({
    operationId: "generatedSecurityProjection",
    queryClass: "detail",
    staleMs: 10_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  platformOperations: defineQueryPolicy({
    operationId: "generatedPlatformOperations",
    queryClass: "queue",
    staleMs: 10_000,
    cacheMs: 30_000,
    retryLimit: 1,
    pollMs: null,
    persist: false,
  }),
  changePreview: defineQueryPolicy({
    operationId: "generatedChangePreview",
    queryClass: "command",
    staleMs: 0,
    cacheMs: 0,
    retryLimit: 0,
    pollMs: null,
    persist: false,
  }),
});
