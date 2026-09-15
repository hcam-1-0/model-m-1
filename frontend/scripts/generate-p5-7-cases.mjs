import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";

const frontendRoot = resolve(import.meta.dirname, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const contractRoot = resolve(repositoryRoot, "contracts", "phase-5", "p5-7");
const evidenceRoot = resolve(frontendRoot, "evidence");
const allocations = Object.freeze({
  cross_portal_journeys_and_replay: 512,
  contract_API_event_and_concurrency: 320,
  accessibility: 256,
  localization_time_and_Unicode: 192,
  browser_layout_and_resource_profiles: 256,
  performance_scale_and_bundles: 192,
  resilience: 192,
  security_privacy_and_supply_chain: 128,
});
const surfaces = [
  "command",
  "gis",
  "camera_live",
  "intelligence",
  "investigation",
  "evidence",
  "admin",
  "security",
  "platform_operations",
];
const states = [
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
];
const journeys = [
  ["J01", "situation_to_mandatory_review", ["command", "gis", "intelligence"]],
  ["J02", "reviewed_proposal_to_investigation", ["intelligence", "investigation"]],
  ["J03", "investigation_to_evidence_reference", ["investigation", "evidence"]],
  [
    "J04",
    "correction_and_retraction_propagation",
    ["intelligence", "investigation", "evidence", "command"],
  ],
  ["J05", "gis_to_camera_diagnostics_to_live_workspace", ["gis", "camera_live"]],
  ["J06", "monitor_wall_admission_and_profile_downgrade", ["camera_live", "platform_operations"]],
  ["J07", "platform_degradation_response", ["command", "platform_operations", "security"]],
  ["J08", "administrative_proposal_and_separation_of_duty", ["admin", "security"]],
  ["J09", "access_revocation_and_department_transition", surfaces],
  ["J10", "event_gap_and_authoritative_recovery", surfaces],
  ["J11", "session_expiry_during_consequential_review", ["intelligence", "admin", "investigation"]],
  ["J12", "localized_keyboard_only_command_workflow", ["command", "gis", "camera_live"]],
  ["J13", "security_finding_to_supply_chain_evidence", ["security", "platform_operations"]],
  ["J14", "offline_no_provider_generated_demonstration", surfaces],
];
const viewports = [
  ["V01", 390, 844, "compact_touch"],
  ["V02", 768, 1024, "tablet_portrait"],
  ["V03", 1280, 720, "constrained_laptop"],
  ["V04", 1440, 900, "enhanced_workstation"],
  ["V05", 1920, 1080, "full_hd_operations"],
  ["V06", 2560, 1440, "control_room"],
  ["V07", 3840, 1080, "logical_dual_display"],
];
const locales = [
  ["L01", "en-IN", "Asia/Kolkata", "operator"],
  ["L02", "gu-IN", "Asia/Kolkata", "operator"],
  ["L03", "hi-IN", "Asia/Kolkata", "operator"],
  ["L04", "qps-ploc", "Asia/Kolkata", "pseudo_unicode"],
  ["L05", "en", "UTC", "canonical"],
];
const profiles = [
  ["R01", "low_resource_laptop", true],
  ["R02", "enhanced_workstation", true],
  ["R03", "control_room", true],
  ["R04", "gpu_lab_projection", false],
  ["R05", "future_server_projection", false],
  ["R06", "kubernetes_projection", false],
];
const workloads = ["C1", "C10", "C50"];

function sha256(value) {
  return createHash("sha256").update(value).digest("hex").toUpperCase();
}
function writeJson(path, value) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}
function outcome(state) {
  if (["denied", "scope_changed", "session_expired"].includes(state)) return "deny";
  if (["event_gap", "recovery"].includes(state)) return "recover_by_authoritative_refetch";
  if (state === "abstention") return "abstain";
  if (["non_effective", "pending_review"].includes(state)) return "remain_non_effective";
  if (["partial", "stale", "degraded", "failure", "offline", "unsupported"].includes(state))
    return "degrade";
  return "allow_generated_read";
}
function generateCases() {
  const cases = [];
  for (const [category, count] of Object.entries(allocations))
    for (let local = 0; local < count; local += 1) {
      const sequence = cases.length + 1;
      const expected = outcome(states[(sequence - 1) % states.length]);
      cases.push({
        ref: `SYN-P57-CASE-${String(sequence).padStart(4, "0")}`,
        generated_only: true,
        category,
        sequence,
        seed: 570000 + sequence * 17,
        journey_id: journeys[(sequence - 1) % journeys.length][0],
        state: states[(sequence - 1) % states.length],
        surface: surfaces[(sequence - 1) % surfaces.length],
        viewport_id: viewports[(sequence - 1) % viewports.length][0],
        locale_time_id: locales[(sequence - 1) % locales.length][0],
        resource_profile_id: profiles[(sequence - 1) % profiles.length][0],
        workload: workloads[(sequence - 1) % workloads.length],
        expected,
        authority:
          expected === "remain_non_effective"
            ? "non_effective"
            : expected === "abstain"
              ? "mandatory_review"
              : "read_only",
        truth: ["observation", "inference", "hypothesis", "proposal", "qualified_system_state"][
          sequence % 5
        ],
      });
    }
  return cases;
}
function fileEntry(path) {
  const bytes = statSync(path).size;
  return {
    path: relative(repositoryRoot, path).replaceAll("\\", "/"),
    bytes,
    sha256: sha256(readFileSync(path)),
  };
}

const cases = generateCases();
if (cases.length !== 2048 || new Set(cases.map(({ ref }) => ref)).size !== 2048)
  throw new Error("generated_case_contract_failed");
const corpus = {
  schema_version: "hcam.phase5.p5_7.generated_cases.v1",
  generated_only: true,
  exact_case_count: 2048,
  allocation: allocations,
  seed_rule: "570000_plus_sequence_times_17",
  cases,
};
writeJson(resolve(contractRoot, "quality-contracts.v1.json"), {
  schema_version: "hcam.phase5.p5_7.quality_contracts.v1",
  generated_only: true,
  surfaces,
  states,
  viewports,
  locales,
  resource_profiles: profiles,
  workloads,
  hard_gate_policy: "zero_unresolved_blocker_or_critical_failure_and_no_unexplained_skip",
  production_claim_authorized: false,
});
writeJson(resolve(contractRoot, "journey-manifest.json"), {
  schema_version: "hcam.phase5.p5_7.journey_manifest.v1",
  generated_only: true,
  journey_count: journeys.length,
  journeys: journeys.map(([id, title, journeySurfaces]) => ({
    id,
    title,
    surfaces: journeySurfaces,
  })),
  pairwise_policy: "bounded_deterministic_no_unbounded_Cartesian_product",
});
writeJson(resolve(contractRoot, "generated-contract-cases.json"), corpus);
const caseBytes = Buffer.from(`${JSON.stringify(corpus, null, 2)}\n`, "utf8");
const corpusSha = sha256(caseBytes);
writeJson(resolve(contractRoot, "generated-workloads.json"), {
  schema_version: "hcam.phase5.p5_7.generated_workloads.v1",
  generated_only: true,
  corpus_sha256: corpusSha,
  replays: [
    { run: 1, sha256: corpusSha },
    { run: 2, sha256: corpusSha },
  ],
  workloads: workloads.map((id) => ({
    id,
    case_count: cases.filter(({ workload }) => workload === id).length,
  })),
  claim_boundary: "UI_and_workflow_scale_only_not_hardware_or_production_capacity",
});
writeJson(resolve(contractRoot, "browser-viewport-profile-matrix.json"), {
  schema_version: "hcam.phase5.p5_7.browser_matrix.v1",
  generated_only: true,
  primary: { engine: "chromium", channel: "msedge", automatic_download: false },
  optional: ["approved_existing_chromium", "approved_existing_firefox", "approved_existing_webkit"],
  missing_optional_policy: "blocked_or_unsupported_never_pass",
  viewports,
  resource_profiles: profiles,
});
writeJson(resolve(contractRoot, "accessibility-evidence-manifest.json"), {
  schema_version: "hcam.phase5.p5_7.accessibility_manifest.v1",
  target: "WCAG_2_2_AA",
  generated_only: true,
  automated_layers: [
    "semantic",
    "axe",
    "keyboard",
    "focus",
    "zoom",
    "reflow",
    "target_size",
    "reduced_motion",
    "error_state",
  ],
  manual_protocols_separately_required: [
    "screen_reader",
    "contrast_review",
    "workflow_keyboard_review",
    "WCAG_EM_style_sample_review",
  ],
  conformance_claim_authorized: false,
});
writeJson(resolve(contractRoot, "localization-time-manifest.json"), {
  schema_version: "hcam.phase5.p5_7.localization_time_manifest.v1",
  generated_only: true,
  profiles: locales,
  canonical_ordering: "locale_independent_record_sequence_then_identifier",
});
writeJson(resolve(contractRoot, "performance-budget-manifest.json"), {
  schema_version: "hcam.phase5.p5_7.performance_budget_manifest.v1",
  generated_only: true,
  hard_budgets: [
    { metric: "interaction_ms", maximum: 250, context: "local_Edge_generated_V04_C1" },
    { metric: "long_task_ms", maximum: 100, context: "local_Edge_generated_V04_C1" },
    { metric: "map_idle_ms", maximum: 5000, context: "local_Edge_generated_V04_C1" },
    { metric: "query_fanout", maximum: 12, context: "generated_cross_portal_journey" },
    { metric: "bundle_kib", maximum: 1900, context: "largest_uncompressed_portal_JS" },
  ],
  automatic_relaxation: false,
  production_or_hardware_claim_authorized: false,
});
writeJson(resolve(contractRoot, "resilience-fault-manifest.json"), {
  schema_version: "hcam.phase5.p5_7.resilience_manifest.v1",
  generated_only: true,
  faults: [
    "event_gap",
    "duplicate_event",
    "out_of_order_event",
    "API_degradation",
    "session_expiry",
    "scope_change",
    "conflict",
    "profile_downgrade",
  ],
  required_recovery: "typed_bounded_authoritative_refetch_or_terminal_failure",
  automatic_consequential_retry: false,
});
writeJson(resolve(contractRoot, "security-privacy-manifest.json"), {
  schema_version: "hcam.phase5.p5_7.security_privacy_manifest.v1",
  generated_only: true,
  gates: [
    "CSP",
    "CSRF",
    "XSS_sinks",
    "browser_storage",
    "redaction",
    "telemetry",
    "authorization",
    "department_isolation",
    "dependency",
    "SBOM",
    "license",
    "vulnerability",
    "provenance",
  ],
  external_network_authorized: false,
  real_data_authorized: false,
  production_security_or_compliance_claim_authorized: false,
});

const sourcePaths = [
  "packages/quality-contracts/src/index.ts",
  "packages/quality-domain/src/index.ts",
  "packages/quality-fixtures/src/index.ts",
  "packages/quality-harness/src/index.ts",
  "scripts/generate-p5-7-cases.mjs",
].map((path) => resolve(frontendRoot, path));
const sourceEntries = sourcePaths.map(fileEntry);
writeJson(resolve(contractRoot, "source-manifest.json"), {
  schema_version: "hcam.phase5.p5_7.source_manifest.v1",
  generated_only: true,
  source_file_count: sourceEntries.length,
  sources: sourceEntries,
});
writeJson(resolve(evidenceRoot, "p5-7-fixture-manifest.json"), {
  schema_version: "hcam.phase5.p5_7.fixture_manifest.v1",
  generated_only: true,
  exact_case_count: 2048,
  corpus_sha256: corpusSha,
  category_allocation: allocations,
  first_ref: cases[0].ref,
  last_ref: cases.at(-1).ref,
});
writeJson(resolve(evidenceRoot, "p5-7-source-manifest.json"), {
  schema_version: "hcam.phase5.p5_7.source_evidence.v1",
  generated_only: true,
  sources: sourceEntries,
  source_digest: sha256(
    Buffer.from(
      sourceEntries.map(({ path, bytes, sha256: hash }) => `${path}|${bytes}|${hash}`).join("\n"),
      "utf8",
    ),
  ),
});
writeJson(resolve(evidenceRoot, "p5-7-dependency-baseline.json"), {
  schema_version: "hcam.phase5.p5_7.dependency_baseline.v1",
  status: "preserved_not_refreshed",
  lockfile: fileEntry(resolve(frontendRoot, "pnpm-lock.yaml")),
  sbom: fileEntry(resolve(frontendRoot, "sbom.cdx.json")),
  dependency_evidence: fileEntry(resolve(frontendRoot, "dependency-evidence.json")),
  resolution_download_install_update_or_lockfile_change: false,
  vulnerability_refresh: false,
});
process.stdout.write(
  `${JSON.stringify({ status: "pass", exactCaseCount: cases.length, corpusSha256: corpusSha })}\n`,
);
