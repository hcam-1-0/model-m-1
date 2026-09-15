export const adminProblemCodes = [
  "denied",
  "department_mismatch",
  "purpose_mismatch",
  "capability_missing",
  "policy_stale",
  "etag_mismatch",
  "duplicate_actor",
  "idempotency_conflict",
  "producer_unavailable",
  "safe_failure",
] as const;
export type AdminProblemCode = (typeof adminProblemCodes)[number];
export function safeAdminProblem(value: unknown): AdminProblemCode {
  return adminProblemCodes.includes(value as AdminProblemCode)
    ? (value as AdminProblemCode)
    : "safe_failure";
}
