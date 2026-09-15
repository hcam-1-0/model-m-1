# P4.6 Proposed Contract Catalog

Status: non-effective planning proposal

Authority: `D-P4.6-PLAN-AUTH`

This catalog defines the proposed typed boundaries for P4.6 Operations,
Security, And Scale. It is a design input only. No schema, persistence model,
API, exporter, worker, deployment, capacity run, backup, restore, or security
control described here is implemented or authorized by this document.

## Contract Principles

1. Contracts are versioned, department-aware where applicable, bounded in
   size, and fail closed on unknown enum values or unsupported versions.
2. Metrics use a centrally reviewed low-cardinality label registry. Camera,
   stream, user, case, entity, alert, evidence, locator, hostname, IP address,
   exception text, and free-form reason values are forbidden labels.
3. Trace context is transport metadata, not an authorization credential.
4. Operational logs, security logs, audit records, and evidence records have
   separate schemas, stores, access rules, retention references, and export
   controls. Copying data between lanes requires a typed projection.
5. Every externally visible failure is a bounded code plus safe parameters;
   raw exceptions remain inside separately controlled diagnostics.
6. SLO targets, alert thresholds, RPOs, RTOs, retention periods, and capacity
   claims remain unset until evidence and owner policy approve exact values.
7. Workers retain domain ownership. Shared P4.6 contracts standardize leases,
   retries, idempotency, circuit state, shutdown, recovery, and observation;
   they do not create one universal queue implementation.
8. Standalone, owned GPU lab, server, and Kubernetes are placement profiles,
   not divergent product editions. Capability detection selects from signed or
   locally trusted profiles and never silently weakens a mandatory control.
9. Generated C1/C10/C50 workloads contain no real camera, media, identity,
   Government, private, biometric, case, watchlist, or evidence data.
10. Unknown capability, provenance, vulnerability, recovery, or policy state
    is represented explicitly and never converted to a successful state.

## Common Envelope

All proposed P4.6 records use these common fields unless a contract explicitly
states that it is process-local and non-persistent:

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | constrained string | Exact supported contract version |
| `record_id` | UUID | Random opaque identifier; no embedded identity |
| `occurred_at` | UTC timestamp | Source occurrence time when known |
| `recorded_at` | UTC timestamp | H-CAM persistence time |
| `department_scope` | opaque scope ID or `platform` | Required for department-owned records |
| `correlation_id` | opaque 128-bit value | Groups one bounded operation; not authorization |
| `trace_context` | object or null | Validated W3C-compatible projection |
| `actor_ref` | opaque attributable reference or null | Required for owner/admin mutations |
| `reason_code` | closed enum or null | Sanitized code, never free-form failure text |
| `contract_digest` | SHA-256 | Canonical contract and policy binding |

The common envelope forbids credentials, tokens, raw headers, media, frames,
biometrics, registration or owner details, unrestricted URLs, raw SQL,
stack traces, personal paths, and environment snapshots.

## C01: Telemetry Registry

Contract: `hcam.operations.telemetry-registry.v1`

Purpose: the canonical allowlist for metric names, types, units, labels,
cardinality budgets, ownership, and lifecycle.

Required fields:

- `registry_revision`, `effective_from`, `metric_definitions`, and
  `registry_digest`;
- for each metric: `name`, `instrument_type`, `unit`, `description`,
  `owner_module`, `allowed_labels`, `label_value_enums`, `cardinality_budget`,
  `stability`, and `deprecation_state`;
- a fixed mapping from every label to a closed value source.

Invariants:

- a metric name has one unit and semantic meaning for its lifetime;
- `_total` is reserved for counters; ratios use an explicit unit;
- histogram boundaries are centrally versioned;
- tenant, department, object, user, locator, and unbounded reason values cannot
  become labels;
- removed metrics pass through a declared deprecation window.

## C02: Telemetry Envelope

Contract: `hcam.operations.telemetry-envelope.v1`

Purpose: bounded internal transport for metrics, spans, and structured health
signals before optional export.

Required fields: `signal_kind`, `registry_revision`, `service_name`,
`service_version`, `deployment_profile`, `observed_at`, `attributes`, and
`payload`.

Rules:

- `attributes` are checked against the registry before emission;
- exporters are default off and have exact destination and trust policy;
- failed export cannot block the safety-critical transaction path;
- retry buffers are byte-, item-, and age-bounded with explicit loss counts;
- user or case context is not promoted to resource attributes.

## C03: Trace Context

Contract: `hcam.operations.trace-context.v1`

Purpose: propagate validated W3C Trace Context plus one H-CAM operation ID
across HTTP, event, worker, and outbox boundaries.

Required fields: `traceparent`, optional bounded `tracestate`,
`correlation_id`, `origin_service`, and `propagation_decision`.

Invariants:

- malformed or oversized context is replaced with a new local root and a safe
  `trace_context_rejected` security signal;
- incoming trace context never grants role, department, data, or network
  authority;
- baggage is disabled by default; if later enabled, it requires an exact key
  registry and must exclude identity, purpose, case, and evidence values;
- trace sampling cannot suppress audit or evidence records.

## C04: Governed Log Event

Contract: `hcam.operations.log-event.v1`

Purpose: a shared envelope with physically and logically separate signal
classes.

Required fields: `log_class`, `event_code`, `severity`, `service_name`,
`occurred_at`, `correlation_id`, `safe_dimensions`, and `retention_policy_ref`.

Closed `log_class` values:

- `operational`: health, queue, dependency, and lifecycle behavior;
- `security`: policy denial, authentication, authorization, integrity, abuse,
  and tamper signals;
- `audit_projection`: read-only observation that an authoritative audit record
  exists; it is not the audit record itself;
- `evidence_projection`: read-only observation that an authoritative evidence
  reference exists; it contains no evidence payload.

Rules:

- audit and evidence records cannot be reconstructed from ordinary logs;
- operational logging failure cannot erase required audit persistence;
- security events have independent access and alert routing;
- free-form messages are optional, bounded, sanitized, and never indexed as a
  high-cardinality dimension.

## C05: Sanitized Failure

Contract: `hcam.operations.failure.v1`

Purpose: one closed failure taxonomy across APIs, jobs, events, metrics, logs,
and operator projections.

Required fields: `failure_code`, `failure_domain`, `failure_class`,
`retry_disposition`, `safe_parameters`, `public_status`, `operator_action_ref`,
and `taxonomy_revision`.

Closed failure classes:

- `validation`, `authorization`, `policy`, `configuration`, `dependency`,
  `capacity`, `timeout`, `conflict`, `integrity`, `transient`, `internal`, and
  `aborted`.

Rules:

- unknown failures map to `internal_unclassified` and are not retried by
  default;
- retryability is policy metadata, not inferred from an HTTP status alone;
- safe parameters come from an allowlist and cannot include raw exception,
  query, URL, credential, path, identity, media, or provider response data;
- the original exception is discarded or retained only in a separately
  authorized diagnostic lane.

## C06: Service Objective

Contract: `hcam.operations.service-objective.v1`

Purpose: versioned SLI, objective, measurement-window, exclusion, and evidence
definition for a service class or user journey.

Required fields: `objective_id`, `objective_revision`, `service_class`,
`journey`, `sli_definition`, `good_event_predicate`, `valid_event_predicate`,
`window`, `target_state`, `target_value`, `exclusions`, `data_quality_rules`,
`evidence_ref`, and `owner_state`.

Rules:

- `target_state` is `unset`, `provisional`, or `approved`;
- `target_value` must be null while state is `unset`;
- exclusions are bounded and visible; unknown data is not counted as good;
- each objective declares whether it measures availability, correctness,
  freshness, latency, durability, or recovery;
- objective changes create a new immutable revision.

## C07: Error-Budget State

Contract: `hcam.operations.error-budget-state.v1`

Purpose: deterministic window calculation and release/degradation policy input.

Required fields: `objective_ref`, `window_start`, `window_end`, `eligible`,
`good`, `bad`, `unknown`, `budget_total`, `budget_consumed`, `burn_rates`,
`calculation_digest`, and `policy_decision`.

Invariants:

- unknown and missing telemetry are explicit;
- calculations are replayable from immutable aggregate inputs;
- budget state cannot independently activate a model, camera, provider,
  operational alert, deployment, or enforcement action;
- policy decisions remain proposed until the relevant authority gate exists.

## C08: Degradation State

Contract: `hcam.operations.degradation-state.v1`

Purpose: hierarchical, revisioned, attributable control of capability
reduction without silent semantic change.

Required fields: `scope_kind`, `scope_ref`, `revision`, `requested_mode`,
`effective_mode`, `cause_code`, `entered_at`, `expires_at`, `actor_ref`,
`approval_ref`, `fallback_contract`, and `rollback_ref`.

Closed modes: `normal`, `reduced_rate`, `reduced_quality`, `metadata_only`,
`read_only`, `queue_only`, `disabled`, and `emergency_stop`.

Rules:

- a child cannot override a stricter parent mode;
- mandatory security, audit, department isolation, and evidence-integrity
  controls cannot be degraded;
- every bypassed optional layer is visible in output provenance;
- transition and rollback are idempotent and audited.

## C09: Worker Policy

Contract: `hcam.operations.worker-policy.v1`

Purpose: common conformance policy for domain-owned queues and workers.

Required fields: `worker_class`, `lease_duration`, `heartbeat_interval`,
`max_attempts`, `retry_schedule`, `retryable_failure_codes`, `dead_letter_rule`,
`idempotency_scope`, `shutdown_grace`, `abandonment_rule`, `circuit_policy_ref`,
and `resource_bounds`.

Invariants:

- `heartbeat_interval` is shorter than the lease and includes clock-skew
  tolerance;
- claim and lease transitions are compare-and-set or transactionally locked;
- only allowlisted transient failures retry;
- authorization, policy, validation, and integrity failures do not retry;
- retry count, delay, queue age, payload size, output size, and total runtime
  are bounded;
- dead-letter entries retain sanitized context and immutable lineage, not raw
  payloads by default.

## C10: Worker Attempt

Contract: `hcam.operations.worker-attempt.v1`

Purpose: append-only lifecycle evidence for one domain job attempt.

Required fields: `job_ref`, `attempt_number`, `state`, `lease_token_digest`,
`claimed_at`, `heartbeat_at`, `finished_at`, `worker_class`, `failure_ref`,
`result_ref`, `idempotency_key_digest`, and `resource_summary`.

Closed states: `queued`, `leased`, `running`, `succeeded`, `retry_wait`,
`dead_lettered`, `cancelled`, and `abandoned`.

Rules:

- late workers cannot commit after lease loss;
- success is durable only with the domain result and outbox transaction;
- reclaiming abandoned work increments an observable bounded counter;
- `resource_summary` contains coarse profile-level values, not host identity.

## C11: Circuit State

Contract: `hcam.operations.circuit-state.v1`

Purpose: deterministic dependency protection independent from retry policy.

Required fields: `dependency_class`, `scope`, `state`, `window`,
`failure_threshold`, `minimum_samples`, `opened_at`, `probe_due_at`,
`half_open_budget`, and `revision`.

Closed states: `closed`, `open`, `half_open`, and `forced_open`.

Rules:

- dependency classes are low-cardinality and cannot contain destination names;
- forced state requires attributable control and expiry;
- half-open probes are separately bounded;
- circuit state cannot bypass exact destination or authorization controls.

## C12: Kill-Switch Revision

Contract: `hcam.operations.kill-switch-revision.v1`

Purpose: fail-closed, hierarchical, signed or locally trusted control that can
stop a capability while preserving read-only visibility and audit.

Required fields: `switch_id`, `scope_kind`, `scope_ref`, `revision`, `state`,
`cause_code`, `actor_ref`, `approved_at`, `effective_at`, `expires_at`,
`supersedes`, and `signature_or_trust_ref`.

Rules:

- deny wins over allow at equal or broader scope;
- stale, invalid, ambiguous, or missing required policy fails closed;
- emergency activation is auditable and cannot erase queued work or evidence;
- deactivation requires a newer attributable revision;
- switches cannot grant a capability that is otherwise unauthorized.

## C13: Recovery Plan

Contract: `hcam.operations.recovery-plan.v1`

Purpose: policy-reference design for backup sets, restore dependencies,
recovery order, integrity gates, and evidence.

Required fields: `recovery_tier`, `protected_assets`, `dependency_order`,
`backup_method`, `restore_method`, `rpo_state`, `rto_state`,
`integrity_checks`, `key_dependency_refs`, `offsite_policy_ref`,
`exercise_schedule_ref`, and `owner_state`.

Rules:

- RPO/RTO values remain null until approved and evidenced;
- database, object, configuration, secret, signing-key, and contract recovery
  dependencies are explicit and separately governed;
- a backup does not become `recoverable` until a bounded restore and integrity
  check succeeds in an authorized isolated target;
- destructive restore requires separate future authorization.

## C14: Recovery Drill

Contract: `hcam.operations.recovery-drill.v1`

Purpose: immutable plan/result evidence for generated, tabletop, or later
authorized isolated recovery exercises.

Required fields: `drill_id`, `plan_ref`, `drill_kind`, `authorization_ref`,
`started_at`, `completed_at`, `observed_rpo`, `observed_rto`,
`integrity_results`, `missing_dependencies`, `sanitized_failures`,
`cleanup_state`, and `evidence_digest`.

Rules:

- `drill_kind` distinguishes generated simulation, tabletop, isolated restore,
  and production exercise;
- only generated simulation is proposed for the initial P4.6 implementation;
- failed cleanup or missing evidence prevents a successful result;
- claimed RPO/RTO must be computed from observed records, never copied from a
  target.

## C15: Security Control Evidence

Contract: `hcam.security.control-evidence.v1`

Purpose: append-only generated test evidence for authorization, department
isolation, RLS equivalence, privileged-role behavior, abuse resistance, and
tamper detection.

Required fields: `control_id`, `control_revision`, `test_class`,
`principal_class`, `database_role_class`, `department_relation`, `expected`,
`observed`, `result`, `fixture_digest`, `environment_class`, and
`evidence_digest`.

Rules:

- no username, real department, host, database address, or query payload;
- RLS evidence distinguishes table owner, `FORCE ROW LEVEL SECURITY`,
  superuser, `BYPASSRLS`, ordinary role, absent policy, and policy failure;
- application and database decisions are tested as independent oracles;
- a test passes only when both expected deny/allow and attributable audit
  behavior match.

## C16: Supply-Chain Bundle

Contract: `hcam.supply-chain.bundle.v1`

Purpose: canonical internal inventory with loss-accounted projections to
standard interchange formats.

Required fields: `bundle_id`, `source_revision`, `dependency_inventory`,
`artifact_inventory`, `license_findings`, `vulnerability_observations`,
`provenance_observations`, `build_observations`, `projection_refs`,
`unknowns`, `policy_result`, and `bundle_digest`.

Rules:

- `not_observed`, `not_applicable`, `unknown`, `failed`, and `verified` are
  distinct states;
- absence of a vulnerability observation is not proof of no vulnerability;
- SPDX and CycloneDX projections are generated from one canonical inventory;
- SLSA provenance is an optional projection and no SLSA level is claimed
  unless every required predicate is independently demonstrated;
- signatures, attestations, scanner databases, and registry access remain
  outside the initial generated-only implementation.

## C17: Capacity Profile

Contract: `hcam.capacity.profile.v1`

Purpose: a portable, privacy-preserving description of execution capability
and policy constraints.

Required fields: `profile_id`, `profile_class`, `cpu_class`, `memory_band`,
`accelerator_classes`, `storage_band`, `network_band`, `runtime_capabilities`,
`scheduler_capabilities`, `policy_constraints`, `supported_lanes`,
`unsupported_lanes`, `source_kind`, and `profile_digest`.

Profile classes: `developer_laptop`, `owned_gpu_lab`, `server_node`, and
`kubernetes_node_class`.

Rules:

- exact host identity, serials, MAC/IP addresses, personal paths, and user
  identity are forbidden;
- capability detection never loads a model, runs inference, starts a
  container, or probes a camera under the initial scope;
- unsupported optional lanes are explicitly bypassed with provenance;
- mandatory controls make the placement ineligible rather than degraded.

## C18: Capacity Run

Contract: `hcam.capacity.run.v1`

Purpose: deterministic generated C1/C10/C50 workload plan and result.

Required fields: `run_id`, `scenario_class`, `workload_mode`, `profile_ref`,
`fixture_digest`, `duration_plan`, `concurrency`, `arrival_pattern`,
`latency_summary`, `throughput_summary`, `backlog_summary`,
`saturation_summary`, `recovery_summary`, `resource_summary`, `loss_counts`,
`limitations`, and `result_digest`.

Scenario classes: `C1`, `C10`, and `C50`.

Workload modes: `latency`, `balanced`, and `throughput`.

Rules:

- fixtures are generated metadata and synthetic event envelopes only;
- percentile calculation, warmup, sample count, clock, and exclusion rules are
  versioned;
- an incomplete run is never presented as a capacity claim;
- results identify the profile class and limitations, not a universal camera
  or deployment capacity.

## C19: Placement Plan

Contract: `hcam.placement.plan.v1`

Purpose: deterministic matching of required service capabilities to standalone,
GPU-lab, server, or future Kubernetes resources.

Required fields: `plan_id`, `requested_services`, `required_capabilities`,
`available_profile_refs`, `placements`, `bypasses`, `rejections`,
`workload_mode`, `policy_revision`, `scheduler_adapter`, and `plan_digest`.

Rules:

- the pure policy decision is platform-neutral;
- the standalone executor and future Kubernetes adapter consume the same plan;
- automatic placement is advisory/default-off until separately authorized;
- Kubernetes Dynamic Resource Allocation or device-plugin use is selected only
  when the target cluster explicitly supports the required version and driver;
- placement cannot bypass department isolation, network policy, provenance,
  resource limit, or kill-switch constraints.

## C20: Health Projection

Contract: `hcam.operations.health-projection.v1`

Purpose: safe API/UI projection of component, dependency, queue, SLO, capacity,
and recovery state without exposing sensitive diagnostic material.

Required fields: `component_class`, `health_state`, `degradation_state`,
`freshness`, `safe_reason_codes`, `objective_refs`, `queue_summary`,
`recovery_summary`, `last_transition_at`, and `projection_revision`.

Closed health states: `healthy`, `degraded`, `unavailable`, `unknown`, and
`administratively_disabled`.

Rules:

- `unknown` is not healthy;
- read projection is department-scoped where applicable;
- no raw topology, URL, address, exception, principal, case, evidence, or
  provider data is returned;
- mutations are excluded from the initial UI support; any future control API
  requires role, scope, reason, revision, ETag, audit, and separate authority.

## Cross-Contract Lifecycle

```text
registry and policy revisions
        |
        v
validated telemetry / worker / security / recovery inputs
        |
        +----> sanitized operational and security signals
        |
        +----> immutable audit or evidence references
        |
        v
objective and capacity calculations
        |
        v
proposed degradation / circuit / placement decisions
        |
        v
authorized revisioned control, or fail-closed no-op
```

No arrow in this lifecycle grants camera, model, provider, operational-action,
container, Kubernetes, deployment, or remote-Git authority.

## Compatibility Rules

- Existing Prometheus metrics remain supported; new definitions must enter the
  registry before emission.
- Existing `X-Request-ID` behavior becomes an input to the opaque correlation
  contract; it is not silently reinterpreted as trusted trace context.
- Existing domain queue tables remain authoritative. P4.6 adds shared
  conformance contracts and projections rather than moving jobs into a new
  central queue.
- Existing audit and Phase 4.5 evidence stores remain authoritative and are
  never replaced by logs or traces.
- Existing backup and recovery-drill commands remain unchanged until a later
  exact implementation package names any extension.
- Unsupported contract versions, fields, profile capabilities, and adapter
  functions fail closed with a sanitized failure.

## Initial Generated-Only Validation Expectations

The future bounded implementation plan should prove, using generated inputs:

- schema/version rejection and canonical digest stability;
- forbidden telemetry labels and bounded cardinality;
- malformed trace context rejection without authorization impact;
- lane separation and audit/evidence non-substitution;
- sanitized failure redaction and deterministic retry disposition;
- objective and budget unknown-state behavior;
- lease loss, duplicate delivery, abandoned-work recovery, dead-letter, circuit,
  graceful shutdown, and kill-switch races;
- application/RLS equivalence including privileged-role negative cases;
- incomplete SBOM, provenance, license, and vulnerability states;
- recovery-plan and drill evidence without executing backup or restore;
- deterministic C1/C10/C50 calculations without performance claims;
- profile selection, optional-lane bypass, and mandatory-control rejection;
- standalone and Kubernetes adapter contract equivalence without starting a
  process, container, or cluster.

## Explicit Non-Claims

This proposal does not claim OpenTelemetry, W3C, Prometheus, NIST, PostgreSQL,
SPDX, CycloneDX, SLSA, or Kubernetes conformance. It does not establish a
production SLO, error budget, RPO, RTO, capacity, security certification,
recovery capability, Kubernetes readiness, or deployment authorization.
