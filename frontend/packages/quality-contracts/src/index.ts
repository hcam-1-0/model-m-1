export const qualityContractVersion = "1.0.0" as const;

export const qualitySurfaces = [
  "command",
  "gis",
  "camera_live",
  "intelligence",
  "investigation",
  "evidence",
  "admin",
  "security",
  "platform_operations",
] as const;
export type QualitySurface = (typeof qualitySurfaces)[number];

export const mandatoryStates = [
  "loading",
  "empty",
  "partial",
  "fresh",
  "stale",
  "degraded",
  "denied",
  "conflict",
  "failure",
  "recovery",
  "offline",
  "unsupported",
  "session_expired",
  "scope_changed",
  "event_gap",
  "correction",
  "retraction",
  "abstention",
  "pending_review",
  "non_effective",
] as const;
export type MandatoryState = (typeof mandatoryStates)[number];

export const journeyDefinitions = [
  {
    id: "J01",
    title: "situation_to_mandatory_review",
    surfaces: ["command", "gis", "intelligence"],
  },
  {
    id: "J02",
    title: "reviewed_proposal_to_investigation",
    surfaces: ["intelligence", "investigation"],
  },
  {
    id: "J03",
    title: "investigation_to_evidence_reference",
    surfaces: ["investigation", "evidence"],
  },
  {
    id: "J04",
    title: "correction_and_retraction_propagation",
    surfaces: ["intelligence", "investigation", "evidence", "command"],
  },
  {
    id: "J05",
    title: "gis_to_camera_diagnostics_to_live_workspace",
    surfaces: ["gis", "camera_live"],
  },
  {
    id: "J06",
    title: "monitor_wall_admission_and_profile_downgrade",
    surfaces: ["camera_live", "platform_operations"],
  },
  {
    id: "J07",
    title: "platform_degradation_response",
    surfaces: ["command", "platform_operations", "security"],
  },
  {
    id: "J08",
    title: "administrative_proposal_and_separation_of_duty",
    surfaces: ["admin", "security"],
  },
  { id: "J09", title: "access_revocation_and_department_transition", surfaces: qualitySurfaces },
  { id: "J10", title: "event_gap_and_authoritative_recovery", surfaces: qualitySurfaces },
  {
    id: "J11",
    title: "session_expiry_during_consequential_review",
    surfaces: ["intelligence", "admin", "investigation"],
  },
  {
    id: "J12",
    title: "localized_keyboard_only_command_workflow",
    surfaces: ["command", "gis", "camera_live"],
  },
  {
    id: "J13",
    title: "security_finding_to_supply_chain_evidence",
    surfaces: ["security", "platform_operations"],
  },
  { id: "J14", title: "offline_no_provider_generated_demonstration", surfaces: qualitySurfaces },
] as const satisfies readonly {
  id: string;
  title: string;
  surfaces: readonly QualitySurface[];
}[];
export type JourneyId = (typeof journeyDefinitions)[number]["id"];

export const viewportProfiles = [
  { id: "V01", width: 390, height: 844, label: "compact_touch" },
  { id: "V02", width: 768, height: 1024, label: "tablet_portrait" },
  { id: "V03", width: 1280, height: 720, label: "constrained_laptop" },
  { id: "V04", width: 1440, height: 900, label: "enhanced_workstation" },
  { id: "V05", width: 1920, height: 1080, label: "full_hd_operations" },
  { id: "V06", width: 2560, height: 1440, label: "control_room" },
  { id: "V07", width: 3840, height: 1080, label: "logical_dual_display" },
] as const;
export type ViewportId = (typeof viewportProfiles)[number]["id"];

export const localeTimeProfiles = [
  { id: "L01", locale: "en-IN", timezone: "Asia/Kolkata", mode: "operator" },
  { id: "L02", locale: "gu-IN", timezone: "Asia/Kolkata", mode: "operator" },
  { id: "L03", locale: "hi-IN", timezone: "Asia/Kolkata", mode: "operator" },
  { id: "L04", locale: "qps-ploc", timezone: "Asia/Kolkata", mode: "pseudo_unicode" },
  { id: "L05", locale: "en", timezone: "UTC", mode: "canonical" },
] as const;
export type LocaleTimeId = (typeof localeTimeProfiles)[number]["id"];

export const resourceProfiles = [
  { id: "R01", label: "low_resource_laptop", executable: true },
  { id: "R02", label: "enhanced_workstation", executable: true },
  { id: "R03", label: "control_room", executable: true },
  { id: "R04", label: "gpu_lab_projection", executable: false },
  { id: "R05", label: "future_server_projection", executable: false },
  { id: "R06", label: "kubernetes_projection", executable: false },
] as const;
export type ResourceProfileId = (typeof resourceProfiles)[number]["id"];

export const workloadProfiles = ["C1", "C10", "C50"] as const;
export type WorkloadProfile = (typeof workloadProfiles)[number];

export const generatedCaseAllocation = {
  cross_portal_journeys_and_replay: 512,
  contract_API_event_and_concurrency: 320,
  accessibility: 256,
  localization_time_and_Unicode: 192,
  browser_layout_and_resource_profiles: 256,
  performance_scale_and_bundles: 192,
  resilience: 192,
  security_privacy_and_supply_chain: 128,
} as const;
export type GeneratedCaseCategory = keyof typeof generatedCaseAllocation;

export type ExpectedOutcome =
  | "allow_generated_read"
  | "deny"
  | "degrade"
  | "recover_by_authoritative_refetch"
  | "abstain"
  | "remain_non_effective";

export interface GeneratedQualityCase {
  readonly ref: `SYN-P57-CASE-${string}`;
  readonly generatedOnly: true;
  readonly category: GeneratedCaseCategory;
  readonly sequence: number;
  readonly seed: number;
  readonly journeyId: JourneyId;
  readonly state: MandatoryState;
  readonly surface: QualitySurface;
  readonly viewportId: ViewportId;
  readonly localeTimeId: LocaleTimeId;
  readonly resourceProfileId: ResourceProfileId;
  readonly workload: WorkloadProfile;
  readonly expected: ExpectedOutcome;
  readonly authority: "read_only" | "mandatory_review" | "non_effective";
  readonly truth:
    "observation" | "inference" | "hypothesis" | "proposal" | "qualified_system_state";
}

export interface QualityResult {
  readonly ref: string;
  readonly status: "pass" | "fail" | "blocked" | "unsupported";
  readonly reason: string;
}

export interface QualityEvidenceNode {
  readonly id: string;
  readonly kind: "requirement" | "case" | "result" | "claim" | "limitation" | "artifact";
  readonly dependsOn: readonly string[];
}

export interface HardBudget {
  readonly metric:
    | "interaction_ms"
    | "long_task_ms"
    | "map_idle_ms"
    | "query_fanout"
    | "memory_mib"
    | "bundle_kib"
    | "media_admission";
  readonly maximum: number;
  readonly context: string;
}

export const prohibitedEvidenceKeys = [
  "password",
  "secret",
  "token",
  "credential",
  "biometric",
  "owner_name",
  "registration_number",
  "watchlist_identity",
  "raw_payload",
  "camera_locator",
  "media_url",
] as const;

export const terminalReasonCodes = [
  "quality_pass",
  "contract_invalid",
  "authority_changed",
  "truth_overclaimed",
  "generated_boundary_breached",
  "hard_budget_exceeded",
  "browser_unavailable",
  "evidence_cycle",
  "prohibited_field",
  "replay_drift",
  "unresolved_blocker",
] as const;
export type TerminalReasonCode = (typeof terminalReasonCodes)[number];
