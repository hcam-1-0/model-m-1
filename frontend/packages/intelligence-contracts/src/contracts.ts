import type { Freshness, Page, ResourceId } from "@hcam/contracts";

export const generatedMarker = "HCAM-GENERATED-NON-OPERATIONAL" as const;
export const analyticalConceptKinds = [
  "observation",
  "inference",
  "hypothesis",
  "candidate",
  "proposed_alert",
  "review",
  "correction",
  "lifecycle",
] as const;
export type AnalyticalConceptKind = (typeof analyticalConceptKinds)[number];
export type AuthorityClass =
  "source_fact" | "analytical_only" | "human_decision" | "historical_record";
export type QueueKind =
  "hypothesis" | "correlation_run" | "proposed_alert" | "mandatory_review" | "correction";
export type PriorityBand = "urgent_review" | "elevated_review" | "standard_review" | "unknown";

export interface AnalyticalConcept {
  readonly ref: ResourceId;
  readonly kind: AnalyticalConceptKind;
  readonly label: string;
  readonly authority: AuthorityClass;
  readonly state: string;
  readonly occurredAt: string;
  readonly sourceRevision: string;
  readonly departmentRef: string;
  readonly generated: true;
}
export interface QueueItem {
  readonly ref: ResourceId;
  readonly queue: QueueKind;
  readonly title: string;
  readonly summary: string;
  readonly concept: AnalyticalConceptKind;
  readonly priority: PriorityBand;
  readonly state: string;
  readonly ageMinutes: number;
  readonly revision: number;
  readonly etag: string;
  readonly freshness: Freshness;
  readonly generated: true;
}
export interface IntelligenceQueue extends Page<QueueItem> {
  readonly contractVersion: "1.0.0";
  readonly marker: typeof generatedMarker;
  readonly queue: QueueKind;
  readonly departmentRef: string;
  readonly orderedBy: "server_priority_then_age_then_ref";
}
export type EvidenceRole = "supports" | "contradicts" | "ambiguous" | "missing";
export interface EvidenceField {
  readonly field: string;
  readonly displayValue: string;
  readonly role: EvidenceRole;
  readonly confidenceBand: "high" | "medium" | "low" | "not_scored";
  readonly calibrated: boolean;
  readonly stale: boolean;
  readonly provenanceRef: ResourceId;
  readonly limitation: string;
}
export interface CandidateEvidence {
  readonly candidateRef: ResourceId;
  readonly hypothesisRef: ResourceId;
  readonly fields: readonly EvidenceField[];
  readonly abstained: boolean;
  readonly identityEstablished: false;
  readonly generated: true;
}
export interface RuleTraceStep {
  readonly sequence: number;
  readonly nodeType: "input" | "predicate" | "temporal" | "geometry" | "result" | "abstention";
  readonly label: string;
  readonly result: "pass" | "fail" | "unknown" | "abstain";
  readonly normalizedInput: string;
  readonly limitation: string | null;
}
export interface RuleTrace {
  readonly evaluationRef: ResourceId;
  readonly ruleRef: ResourceId;
  readonly ruleRevision: number;
  readonly normalizedAt: string;
  readonly timerWindow: string;
  readonly result: "matched" | "not_matched" | "abstained";
  readonly exactSteps: readonly RuleTraceStep[];
  readonly generated: true;
}
export interface RelationshipNode {
  readonly ref: ResourceId;
  readonly label: string;
  readonly kind: AnalyticalConceptKind;
  readonly state: string;
}
export interface RelationshipEdge {
  readonly ref: ResourceId;
  readonly fromRef: ResourceId;
  readonly toRef: ResourceId;
  readonly relationship: "derived_from" | "supports" | "contradicts" | "correlates_with";
  readonly confidenceBand: "high" | "medium" | "low" | "not_scored";
}
export interface RelationshipProjection {
  readonly nodes: readonly RelationshipNode[];
  readonly edges: readonly RelationshipEdge[];
  readonly nodeCeiling: 12 | 50 | 100;
  readonly edgeCeiling: 24 | 100 | 200;
  readonly truncated: boolean;
  readonly authoritativeRepresentation: "tables";
}
export interface SpatialRecord {
  readonly ref: ResourceId;
  readonly label: string;
  readonly zoneRef: string;
  readonly longitude: number;
  readonly latitude: number;
  readonly concept: AnalyticalConceptKind;
  readonly state: string;
}
export interface SpatialProjection {
  readonly records: readonly SpatialRecord[];
  readonly generated: true;
  readonly tileNetworkUsed: false;
  readonly authoritativeRepresentation: "table";
}
export interface ProposedAlert {
  readonly ref: ResourceId;
  readonly semanticIdentity: string;
  readonly title: string;
  readonly priority: PriorityBand;
  readonly lifecycle:
    "proposed" | "in_review" | "confirmed_for_record" | "rejected" | "retracted" | "corrected";
  readonly hypothesisRef: ResourceId;
  readonly candidateRefs: readonly ResourceId[];
  readonly identityEstablished: false;
  readonly operationalAuthority: false;
  readonly etag: string;
  readonly revision: number;
  readonly generated: true;
}
export interface ReviewPolicy {
  readonly policyRevision: string;
  readonly requiredApprovals: number;
  readonly requiredCapabilities: readonly string[];
  readonly requireIndependentActors: true;
  readonly allowedOutcomes: readonly ReviewOutcome[];
}
export type ReviewOutcome = "confirm_for_record" | "reject" | "abstain" | "request_more_context";
export interface ReviewRecord {
  readonly reviewRef: ResourceId;
  readonly alertRef: ResourceId;
  readonly actorRef: string;
  readonly outcome: ReviewOutcome;
  readonly reasonCode: string;
  readonly policyRevision: string;
  readonly decidedAt: string;
  readonly revision: number;
  readonly generated: true;
}
export interface CorrectionImpact {
  readonly correctionRef: ResourceId;
  readonly correctedRef: ResourceId;
  readonly impactedRefs: readonly ResourceId[];
  readonly viewsMarkedStale: readonly string[];
  readonly mutationDisabled: true;
  readonly requiresRefetch: true;
  readonly historyRewritten: false;
}
