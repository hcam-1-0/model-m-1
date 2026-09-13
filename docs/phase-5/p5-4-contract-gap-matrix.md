# P5.4 Contract Gap Matrix

Status: planning inventory; gaps are not implementation authorization

## Classification

- `Stable handoff`: included in the accepted P4.7 Phase 5 handoff.
- `Existing producer`: an accepted backend surface exists, but the exact P5.4
  browser projection is not frozen by the P4.7 handoff.
- `Consumer design`: P5.4 can implement generated-only behavior against a
  local typed fixture after a start authorization.
- `Producer gap`: a safe production consumer requires later backend work.
- `Operationally blocked`: real data, provider, action, or deployment remains
  outside current authority.

Existing producer code is not automatically a stable browser contract. P5.4
must not bind a UI directly to internal persistence models or infer missing
authority from an available route.

## Accepted Stable Handoff

| Operation/event | P5.4 use | Boundary |
| --- | --- | --- |
| `GET /intelligence-health` | Intelligence health and degraded state | Low-cardinality sanitized projection only |
| `GET /correlation-hypotheses` | Hypothesis queue | Department-scoped cursor pagination |
| `GET /correlation-runs` | Correlation-run queue | Department-scoped cursor pagination |
| `GET /correlation-runs/{run_id}` | Run detail | Response ETag and typed not-found/denied behavior |
| `GET /generated-alerts` | Proposed-alert queue | Proposed objects, not operational alerts |
| `GET /generated-alerts/{alert_id}` | Proposed-alert detail | Current lifecycle and response ETag |
| `POST /generated-alerts/{alert_id}/reviews` | Append review | Reviewer role, reason, idempotency, and `If-Match` |
| `POST /generated-alerts/{alert_id}/lifecycle` | Allowed lifecycle transition | Same concurrency and audit boundaries |
| `GET /reference-integrations/health` | Provider subsystem health | No provider destination or credential detail |
| `GET /reference-integrations/queries/{job_id}` | Generated query status | Purpose and field-minimized projection |
| `hcam.correlation.hypothesis.changed.v1` | Queue/detail invalidation | Hint only; HTTP confirms authority and state |
| `hcam.intelligence.alert.changed.v1` | Alert invalidation | Hint only; unknown version quarantined |
| `hcam.intelligence.review.recorded.v1` | Review/quorum invalidation | Never applies review authority from event data |

## Producer And Consumer Gaps

| ID | Gap | Current evidence | Required safe closure | P5.4 treatment |
| --- | --- | --- | --- | --- |
| P5.4-G01 | Hypothesis queue filter and sort vocabulary is not frozen in P4.7 | Stable list route exists | Typed allowlisted filters, stable ordering, cursor semantics, max page size | Generated fixture and blocked producer marker |
| P5.4-G02 | Hypothesis detail is not in the stable P4.7 HTTP handoff | Existing intelligence routes expose richer surfaces | Field-minimized detail DTO with ETag, provenance, revision, freshness, and completeness | Generated detail contract only |
| P5.4-G03 | Hypothesis revision history consumer contract is not handed off | Existing revision producer surface is present | Cursor history with immutable revision refs and correction lineage | Generated history projection |
| P5.4-G04 | Relationship graph bounds are not frozen | Existing graph endpoint is available | Max nodes/edges/depth/window, omitted counts, truncation, stable node/edge schemas | Hard-coded generated bounds and fail closed |
| P5.4-G05 | Authoritative graph table projection is not explicit | Graph response is visualizable | Node and edge tables with identical refs, labels, provenance, direction, and selection | Consumer-generated projection only from accepted fixture |
| P5.4-G06 | Spatial projection contract is not in P4.7 handoff | Existing projection route and P5.2 GIS domain exist | GeoJSON type, WGS 84, precision, bounds, time, freshness, omitted count | Generated spatial projection and GIS handoff |
| P5.4-G07 | Correlation-run progress, partial-state, and attempt lineage are incomplete for UI | Stable list/detail routes exist | Typed run state, accepted input manifest summary, attempt and supersession refs | Present unknown fields as unavailable; no inference |
| P5.4-G08 | Correlation-run cancellation or retry authority is not handed off | No stable P5 action | Exact capability and command contract if ever added | No controls in P5.4 baseline |
| P5.4-G09 | Rule catalogue and detail are not in P4.7 handoff | Existing rule routes expose create/list/detail/version surfaces | Read-only field-minimized list/detail with lifecycle and revision ETags | Generated read-only contract |
| P5.4-G10 | Rule evaluation explanation projection is not handed off | Existing evaluation and compilation data exist | Exact typed node trace, normalized inputs, timer/window result, limits, abstention | Generated explanation contract |
| P5.4-G11 | Rule authoring and lifecycle mutations are outside P5.4 | Backend has rule mutation routes | Future admin/authoring authority and separate phase decision | Read-only only; no controls |
| P5.4-G12 | Proposed-alert queue filters and stable procedural priority are not frozen | Stable alert list exists | Type-safe filters, deterministic ordering, no score-to-priority conversion | Generated queue policy |
| P5.4-G13 | Alert detail must expose semantic identity separately from delivery identity | Phase 4 contract defines both | Browser DTO and labels that cannot collapse the two IDs | Generated distinction assertions |
| P5.4-G14 | Review-policy read operation is not in P4.7 stable handoff | Existing review-policy route exists | Current policy DTO with ETag, independent slots, allowed decisions/reasons, expiry | Generated policy projection; submission blocked if absent |
| P5.4-G15 | Lifecycle history operation is not in P4.7 stable handoff | Existing lifecycle-history route exists | Cursor chronology with actor class, reason, revision, receipt, correction refs | Generated chronology projection |
| P5.4-G16 | Review history and quorum contribution projection are not frozen | Review records exist in Phase 4 | Attributable minimized entries, independent-slot state, no duplicate actor leakage | Generated review history |
| P5.4-G17 | Allowed lifecycle transitions are not a stable read contract | Mutation endpoint exists | Server-provided allowed commands and reason vocabulary per ETag/capability | UI shows no action when projection absent |
| P5.4-G18 | Candidate-set detail is not in P4.7 stable handoff | Existing integration route exists | Field-level support/contradiction/ambiguity/missingness/calibration DTO | Generated-only candidate matrix |
| P5.4-G19 | Reference query queue/list is absent | P4.7 hands off query detail only | Department-scoped cursor queue with purpose, state, freshness, and revocation | Direct opaque detail handoff only |
| P5.4-G20 | Exact conflict/problem response contract is incomplete | ETag and idempotency are required | RFC 9457-shaped safe problem vocabulary, current ETag, retryability, correlation ID | Generated error taxonomy |
| P5.4-G21 | Idempotency command-receipt projection is not frozen | Phase 4 stores immutable receipts | Receipt ID, request fingerprint behavior, replay/mismatch results, no payload leak | Generated command simulator |
| P5.4-G22 | Event transport, reconnect cursor, and polling fallback are not selected | Event envelopes are handed off | Same-origin transport contract, sequence/cursor, resync, version quarantine | Generated event harness; HTTP remains authority |
| P5.4-G23 | Correction impact projection across hypotheses, candidates, alerts, and reviews is absent | Corrections exist across Phase 4 contracts | Typed impact edges, stale markers, supersession, reconsideration eligibility | Generated impact graph only |
| P5.4-G24 | Work assignment, claiming, and saved views have no producer | No stable handoff | Optional revisioned server state with ETags, leases, department scope, no browser secrets | Memory-only non-authoritative organization |
| P5.4-G25 | Cross-portal handoff payloads for intelligence are not frozen | P5.1-P5.3 have handoff patterns | Opaque ref, source portal, target intent, time/spatial context, TTL, server reauthorization | Generated handoff contract |
| P5.4-G26 | Department/permission change purge acknowledgment is not intelligence-specific | P5.1 session foundation exists | Exact cache/query/draft/selection purge and window acknowledgment | Reuse P5.1 baseline plus P5.4 tests |

## Gap Closure Priority

### Start-Blocking Consumer Contracts

P5.4 implementation cannot start without generated browser contracts for
G01-G07, G09-G10, G12-G18, G20-G23, G25, and G26. They may be satisfied by
generated-only local fixtures under a bounded P5.4 start package. This does not
close the corresponding production producer gap.

### Mutation-Blocking Producer Contracts

Review and lifecycle mutation controls must remain disabled unless G14, G16,
G17, G20, and G21 are available together from an authoritative generated
producer. A missing policy, stale ETag, incomplete quorum, or unknown reason
vocabulary is a fail-closed condition.

### Runtime-Blocking Contracts

Real runtime use additionally requires production closure of every applicable
gap, approved provider/data policy, authentication, deployment, security,
retention, legal, and operational gates. P5.4 planning and generated UI
implementation cannot claim those closures.

## No-Downgrade Rule

Later producer work may replace generated adapters behind the typed client
interfaces. It may not remove semantic distinctions, contradiction and
abstention visibility, authoritative tables, ETag conflict handling,
idempotency receipts, correction lineage, department isolation, accessibility,
or the ban on external actions.
