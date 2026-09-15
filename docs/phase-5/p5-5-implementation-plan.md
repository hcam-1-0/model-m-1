# P5.5 Bounded Implementation Plan

Status date: 2026-09-09

Status: proposed; owner decisions, reconciled planning acceptance, and start authorization required

## Objective

Build a generated-only Investigation Center and separately authorized Evidence
Desk that make accepted Phase 4.5 timelines, reconstruction, corrections,
evidence references, integrity, provenance, relationships, and non-operative
policy previews usable without resolving source material or making legal,
identity, authenticity, guilt, or evidentiary claims.

## Frozen Product Weight

| Workstream | Points | Exit evidence |
| --- | ---: | --- |
| P5.5-W1 Consumer contracts and generated fixtures | 2.0 | schemas, fixtures, gap markers, prohibited-data guards |
| P5.5-W2 Investigation overview and authoritative timeline | 2.5 | routes, bounded pages, dual-clock chronology, states, handoffs |
| P5.5-W3 Reconstruction, comparison, corrections, and relationships | 2.5 | exact revision, typed diff, impact closure, graph/table parity |
| P5.5-W4 Evidence Desk, integrity, provenance, and custody | 2.5 | orthogonal state matrix, histories, bounded graph and tables |
| P5.5-W5 Non-operative policy previews and disabled bridges | 1.5 | retention/hold/deletion/export previews, case/PROV boundaries |
| P5.5-W6 Authorization, concurrency, invalidation, and handoffs | 1.5 | scope, purpose, ETag, idempotency, conflict, cache teardown |
| P5.5-W7 Accessibility, security, profiles, and signals | 1.0 | keyboard/table equivalence, threat tests, profile invariance |
| P5.5-W8 Validation, evidence, and acceptance | 1.5 | generated workloads, browser/build/regression evidence, acceptance |
| **Total** | **15.0** | |

Technical implementation can earn at most **14/15 (93.3333%)**. Exact owner
acceptance earns the final **1 point**, taking Phase 5 from **63/100** to
**78/100 (78.0000%)**. Planning and owner selections earn no product points.

## Delivery Sequence

### W1: Consumer Contracts And Generated Fixtures

Proposed implementation:

- add `@hcam/investigation-evidence-domain` and generated contract schemas;
- define timeline page, entry page, revision list, reconstruction, comparison,
  correction impact, relationship, evidence summary/detail, integrity history,
  provenance/custody, policy preview, and disabled bridge projections;
- record producer status on every contract as stable, partial, absent, or
  blocked;
- generate non-issuable C1/C10/C50 investigations with exact seeds;
- include corrections, retractions, unknown times, unavailable references,
  digest mismatch, partial provenance, custody gaps, policy conflicts, residual
  deletion outcomes, and incomplete export closure;
- recursively reject real names, plates, phone/email/address, Government/case
  identifiers, locators, URLs, paths, credentials, media, documents, and source
  payloads.

No backend route or migration is added.

### W2: Investigation Overview And Authoritative Timeline

Proposed implementation:

- add connected Investigation Center portal and navigation capability;
- implement workload overview, bounded saved views, freshness, producer-gap,
  partial, and degradation states;
- add investigation list/detail and authoritative paginated timeline table;
- support record-sequence default and explicitly qualified event-time view;
- implement stable row anchors, page navigation, filters, selected entry detail,
  and focus restoration;
- add Command, Intelligence, GIS, Camera, and Evidence Desk opaque handoffs;
- keep all mutation controls absent unless exact producer/start requirements are
  later met.

### W3: Reconstruction, Comparison, Corrections, And Relationships

Proposed implementation:

- implement exact through-revision selection and reconstructed-state detail;
- validate revision, manifest digest/profile, completeness, and limitations;
- render typed field-level comparison between two revisions;
- show later corrections/retractions excluded by historical reconstruction;
- render original plus correction/retraction and per-target impact closure;
- display unresolved impacts as stale/incomplete downstream state;
- render bounded relationship graph with authoritative node/edge table;
- prohibit client replay as authoritative reconstruction.

### W4: Evidence Desk, Integrity, Provenance, And Custody

Proposed implementation:

- add independently authorized Evidence Desk routes;
- implement reference inventory and detail using a strict field allowlist;
- show reference identity, availability, digest observation, provenance closure,
  custody state, signature/timestamp observation, access, and legal assessment
  as separate rows;
- implement append-only integrity-assessment history;
- render bounded entity/activity/agent provenance graph and node/edge tables;
- render supplied custody events and gaps separately from audit/access history;
- display source-not-resolved and media-not-rendered states persistently;
- include no source resolver, media/document renderer, hash verifier, or
  cryptographic operation.

### W5: Non-Operative Policy Previews And Disabled Bridges

Proposed implementation:

- render generated retention evaluation and conflict states;
- render exact-target hold overlay and inert release projection;
- render deletion simulation with per-target outcomes and residuals;
- render purpose-bound reference-only export manifest, inclusion/exclusion
  ledger, contradictions, corrections, and completeness;
- render disabled case-management bridge status;
- render generated lossy PROV projection status and tables;
- make `preview_only`, `generated_only`, and `execution_unavailable` persistent;
- include no Run/Delete/Hold/Release/Export/Download/Print/Sign/Send command.

### W6: Authorization, Concurrency, Invalidation, And Handoffs

Proposed implementation:

- apply department, role, purpose, capability, and current-session checks to
  route, query, detail, graph, and handoff state;
- use scope-bound query keys and no sensitive URL state;
- model strong ETag, expected revision/digest, semantic command ID, delivery ID,
  reason, and receipt for future mutations;
- preserve bounded drafts in memory on conflict and require reconsideration;
- use versioned events only to invalidate exact query families;
- confirm state over HTTP and recover from event gaps with bounded refetch;
- cancel requests and clear cache/drafts/subscriptions on logout or scope loss.

### W7: Accessibility, Security, Profiles, And Signals

Proposed implementation:

- provide native semantic list/table detail for every visual timeline/graph;
- implement logical keyboard order, visible focus, skip/navigation landmarks,
  status announcements, and text-based state distinctions;
- verify that pagination, filtering, expansion, conflict refresh, and route
  return preserve a sensible focus anchor;
- enforce low-resource functional completeness and profile-invariant truth;
- add low-cardinality sanitized signals only;
- test all 56 threats and explicit absent-feature controls;
- preserve CSP and avoid raw HTML/JSON/source rendering.

### W8: Validation, Evidence, And Acceptance

Proposed implementation evidence:

- schema and generated-fixture validation;
- exactly bounded generated contract matrix defined by the future start package;
- C1/C10/C50 deterministic workload and replay evidence;
- unit, component, contract, integration, browser, keyboard, accessibility,
  concurrency, invalidation, scope isolation, and cache teardown tests;
- all-portal typecheck, lint, formatting, build, Storybook, and bundle checks;
- dependency inventory, lockfile invariance unless separately amended, license,
  audit, and vulnerability evidence;
- complete repository regression and PostgreSQL limitations;
- technical commit, evidence package, hashes, limitations, and exact owner
  acceptance proposal.

W8 earns **0.5 technical point** after complete evidence and **1 owner-acceptance
point** after exact acceptance.

## Proposed Frontend Structure

```text
frontend/
  apps/
    investigation-center/
  packages/
    investigation-evidence-domain/
      src/contracts/
      src/fixtures/
      src/queries/
      src/timeline/
      src/reconstruction/
      src/evidence/
      src/provenance/
      src/policy-previews/
      src/security/
    app-shell/                 # additive navigation only
    test-fixtures/             # generated-only additions
  tests/
    browser/investigation-*.spec.ts
```

The exact path allowlist must be sealed in the future start package. This plan
does not authorize creating these paths.

## Generated Scenario Matrix

Minimum scenario families:

1. single current timeline with no evidence references;
2. multi-entry dual-clock timeline with unknown/tied event times;
3. exact historical reconstruction with later correction;
4. retraction that remains visible in current and historical views;
5. partial correction impact with stale downstream review;
6. merge/alias/reopen relationship with inaccessible endpoint;
7. evidence reference with unknown availability;
8. digest match that retains authenticity/legal unknown states;
9. mismatch and unavailable integrity observations;
10. partial/cyclic/over-bound provenance projections;
11. custody history with explicit gaps;
12. missing/expired/conflicting retention policy;
13. exact-target hold and wildcard-hold rejection;
14. deletion simulation with blocked and residual targets;
15. export preview with contradictions and incomplete closure;
16. ETag conflict and reconsideration with memory-only draft;
17. event gap followed by authoritative HTTP recovery;
18. department/purpose/capability/session transition purge;
19. dynamic-profile equivalence;
20. keyboard/focus/accessibility equivalence.

C1 validates one investigation, C10 validates mixed workflows and bounded
parallel navigation, and C50 validates scheduling/resource behavior with fixed
generated fixtures. None is a production capacity claim.

## Start-Package Requirements

A future P5.5 start package must bind:

- accepted reconciled owner decisions;
- exact allowed source/test/docs/evidence paths;
- exact existing dependency and lockfile digests;
- any separately justified dependency amendment;
- exact contract/fixture counts and workload seeds;
- page, string, entry, graph, comparison, and cache bounds;
- browser, coverage, accessibility, build, bundle, security, regression, and
  evidence thresholds;
- prohibited-data and absent-feature scanners;
- accepted producer gaps and visible limitation requirements;
- local commit limits and no-push boundary;
- explicit stop conditions.

## Acceptance Criteria

P5.5 can be accepted only when:

1. all selected owner decisions are implemented exactly;
2. all eight workstreams pass their frozen evidence;
3. low-resource mode retains all records, states, limitations, and keyboard
   workflows;
4. no source reference is resolved and no source/media/document is rendered,
   copied, downloaded, exported, printed, deleted, held, released, or modified;
5. integrity, provenance, custody, access, and legal assessment remain separate;
6. record sequence and event-time semantics are unambiguous;
7. historical revisions, corrections, retractions, impacts, and limitations are
   deterministic and visible;
8. every graph/visual has an authoritative table/list equivalent;
9. policy previews are generated-only and non-operative;
10. all 36 producer gaps remain accurately classified;
11. all 56 threats have generated/static/browser coverage or an explicit
    residual limitation;
12. complete validation and evidence hashes are recorded;
13. exact owner acceptance is recorded separately.

## Stop Conditions

Stop closed on an unapproved dependency or lockfile change, backend route or
migration, real identifier or source locator, network/source/media access,
source rendering, evidence operation, legal-policy selection, missing scope or
purpose, integrity/legal truth collapse, client-authoritative reconstruction,
unbounded query/graph/timeline, missing table equivalence, dynamic-profile
semantic downgrade, operational action, container/deployment action, or remote
Git activity.
