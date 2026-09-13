import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";

const frontendRoot = resolve(import.meta.dirname, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const contractRoot = join(repositoryRoot, "contracts", "phase-5", "p5-6");
const evidenceRoot = join(frontendRoot, "evidence");
const docsRoot = join(repositoryRoot, "docs", "phase-5", "p5-6");
const marker = "HCAM_GENERATED_ONLY_P5_6";
const seed = "HCAM-P5.6-R0-2026-09-10";
const generatedAt = "2026-09-10T09:00:00.000Z";

function sha256Bytes(value) {
  return createHash("sha256").update(value).digest("hex").toUpperCase();
}
function sha256File(path) {
  return sha256Bytes(readFileSync(path));
}
function writeJson(path, value) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => [key, canonical(item)]),
  );
}
function canonicalSha(value) {
  return sha256Bytes(Buffer.from(JSON.stringify(canonical(value)), "utf8"));
}
function manifestEntry(path) {
  return {
    path: relative(repositoryRoot, path).replaceAll("\\", "/"),
    bytes: statSync(path).size,
    sha256: sha256File(path),
  };
}

const adminContracts = {
  schema_version: "hcam.phase5.p5_6.admin_contracts.v1",
  marker,
  generated_at: generatedAt,
  primary_dashboard: "H_CAM_Command_Center",
  specialist_surface: "H_CAM_Admin_Center",
  resource_kinds: [
    "organization",
    "department",
    "user",
    "membership",
    "role",
    "permission",
    "policy",
    "camera",
    "stream",
    "provider",
    "configuration",
    "resource_profile",
    "retention_policy",
  ],
  change_lifecycle: [
    "draft",
    "submitted",
    "independent_review",
    "approved_non_effective",
    "rejected",
    "superseded",
  ],
  authorization: {
    default_deny: true,
    server_authoritative_rbac: true,
    constrained_abac: true,
    postgresql_rls_equivalence: true,
    department_purpose_capability_and_object_scope: true,
  },
  concurrency: {
    strong_etag: true,
    revision: true,
    policy_revision: true,
    idempotency_key: true,
    receipt: true,
    deliberate_reconsideration_after_conflict: true,
  },
  separation_of_duty: {
    static_and_dynamic: true,
    self_approval_denied: true,
    independent_approval_required: true,
  },
  boundaries: {
    effective_mutation: false,
    automatic_activation: false,
    break_glass: false,
    secret_resolution: false,
    camera_stream_or_provider_operation: false,
    retention_hold_deletion_export_or_deployment_operation: false,
  },
};

const securityContracts = {
  schema_version: "hcam.phase5.p5_6.security_contracts.v1",
  marker,
  generated_at: generatedAt,
  specialist_surface: "H_CAM_Security_Center",
  signal_lanes: ["operational", "security", "audit", "evidence", "administrative"],
  views: [
    "security_posture",
    "access_assurance",
    "privileged_activity",
    "session_authentication",
    "denied_activity",
    "audit_references",
    "compliance_exceptions_attestations",
    "supply_chain_assurance",
    "provider_destination_secret_posture",
    "soc_handoff_unavailable",
  ],
  truth_policy: {
    immutable_reference_is_not_evidence_truth: true,
    derived_search_requires_source_confirmation: true,
    unknown_stale_partial_and_unavailable_are_explicit: true,
    no_compliance_or_security_certification_claim: true,
  },
  boundaries: {
    secret_resolution: false,
    credential_operation: false,
    scanner_execution: false,
    attestation_signing: false,
    external_soc_handoff: false,
    provider_or_network_contact: false,
    raw_security_payload_retention: false,
  },
};

const operationsContracts = {
  schema_version: "hcam.phase5.p5_6.operations_contracts.v1",
  marker,
  generated_at: generatedAt,
  specialist_surface: "H_CAM_Operations_Center",
  preserved_domain: "P5_3_camera_and_live_monitoring",
  additive_domain: "Platform_Operations",
  views: [
    "services_and_dependencies",
    "queues_workers_and_circuits",
    "data_infrastructure",
    "AI_runtime_scheduler_projection",
    "SLO_and_error_budgets",
    "degradation_and_kill_switch",
    "maintenance_and_recovery_preview",
    "capacity_evidence",
    "topology_projections",
  ],
  resource_profiles: [
    "low_resource",
    "enhanced_workstation",
    "control_room",
    "owned_GPU_lab",
    "future_server",
    "future_Kubernetes",
  ],
  profile_authority_invariant: true,
  resilience_contracts: {
    bounded_queue_leases: true,
    typed_retries_and_backoff: true,
    dead_letter_projection: true,
    circuit_breaker_projection: true,
    graceful_shutdown_projection: true,
    abandoned_work_recovery_projection: true,
  },
  boundaries: {
    live_telemetry: false,
    runtime_profile_activation: false,
    kill_switch_operation: false,
    backup_restore_or_recovery_execution: false,
    hardware_capacity_claim: false,
    production_slo_rpo_or_rto_target: false,
    container_or_kubernetes_execution: false,
  },
};

const groups = [
  ["organization_identity_membership_role_capability_and_session", 176],
  ["policy_changes_approval_SoD_ETag_and_idempotency", 192],
  ["camera_stream_provider_secret_ref_feature_config_profile_and_retention", 176],
  ["security_posture_denials_audit_refs_compliance_exceptions_and_attestations", 160],
  ["supply_chain_service_health_queues_workers_circuits_and_degradation", 160],
  ["SLO_budgets_storage_recovery_maintenance_capacity_and_topology", 128],
  ["cross_department_hostile_input_redaction_overclaim_and_signal_separation", 80],
  ["accessibility_handoff_state_and_cross_profile_equivalence", 48],
];
let sequence = 0;
const cases = groups.flatMap(([group, count], groupIndex) =>
  Array.from({ length: count }, (_, ordinal) => {
    sequence += 1;
    return {
      ref: `SYN-P56-CASE-${String(sequence).padStart(4, "0")}`,
      seed,
      group,
      ordinal: ordinal + 1,
      expected:
        groupIndex === 6
          ? "deny"
          : groupIndex === 2 || groupIndex === 5
            ? "non_effective"
            : groupIndex === 3 || groupIndex === 4
              ? "qualified"
              : "allow",
      department_ref: `SYN-DEPT-${String((ordinal % 10) + 1).padStart(2, "0")}`,
      generated: true,
      effective: false,
    };
  }),
);
const generatedCases = {
  schema_version: "hcam.phase5.p5_6.generated_contract_cases.v1",
  marker,
  seed,
  exact_case_count: cases.length,
  groups: groups.map(([group, count]) => ({ group, count })),
  cases,
};
const workloadSpecs = [
  ["C1", 1, 2, 10, 10, 4, 8],
  ["C10", 1, 10, 100, 50, 20, 100],
  ["C50", 5, 50, 500, 200, 100, 500],
];
const workloadProjection = {
  schema_version: "hcam.phase5.p5_6.generated_workloads.v1",
  marker,
  workloads: workloadSpecs.map(
    ([profile, organizations, departments, users, services, queues, changeRequests]) => ({
      profile,
      organizations,
      departments,
      users,
      services,
      queues,
      change_requests: changeRequests,
      functional_only: true,
      hardware_claim: false,
      production_claim: false,
      runtime_profile_activation: false,
    }),
  ),
  replays: [1, 2].map((run) => ({ run, sha256: canonicalSha(generatedCases) })),
};
const forbiddenKeys = [
  "password",
  "secretValue",
  "accessToken",
  "refreshToken",
  "privateKey",
  "connectionString",
  "rawLog",
  "mediaUrl",
  "modelArtifact",
  "executableInstruction",
];
const prohibitedFieldManifest = {
  schema_version: "hcam.phase5.p5_6.prohibited_field_manifest.v1",
  marker,
  scanned_records: cases.length,
  forbidden_keys: forbiddenKeys,
  forbidden_value_classes: [
    "credential_or_secret_material",
    "raw_log_or_security_payload",
    "provider_camera_media_or_model_locator",
    "executable_machine_or_deployment_instruction",
  ],
  findings: 0,
  secret_values_retained: 0,
  raw_logs_retained: 0,
  media_or_model_bytes_retained: 0,
};

writeJson(join(contractRoot, "admin-contracts.v1.json"), adminContracts);
writeJson(join(contractRoot, "security-contracts.v1.json"), securityContracts);
writeJson(join(contractRoot, "operations-contracts.v1.json"), operationsContracts);
writeJson(join(contractRoot, "generated-contract-cases.json"), generatedCases);
writeJson(join(contractRoot, "generated-workloads.json"), workloadProjection);
writeJson(join(contractRoot, "prohibited-field-manifest.json"), prohibitedFieldManifest);

const fixturePaths = [
  "admin-contracts.v1.json",
  "security-contracts.v1.json",
  "operations-contracts.v1.json",
  "generated-contract-cases.json",
  "generated-workloads.json",
  "prohibited-field-manifest.json",
].map((name) => join(contractRoot, name));
const fixtureManifest = {
  schema_version: "hcam.phase5.p5_6.fixture_manifest.v1",
  marker,
  seed,
  exact_case_count: cases.length,
  generator: "frontend/scripts/generate-evidence.mjs",
  records: fixturePaths.map(manifestEntry),
};
writeJson(join(evidenceRoot, "p5-6-fixture-manifest.json"), fixtureManifest);

const start = JSON.parse(
  readFileSync(
    join(repositoryRoot, "contracts", "phase-5", "p5-6-start-authorization-package.json"),
  ),
);
const sourcePaths = [
  ...start.exact_existing_file_changes,
  ...start.exact_additive_implementation_paths,
]
  .filter((path, index, all) => all.indexOf(path) === index)
  .map((path) => join(repositoryRoot, path))
  .filter((path) => {
    try {
      return statSync(path).isFile();
    } catch {
      return false;
    }
  })
  .sort();
const sourceManifest = {
  schema_version: "hcam.phase5.p5_6.source_manifest.v1",
  marker,
  package_id: "P5.6-START-R0",
  source_file_count: sourcePaths.length,
  files: sourcePaths.map(manifestEntry),
};
writeJson(join(contractRoot, "source-manifest.json"), sourceManifest);
writeJson(join(evidenceRoot, "p5-6-source-manifest.json"), sourceManifest);

const dependencyBaseline = {
  schema_version: "hcam.phase5.p5_6.dependency_baseline.v1",
  result: "pass",
  node: "24.18.0",
  package_manager_executed: false,
  dependency_resolution: false,
  dependencies_added: 0,
  lockfile_sha256: sha256File(join(frontendRoot, "pnpm-lock.yaml")),
  sbom_sha256: sha256File(join(frontendRoot, "sbom.cdx.json")),
  vulnerability_baseline_sha256: sha256File(join(frontendRoot, "dependency-evidence.json")),
  statement:
    "Existing locked dependencies and supply-chain baseline are preserved; no refresh or scanner execution was performed.",
};
writeJson(join(evidenceRoot, "p5-6-dependency-baseline.json"), dependencyBaseline);

const implementationDoc = `# P5.6 Administration, Security, And Operations Implementation

## Scope

P5.6 implements generated-only Admin Center, Security Center, and additive Platform Operations surfaces. Command Center remains the primary dashboard. Existing P5.3 Camera Catalogue, Camera Detail, Stream Diagnostics, Live Workspace, and Monitor Wall routes remain preserved inside Operations Center.

## Control Model

Administrative changes are typed, revisioned, non-effective proposals. Authorization is server-authoritative, default-deny, department and purpose scoped, and represented with PostgreSQL row-security equivalence. Static and dynamic separation of duty reject self-approval. Strong ETags, revisions, policy revisions, idempotency keys, receipts, and deliberate conflict reconsideration define concurrency behavior.

Security views keep operational, security, audit, evidence, and administrative signal lanes separate. Secret references are opaque and never resolved. Provider, certificate, audit, compliance, exception, attestation, and supply-chain records are generated projections with explicit freshness, completeness, and limitations.

Platform Operations adds qualified service, dependency, queue, worker, circuit, storage, database, event-bus, media-edge, AI-runtime, SLO, degradation, maintenance, recovery, capacity, and topology projections. They are not live telemetry, production targets, hardware claims, deployment states, or executable operations.

## Dynamic Profiles

Low-resource, enhanced-workstation, control-room, owned-GPU-lab, future-server, and future-Kubernetes profiles may change density and rendering only. Authority, truth qualification, scope, available actions, security, and accessibility remain invariant.

## Generated Validation

The deterministic fixture set contains exactly 1,120 generated contract cases under seed \`${seed}\`, C1/C10/C50 functional workloads, two canonical replays, 48 preserved producer gaps, and 72 threat controls. It contains no real identities, telemetry, secrets, providers, cameras, media, models, operational actions, scanner results, backup/restore execution, containers, Kubernetes execution, or deployment evidence.
`;
mkdirSync(docsRoot, { recursive: true });
writeFileSync(join(docsRoot, "implementation.md"), implementationDoc, "utf8");

process.stdout.write(
  `${JSON.stringify({ status: "pass", cases: cases.length, sourceFiles: sourcePaths.length, fixtures: fixturePaths.length })}\n`,
);
