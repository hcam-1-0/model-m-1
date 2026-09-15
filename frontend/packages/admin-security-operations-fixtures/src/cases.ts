export const p56Seed = "HCAM-P5.6-R0-2026-09-10" as const;
export const p56CaseGroups = [
  ["organization_identity_membership_role_capability_and_session", 176],
  ["policy_changes_approval_SoD_ETag_and_idempotency", 192],
  ["camera_stream_provider_secret_ref_feature_config_profile_and_retention", 176],
  ["security_posture_denials_audit_refs_compliance_exceptions_and_attestations", 160],
  ["supply_chain_service_health_queues_workers_circuits_and_degradation", 160],
  ["SLO_budgets_storage_recovery_maintenance_capacity_and_topology", 128],
  ["cross_department_hostile_input_redaction_overclaim_and_signal_separation", 80],
  ["accessibility_handoff_state_and_cross_profile_equivalence", 48],
] as const;
export type P56CaseGroup = (typeof p56CaseGroups)[number][0];
export interface P56GeneratedContractCase {
  readonly ref: string;
  readonly seed: typeof p56Seed;
  readonly group: P56CaseGroup;
  readonly ordinal: number;
  readonly expected: "allow" | "deny" | "qualified" | "non_effective";
  readonly departmentRef: string;
  readonly generated: true;
}
export function generateContractCases(): readonly P56GeneratedContractCase[] {
  let sequence = 0;
  return p56CaseGroups.flatMap(([group, count], groupIndex) =>
    Array.from({ length: count }, (_, ordinal) => {
      sequence += 1;
      return {
        ref: `SYN-P56-CASE-${String(sequence).padStart(4, "0")}`,
        seed: p56Seed,
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
        departmentRef: `SYN-DEPT-${String((ordinal % 10) + 1).padStart(2, "0")}`,
        generated: true,
      } satisfies P56GeneratedContractCase;
    }),
  );
}
export const p56ContractCases = Object.freeze(generateContractCases());
