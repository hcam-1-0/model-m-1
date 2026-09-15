export const securityGeneratedMarker = "HCAM-GENERATED-NON-OPERATIONAL" as const;
export const signalLanes = [
  "operational",
  "security",
  "audit",
  "evidence",
  "administrative",
] as const;
export type SignalLane = (typeof signalLanes)[number];
export type AssuranceState = "current" | "partial" | "stale" | "unknown" | "unavailable";
export interface QualifiedSecurityProjection {
  readonly source: "generated_fixture";
  readonly state: AssuranceState;
  readonly observedAt: string;
  readonly staleAt: string;
  readonly completeness: "complete" | "partial" | "unknown";
  readonly limitations: readonly string[];
  readonly operationalTruth: false;
  readonly generated: true;
}
export interface DenialActivity {
  readonly ref: string;
  readonly lane: "security";
  readonly category: "authorization" | "scope" | "policy" | "session" | "input";
  readonly reasonCode: string;
  readonly actorClass: string;
  readonly departmentRef: string;
  readonly recordedAt: string;
  readonly rawPayloadRetained: false;
  readonly generated: true;
}
export interface AuditReference {
  readonly ref: string;
  readonly lane: "audit";
  readonly actionClass: string;
  readonly outcome: "allowed" | "denied" | "conflict" | "unknown";
  readonly actorRef: string;
  readonly targetRef: string;
  readonly sequence: number;
  readonly immutable: true;
  readonly generated: true;
}
export interface ComplianceControl {
  readonly ref: string;
  readonly framework: string;
  readonly title: string;
  readonly state: AssuranceState;
  readonly evidenceRefs: readonly string[];
  readonly exceptionRef: string | null;
  readonly attested: false;
  readonly generated: true;
}
