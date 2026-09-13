# P4.7 Owner Decisions And Reconciliation

Status date: 2026-09-05

Status: all twelve P4.7 design decisions are recorded and effective for
planning reconciliation only. They do not authorize implementation, tests,
migrations, dependencies, scenario execution, runtime, providers, network,
real data, models, operational actions, deployment, Phase 4 final acceptance,
Phase 5, or remote Git.

Owner: `mayank-admin`

Planning predecessor: `P4.7-PLANNING-R0`, SHA-256
`BFC360F466A45E8830AAF0547083A10EF49E55C7792A2E2E67DB9211E215FBC1`.

## Recorded Selection

The owner's message is normalized as UTF-8 with LF line endings, trailing line
whitespace removed, and no terminal newline:

```text
D-P4.7-001: C
D-P4.7-002: C
D-P4.7-003: C
D-P4.7-004: C
D-P4.7-005: C
D-P4.7-006: B
D-P4.7-007: C
D-P4.7-008: C
D-P4.7-009: B
D-P4.7-010: B
D-P4.7-011: B + C if possible
D-P4.7-012: A
```

The phrase `B + C if possible` is a binding architecture-capability request,
not authority to treat option C as an executable production manual. Option B
is the P4.7 implementation baseline. Option C is reconciled as a guarded,
non-effective outline of future production-operating prerequisites and
unverified procedure categories. It cannot contain environment-specific
instructions, values, credentials, destinations, commands, recovery promises,
or an assertion that a real operating procedure has been validated.

## Reconciled Profile

| Decision | Planning binding |
| --- | --- |
| `D-P4.7-001:C` | Canonical scenario engine with bounded in-process adapters and separate HTTP/event projection checks; direct persistence access is forbidden |
| `D-P4.7-002:C` | One golden generated narrative, eight mandatory failure/recovery variants, and bounded pairwise contract cases |
| `D-P4.7-003:C` | Manifest-derived logical time, identities, ordering, policy revisions, fixture hashes, normalization, allowed variance, and two clean semantic replays |
| `D-P4.7-004:C` | Exact immutable inputs plus independent mandatory semantic assertion families; skip, unknown, or incomplete is a failure |
| `D-P4.7-005:C` | Acyclic H-CAM evidence DAG with optional independently validated RFC 8785, PROV, and SLSA-shaped projections and no conformance claim |
| `D-P4.7-006:B` | Machine-readable claim and limitation registers with one derived human review summary |
| `D-P4.7-007:C` | Canonical HTTP operation catalogue with a pinned OpenAPI projection and RFC 9457-compatible safe failures |
| `D-P4.7-008:C` | Canonical H-CAM event/workflow catalogues with optional pinned AsyncAPI, CloudEvents, and Arazzo projections |
| `D-P4.7-009:B` | Typed backend-to-UI state/action matrix with explicit WCAG and WAI-ARIA-informed requirements and no conformance claim |
| `D-P4.7-010:B` | Versioned compatibility/change matrix with consumer support, deprecation, migration, and evidence rules |
| `D-P4.7-011:B+[guarded C capability]` | Typed generated-only non-operational runbook and human guide, plus a non-effective future production-operations prerequisite outline |
| `D-P4.7-012:A` | Exact Phase 4 closeout acceptance remains separate from a later explicit Phase 5 planning authorization |

## D-P4.7-001: Canonical Scenario Engine

Option C is selected as written. A canonical scenario manifest and typed step
model define the acceptance narrative. A bounded in-process adapter invokes
the same application-service boundaries used by consumer adapters. Separate
HTTP and event projections validate the Phase 5 consumer boundary without
making either projection the scenario authority.

The engine cannot use direct persistence, bypass authorization, inject
unrecorded state, or turn generated outputs into operational records. Adapter
equivalence, side-effect accounting, failure propagation, and bypass-denial
tests are mandatory.

## D-P4.7-002: Layered Deterministic Portfolio

Option C is selected as written. The portfolio contains `S00` as the golden
narrative and `S01` through `S08` for abstention, replay, ordering/conflict,
authorization/isolation, reference degradation, review/lifecycle denial,
correction/retraction, and worker/recovery degradation. Bounded pairwise cases
cover material interactions without claiming exhaustive state exploration.

Every fixture remains synthetic, anonymous, non-issuable, generated-only, and
production-forbidden. A successful golden path cannot compensate for a failed,
skipped, unknown, or incomplete mandatory variant.

## D-P4.7-003: Manifest-Derived Determinism

Option C is selected as written. Seed, logical epoch, timezone, identifier
namespace, step quantum, source and durable ordering, policy revisions,
fixture hashes, normalization rules, and allowed variance are immutable
manifest inputs. Two clean attempts must produce equal normalized semantic
digests.

Wall-clock, random identity, database row order, retry timing, generated
timestamps, and incidental serialization cannot silently enter the oracle.
Any allowed variance must be named, bounded, normalized, and excluded from
security, authority, chronology, identity, integrity, and side-effect facts.

## D-P4.7-004: Layered Semantic Assertions

Option C is selected as written. Exact fixtures, schemas, policies, and
canonical records are hash-bound. Independent schema, authorization,
chronology, identity, rule, review, integrity, redaction, recovery,
side-effect, replay, handoff, and accessibility assertion families are
evaluated separately.

All mandatory families must pass. `skip`, `unknown`, `incomplete`, missing
evidence, unexpected side effects, and unclassified failures fail closed.
Narrative appearance, an AI/LLM qualitative judgment, or final-state success
cannot override a failed layer.

## D-P4.7-005: Canonical Evidence DAG

Option C is selected as written. The evidence index is acyclic and binds the
source commit, authorization, exact inputs, producer and version, parent
components, byte lengths, SHA-256 values, completeness, verification result,
claims, limitations, and reviewer decisions.

Accepted H-CAM canonical encoding remains authoritative. RFC 8785, W3C PROV,
and SLSA-shaped outputs are optional derived projections with explicit mapping
and independent validation. They cannot claim standards conformance, a SLSA
level, legal admissibility, custody, authenticity, or external attestation.

## D-P4.7-006: Claims And Limitations Registers

Option B is selected as written. Every claim records scope, evidence class,
supporting components, freshness, limitations, status, and prohibited
interpretations. Every limitation records impact, mitigation, future evidence,
owner, status, and affected claims.

The human review is generated from the same canonical records. Unsupported,
stale, contradicted, withdrawn, unresolved, or evidence-free claims cannot be
presented as accepted capabilities. Limitations are retained rather than
softened to improve the demonstration narrative.

## D-P4.7-007: Canonical HTTP Handoff

Option C is selected as written. The canonical catalogue records each
operation's purpose, audience, authorization gate, department scope, reason,
ETag, idempotency, schema, pagination, ordering, freshness, safe failures,
examples, events, actions, UI states, and compatibility class.

A pinned OpenAPI projection and RFC 9457-compatible problem mapping derive
from that catalogue. Projection validation does not authorize a generated SDK,
provider, network listener, deployment, or Phase 5 implementation.

## D-P4.7-008: Canonical Event And Workflow Handoff

Option C is selected as written. H-CAM contracts remain authoritative for
event semantics, chronology, correlation, causation, replay, idempotency,
delivery, failure, review, and workflow steps. Optional AsyncAPI 3.1,
CloudEvents 1.0.2, and Arazzo 1.1 projections are pinned, mapped, and validated
without selecting a broker or claiming conformance.

No projection can grant authorization, alter an accepted domain state,
activate a workflow engine, emit an operational alert, or invoke an external
action.

## D-P4.7-009: Typed UI And Accessibility Handoff

Option B is selected as written. Every Phase 5 view and action maps loading,
empty, partial, stale, degraded, denied, conflict, failure, recovery,
correction, and success states to source facts, visible copy, available
actions, focus behavior, keyboard operation, status announcements, error
association, non-color meaning, target/contrast expectations, and evidence
state.

The matrix is an implementation contract, not a dashboard implementation,
visual-design approval, usability finding, accessibility conformance claim, or
authorization to begin Phase 5.

## D-P4.7-010: Versioned Compatibility Governance

Option B is selected as written. The compatibility matrix distinguishes
documentation-only, optional additive, new capability, compatible behavioral,
deprecation, breaking schema, breaking semantic, and security-boundary
changes. It records supported consumers, migration needs, deprecation windows,
evidence, and release gates.

Security boundaries and mandatory controls cannot be weakened under an
additive or compatible label. Permanent backward compatibility is not
promised, and latest-version-only replacement is not permitted without the
recorded change process.

## D-P4.7-011: Generated Runbook With Guarded Production Outline

Option B is the executable P4.7 baseline. The machine-readable non-operational
runbook and its concise human projection define bounded preflight, fixture
verification, execution order, expected outputs, safe stop/failure codes,
resume policy, cleanup, zero-retention verification, reconstruction, evidence
sealing, and reviewer checks for the generated-only acceptance environment.

The requested option C capability is retained only as a future production-
operations extension outline. It may enumerate categories such as deployment,
incident handling, backup/restore, recovery, capacity, scaling, observability,
on-call ownership, security response, rollback, data governance, and change
control. Each category must be marked `not_operationally_validated` and list
the evidence, accountable owner, environment, target, credential, network,
data-policy, drill, approval, and rollback prerequisites still required.

The guarded C capability has these hard limits:

- no production command, endpoint, destination, credential, secret, identity,
  host, cluster, volume, threshold, RPO/RTO, SLO, scale, or retention value;
- no claim that backup, restore, failover, incident response, scaling,
  deployment, rollback, or on-call procedure works in a real environment;
- no operational execution, environment connection, provider integration,
  scanner, container, Kubernetes action, deployment, or data/media access;
- no use of the future outline as a Phase 4 acceptance oracle;
- every executable production procedure requires later environment evidence,
  separate owner authorization, implementation, validation, and acceptance.

This preserves the user's future-production intent without fabricating an
operations manual from generated-only evidence.

## D-P4.7-012: Separate Phase Boundary

Option A is selected as written. P4.7 technical evidence can earn the first
four weighted points. The owner must then accept one exact source commit,
evidence package, claims/limitations set, and handoff digest to earn the final
point and close Phase 4.

Phase 4 acceptance does not authorize Phase 5 planning or implementation.
Phase 5 requires a separate explicit planning authorization and retains every
real-data, provider, model, media, operational-action, infrastructure,
deployment, and remote-Git gate until separately opened.

## Reconciled Architecture

```text
accepted anonymous Phase 3 analytic fixtures
    -> canonical generated P4.7 scenario manifest
       -> bounded application-service adapter
       -> separate HTTP and event projection checks
    -> golden narrative + eight mandatory variants + pairwise cases
    -> manifest-derived logical time, identity, order, and replay
    -> independent fail-closed semantic assertion families
    -> acyclic evidence DAG
       -> exact claims and limitations registers
       -> optional standards-shaped projections
    -> canonical Phase 5 HTTP/event/workflow catalogues
    -> typed UI, action, accessibility, and compatibility matrices
    -> generated-only non-operational runbook
       -> guarded future production-operations prerequisite outline
    -> exact Phase 4 closeout acceptance
       -> separate future Phase 5 planning authorization
```

## Progress And Remaining Gate

The planning/research gate remains **5/5 (100.0000%)**. The owner decision
gate is now **12/12 (100.0000%)**, change **+100.0000 percentage points**.
Reconciled-package preparation becomes **1/1 (100.0000%)** when the exact R1
digest is sealed. These planning gates award no weighted product points:

- P4.7 remains **0/5 (0.0000%)**, change **+0.0000 percentage points**;
- Phase 4 remains **95/100 (95.00%)**, change **+0.00 percentage points**.

The non-effective, digest-bound `P4.7-PLANNING-R1` package must be accepted
exactly by the owner before one non-effective `P4.7-START-R0` package may be
prepared. Implementation and scenario execution cannot begin until that later
start package is also accepted exactly.
