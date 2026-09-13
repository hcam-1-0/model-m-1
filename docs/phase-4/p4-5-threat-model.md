# P4.5 Investigation Timeline And Evidence Threat Model

Status date: 2026-09-05

Status: planning-only. Controls are proposed and non-effective. This document
does not authorize evidence access, copying, holds, deletion, exports, real
investigations, runtime execution, or deployment.

## Security Objective

P4.5 must let an authorized reviewer reconstruct what H-CAM knew, inferred,
displayed, reviewed, changed, and recorded at a point in time without confusing
that record with the underlying source evidence. It must preserve provenance,
integrity state, chronology, authorization, and uncertainty while minimizing
data and preventing the software from making legal or evidentiary claims.

## Protected Assets

- immutable timeline-entry versions and aggregate revisions;
- evidence identities, source locators, digests, verification records, and
  provenance edges;
- hypothesis, alert, review, action, correction, retraction, merge, reopen,
  disposition, retention, hold, deletion, and export chronology;
- department, purpose, role, policy, actor/service, transaction, and request
  attribution;
- canonical manifests, signatures/timestamp receipts when separately enabled,
  and algorithm metadata;
- access, mutation, policy-evaluation, and export audit records;
- source confidentiality and the fact that media is not copied by default.

## Trust Boundaries

1. **Source systems:** cameras, media stores, event stores, external providers,
   and records systems remain outside P4.5 authority.
2. **Accepted H-CAM intelligence:** generated events, hypotheses, alerts,
   reviews, and provider candidates are referenced by exact immutable versions.
3. **Investigation service:** validates commands, assigns ordered identities,
   and commits aggregate revision, timeline entry, provenance, audit, and outbox
   atomically.
4. **Policy services:** authorize purpose, access, retention class, hold,
   deletion eligibility, and export profile. Missing policy fails closed.
5. **Workers:** propagate corrections, reconstruct projections, evaluate due
   retention work, and build manifests through bounded leased jobs.
6. **Persistence:** PostgreSQL row security and append-only controls provide
   defense in depth; object/media stores are references, not implicit trust.
7. **Operator/API boundary:** all reads and commands are department, role,
   purpose, reason, and version scoped.
8. **Export boundary:** an export is a new controlled derivative, never a direct
   database dump or raw path handoff.

## Threat Actors And Failure Sources

- unauthorized or over-privileged users;
- authorized insiders acting outside purpose or policy;
- compromised service credentials or worker identity;
- malformed, stale, hostile, or cross-department source references;
- software defects, retries, races, partial transactions, and clock skew;
- policy misconfiguration or missing policy;
- unavailable, altered, replaced, or deleted source content;
- compromised exports, caches, backups, or downstream consumers;
- cryptographic algorithm aging or canonicalization disagreement.

## Threat Register

| ID | Threat | Consequence | Required control |
| --- | --- | --- | --- |
| T45-01 | Timeline row update or deletion | History is rewritten | Append-only database permissions, restrictive foreign keys, revision commands only, invariant tests |
| T45-02 | Retry creates duplicate entries | False chronology and inflated evidence | Semantic command ID plus delivery ID, unique constraints, idempotent receipt |
| T45-03 | Concurrent writers reuse sequence | Ambiguous order | Aggregate lock/version check, database-assigned monotonic sequence, transactional commit |
| T45-04 | Event-time sorting invents causality | Misleading reconstruction | Multi-clock chronology, trust/precision state, aggregate sequence, causal edges only when proven |
| T45-05 | Digest is presented as authenticity | False evidentiary confidence | Separate integrity, provenance, custody, availability, signature, and legal-assessment states |
| T45-06 | Source content changes at same locator | Reference substitution | Immutable source-version identity, expected digest/size/profile, fresh verification record, mismatch state |
| T45-07 | Media is copied during reference registration | Excess collection and retention | Reference-only default, payload field denial, no source fetch in baseline, separate copy authorization |
| T45-08 | Cross-department evidence edge | Information disclosure | Same-department validation, forced RLS, scoped identifiers, direct SQL isolation tests |
| T45-09 | Provenance graph cycle or bomb | False lineage or resource exhaustion | Closed edge taxonomy, DAG/cycle policy, node/edge/depth/fanout/time bounds |
| T45-10 | Unattributed service activity | No accountability | Typed agent, delegated role, policy, transaction, software version, and activity digest |
| T45-11 | Correction mutates original | Loss of historical truth | New correction entity and typed edge; immutable predecessor and impact closure |
| T45-12 | Correction propagation is partial | Stale alerts, timelines, indexes, exports | Durable idempotent impact jobs, per-target outcomes, retry/dead-letter, completeness state |
| T45-13 | Retraction is treated as deletion | Prior reliance disappears | Retraction is a new assertion; source and previous interpretation remain with visible state |
| T45-14 | Merge deletes the source timeline | Lost provenance and access errors | Merge relationship plus canonical alias; both aggregates remain immutable and reconstructable |
| T45-15 | Reopen silently changes closed state | Unauthorized investigation continuation | ETag, permission, reason, policy, append-only revision, explicit reopen event |
| T45-16 | Hold grants broader access | Purpose bypass | Hold affects deletion eligibility only; access authorization remains independent |
| T45-17 | Broad hold never expires or cannot be reviewed | Indefinite over-retention | Exact target closure, authority, reason, review state, separate release, conflict reporting |
| T45-18 | Deletion occurs under unknown hold | Destruction contrary to policy | Atomic policy/hold recheck immediately before execution; conflict stops closed |
| T45-19 | Deletion receipt claims all copies are gone | False assurance | Record exact targets/outcomes/residuals; never claim universal deletion |
| T45-20 | Export omits contradicting/correcting evidence | Biased package | Deterministic closure rules, inclusion/exclusion ledger, correction/retraction resolution, completeness state |
| T45-21 | Export includes unauthorized source data | Disclosure | Purpose-bound field projection, source-copy default deny, per-item authorization, preflight |
| T45-22 | Export changes after approval | Integrity failure | Immutable manifest version, canonical digest, optional separately authorized signature/timestamp profile |
| T45-23 | Export replay to a new recipient/purpose | Secondary-use violation | Bind purpose, recipient class, scope, expiry, nonce/manifest ID, policy and authorization IDs |
| T45-24 | Audit log is mistaken for evidence | Wrong retention and trust | Separate audit, security, operational, investigation, and evidence record classes |
| T45-25 | Sensitive IDs leak through metrics/errors | Privacy or investigative disclosure | Low-cardinality labels, opaque IDs, bounded reason codes, no payload/locator in telemetry |
| T45-26 | Unknown fields smuggle paths, URLs, or content | Source access and exfiltration | Closed schemas, recursive prohibited-field scan, size/depth/string/array bounds |
| T45-27 | Hash/canonicalization algorithm ages or drifts | Verification failure | Named profile/version, test vectors, algorithm registry, renewal metadata, no silent fallback |
| T45-28 | Backup or cache outlives deletion record | Residual unreported copy | Storage-class inventory, per-target outcomes, residual state, separate backup policy binding |
| T45-29 | Source becomes unavailable | Reconstruction overstates completeness | `unavailable` integrity/availability state; retain reference/provenance, abstain from verification claims |
| T45-30 | Legal/policy configuration is absent | System invents authority | Fail closed; no built-in periods, legal conclusions, certification, hold, deletion, or export defaults |

## Abuse Cases

### Backdating An Operator Observation

An operator submits an old `occurred_at` to place an observation before a
critical event. The system records the asserted occurrence time separately from
trusted receive/record time, clock source, precision, and actor. Ordering views
may show both occurrence and record sequence. Backdating cannot change prior
sequence or causal relations.

### Replacing A Source At A Stable URL

A referenced object at a locator changes after review. The old evidence entity
retains its expected digest, size, source-version token, and verification
history. A new verification produces either a new matching observation or a
mismatch/unavailable state. It does not rewrite the old verification.

### Removing Contradictory Material From An Export

A requester selects only supportive entries. The export builder computes the
authorized provenance and correction closure from a versioned profile. Every
included and excluded reference receives a typed reason. A manifest with
unresolved contradictions or incomplete closure is marked incomplete and
cannot claim a complete investigation reconstruction.

### Holding An Entire Department

A user attempts a wildcard hold. The baseline denies wildcard targets. A hold
must bind an exact bounded target set or a policy-defined query snapshot, named
authority, purpose, reason, start, review state, and owner. Even an active hold
does not add read access.

### Deleting A Closed Timeline

Closing is not deletion. No product command deletes a timeline aggregate or
entry. An authorized retention workflow may evaluate separately classified
derived payloads or references, but it records outcomes and leaves the minimum
policy-authorized lifecycle and deletion evidence. Exact behavior requires a
future policy decision.

## Mandatory Invariants

- source, event, hypothesis, alert, review, action, correction, retraction,
  retention, hold, deletion, and export records use distinguishable types;
- no mutable payload can be addressed only by a stable locator;
- every digest names its algorithm and canonicalization/content profile;
- one timeline sequence is gap-tolerant but never reused or reordered;
- a timeline entry can have multiple evidence roles, including supports,
  contradicts, contextualizes, supersedes, retracts, and unavailable;
- previous versions are never overwritten by correction, merge, reopen,
  disposition, retention, deletion, or export;
- references are not authorization grants;
- policy denial, missing policy, integrity mismatch, cross-scope reference, and
  graph inconsistency are non-retryable until state changes;
- transient source unavailability never becomes `verified` through retry;
- holds block eligible deletion but do not block correction or add access;
- exports are immutable derivatives and never direct mutable views;
- source media remains outside generated baseline tests and storage;
- no output says `admissible`, `authentic`, `certified`, or `all copies deleted`
  as a machine-derived fact.

## Validation Strategy

Generated tests must cover duplicate delivery, idempotency conflict, sequence
races, timestamp disagreement, unknown time, source replacement, digest
mismatch, unavailable source, cross-department references, graph cycles,
excessive depth/fanout, orphan edges, duplicate entity IDs, correction chains,
correction cycles, retraction, partial propagation, merge chains, alias loops,
reopen conflicts, overlapping holds, expired policy, hold/deletion race,
residual copies, incomplete export closure, recipient/purpose mismatch,
canonicalization drift, algorithm deprecation, malformed manifests, oversized
payloads, prohibited source content, and telemetry redaction.

The generated corpus must be non-issuable, contain no real person, vehicle,
case, Government identifier, source locator, media, document, or external data,
and regenerate byte-for-byte from a fixed seed and generator digest.

## Residual Risks Requiring Deployment Decisions

- legal applicability and court procedure;
- physical or external-system custody not observable by H-CAM;
- source-store durability, backup, sanitization, and deletion behavior;
- key, certificate, timestamp authority, and cryptographic renewal operations;
- privileged database/storage administrators;
- cross-system clock quality and source authenticity;
- authorized recipient behavior after export;
- disaster recovery and geo-replication retention interactions;
- actual departmental roles, approval separation, and emergency access.

These risks cannot be closed by generated P4.5 implementation evidence.
