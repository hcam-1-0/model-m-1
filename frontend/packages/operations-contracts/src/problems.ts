export const operationsProblemCodes = [
  "denied",
  "department_mismatch",
  "projection_stale",
  "dependency_unavailable",
  "queue_degraded",
  "evidence_missing",
  "producer_unavailable",
  "safe_failure",
] as const;
export type OperationsProblemCode = (typeof operationsProblemCodes)[number];
export function safeOperationsProblem(value: unknown): OperationsProblemCode {
  return operationsProblemCodes.includes(value as OperationsProblemCode)
    ? (value as OperationsProblemCode)
    : "safe_failure";
}
