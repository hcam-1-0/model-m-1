import type { Freshness, ResourceId } from "@hcam/contracts";

export type SourceTruth = "current" | "partial" | "stale" | "unavailable" | "unknown";
export interface CommandMetric {
  readonly id: string;
  readonly label: string;
  readonly value: string;
  readonly detail: string;
  readonly truth: SourceTruth;
}
export interface CommandWorkItem {
  readonly id: ResourceId;
  readonly label: string;
  readonly category: "review" | "investigation" | "source" | "platform";
  readonly band: "critical" | "attention" | "routine" | "unknown";
  readonly occurredAt: string;
  readonly sourceRevision: string;
  readonly generated: true;
}
export interface CommandActivity {
  readonly id: ResourceId;
  readonly at: string;
  readonly title: string;
  readonly detail: string;
  readonly kind: "observation" | "review" | "correction" | "system";
  readonly generated: true;
}
export interface SituationSnapshot {
  readonly contractVersion: "1.0.0";
  readonly marker: "HCAM-GENERATED-NON-OPERATIONAL";
  readonly departmentRef: string;
  readonly revision: string;
  readonly freshness: Freshness;
  readonly metrics: readonly CommandMetric[];
  readonly workItems: readonly CommandWorkItem[];
  readonly activity: readonly CommandActivity[];
  readonly unavailableProducers: readonly string[];
}

const bandRank: Record<CommandWorkItem["band"], number> = {
  critical: 0,
  attention: 1,
  routine: 2,
  unknown: 3,
};
export function sortWorkItems(items: readonly CommandWorkItem[]): readonly CommandWorkItem[] {
  return [...items].sort(
    (left, right) =>
      bandRank[left.band] - bandRank[right.band] ||
      Date.parse(left.occurredAt) - Date.parse(right.occurredAt) ||
      left.id.localeCompare(right.id),
  );
}
export function limitWorkItems(
  items: readonly CommandWorkItem[],
  limit: number,
): readonly CommandWorkItem[] {
  if (!Number.isInteger(limit) || limit < 1 || limit > 100)
    throw new Error("invalid_work_item_limit");
  return sortWorkItems(items).slice(0, limit);
}
export function validateSituationSnapshot(value: unknown): value is SituationSnapshot {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<SituationSnapshot>;
  return (
    item.contractVersion === "1.0.0" &&
    item.marker === "HCAM-GENERATED-NON-OPERATIONAL" &&
    typeof item.departmentRef === "string" &&
    /^SYN-[A-Z0-9-]{3,48}$/.test(item.departmentRef) &&
    Array.isArray(item.metrics) &&
    item.metrics.length <= 24 &&
    Array.isArray(item.workItems) &&
    item.workItems.length <= 100 &&
    Array.isArray(item.activity) &&
    item.activity.length <= 100 &&
    Array.isArray(item.unavailableProducers) &&
    item.unavailableProducers.length === 14
  );
}

export interface InvestigationWorkloadProjection {
  readonly open: number;
  readonly correctionPending: number;
  readonly evidenceReferences: number;
  readonly producerGaps: 36;
  readonly authority: "generated_summary_only";
  readonly generated: true;
}
export function generatedInvestigationWorkload(
  open: number,
  correctionPending: number,
  evidenceReferences: number,
): InvestigationWorkloadProjection {
  const bounded = (value: number) => Math.max(0, Math.min(10_000, Math.trunc(value)));
  return Object.freeze({
    open: bounded(open),
    correctionPending: bounded(correctionPending),
    evidenceReferences: bounded(evidenceReferences),
    producerGaps: 36,
    authority: "generated_summary_only",
    generated: true,
  });
}
