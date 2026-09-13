# Phase 5 Repository And Handoff Inventory

Status date: 2026-09-06

Status: read-only inventory; planning only

## Baseline Identity

| Item | Value |
| --- | --- |
| Planning base | `96a902315e78c184e92df9ebe5bcef1e336eab38` |
| Phase 4 technical commit | `6ad9ff4b06b5f5516e5b346408807a70fe6466a0` |
| Phase 4 acceptance commit | `96a902315e78c184e92df9ebe5bcef1e336eab38` |
| P4.7 evidence package SHA-256 | `B739251D7D86A265DE60BA9B9943A1D0002B515C68AA1297D8B1378ADF1C8FBC` |
| P4.7 canonical component digest | `75D0A3B7667C25BF8B5180639F5B8F3937A734FAA2B2BB63CB9FE9914182A875` |
| Phase 5 handoff component digest recorded by P4.7 | `4A733C481A8491CC33ED6EE31B4BE4089663E9D506D4A2C51E0DE93D79EFD2A8` |
| Migration head | `0018_operations_security_scale` |
| Backend | Python 3.12+, FastAPI, SQLAlchemy, Alembic |
| Frontend implementation | None present |

The accepted P4.7 handoff explicitly reports `phase5_authorized=false` and
`phase5_implemented=false`. The later `D-P5.0-PLAN-AUTH` opens planning only;
it does not alter either implementation fact.

## Canonical P4.7 HTTP Handoff

All listed operations require department scope. GET operations return ETags.
The four command operations require a reason, `If-Match`, and idempotency.
All examples and current implementations remain generated-only under their
accepted Phase 4 gates.

| Operation | Method and path | Roles | Key semantics |
| --- | --- | --- | --- |
| `intelligence.health.read` | `GET /intelligence-health` | viewer, reviewer | Fresh/stale/unknown; success, empty, or partial |
| `hypotheses.list` | `GET /correlation-hypotheses` | viewer, reviewer | Bounded list and current hypothesis state |
| `runs.list` | `GET /correlation-runs` | viewer, reviewer | Bounded correlation-run list |
| `runs.detail` | `GET /correlation-runs/{run_id}` | viewer, reviewer | Current run detail |
| `alerts.list` | `GET /generated-alerts` | viewer, reviewer | Proposed generated-alert list |
| `alerts.detail` | `GET /generated-alerts/{alert_id}` | viewer, reviewer | Alert aggregate and current revision |
| `alerts.review` | `POST /generated-alerts/{alert_id}/reviews` | reviewer | Reason, ETag, idempotency, accepted/conflict |
| `alerts.lifecycle` | `POST /generated-alerts/{alert_id}/lifecycle` | reviewer | Reason, ETag, idempotency, accepted/conflict |
| `reference.health` | `GET /reference-integrations/health` | viewer, reviewer | Generated provider subsystem state |
| `reference.queries.detail` | `GET /reference-integrations/queries/{job_id}` | viewer, reviewer | Generated query lifecycle and uncertainty |
| `timelines.list` | `GET /timelines` | viewer, reviewer | Bounded investigation timeline list |
| `timelines.detail` | `GET /timelines/{timeline_id}` | viewer, reviewer | Current timeline revision |
| `timelines.reconstruction` | `GET /timelines/{timeline_id}/reconstruction` | viewer, reviewer | Record-order or event-time reconstruction |
| `timelines.entries.create` | `POST /timelines/{timeline_id}/entries` | reviewer | Reason, ETag, idempotency, accepted/conflict |
| `timelines.corrections.create` | `POST /timelines/{timeline_id}/corrections` | reviewer | Reason, ETag, idempotency, accepted/conflict |
| `operations.summary` | `GET /operations/summary` | viewer, reviewer | Generated operations overview and degradation |

Common safe failure codes are `authorization.denied`, `resource.not_found`,
`request.invalid`, and `service.unavailable`. The UI must not replace these
with raw exceptions or infer a retry without operation-specific policy.

## Canonical P4.7 Event Handoff

| Event | Consumer intent | Ordering |
| --- | --- | --- |
| `hcam.correlation.hypothesis.changed.v1` | Refresh hypothesis views | Aggregate |
| `hcam.intelligence.alert.changed.v1` | Refresh alert views | Aggregate |
| `hcam.intelligence.review.recorded.v1` | Refresh review state | Aggregate |
| `hcam.investigation.timeline.changed.v1` | Refresh timeline views | Aggregate |
| `hcam.investigation.correction.recorded.v1` | Show correction state | Aggregate |
| `hcam.operations.degradation.changed.v1` | Show degradation state | Aggregate |

Every event is delivered through the accepted transactional-outbox semantic,
supports correction where declared, grants no authority, and quarantines an
unknown version. No event broker or browser transport is selected.

The two handed-off workflows are:

- `phase5.review_and_investigate`: load alert, submit mandatory review, load
  timeline, then reconstruct;
- `phase5.observe_degradation`: load the operations summary and preserve a
  partial state when a supporting service is unavailable.

## Canonical UI State Handoff

P4.7 defines eleven states for the alert view: `loading`, `empty`, `partial`,
`stale`, `degraded`, `denied`, `conflict`, `failure`, `recovery`, `correction`,
and `success`. Every state includes source fact, visible message,
announcement mode, focus rule, non-color indicator requirement, and available
actions.

The nine accessibility requirement categories are keyboard, focus,
name/role/value, status, error, non-color meaning, target size, contrast, and
motion. Target, contrast, and motion remain future manual evidence; no
accessibility conformance was accepted in Phase 4.

## Earlier Accepted Backend Surfaces

The following surfaces exist in source and can inform Phase 5 planning. Their
runtime availability still depends on accepted settings, authentication,
department scope, environment, and feature gates.

### Camera Registry

- list, create, detail, and optimistic update;
- source, external identifier, display name, department, ownership, type,
  location label, timezone, paired latitude/longitude, state, stream summary,
  provenance, and timestamps;
- bounded filtering and pagination;
- normalized imports through a separate adapter boundary.

### Stream Management

- stream list, create, detail, and optimistic update;
- health and probe history;
- queued probes;
- synchronous and asynchronous capability discovery with snapshot history;
- bounded ONVIF imaging inspection, event pull, PTZ command, and discovery
  routes under their separate default-off safety controls;
- playback-session creation with short-lived bearer material and expiry;
- an internal playback verification key endpoint.

Planning must not interpret route presence as authorization to expose ONVIF
control, discovery, media, or raw locators in Phase 5.

### Analytics And Spatial

- analytics assignments, revisions, activation and pause commands;
- generated analytics and tracking runs, observations, epochs, tracks, and
  lifecycle history;
- spatial geometries, geometry rules, compile preview, approval, generated
  geometry runs, and generated events.

Current analytics execution surfaces are generated-only. Phase 5 may plan
administrative and explanatory views but cannot expose them as operational
model execution.

### Intelligence And Rules

- intelligence health;
- rule list/detail/version, compile preview, validation, approval, shadow
  eligibility, suspend, retire, evaluation, and comparison;
- hypotheses, correlation runs, graph, projection, and revisions;
- alert lists and investigation-timeline list projections.

### Alert Lifecycle

- generated-alert list and detail;
- mandatory review and lifecycle transition;
- review policy and lifecycle history.

### Reference Integrations

- generated integration health;
- provider manifests and lists;
- generated query submit/detail/cancel;
- candidate sets;
- control revisions and kill-switch projections.

No real provider, credential, network connection, Government database, or
identity conclusion is available or authorized.

### Investigations And Evidence

- timeline create/list/detail, entry append, reconstruction, and lifecycle;
- evidence references, integrity assessments, provenance bundles,
  corrections, reviews, and relationships;
- generated hold overlays, retention evaluations, deletion simulations, and
  export previews.

These are reference and simulation surfaces. They do not authorize source
resolution, media copying, legal policy, hold activation, deletion, or export.

### Operations And Security

- operations summary;
- bounded views for objectives, budgets, degradation, controls, recovery,
  capacity, supply chain, and security;
- low-cardinality generated signal, worker resilience, and platform topology
  contracts.

No external telemetry, search, security, broker, backup, recovery, hardware,
container, Kubernetes, or deployment backend is selected or active.

## Frontend Baseline Findings

- No `package.json`, JavaScript lockfile, TypeScript, JSX, Vue, Svelte, or HTML
  application exists in the accepted Phase 4 tree.
- The repository is currently a Python package with FastAPI as its API
  boundary.
- There is no accepted browser authentication flow, design system, frontend
  routing, client state, browser event transport, map renderer, media player,
  localization framework, or frontend observability adapter.
- P4.7 projections are consumer contracts, not generated SDKs or UI code.

## Initial Contract Gaps

| Need | Current state | Required before UI reliance |
| --- | --- | --- |
| Unified authenticated browser session | Backend JWT roles exist; browser flow not selected | BFF/OIDC/session contract, CSRF/logout/session-expiry behavior, exact security headers |
| Capability/action discovery | Roles and settings exist; no unified per-resource UI-capability contract | Typed allowed/denied action projection that never replaces server enforcement |
| Cursor/snapshot pagination | Several routes use limit/offset; P4.7 describes stronger semantics | Freeze per-surface pagination, stable sort, snapshot, and freshness behavior |
| Browser event delivery | Domain outbox events exist; no broker or browser transport selected | SSE/WebSocket/polling contract with replay, gap, reconnect, and unknown-version policy |
| Command-center aggregates | Operations and domain lists exist; no bounded overview API | Define server-side aggregate semantics, windows, completeness, and drill-down links |
| GIS viewport queries | Camera coordinates exist; no viewport/tile API | Define bounds/time/layer query contract and result ceiling before city-scale map |
| Multi-camera playback | Single playback-session route exists | Define per-profile concurrency, session refresh, teardown, quality, and failure contract |
| Investigation search | Timeline list/detail exist; cross-domain search is not accepted | Define bounded, purpose-aware search without creating an unrestricted index |
| Audit viewer | Audit records exist internally; no accepted operator query contract inventoried | Define read-only scoped audit projection and redaction policy |
| User/role/department admin | Authentication roles exist; management APIs are not accepted here | Keep portal placeholder blocked until explicit backend contracts exist |
| Saved views/workspaces | No accepted persistence contract | Decide local non-sensitive preferences versus server-scoped saved-view records |
| Localization | No frontend exists | Define message keys, fallback, date/time/number rules, and evidence |

The detailed disposition is maintained in `contract-gap-matrix.md`.

## Inventory Conclusion

The backend foundation is broad enough to plan the operator application, but
it is not sufficient to implement every proposed portal without contract work.
Phase 5 must begin with a generated-only consumer foundation and explicit gap
closure. It must not let a frontend mock, direct database read, raw event, or
camera URL stand in for an accepted producer contract.
