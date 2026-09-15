# Phase 5 Contract Gap Matrix

Status: proposed, non-effective, planning only

## Classification

| State | Meaning |
| --- | --- |
| `ready_for_generated_consumer` | Accepted route and consumer semantics are sufficient for generated-only UI planning and later bounded implementation |
| `partial` | Useful accepted data exists, but one or more consumer semantics are missing or fragmented |
| `blocked` | No accepted producer contract supports the planned capability |
| `future_operational` | A generated or control-plane contract exists, but real-world execution needs separate data, provider, media, or operational authority |

No state authorizes implementation.

## Cross-Cutting Gaps

| Capability | State | Existing foundation | Gap and required disposition |
| --- | --- | --- | --- |
| Browser authentication | `partial` | JWT principal, roles, departments, route guards | Select BFF/OIDC/session architecture; define CSRF, cookie, expiry, logout, revocation, and identity-provider failure |
| UI action capabilities | `partial` | Per-route roles, feature settings, ETags, reasons | Add typed server-returned allowed/denied action projection or derive only from accepted contract plus current server response; never client-authoritative |
| Safe problem model | `ready_for_generated_consumer` for P4.7 | Stable failure codes and RFC 9457 projection | Extend consistently to camera/stream/analytics routes without leaking raw FastAPI detail |
| Consumer compatibility | `ready_for_generated_consumer` for P4.7 | Versioned P4.7 matrix | Define support window across all earlier APIs and generated client package |
| Pagination | `partial` | Many limit/offset lists; P4.7 handoff names stronger semantics | Freeze stable sort, cursor/snapshot, page mutation, total-count, and stale-page behavior per list |
| Search | `blocked` cross-domain | Domain filters only | Define purpose-bound domain search contracts; no unrestricted universal index |
| Browser events | `blocked` | Outbox event contracts; no browser transport | Select SSE/WebSocket/polling, replay/gap/heartbeat/reconnect, department scope, and unknown-version policy |
| Saved views | `blocked` | None | Define non-sensitive local preferences and optional scoped server record; exclude query results and protected payloads |
| Localization | `blocked` | Backend timestamps/time zones | Define locale keys, Gujarati/Hindi/English resources, fallback, date/time/number formatting, and audit-safe canonical values |
| Client telemetry | `partial` | Phase 4 low-cardinality signals | Define browser signal contract and prohibited labels; no external collector selected |

## Command And GIS

| Capability | State | Existing foundation | Gap and required disposition |
| --- | --- | --- | --- |
| Operations summary | `ready_for_generated_consumer` | `GET /operations/summary` | Bind fields to command widgets and preserve partial/degraded states |
| Alert/review aggregates | `partial` | Alert lists, lifecycle, review policy | Define server-side time windows, priority inputs, backlog counts, completeness, and drill-down links |
| Camera coverage | `partial` | Camera coordinates and stream health | Define aggregate coverage and blind-spot semantics; no client-only city-wide computation |
| GIS feature query | `blocked` | Paired camera coordinates, hypothesis projections | Add bounded viewport/time/department/layer query or tile contracts |
| Base maps/tiles | `blocked` | None | Select private/offline/external source policy later; exact destinations and attribution required |
| Hotspots/heatmaps | `blocked` | Raw domain events and positions may exist | Define privacy-preserving aggregation, cell/time bounds, minimum counts, uncertainty, and no re-identification |
| 3D view | `blocked` | None | Optional later capability; 2D and list alternatives remain authoritative |
| Shift handoff | `blocked` | Domain records and timelines | Define immutable handoff snapshot, unresolved items, source freshness, acknowledgement, and correction behavior |

## Camera And Live Monitoring

| Capability | State | Existing foundation | Gap and required disposition |
| --- | --- | --- | --- |
| Camera list/detail | `ready_for_generated_consumer` | Camera CRUD/list/filter and location | Define UI-safe field projection so raw adapter-specific fields never leak |
| Stream list/detail | `partial` | Stream CRUD/list/filter | Raw locator and secret reference need explicit response minimization before browser use |
| Stream health/probes | `ready_for_generated_consumer` | Health, probe queue/history | Freeze polling/event freshness and safe reason display |
| Capability snapshots | `ready_for_generated_consumer` | Latest/history/refresh jobs | Freeze stale/completeness presentation and cooldown response mapping |
| ONVIF inspection/control | `future_operational` | Default-off imaging, event, PTZ, discovery routes | Keep unavailable in P5 baseline unless separate physical-camera/control authority and safety UX are accepted |
| Single playback session | `partial` | Short-lived playback URL/token/expiry | Define browser delivery, token handling, CSP, refresh, teardown, and safe errors |
| Multi-camera live grid | `blocked` | Single-session primitive | Define profile-based session ceiling, admission, quality, reconnect, teardown, and bandwidth accounting |
| HLS player | `blocked` as UI | Backend may provide playback URL | Select native/MSE adapter and supported codec/browser matrix |
| WebRTC/WHEP player | `blocked` as UI | Lab experience only; WHEP is draft | Version-pin provisional adapter and define ICE/privacy/reconnect/cleanup/fallback |
| Recording/snapshot/export | `blocked` | Not authorized | Keep absent; UI must not simulate or imply availability |
| Overlay alignment | `blocked` | Analytics geometry/events exist | Define frame/time/coordinate/transform/confidence contract before drawing overlays |

## Intelligence And Review

| Capability | State | Existing foundation | Gap and required disposition |
| --- | --- | --- | --- |
| Hypothesis list | `ready_for_generated_consumer` | P4.7 handoff | Add accepted filter/sort/cursor semantics before scale |
| Correlation run detail | `ready_for_generated_consumer` | P4.7 handoff | Define long-running refresh/event behavior |
| Graph projection | `partial` | Graph endpoint | Freeze node/edge bounds, truncation, expansion, layout-independent semantics, and accessible table projection |
| Spatial projection | `partial` | Hypothesis projection | Requires GIS adapter contract and coordinate/time bounds |
| Alert list/detail | `ready_for_generated_consumer` | P4.7 handoff | Extend state matrix from alerts to all views |
| Mandatory review | `ready_for_generated_consumer` | Reason, ETag, idempotency, quorum | Define draft handling, confirmation, conflict recovery, and consequence text |
| Lifecycle command | `ready_for_generated_consumer` | Reason, ETag, idempotency | Define allowed transition projection and no optimistic completion |
| Candidate set | `partial` | Generated integration APIs | Define minimized UI projection, calibration/contradiction wording, and no identity conclusion |
| Rule explanation | `partial` | Rule, version, compilation, evaluation APIs | Consolidate exact presentation schema across P3.4 and P4.2 versions |
| Operational alert/notification | `future_operational` | Proposed generated alert only | Separate provider, approval, delivery, acknowledgement, dispatch, and legal gates required |

## Investigation And Evidence

| Capability | State | Existing foundation | Gap and required disposition |
| --- | --- | --- | --- |
| Timeline list/detail | `ready_for_generated_consumer` | P4.7 handoff and P4.5 routes | Add bounded filters, stable sort, cursor, and summary fields |
| Timeline entry append | `ready_for_generated_consumer` | P4.7 command contract | Define typed forms and draft/conflict behavior |
| Reconstruction | `ready_for_generated_consumer` | Record-order/event-time views | Define virtualized and accessible display bounds |
| Corrections | `ready_for_generated_consumer` | Append-only correction command/event | Define impact traversal and visible prior/current relationship |
| Relationships | `partial` | Create relationship command | Add scoped query/list and revision-history projection |
| Reviews | `partial` | Create review command | Add consolidated query/list projection |
| Evidence list | `partial` | Per-timeline evidence list | Add bounded cross-timeline query only if purpose and scope justify it |
| Integrity/provenance | `ready_for_generated_consumer` | Typed generated records | Define graph/list presentation and unsupported-claim wording |
| Hold/retention | `future_operational` | Generated overlays/evaluations | Legal policy, accountable owner, activation, expiry, appeal, and jurisdiction remain absent |
| Deletion/export | `future_operational` | Simulation/preview only | No execution UI until policy, authorization, evidence, destination, and audit contracts exist |
| Source evidence rendering | `blocked` | References only | Separate secure resolver, media/document viewer, redaction, watermark, access, and retention authority needed |

## Admin, Security, And Operations

| Capability | State | Existing foundation | Gap and required disposition |
| --- | --- | --- | --- |
| Camera/stream admin | `partial` | CRUD and optimistic locking | Define browser-safe write schemas, confirmation, reason, audit, and raw-locator controls |
| Analytics assignment admin | `future_operational` | Generated assignment controls | Model/runtime activation remains outside Phase 5 authority |
| Rule admin | `partial` | Version, preview, validate, approve, suspend, retire | Define editor/approver separation and visual rule-builder contract |
| Provider admin | `future_operational` | Generated provider/control records | No real credentials, destinations, extensions, or providers |
| Users/roles/departments | `blocked` | Runtime principal checks only | Identity and authorization administration API required |
| Feature gates | `partial` | Settings and control revisions | Define read-only current-state projection and accepted mutation workflow |
| Operations views | `ready_for_generated_consumer` | Objectives, budgets, degradation, controls, recovery, capacity, supply chain, security | Preserve generated-only and unknown target limitations |
| Audit viewer | `blocked` | Audit persistence exists | Add minimized, scoped, immutable audit query contract and access policy |
| Security signal detail | `partial` | Generated low-cardinality signals | Define security-specific query and retention; no SIEM claim |
| Vulnerability/SBOM detail | `partial` | Evidence projections | Define current/stale/unknown scan state and artifact identity without exposing private paths |

## Required Gap-Closure Order

1. Browser authentication/session and common safe problem contract.
2. UI capability/action projection and cross-API compatibility matrix.
3. Stable list filtering, ordering, cursor/snapshot, and freshness semantics.
4. Generated-only portal shell and P4.7 intelligence consumer vertical slice.
5. Browser event delivery with polling fallback.
6. GIS viewport/feature/tile contracts.
7. Playback transport and multi-session admission contracts.
8. Command aggregates and shift handoff.
9. Investigation relationship/review/evidence query projections.
10. Admin, audit, identity, saved-view, and operational extension contracts.

## Enforcement Rule

Each future screen, panel, table, map layer, player control, and command must
name its producer operation/event, schema version, role, department scope,
freshness, bounds, failure states, and current gap classification. `blocked`
and `future_operational` capabilities remain unavailable in product code until
their exact producer and authority gates are accepted.
