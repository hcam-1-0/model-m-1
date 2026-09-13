export const intelligenceProblemCodes = [
  "department_denied",
  "capability_denied",
  "stale_policy",
  "stale_revision",
  "etag_mismatch",
  "duplicate_actor",
  "quorum_incomplete",
  "correction_pending",
  "producer_unavailable",
  "invalid_generated_record",
] as const;
export type IntelligenceProblemCode = (typeof intelligenceProblemCodes)[number];
export function safeIntelligenceProblem(value: unknown): IntelligenceProblemCode {
  return intelligenceProblemCodes.includes(value as IntelligenceProblemCode)
    ? (value as IntelligenceProblemCode)
    : "producer_unavailable";
}
