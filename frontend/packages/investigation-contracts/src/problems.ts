export const investigationProblemCodes = [
  "department_denied",
  "purpose_denied",
  "capability_denied",
  "object_scope_denied",
  "stale_revision",
  "etag_mismatch",
  "idempotency_conflict",
  "stable_anchor_expired",
  "reconstruction_incomplete",
  "impact_closure_incomplete",
  "evidence_unavailable",
  "source_resolution_forbidden",
  "policy_operation_forbidden",
  "producer_unavailable",
] as const;
export type InvestigationProblemCode = (typeof investigationProblemCodes)[number];
export function safeInvestigationProblem(value: unknown): InvestigationProblemCode {
  return investigationProblemCodes.includes(value as InvestigationProblemCode)
    ? (value as InvestigationProblemCode)
    : "producer_unavailable";
}
