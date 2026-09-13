# P4.6 Bounded Implementation Plan

Status: non-effective plan; owner decisions pending

Authority: `D-P4.6-PLAN-AUTH`

This document specifies how P4.6 Operations, Security, And Scale could be
implemented after all owner gates are satisfied. It does not authorize or claim
any product, test, migration, dependency, runtime, container, Kubernetes,
backup, restore, capacity, hardware, scanner, network, deployment, or remote
Git action.

## Outcome

P4.6 should make the existing H-CAM platform operable and testable as one
system across a conservative developer laptop, an owned GPU lab, server nodes,
and a future Kubernetes cluster. The implementation must preserve common
business and security contracts while allowing optional analytics and resource
lanes to be selected, bypassed, or degraded visibly according to an approved
capability profile.

It should not replace accepted Phase 0-4.5 domain behavior. It should add:

- one governed low-cardinality telemetry and failure vocabulary;
- trace/correlation propagation without authorization semantics;
- separated operations, security, audit, and evidence lanes;
- evidence-gated SLI/SLO, error-budget, alert, and degradation contracts;
- shared resilience conformance for domain-owned workers;
- hierarchical kill switches and safe graceful shutdown;
- application authorization and PostgreSQL RLS equivalence evidence;
- generated abuse, isolation, and privileged-role tests;
- canonical supply-chain inventory and standard projections;
- restore-first recovery plans and generated drill evidence;
- portable capability, capacity, and placement contracts;
- safe read projections for a later Phase 5 operations/security UI.

## Frozen Weighted Work Breakdown

P4.6 owns **10 of 100 Phase 4 points**. No partial item credit is awarded.

| Item | Weight | Acceptance condition |
| --- | ---: | --- |
| P4.6-A Observability, SLOs, and failures | 3 | Typed contracts, low-cardinality registry, trace propagation, signal separation, SLI/SLO/budget/degradation logic, safe APIs/metrics, generated tests, and evidence all pass |
| P4.6-B Worker resilience and recovery | 2 | Lease/retry/dead-letter/circuit/idempotency/shutdown/kill-switch/abandonment contracts and generated conformance pass across in-scope domain workers |
| P4.6-C Security, isolation, and supply chain | 3 | App/RLS equivalence, privileged negatives, abuse tests, dependency/license/SBOM/vulnerability/provenance controls, migration/API security, and evidence pass |
| P4.6-D Capacity and topology methodology | 1 | Generated C1/C10/C50 methodology, hardware profiles, placement policy, standalone/Kubernetes adapter contracts, limitation reporting, and deterministic tests pass without runtime capacity claims |
| P4.6-E Owner acceptance | 1 | Exact evidence package and technical commit are explicitly accepted by `mayank-admin` |

Current accepted progress remains:

- P4.6: **0/10 (0.0000%)**, change **+0.0000 percentage points**;
- Phase 4: **85/100 (85.00%)**, change **+0.00 percentage points**.

Planning and research completeness is tracked separately and awards no weighted
product progress. If A-D are fully implemented and validated, the technical
ceiling before owner acceptance is:

- P4.6: **9/10 (90.0000%)**;
- Phase 4: **94/100 (94.00%)**.

After exact P4.6 owner acceptance:

- P4.6: **10/10 (100.0000%)**;
- Phase 4: **95/100 (95.00%)**.

P4.7 remains the final five-point Phase 4 acceptance and Phase 5 handoff.

## Required Gate Sequence

1. Finish and locally seal `P4.6-PLANNING-R0`.
2. Owner explicitly selects `D-P4.6-001` through `D-P4.6-012`.
3. Reconcile choices into non-effective `P4.6-PLANNING-R1`.
4. Owner accepts the exact reconciled planning-package SHA-256.
5. Prepare one non-effective `P4.6-START-R0` with exact path, dependency,
   runtime, data, network, and evidence bounds.
6. Owner separately accepts the exact start-package SHA-256.
7. Implement only the accepted generated-only scope.
8. Regenerate fixtures and run focused, security, compatibility, PostgreSQL,
   package, and repository validation authorized by the start package.
9. Seal evidence and a non-effective acceptance proposal.
10. Owner explicitly accepts the exact evidence package and technical commit.

No `continue` message, earlier phase authorization, planning acceptance, code
completion, test result, commit, or merge substitutes for a gate above.

## Proposed Delivery Sequence

### W1: Canonical Operations Contracts

Proposed scope:

- add the twenty contracts in
  `docs/phase-4/p4-6-contract-catalog.md` as typed product schemas;
- add canonical JSON projection and SHA-256 identities;
- define closed registries for metrics, labels, failures, service classes,
  degradation modes, worker classes, recovery tiers, capacity scenarios, and
  placement reasons;
- add generated fixture manifests and deterministic regeneration;
- enforce exact version rejection, size bounds, field bounds, enum closure,
  and forbidden-field scanning.

Stop conditions:

- any contract permits a credential, token, unrestricted URL, media payload,
  private/Government field, free-form metric label, or raw exception;
- canonical representation is platform- or locale-dependent;
- a new contract reinterprets accepted Phase 3 or Phase 4.0-4.5 semantics.

### W2: Observability And Reliability Core

Proposed scope:

- register existing Prometheus metrics and reject unregistered labels;
- introduce bounded typed telemetry envelopes and optional default-off exporter
  interfaces without selecting a vendor or endpoint;
- propagate validated W3C trace context and opaque correlation IDs across API,
  outbox, and worker boundaries;
- define operational/security log sinks while preserving audit and evidence as
  authoritative stores;
- implement the sanitized failure registry and mappings for APIs, jobs, events,
  logs, and metrics;
- implement objective revision, SLI aggregation, unknown-state handling,
  error-budget calculations, and safe health projections;
- keep target values unset in default generated fixtures.

Compatibility:

- existing `/metrics` remains available under its present authentication
  boundary;
- current request IDs remain accepted as local correlation candidates;
- exporters remain disabled when configuration, trust, destination, or policy
  is missing.

### W3: Worker Conformance And Control

Proposed scope:

- inventory each accepted domain worker and map its state model to the shared
  worker policy;
- add generated conformance tests for claim, heartbeat, lease loss, retry,
  cooldown, dead letter, duplicate delivery, idempotent result, outbox commit,
  shutdown, abandonment, and late-worker denial;
- add bounded circuit state and dependency-class registry;
- add hierarchical kill-switch and degradation revisions;
- make mandatory controls non-degradable;
- expose low-cardinality queue, retry, loss, stale-work, circuit, and recovery
  metrics.

Domain queue tables remain authoritative. A future broker adapter may mirror
the contract, but no external broker is required or activated.

### W4: Security And Isolation Assurance

Proposed scope:

- create a generated principal/role/department matrix for every P4.6 read and
  mutation boundary;
- test application authorization and database policy as independent oracles;
- apply and validate `FORCE ROW LEVEL SECURITY` for new department-scoped
  P4.6 tables;
- test ordinary role, cross-department role, table owner, superuser,
  `BYPASSRLS`, absent policy, unset/malformed scope context, pooled-connection
  reset, prepared query, transaction retry, and concurrent policy-change cases;
- fuzz bounded API, contract, header, trace, JSON, enum, timestamp, counter,
  identifier, and pagination inputs;
- verify denial is attributable without exposing rejected material;
- test kill-switch, stale policy, role misuse, and audit-write failure paths.

SQLite remains suitable only for deterministic single-process development
tests. It cannot be cited as PostgreSQL RLS evidence.

### W5: Supply-Chain Evidence

Proposed scope:

- build a canonical inventory from the locked dependency and produced package
  metadata available inside the authorized source environment;
- represent package identity, source revision, build inputs, license findings,
  vulnerability observation freshness, artifact digests, provenance
  observations, policy results, and unknowns;
- generate deterministic SPDX and CycloneDX projections;
- define a SLSA provenance projection without making a level claim;
- require stale vulnerability information to be visible and policy-sensitive;
- bind build outputs and evidence to the source commit and lockfile digests.

Initial generated-only implementation must not install or update scanners,
retrieve vulnerability databases, access registries, download artifacts, sign
attestations, or publish an SBOM. Those actions require later exact authority.

### W6: Recovery Design And Generated Drills

Proposed scope:

- classify database, object reference, generated fixture, configuration,
  contract, secret-reference, signing-key-reference, and audit/evidence assets;
- define dependency-aware backup and restore plans;
- record target RPO/RTO as unset, provisional, or approved;
- simulate generated backup manifests, interruption, corruption, missing
  dependency, restore ordering, integrity checks, observed RPO/RTO, and cleanup;
- add immutable generated drill evidence and safe health projections;
- preserve existing SQLite backup and recovery-drill behavior unless exact
  changes are named in the future start package.

No actual backup, restore, filesystem mutation, database recovery, or disaster
exercise is part of the generated-only baseline.

### W7: Capability Profiles And Placement

Proposed scope:

- define developer-laptop, owned-GPU-lab, server-node, and Kubernetes-node
  profile classes;
- distinguish declared, observed, attested, stale, unsupported, and unknown
  capability states;
- map each service and optional AI lane to required and preferred capability,
  resource, security, topology, and runtime constraints;
- support explicit optional-lane bypass while retaining provenance and output
  semantics;
- keep mandatory controls as hard placement requirements;
- produce one platform-neutral immutable placement plan;
- provide machine-disabled standalone and Kubernetes adapter projections.

The future Kubernetes projection may include requests/limits, affinity,
topology spread, disruption policy, NetworkPolicy intent, device-plugin
resources, or Dynamic Resource Allocation only when a target version and
driver capability are declared. This plan does not start or inspect a cluster.

### W8: Generated Capacity Methodology

The capacity suite has three scenario sizes:

| Scenario | Generated stream-equivalents | Purpose |
| --- | ---: | --- |
| C1 | 1 | Determinism, latency path, cold/warm distinction, and correctness baseline |
| C10 | 10 | Concurrency, queue fairness, bounded resource sharing, and partial degradation |
| C50 | 50 | Backlog, saturation, loss accounting, recovery, and placement-plan pressure |

Each scenario supports three workload modes:

- `latency`: lower concurrency and strict tail-latency observation;
- `balanced`: combined latency, throughput, backlog, and recovery observation;
- `throughput`: bounded sustained arrival rate and saturation behavior.

Generated inputs contain metadata and anonymous typed events only. The suite
must declare warmup, duration, sample count, arrival distribution, percentile
algorithm, clock source, queue bounds, loss counters, recovery interval, and
profile limitations. It cannot claim camera FPS, model throughput, GPU
capacity, city scale, or production capacity without later authorized runs on
declared hardware using separately approved data.

### W9: Read APIs And Future UI Support

Proposed read-only/default-off projections:

- platform and service health;
- objective definitions, freshness, and error-budget state;
- queue, retry, dead-letter, lease-recovery, and circuit summaries;
- effective degradation and kill-switch state;
- recovery-plan and drill summaries;
- capability profiles, placement plans, and capacity-run limitations;
- supply-chain bundle freshness and unknown states;
- security-control evidence summaries.

The initial P4.6 UI support is contract and API support only. Phase 5 owns the
operator experience. Any future mutation endpoint must require an exact role,
department/platform scope, purpose or reason, optimistic revision/ETag, audit,
idempotency, and separate activation authority.

### W10: Evidence, Compatibility, And Acceptance

Proposed completion gates:

- deterministic fixture regeneration is byte-exact;
- focused branch-enabled coverage is at least 90% for new logic, with critical
  failure and authorization modules at least 95%;
- full repository tests pass without deselection;
- Ruff, compile, schema, migration, package build/install, dependency
  compatibility, and historical readiness checks pass;
- one Alembic head exists and upgrade/downgrade compatibility is proven;
- PostgreSQL tests prove RLS, concurrent claims, isolation, recovery, and
  transactional outbox behavior;
- no network, model, media, private/Government data, operational action,
  container, Kubernetes, deployment, or remote Git access occurred;
- all generated capacity results include loss, incomplete-run, and limitation
  fields;
- evidence records exact source, fixture, dependency, contract, migration,
  and test digests;
- owner receives a non-effective exact acceptance proposal.

## Proposed Persistence Boundaries

The exact future migration depends on owner decisions, but the design should
prefer additive PostgreSQL tables such as:

| Store | Purpose | Authority |
| --- | --- | --- |
| `operations_objective_versions` | Immutable SLI/SLO definitions and target states | Platform policy |
| `operations_budget_windows` | Deterministic aggregate results | Derived, non-authorizing |
| `operations_degradation_revisions` | Hierarchical attributable degradation state | Policy control |
| `operations_circuit_snapshots` | Bounded dependency-class state | Derived/control input |
| `operations_kill_switch_revisions` | Fail-closed immutable switch history | Policy control |
| `operations_recovery_plans` | Recovery dependency and target references | Planning policy |
| `operations_recovery_drills` | Generated or later authorized drill evidence | Evidence |
| `operations_capacity_profiles` | Portable capability classes and constraints | Planning/runtime input |
| `operations_capacity_runs` | Generated workload plans and results | Evidence |
| `operations_supply_chain_bundles` | Canonical inventory and observation state | Evidence |
| `operations_control_evidence` | Security/isolation generated results | Evidence |
| `operations_outbox` | Transactional publication of sanitized state changes | Integration boundary |

Department-owned rows require department scope and forced RLS. Platform rows
require separately authorized platform roles. High-volume telemetry remains in
the telemetry system and is not copied into the transactional database.

## Proposed API Boundaries

Read endpoints should be versioned, paginated, freshness-aware, and sanitized.
Representative future routes:

```text
GET /operations/health
GET /operations/objectives
GET /operations/error-budgets
GET /operations/workers
GET /operations/circuits
GET /operations/degradation
GET /operations/kill-switches
GET /operations/recovery-plans
GET /operations/recovery-drills
GET /operations/capacity/profiles
GET /operations/capacity/runs
GET /operations/placement-plans
GET /security/control-evidence
GET /supply-chain/bundles
```

Mutation routes are not assumed. If a later accepted start package includes
them, each must use optimistic concurrency, an idempotency key, closed reason
code, actor attribution, scope checks, audit, transactional outbox, and
fail-closed stale-policy behavior.

## Test Matrix

| Area | Required generated/static validation |
| --- | --- |
| Contracts | versions, canonicalization, bounds, enums, unknowns, forbidden fields |
| Metrics | naming, unit stability, label allowlist, cardinality budget, histogram revision |
| Trace | valid/invalid context, new roots, no authority, baggage denial, async propagation |
| Logs | lane separation, redaction, access projection, retention reference, audit/evidence non-substitution |
| Failures | mapping, retry disposition, safe parameters, unknown fail-closed, cross-transport equivalence |
| SLO | good/valid events, unknowns, exclusions, windows, burn calculation, target state, replay |
| Workers | claims, leases, heartbeats, retries, jitter, dead letter, idempotency, outbox, abandonment, shutdown |
| Controls | hierarchy, deny precedence, expiry, stale revisions, ETags, audit failure, rollback |
| Security | RBAC, scope, RLS, owner/superuser/BYPASSRLS, pool reset, cross-scope, abuse, races |
| Supply chain | inventory identity, licenses, stale vulnerabilities, provenance unknowns, projection equivalence |
| Recovery | dependency order, incomplete backup, corruption, missing key/object, observed RPO/RTO, cleanup |
| Capacity | C1/C10/C50, all three modes, percentiles, backlog, saturation, loss, recovery, incomplete result |
| Placement | capability states, mandatory rejection, optional bypass, adapter equivalence, version mismatch |
| API/UI | scope, pagination, freshness, sanitized output, disabled writes, no topology or sensitive leakage |

## SLO And Recovery Policy Boundaries

The planning package intentionally does not choose numeric production targets.
The first generated-only implementation may validate schemas with clearly
labeled synthetic values, but those values cannot become defaults or claims.

An exact target decision must later identify:

- journey or service class;
- indicator and measurement point;
- good, valid, bad, unknown, and excluded event definitions;
- objective window and target;
- minimum sample and data-quality requirements;
- alert burn windows and thresholds;
- allowed and prohibited automatic reactions;
- owner, review period, rollback, and expiry;
- generated, lab, pilot, or production evidence class.

RPO/RTO decisions require the same distinction between target and observed
result and must name all dependent stores and key/configuration requirements.

## Security Stop Conditions

Implementation must stop closed if:

- a new metric label is unbounded or identity-bearing;
- trace or correlation context changes authorization behavior;
- logs become authoritative audit or evidence records;
- an unknown failure becomes retryable;
- a worker can commit after lease loss;
- a kill switch can grant unauthorized capability;
- a degradation mode bypasses mandatory security or evidence integrity;
- a PostgreSQL privileged role is treated as RLS-protected without evidence;
- a missing/stale vulnerability or provenance observation is reported as clean;
- backup creation is reported as successful recovery;
- an incomplete capacity run is reported as a capacity result;
- automatic placement activates an unsupported model, provider, camera,
  network, container, cluster, or operational action;
- an implementation path exceeds a later accepted exact allowlist.

## Documented Limitations

- Research used public official sources and repository analysis; no operational
  network, provider, Sentinel, camera, or media access occurred.
- No process, service, container, cluster, backup, restore, scanner, hardware,
  capacity, performance, stress, or recovery execution occurred.
- No dependency, model, dataset, artifact, vulnerability database, container
  image, or software was installed, updated, or downloaded.
- No production telemetry backend, SLO, RPO, RTO, capacity, security,
  compliance, provenance, recovery, or Kubernetes-readiness claim is made.
- The generated-only technical plan cannot replace future owned-lab,
  PostgreSQL, restore, security-review, capacity, or deployment evidence.
