# P5.4 Bounded Implementation Plan

Status: accepted bounded generated-only implementation baseline; implementation in progress

## Objective

Implement a production-shaped but generated-only Intelligence Center that
preserves analytical meaning, exposes uncertainty and correction, enables
accountable mandatory review, and remains functionally complete on a
low-resource laptop while scaling visual density on capable hardware without
changing operator authority.

## Frozen Product Weight

P5.4 carries 15 of 100 Phase 5 points. Planning and research earn no product
points.

| Workstream | Points | Exit outcome |
| --- | ---: | --- |
| W1. Consumer contracts and generated fixtures | 2.0 | Typed evidence ladder, queues, details, errors, events, handoffs, and deterministic fixtures |
| W2. Intelligence overview and queues | 2.0 | Hypothesis/run/alert/review/correction workloads with complete states |
| W3. Hypothesis, run, graph, spatial, and rule explanation | 2.5 | Bounded synchronized projections with exact provenance and rule trace |
| W4. Proposed alerts and candidate uncertainty | 2.5 | Semantic alert identity, field-level candidate evidence, contradiction, and abstention |
| W5. Mandatory review, quorum, and concurrency | 2.5 | Policy, draft, confirmation, ETag, idempotency, receipt, and conflict recovery |
| W6. Lifecycle, corrections, and event invalidation | 1.5 | Append-only chronology, correction impact, stale locks, HTTP-confirmed refresh |
| W7. Accessibility, security, profiles, and signals | 1.0 | Equivalent workflows and invariant authority across profiles |
| W8. Validation, evidence, and acceptance | 1.0 | Deterministic generated evidence, limitations, sealed package, exact acceptance |
| **Total** | **15.0** | **P5.4 complete only after exact owner acceptance** |

Technical implementation may earn at most 14/15 points. The final 1 point is
awarded only by exact owner acceptance of the sealed evidence package.

## Delivery Sequence

### W1: Consumer Contracts And Generated Fixtures

1. Add browser-safe schemas for observation, inference, hypothesis, candidate,
   proposed alert, review, correction, lifecycle, rule trace, graph, spatial
   projection, review policy, command receipt, and safe problem details.
2. Encode recursive forbidden-key and forbidden-claim rules.
3. Define typed query keys, event invalidations, handoffs, pagination,
   freshness, completeness, ETag, idempotency, and profile projections.
4. Generate deterministic normal, partial, stale, denied, conflicting,
   contradictory, abstaining, corrected, hostile, and degraded fixtures.
5. Preserve each production producer gap as explicit fixture metadata.

Stop conditions: any DTO contains raw provider data, destination, credential,
camera/media locator, unnecessary identity field, operational action, or an
unqualified identity/guilt/criminality claim.

### W2: Intelligence Overview And Queues

1. Add the connected Intelligence Center route family under the P5.1 shell.
2. Build overview, hypothesis, run, proposed-alert, review, correction, and
   health queues against generated adapters only.
3. Implement stable cursor pagination, typed filters, deterministic sort,
   visible filter reset, and authoritative list/detail navigation.
4. Implement loading, empty, partial, stale, degraded, denied, conflict,
   failure, correction, and recovery states.
5. Connect safe aggregate and opaque handoffs from Command Center.

Stop conditions: one universal untyped queue, client-side unbounded joins,
score-first default order, bulk review, or implied real producer availability.

### W3: Hypothesis, Run, Graph, Spatial, And Rule Explanation

1. Build hypothesis and run detail with exact revisions, evidence roles,
   provenance, time bounds, freshness, completeness, partial state, and
   correction lineage.
2. Implement `RelationshipGraphRenderer` and synchronized node/edge tables.
3. Under an exact dependency gate, add a read-only bounded React Flow adapter;
   retain a dependency-free table fallback and renderer kill switch.
4. Reuse the P5.2 GIS domain for bounded GeoJSON spatial projection and table
   parity without tiles or network.
5. Build exact rule revision and typed evaluation trace with a secondary
   deterministic summary.

Stop conditions: client inference, graph algorithm claims, unbounded expansion,
visual distance as evidence, spatial proximity as association, or prose as the
only explanation.

### W4: Proposed Alerts And Candidate Uncertainty

1. Build alert list/detail and chronology with semantic occurrence identity
   separate from delivery/idempotency identity.
2. Display procedural priority without translating it into criminal severity.
3. Build candidate-set field matrix with support, contradiction, ambiguity,
   missingness, staleness, calibration class, provenance, and abstention.
4. Require persistent `identity not established` and proposed-alert authority
   limits.
5. Exclude raw provider responses and provider/network controls.

Stop conditions: top-candidate auto-selection, identity probability copy,
hidden contradictions, or any operational-alert wording/action.

### W5: Mandatory Review, Quorum, And Concurrency

1. Implement a generated server-authoritative review-policy adapter and
   independent quorum projection.
2. Keep decision drafts in memory with purge on logout, department change,
   role loss, expiry, route disposal, and window closure.
3. Implement bounded reasons, optional minimized rationale, evidence-first
   review, neutral confirmation, and exact non-effect summary.
4. Require strong ETag, expected revision, idempotency key, request
   fingerprint, immutable command receipt, and authoritative refetch.
5. Implement conflict comparison and explicit reconsideration with no
   automatic mutation retry.

Stop conditions: client quorum, duplicate actor slot, stale review, persisted
draft, last-write-wins, automatic approval, or external side effect.

### W6: Lifecycle, Corrections, And Event Invalidation

1. Build server-projected allowed lifecycle commands and append-only history.
2. Build correction/retraction/supersession impact views and stale-action lock.
3. Record reconsideration as a new review without changing historical entries.
4. Extend the P5.1 invalidation package with typed P5.4 query-key mapping,
   unknown-version quarantine, burst coalescing, and polling/manual fallback.
5. Refetch HTTP authority before enabling any mutation after an event.

Stop conditions: event-applied authority, silent history rewrite, correction
visible only on one page, or automatic reversal of a human decision.

### W7: Accessibility, Security, Profiles, And Signals

1. Complete keyboard, focus, dialog, announcement, contrast, reflow, target,
   reduced-motion, and stable-dimension behavior.
2. Prove graph/map/list/table selection and meaning parity.
3. Apply department-partitioned queries, uniform denial, deep cache/draft purge,
   output encoding, CSP, and recursive telemetry redaction.
4. Verify low-resource, enhanced, control-room, GPU-lab, and future-server
   profiles change rendering only.
5. Emit low-cardinality generated signals for queue state, conflict,
   invalidation, correction, review result family, and degraded state without
   object/user/department/provider labels.

Stop conditions: profile-dependent authority, inaccessible core workflow,
protected metric/log value, or browser-only authorization.

### W8: Validation, Evidence, And Acceptance

1. Run contract, unit, component, story, browser, visual, accessibility,
   security, forbidden-claim, concurrency, replay, dependency, and repository
   regression suites.
2. Run generated C1, C10, and C50 queue workloads for all profiles without
   hardware or production-capacity claims.
3. Execute two clean deterministic scenario replays and compare canonical
   outputs.
4. Generate source, dependency, fixture, screenshot, accessibility, validation,
   threat, gap, environment, and limitation evidence indexes.
5. Seal exact technical commit, evidence package, and owner acceptance proposal.

Stop conditions: nondeterminism, graph/table mismatch, profile authority drift,
unmapped producer gap or threat, unsupported claim, real data/network use, or
failed security/accessibility validation.

## Proposed Frontend Structure

The exact start package may authorize additive paths shaped like:

```text
frontend/apps/intelligence-center/
  src/pages/
    overview/
    hypotheses/
    correlation-runs/
    relationship-explorer/
    spatial-intelligence/
    rule-evaluations/
    candidates/
    proposed-alerts/
    review-desk/
    corrections/
    intelligence-health/

frontend/packages/
  intelligence-contracts/
  intelligence-domain/
  intelligence-fixtures/
  relationship-renderers/
  review-workflows/
```

This is a proposed ownership map, not authorization to create these paths.
P5.1 packages remain the shared shell, API, session, capability, query,
invalidation, observability, design, accessibility, and test foundation.

## Generated Scenario Matrix

| Dimension | Required cases |
| --- | --- |
| Semantic type | observation, inference, hypothesis, candidate, proposed alert, review, correction, lifecycle |
| Evidence | supporting, contradicting, missing, retracted, stale, superseded, mixed |
| Hypothesis/run | queued, running, succeeded, partial, failed, superseded, corrected |
| Graph | empty, bounded, truncated, cyclic, disconnected, hostile label, revision change |
| Spatial | no geometry, point, path, zone, imprecise, stale, truncated, denied |
| Rule | approved, shadow, suspended, retired, mismatch summary, abstention, missing input |
| Candidate | none, one, tie, contradiction, ambiguous, stale, revoked provider, abstention |
| Alert | each accepted lifecycle, corrected, suppressed, merged, stale policy |
| Review | one and multi-reviewer, duplicate actor, forbidden role, conflict, receipt loss, replay, mismatch |
| Event | ordered, duplicate, delayed, burst, unknown version, HTTP divergence, reconnect gap |
| Session | logout, department switch, permission loss, expiry, two windows, stale deep link |
| Profile | low-resource, enhanced, control-room, GPU-lab, future-server with authority parity |
| Accessibility | keyboard, focus, live region, non-color, contrast, zoom/reflow, reduced motion |
| Workload | generated C1, C10, C50 with declared machine and no production claim |

## Start-Package Requirements

A future `P5.4-START-R0` package must bind:

- exact accepted planning package, owner decisions, base commit, branch, paths,
  immutable Phase 3/4/P5.1-P5.3 inputs, and change budget;
- exact direct dependency allowlist, version, integrity, license, transitive
  set, vulnerability evidence, bundle budget, kill switch, and rollback;
- exact generated fixture seeds, counts, schemas, forbidden values, maximum
  sizes, hashes, and retention paths;
- exact loopback origins and network prohibition;
- exact command simulator semantics for ETag, idempotency, quorum, conflicts,
  receipts, correction, and event/HTTP divergence;
- exact browser viewports, profiles, process/time/output bounds, commands, and
  evidence paths;
- exact local-commit allowance and continuing no-remote-Git rule;
- explicit no-action and no-overclaim assertions.

## Acceptance Criteria

P5.4 is complete only when all 15 points are earned under sealed evidence and
exact owner acceptance. At that point Phase 5 advances from 48/100 to 63/100.
Planning completion leaves P5.4 at 0/15 and Phase 5 at 48/100.
