# P5.4 Reconciled Planning R1

Status: owner selections reconciled; exact planning acceptance pending

Selected profile: `A/A/A/A/A/A/A/A/A/A/A/A`

Base package: `P5.4-PLANNING-R0`, SHA-256
`1ACB4280AF7DC8F88B847D0906A6B97704AAF1E4EF6FB3DA32B979D030235451`

## Reconciled Product Shape

Command Center remains the primary H-CAM dashboard. Intelligence Center is one
connected specialist portal with grouped page families for intelligence
overview, hypotheses, correlation runs, relationship exploration, spatial
intelligence, rules and evaluations, candidate evidence, proposed alerts,
mandatory review, corrections and reconsideration, and intelligence health.

Command Center may show field-minimized workload aggregates and opaque links.
It does not duplicate intelligence review controls. GIS Center remains the
specialist spatial dashboard and shares the accepted P5.2 GIS domain.
Operations camera and live surfaces remain separately owned under P5.3.

## Reconciled Truth Model

The selected evidence ladder is mandatory and cannot be simplified by a
resource profile or visual design:

1. source observation;
2. derived inference;
3. falsifiable hypothesis;
4. possible reference candidate;
5. review-required proposed alert;
6. attributable human review;
7. append-only correction, retraction, or supersession;
8. procedural lifecycle state.

Each object carries its type, source class, provenance, revision, freshness,
completeness, evidence role, and authority limit. A score, relationship,
hypothesis, candidate, proposed alert, review, or quorum result cannot be
presented as confirmed identity, guilt, criminality, intent, predictive risk,
or operational truth.

## Reconciled Queue Architecture

Separate queues are selected for hypotheses, correlation runs, proposed
alerts, mandatory reviews, and corrections. They use server-side allowlisted
filters, stable deterministic ordering, bounded cursor pagination, visible
filter state, and authoritative list/detail navigation. A universal client-side
joined queue is rejected.

Default ordering emphasizes work age and procedural need without ranking
people or converting analytical scores into priority. Bulk review and bulk
lifecycle mutation remain prohibited. Revisioned saved views remain a producer
gap; generated or memory-only organization is used until a safe server
contract exists.

## Reconciled Relationship And Spatial Projections

The selected relationship architecture uses an H-CAM renderer adapter. A later
exactly pinned React Flow package is the preferred bounded read-only enhanced
renderer candidate. It is not installed or authorized by this reconciliation.
Editing, dragging-as-meaning, graph mutation, client inference, identity
resolution, risk calculation, centrality claims, and unbounded expansion are
prohibited.

Authoritative node and edge tables remain complete and synchronized with the
graph. Server responses define maximum nodes, edges, depth, time window,
omitted counts, truncation, direction, evidence role, provenance, and
revision. Visual distance, size, color, and layout are never evidence.

Spatial intelligence reuses P5.2 MapLibre and optional deck.gl adapters over
bounded GeoJSON/WGS 84 projections. The synchronized table remains
authoritative. Spatial proximity is not association, causation, identity, or
guilt. No map/tile/provider network access is selected.

## Reconciled Rule Explanation

The exact immutable rule revision and typed execution trace are authoritative.
The view includes lifecycle-at-evaluation, normalized inputs, provenance,
node-by-node outcomes, time windows, timers, result, abstention, missing input,
and limitations. A deterministic natural-language summary may assist scanning
but cannot replace or contradict the exact trace. Raw logs and LLM-generated
explanations are not selected.

## Reconciled Candidate Presentation

Candidate sets use a field-level evidence matrix. Each candidate exposes only
authorized minimized fields with support, contradiction, ambiguity,
missingness, staleness, calibration class, provenance, and limitation states.
`Identity not established` and `insufficient evidence` are first-class states.

The browser never receives raw provider responses, provider destinations,
credentials, secret references, unnecessary identity fields, or mutation
controls. It never automatically chooses a top candidate or translates a
score into identity probability.

## Reconciled Human Review And Quorum

The server is authoritative for review policy, current ETag, allowed decision
and reason vocabulary, independent reviewer slots, actor eligibility, quorum,
and lifecycle transitions. Duplicate actors cannot satisfy multiple
independent slots. Administrator role alone does not grant reviewer authority.

The review desk presents evidence, contradiction, correction, freshness,
completeness, rule trace, current policy, and remaining quorum before decision
controls. Drafts are memory-only, reasons are bounded, confirmation is neutral,
and every accepted review is append-only and attributable.

Quorum completion changes procedural state only. It does not establish
identity or truth and cannot trigger notification, dispatch, enforcement,
provider mutation, case mutation, or another external action.

## Reconciled Concurrency And Idempotency

Every consequential mutation requires:

- a current strong ETag and `If-Match`;
- an exact expected aggregate revision;
- a unique idempotency key;
- server request-fingerprint comparison;
- an immutable sanitized command receipt;
- one authoritative HTTP refetch after response.

A precondition, policy, quorum, or revision conflict stops automatic
submission. The old draft is marked stale and retained in memory only. The UI
fetches current state, shows a semantic comparison, and requires deliberate
reconsideration, a new idempotency key, and a new confirmation. Last-write-wins
and automatic mutation retry are rejected.

## Reconciled Events And Corrections

Versioned events invalidate exact query keys. They do not patch authority,
review, quorum, lifecycle, candidate identity, or correction truth directly
into the client cache. Duplicate events are harmless, bursts are coalesced,
unknown versions are quarantined, and bounded polling or manual refresh is the
fallback. HTTP remains authoritative.

Corrections, retractions, and supersessions are append-only. Impacted open
hypotheses, candidate sets, proposed alerts, reviews, and future investigation
references become visibly stale and mutation-disabled until refetched.
Reconsideration creates a new attributable entry and never rewrites an earlier
review.

## Reconciled Accessibility And Human Factors

Authoritative list/table workflows provide the complete task when graph, map,
WebGL, animation, multiple monitors, or enhanced rendering are unavailable.
Enhanced graph and map selections synchronize with those tables.

Keyboard operation, visible focus, logical task order, non-color state,
localized names and descriptions, bounded polite announcements, critical
authority-loss announcements, stable dimensions, reflow, target size,
contrast, reduced motion, neutral confirmation, contradiction prominence, and
workload-age visibility are mandatory gates. Speed leaderboards, score-first
defaults, and approval-biased controls are rejected.

## Reconciled Dynamic Profiles

Low-resource, enhanced-workstation, control-room, GPU-lab, and future-server
profiles may change rendering density, visible graph cap within server bounds,
layout quality, prefetch budget, and animation. Low-resource mode remains
functionally complete through authoritative tables and all review safeguards.

Profiles cannot change department or role authorization, field minimization,
evidence semantics, quorum, lifecycle transitions, review confirmation,
correction behavior, retention, logging, accessibility authority, or the
external-action prohibition. GPU-lab does not imply model or inference access.

## Reconciled Validation Contract

The selected generated-only evidence matrix covers:

- contract, unit, component, story, browser, visual, and accessibility checks;
- normal, empty, partial, stale, degraded, denied, conflicting, failed,
  corrected, recovering, contradictory, abstaining, and hostile states;
- exact ETag, expected revision, idempotency, replay, payload mismatch,
  duplicate actor, quorum race, receipt loss, and reconsideration behavior;
- event ordering, duplication, delay, burst, unknown version, reconnect gap,
  and event/HTTP divergence;
- graph/table and map/table semantic parity, truncation, hostile labels, and
  profile fallback;
- recursive forbidden-field, forbidden-claim, URL, storage, log, telemetry,
  CSP, output-encoding, and external-action scans;
- generated C1, C10, and C50 workloads on every profile without production or
  hardware-capacity claims;
- two clean deterministic replays, exact hashes, environment declaration,
  dependency evidence, known limitations, and full repository regression.

No generated test can establish model validity, bias absence, meaningful human
judgment, legal compliance, operational readiness, or fitness for policing.

## Preserved Gaps, Threats, And Workstreams

All 26 `P5.4-G01` through `P5.4-G26` gaps and all 40 `T01` through `T40`
threats remain open until an authorized implementation provides evidence or an
explicit blocked status. The eight workstreams remain frozen:

| Workstream | Weight |
| --- | ---: |
| P5.4-W1 Consumer contracts and generated fixtures | 2.0 |
| P5.4-W2 Intelligence overview and queues | 2.0 |
| P5.4-W3 Hypothesis, run, graph, spatial, and rule explanation | 2.5 |
| P5.4-W4 Proposed alerts and candidate uncertainty | 2.5 |
| P5.4-W5 Mandatory review, quorum, and concurrency | 2.5 |
| P5.4-W6 Lifecycle, corrections, and event invalidation | 1.5 |
| P5.4-W7 Accessibility, security, profiles, and signals | 1.0 |
| P5.4-W8 Validation, evidence, and acceptance | 1.0 |
| **Total** | **15.0** |

The technical cap remains 14/15. Exact owner exit acceptance remains worth the
final 1 point. No scope or weight was rebaselined.

## Exact Progress

- P5.4 owner decisions: **12/12 (100.0000%)**, change **+100.0000 percentage points**.
- P5.4 planning: **8/8 (100.0000%)**, change **+0.0000 percentage points**.
- P5.4 product: **0/15 (0.0000%)**, change **+0.0000 percentage points**.
- Phase 5 product: **48/100 (48.0000%)**, change **+0.0000 percentage points**.

## Next Gate

Exact owner acceptance of the sealed `P5.4-PLANNING-R1` package is required.
That acceptance may authorize preparation only of one separate non-effective
start package. It does not authorize implementation.

The original one-commit allowance in `D-P5.4-PLAN-AUTH` was consumed by commit
`16f9029e104cec40d06a3b9ce0eb0e2ec4e4d0ac`. This reconciliation is not
committed and cannot be committed without new authority.

## Continuing Prohibitions

Product/test implementation, source import, dependency resolution/install or
lockfile changes, backend routes/migrations, frontend/browser runtime,
models/datasets/artifacts/inference, providers/network/cameras/media,
Government/private data, real investigations/identities, operational alerts,
notifications, dispatch, enforcement, autonomous action, containers,
Kubernetes, deployment, P5.5, commit, push, and remote Git remain closed.
