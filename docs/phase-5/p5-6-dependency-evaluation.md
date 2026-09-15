# P5.6 Dependency Evaluation

Status date: 2026-09-10

Status: existing locked dependency baseline recommended; no dependency action authorized

## Decision

The recommended initial P5.6 implementation needs no new frontend or Python
runtime dependency. The accepted Phase 5 workspace already provides React,
TypeScript, TanStack Query/Router, Zod, Lucide icons, shared design-system
components, application shell, auth/session projection, capability projection,
query policy, observability contracts, and generated fixture patterns.

This decision minimizes supply-chain change while still supporting complete
Admin, Security, and Operations operator workflows.

## Existing Capability Mapping

| Need | Existing capability | Initial decision |
| --- | --- | --- |
| Routing and portal separation | Accepted shared shell/router and independent portal builds | Reuse |
| Server-state queries and invalidation | Accepted query package and TanStack Query | Reuse |
| Contract validation | Zod and accepted typed packages | Reuse |
| Tables, forms, tabs, dialogs, status, pagination | Shared UI/design-system primitives | Reuse and extend only within future bounded start scope |
| Icons | Existing Lucide dependency | Reuse |
| Authorization projection | Shared auth-session and capabilities packages | Reuse; never make authoritative |
| Errors and conflicts | Shared typed problem and query policies | Reuse |
| Signals | Shared low-cardinality observability package | Reuse; adapters remain default-off |
| Graph/topology views | Existing internal bounded graph adapters and table alternatives | Reuse; no new graph library required |
| Charts | CSS/SVG-free semantic summaries or existing primitives with authoritative tables | Avoid dependency; rich charts optional later |
| JSON/schema editing | Not required and intentionally prohibited | Do not add editor dependency |
| Policy evaluation | Backend producer gap | Do not add browser policy engine |
| Secret handling | Backend provider gap | Do not add vault SDK or secret client |
| Telemetry backend | P4.6 default-off adapters | Do not add collector/vendor SDK |
| Kubernetes | Future deployment projection only | Do not add Kubernetes client |

## Evaluated Optional Dependencies

### Policy engines: OPA/Rego or Cedar

Potential future value:

- centralized fine-grained policy evaluation;
- explicit contextual authorization;
- policy testing, revisioning, and explanation;
- consistency across services.

Why not add in initial P5.6:

- authorization must be a backend enforcement concern, not a browser feature;
- bundle distribution, policy trust, versioning, availability, and fail-closed
  behavior require a separate architecture and deployment decision;
- adding a policy engine does not solve identity, RLS, approval, or audit by
  itself;
- current P5.6 work is generated-only and has no operational policy producer.

Recommendation: preserve a typed `PolicyDecisionProvider` backend boundary for
future evaluation. Do not add OPA, Cedar, Wasm, sidecar, or client package now.

### Feature control: OpenFeature SDK

Potential future value:

- vendor-neutral typed flag evaluation API;
- evaluation context, hooks, events, reasons, and provider state;
- consistent telemetry conventions.

Why not add now:

- P5.6 only needs generated read and proposal projections;
- frontend evaluation could be mistaken for authorization;
- no accepted feature-control provider exists;
- the typed contract can follow OpenFeature concepts without claiming
  conformance or installing an SDK.

Recommendation: model flag key, type, default, value, variant, reason,
provider state, context identity, revision, and freshness. Evaluate later
whether the backend adapter should implement OpenFeature.

### Table virtualization

Potential future value: lower DOM cost for very large local collections.

Why not add now:

- authoritative server cursor pagination remains required;
- admin/security tables are bounded and semantically dense;
- virtualization adds focus, row measurement, reading-order, and browser-test
  complexity;
- low-resource mode can reduce page size without removing information.

Recommendation: keep a future list-window adapter boundary. Add a dependency
only when measured browser evidence shows pagination is insufficient.

### Charting and topology libraries

Potential future value: richer SLO, queue, capacity, policy, service, and
supply-chain visualizations.

Why not add now:

- existing tables and bounded internal adapters are sufficient for truth and
  accessibility;
- a chart library can increase bundle, canvas/SVG complexity, accessibility,
  and supply-chain risk;
- P5.6 cannot consume real high-volume telemetry.

Recommendation: implement authoritative tables and small bounded visual
summaries first. Evaluate a library in P5.7 only against measured accessibility,
bundle, performance, and maintenance criteria.

### Identity, vault, SIEM, telemetry, scanner, backup, and Kubernetes SDKs

These are explicitly rejected for initial P5.6. Each would cross an external
or runtime trust boundary that planning does not authorize. UI contracts must
use same-origin backend projections and opaque references, not direct vendor
clients.

## Supply-Chain Gates For Any Future Addition

A new dependency requires a separate exact decision and must record:

- exact package, version, registry, integrity, and lockfile change;
- license and transitive dependency review;
- SBOM change and completeness;
- vulnerability observation source and time;
- provenance/signature information where available without overclaim;
- maintenance activity, release cadence, browser/runtime support, and bundle
  impact;
- threat-model and accessibility impact;
- offline/cache behavior and reproducible build evidence;
- rollback plan and an implementation boundary that does not widen authority.

## Recommended Validation Baseline

Future bounded implementation should use existing locked tools for:

- TypeScript type checking and package builds;
- deterministic generated contract validation;
- component and route tests;
- browser validation on loopback only;
- keyboard, focus, reflow, and authoritative-table checks;
- contract hostile-input and redaction tests;
- cross-profile semantic and authority equivalence;
- dependency, lockfile, SBOM, and changed-path identity checks;
- complete repository regression.

No dependency resolution, download, install, update, lockfile mutation, or
package-manager action is authorized by this planning record.
