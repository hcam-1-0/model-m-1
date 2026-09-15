export interface MutationEnvelope {
  readonly revision: number;
  readonly etag: string;
  readonly idempotencyKey: string;
  readonly deliberateReconsideration: boolean;
}
export type MutationDecision =
  | { readonly allowed: true; readonly receipt: string }
  | {
      readonly allowed: false;
      readonly reason:
        "stale_revision" | "etag_mismatch" | "invalid_idempotency" | "reconsideration_required";
    };
export function authorizeGeneratedMutation(
  envelope: MutationEnvelope,
  expectedRevision: number,
  expectedEtag: string,
  isConflictRetry = false,
): MutationDecision {
  if (!/^SYN-IDEMP-[A-Z0-9-]{8,64}$/u.test(envelope.idempotencyKey))
    return { allowed: false, reason: "invalid_idempotency" };
  if (envelope.revision !== expectedRevision) return { allowed: false, reason: "stale_revision" };
  if (envelope.etag !== expectedEtag) return { allowed: false, reason: "etag_mismatch" };
  if (isConflictRetry && !envelope.deliberateReconsideration)
    return { allowed: false, reason: "reconsideration_required" };
  return { allowed: true, receipt: `SYN-RECEIPT-${envelope.idempotencyKey.slice(10)}` };
}
