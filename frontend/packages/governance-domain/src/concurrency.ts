export interface ConcurrencyInput {
  readonly expectedEtag: string;
  readonly actualEtag: string;
  readonly expectedRevision: number;
  readonly actualRevision: number;
  readonly idempotencyKey: string;
  readonly existingReceiptKey: string | null;
}
export type ConcurrencyResult =
  "proceed" | "etag_mismatch" | "stale_revision" | "replay" | "idempotency_conflict";
export function resolveConcurrency(input: ConcurrencyInput): ConcurrencyResult {
  if (!/^SYN-IDEMP-[A-Z0-9-]{8,64}$/u.test(input.idempotencyKey)) return "idempotency_conflict";
  if (input.existingReceiptKey === input.idempotencyKey) return "replay";
  if (input.expectedEtag !== input.actualEtag) return "etag_mismatch";
  if (input.expectedRevision !== input.actualRevision) return "stale_revision";
  return "proceed";
}
export const conflictRecovery = Object.freeze({
  automaticRetry: false,
  requiresRefetch: true,
  requiresComparison: true,
  requiresDeliberateReconsideration: true,
} as const);
