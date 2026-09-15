# P5.2 Contract Gap Matrix

Status: planning baseline; gaps are blocked until separately implemented and accepted

## Rule

P5.2 consumes accepted producer contracts. It does not invent server truth in
the browser, reinterpret a generated contract as operational, or add backend
routes and migrations under planning authority. A UI capability remains
unavailable when its authoritative producer contract is absent or incompatible.

## Existing Inputs

| Input | Existing support | P5.2 use | Boundary |
| --- | --- | --- | --- |
| P5.1 shell and route manifest | Implemented and accepted | Command portal entry, landmarks, navigation, status regions | Client route visibility is not authorization. |
| P5.1 typed API client and problem mapper | Implemented and accepted | All future P5.2 HTTP requests | No direct `fetch`, arbitrary destination, or raw error display. |
| P5.1 query policy | Implemented and accepted | Operation-specific cache, retry, invalidation, and stale behavior | Commands are not retried; no persistent cache. |
| P5.1 capability profiles | Implemented and accepted | Low-resource, enhanced, control-room, and future-server admission | Profiles cannot change authority or truth semantics. |
| P5.1 GIS contract | Implemented and accepted | Renderer-neutral admission, viewport validation, list fallback | Feature kinds and statuses require an additive P5.2 extension. |
| P4.7 `operations.summary` | Generated-only handoff contract | Initial aggregate source | Role projection and per-source truth envelope are insufficient. |
| P4.7 alert, hypothesis, timeline, and health list/read operations | Generated-only handoff contracts | Authoritative drill-down targets | No operational data or action is authorized. |
| P4.7 invalidation events | Generated-only handoff contracts | Bounded query invalidation | Events are hints; HTTP remains authoritative. |
| Camera and stream catalogue/detail/health APIs | Existing department-scoped services | Future coverage and health drill-down | Raw locator and credential fields must never reach the browser. |
| P4.6 health and degradation contracts | Generated-only accepted contracts | Platform status and degradation projection | No real telemetry backend or production SLO is authorized. |

## Required Gaps

| Gap ID | Missing or incompatible contract | Required shape | Until resolved |
| --- | --- | --- | --- |
| `P5.2-G01` | `operations.summary` authorizes intelligence roles while the Command view expects `command.viewer` or administrator. | Server-side role policy and generated denial/isolation tests for the exact command operation. | Command summary remains unavailable; do not alias roles in the client. |
| `P5.2-G02` | No bounded viewport feature-query operation. | Department-scoped collection/layer ID, validated bbox, bounded time window, cursor, revision, freshness, completeness, generalized geometry and safe properties. | Interactive feature lane remains unavailable. |
| `P5.2-G03` | No tile-set/style manifest operation. | Versioned same-origin tile-set metadata, style hash, layer registry, zoom bounds, revision, expiry, and exact allowed resource origins. | Vector-tile lane and map renderer remain unavailable. |
| `P5.2-G04` | No authoritative command snapshot envelope. | One snapshot ID/revision/window with per-source observed/stale timestamps, completeness, loss, safe reason, aggregates, and drill-down definitions. | Separate panels must show independent source state; no overall status. |
| `P5.2-G05` | No coverage or blind-spot aggregate. | Declared denominator, spatial/time scope, source inventory revision, coverage method, unknown set, completeness and limitations. | Do not infer coverage from visible camera markers. |
| `P5.2-G06` | No cross-domain workload aggregate. | Server-provided bounded counts and safe priority bands for alerts, mandatory review, investigations, camera health, stream health, and degradation. | Use separate authoritative lists; no client risk score or combined priority. |
| `P5.2-G07` | No typed shift-handoff contract. | Versioned read/write model, owner, department, revision/ETag, chronology, correction, retention, and authorization. | Show no handoff editor or persistence claim. |
| `P5.2-G08` | GIS feature kinds are limited to camera, incident, and resource; status is limited to available, unavailable, and unknown. | Additive discriminated feature summaries for accepted alert, investigation, coverage, health, cluster and degradation projections with safe shared fields. | Unsupported kinds stay in lists or are omitted with an explicit reason. |
| `P5.2-G09` | No versioned layer registry. | Stable layer metadata, role, feature kind, geometry, source operation, legend, freshness, clustering, detail target and fallback. | Layer controls remain generated placeholders only. |
| `P5.2-G10` | No correction/retraction and temporal projection for map features. | Event/recorded time, revision, corrected/retracted state, supersession reference and bounded query-window semantics. | Map cannot claim current chronology for corrected records. |
| `P5.2-G11` | No canonical selection/drill-down target. | Opaque feature reference plus exact authoritative list/detail operation and parameters, without protected fields in the URL. | Selection may remain local generated state only. |
| `P5.2-G12` | No saved command-workspace operation. | Department-scoped opaque workspace ID, bounded non-sensitive filters, viewport, panel layout, revision/ETag, ownership and expiry. | No persistent layouts; memory-only generated state. |
| `P5.2-G13` | No camera/stream aggregate invalidation event. | Low-cardinality scope hint and revision only, with HTTP refetch as authority. | Use bounded polling policy for these projections. |
| `P5.2-G14` | No production map capacity or payload budget evidence. | Declared C1/C10/C50 generated tests for features, tiles, pages, invalidation bursts, memory and interaction latency by profile. | No operational scale or performance claim. |

## Producer Ownership Proposal

| Producer area | Candidate owner | Consumer |
| --- | --- | --- |
| Command summary, workload, coverage and blind-spot projections | Phase 4 operations/intelligence API | Command overview and workload rail |
| Viewport features, tile-set metadata and layer registry | GIS/query service using accepted PostGIS boundaries | GIS adapter and accessible list |
| Camera and stream aggregate health | Camera/stream platform | Coverage and health panels |
| Workspace persistence and handoff | Phase 5 backend contract slice | Command shell and shift workflow |
| Invalidation revisions | Existing outbox/event projection | P5.1 event invalidation client |

These ownership labels are planning proposals, not assignments or implementation authority.

## Consumer Acceptance Rules

- No P5.2 panel leaves generated-fixture mode until its producer operation is
  versioned, authorized, department-isolated, and accepted.
- Every list and detail link identifies an exact operation from the accepted
  contract catalogue.
- Unknown fields fail according to the accepted compatibility policy.
- A map feature is a summary reference, not an evidence record or identity
  conclusion.
- Events may reduce refetch delay but cannot substitute for an HTTP revision.
- Denied, partial, stale, unknown, and degraded are data states, not generic
  exceptions and not interchangeable.
- No browser fallback computes an operational conclusion from incomplete data.

## Required Generated Contract Vectors

The later bounded start package should include, at minimum:

- valid and hostile bbox, antimeridian, zoom, time-window, cursor, layer and
  property bounds;
- cross-department and cross-role denial;
- missing, partial, stale, degraded, corrected, retracted and conflicting
  source revisions;
- oversized feature/tile/list payload rejection;
- invalid drill-down and protected URL-field rejection;
- out-of-order and duplicate invalidation events;
- renderer failure with complete list fallback;
- exact role mismatch evidence for `P5.2-G01` until the producer is repaired.
