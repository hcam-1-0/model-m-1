export interface SupplyChainRecord {
  readonly ref: string;
  readonly component: string;
  readonly version: string;
  readonly licenseState: "recorded" | "review_required" | "unknown";
  readonly vulnerabilityState: "current" | "stale" | "unavailable" | "unknown";
  readonly provenanceState: "verified_reference" | "unverified" | "unknown";
  readonly sbomRef: string;
  readonly scannerExecuted: false;
  readonly generated: true;
}
export interface ProviderPosture {
  readonly ref: string;
  readonly destinationRuleRef: string;
  readonly secretRefPresent: boolean;
  readonly secretValueAvailable: false;
  readonly certificateState: "declared" | "stale" | "unknown";
  readonly networkContacted: false;
  readonly generated: true;
}
export function laneAllowsPayload(lane: string, payloadClass: string): boolean {
  const allowed: Readonly<Record<string, readonly string[]>> = {
    operational: ["health", "queue", "slo"],
    security: ["denial", "posture", "anomaly"],
    audit: ["audit_reference"],
    evidence: ["evidence_reference"],
    administrative: ["change_reference"],
  };
  return (allowed[lane] ?? []).includes(payloadClass);
}
