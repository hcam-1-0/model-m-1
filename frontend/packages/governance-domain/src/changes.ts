import type { ChangeRequest, ChangeStatus } from "../../admin-contracts/src";
const transitions: Readonly<Record<ChangeStatus, readonly ChangeStatus[]>> = {
  draft: ["submitted", "superseded"],
  submitted: ["independent_review", "rejected", "superseded"],
  independent_review: ["approved_non_effective", "rejected", "superseded"],
  approved_non_effective: ["superseded"],
  rejected: ["superseded"],
  superseded: [],
};
export function canTransitionChange(from: ChangeStatus, to: ChangeStatus): boolean {
  return transitions[from].includes(to);
}
export function transitionChange(request: ChangeRequest, to: ChangeStatus): ChangeRequest | null {
  if (!canTransitionChange(request.status, to)) return null;
  return {
    ...request,
    status: to,
    resourceRevision: request.resourceRevision + 1,
    etag: `"SYN-CHANGE-ETAG-${request.resourceRevision + 1}"`,
    effective: false,
  };
}
