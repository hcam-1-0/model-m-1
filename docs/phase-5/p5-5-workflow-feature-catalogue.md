# P5.5 Workflow And Feature Catalogue

Status date: 2026-09-09

Status: planning complete; owner decisions and implementation remain pending

## Actors

| Actor | Permitted planning surface | Explicitly absent authority |
| --- | --- | --- |
| Command operator | scoped investigation summary and handoff | evidence detail, legal action, source access |
| Investigator | timeline, reconstruction, corrections, relationships | source resolution, deletion, export execution |
| Evidence reader | field-minimized evidence reference and history | source content, mutation, policy execution |
| Integrity assessor | append-only assessment review and future bounded submission | authenticity or legal determination |
| Provenance reviewer | bounded lineage and custody projection | external PROV import, graph mutation |
| Investigation reviewer | attributable review/disposition history | notification, dispatch, enforcement |
| Retention evaluator | generated policy preview | selecting law, period, hold, deletion, export |
| Administrator | capability and producer-gap status | investigation/evidence access by admin role alone |
| Auditor | separate attributable audit projection | evidence access unless independently authorized |

All actors remain department, purpose, role, capability, and current-session
scoped. A reference or relationship never grants access.

## Workflow 1: Triage Investigation Workload

1. Open Investigation Center from Command Center or Intelligence Center.
2. Confirm department, purpose, role, data freshness, degradation, and profile.
3. Review bounded saved views such as recently changed, correction pending,
   reconstruction incomplete, evidence unavailable, or review required.
4. Sort only through server-authoritative allowlisted fields.
5. Open a timeline by opaque ID.

Required states: loading, empty, partial, stale, denied, degraded, failed, and
recovered. Counts are summaries, not client-side joins.

## Workflow 2: Inspect The Current Investigation State

1. Read title/neutral label, lifecycle, current revision, record count, last
   record time, event-time range, and completeness.
2. Inspect typed entry-family counts without collapsing their meanings.
3. Review active corrections, retractions, relationships, and unresolved impact
   warnings.
4. Follow authorized handoffs to Intelligence Center, GIS Center, or Evidence
   Desk using opaque references and no sensitive URL state.

The summary never presents a hypothesis, candidate, review, or digest as an
established fact.

## Workflow 3: Navigate The Authoritative Timeline

1. Default to record-sequence ordering.
2. Apply bounded entry-family, state, actor-class, or time filters.
3. Navigate server pages with stable first/last entry anchors.
4. Expand one row for field-minimized metadata and relationships.
5. Preserve focus when rows are refreshed, filtered, or paged.
6. Optionally switch to event-time view with an explicit asserted-time warning.

The semantic table/list is authoritative. A visual lane is optional and
subordinate. Unknown event times and ties remain visible.

## Workflow 4: Reconstruct Through An Exact Revision

1. Select a known revision from the server-provided bounded range.
2. Choose record-sequence or event-time presentation.
3. Request a deterministic reconstruction.
4. Verify returned revision, digest/profile, included count, completeness, and
   limitations before showing results.
5. View reconstructed state and entries.
6. Compare with current or another permitted revision.
7. Inspect later corrections/retractions excluded from the selected state.

No client builds an authoritative reconstruction by replaying cached events.

## Workflow 5: Compare Two Revisions

1. Select base and target revisions, with base not later than target.
2. Receive a server-authoritative or generated-contract comparison.
3. Review added entries, new corrections, lifecycle changes, relationship
   revisions, evidence-reference changes, and limitation changes.
4. Use text labels for added, removed-from-current-view, changed, unchanged,
   unavailable, and unknown.
5. Follow exact entries rather than a generated narrative.

Historical records are never described as deleted merely because they are not
active in the target projection.

## Workflow 6: Review A Correction Or Retraction

1. Open the immutable original entry.
2. Open the correcting or retracting entry and reason.
3. Compare exact affected fields and versions.
4. Inspect impact closure across hypotheses, alerts, reviews, relationships,
   evidence references, and previews.
5. Review each impact state and unresolved failures.
6. Return to the timeline with both records visible.

A retraction changes reliance state; it does not erase the source record.

## Workflow 7: Inspect Investigation Relationships

1. Load bounded timeline relationships for the current scope.
2. Review canonical, merged, alias, related, reopened, or superseding links.
3. Use the authoritative edge table.
4. Optionally inspect a bounded graph projection.
5. Open another timeline only after independent authorization.

Graph position and visual proximity have no semantic meaning.

## Workflow 8: Triage Evidence References

1. Enter Evidence Desk through an authorized timeline handoff or scoped list.
2. Confirm evidence-reader capability independently from investigation access.
3. Review reference role, source class, availability, latest integrity state,
   provenance completeness, custody-gap state, and limitations.
4. Filter and page using server-authoritative fields.
5. Open one reference by opaque ID.

No locator, path, media thumbnail, payload preview, or download action appears.

## Workflow 9: Inspect Evidence Identity And Availability

1. Review immutable reference identity and source-version assertion.
2. Review expected digest/size/profile only when supplied and authorized.
3. Inspect latest availability observation and observation history summary.
4. Review supersession, correction, retraction, and timeline roles.
5. Read explicit `source_not_resolved` and `media_not_rendered` limitations.

Availability does not imply integrity, authenticity, custody, or admissibility.

## Workflow 10: Inspect Integrity History

1. Open the append-only integrity-assessment table.
2. Compare observation time, assessor class, algorithm, canonicalization or
   content profile, expected digest state, observed result, and limitations.
3. Identify mismatch, unsupported, unavailable, or superseded assessments.
4. Follow provenance links without resolving the source.

The UI never collapses multiple observations into an unqualified `verified`
badge.

## Workflow 11: Inspect Provenance And Custody

1. Load a bounded provenance bundle and closure status.
2. Review entity, activity, and agent tables.
3. Review typed edge table and ordering/consistency results.
4. Optionally open the bounded graph projection.
5. Inspect custody assertions and visible gaps separately.
6. View generated PROV projection status without import or conformance claims.

An H-CAM access event, audit record, or provenance edge is not silently
converted into a custody event.

## Workflow 12: Review Retention Evaluation Preview

1. Open a generated-only policy preview.
2. Review opaque policy reference/version, evaluated record classes, effective
   interval, evaluator, and generated result.
3. Inspect unknown policy, conflicting policy, active hold, and unavailable
   classification states.
4. Close the preview.

No period is built into the client and no execution control exists.

## Workflow 13: Review Hold Overlay Preview

1. Review the exact bounded target set or query snapshot.
2. Review authority reference, reason class, start/review state, and conflicts.
3. Confirm that hold status does not grant read access.
4. Review an inert release projection when present.

Wildcard department or tenant holds are rejected by the contract projection.

## Workflow 14: Review Deletion Simulation

1. Review generated deletion intent, exact target classes, and policy inputs.
2. Review per-target simulated `eligible`, `blocked`, `not_found`, `residual`,
   or `unknown` outcomes.
3. Inspect unresolved backups/caches/external-source limitations.
4. Close the simulation.

The page says `simulation only`; there is no delete command and no statement
that all copies are gone.

## Workflow 15: Review Export Manifest Preview

1. Review purpose, recipient class, scope, expiry, profile, and exact revision.
2. Inspect reference-only included and excluded items with reason codes.
3. Inspect correction/retraction closure, contradictions, unavailable sources,
   and completeness.
4. Review canonical profile and digest metadata.
5. Close the preview.

No source content, download, print, sign, approve, send, or delivery action is
available.

## Workflow 16: Recover From Concurrent Change

1. Submit a separately authorized future mutation with ETag, expected revision,
   semantic command identity, reason, and idempotency identity.
2. On `412` or typed conflict, preserve the bounded draft in memory.
3. Fetch current authoritative state.
4. Show exact differences and stale dependencies.
5. Require explicit reconsideration or cancellation.
6. Clear the draft on logout, scope change, capability loss, or expiry.

Last-write-wins behavior is prohibited.

## Workflow 17: Respond To Event Invalidation

1. Receive a versioned event containing only scoped opaque identity/version.
2. Verify event type, version, department scope, and monotonic freshness.
3. Mark affected queries stale.
4. Fetch authoritative HTTP state.
5. Reconcile focus, pagination anchor, and selected entry.

Events never append client-authored timeline entries or patch evidence state
directly.

## Workflow 18: Change Department, Purpose, Or Session

1. Stop prefetch and background refresh.
2. Tear down investigation and evidence subscriptions.
3. Clear sensitive query caches, graph data, comparison state, and drafts.
4. Re-evaluate navigation and capabilities.
5. Render denied or empty states without leaking prior-scope counts.

## Shared UI States

Every list, detail, graph, preview, and workflow supports:

- loading with stable dimensions;
- empty with current filter and scope;
- partial with missing component reasons;
- stale with last authoritative observation time;
- degraded with retained functional table access;
- denied without confirming resource existence;
- conflict with recoverable in-memory draft;
- failure with sanitized typed reason;
- correction/retraction with visible historical context;
- recovery with focus and selection restoration.

## Cross-Portal Handoffs

| From | To | Payload | Rule |
| --- | --- | --- | --- |
| Command Center | Investigation Center | opaque timeline ID | independent authorization |
| Intelligence Center | Investigation Center | opaque alert/hypothesis reference | no truth promotion |
| Investigation Center | GIS Center | bounded opaque spatial query reference | no sensitive URL payload |
| Investigation Center | Evidence Desk | opaque evidence-reference ID | independent evidence authorization |
| Investigation Center | Camera workspace | opaque camera/event reference | no media autoplay or source resolution |
| Evidence Desk | Investigation timeline | opaque timeline/entry ID | independent investigation authorization |

## Explicitly Absent Features

- source locator display or resolution;
- media, image, document, waveform, or thumbnail rendering;
- copy, download, print, export, share, email, or clipboard payload action;
- legal certificate generation, digital signing, trusted timestamping, or
  admissibility assessment;
- case-system creation or synchronization;
- retention-period selection or legal-policy editing;
- hold activation/release, deletion, disposition, export approval, or delivery;
- external PROV import;
- AI-generated narrative, evidence ranking, guilt score, or automatic finding;
- notification, dispatch, enforcement, or autonomous action.
