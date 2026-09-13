import type { RecoveryPreview } from "../../operations-contracts/src";
export function recoveryQualification(preview: RecoveryPreview): readonly string[] {
  const limitations = ["Generated preview only", "No recovery action is available"];
  if (!preview.lastEvidenceRef) return [...limitations, "No generated evidence reference"];
  return limitations;
}
export const recoveryControls = Object.freeze({
  backup: false,
  restore: false,
  failover: false,
  maintenance: false,
  disasterRecovery: false,
} as const);
