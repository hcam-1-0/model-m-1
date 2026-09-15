export const securityProblemCodes = [
  "denied",
  "department_mismatch",
  "purpose_mismatch",
  "capability_missing",
  "session_stale",
  "lane_mismatch",
  "projection_stale",
  "producer_unavailable",
  "safe_failure",
] as const;
export type SecurityProblemCode = (typeof securityProblemCodes)[number];
export function safeSecurityProblem(value: unknown): SecurityProblemCode {
  return securityProblemCodes.includes(value as SecurityProblemCode)
    ? (value as SecurityProblemCode)
    : "safe_failure";
}
