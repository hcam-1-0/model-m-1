import type { Freshness, ResourceId } from "@hcam/contracts";

export type EvidenceAvailability = "referenced" | "unavailable" | "unknown";
export type EvidenceIntegrity = "not_checked" | "digest_observed" | "digest_mismatch" | "unknown";
export type EvidenceProvenanceState = "complete" | "partial" | "unknown";
export type EvidenceCustodyState = "recorded" | "partial" | "not_provided" | "unknown";
export type EvidenceSignatureState = "observed" | "not_observed" | "unknown";
export type EvidenceAccessState = "allowed" | "denied" | "unknown";
export type EvidenceLegalAssessment = "not_assessed" | "review_required" | "external_recorded";

export interface OpaqueSourceReference {
  readonly referenceId: string;
  readonly sourceClass: "generated_reference";
  readonly resolved: false;
  readonly renderable: false;
  readonly downloadable: false;
  readonly locatorExposed: false;
}
export interface EvidenceReference {
  readonly ref: ResourceId;
  readonly investigationRef: ResourceId;
  readonly label: string;
  readonly category:
    "document_reference" | "event_reference" | "media_reference" | "derived_reference";
  readonly availability: EvidenceAvailability;
  readonly integrity: EvidenceIntegrity;
  readonly provenance: EvidenceProvenanceState;
  readonly custody: EvidenceCustodyState;
  readonly signature: EvidenceSignatureState;
  readonly access: EvidenceAccessState;
  readonly legalAssessment: EvidenceLegalAssessment;
  readonly digestObservation: string | null;
  readonly source: OpaqueSourceReference;
  readonly freshness: Freshness;
  readonly limitations: readonly string[];
  readonly etag: string;
  readonly revision: number;
  readonly generated: true;
}
export interface EvidenceVerificationEvent {
  readonly ref: ResourceId;
  readonly evidenceRef: ResourceId;
  readonly sequence: number;
  readonly observedAt: string;
  readonly outcome: EvidenceIntegrity;
  readonly digestObservation: string | null;
  readonly truthEstablished: false;
  readonly generated: true;
}
export interface EvidenceHandoff {
  readonly investigationRef: ResourceId;
  readonly evidenceRef: ResourceId;
  readonly purposeCode: string;
  readonly departmentRef: string;
  readonly capability: "evidence.viewer";
  readonly sourceOperationAuthorized: false;
  readonly generated: true;
}
