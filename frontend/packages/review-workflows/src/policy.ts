import type { ReviewPolicy, ReviewRecord } from "../../intelligence-contracts/src";

export type PolicyDenial =
  "allowed" | "stale_policy" | "forbidden_role" | "duplicate_actor" | "outcome_denied";
export function evaluateReviewPolicy(
  policy: ReviewPolicy,
  policyRevision: string,
  actorCapabilities: readonly string[],
  actorRef: string,
  records: readonly ReviewRecord[],
  outcome: ReviewRecord["outcome"],
): PolicyDenial {
  if (policy.policyRevision !== policyRevision) return "stale_policy";
  if (!policy.requiredCapabilities.every((capability) => actorCapabilities.includes(capability)))
    return "forbidden_role";
  if (!policy.allowedOutcomes.includes(outcome)) return "outcome_denied";
  if (records.some((record) => record.actorRef === actorRef)) return "duplicate_actor";
  return "allowed";
}
