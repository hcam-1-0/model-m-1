# P5.6 Owner Decision Packet

Status date: 2026-09-10

Status: twelve owner decisions pending; no option authorizes implementation

Record selections as `D-P5.6-001:A` through `D-P5.6-012:A` or another explicit
option. The recommended `A` profile provides broad enterprise capability while
preserving the accepted generated-only and non-operative boundaries.

## D-P5.6-001: Portal Ownership And Topology

### A. Three connected specialist centers, recommended

Command Center remains primary. Admin Center owns governance and change
workflows. Security Center owns security, access, audit-reference, compliance,
and supply-chain posture. Operations Center preserves P5.3 camera/live pages
and adds a separate Platform Operations domain. Shared packages prevent
duplication without weakening responsibility or access boundaries.

### B. One combined Administration portal

Fewer routes and builds, but administrative mutations, security review, and
runtime operations become easy to confuse and over-authorize.

### C. Make Admin Center the primary dashboard

Useful for platform teams but contradicts the accepted operator hierarchy in
which Command Center is primary.

### D. Put everything into shared shell tabs

Visually compact, but produces an overloaded application and makes portal,
domain, authorization, and failure boundaries harder to verify.

## D-P5.6-002: Authorization Model

### A. Server-authoritative RBAC plus constrained ABAC and default deny, recommended

Roles establish stable job capability; organization, department, purpose,
resource, state, session assurance, policy revision, and SoD refine each
decision. Unknown, missing, stale, or contradictory context denies. PostgreSQL
RLS must independently enforce data scope.

### B. RBAC only

Simpler but insufficient for department, purpose, object state, step-up,
assignment, and SoD conditions.

### C. ABAC/policy engine only

Flexible but harder for operators to understand, review, and administer; it
also introduces a major backend/deployment dependency.

### D. Client-side capability evaluation

Responsive but unacceptable as an authorization boundary. The browser is not
a trusted policy enforcement point.

## D-P5.6-003: Administrative Change Lifecycle

### A. Typed draft, validation, approval, schedule, effect, supersession, recommended

Use schema-specific proposals, exact revisions, before/after comparison,
dependency and blast-radius checks, strong ETags, idempotency, typed approval,
SoD, scheduled effect, executor result, and append-only rollback-by-new-revision.
P5.6 implements generated non-effective states only.

### B. Immediate authorized mutation

Fast for administrators but lacks review, impact, rollback, conflict, and
separation-of-duty safeguards.

### C. GitOps-only changes

Strong review and version history for infrastructure, but unsuitable as the
only interface for identities, sessions, department assignments, and urgent
bounded controls.

### D. Ticket-only workflow

Preserves manual governance but loses typed validation, exact entity revision,
machine-readable effects, and product-integrated status.

## D-P5.6-004: Privileged And Break-Glass Access

### A. Design the contract but keep it unavailable, recommended

Show why break-glass is unavailable and define future strong authentication,
reason, scope, expiry, alerting, immutable audit, approval exception, and
after-action review requirements. No bypass exists in P5.6.

### B. Generated break-glass simulation

Allows richer workflow testing but risks being mistaken for accepted
privileged authority. It must remain visibly non-effective.

### C. Administrator override

Operationally convenient but creates an unacceptable universal-bypass risk
without independent identity, policy, audit, monitoring, and deployment
controls.

### D. Omit break-glass entirely

Reduces scope but leaves a critical future operational requirement undefined.

## D-P5.6-005: Security, Audit, Evidence, And Search Lanes

### A. Separate authoritative lanes with bounded references, recommended

Operational signals, security events, audit records, evidence references, and
administrative events keep distinct schemas, stores, authorization, retention,
and meaning. Trace/correlation refs link them. A future combined index remains
derived and must confirm source records.

### B. One universal log and search store

Powerful but conflates authority and retention, increases exposure, and can
silently lose source-specific semantics.

### C. Security-only combined search

Useful for analysts, but still risks treating telemetry or audit material as
the same evidence type.

### D. External SIEM as the only interface

Reduces H-CAM work but creates provider, authorization, data replication, and
availability dependencies and weakens in-product source traceability.

## D-P5.6-006: Operations Health, SLO, And Degradation

### A. Reuse P4.6 projections with explicit unknown and unset states, recommended

Present service health, queues, objectives, budgets, degradation, controls,
recovery, capacity, and supply-chain records using source, freshness,
completeness, policy revision, and limitations. Generated C1/C10/C50 evidence
never becomes a production target or claim.

### B. Connect directly to live telemetry backends

Would provide current data but introduces network, credentials, vendor schemas,
high-cardinality exposure, deployment, and runtime work outside P5.6.

### C. Static green/yellow/red service board

Simple but hides source, age, coverage, data quality, dependency state, and
unknown conditions.

### D. Use an external observability console only

Mature visualization, but fragments operator workflow and bypasses H-CAM
department, capability, minimization, and truth contracts.

## D-P5.6-007: Secret And Provider Governance

### A. Opaque references and metadata only, recommended

Show provider type/state, exact destination-policy ref, `secret_ref`, rotation
observation, certificate metadata, revocation, freshness, and access-review
state. Do not reveal, resolve, copy, test, validate, rotate, or transmit a
secret in the browser.

### B. Show masked last characters

Can help operators distinguish secrets but unnecessarily exposes correlation
material and implies the browser handled the value.

### C. Allow browser secret entry

Common in admin consoles but expands memory, logging, clipboard, extension,
telemetry, and error leakage risks; it needs a separately designed secret
enrollment path.

### D. Link directly to an external vault console

Avoids handling values, but creates cross-origin navigation, identity, scope,
and audit ambiguity and does not solve H-CAM governance.

## D-P5.6-008: Features, Configuration, Profiles, And Kill Switches

### A. Typed revisioned proposals with dependency and impact projection, recommended

Use typed values, defaults, overrides, scope, provider/evaluation reason,
revision, expiry, dependency graph, impact preview, kill-switch relationship,
approval, and authoritative effective state. No generic editor or direct
toggle.

### B. Generic JSON/YAML editor

Flexible but unsafe, inaccessible, difficult to validate, and vulnerable to
mass assignment and unsupported field behavior.

### C. Feature flags only

Useful but does not cover configuration schemas, resource/model lanes,
providers, kill switches, or deployment profiles.

### D. Environment files and restart

Familiar for developers but weak for enterprise governance, auditability,
department scope, approval, and dynamic state.

## D-P5.6-009: Retention, Recovery, And Compliance

### A. Non-operative policy previews and evidence checklists, recommended

Display policy/jurisdiction refs, unresolved applicability, declared targets,
evidence, exceptions, expiry, drill history, generated effects, residuals,
limitations, and prerequisites. Do not choose periods, activate holds, delete,
export, back up, restore, fail over, or claim compliance.

### B. Editable production RPO/RTO and retention targets

Operationally useful but requires owner, legal, records, infrastructure, and
production authority not present here.

### C. Built-in legal-policy defaults

Fast, but legislation and applicability cannot be safely reduced to universal
product defaults.

### D. External governance/risk/compliance tool only

May be appropriate later but adds integration and makes H-CAM control-to-
evidence traceability dependent on another system.

## D-P5.6-010: Supply-Chain Assurance

### A. Read-only SBOM, license, vulnerability, and provenance projections, recommended

Bind exact release, subject, digest, source, observation time, freshness,
coverage, applicability, exception, verification, and limitations. Preserve
stale, unknown, partial, not-run, and not-applicable states. Make no SLSA,
CycloneDX, license, or security claim beyond evidence.

### B. Vulnerability dashboard only

Useful but omits component completeness, licenses, services, provenance,
accepted baseline, and release identity.

### C. Live scanning from the UI

Would improve freshness but requires scanner execution, artifacts, network,
credentials, resource controls, and security isolation outside the phase.

### D. External links only

Low implementation cost but loses bounded in-product context, evidence age,
scope, and department-aware access.

## D-P5.6-011: Resource And Deployment Profiles

### A. Shared dynamic profiles with non-effective topology projections, recommended

Preserve low-resource functional completeness and enhanced/control-room/GPU-
lab/server/Kubernetes scaling. Profiles may change density, refresh, page size,
and optional visuals, never authority, data scope, truth, action eligibility,
or security policy. No activation occurs.

### B. Laptop-only UI

Simplest now but conflicts with the platform-wide hardware-dynamic architecture
and creates future rework.

### C. Kubernetes-first administration

Aligns with future scale but overfits an unavailable deployment and weakens
standalone and lab usability.

### D. Automatic profile and deployment activation

Convenient but requires hardware discovery, infrastructure authority, rollback,
and production validation that P5.6 explicitly lacks.

## D-P5.6-012: Dependency, Accessibility, Security, And Validation Baseline

### A. Existing locked dependencies and layered generated validation, recommended

Use exactly 1,120 generated contract cases, C1/C10/C50 workloads, unit and
component tests, all-portal builds, loopback browser tests, keyboard/focus/
reflow/accessibility checks, route/scope/concurrency/redaction/overclaim tests,
profile equivalence, immutable dependency/SBOM verification, and complete
repository regression. Reserve one P5.6 point for exact owner acceptance.

### B. Add policy, graph, chart, identity, and operations SDKs now

Enables richer integrations but materially expands supply chain and runtime
scope before authoritative producers exist.

### C. Unit tests and manual review only

Too narrow for portal isolation, cross-department denial, SoD, concurrency,
focus, degraded states, redaction, signal separation, and dynamic profiles.

### D. Validate against real users, infrastructure, secrets, and telemetry

Potentially realistic but prohibited, high risk, and premature for the
generated-only contract milestone.

## Recommended Selection Statement

```text
D-P5.6-001: A
D-P5.6-002: A
D-P5.6-003: A
D-P5.6-004: A
D-P5.6-005: A
D-P5.6-006: A
D-P5.6-007: A
D-P5.6-008: A
D-P5.6-009: A
D-P5.6-010: A
D-P5.6-011: A
D-P5.6-012: A
```

This statement records architecture choices only. It does not authorize source
or test implementation, dependencies, routes, migrations, browser/runtime,
secrets, administrative mutations, providers, cameras/media, data, models,
operational actions, containers, Kubernetes, deployment, P5.7, or remote Git.
