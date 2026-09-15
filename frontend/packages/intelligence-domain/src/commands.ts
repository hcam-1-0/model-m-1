import type { ResourceId } from "@hcam/contracts";
import type { ReviewOutcome } from "../../intelligence-contracts/src";
import { assertSafeReasonCode } from "./reasons";

export interface ReviewCommand {
  readonly alertRef: ResourceId;
  readonly outcome: ReviewOutcome;
  readonly reasonCode: string;
  readonly expectedRevision: number;
  readonly ifMatch: string;
  readonly idempotencyKey: string;
  readonly canonicalFingerprint: string;
  readonly policyRevision: string;
}
export function validateReviewCommand(command: ReviewCommand): ReviewCommand {
  if (!/^SYN-[A-Z0-9-]{4,80}$/.test(command.alertRef)) throw new Error("invalid_alert_ref");
  if (!/^"SYN-ETAG-\d+"$/.test(command.ifMatch)) throw new Error("weak_etag");
  if (!Number.isInteger(command.expectedRevision) || command.expectedRevision < 1)
    throw new Error("invalid_revision");
  if (!/^SYN-IDEMP-[A-Z0-9-]{8,80}$/.test(command.idempotencyKey))
    throw new Error("invalid_idempotency_key");
  if (!/^[A-F0-9]{64}$/.test(command.canonicalFingerprint)) throw new Error("invalid_fingerprint");
  assertSafeReasonCode(command.reasonCode);
  return Object.freeze({ ...command });
}
