# P4.6 Operations, Security, And Scale Threat Model

Status: planning-only, non-effective

## Purpose

This threat model covers the proposed P4.6 operational control plane,
telemetry contracts, resilience policies, recovery evidence, supply-chain
bundle, capacity harness, hardware profiles, and optional Kubernetes adapter.
It does not authorize implementation or operation.

## Protected Assets

- Integrity and availability of accepted Phase 0 through P4.5 behavior.
- Department isolation and purpose-bound access decisions.
- Audit, security, operations, investigation, and evidence records with their
  distinct authority and retention semantics.
- Queue jobs, leases, attempts, terminal outcomes, idempotency keys, and
  transactional outbox records.
- SLO definitions, error budgets, alert policies, degradation revisions, and
  kill-switch state.
- Backup manifests, restore results, recovery-drill evidence, and declared
  RPO/RTO observations.
- Source, dependency, license, SBOM, vulnerability, build, and provenance
  evidence.
- Capacity profiles, generated workloads, measurements, hardware-class
  declarations, placement plans, and limitations.
- Secrets and credentials by reference only; P4.6 telemetry must never contain
  their values.

## Trust Boundaries

1. Client to API request edge.
2. API to application authorization and department scope.
3. Application to PostgreSQL roles and row-security policies.
4. Transactional domain state to queue claims and workers.
5. Service process to metrics, trace, log, audit, and evidence emitters.
6. Telemetry emitter to local or external collector adapters.
7. Operator control to degradation, circuit, and kill-switch revisions.
8. Database to backup target and restore environment.
9. Source checkout to build environment, package artifact, and provenance.
10. Capability inventory to placement compiler.
11. Placement compiler to standalone, server, or Kubernetes adapters.
12. Kubernetes API to scheduler, CNI, storage, log backend, and device drivers.

## Actors

- Authorized operator, reviewer, security analyst, platform administrator, and
  recovery administrator.
- Application service, domain worker, scheduler, telemetry exporter, and
  evidence verifier.
- CI builder, dependency scanner, package registry, and artifact verifier.
- Cluster administrator, scheduler, kubelet, CNI, storage driver, device
  plugin, and DRA driver in a future deployment.
- Mis-scoped user, compromised service, malicious dependency, hostile input,
  careless administrator, overloaded node, failed database, and unavailable
  external telemetry sink.

## Threat Matrix

| ID | Threat | Failure mode | Required planning control |
| --- | --- | --- | --- |
| T-01 | Cardinality exhaustion | IDs, URLs, reasons, or free text create unbounded metric series | Closed label registry, static checks, per-family budgets, rejection at registration |
| T-02 | Sensitive telemetry disclosure | Secrets, people, plates, case data, or evidence IDs enter metrics or propagated context | Typed allowlists, structural redaction, no free-text labels, negative fixtures |
| T-03 | Signal-authority confusion | Operational logs are treated as audit or evidence | Separate contracts, stores/sinks, access policies, retention, and UI labels |
| T-04 | Trace-context injection | Malformed or attacker-selected context breaks correlation or pollutes downstream systems | Strict W3C parsing, length bounds, new root on invalid input, bounded tracestate |
| T-05 | Alert feedback storm | A failing exporter or dependency creates recursive alerts | Symptom alerts, deduplication, rate limits, inhibition, circuit state, no self-page loop |
| T-06 | False reliability claim | Dashboard reports SLO or capacity without valid evidence | Approval state, source-bound window, completeness, exclusions, and `unknown` default |
| T-07 | Retry amplification | Unbounded retries multiply load during dependency failure | Typed retryability, attempt cap, exponential backoff with jitter, deadline, budget |
| T-08 | Duplicate side effect | Lease expiry or crash repeats a non-idempotent action | Idempotency keys, transactional outbox, effect ledger, replay-safe handler contract |
| T-09 | Lost work | Job is leased and worker disappears | Lease expiry, bounded reaper, attempt history, terminal/dead-letter outcome |
| T-10 | Poison-job starvation | One malformed job blocks a queue | Per-job attempt cap, quarantine/dead letter, fair bounded claim ordering |
| T-11 | Circuit manipulation | Attacker opens/closes a circuit to hide failure or force traffic | Revisioned policy, role and reason, bounded state machine, audit and cooldown |
| T-12 | Kill-switch escalation | A narrow control enables broader authority or is silently cleared | Monotonic effective disable, scope hierarchy, optimistic lock, quorum option, audit |
| T-13 | Split-brain control state | Replicas disagree on kill switch or degradation mode | Database truth, versioned snapshots, cache TTL, fail-closed stale behavior |
| T-14 | Department crossover | API authorization or worker query accesses another department | Dual application/RLS oracle, forced RLS, scoped claims, negative concurrency tests |
| T-15 | RLS privileged bypass | Table owner, superuser, or `BYPASSRLS` role evades policy | Dedicated non-owner application role, `FORCE ROW LEVEL SECURITY`, privilege audit |
| T-16 | RLS side channel | Constraint, error, timing, or policy subquery leaks cross-scope existence | Constraint design review, sanitized errors, race tests, bounded timing assertions |
| T-17 | Audit erasure | Operational retention deletes attributable decisions | Append-only audit lane, independent retention authority, correction not overwrite |
| T-18 | Log tampering | Local process modifies or truncates security records | Integrity envelope, sequence/gap detection, restricted sink, immutable export receipt |
| T-19 | Backup exfiltration | Backup contains broader data than the caller can read | Separate recovery role, encrypted destination design, inventory, access audit, no API download |
| T-20 | Incomplete backup | RLS or missing WAL silently omits required state | Backup-specific validation, manifest, restore-first verification, coverage inventory |
| T-21 | Destructive restore | Recovery overwrites active state or wrong environment | Isolated destination, explicit environment binding, non-overwrite default, staged cutover |
| T-22 | Stale recovery claim | Old successful drill is displayed as current readiness | Expiry, source/config digest, age indicator, invalidation on material change |
| T-23 | SBOM incompleteness | Missing components are interpreted as clean | Completeness enum, source/tool bindings, unknown state, independent vulnerability evidence |
| T-24 | Forged provenance | Artifact and attestation are produced by the same untrusted path | Builder identity, digest binding, signature/trust policy, verification receipt, level `not_assessed` |
| T-25 | Dependency confusion | Name collision or untrusted index supplies a package | Lock hashes, explicit indexes, build isolation, provenance and source policy |
| T-26 | Scanner staleness | Old vulnerability data yields a false clean result | Database timestamp, source/version, stale state, no `passed` from unavailable refresh |
| T-27 | Capacity result gaming | Warmup, failed requests, or dropped work are excluded | Frozen workload, loss accounting, percentile method, raw aggregate counts, immutable config |
| T-28 | Hardware identity leakage | Serial, hostname, user, path, MAC/IP, or device ID enters evidence | Sanitized capability classes, no raw identifiers, bounded allowlist, owner-controlled labels |
| T-29 | Silent capability downgrade | Missing GPU or memory quietly skips required stages | Explicit placement decision, bypass reason, quality mode, operator-visible degradation |
| T-30 | Resource oversubscription | Scheduler plans more CPU, memory, GPU, storage, or bandwidth than available | Reservations, limits, admission policy, saturation budgets, fail-closed placement |
| T-31 | Kubernetes policy illusion | NetworkPolicy, PDB, logging, or security manifests exist but are not enforced | Cluster capability attestation and owned-cluster validation before readiness claim |
| T-32 | Probe cascade | Liveness depends on an unavailable downstream service and restarts healthy pods | Separate startup/readiness/liveness semantics and overload tests |
| T-33 | Accelerator privilege abuse | Device plugin or DRA driver expands workload privileges | Cluster-admin ownership, least privilege, signed driver provenance, isolated node pool |
| T-34 | Cross-node data residue | Worker or accelerator memory retains sensitive material | Zero-retention contracts, process isolation, buffer cleanup design, no claim before validation |
| T-35 | Planning-to-runtime confusion | A proposed policy, threshold, or manifest is treated as active | `effective=false`, environment and activation gates, explicit accepted package digests |

## Mandatory Invariants

1. Metrics use only enumerated low-cardinality labels. Camera, stream, person,
   plate, user, case, evidence, locator, secret reference, request ID, trace ID,
   exception text, and free text are prohibited labels.
2. Trace context is diagnostic metadata, not authentication, authorization,
   audit, evidence, or idempotency authority.
3. Logs never contain secret values. Sanitization happens before formatting,
   buffering, sampling, export, or exception wrapping.
4. Audit and evidence records are append-only. Corrections reference prior
   records and do not erase them.
5. A telemetry exporter failure cannot fail a core transaction or trigger an
   unbounded retry loop.
6. Production SLO targets remain unset until separately approved evidence
   exists. Missing data produces `unknown`, not healthy.
7. Domain jobs remain authoritative in domain stores. Shared resilience policy
   cannot alter business semantics.
8. Retries require an allowlisted transient failure code and remaining time,
   attempt, and resource budgets.
9. Every external side effect requires idempotency and a durable effect or
   delivery record before future activation.
10. An effective kill switch is the most restrictive applicable revision.
    Lower scopes cannot override a broader disable.
11. Application authorization and database RLS must independently deny
    cross-department access.
12. Application database roles cannot own protected tables and cannot have
    superuser or `BYPASSRLS` privileges.
13. Backup success does not imply recoverability. Only a bound restore drill
    can produce recovery evidence.
14. SBOM, vulnerability, license, and provenance states remain separate.
    Unknown or stale evidence never becomes pass.
15. Capacity evidence includes all attempts, failures, drops, timeouts, retries,
    warmup, queue growth, and recovery time.
16. A hardware profile contains capability classes and limits, not personal or
    unique machine identity.
17. Placement cannot enable a disabled feature and cannot silently substitute a
    lower-quality model or bypass an AI layer.
18. Kubernetes is optional. A valid standalone plan must exist for supported
    developer and owned-lab profiles.
19. Kubernetes policy presence is not enforcement evidence. CNI, admission,
    storage, logging, scheduler, and accelerator capabilities are explicit.
20. Planning artifacts remain non-effective until exact owner decisions,
    reconciled-package acceptance, start authorization, implementation
    evidence, and subphase acceptance occur.

## Required Negative Tests For Future Implementation

- High-cardinality and sensitive metric labels are rejected before
  registration.
- Invalid, oversized, repeated, or conflicting trace headers create a sanitized
  new context or fail closed according to the accepted contract.
- Exporter timeout, outage, and malformed response cannot roll back a domain
  transaction or leak raw payloads.
- Security, audit, operations, and evidence records cannot be read through the
  wrong API role or sink adapter.
- Non-retryable failures, expired deadlines, exhausted attempts, and open
  circuits never retry.
- Lease expiry, duplicate claims, worker crash, clock skew, and replay produce
  one visible terminal outcome with loss accounting.
- Global and department kill switches dominate capability-level enable
  attempts, including stale-cache and concurrent-revision cases.
- Normal, cross-department, table-owner, forced-RLS, superuser,
  `BYPASSRLS`, missing-policy, referential-integrity, and concurrent policy
  cases are explicit.
- Backup tampering, missing manifests, stale schema, partial WAL, active target,
  wrong environment, and restore collision stop closed.
- Incomplete or stale SBOM, unsigned provenance, wrong artifact digest,
  unknown license, unavailable vulnerability source, and expired exception do
  not produce a clean status.
- C1/C10/C50 results reject omitted failures, mismatched source/config,
  nondeterministic seeds, negative durations, impossible throughput, and
  undeclared hardware limitations.
- Standalone and Kubernetes plans reject unsupported resources, missing CNI
  enforcement, absent log sink, invalid probes, missing topology domains,
  privileged containers, unsigned accelerator drivers, and silent fallback.

## Residual Risks

- Telemetry systems can still expose patterns through aggregate timing and
  counts even when direct identifiers are removed.
- PostgreSQL superusers remain outside RLS; organizational role separation and
  database administration controls are required beyond application code.
- A backup and restore drill cannot prove recovery under every regional,
  hardware, operator, or corruption scenario.
- SBOM and provenance quality depends on builder and inventory completeness.
- Vulnerability intelligence can be delayed, incomplete, or inaccurate.
- Generated C1/C10/C50 workloads cannot prove camera, network, model, user, or
  city-scale production performance.
- Kubernetes controls depend on cluster version, admission, CNI, storage,
  runtime, node, and vendor-driver implementations.
- Dynamic placement improves portability but increases policy complexity and
  requires strong explainability and deterministic fallback tests.

These residual risks must remain visible in evidence and operator surfaces;
they cannot be converted into pass states by configuration.
