# Phase 4 Owner Decision Record

Status: composite selections recorded on 2026-09-03; separate planning
acceptance remains pending.

Owner: `mayank-admin`

Decision source package: `P4-PLANNING-R1`, SHA-256
`E03286FEA45818221EE8E605E0623F93380680F85077080CFACAA4857B60F05D`.

This record preserves the owner's selections and defines how combinations are
made internally coherent. It does not authorize implementation, runtime work,
external integration, operational activation, deployment, or remote Git.

## Raw Selections

```text
D-P4.0-001: A+B
D-P4.0-002: A+C+D, with research and an innovative D architecture
D-P4.0-003: A
D-P4.0-004: A+B+C
D-P4.0-005: A+B+D, with no integration right now
D-P4.0-006: A
D-P4.0-007: A
D-P4.0-008: A
```

## Reconciled Decision Profile

| Decision | Binding planning interpretation |
| --- | --- |
| `D-P4.0-001:A+B` | Evidence-first hypothesis graph is canonical; flat event groups are bounded read projections |
| `D-P4.0-002:A+C+D` | Adaptive Multi-Engine Correlation combines a mandatory deterministic lane, optional model-first proposal, probabilistic/ensemble evidence, calibration, contradiction, and abstention |
| `D-P4.0-003:A` | Visual graph, typed temporal nodes, constrained CEL, shadow evaluation, immutable versions, and rollback |
| `D-P4.0-004:A+B+C` | All authority capabilities are contractually distinguishable; police-intelligence baseline uses mandatory human review, lower-consequence automation is class-scoped, and autonomous dispatch remains future-only and hard-disabled |
| `D-P4.0-005:A+B+D` | Define typed provider contracts, generic transport envelope, and generated provider fixtures, but activate no real/external integration now |
| `D-P4.0-006:A` | Multi-signal candidates, per-signal evidence, calibration, contradiction, abstention, and human confirmation |
| `D-P4.0-007:A` | PostgreSQL/PostGIS aggregates, row-security defense, bitemporal revisions, typed provenance, append-only evidence, and transactional outbox |
| `D-P4.0-008:A` | Data-class retention with separately authorized, attributable hold overlay |

## D-P4.0-001: Canonical Graph Plus Flat Projection

The evidence-first bounded hypothesis graph is the source of truth. It stores
typed edges for supporting, contradicting, missing, stale, superseded, and
retracted evidence with immutable provenance.

Flat event groups are derived, rebuildable projections optimized for lists,
exports, simple APIs, and low-resource clients. They cannot introduce an edge,
identity, confidence, or conclusion that is absent from the canonical graph.
Projection version and source graph digest are always returned.

## D-P4.0-002: Adaptive Multi-Engine Correlation

The selected D innovation is defined in
[Adaptive Multi-Engine Correlation Research](adaptive-correlation-research.md).
It preserves deterministic behavior on the owner's laptop and adds optional
probabilistic, temporal-graph, and ensemble lanes when capable hardware is
available.

Model-first means candidate proposal, not authority. Every model candidate is
validated by department, schema, time, geometry, policy, contradiction, and
resource constraints. Every mode can abstain, and only a separately approved
alert policy may turn a hypothesis into a proposed alert.

## D-P4.0-003: Rule System

Option A is selected without modification. Stateful behavior remains in typed
temporal nodes. CEL is stateless and constrained. All rules are parsed,
type-checked, cost-checked, canonicalized, approved, shadow-tested, versioned,
and rollback-capable before operational activation.

## D-P4.0-004: Tiered Authority Without Silent Escalation

The combined selection supports three explicitly different capability classes:

1. `mandatory_review`: every police-intelligence alert is proposed and requires
   an attributable authorized human disposition. This is the Phase 4 baseline.
2. `bounded_automation`: generated tests and separately approved
   low-consequence system-health workflows may auto-route, suppress duplicates,
   or resolve machine-health conditions. They cannot confirm person/vehicle
   identity, threat, guilt, or enforcement action.
3. `future_autonomous_action`: schemas may reserve a future integration boundary
   for autonomous confirmation or dispatch, but the capability is absent or
   compile/deployment disabled in the baseline. Enabling it requires a separate
   legal, safety, operational, integration, human-factors, and owner program.

An alert class cannot inherit a more permissive authority mode. Policy changes
cannot silently reclassify an intelligence alert as system health. Every class,
mode, transition, actor, reason, and policy version is audited.

## D-P4.0-005: Provider Readiness With No External Integration

P4.0 defines the typed provider interface, purpose and field policy, secret
provider contract, exact-destination contract, bounded transport envelope,
normalization, audit, freshness, revocation, and kill-switch state.

P4.4 may implement only an in-process generated provider using invented,
non-issuable records. A generic transport implementation may be designed and
tested against local generated simulators, but it remains disabled and cannot
receive an arbitrary runtime URL, query, credential, or schema.

No Government, police, vehicle-owner, registration, case, watchlist, private,
or other external provider is integrated under this decision. A future provider
requires an independent exact authorization and cannot enter as a configuration
change to the generic envelope.

## D-P4.0-006 Through D-P4.0-008

Options A are selected as written and strengthened by the R1 planning baseline:

- candidate matching retains per-signal evidence and explicit abstention;
- persistence preserves application and row-level department isolation,
  chronology, provenance, revisions, and atomic outbox publication;
- retention is data-class-specific, while each hold is narrow, attributable,
  purpose-bound, reviewable, and releasable.

Exact real-data retention periods, hold authority, provider fields, operational
alert authority, and evidentiary procedures remain unresolved external gates.

## Remaining Gate

All eight design decisions are now selected. `D-P4-PLAN-ACCEPTANCE` remains
pending and must bind the resealed planning package digest. Acceptance permits
preparation of a separate P4.0 implementation package only. It does not itself
authorize implementation.
