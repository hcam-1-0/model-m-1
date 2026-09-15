export const operationsGeneratedMarker = "HCAM-GENERATED-NON-OPERATIONAL" as const;
export type OperationalState =
  "healthy" | "degraded" | "stale" | "recovering" | "unknown" | "unavailable";
export interface OperationalTruth {
  readonly source: "generated_fixture";
  readonly observedAt: string;
  readonly staleAt: string;
  readonly completeness: "complete" | "partial" | "unknown";
  readonly limitations: readonly string[];
  readonly productionClaim: false;
}
export interface ServiceHealth {
  readonly ref: string;
  readonly label: string;
  readonly domain: string;
  readonly state: OperationalState;
  readonly dependencyRefs: readonly string[];
  readonly latencyBucket: "lt100" | "lt500" | "lt2000" | "unknown";
  readonly saturationBand: "low" | "moderate" | "high" | "unknown";
  readonly truth: OperationalTruth;
  readonly generated: true;
}
export interface QueueHealth {
  readonly ref: string;
  readonly label: string;
  readonly depthBand: "empty" | "low" | "moderate" | "high" | "unknown";
  readonly oldestAgeBand: "lt30s" | "lt2m" | "lt10m" | "unknown";
  readonly leaseState: "current" | "recovering" | "expired" | "unknown";
  readonly retryBand: "none" | "low" | "elevated" | "unknown";
  readonly deadLetterBand: "none" | "present" | "unknown";
  readonly generated: true;
}
export interface SloProjection {
  readonly ref: string;
  readonly label: string;
  readonly indicator: string;
  readonly objective: string;
  readonly window: string;
  readonly budgetState: "healthy" | "watch" | "exhausted" | "unknown";
  readonly targetAuthority: "generated_non_production";
  readonly generated: true;
}
