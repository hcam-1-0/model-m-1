# P5.6 Administration, Security, And Operations Architecture

Status date: 2026-09-10

Status: proposed architecture; owner decisions and implementation authorization pending

## Objective

P5.6 turns the accepted shell-only Admin and Security portals and the existing
camera-oriented Operations portal into three connected enterprise workspaces.
It does not create direct control over infrastructure, credentials, cameras,
streams, providers, models, evidence, retention, deployments, or operational
authority.

The design separates four concepts that are often incorrectly combined:

- **governance:** what configuration or authority is proposed and approved;
- **security:** who attempted what, what was denied, and which controls or
  evidence are current;
- **operations:** whether services and queues are healthy, degraded, stale, or
  recovering;
- **execution:** the authoritative backend or infrastructure action, which is
  outside this subphase.

## Product Topology

```text
Command Center (primary operator entry)
|
+-- Admin Center
|   +-- Organization and departments
|   +-- Identities, roles, permissions, and policies
|   +-- Administrative change requests and approvals
|   +-- Camera, stream, integration, and provider governance
|   +-- Feature, configuration, model-lane, and profile governance
|   +-- Retention and deployment policy projections
|
+-- Security Center
|   +-- Security posture and denied-action views
|   +-- Access, privilege, department, and RLS assurance
|   +-- Audit and administrative-event references
|   +-- Session and authentication posture
|   +-- Supply-chain and dependency posture
|   +-- Compliance, exception, attestation, and evidence references
|
+-- Operations Center
    +-- Existing camera catalogue, diagnostics, live workspace, monitor wall
    +-- Platform health and service inventory
    +-- Queues, workers, retries, circuits, and dead letters
    +-- Storage, database, event bus, media edge, and AI runtime status
    +-- SLO, error budget, degradation, and recovery projections
    +-- Maintenance, backup/DR, capacity, and topology projections
```

Command Center remains the primary application. Admin, Security, and
Operations are specialist centers reached through capability-filtered
navigation and explicit handoffs. Portal visibility is not proof of resource
authorization.

## Shared Control Plane

All three centers consume one typed, server-authoritative control-plane
projection. The browser does not merge unbounded records or infer permission.

```text
Authenticated session projection
        |
        v
Department + role + purpose + capability ceiling
        |
        v
Authoritative HTTP list/detail/action contract
        |
        +-- ETag and revision
        +-- freshness and completeness
        +-- source and policy revision
        +-- allowed actions with reason codes
        +-- typed limitations and producer gaps
        |
        v
Portal domain adapter and authoritative table
```

Every action contract includes:

- subject and active session reference;
- organization and department scope;
- purpose and bounded reason where required;
- resource kind and opaque resource identifier;
- requested action and server-produced capability decision;
- policy and role revision;
- current entity revision and strong ETag;
- idempotency key for consequential commands;
- step-up or reauthentication requirement when applicable;
- separation-of-duty requirement and actor eligibility;
- outcome, resulting revision, audit reference, and safe problem detail.

## Authorization Model

### RBAC baseline

Roles group stable job responsibilities. Proposed initial roles are projections,
not production entitlements:

| Role projection | Typical read scope | Consequential capability projection |
| --- | --- | --- |
| Platform administrator | Organization, configuration, service, and governance state | Propose bounded changes; approval depends on policy |
| Department administrator | Own-department users, roles, cameras, views, and policy state | Propose department-scoped changes |
| Security auditor | Security, access, audit references, policy and supply-chain posture | Attest or review where separately permitted; no infrastructure control |
| Operations supervisor | Service, queue, degradation, recovery, and camera-operation state | Acknowledge or propose maintenance only when producer exists |
| Camera technician | Assigned camera and stream configuration/health | Propose assigned device changes; no identity or security administration |
| Compliance reviewer | Policy, exception, attestation, evidence-reference state | Review or attest; no configuration execution |
| Read-only observer | Explicitly allowed status projections | No consequential command |

No role name is privileged by itself. Effective capabilities come from the
server response for the current subject, department, purpose, resource, action,
policy revision, and state.

### Constrained ABAC context

Attributes refine but do not replace RBAC:

- active organization and department;
- assignment or resource ownership relation;
- declared purpose and reason class;
- environment class and deployment policy;
- data and action sensitivity;
- session age, authentication assurance, and step-up state;
- resource lifecycle, freshness, conflict, and incident state;
- separation-of-duty relationship;
- kill-switch, feature, provider, or degradation state.

Unknown, missing, stale, contradictory, or unsupported attributes deny the
action. Resource profile and client hardware are never authorization
attributes.

### Department isolation

Isolation requires both:

1. API/service policy that binds the authenticated department context to the
   requested resource and response projection.
2. PostgreSQL row security under a non-owner application role, with forced RLS
   where appropriate and default-deny behavior when no policy applies.

Tests must prove same-department access, cross-department denial, absent-scope
denial, role escalation denial, owner-role bypass prevention, background-worker
scope propagation, pagination isolation, aggregate isolation, and event
invalidation isolation.

## Administrative Change Lifecycle

P5.6 plans one reusable typed lifecycle for configuration and governance:

```text
Draft -> Validate -> Submitted -> Review required
     -> Approved -> Scheduled -> Effective
     -> Superseded / Revoked / Rolled back by new revision

Any state may become Rejected, Expired, Conflict, Blocked, or Failed.
```

Properties:

- append-only revisions and decisions;
- no in-place erasure of an effective revision;
- schema-specific forms, never an arbitrary JSON editor;
- exact before/after comparison;
- dependency and blast-radius preview;
- validation issues split into error, warning, unknown, and unavailable;
- proposer and approver eligibility evaluated by the server;
- self-approval denied when separation of duty applies;
- scheduled effect requires a future executor contract;
- rollback creates a new proposal referencing the previous effective revision;
- stale ETag, policy revision, or prerequisite forces reconsideration;
- event messages only invalidate; HTTP confirms authoritative state.

P5.6 implementation will use generated non-effective outcomes. It will not
apply configuration.

## Admin Center

### Page families

1. **Admin overview:** pending approvals, stale configuration, blocked
   producers, policy changes, exceptions, and recent administrative events.
2. **Organization and departments:** hierarchy, status, data-scope policy,
   service assignments, and owner references.
3. **Users and sessions:** minimized account state, role bindings, department
   membership, authentication posture, session/revocation state, and access
   review due state. No credential or personal-profile editing.
4. **Roles and permissions:** role catalogue, permission matrix, capability
   graph, static/dynamic SoD constraints, affected assignments, and revision
   comparison.
5. **Policies and approvals:** policy revisions, evaluation examples, pending
   change requests, reviewer eligibility, decision chronology, and conflicts.
6. **Cameras and streams governance:** existing camera/stream configuration,
   capability refresh policy, assignments, department, and proposal history.
   No direct camera or stream connection.
7. **Integrations and providers:** type, state, destination-policy reference,
   secret reference, last observation, revocation state, and test capability
   availability. No secret resolution or provider network test.
8. **Features and configuration:** typed flags, configuration revisions,
   dependency graph, defaults, overrides, expiry, blast radius, and kill-switch
   relationship.
9. **Resource and model lanes:** low-resource, enhanced, control-room, GPU-lab,
   server, and Kubernetes capability projections plus model-lane eligibility.
   No activation or model operation.
10. **Retention and deployment profiles:** policy references, target classes,
    unresolved decisions, previewed effects, and prerequisites. No retention,
    deployment, backup, or recovery execution.

### Prohibited Admin Center patterns

- universal super-admin bypass;
- arbitrary raw JSON or YAML editing;
- displaying, copying, validating, rotating, or resolving a secret;
- trusting a disabled button as authorization enforcement;
- client-computed role or policy decisions;
- immediate configuration mutation;
- hidden self-approval;
- action controls without reason, revision, ETag, and idempotency contracts;
- cluster, shell, SQL, ONVIF, provider, model-runtime, or camera console access.

## Security Center

### Page families

1. **Security posture:** control freshness, denied-action trends, exception
   posture, stale evidence, unresolved findings, and explicit unknowns.
2. **Access assurance:** role and capability inventory, high-risk grants,
   wildcard or broad-scope findings, dormant access, access-review state, and
   department/RLS parity evidence.
3. **Denied and suspicious activity:** bounded low-cardinality aggregates with
   drill-down to authorized security-event references. No guilt or identity
   inference.
4. **Privileged activity:** administrative proposals, approvals, conflicts,
   step-up requirements, break-glass availability, and audit references.
5. **Sessions and authentication:** identity-provider status, session age,
   revocation propagation, assurance, failed authentication aggregates, and
   reauthentication requirements. No tokens or credentials.
6. **Audit explorer:** immutable audit-reference list/detail, actor/resource/
   action/outcome chronology, hash or integrity observation, source, retention
   policy reference, and export availability state. No evidence conflation.
7. **Policy, exceptions, and attestations:** control mappings, revisions,
   exception scope/owner/expiry, reviewer decisions, attestation evidence
   references, and limitations.
8. **Supply-chain posture:** dependency inventory, SBOM identity, license
   findings, vulnerability observations, provenance, freshness, completeness,
   exceptions, and accepted release references.
9. **Integration and secret posture:** provider state, opaque secret refs,
   rotation observation, destination-control state, certificate expiry
   projection, and access review. No resolution or network verification.
10. **Future SOC handoff:** disabled typed link and event-reference contract for
    an external authorized SOC/SIEM integration; absent in this subphase.

Security Center is read-mostly. A security review or attestation is a typed
workflow with server authorization, not an infrastructure action.

## Operations Center

P5.3 camera catalogue, camera detail, stream diagnostics, live workspace, and
monitor wall stay intact. P5.6 adds a separate `Platform Operations` domain;
it does not convert camera pages into an infrastructure console.

### Page families

1. **Platform overview:** service state, data freshness, active degradation,
   queue pressure, worker availability, storage/database state, and open
   recovery limitations.
2. **Service inventory:** service, version, environment, dependency state,
   capability, last heartbeat, observation source, completeness, and owner
   reference.
3. **Queues and workers:** depth, age, leases, retries, dead letters, circuits,
   abandoned-work recovery, drain state, and capacity limits.
4. **Data and storage:** PostgreSQL/PostGIS, object storage, event bus, media
   edge, caches, indexes, and retention-policy references. No browsing of
   underlying private or media data.
5. **AI runtime:** runtime/profile/model-lane health projection, scheduler and
   saturation state, bypass/degradation reason, and capability inventory. No
   model activation, inference, download, or artifact access.
6. **SLO and error budgets:** indicators, objective policy reference,
   measurement windows, completeness, budget state, burn projection, and
   limitations. Unset targets remain visibly unset.
7. **Degradation and kill switches:** current effective projection, source
   revision, affected capabilities, dependency chain, reason, expiry,
   recovery condition, and proposal history. No direct toggle.
8. **Maintenance and recovery:** maintenance proposals, dependency checks,
   backup inventory, recovery plan/result history, RPO/RTO policy references,
   last drill, unresolved prerequisites, and non-effective preview.
9. **Capacity and profiles:** generated C1/C10/C50 evidence, declared hardware,
   workload definition, latency/throughput/backlog/saturation/recovery metrics,
   profile recommendations, and explicit non-production limitations.
10. **Topology projections:** standalone, enhanced/GPU lab, future server, and
    Kubernetes desired-state views with dependency, placement, isolation, and
    readiness gaps. No cluster connection or activation.

## Truth And State Model

Every status-bearing record includes:

| Field | Meaning |
| --- | --- |
| `state` | Typed producer assertion such as healthy, degraded, failed, stale, unknown, unavailable, or not_configured |
| `observed_at` | When the producer observed the condition |
| `recorded_at` | When H-CAM recorded the projection |
| `fresh_until` | Last instant at which the observation remains fresh |
| `source_ref` | Opaque producer or evidence reference |
| `revision` | Monotonic or immutable revision identity |
| `completeness` | Complete, partial, unknown, or not_applicable |
| `limitations` | Typed reasons the state must not be overinterpreted |
| `allowed_actions` | Server-produced actions for the current subject and state |

Color, icon, or placement alone never carries state. Unknown is not healthy;
not configured is not compliant; no recent finding is not proof of security;
integrity is not factual truth; an accepted build is not deployed software.

## Signal And Record Lanes

| Lane | Authority | Examples | Forbidden conflation |
| --- | --- | --- | --- |
| Operational signal | Runtime/observability producer | queue depth, latency, heartbeat, saturation | Not an audit or evidence record |
| Security event | Security producer | authentication failure, denial, policy anomaly | Not proof of malicious behavior |
| Audit record | Append-only audit producer | actor, action, resource, outcome, revision | Not source evidence or telemetry |
| Evidence reference | Evidence domain | source identity, provenance, integrity observation | Not operational health or guilt |
| Administrative event | Governance producer | proposal, approval, effect, supersession | Not proof execution succeeded without executor result |

Cross-lane search, if later implemented, is a bounded derived index. It must
identify the authoritative source and cannot replace source queries.

## Resource Profiles

| Profile | UI adaptation | Preserved invariants |
| --- | --- | --- |
| Low resource | fewer concurrent charts, longer refresh, smaller pages, visual layers disabled by default | all workflows, truth, tables, security, authority |
| Enhanced workstation | more panels, shorter bounded refresh, richer comparisons | same authority and query bounds |
| Control room | multi-monitor layouts, wall-safe summaries, supervisor handoffs | same data scope and action eligibility |
| GPU lab | richer local visualization where useful | no model, media, or administrative authority |
| Future server | larger server-produced result windows where policy permits | browser remains bounded and non-authoritative |
| Kubernetes | topology, placement, namespace, and policy projection | no cluster mutation or implied deployment |

Profile selection is server-bounded and may be reduced by client capability.
The client cannot select a profile to gain data, authority, or higher-risk
controls.

## Failure And Recovery UX

All list and detail views support:

- loading, empty, partial, stale, degraded, denied, conflict, failed,
  unavailable, not configured, and recovery states;
- bounded retry for safe idempotent reads only;
- no automatic retry of consequential commands;
- preserved user draft without persisting secret or prohibited fields;
- exact conflict comparison before reconsideration;
- session/department change teardown before new-scope data loads;
- inaccessible route removal plus explicit denied state for deep links;
- event gap or reconnect state followed by authoritative HTTP refresh;
- safe typed problem details with correlation reference and no raw exception.

## Accessibility And Localization

- semantic landmarks and level-consistent headings;
- native forms and tables before custom widgets;
- keyboard-complete navigation and action workflows;
- focus moves to the affected heading, error summary, conflict dialog, or
  completion state and is never obscured;
- dialogs do not trap or lose focus;
- charts, matrices, topologies, and dependency graphs have complete tables;
- state never relies on color, animation, or icon alone;
- live regions are bounded and do not announce high-frequency telemetry;
- time is shown with timezone and machine-readable value;
- identifiers and reason codes are not localized; descriptions are;
- layout supports narrow screens and multi-monitor desktops without hiding
  security-critical content or actions.

## Deployment And Runtime Boundary

This architecture deliberately describes future standalone, GPU-lab, server,
and Kubernetes projections. P5.6 planning does not:

- start or inspect a container or cluster;
- discover hardware or activate a resource profile;
- resolve telemetry, backup, storage, provider, identity, or secret backends;
- execute a kill switch, maintenance action, recovery, scan, deployment, or
  configuration mutation;
- access a camera, stream, model, dataset, artifact, media, Government data,
  private data, or real administrative record.

## Acceptance Direction

The recommended implementation remains generated-only and default-off. It
should implement complete operator workflows and explicit blocked states over
typed fixtures, while preserving every existing producer gap. Technical work
may earn at most 9/10 P5.6 points. The final point requires exact owner
acceptance of sealed evidence.
