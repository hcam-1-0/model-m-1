# P5.6 Workflow And Feature Catalogue

Status date: 2026-09-10

Status: proposed generated-only operator workflows; owner decisions pending

## Common Interaction Contract

Every P5.6 page uses the accepted Phase 5 shell, session, navigation,
capability, query, error, observability, accessibility, and resource-profile
contracts. Each page begins with an authoritative read projection and never
derives a consequential capability from UI state.

Common page regions are:

- identity, organization, department, purpose, and freshness context;
- page title, bounded description, and authoritative last-updated state;
- server-filtered list or summary with explicit completeness;
- typed filters, sort, cursor pagination, and saved-view projection;
- list/detail handoff preserving scope, filter, and focus return target;
- allowed-action area populated only by server-produced capabilities;
- source, policy, revision, limitation, and audit-reference panel;
- loading, empty, partial, stale, degraded, denied, conflict, failure, and
  recovery states.

## Cross-Portal Handoffs

| Source | Target | Preserved context | Authority behavior |
| --- | --- | --- | --- |
| Command Center workload | Admin change request | department, resource, reason class | Admin Center refetches and reauthorizes |
| Command Center degradation | Operations service detail | service, window, degradation revision | Operations refetches authoritative state |
| Security denied-action aggregate | Audit record detail | bounded query, actor reference, correlation reference | Audit producer independently authorizes |
| Admin role binding | Security access assurance | role, subject, department, policy revision | Security refetches its own minimized view |
| Operations kill-switch projection | Admin governance history | capability, effective revision | No direct toggle; Admin refetches proposal history |
| Camera diagnostics | Admin stream governance | camera/stream opaque IDs, current revision | Existing camera editor capability still required |
| Supply-chain finding | Operations service dependency | component, build, service refs | Each domain preserves its own authority |
| Compliance exception | Security evidence reference | policy, exception, evidence ref | Evidence is not resolved or downloaded |

URL parameters carry opaque identifiers and bounded view state only. They do
not carry tokens, secrets, raw policy, personal data, capabilities, or trusted
department assertions.

## Admin Center Workflows

### A1. Administrative overview

1. Load summary counts scoped by organization, department, and capability.
2. Distinguish pending approval, conflict, validation failure, stale policy,
   blocked producer, expiring exception, and not-configured states.
3. Select a card to open an authoritative filtered table, not a client-filtered
   mixed queue.
4. Preserve the source revision and query time window in the handoff.

Features:

- pending work by typed domain;
- overdue access review and exception review;
- policy/configuration drift projection;
- blocked executor and missing producer inventory;
- recent administrative-event references;
- exact unknown and partial counts.

### A2. Organization and department governance

1. Browse organization and department hierarchy as tree plus authoritative
   table.
2. Inspect department status, owner refs, policy revision, inherited settings,
   direct settings, and unresolved conflicts.
3. Open a generated proposal preview for a bounded field change.
4. Validate impact across users, cameras, services, saved views, and policy.
5. Submit only when the server-produced capability permits it; P5.6 fixtures
   return a non-effective generated receipt.

No department deletion, data movement, ownership transfer, or scope widening
is executed.

### A3. User, membership, session, and access review

1. Search minimized account projections by opaque ID, display label, role, or
   status within an authorized department.
2. Inspect role bindings, membership revisions, access-review state, session
   posture, revocation observation, and authentication assurance.
3. Compare current and proposed bindings.
4. Show separation-of-duty conflicts and affected resources.
5. Record a generated proposal or review decision without mutating identity.

Credentials, authenticators, tokens, personal profiles, raw IP addresses, and
secret recovery data are never shown.

### A4. Role, permission, and policy analysis

1. Select a role revision.
2. View direct, inherited, conditional, denied, and unavailable capabilities.
3. Compare revisions through exact added/removed/changed permission rows.
4. Inspect static and dynamic separation-of-duty constraints.
5. Run generated policy examples with synthetic subjects/resources only.
6. Prepare a typed proposal with blast-radius and privilege-escalation checks.

The UI does not evaluate production policy or infer access from the matrix.

### A5. Change request and approval

1. Create or resume a draft bound to resource revision and policy revision.
2. Validate schema, dependencies, scope, conflicts, expiry, and rollback ref.
3. Submit with bounded reason and idempotency key.
4. Eligible reviewer examines exact before/after, validation evidence, impact,
   and proposer relationship.
5. Reviewer approves, rejects, or requests changes using a typed reason.
6. Scheduled/effective states stay unavailable without a future executor.

Self-approval is not permitted when independent review is required. The
browser never treats a generated approval as an applied change.

### A6. Camera and stream governance

- camera and endpoint configuration list/detail;
- department assignment and revision history;
- capability refresh policy and cached observation history;
- analytics assignment and geometry/rule references;
- generated proposal for configuration change;
- explicit handoff to Operations diagnostics;
- no connection, probe, ONVIF call, playback, snapshot, recording, PTZ, or
  provider action.

### A7. Integration, provider, and secret-reference governance

- provider type, enabled projection, revocation, health observation, and
  destination-policy ref;
- opaque `secret_ref`, provider class, last rotation observation, and policy
  state without secret value;
- exact allowed destination rule and certificate metadata projection;
- proposed enable/disable/revoke/rotate-request lifecycle;
- explicit unavailable states for test connection, reveal, resolve, rotate,
  or external login;
- no network request or authentication-extension loading.

### A8. Feature, configuration, and kill-switch governance

- typed flag/config catalogue with owner, revision, default, override scope,
  expiry, dependencies, and evaluation state;
- effective-state projection with source and reason;
- dependency graph plus authoritative table;
- generated blast-radius and rollout preview;
- kill-switch current revision and affected capabilities;
- proposal history and conflicts;
- no immediate toggle, generic JSON editor, or client-side targeting.

### A9. Resource profile, model-lane, and deployment projection

- low-resource, enhanced-workstation, control-room, GPU-lab, future-server,
  and Kubernetes profiles;
- observed versus required capability dimensions;
- supported, degraded, bypassed, unavailable, and unknown lanes;
- placement and topology projection;
- profile comparison and generated recommendation explanation;
- no hardware discovery, activation, model operation, container, cluster, or
  deployment action.

### A10. Retention policy projection

- policy source and jurisdiction refs;
- record classes and unresolved applicability;
- generated effect preview, conflicts, residuals, exceptions, and owner;
- approval and effective-state prerequisites;
- no period selection by the UI;
- no hold, release, deletion, export, backup, or storage operation.

## Security Center Workflows

### S1. Security posture triage

1. Load bounded posture dimensions separately: access, authentication,
   configuration, secrets, supply chain, audit, exceptions, and isolation.
2. Display source age, completeness, policy revision, evidence age, and unknown
   counts.
3. Drill into a dimension-specific authoritative table.
4. Record a generated review note or exception proposal where capability
   allows; do not mark the platform secure or compliant.

### S2. Access assurance and department isolation

- high-risk and broad capabilities;
- wildcard and inherited grants;
- dormant and expiring access;
- SoD conflicts and self-approval exposure;
- API authorization versus RLS parity evidence;
- service-account and worker-scope projection;
- cross-department denial evidence;
- access-review queue and generated decisions.

### S3. Denied and anomalous activity

- low-cardinality aggregate by safe reason, resource class, action class, and
  bounded time window;
- no camera, user, locator, token, or secret as a metric label;
- authorized drill-down to minimized security event refs;
- correlation links to audit refs when present;
- explicit statement that denial volume is not proof of attack or guilt;
- future external SOC handoff remains disabled.

### S4. Privileged activity review

- proposal, approval, step-up, executor, effect, rollback, and conflict
  chronology;
- actor refs, role/policy revisions, reason classes, and audit refs;
- self-approval and stale-authorization indicators;
- break-glass status shown as unavailable until backend policy, strong
  authentication, expiry, alerting, and after-action review exist;
- no administrator impersonation or bypass.

### S5. Session and authentication posture

- identity-provider and federation metadata projection;
- active/expired/revoked/unknown session aggregates;
- assurance and phishing-resistance assertion source;
- reauthentication and inactivity policy refs;
- revocation propagation age;
- failed authentication and lockout aggregates;
- no token, cookie, assertion, authenticator, IP, or credential display.

### S6. Audit explorer

- cursor-paginated immutable audit references;
- actor, role, department, purpose, action, resource class, result, sequence,
  record time, policy revision, correlation, and source;
- integrity and retention-policy observations as separate fields;
- exact detail refetch and append-only correction reference;
- no editable audit entry, raw secret/request body, source evidence, or direct
  export.

### S7. Compliance, policy, exception, and attestation

- framework/control reference catalogue without automatic compliance claim;
- policy revision and implementation/evidence mappings;
- exception scope, justification class, owner, approval, expiry, renewal, and
  compensating-control refs;
- attestation chronology and evidence refs;
- missing, stale, partial, contradictory, and not-applicable states;
- no legal conclusion, production certification, or evidence resolution.

### S8. Supply-chain posture

- release/component/SBOM identity and digest;
- direct/transitive dependency and service relationship;
- license assertion and review state;
- vulnerability observation, source, age, severity, applicability, and
  exception;
- build/source provenance assertion and verification result;
- completeness, freshness, accepted baseline, and drift;
- no scanner execution, vulnerability refresh, artifact download, or SLSA
  level claim.

## Operations Center Workflows

### O1. Platform health triage

1. Load authoritative service and dependency summary.
2. Separate unhealthy, degraded, stale, unknown, not configured, and partial.
3. Order by server-produced impact and dependency relationships, not a
   client-invented severity.
4. Open service detail with bounded signal history, current controls, SLO
   state, queues, dependencies, and limitations.
5. Handoff to Security or Admin with opaque refs and authoritative refetch.

### O2. Service and dependency inventory

- service version, environment, owner ref, capability, health observation,
  last heartbeat, dependency status, and deployment-profile projection;
- graph visualization with authoritative nodes/edges table;
- cycle, missing dependency, stale observation, and incompatible revision
  states;
- no process, service, container, or cluster control.

### O3. Queue, worker, retry, and circuit operations

- depth, oldest age, in-flight, lease, retry, dead-letter, cooldown, backoff,
  abandoned-work, and circuit state;
- typed saturation and recovery projections;
- generated drain/retry/requeue/recover previews only;
- exact reasons why control commands are unavailable;
- no job execution, queue mutation, broker connection, or worker signal.

### O4. Data, storage, database, and event bus

- component health, capacity projection, replication/consistency assertion,
  migration/schema revision, backup coverage, restore/drill evidence age, and
  retention refs;
- database RLS policy coverage and application-role posture;
- storage and media-edge status without object listing or media access;
- event-bus lag and outbox state without payload browsing;
- no SQL console, object browser, backup, restore, delete, or broker operation.

### O5. Media edge and AI runtime status

- edge/service health, session-admission capacity, codec/transport capability,
  scheduler state, runtime profile, model-lane status, saturation, bypass, and
  fallback reason;
- links to generated capacity evidence and accepted artifact refs;
- no playback issuance, provider access, cameras, media, model loading,
  inference, or hardware execution.

### O6. SLO and error-budget review

- SLI definition, source, window, completeness, target policy ref, objective,
  current value, budget remaining, burn projection, and degradation state;
- target `unset` and data `insufficient` are first-class states;
- generated C1/C10/C50 evidence is not a production SLO;
- no production target selection or alert activation.

### O7. Degradation and kill-switch review

- effective degradation and switch revision;
- trigger/source, reason, affected capabilities, denied actions, dependency
  impact, expiry, recovery criteria, and superseding revision;
- generated proposed change and impact preview;
- no direct switch, profile activation, or infrastructure command.

### O8. Maintenance, backup, recovery, and disaster recovery

- maintenance proposal and affected dependency graph;
- backup policy, inventory, success assertion, age, encryption assertion, and
  restoration evidence ref;
- RPO/RTO policy reference, current evidence, last drill, results,
  limitations, and unresolved prerequisites;
- generated recovery sequence preview;
- no maintenance, backup, restore, failover, recovery drill, or target change.

### O9. Capacity and topology

- C1/C10/C50 generated workload definitions and hardware declaration;
- latency, throughput, backlog, saturation, recovery, and resource-use results;
- low-resource, enhanced, control-room, GPU-lab, server, and Kubernetes
  topology comparison;
- exact extrapolation and production-claim limitations;
- no stress, performance, thermal, container, Kubernetes, or deployment run.

## Authoritative Non-Visual Alternatives

| Visual | Required equivalent |
| --- | --- |
| Organization tree | Parent/child department table with depth and path |
| Capability matrix | Role, resource, action, effect, condition, source table |
| Policy graph | Rule/dependency node and edge tables plus evaluation trace |
| Service topology | Service/dependency table with state and freshness |
| Queue chart | Time-bucket table with exact values and missing-data markers |
| SLO/budget chart | Windowed SLI and budget table with target/source/coverage |
| Supply-chain graph | Component/service/dependency/provenance tables |
| Capacity chart | Scenario/result/limit table with declared hardware |
| Approval lifecycle | Ordered transition table with actor, reason, revision, time |

## Generated Fixture Families

- C1: one organization, one department, bounded roles/services/queues;
- C10: ten departments with mixed freshness, conflicts, denials, and
  degradations;
- C50: fifty departments/services/config records with cursor pagination and
  bounded summaries;
- cross-department hostile fixtures;
- self-approval, stale ETag, stale policy, replayed idempotency, missing purpose,
  and revoked-session fixtures;
- secret-shaped, token-shaped, personal-data-shaped, path, markup, and
  oversized hostile strings that must be redacted, rejected, or safely shown;
- partial telemetry, missing audit links, stale SBOM, unknown backup, no RLS
  evidence, and disabled producer fixtures;
- resource-profile equivalence fixtures proving authority and truth invariance.

All fixtures remain synthetic and contain no Government, police, private,
camera, media, identity, credential, secret, model, or operational data.

## Implementation Boundary

These workflows define what a functionally complete operator application must
show, including why actions are unavailable. They do not authorize any source
or test implementation, dependency, API, migration, browser runtime, provider,
data, model, infrastructure, operational action, deployment, or remote Git.
