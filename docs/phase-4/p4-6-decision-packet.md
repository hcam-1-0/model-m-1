# P4.6 Owner Decision Packet

Status: owner selections pending

Authority: `D-P4.6-PLAN-AUTH`

These are non-effective architecture choices for P4.6 Operations, Security,
And Scale. The recommendation for each decision is an engineering proposal,
not an owner decision. `continue`, silence, implementation preferences from a
different phase, or acceptance of this document do not select an option.

Record all twelve IDs explicitly. Composite choices are valid only where an
option says that capabilities can coexist.

## Recommended Profile

`C / A / A / A / A / A / A / A / A / A / C / C`

This profile preserves the existing Prometheus and domain-worker investments,
adds portable typed contracts, treats unknown states honestly, keeps standalone
operation first-class, and makes Kubernetes an optional adapter instead of a
product dependency.

## D-P4.6-001: Telemetry Architecture

### A. Prometheus only

Keep the current metric model and add more Prometheus instruments and
dashboards.

Benefits: smallest dependency and migration surface; strong operational metric
fit. Costs: traces and logs remain separately shaped, and future multi-service
correlation has no common semantic envelope.

### B. OpenTelemetry-first replacement

Replace current instrumentation with OpenTelemetry APIs and an OTel-native
pipeline.

Benefits: broad signal model and exporter portability. Costs: unnecessary
replacement risk, dependency growth, and a larger blast radius before runtime
evidence exists.

### C. Existing Prometheus plus typed OpenTelemetry-compatible adapters

Keep existing Prometheus metrics authoritative, add a central low-cardinality
registry, and define bounded metric/span/log envelopes with default-off OTel
export adapters.

Benefits: preserves current behavior while creating a portable multi-signal
contract. Costs: requires equivalence tests and duplicate-semantic prevention.

### D. Vendor-managed observability platform

Adopt one hosted vendor's agents, schemas, and dashboards.

Benefits: rapid packaged operations. Costs: external dependency, egress,
licensing, credentials, deployment coupling, and lock-in that are outside the
current boundary.

Recommendation: **C**.

## D-P4.6-002: Trace And Correlation Context

### A. W3C Trace Context plus an opaque H-CAM correlation ID

Validate `traceparent`/bounded `tracestate`, propagate an independent opaque
operation ID, disable baggage by default, and treat all context as untrusted
metadata.

Benefits: standards-compatible propagation without mixing trace state with
authorization. Costs: strict parsing and transport-equivalence work.

### B. H-CAM request ID only

Extend the existing request ID across APIs and workers.

Benefits: simple. Costs: weak interoperability and limited parent/child span
semantics.

### C. Framework-generated trace identifiers

Let each service framework create and propagate its native identifiers.

Benefits: low initial design effort. Costs: inconsistent semantics and weak
cross-language replay.

### D. Rich baggage context

Propagate department, purpose, case, alert, and other business context as
baggage.

Benefits: convenient querying. Costs: high privacy, cardinality, spoofing, and
authorization-confusion risk.

Recommendation: **A**.

## D-P4.6-003: Operational, Security, Audit, And Evidence Signal Separation

### A. Independently governed lanes with typed projections

Use separate schemas, stores, access controls, retention-policy references, and
export controls for operational logs, security logs, audit records, and
evidence records. Metrics and traces are separate non-authoritative telemetry
lanes. Cross-lane links use opaque references.

Benefits: strongest authority and privacy boundary; audit/evidence cannot be
silently replaced by logs. Costs: more lifecycle policy and testing.

### B. One structured event store

Put all signals into one event table with a type field.

Benefits: easy search and transport. Costs: broad access, retention conflicts,
and authority ambiguity.

### C. One log pipeline with indexes

Send everything to a centralized log backend and separate by index.

Benefits: operational convenience. Costs: infrastructure policy becomes the
only isolation control and evidence semantics remain weak.

### D. Per-service local logging

Let each module define and retain its own logs.

Benefits: strong module autonomy. Costs: inconsistent failure codes,
correlation, access, and retention.

Recommendation: **A**.

## D-P4.6-004: SLI, SLO, Error-Budget, And Alert Policy

### A. User-journey plus service-class objectives with evidence-gated targets

Define availability, correctness, freshness, latency, durability, and recovery
SLIs. Keep target values unset until generated and owned-lab evidence supports
provisional values; require owner approval for production targets and error
budget actions.

Benefits: honest objectives tied to observable outcomes. Costs: targets cannot
be marketed early and require disciplined data-quality rules.

### B. Fixed platform-wide targets now

Choose one availability and latency target for every service.

Benefits: simple headline. Costs: unsupported precision and mismatched service
semantics.

### C. Per-team informal dashboards

Track useful metrics without objectives or budget policy.

Benefits: low ceremony. Costs: no consistent reliability decisions.

### D. Infrastructure-only objectives

Measure process uptime, CPU, memory, and queue depth.

Benefits: easy collection. Costs: does not measure correctness, freshness, or
operator outcomes.

Recommendation: **A**.

## D-P4.6-005: Sanitized Failure Taxonomy

### A. Central closed registry with domain extensions

Create stable failure classes, retry disposition, public status, safe
parameters, and domain-specific codes under one reviewed registry. Unknowns map
to a non-retryable internal code.

Benefits: deterministic APIs, worker behavior, metrics, logs, and tests. Costs:
registry governance is required.

### B. HTTP-status taxonomy

Use HTTP status as the primary failure classification.

Benefits: simple API behavior. Costs: not portable to workers, queues, recovery,
or dependency circuits.

### C. Exception-class taxonomy

Expose normalized application exception names.

Benefits: easy implementation mapping. Costs: implementation leakage and
unstable public behavior.

### D. Free-form error messages

Store and return descriptive text.

Benefits: immediate debugging detail. Costs: redaction, cardinality, stability,
and secret/data exposure risk.

Recommendation: **A**.

## D-P4.6-006: Worker Resilience Architecture

### A. Domain-authoritative database jobs plus shared conformance policy

Keep existing domain queue tables and workers. Standardize leases, heartbeats,
late-commit denial, bounded retries, dead letters, idempotency, outbox coupling,
shutdown, abandonment recovery, and metrics through common contracts. Reserve
a disabled adapter contract for a future external broker.

Benefits: preserves ownership and transactional behavior; supports standalone
operation. Costs: every worker must pass a shared conformance suite.

### B. One new global PostgreSQL queue

Move all work to a central job table.

Benefits: one worker implementation. Costs: migration risk, coupling, and loss
of domain-specific transaction boundaries.

### C. External broker now

Adopt Kafka, RabbitMQ, NATS, or a cloud queue immediately.

Benefits: mature distributed messaging. Costs: dependency, deployment,
operations, and exactly-once misconception risks.

### D. In-memory queues

Use process-local bounded queues and reconstruct work after restart.

Benefits: fast and simple. Costs: poor durability and recovery semantics.

Recommendation: **A**.

## D-P4.6-007: Kill Switches And Degradation

### A. Hierarchical revisioned fail-closed control plane

Define platform, department, service, capability, and adapter scopes. Deny wins;
stricter parent state cannot be overridden; controls are attributable,
expiring, audited, and rollback-capable. Mandatory security and evidence
controls cannot degrade.

Benefits: visible and controlled failure behavior from laptop to cluster.
Costs: conflict resolution and stale-policy tests are substantial.

### B. Environment-variable switches

Use static process configuration.

Benefits: easy standalone operation. Costs: weak attribution and slow changes.

### C. Feature flags

Use a general feature-flag service.

Benefits: mature rollout controls. Costs: external dependency and ordinary
flags do not automatically provide safety hierarchy or audit semantics.

### D. Automatic degradation only

Let resource and SLO state directly switch modes.

Benefits: fast response. Costs: unsupported automation could silently alter
analytics or operational semantics.

Recommendation: **A**. Automatic recommendations can be added later, but they
must not bypass explicit authority.

## D-P4.6-008: Application Authorization And PostgreSQL RLS Assurance

### A. Independent application and database policy oracles

Test department scope and roles at the application boundary and forced RLS at
the database boundary, including table-owner, superuser, `BYPASSRLS`, absent
policy, cross-scope, race, prepared-query, and pool-reset negatives.

Benefits: layered isolation with explicit privileged-path evidence. Costs:
requires PostgreSQL-specific generated validation in addition to SQLite tests.

### B. Application authorization only

Rely on API and repository scope filters.

Benefits: database portability. Costs: one missing filter can cross scopes.

### C. PostgreSQL RLS only

Let database policies provide all department isolation.

Benefits: centralized data enforcement. Costs: non-database actions and
privileged roles remain outside it.

### D. Schema or database per department

Physically isolate each department.

Benefits: strong separation. Costs: migration, operations, search, and scale
complexity; it does not replace application policy.

Recommendation: **A**.

## D-P4.6-009: Supply-Chain Evidence Profile

### A. Canonical internal bundle with SPDX, CycloneDX, and SLSA projections

Maintain one typed inventory for dependencies, artifacts, licenses,
vulnerabilities, provenance, build observations, and unknowns. Generate
loss-accounted projections; make no conformance or assurance-level claim
without exact evidence.

Benefits: avoids divergent inventories and supports multiple ecosystems.
Costs: projection equivalence and unknown-state rules must be tested.

### B. SPDX only

Use one standardized SBOM format.

Benefits: narrower scope. Costs: provenance and operations-oriented dependency
semantics need separate handling.

### C. CycloneDX only

Use one BOM format for software, services, vulnerabilities, and operations.

Benefits: rich ecosystem. Costs: build provenance still requires a separate
model.

### D. Tool-native reports

Store whatever each future scanner or build tool emits.

Benefits: minimum transformation. Costs: poor reproducibility, portability,
and policy consistency.

Recommendation: **A**.

## D-P4.6-010: Backup, Restore, RPO/RTO, And Recovery

### A. Restore-first tiered recovery with evidence-gated RPO/RTO

Classify protected assets and dependencies; define database, object,
configuration, key, contract, and evidence recovery order; treat backup as
unverified until an authorized isolated restore and integrity check succeeds;
record observed RPO/RTO separately from targets.

Benefits: measures recoverability instead of backup creation. Costs: later
isolated drills need storage, cleanup, and separate execution authority.

### B. Backup-success model

Treat successful scheduled backup jobs as recovery assurance.

Benefits: easy measurement. Costs: no proof that data is complete or restorable.

### C. Database-only recovery

Protect PostgreSQL and reconstruct other assets.

Benefits: smaller scope. Costs: object references, contracts, configuration,
keys, and evidence dependencies may not reconstruct consistently.

### D. Infrastructure snapshot recovery

Rely on VM, volume, or cluster snapshots.

Benefits: potentially fast. Costs: application consistency and cross-store
integrity are not guaranteed.

Recommendation: **A**.

## D-P4.6-011: Dynamic Hardware Profiles And Capacity Method

### A. One conservative CPU profile

Build and validate only for the developer laptop.

Benefits: simplest immediate environment. Costs: does not satisfy the
platform-wide dynamic hardware requirement.

### B. Separate code paths per environment

Maintain laptop, GPU, server, and Kubernetes editions.

Benefits: direct tuning. Costs: feature drift, duplicated security logic, and
hard upgrades.

### C. Capability-aware profiles plus generated C1/C10/C50 evidence

Use one contract set with profile-class capabilities, required controls,
optional lane bypass, and deterministic placement. Define latency, balanced,
and throughput workload modes. C1/C10/C50 validate generated metadata/event
workloads; later owned-hardware runs produce profile-specific evidence without
universal capacity claims.

Benefits: runs conservatively on the developer laptop while preserving GPU,
server, and cluster capabilities in main architecture. Costs: compatibility
matrix and honest limitation reporting are required.

### D. Runtime auto-tuning without profiles

Probe resources and continuously choose execution settings.

Benefits: convenience. Costs: nondeterminism, hidden degradation, and unsafe
capability activation.

Recommendation: **C**. Later bounded auto-tuning may operate only inside an
approved profile envelope.

## D-P4.6-012: Standalone And Kubernetes Scheduling Boundary

### A. Standalone only

Implement local scheduling and defer all cluster contracts.

Benefits: lowest near-term complexity. Costs: later cluster support may require
contract redesign.

### B. Kubernetes-native core

Represent all scheduling as Kubernetes resources, including laptop use.

Benefits: one cluster-oriented deployment model. Costs: Kubernetes becomes a
mandatory dependency and harms offline/single-machine operation.

### C. Platform-neutral placement contract with optional adapters

Keep a pure placement policy and immutable plan. A standalone executor is
first-class; an optional Kubernetes adapter maps the same requirements to
requests, limits, affinity, topology spread, disruption policy, NetworkPolicy,
device plugins, or DRA when supported. No adapter runs by default.

Benefits: portable and testable without a cluster; preserves future scale.
Costs: adapter equivalence and Kubernetes version/capability checks are needed.

### D. External scheduler abstraction now

Create generic adapters for Kubernetes, Nomad, Slurm, and cloud batch systems.

Benefits: broad portability. Costs: speculative surface and high maintenance.

Recommendation: **C**.

## Decision Recording Template

```text
D-P4.6-001: C
D-P4.6-002: A
D-P4.6-003: A
D-P4.6-004: A
D-P4.6-005: A
D-P4.6-006: A
D-P4.6-007: A
D-P4.6-008: A
D-P4.6-009: A
D-P4.6-010: A
D-P4.6-011: C
D-P4.6-012: C
```

After explicit selections, the next planning action is to reconcile them into
`P4.6-PLANNING-R1`. Implementation remains prohibited until the owner accepts
that exact reconciled package and separately accepts a digest-bound P4.6 start
package.
