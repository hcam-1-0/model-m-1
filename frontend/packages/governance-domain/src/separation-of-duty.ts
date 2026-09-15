export type SodReason = "allowed" | "self_approval" | "duplicate_actor" | "quorum_incomplete";
export function evaluateSeparationOfDuty(input: {
  readonly requesterRef: string;
  readonly actorRef: string;
  readonly priorActorRefs: readonly string[];
  readonly requiredApprovals: number;
}): { readonly allowed: boolean; readonly reason: SodReason; readonly remaining: number } {
  if (input.actorRef === input.requesterRef)
    return { allowed: false, reason: "self_approval", remaining: input.requiredApprovals };
  if (input.priorActorRefs.includes(input.actorRef))
    return { allowed: false, reason: "duplicate_actor", remaining: input.requiredApprovals };
  const remaining = Math.max(0, input.requiredApprovals - input.priorActorRefs.length - 1);
  return { allowed: true, reason: remaining ? "quorum_incomplete" : "allowed", remaining };
}
