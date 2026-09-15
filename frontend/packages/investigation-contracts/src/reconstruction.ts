import type { ResourceId } from "@hcam/contracts";
import type { TimelineEntry } from "./contracts";

export type ReconstructionCompleteness = "complete" | "partial" | "unknown";
export interface ReconstructionProjection {
  readonly investigationRef: ResourceId;
  readonly requestedRevision: string;
  readonly resolvedRevision: string;
  readonly digest: string;
  readonly completeness: ReconstructionCompleteness;
  readonly includedComponents: readonly string[];
  readonly omittedComponents: readonly string[];
  readonly limitations: readonly string[];
  readonly laterChangesExist: boolean;
  readonly timeline: readonly TimelineEntry[];
  readonly generated: true;
}
export interface RevisionFieldChange {
  readonly field: string;
  readonly before: string;
  readonly after: string;
  readonly meaning: "added" | "removed" | "changed" | "unchanged";
  readonly source: "server_projection";
}
export interface RevisionComparison {
  readonly investigationRef: ResourceId;
  readonly fromRevision: string;
  readonly toRevision: string;
  readonly fromDigest: string;
  readonly toDigest: string;
  readonly changes: readonly RevisionFieldChange[];
  readonly complete: boolean;
  readonly limitations: readonly string[];
  readonly generated: true;
}
export interface ImpactTarget {
  readonly targetRef: ResourceId;
  readonly targetKind: string;
  readonly status: "pending" | "applied" | "blocked" | "failed" | "superseded";
  readonly revision: number;
  readonly limitation: string | null;
}
export interface CorrectionRetractionRecord {
  readonly ref: ResourceId;
  readonly investigationRef: ResourceId;
  readonly kind: "correction" | "retraction";
  readonly predecessorRef: ResourceId;
  readonly successorRef: ResourceId;
  readonly reasonCode: string;
  readonly recordedAt: string;
  readonly actorClass: "generated_reviewer";
  readonly impactTargets: readonly ImpactTarget[];
  readonly rewritesHistory: false;
  readonly generated: true;
}
