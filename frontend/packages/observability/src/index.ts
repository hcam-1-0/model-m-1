import type { PortalId, UiState } from "@hcam/contracts";
export type SignalOutcome = "ok" | "denied" | "conflict" | "incompatible" | "timeout" | "failure";
export interface ClientSignal {
  readonly name:
    | "route_view"
    | "operation_outcome"
    | "profile_change"
    | "event_state"
    | "focus_invariant"
    | "gis_renderer_state"
    | "gis_fallback"
    | "source_truth_state"
    | "intelligence_queue_state"
    | "review_outcome"
    | "review_conflict"
    | "correction_state"
    | "investigation_state"
    | "reconstruction_state"
    | "evidence_state"
    | "source_boundary";
  readonly portal: PortalId;
  readonly routeClass: string;
  readonly state: UiState;
  readonly outcome: SignalOutcome;
  readonly durationBucket: "lt100" | "lt500" | "lt2000" | "gte2000";
}
export interface SignalAdapter {
  readonly enabled: boolean;
  emit(signal: ClientSignal): void;
  shutdown(): void;
}
export const disabledSignalAdapter: SignalAdapter = Object.freeze({
  enabled: false,
  emit: () => undefined,
  shutdown: () => undefined,
});
export interface MediaClientSignal {
  readonly name:
    | "session_started"
    | "manifest_loaded"
    | "playing"
    | "stalled"
    | "fallback"
    | "recovering"
    | "teardown";
  readonly transport: "hls" | "native_hls" | "whep" | "none";
  readonly profile:
    "low_resource" | "enhanced_workstation" | "control_room" | "owned_gpu_lab" | "future_server";
  readonly reason: string;
  readonly durationBand: "none" | "under_1s" | "1_to_5s" | "over_5s";
}
const mediaKeys = new Set(["name", "transport", "profile", "reason", "durationBand"]);
export function validateMediaClientSignal(signal: MediaClientSignal): boolean {
  return (
    Object.keys(signal).every((key) => mediaKeys.has(key)) &&
    Object.values(signal).every(
      (value) => typeof value === "string" && /^[a-z0-9_]{1,48}$/u.test(value),
    )
  );
}
const allowedKeys = new Set(["name", "portal", "routeClass", "state", "outcome", "durationBucket"]);
export function validateSignal(signal: ClientSignal): boolean {
  return (
    Object.keys(signal).every((key) => allowedKeys.has(key)) &&
    Object.values(signal).every((value) => typeof value === "string" && value.length <= 64)
  );
}

export type IntelligenceSignalReason =
  | "current"
  | "partial"
  | "stale"
  | "denied"
  | "conflict"
  | "correction"
  | "quorum_incomplete"
  | "confirmed"
  | "abstained"
  | "safe_failure";
export interface IntelligenceSignal {
  readonly name: "queue_load" | "detail_load" | "review_attempt" | "correction_refresh";
  readonly outcome: SignalOutcome;
  readonly reason: IntelligenceSignalReason;
  readonly profile:
    "low_resource" | "enhanced_workstation" | "control_room" | "owned_gpu_lab" | "future_server";
  readonly durationBucket: ClientSignal["durationBucket"];
}
export function validateIntelligenceSignal(signal: IntelligenceSignal): boolean {
  const allowed = new Set(["name", "outcome", "reason", "profile", "durationBucket"]);
  return (
    Object.keys(signal).every((key) => allowed.has(key)) &&
    Object.values(signal).every(
      (value) => typeof value === "string" && /^[a-z0-9_]{1,48}$/u.test(value),
    )
  );
}

export interface InvestigationEvidenceSignal {
  readonly name: "timeline_load" | "reconstruction_load" | "evidence_load" | "conflict_refresh";
  readonly outcome: SignalOutcome;
  readonly reason:
    | "current"
    | "partial"
    | "stale"
    | "denied"
    | "conflict"
    | "correction"
    | "retracted"
    | "safe_failure";
  readonly profile:
    "low_resource" | "enhanced_workstation" | "control_room" | "owned_gpu_lab" | "future_server";
  readonly durationBucket: ClientSignal["durationBucket"];
}
export function validateInvestigationEvidenceSignal(signal: InvestigationEvidenceSignal): boolean {
  const allowed = new Set(["name", "outcome", "reason", "profile", "durationBucket"]);
  return (
    Object.keys(signal).every((key) => allowed.has(key)) &&
    Object.values(signal).every(
      (value) => typeof value === "string" && /^[a-z0-9_]{1,48}$/u.test(value),
    )
  );
}

export interface AdministrationSignal {
  readonly name:
    "projection_load" | "authorization_decision" | "change_preview" | "conflict_refresh";
  readonly portal: "admin" | "security" | "operations";
  readonly lane: "operational" | "security" | "audit" | "evidence" | "administrative";
  readonly outcome: SignalOutcome;
  readonly reason: "current" | "partial" | "stale" | "denied" | "conflict" | "safe_failure";
  readonly durationBucket: ClientSignal["durationBucket"];
}
export function validateAdministrationSignal(signal: AdministrationSignal): boolean {
  const allowed = new Set(["name", "portal", "lane", "outcome", "reason", "durationBucket"]);
  return (
    Object.keys(signal).every((key) => allowed.has(key)) &&
    Object.values(signal).every(
      (value) => typeof value === "string" && /^[a-z0-9_]{1,48}$/u.test(value),
    )
  );
}
