# P5.5 Contract Gap Matrix

Status date: 2026-09-09

Status: planning complete; no producer gap is silently implemented by the client

## Classification

| Class | Meaning |
| --- | --- |
| Stable | Accepted producer or Phase 5 consumer contract can be used as planned |
| Adapt | Accepted data exists but needs an additive bounded consumer projection |
| Gap | Required producer read/aggregate/event contract is absent |
| Blocked | Capability is deliberately unavailable in P5.5 |

## Accepted Stable Handoff

The following accepted Phase 4.5 contracts form the source model:

- `InvestigationTimelineV2` and immutable timeline revisions;
- `TimelineEntryV2` and dual-clock temporal assertions;
- exact-revision `ReconstructionV1`;
- `EvidenceReferenceV2` and append-only integrity assessments;
- typed provenance bundle and generated lossy PROV projection;
- correction command, impact set/job, review, and relationship revision;
- retention evaluation, hold overlay, deletion receipt, and export manifest;
- disabled case-management bridge;
- idempotent command receipt, audit, and transactional outbox behavior.

Existing routes support timeline create/list/detail, entry append,
reconstruction, lifecycle revision, evidence registration/list, integrity and
provenance submission, correction, review, relationship, generated hold,
retention evaluation, deletion simulation, and export preview. Runtime remains
generated-only, default-off, and forbidden in production.

## Producer And Consumer Gaps

| ID | Needed contract | Current state | P5.5 treatment |
| --- | --- | --- | --- |
| P5.5-G01 | Paginated/filterable timeline list with total and cursor | list returns bounded internal collection without UI pagination contract | Gap: generated adapter only; runtime producer required later |
| P5.5-G02 | Investigation workload aggregates and freshness | absent | Gap: generated fixture; no client join |
| P5.5-G03 | Timeline entry GET list with page/cursor/order | append route exists; read collection route absent | Start-blocking consumer gap |
| P5.5-G04 | Timeline revision history GET | persistence exists; route absent | Start-blocking reconstruction navigation gap |
| P5.5-G05 | Available reconstruction revision range and bounds | request accepts revision; discovery contract absent | Adapt through generated capability contract |
| P5.5-G06 | Server-authoritative revision comparison | absent | Generated deterministic projection only |
| P5.5-G07 | Correction list/detail/history reads | correction write exists | Mutation blocked; generated read fixture only |
| P5.5-G08 | Correction impact job/status/per-target reads | persistence/service internals exist | Gap: generated impact projection |
| P5.5-G09 | Review and disposition history reads | review write exists | Gap: generated append-only history |
| P5.5-G10 | Relationship list/detail/closure reads | relationship write and persistence exist | Gap: generated bounded projection |
| P5.5-G11 | Scoped evidence-reference inventory across timelines | per-timeline list exists | Adapt; no unbounded client join |
| P5.5-G12 | Evidence-reference detail GET | service read exists; route absent | Start-blocking Evidence Desk gap |
| P5.5-G13 | Integrity-assessment history GET | write exists; persistence stores history | Start-blocking integrity page gap |
| P5.5-G14 | Provenance bundle/closure GET | submission exists; persistence stores bundle | Start-blocking provenance page gap |
| P5.5-G15 | Custody-event contract and history | no dedicated accepted contract | Gap: show unavailable, do not infer from audit |
| P5.5-G16 | Orthogonal evidence-state summary | fields exist across records | Add generated consumer projection without truth collapse |
| P5.5-G17 | Field-minimized source identity projection | evidence contract may carry bounded source metadata | Add strict consumer allowlist; never display locator |
| P5.5-G18 | Lifecycle/disposition revision history GET | timeline revisions exist; dedicated view absent | Generated fixture only |
| P5.5-G19 | Merge/reopen command and history routes | relationship/revision primitives exist | No mutation; generated history projection |
| P5.5-G20 | Retention evaluation history GET | write/read internal service exists | Generated preview fixture only |
| P5.5-G21 | Hold list, detail, review, and release projections | create/list internals exist; release absent | Preview only; activation/release blocked |
| P5.5-G22 | Deletion simulation retrieval and revision | response exists at command time | Generated retained preview fixture only |
| P5.5-G23 | Export preview retrieval, revision, and completeness | preview creation exists | Generated reference-only preview fixture |
| P5.5-G24 | Unified policy-preview capability/status | absent | Add generated consumer capability contract |
| P5.5-G25 | Case-bridge status contract | accepted disabled contract exists | Stable disabled status; no adapter |
| P5.5-G26 | Generated PROV projection read contract | projection function exists; no route | Generated fixture only; import blocked |
| P5.5-G27 | Uniform RFC 9457 typed problems | error translation exists but not frozen for all reads | Add consumer problem union; preserve unknown failure |
| P5.5-G28 | Cursor, page, sort, and filter schema | absent for timeline/evidence reads | Start-blocking generated contract |
| P5.5-G29 | Strong ETag/current revision on all detail reads | timeline mutation path supports version metadata | Adapt; disable mutation where current ETag absent |
| P5.5-G30 | Investigation/evidence invalidation event catalogue | Phase 4 outbox names exist | Add consumer allowlist and version policy |
| P5.5-G31 | Event sequence/gap recovery contract | absent | Poll/refetch fallback; no event authority |
| P5.5-G32 | Intelligence Center to investigation typed handoff | generic accepted handoff exists | Add opaque generated reference projection |
| P5.5-G33 | Investigation to GIS bounded spatial handoff | P5.2 GIS domain exists; investigation projection absent | Generated handoff only; no map producer join |
| P5.5-G34 | Investigation to camera/live opaque handoff | P5.3 workspace exists | Reference only; no media autoplay or resolution |
| P5.5-G35 | Separate audit-view projection | audit subsystem exists; P5.5 access not defined | Blocked pending P5.6 administration/security work |
| P5.5-G36 | Canonical localized reason/status catalogue | partial shared error/i18n foundation exists | Add generated P5.5 catalogue; canonical codes unchanged |

## Gap Closure Priority

### Start-Blocking Consumer Contracts

The P5.5 start package must define generated schemas for G01 through G06, G08
through G18, G24, G27 through G34, and G36. They permit generated UI work only
and must identify their runtime producer status as absent or partial.

### Mutation-Blocking Producer Contracts

G07, G09, G19, G21, G22, and G23 prevent operational mutation or policy action.
P5.5 may render generated previews and future command shapes, but all commands
remain unavailable. Missing ETag, revision, reason, purpose, authorization,
idempotency, receipt, or audit contracts also disable the action.

### Runtime-Blocking Contracts

G03, G04, G12, G13, G14, G15, G20, G21, G22, G23, G26, G29, and G31 prevent a
production-capable Investigation/Evidence runtime. Generated fixtures cannot be
described as backend integration evidence.

## No-Downgrade Rule

The client must not:

- fetch all records to synthesize pagination, counts, relationships, or closure;
- infer custody from audit, integrity from availability, authenticity from a
  digest, or legal state from any technical record;
- reconstruct authoritative history from events or cached list responses;
- activate a command because a visual control or old contract shape exists;
- expose source locators or resolve references to compensate for missing
  metadata;
- hide missing records, contradictions, corrections, retractions, residuals,
  or limitations in low-resource mode;
- treat generated adapters as accepted production producers.
