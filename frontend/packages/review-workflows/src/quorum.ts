import type { ReviewPolicy, ReviewRecord } from "../../intelligence-contracts/src";

export interface QuorumProjection {
  readonly reached: boolean;
  readonly approvals: number;
  readonly required: number;
  readonly independentActors: number;
  readonly serverAuthoritative: true;
}
export function projectQuorum(
  policy: ReviewPolicy,
  reviews: readonly ReviewRecord[],
): QuorumProjection {
  const independent = new Set(reviews.map((review) => review.actorRef));
  const approvals = reviews.filter((review) => review.outcome === "confirm_for_record").length;
  return {
    reached: approvals >= policy.requiredApprovals && independent.size >= policy.requiredApprovals,
    approvals,
    required: policy.requiredApprovals,
    independentActors: independent.size,
    serverAuthoritative: true,
  };
}
