# P5.5 Reconciled Planning R1

Status: owner selections reconciled; exact planning acceptance pending

Selected profile: `A/A/A/A/A/A/A/A/A/A/A/A`

Base package: `P5.5-PLANNING-R0`, SHA-256
`6163927BD3C5E7649E7114A63C449839141D38BA6E2DD9CA87889E759DB4A84A`

## Reconciled Product Topology

Command Center remains the primary H-CAM dashboard. Investigation Center is a
connected specialist portal for investigation workload, typed chronology,
reconstruction, comparison, correction and retraction impact, relationships,
and authorized handoffs. It does not replace Command Center, Intelligence
Center, GIS Center, Operations, Live Workspace, or Monitor Wall.

Evidence Desk is connected to Investigation Center but remains a separately
authorized domain. Investigation access, an evidence reference, a relationship,
an administrator role, or a deep link never grants evidence access. Every
Evidence Desk entry performs current department, purpose, role, capability,
session, and object-scope checks and returns bounded denial behavior without
resource-existence disclosure.

## Reconciled Work Organization

Investigation work uses bounded typed views rather than one client-composed
universal queue. Initial views include recent changes, correction pending,
reconstruction incomplete, evidence unavailable, review required, and
generated policy-preview state. Counts, filters, sort fields, page cursors,
freshness, completeness, and truncation are server authoritative.

Saved-filter capability is guarded by an explicit producer contract. Until it
exists, generated fixtures or memory-only local preferences may demonstrate
organization without creating a durable or cross-device truth source. The UI
does not join unbounded investigation, evidence, review, relationship, or
policy collections in the browser.

## Reconciled Chronology

Monotonic record sequence is the authoritative append-history order. Every
timeline row preserves record time, sequence, entry type, actor class,
provenance, revision, freshness, and authority limit. Pagination exposes stable
first and last anchors so an exact row can be referenced and focus can be
restored after refresh.

Event time is a separately labeled analytical view. It carries the asserting
source, instant or range, precision, clock condition, unknown state, and tie
handling. Event time cannot reorder or rewrite append history. Unknown values,
late arrivals, ties, backdated assertions, and clock disagreement remain
visible rather than being silently normalized.

The server-paginated semantic table or list is authoritative and complete. An
optional visual lane may window only bounded returned data and must stay
synchronized with the table. Infinite-scroll-only and full 10,000-row render
paths are rejected. No timeline virtualization dependency is selected now.

## Reconciled Reconstruction And Comparison

Reconstruction is requested through an exact known revision. The authoritative
response identifies revision, reconstruction profile, deterministic digest,
included entries, omitted components, completeness, limitations, and later
corrections or retractions outside the reconstructed point. A client cannot
claim authority by replaying cached events.

Comparison accepts exact base and target revisions and returns typed changes
for entries, lifecycle, corrections, retractions, relationships, evidence
references, completeness, and limitations. Added, changed, unchanged,
unavailable, unknown, and not-active-in-this-projection are distinct. A record
is never described as deleted merely because it is inactive in the selected
revision. Generated or AI-authored historical narrative is not authoritative.

## Reconciled Corrections, Retractions, And Impact

Corrections and retractions are append-only successors. The original entry
remains available subject to authorization. The UI binds predecessor and
successor, exact changed fields, reason vocabulary, actor class, record time,
revision, and authority. Historical state is never overwritten or hidden.

Every affected hypothesis, proposed alert, review, relationship, evidence
reference, reconstruction, export preview, and other accepted target receives
a typed impact status: pending, applied, blocked, failed, or superseded.
Incomplete impact closure is visible. Stale downstream mutation remains locked
until authoritative state is fetched and any reconsideration is explicitly
recorded as a new attributable entry. No review or relationship is
automatically reversed.

## Reconciled Evidence State

Evidence Desk uses an orthogonal state matrix. It never collapses evidence into
one verified badge, confidence score, authenticity claim, identity claim,
guilt claim, admissibility claim, or proof-of-event claim. The selected state
dimensions are:

1. reference identity and immutable opaque identifier;
2. source-reference availability without source resolution;
3. digest or integrity observation, algorithm, observer, time, and freshness;
4. provenance closure, truncation, derivation, and limitations;
5. custody-event history, sequence, gaps, and disputed or unknown state;
6. signature or timestamp observation without validity or legal conclusion;
7. current access decision and purpose boundary;
8. separately sourced legal or policy assessment, including unknown or not
   assessed.

Integrity indicates only that a defined technical comparison produced a
defined result. It does not establish factual truth, source authenticity,
identity, legality, admissibility, or correctness of the recorded event.

## Reconciled Provenance And Custody

The selected provenance view reuses a bounded internal read-only graph adapter.
It preserves typed entity, activity, agent, generation, use, derivation,
association, attribution, delegation, and invalidation semantics from accepted
Phase 4.5 contracts. Every graph response states node, edge, depth, time,
omission, and truncation bounds.

Authoritative node and edge tables provide the complete accessible task.
Visual position, distance, color, size, clustering, and centrality are not
evidence. Custody remains a separate sequence-authoritative table/timeline;
provenance edges do not imply physical or legal custody. Gaps, unknown actors,
late custody entries, and disputed transitions remain explicit.

A generated W3C PROV-compatible projection is a lossy interchange preview.
External import, round-trip equivalence, validator execution, and conformance
claims remain disabled.

## Reconciled Source And Media Boundary

The browser receives minimized opaque source references only. It displays
explicit source-not-resolved and media-not-rendered states. It does not receive
source credentials, secret references, operational locators, raw provider
responses, filesystem paths, object-store keys, signed source URLs, or hidden
media endpoints.

P5.5 does not resolve, copy, render, preview, transcode, stream, snapshot,
download, print, export, delete, hold, release, or modify source evidence. A
future source resolver or media handoff requires a separate typed producer,
authorization, retention, custody, security, privacy, audit, and deployment
decision. No reference, route, role, profile, or UI state activates it.

## Reconciled Policy Preview Studio

Retention, hold, deletion, disposition, and export remain generated-only and
non-operative. Policy Preview Studio presents policy-reference identifiers,
exact target sets, conflicts, inclusion and exclusion reasons, simulated
per-target outcomes, residual references, completeness, limitations, and
unresolved producer gaps.

The UI contains no execute, approve, sign, activate, release, deliver,
download, print, delete, hold, retention-change, or export control. A preview
never selects applicable law, a retention period, a disposition authority, an
export recipient, or an operational procedure. Disabled case-management and
external-PROV bridges remain visible only as typed unavailable capabilities.

## Reconciled Concurrency, Events, And Recovery

Consequential future commands require a current strong ETag, `If-Match`, exact
expected revision, unique idempotency key, request fingerprint, immutable
sanitized receipt, server transaction, and authoritative HTTP refetch. Drafts
are memory-only and bound to department, purpose, object, revision, ETag, and
session. Logout, authority loss, purpose change, department switch, or object
scope loss clears drafts and sensitive caches.

A precondition, revision, scope, or policy conflict stops automatic submission.
The UI preserves a bounded memory-only draft, fetches current state, displays a
typed before/after comparison, and requires deliberate reconsideration with a
new idempotency key and confirmation. Last-write-wins and automatic mutation
retry are rejected.

Versioned events invalidate exact scoped query keys only. They do not append
authoritative evidence history, apply corrections, establish custody, or patch
policy truth directly into client state. Duplicates are harmless, bursts are
coalesced, unknown versions are quarantined, and bounded polling or manual
refresh handles event gaps. HTTP remains authoritative.

## Reconciled Accessibility And Resource Profiles

Every graph, visual lane, matrix, comparison, and state indicator has a
complete semantic table or list path with keyboard operation, visible focus,
logical reading order, non-color labels, bounded announcements, target size,
reflow, contrast, reduced motion, hostile-text containment, and stable focus
after pagination or invalidation.

Low-resource, enhanced-workstation, control-room, GPU-lab, and future-server
profiles may change page size within server bounds, prefetch budget, animation,
layout density, graph cap, or rendering quality. Low-resource mode retains all
information, warnings, access checks, corrections, limitations, and recovery
paths. Hardware cannot change authority, evidence semantics, legal meaning,
retention behavior, field minimization, audit, or source-operation boundaries.

## Reconciled Validation Contract

The existing locked frontend dependencies remain the baseline. No immediate
virtualization, graph database, browser cryptography, document viewer, export,
or media dependency is selected. An additive adapter may be evaluated later
only after a concrete producer and workload need is authorized.

Generated-only layered validation covers:

- contract, fixture, schema, component, story, browser, keyboard,
  accessibility, visual, security, scope, cache-teardown, and repository tests;
- normal, empty, partial, stale, degraded, denied, conflicting, failed,
  corrected, retracted, recovering, disputed, unknown, and unavailable states;
- record/event-time disagreement, late entry, tie, unknown time, pagination,
  stable anchors, exact reconstruction, comparison, and digest mismatch;
- ETag, revision, idempotency, receipt, conflict, reconsideration, duplicate or
  delayed event, reconnect gap, unknown version, and HTTP divergence;
- graph/table, visual-lane/table, custody/table, matrix/table, and profile
  equivalence;
- recursive forbidden-field, URL, storage, log, telemetry, output-encoding,
  source-operation, evidence-overclaim, and policy-action scans;
- deterministic C1, C10, and C50 generated workloads on all profiles, two
  clean replays, hashes, environment declarations, and full regression.

Generated validation cannot establish legal compliance, admissibility,
authenticity, factual truth, meaningful human judgment, operational readiness,
production capacity, or fitness for policing.

## Preserved Gaps, Threats, And Workstreams

All 36 `P5.5-G01` through `P5.5-G36` producer and consumer gaps and all 56
`T01` through `T56` threats remain open until a later authorized implementation
provides exact evidence or an explicit blocked result. The eight frozen
workstreams remain unchanged:

| Workstream | Weight |
| --- | ---: |
| P5.5-W1 Consumer contracts and generated fixtures | 2.0 |
| P5.5-W2 Investigation overview and authoritative timeline | 2.5 |
| P5.5-W3 Reconstruction, comparison, corrections, and relationships | 2.5 |
| P5.5-W4 Evidence Desk, integrity, provenance, and custody | 2.5 |
| P5.5-W5 Non-operative policy previews and disabled bridges | 1.5 |
| P5.5-W6 Authorization, concurrency, invalidation, and handoffs | 1.5 |
| P5.5-W7 Accessibility, security, profiles, and signals | 1.0 |
| P5.5-W8 Validation, evidence, and acceptance | 1.5 |
| **Total** | **15.0** |

The technical cap remains 14/15. Exact owner exit acceptance remains worth the
final 1 point. No scope or weight was rebaselined.

## Exact Progress

- P5.5 owner decisions: **12/12 (100.0000%)**, change **+100.0000 percentage points**.
- P5.5 planning: **8/8 (100.0000%)**, change **+0.0000 percentage points**.
- P5.5 product: **0/15 (0.0000%)**, change **+0.0000 percentage points**.
- Phase 5 product: **63/100 (63.0000%)**, change **+0.0000 percentage points**.

## Next Gate

Exact owner acceptance of the sealed `P5.5-PLANNING-R1` package is required.
That acceptance permits preparation only of one separate non-effective exact
digest-bound P5.5 start package. It does not authorize implementation.

The single local checkpoint commit allowed by `D-P5.5-PLAN-AUTH` was consumed
by commit `7bd579cf8a42fafd48f9cc1752bb12656587b19d`. This reconciliation remains
uncommitted and cannot be committed without new authority.

## Continuing Prohibitions

Product/test implementation, source import, dependencies or lockfiles, routes,
migrations, frontend/browser runtime, source/evidence operations, legal-policy
decisions, real investigations, providers/network/cameras/media,
Government/private data, identities, models/datasets/inference, operational
actions, containers, Kubernetes, deployment, P5.6, another commit, and remote
Git remain closed.
