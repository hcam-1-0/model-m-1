export interface AuthorizationContext {
  readonly actorRef: string | null;
  readonly sessionCurrent: boolean;
  readonly departmentRef: string | null;
  readonly purposeCode: string | null;
  readonly capabilities: readonly string[];
  readonly policyRevision: string | null;
}
export interface AuthorizationTarget {
  readonly departmentRef: string;
  readonly purposeCode: string;
  readonly requiredCapability: string;
  readonly policyRevision: string;
}
export type AuthorizationReason =
  | "allowed"
  | "session_missing"
  | "session_stale"
  | "department_mismatch"
  | "purpose_mismatch"
  | "capability_missing"
  | "policy_stale";
export interface AuthorizationDecision {
  readonly allowed: boolean;
  readonly reason: AuthorizationReason;
  readonly serverAuthoritative: true;
}
export function authorize(
  context: AuthorizationContext,
  target: AuthorizationTarget,
): AuthorizationDecision {
  if (!context.actorRef)
    return { allowed: false, reason: "session_missing", serverAuthoritative: true };
  if (!context.sessionCurrent)
    return { allowed: false, reason: "session_stale", serverAuthoritative: true };
  if (context.departmentRef !== target.departmentRef)
    return { allowed: false, reason: "department_mismatch", serverAuthoritative: true };
  if (context.purposeCode !== target.purposeCode)
    return { allowed: false, reason: "purpose_mismatch", serverAuthoritative: true };
  if (context.policyRevision !== target.policyRevision)
    return { allowed: false, reason: "policy_stale", serverAuthoritative: true };
  if (
    !context.capabilities.includes(target.requiredCapability) &&
    !context.capabilities.includes("administrator")
  )
    return { allowed: false, reason: "capability_missing", serverAuthoritative: true };
  return { allowed: true, reason: "allowed", serverAuthoritative: true };
}
export function projectRlsEquivalent(
  context: AuthorizationContext,
  target: AuthorizationTarget,
): AuthorizationDecision {
  return authorize(context, target);
}
