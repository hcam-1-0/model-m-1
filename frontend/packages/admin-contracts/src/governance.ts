export const changeKinds = [
  "membership",
  "role_binding",
  "policy_revision",
  "camera_governance",
  "provider_governance",
  "feature_configuration",
  "resource_profile",
  "retention_projection",
] as const;
export type ChangeKind = (typeof changeKinds)[number];
export type ChangeStatus =
  | "draft"
  | "submitted"
  | "independent_review"
  | "approved_non_effective"
  | "rejected"
  | "superseded";
export interface ChangeRequest {
  readonly ref: string;
  readonly kind: ChangeKind;
  readonly status: ChangeStatus;
  readonly departmentRef: string;
  readonly requesterRef: string;
  readonly reviewerRefs: readonly string[];
  readonly requiredApprovals: number;
  readonly policyRevision: string;
  readonly resourceRevision: number;
  readonly etag: string;
  readonly idempotencyKey: string;
  readonly reasonCode: string;
  readonly impactSummary: readonly string[];
  readonly effective: false;
  readonly generated: true;
}
export interface ChangeReceipt {
  readonly requestRef: string;
  readonly receiptRef: string;
  readonly acceptedRevision: number;
  readonly status: ChangeStatus;
  readonly effectApplied: false;
  readonly generated: true;
}
export interface ApprovalDecision {
  readonly requestRef: string;
  readonly actorRef: string;
  readonly outcome: "approve_non_effective" | "reject" | "abstain";
  readonly reasonCode: string;
  readonly expectedEtag: string;
  readonly idempotencyKey: string;
  readonly generated: true;
}
