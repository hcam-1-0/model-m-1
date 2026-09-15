# Phase 4 Implementation Plan

Status: planning baseline prepared and composite decisions recorded; planning
acceptance and implementation authorization remain pending.

## Progress Accounting

Phase 4 uses a frozen 100-point work breakdown. A weighted item earns all of
its points only after its listed evidence passes and its acceptance requirement
is recorded. It earns zero points while pending or partially implemented.
Changes to scope or weights require an explicit rebaseline record showing old
weights, new weights, reason, date, and owner acceptance.

Current result: **3 of 100 points, or 3.00%**. This is the completed P4.0
handoff-and-planning-baseline item only.

## Frozen Work Breakdown

| ID | Deliverable | Points | Current | Completion evidence |
| --- | --- | ---: | ---: | --- |
| P4.0-A | Phase 3 handoff audit and Phase 4 planning baseline | 3 | 3 | Scope, architecture, backlog, decisions, checklist, research, roadmap synchronization |
| P4.0-B | Machine-validated Phase 4 event and state contracts | 3 | 0 | Schemas, chronology, GeoJSON profile, provenance, deterministic fixtures, bounds, privacy negatives |
| P4.0-C | Default-off control-plane persistence and API skeleton | 2 | 0 | Additive migration, RBAC, ETags, audit, outbox, production denial |
| P4.0-D | P4.0 threat evidence and owner acceptance | 2 | 0 | Security matrix, clean validation, evidence index, explicit acceptance |
| P4.1-A | Ingress validation, dedupe, partition, and event-time ordering | 4 | 0 | Duplicate, late, conflict, malformed, oversize, isolation tests |
| P4.1-B | Bounded adaptive multi-engine correlation | 5 | 0 | Deterministic CPU goldens, typed lane/arbitration contracts, watermark/replay and resource bounds |
| P4.1-C | Hypothesis, evidence, uncertainty, and retraction model | 4 | 0 | Canonical graph plus flat projection, lane lineage, contradiction, abstention, correction tests |
| P4.1-D | P4.1 acceptance | 2 | 0 | Reproducible evidence and owner acceptance |
| P4.2-A | Visual graph and canonical typed AST | 4 | 0 | Round-trip, lifecycle, shadow, version, digest, type, depth, and cost tests |
| P4.2-B | Stateful temporal nodes | 5 | 0 | Sequence/window/count/absence/cooldown generated goldens |
| P4.2-C | Constrained CEL host environment | 4 | 0 | Function allowlist, no side effects, compile-once evidence |
| P4.2-D | P4.2 acceptance | 2 | 0 | Rule replay, abuse tests, and owner acceptance |
| P4.3-A | Deterministic proposed-alert creation and deduplication | 4 | 0 | At-least-once replay and concurrency evidence |
| P4.3-B | Full alert lifecycle and optimistic concurrency | 5 | 0 | Transition matrix, actor/reason/ETag/audit tests |
| P4.3-C | Routing, authority class, suppression, escalation, and SLA policy | 4 | 0 | Mandatory-review baseline, bounded system automation, future-action denial, budgets, timers, overload tests |
| P4.3-D | P4.3 acceptance | 2 | 0 | Lifecycle recovery drill and owner acceptance |
| P4.4-A | Typed provider, generic transport, secret, destination, and field-policy contracts | 4 | 0 | Default-off generated provider/simulator, arbitrary-configuration denial, and redaction tests |
| P4.4-B | Generated reference catalogue and query workflow | 4 | 0 | Non-issuable fixtures, freshness, partial/outage/malformed tests |
| P4.4-C | Candidate matching, calibration, abstention, and review | 4 | 0 | Exact/fuzzy/contradictory/missing candidate goldens |
| P4.4-D | Provider governance and revocation drill | 2 | 0 | Kill switch, secret rotation, stale source, audit evidence |
| P4.4-E | P4.4 generated-only acceptance | 1 | 0 | No external connection and explicit owner acceptance |
| P4.5-A | Investigation timeline and typed entry contracts | 4 | 0 | Append-only facts/hypotheses/actions/corrections |
| P4.5-B | Evidence-reference graph and integrity | 4 | 0 | Source digests, typed derivations, missing evidence, provenance traversal |
| P4.5-C | Review, disposition, merge, reopen, and correction workflow | 3 | 0 | Role, reason, concurrency, and immutable-history tests |
| P4.5-D | Retention, hold, deletion, and export controls | 2 | 0 | Class policy, hold conflict, deletion proof, export audit |
| P4.5-E | P4.5 acceptance | 2 | 0 | Investigation reconstruction and owner acceptance |
| P4.6-A | Observability, SLOs, and sanitized failure taxonomy | 3 | 0 | Metrics cardinality, traces, logs, alerts, no-sensitive-data tests |
| P4.6-B | Queue leases, retries, circuit breakers, and recovery | 2 | 0 | Concurrent PostgreSQL workers and abandoned-lease drill |
| P4.6-C | Security, tenant isolation, misuse, and supply chain | 3 | 0 | Threat matrix, RLS bypass negatives, adversarial inputs, SBOM, vulnerability review |
| P4.6-D | C1/C10/C50 generated capacity evidence | 1 | 0 | Declared profile, load, latency, throughput, backlog evidence |
| P4.6-E | P4.6 acceptance | 1 | 0 | Recovery/kill-switch drill and owner acceptance |
| P4.7-A | Controlled generated end-to-end demonstration | 2 | 0 | Reproducible event-to-alert-to-timeline scenario |
| P4.7-B | Known limitations, evidence index, and operations pack | 1 | 0 | Complete traceability and no unsupported claims |
| P4.7-C | Phase 5 API/event/UI-state handoff | 1 | 0 | Consumer compatibility pack and UX state inventory |
| P4.7-D | Final Phase 4 owner acceptance | 1 | 0 | Explicit acceptance record |

## Exact Current Percentages

| Subphase | Earned / weight | Subphase completion | Phase contribution |
| --- | ---: | ---: | ---: |
| P4.0 | 3 / 10 | 30.00% | 3.00% |
| P4.1 | 0 / 15 | 0.00% | 0.00% |
| P4.2 | 0 / 15 | 0.00% | 0.00% |
| P4.3 | 0 / 15 | 0.00% | 0.00% |
| P4.4 | 0 / 15 | 0.00% | 0.00% |
| P4.5 | 0 / 15 | 0.00% | 0.00% |
| P4.6 | 0 / 10 | 0.00% | 0.00% |
| P4.7 | 0 / 5 | 0.00% | 0.00% |
| **Phase 4** | **3 / 100** | **3.00%** | **3.00%** |

## Delivery Sequence

### P4.0: Contracts And Guardrails

Define schemas for correlation hypotheses, evidence references, intelligence
rules, alert aggregates, lifecycle events, provider/query state, timeline
entries, review decisions, chronology, bounded GeoJSON, and typed provenance.
Add prohibited-field tests before persistence.
Then implement default-off control-plane records using existing department,
RBAC, ETag, reason, audit, row-security, and transactional-outbox patterns.

P4.0 cannot contact a provider or create an operational alert.

### P4.1: Correlation Foundation

Implement validated ingress, deterministic partitioning, bounded event-time
windows, deduplication, late/conflict handling, canonical hypothesis keys, and a
mandatory deterministic CPU lane. Define typed optional probabilistic,
temporal-graph, and ensemble lanes with capability-aware placement, arbitration,
calibration, contradiction, and abstention. Build the hypothesis graph as source
of truth and flat groups as projections. Preserve event, observation, receive,
durable-record, and correction chronology. Start with generated events only and
no external reference lookup, model artifact, dataset, or inference.

### P4.2: Rule Authoring And Evaluation

Extend the accepted Phase 3.4 visual graph and typed temporal-node pattern.
Compile configuration into immutable checked ASTs; use constrained CEL only for
stateless predicates. Prove deterministic replay, static cost limits, no side
effects, shadow-mode non-operation, immutable rollback, and safe failure under
malformed or expensive rules.

### P4.3: Alert Lifecycle And Orchestration

Create proposed alerts transactionally and deduplicate across delivery retries.
Implement lifecycle transitions, assignment, acknowledgement, dismissal,
suppression, escalation, merge, resolution, closure, reopen, and correction.
Keep priority, severity, confidence, and disposition independent. Add bounded
alert budgets and deterministic incident-level collapse without silent loss or
automatic confirmation. Implement the mandatory-review baseline and explicit
denial contracts for unauthorized bounded-automation or future autonomous-action
classes.

### P4.4: Authorized Reference Integrations

Implement the typed provider boundary with a generated provider first. Add
exact destination rules, typed secret references, field minimization, bounded
transport, response validation, freshness, circuit breaking, revocation,
candidate ranking, calibrated confidence, abstention, and mandatory human
review. The generic transport envelope is tested only against local generated
simulators and remains default-off. No real provider work begins under the
baseline start package or current owner selection.

### P4.5: Investigation Timeline And Evidence

Build append-only timelines and immutable evidence references. Separate source
facts, system hypotheses, operator observations, decisions, actions, and
corrections. Represent immutable entities, producing activities, attributable
agents, typed derivations, and correction propagation. Implement retention
classes, hold overlays, deletion evidence, and controlled export manifests
without copying source media by default.

### P4.6: Operations, Security, And Scale

Add low-cardinality metrics, traces, separate audit/security/operational logs,
leases, retries, dead letters, circuit breakers, kill switches, recovery,
application and PostgreSQL row-security isolation tests, abuse tests,
supply-chain evidence, and generated C1/C10/C50 capacity profiles.

### P4.7: Acceptance And Phase 5 Handoff

Run a reproducible generated scenario from Phase 3 events through correlation,
proposed alert, review, and investigation timeline. Seal known limitations,
evidence indexes, operator API contracts, UI states, accessibility needs, and
error/degradation behavior for Phase 5.

## Six-Person Ownership Model

| Role | Primary ownership | Required review contribution |
| --- | --- | --- |
| Project owner/system architect | Scope, decisions, cross-phase contracts, final acceptance | Risk and boundary review |
| Backend/platform engineer | Aggregates, APIs, persistence, outbox, workers | Concurrency and migration review |
| Intelligence/rules engineer | Correlation engine, graph compiler, temporal nodes | Determinism and explainability review |
| Data/integration engineer | Provider contracts, candidate normalization, freshness | Data minimization and provenance review |
| Frontend/workflow engineer | Phase 5 handoff states, reviewer workflow contracts | Human factors and error-state review |
| Infrastructure/security engineer | Isolation, observability, recovery, supply chain | Threat, secrets, egress, and operations review |

Roles express accountability, not mandatory separate approvers. The owner may
accept generated-only milestone evidence under the current team policy, but
provider-specific legal/data authorization remains a separate organizational
gate.

## Validation Matrix

- schema: required fields, bounds, unknown fields, major versions, canonical
  serialization, prohibited fields, temporal chronology, bounded GeoJSON, and
  typed provenance;
- event delivery: duplicate, reorder, gap, late, conflict, redelivery, replay,
  dead letter, oversized payload;
- correlation: exact windows, false joins, missing/contradicting evidence,
  expiry, supersession, retraction, clock uncertainty;
- rules: type errors, unknown functions, depth/cost limits, deterministic AST,
  temporal edge cases, schedule transitions, shadow isolation, and rollback;
- alerts: duplicate prevention, transition authorization, concurrent ETags,
  timers, budgets, collapse, suppression, escalation, merge/reopen/correction;
- integrations: secret rotation, redaction, destination denial, TLS, timeout,
  malformed/oversized response, stale data, outage, revocation;
- investigations: immutable ordering, correction without rewrite, provenance,
  hold/deletion conflict, bounded export;
- isolation: department, actor, provider, rule, alert, and timeline access at
  both application and row-security layers, including owner/BYPASSRLS negatives;
- operations: queue saturation, abandoned lease, retry classes, circuit state,
  kill switch, backup/restore, no-sensitive-telemetry;
- scale: generated C1/C10/C50 workload with declared hardware and no statewide
  performance claim.

## Stop Conditions

Stop closed when a required schema, authorization, retention class, policy,
secret provider, exact destination, source freshness, evidence reference,
department scope, temporal field, coordinate system, or integrity check is
absent. Also stop when a bounded window, queue, state count, alert budget, retry
budget, output size, geometry size, or timeline size would be exceeded. A
degraded component must not silently lower a required review gate.

## Next Authorized Work

The eight owner design decisions are recorded. The only next work under this
package is exact owner acceptance of the resealed planning baseline. Executable
contracts and tests require a separately prepared and accepted `D-P4.0-START`
package.
