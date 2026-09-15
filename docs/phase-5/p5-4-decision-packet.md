# P5.4 Owner Decision Packet

Status: decisions pending; no option authorizes implementation or runtime

Select one option for each decision. Composite selections require a reconciled
planning package that states precedence, fallback, and scope. The recommended
profile is `A/A/A/A/A/A/A/A/A/A/A/A`.

## D-P5.4-001: Product And Portal Topology

### A. Connected Intelligence Center, recommended

Keep Command Center primary. Add one connected Intelligence Center with
grouped page families for overview, hypotheses, correlation runs,
relationships, spatial context, rules, candidates, proposed alerts, review,
corrections, and health. Command and GIS receive safe handoffs and aggregates.

Benefits: clear role and information architecture, rich specialist workflows,
shared shell/contracts, and no duplicate mutation controls.

Tradeoff: requires careful cross-portal handoff and route ownership.

### B. Put all intelligence inside Command Center

Reduces navigation but overloads the primary dashboard and risks mixing
situational awareness with analytical evidence and reviewer authority.

### C. Separate Intelligence, Alert, And Review portals

Strongest organizational separation, but fragments end-to-end evidence review
and increases route, state, authorization, and deployment complexity.

### D. One configurable analyst canvas

Highly flexible but creates difficult accessibility, consistency, and saved
state problems. It risks turning every workflow into an ungoverned dashboard.

## D-P5.4-002: Semantic Truth Presentation

### A. Strict evidence ladder, recommended

Use separate schemas and visual vocabulary for observation, inference,
hypothesis, candidate, proposed alert, review, correction, and lifecycle.
Require source, revision, freshness, completeness, provenance, and authority
limit on every detail surface.

### B. Compact shared result cards

Uses one card shell with type chips. It is visually efficient but increases the
risk that users miss the difference between evidence and conclusion.

### C. Confidence-first presentation

Ranks and styles by score. This is rejected for the baseline because score is
not identity, correctness, guilt, fairness, or operational authority.

### D. Free-form producer labels

Lets each backend define its own terminology. It scales poorly, weakens
accessibility, and makes forbidden-claim enforcement unreliable.

## D-P5.4-003: Queue And Work Organization

### A. Separate typed queues with bounded saved views, recommended

Use hypothesis, correlation-run, proposed-alert, mandatory-review, and
correction queues with stable server ordering, explicit filters, cursor
pagination, workload/freshness fields, and optional revisioned saved views
after a producer exists.

### B. One universal intelligence queue

Simplifies navigation but collapses object semantics and produces ambiguous
filtering, ordering, and actions.

### C. Proposed-alert queue only

Fastest initial UI but hides correlation failures, hypotheses, abstentions,
contradictions, and corrections from analysts.

### D. Client-side joined queues

Combines multiple endpoints in the browser. This creates inconsistent
pagination, scope, freshness, and ordering and is not recommended.

## D-P5.4-004: Relationship Graph And Spatial Rendering

### A. Adapter-based bounded React Flow graph plus authoritative table, recommended

Use an H-CAM renderer interface, a later pinned React Flow dependency for a
read-only bounded enhanced graph, synchronized node/edge tables as authority,
and the accepted P5.2 MapLibre/deck.gl domain for spatial projections. Low
resource can be table-first; capable hardware can render more within server
bounds.

Benefits: accessible React integration, keyboard hooks, replaceable renderer,
shared GIS, and future scalability without changing domain contracts.

Tradeoff: editing-oriented defaults must be disabled and the dependency must
pass an exact supply-chain gate.

### B. Table and GIS only

Strongest simplicity and accessibility with no graph dependency. It loses a
valuable relationship overview but remains a valid fallback mode.

### C. Cytoscape.js bounded graph plus table

Offers mature graph layouts and a broad graph API. It adds canvas accessibility
work and must prohibit client graph analysis or identity inference.

### D. Adaptive React Flow and Sigma dual renderer

Uses React Flow for ordinary bounded views and Sigma/WebGL for large capable
profiles. This offers the highest visual scale but adds two dependencies,
cross-renderer parity risk, and premature complexity. Preserve as a future
extension behind the A adapter, not initial baseline.

## D-P5.4-005: Rule And Evaluation Explanation

### A. Exact revision and typed execution trace, recommended

Show immutable rule revision, lifecycle-at-evaluation, normalized inputs,
provenance, node outcomes, windows/timers, result, abstention, and limits.
Natural language is a secondary deterministic summary.

### B. Natural-language summary only

Easy to scan but cannot prove fidelity to the executed rule and may omit
important limitations.

### C. Raw rule JSON and logs

Technically complete but unsafe, inaccessible, unminimized, and unsuitable for
most operators.

### D. LLM-generated explanation

Potentially readable but introduces model, drift, attribution, and factuality
risks. It is outside current model authority and cannot be authoritative.

## D-P5.4-006: Candidate Uncertainty And Comparison

### A. Field-level evidence matrix with abstention, recommended

Show support, contradiction, ambiguity, missingness, staleness, calibration
class, provenance, and field minimization per candidate. Require the explicit
boundary `identity not established` and preserve `insufficient evidence`.

### B. One aggregate candidate score

Compact but hides disagreement and encourages false precision. Not
recommended.

### C. Side-by-side raw provider records

Maximizes detail but violates minimization and could expose protected fields or
provider internals.

### D. Automatically choose the top candidate

Conflicts with mandatory human review and the prohibition on identity claims.

## D-P5.4-007: Mandatory Review And Quorum

### A. Server-authoritative configurable independent quorum, recommended

Load current policy and ETag, show independent slots, deny duplicate actors,
use memory-only drafts, bounded reasons, neutral confirmation, attributable
append-only decisions, and explicit reconsideration. Ordinary generated policy
defaults to one reviewer; generated high-impact policy defaults to two within
the accepted configurable range.

### B. Fixed one-reviewer policy

Simple but cannot represent accepted configurable quorum or higher-impact
separation of duties.

### C. Client-calculated quorum

Responsive but unsafe because the browser cannot authorize or finalize quorum.

### D. Automatic acceptance after timeout

Conflicts with meaningful human review and is prohibited.

## D-P5.4-008: Mutation Concurrency And Idempotency

### A. Strong ETag plus expected revision plus command receipt, recommended

Require `If-Match`, typed expected revision, unique idempotency key, request
fingerprint, immutable receipt, and server transaction. Conflicts stop, refetch,
compare, and require new confirmation. Never auto-resubmit.

### B. ETag only

Prevents many lost updates but leaves command replay and response-loss
ambiguity incomplete.

### C. Idempotency key only

Controls duplicate submission but cannot detect a decision made against stale
evidence or policy.

### D. Last write wins

Simplest implementation but unacceptable for consequential review records.

## D-P5.4-009: Event And Refresh Strategy

### A. Scoped event invalidation with HTTP authority, recommended

Versioned events invalidate exact query keys, coalesce bursts, and trigger
bounded refetch. Unknown versions are quarantined. HTTP confirms current state,
authorization, ETag, and allowed actions. Polling/manual refresh is fallback.

### B. Events directly patch all client state

Lower apparent latency but risks stale authority, event-order bugs, and partial
object corruption.

### C. Polling only

Simple and robust but slower for corrections and potentially wasteful.

### D. Manual refresh only

Low complexity but unsuitable for active review and correction awareness.

## D-P5.4-010: Correction And Reconsideration

### A. Append-only impact graph with stale-action lock, recommended

Preserve original records, show correction/retraction/supersession lineage,
invalidate every affected view, disable stale mutation, refetch authority, and
record any reconsideration as a new attributable entry.

### B. Replace corrected records in place

Cleaner display but destroys chronology and accountability.

### C. Show corrections only on a dedicated page

Preserves a log but lets outdated meaning remain unmarked elsewhere.

### D. Automatically reverse earlier reviews

Removes human judgment and creates an unauthorized action path.

## D-P5.4-011: Accessibility And Human-Factors Baseline

### A. Authoritative table-first equivalence with workload safeguards, recommended

Require complete keyboard workflows, visible focus, stable dimensions,
localized semantic labels, non-color cues, bounded live announcements,
reduced motion, reflow, neutral confirmation, contradiction prominence,
workload age, and no speed leaderboard. Enhanced graph/map views synchronize
with tables.

### B. Visual graph optimized for expert mouse users

Can be efficient for some analysts but excludes other users and cannot be the
authoritative workflow.

### C. Separate accessible application

Duplicates behavior and tends to drift from the primary application.

### D. Browser defaults only

Insufficient for complex queues, graphs, dialogs, conflicts, and live updates.

## D-P5.4-012: Validation And Evidence Standard

### A. Deterministic generated-only layered validation, recommended

Require contract, unit, component, browser, accessibility, visual, security,
profile-parity, concurrency, idempotency, correction, event-divergence,
hostile-input, clean-replay, hash, dependency, and full-regression evidence.
Use generated C1/C10/C50 workload layers without production claims.

### B. Unit tests only

Fast but misses workflow, accessibility, browser, and cross-contract failures.

### C. Manual visual review only

Useful as a supplement but not deterministic or comprehensive.

### D. Real data and operator trial in P5.4

Not authorized. It requires separate data, legal, security, environment, and
operational gates after generated acceptance.

## Recommended Selection Statement

```text
D-P5.4-001: A
D-P5.4-002: A
D-P5.4-003: A
D-P5.4-004: A
D-P5.4-005: A
D-P5.4-006: A
D-P5.4-007: A
D-P5.4-008: A
D-P5.4-009: A
D-P5.4-010: A
D-P5.4-011: A
D-P5.4-012: A
```

Selection records planning intent only. A reconciled package, exact planning
acceptance, bounded start package, and exact start authorization remain
required before any product or test implementation.
