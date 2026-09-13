import type { Freshness, Page, ResourceId } from "@hcam/contracts";

export const investigationGeneratedMarker = "HCAM-GENERATED-NON-OPERATIONAL" as const;
export const timelineKinds = [
  "observation",
  "inference",
  "hypothesis",
  "candidate",
  "proposed_alert",
  "review",
  "correction",
  "retraction",
  "relationship",
  "action_record",
  "system_record",
] as const;
export type TimelineKind = (typeof timelineKinds)[number];
export type InvestigationState =
  "open" | "under_review" | "correction_pending" | "retracted" | "closed" | "unknown";
export type TimelineAuthority = "record_sequence";
export type EventTimePrecision = "exact" | "second" | "minute" | "range" | "unknown";
export type ClockCondition = "synchronized" | "estimated" | "skewed" | "unknown";

export interface QualifiedEventTime {
  readonly value: string | null;
  readonly rangeStart: string | null;
  readonly rangeEnd: string | null;
  readonly precision: EventTimePrecision;
  readonly source: string;
  readonly clockCondition: ClockCondition;
  readonly changesRecordOrder: false;
}
export interface InvestigationSummary {
  readonly ref: ResourceId;
  readonly title: string;
  readonly state: InvestigationState;
  readonly priority: "urgent_review" | "elevated_review" | "standard_review" | "unknown";
  readonly departmentRef: string;
  readonly purposeCode: string;
  readonly latestRecordSequence: number;
  readonly timelineEntries: number;
  readonly evidenceReferences: number;
  readonly correctionStatus: "clear" | "pending" | "incomplete";
  readonly freshness: Freshness;
  readonly etag: string;
  readonly revision: number;
  readonly generated: true;
}
export interface InvestigationQueue extends Page<InvestigationSummary> {
  readonly contractVersion: "1.0.0";
  readonly marker: typeof investigationGeneratedMarker;
  readonly departmentRef: string;
  readonly orderedBy: "server_priority_then_record_sequence_then_ref";
  readonly stableAnchor: string;
}
export interface TimelineEntry {
  readonly ref: ResourceId;
  readonly investigationRef: ResourceId;
  readonly recordSequence: number;
  readonly recordedAt: string;
  readonly eventTime: QualifiedEventTime;
  readonly kind: TimelineKind;
  readonly label: string;
  readonly summary: string;
  readonly authority:
    "source_report" | "analytical_only" | "human_record" | "historical_record" | "system_record";
  readonly revisionRef: string;
  readonly predecessorRef: ResourceId | null;
  readonly supersedesRef: ResourceId | null;
  readonly sourceRef: string | null;
  readonly limitations: readonly string[];
  readonly generated: true;
}
export interface TimelinePage extends Page<TimelineEntry> {
  readonly contractVersion: "1.0.0";
  readonly marker: typeof investigationGeneratedMarker;
  readonly investigationRef: ResourceId;
  readonly authority: TimelineAuthority;
  readonly stableAnchor: string;
  readonly revisionRef: string;
  readonly completeThroughSequence: number;
}
export interface InvestigationHealth {
  readonly projection: "ready" | "partial" | "stale" | "degraded" | "unavailable";
  readonly timeline: "ready" | "partial" | "stale" | "degraded" | "unavailable";
  readonly reconstruction: "ready" | "partial" | "stale" | "degraded" | "unavailable";
  readonly evidence: "ready" | "partial" | "stale" | "degraded" | "unavailable";
  readonly producerGapCount: 36;
  readonly generated: true;
}
