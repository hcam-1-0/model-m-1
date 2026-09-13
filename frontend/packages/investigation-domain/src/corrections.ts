import type { CorrectionRetractionRecord } from "../../investigation-contracts/src";

export function validateAppendOnlyCorrection(
  record: CorrectionRetractionRecord,
): readonly string[] {
  const failures: string[] = [];
  const runtimeRecord = record as unknown as Readonly<Record<string, unknown>>;
  if (record.predecessorRef === record.successorRef) failures.push("lineage_cycle");
  if (runtimeRecord.rewritesHistory !== false) failures.push("history_rewrite_forbidden");
  if (!record.reasonCode || record.reasonCode.length > 64) failures.push("invalid_reason_code");
  if (record.impactTargets.length === 0 || record.impactTargets.length > 100)
    failures.push("invalid_impact_target_count");
  return failures;
}
export function correctionLineage(records: readonly CorrectionRetractionRecord[]) {
  return records.map((record) => ({
    predecessorRef: record.predecessorRef,
    successorRef: record.successorRef,
    kind: record.kind,
    retained: true as const,
  }));
}
