export const p55UnavailableProducers = [
  "investigation_list_api",
  "investigation_detail_api",
  "timeline_page_api",
  "timeline_anchor_api",
  "timeline_filter_api",
  "record_time_api",
  "qualified_event_time_api",
  "reconstruction_api",
  "reconstruction_digest_api",
  "revision_comparison_api",
  "correction_api",
  "retraction_api",
  "impact_closure_api",
  "investigation_relationship_api",
  "relationship_table_api",
  "evidence_list_api",
  "evidence_detail_api",
  "evidence_state_api",
  "integrity_history_api",
  "provenance_api",
  "provenance_table_api",
  "custody_api",
  "custody_table_api",
  "source_reference_api",
  "policy_preview_api",
  "retention_preview_api",
  "hold_preview_api",
  "deletion_preview_api",
  "disposition_preview_api",
  "export_preview_api",
  "case_bridge_api",
  "prov_interchange_api",
  "department_scope_api",
  "purpose_scope_api",
  "event_invalidation_api",
  "health_api",
] as const;
export const p55Threats = Array.from(
  { length: 56 },
  (_, index) => `P5.5-T${String(index + 1).padStart(2, "0")}` as const,
);

const caseGroups = [
  ["chronology_pagination_and_timeline_states", 128],
  ["reconstruction_comparison_and_digest_states", 128],
  ["correction_retraction_and_impact_closure", 128],
  ["evidence_identity_integrity_access_and_source_boundary", 160],
  ["provenance_custody_graph_and_table_parity", 128],
  ["policy_previews_and_disabled_bridges", 96],
  ["authorization_concurrency_events_handoffs_and_teardown", 96],
  ["accessibility_localization_security_profiles_and_hostile_input", 96],
] as const;
export interface GeneratedContractCase {
  readonly id: string;
  readonly group: (typeof caseGroups)[number][0];
  readonly marker: "HCAM-GENERATED-NON-OPERATIONAL";
  readonly expected: "accept" | "reject" | "abstain";
  readonly generated: true;
}
export const generatedContractCases: readonly GeneratedContractCase[] = Object.freeze(
  caseGroups.flatMap(([group, count]) =>
    Array.from({ length: count }, (_, index) => ({
      id: `SYN-P55-${group.toUpperCase()}-${String(index + 1).padStart(4, "0")}`,
      group,
      marker: "HCAM-GENERATED-NON-OPERATIONAL" as const,
      expected:
        index % 11 === 0
          ? ("abstain" as const)
          : index % 7 === 0
            ? ("reject" as const)
            : ("accept" as const),
      generated: true as const,
    })),
  ),
);
