# P4.1 Generated-Event Correlation Contract Catalog

Status: local generated-only implementation in validation.

## Boundary

P4.1 consumes a typed, read-only projection of accepted Phase 3 event outbox
records. It does not publish, acknowledge, delete, or otherwise mutate those
records. Every input must resolve to the exact stream, camera, and department
already recorded by H-CAM and must remain generated-only.

The adapter recognizes only the explicitly catalogued observation, track
lifecycle, line-crossing, zone-entry, zone-exit, dwell-threshold, and occupancy
threshold contracts. Unknown event types, schema versions, fields, scopes, and
payloads fail closed. Canonical input envelopes are limited to 64 KiB.

## Contract Families

| Family | Version | Purpose |
|---|---|---|
| Ingress | `correlation-ingress-event.v1` | Sanitized generated event accepted from the closed Phase 3 adapter |
| Profile | `correlation-profile.v1` | Bounded partition, event-time, window, evidence, and lane policy |
| Receipt | `correlation-receipt.v1` | Durable accepted, duplicate, conflict, late, gap, skew, policy, or capacity result |
| Replay | `correlation-replay-binding.v1` | Exact event-order, profile, clock, partition, and window version binding |
| Window | `correlation-window.v1` | Fixed, tumbling, or generated-session event-time window |
| Lane | `lane-capability.v1`, `lane-result.v1` | Required deterministic CPU lane and unavailable optional-lane contracts |
| Arbitration | `arbitration-result.v1` | Deterministic veto, disagreement preservation, uncertainty, and abstention |
| Hypothesis | `correlation-hypothesis.v2` | Generated-only, nonoperational, mandatory-review evidence graph |
| Projection | `correlation-flat-projection.v1` | Digest-bound read model rebuildable from the graph |
| Revision | `hypothesis-revision.v1` | Append-only correction, expiry, supersession, or retraction record |
| Batch | `correlation-batch-result.v1` | Canonical deterministic run result and replay identity |

The machine-readable source is
`contracts/phase-4/p4-1/correlation-contracts.json`. The live Phase 4 catalog
is `contracts/phase-4/intelligence-contracts.json`.

## Ordering And Replay

Events are ordered by declared event time and a stable event identifier.
Profiles define explicit watermarks, allowed lateness, future-clock skew,
partition dimensions, and fixed resource limits. Gaps, late events, conflicts,
duplicates, policy rejection, and capacity rejection remain visible outcomes;
none are silently discarded.

Replay identity includes the original receipt order, canonical event digests,
the complete profile configuration digest, and explicit event, clock,
partition, and window semantic versions. A change to ordering, time,
configuration, or semantics produces a different run identity.

## AMEC Lanes

The deterministic CPU lane is the only executable lane in P4.1. It operates on
repository-owned generated fixtures and enforces required support,
contradiction limits, window completeness, and abstention. Probabilistic,
temporal-graph, model-first shadow, and uncertainty-ensemble lanes are typed
contracts whose runtime state is `unavailable`.

Generated optional lane-result fixtures may exercise deterministic arbitration
tests. They cannot load a model, bypass the deterministic veto, remove
disagreement, or make an operational decision.

## Canonical Hypotheses

The bounded evidence graph is the source of truth. Evidence roles remain
explicit: supports, contradicts, missing, stale, supersedes, and retracts. The
flat projection carries the graph digest and introduces no new conclusion.

Confidence, uncertainty, freshness, quality, calibration, authority, and
abstention are separate fields. Every hypothesis is generated-only,
nonoperational, and `mandatory_review`. Identity, guilt, intent, sensitive
traits, predictive risk, and vehicle-owner assertions are prohibited.

## Persistence And Read Surface

Migration `0013_correlation_foundation` extends correlation runs, hypotheses,
and evidence references and adds receipts, partition checkpoints, window
membership, lane results, and hypothesis revisions. PostgreSQL applies forced
department row security and `FOR UPDATE SKIP LOCKED`; SQLite is restricted to
one generated-development worker.

Five department-scoped read-only endpoints expose bounded runs, graphs,
projections, and revisions. They require the intelligence viewer role, apply
`no-store` and `no-cache`, and add no ingestion, start, replay, correction,
rule, alert, notification, or dispatch mutation.

## Resource Limits

| Resource | Hard maximum |
|---|---:|
| Events per batch | 1,000 |
| Active partitions per worker | 128 |
| Active windows per partition | 256 |
| Events per window | 4,096 |
| Future clock skew | 30 seconds |
| Worker lease | 90 seconds |
| Evidence references per hypothesis | 256 |
| Graph nodes | 1,024 |
| Graph edges | 4,096 |
| Read page | 500 records |

The runtime flag is disabled by default, forbidden in production, and never
starts a worker during application startup.
