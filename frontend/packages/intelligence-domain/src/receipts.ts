import type { ResourceId } from "@hcam/contracts";

export interface CommandReceipt {
  readonly receiptRef: ResourceId;
  readonly commandFingerprint: string;
  readonly resultingRevision: number;
  readonly resultingEtag: string;
  readonly recordedAt: string;
  readonly replayed: boolean;
  readonly externalSideEffects: false;
}
export function isCommandReceipt(value: unknown): value is CommandReceipt {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<CommandReceipt>;
  return (
    typeof item.receiptRef === "string" &&
    /^[A-F0-9]{64}$/.test(item.commandFingerprint ?? "") &&
    item.externalSideEffects === false &&
    Number.isInteger(item.resultingRevision)
  );
}
