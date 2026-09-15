# P5.4 Workflow And Feature Catalogue

Status: planning baseline; generated-only implementation candidate

## Actors

| Actor | Typical read scope | Mutation scope in P5.4 |
| --- | --- | --- |
| Command viewer | Safe department aggregates and opaque handoffs | None |
| Intelligence viewer | Authorized queues, details, graphs, rules, and chronology | None |
| Intelligence analyst | Viewer scope plus non-authoritative workspace organization | No review or lifecycle authority by implication |
| Mandatory reviewer | Evidence inspection and server-allowed review commands | Exact review/lifecycle commands only with current policy and ETag |
| Intelligence supervisor | Workload and policy visibility under server capability | No automatic override; exact server capabilities only |
| Administrator | Platform configuration visibility as separately authorized | No intelligence truth or review authority by administrator role alone |

Role names are illustrative consumer labels. Exact capabilities come from the
server session and must be rendered, not inferred from route or UI visibility.

## Workflow 1: Triage Intelligence Workload

1. Open Intelligence Overview with department and time-window context.
2. Read freshness, completeness, degraded, contradiction, abstention, and
   correction indicators before volume counts.
3. Open a typed queue using an opaque filter handoff.
4. Confirm the queue header states object type and authority boundary.
5. Sort and filter with server-supported fields only.
6. Preserve a stable selected row across a background invalidation when safe;
   otherwise require an explicit refresh.

Exit: the operator reaches an authoritative list without any client inference.

## Workflow 2: Inspect A Hypothesis

1. Open hypothesis detail at an exact revision.
2. Review supporting, contradicting, missing, retracted, stale, and
   superseding evidence groups.
3. Inspect source observations separately from derived inferences.
4. Inspect time and spatial bounds with precision and truncation markers.
5. Open the producing correlation run and exact rule/configuration revision.
6. Compare earlier revisions without replacing the current revision.
7. Leave through an opaque handoff to a proposed alert or future investigation.

Exit: the operator can explain why the hypothesis exists and what weakens it.

## Workflow 3: Diagnose A Correlation Run

1. Open run queue and filter by procedural state.
2. Inspect input manifest summary, deterministic mode, revision, time bounds,
   attempt lineage, partial result state, and sanitized reason.
3. Compare output references with expected counts and truncation.
4. Open associated hypotheses without treating run success as correctness.
5. Escalate a producer-health issue through a non-operational internal handoff.

Exit: system execution state remains distinct from analytical truth.

## Workflow 4: Explore A Relationship Subgraph

1. Request a bounded server projection around an opaque root reference.
2. Read node/edge count, depth, time window, omitted count, truncation, and
   projection revision before interacting with the graph.
3. Navigate the enhanced graph or authoritative node/edge tables.
4. Select an item to inspect type, provenance, evidence role, direction, and
   temporal validity.
5. Request a new bounded projection for expansion; never expand locally from
   hidden data.
6. Return to the prior projection through explicit history.

Exit: graph shape and visual distance are never presented as evidence.

## Workflow 5: Inspect Spatial Context

1. Open the connected GIS projection with an opaque hypothesis or alert ref.
2. Confirm time window, coordinate reference, precision, completeness,
   freshness, and authorization scope.
3. Compare map features with the synchronized table.
4. Filter by accepted feature and evidence types.
5. Use camera handoff only as an opaque reference to the P5.3 Operations flow.

Exit: proximity remains a spatial observation, not inferred association.

## Workflow 6: Explain A Rule Evaluation

1. Open the exact rule and immutable revision used by an evaluation.
2. Read rule lifecycle and whether it was approved, shadow, suspended, or
   retired at evaluation time.
3. Inspect normalized inputs and provenance.
4. Traverse the typed node trace, timer/window behavior, and outcome.
5. Compare natural-language summary with exact trace.
6. Read abstention, limitation, and missing-input reasons.

Exit: the exact machine-readable trace remains authoritative over prose.

## Workflow 7: Evaluate A Candidate Set

1. Open the candidate set through a field-minimized provider-query projection.
2. Confirm provider class, query purpose, freshness, and revocation state
   without exposing destination, credentials, or raw response.
3. Compare candidates by field-level supporting, contradicting, ambiguous,
   missing, and stale evidence.
4. Read calibration class and method limits; never translate score into a
   percentage identity claim.
5. Select `insufficient evidence` or abstain without penalty.
6. Hand off only opaque references to review context.

Exit: candidate review cannot establish identity or mutate a provider.

## Workflow 8: Review A Proposed Alert

1. Claim or open an item according to a future server work-assignment contract.
2. Read semantic type, chronology, evidence, contradictions, corrections,
   freshness, completeness, rule trace, and current lifecycle.
3. Load the authoritative review policy and current quorum state.
4. Compose a memory-only draft using an allowlisted reason code and bounded
   optional rationale.
5. Review the confirmation summary and exact non-effects.
6. Submit with `If-Match`, expected revision, and idempotency key.
7. Read the command receipt and refetch alert detail.
8. Announce success without moving focus unless the item is no longer visible.

Exit: one append-only review record is accepted or a typed failure is shown.

## Workflow 9: Recover From A Conflict

1. Stop automatic submission after a stale ETag, revision, policy, or quorum.
2. Preserve the old draft in memory only and mark it stale.
3. Fetch current detail, policy, chronology, and review state.
4. Present a semantic comparison of changed fields and new corrections.
5. Require the operator to reconsider the decision and reason.
6. Create a new idempotency key and explicit confirmation.

Exit: no stale decision is replayed and no conflict is silently overwritten.

## Workflow 10: Complete Configurable Quorum

1. Display required independent slots and already accepted attributable votes.
2. Deny duplicate actor, stale-evidence, unauthorized-role, and invalid-slot
   attempts before confirmation when the server projection permits.
3. Submit each review independently through the same guarded mutation path.
4. Refetch lifecycle after each accepted receipt.
5. Explain that quorum completion changes a procedural state only.

Exit: quorum cannot be self-satisfied, client-forged, or treated as authority
for an external action.

## Workflow 11: Review A Correction Or Retraction

1. Receive an invalidation or open Corrections And Reconsideration.
2. Fetch authoritative correction and impact projections.
3. Mark affected open views stale and disable mutation until refetched.
4. Compare old and new meaning, provenance, revision, and effective time.
5. Reconsider prior reviews through a new append-only workflow.
6. Preserve the original review and attach correction lineage.

Exit: changed meaning is visible wherever the affected object appears.

## Workflow 12: Degraded And Recovery Operation

1. Distinguish producer unavailable, partial response, stale cache, event lag,
   policy unavailable, and mutation unavailable.
2. Keep authoritative cached information visibly stale when policy allows.
3. Disable review submission when current policy, ETag, evidence, or quorum
   cannot be confirmed.
4. Fall back from event-driven refresh to bounded polling or manual refresh.
5. Announce recovery and refetch before enabling mutation.

Exit: degradation reduces convenience, never truth or authorization controls.

## Shared UI States

Every page family must implement all applicable accepted states:

| State | Required behavior |
| --- | --- |
| Loading | Stable dimensions, explicit object type, cancellable navigation |
| Empty | Distinguish no results from unavailable, denied, and filtered-out |
| Partial | Show included/omitted counts and producer limitations |
| Stale | Show observation time and stale reason; disable unsafe mutation |
| Degraded | State lost capability and safe fallback without hiding data quality |
| Denied | Avoid resource existence disclosure and remove unauthorized cache |
| Conflict | Stop, preserve draft in memory, refetch, compare, reconsider |
| Failure | Sanitized typed reason, request correlation ID, bounded retry |
| Correction | Show append-only lineage and impacted-object markers |
| Recovery | Refetch authority before clearing warnings or enabling mutation |

## Queue Features

- Cursor pagination with stable server ordering and bounded page size.
- Typed saved-view projection only after a producer contract exists.
- Visible active filters and one-command reset.
- Work age, freshness, completeness, contradiction, abstention, correction, and
  procedural priority columns.
- Table density preferences that do not hide required semantic fields.
- Bulk read-state organization may be considered; bulk review or lifecycle
  mutation is prohibited.
- No auto-advance after a consequential review unless the operator explicitly
  enables a non-destructive view preference.
- No score-only or color-only ranking.

## Cross-Portal Handoffs

| From | To | Payload |
| --- | --- | --- |
| Command Center | Intelligence queue | Opaque filter reference and time window |
| GIS Center | Hypothesis or alert detail | Opaque object ref and bounded spatial context |
| Camera detail | Intelligence detail | Opaque camera/stream ref only |
| Intelligence detail | Live Workspace | Opaque camera ref and requested time context; no playback grant |
| Proposed alert | Future Investigation Center | Opaque alert ref only; P5.5 remains closed |
| Intelligence health | Admin/Security | Sanitized signal and correlation ref only |

Handoffs must be resolved server-side under the destination portal's current
session, department, role, purpose, and field-minimization policy.

## Explicitly Absent Features

P5.4 contains no face or person identity confirmation, guilt assessment,
criminality score, predictive policing, watchlist mutation, provider update,
case-system mutation, recording, snapshot, export, notification, dispatch,
enforcement, autonomous action, model execution, camera control, or direct
network access. UI placeholders must not imply these functions exist.
