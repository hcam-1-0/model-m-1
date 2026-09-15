# P4.2 Planned Contract Catalog

Status date: 2026-09-04

Status: planning only; names and fields are proposed implementation targets and
are not executable contracts.

## Contract Families

| Contract | Role | Canonical authority |
| --- | --- | --- |
| `VisualRuleDocumentV1` | UI authoring document, node placement, labels, and semantic payload | Authoring digest only; never executable |
| `IntelligenceRuleGraphV2` | Closed semantic graph before canonical node renumbering | Compiler input after server-side validation |
| `CanonicalRuleAstV1` | Normalized typed DAG evaluated by workers | Sole semantic source of truth |
| `CelPredicateV1` | Source, environment, checked bytes, AST facts, and cost | Hash-bound checked expression only |
| `RuleScheduleV1` | Immutable weekly intervals and IANA time-zone binding | Versioned schedule digest |
| `RuleCompilationV1` | Compiler inputs, outputs, diagnostics, versions, and digests | Append-only compilation record |
| `RuleLifecycleEventV1` | Attributable lifecycle transition with reason and ETag | Append-only transition record |
| `RuleEvaluationV1` | Generated simulation or non-operational shadow result | Deterministic evaluation digest |
| `RuleEvaluationRevisionV1` | Late/corrected/retracted evaluation update | Append-only revision |
| `RuleShadowComparisonV1` | Bounded candidate-versus-baseline comparison | Evidence only; no routing effect |
| `RuleStateCheckpointV1` | Bounded temporal-node state and watermark | Version-bound runtime checkpoint |

## Visual Authoring Boundary

`VisualRuleDocumentV1` contains two explicitly separate sections:

- `semantics`: closed node and edge payload accepted by the compiler;
- `presentation`: positions, groups, color tokens, labels, collapsed state, and
  viewport metadata needed by a future Phase 5 editor.

The server validates both, but only `semantics` can affect runtime behavior.
The authoring digest binds both sections for audit and exact round-trip. The
semantic digest binds only the canonical AST and semantic environment versions.
Changing presentation alone creates a new authoring revision but not a new
semantic rule version.

## Planned Node Types

| Family | Node types | Output | State owner |
| --- | --- | --- | --- |
| Source | `event_match`, `hypothesis_match` | match token | P4.1 immutable input adapter |
| Predicate | `cel_predicate` | Boolean | none |
| Boolean | `all`, `any`, `not`, `quorum` | Boolean | none |
| Ordering | `sequence`, `within`, `until` | temporal match | typed temporal engine |
| Duration | `for_at_least`, `absence` | temporal match | typed temporal engine |
| Aggregate | `count`, `rate`, `distinct_stream_count` | bounded numeric/match | typed temporal engine |
| Control | `schedule_gate`, `cooldown`, `repeat_limit` | gated match | typed temporal engine |
| Output | `propose_review_candidate` | non-operational candidate | P4.2 evidence sink only |

The P4.2 output name is deliberately not `alert`. P4.3 alone may turn an
accepted rule evaluation into a proposed-alert aggregate under its own gate.

## Closed CEL Profile

`hcam.p4-2.constrained-cel.v1` is planned as a Boolean-only, scalar-only
profile. Candidate variables are fixed by the environment manifest and may
include bounded values such as event kind, object class, confidence,
uncertainty, direction, count, rate, chronology quality, contradiction flag,
completeness, schedule state, and prior typed-node Boolean results.

The profile rejects:

- dynamic values, arbitrary maps, lists, messages, bytes, and null;
- selectors, indexing, object construction, collection construction, macros,
  comprehensions, regex, and string transformation;
- custom functions, late-bound functions, and extension libraries;
- timestamps or durations parsed inside CEL;
- network, files, environment, database, secrets, provider lookup, camera
  control, alert routing, notification, dispatch, and enforcement;
- unchecked expressions and runtime compilation of source text.

## Canonicalization Rules

The planned compiler must:

1. Reject unknown fields, duplicate keys, cycles, dangling edges, unreachable
   nodes, multiple outputs, invalid arity, and type mismatch.
2. Strip presentation fields from semantic compilation.
3. Normalize integers, finite decimals, durations, schedules, enum casing, and
   UTF-8 strings according to a versioned contract.
4. Preserve child order for `sequence`, `until`, and other ordered nodes.
5. Sort child references by child semantic digest for commutative `all`, `any`,
   and `quorum` nodes.
6. Canonically renumber nodes from the output graph while retaining an
   authoring-node-to-canonical-node diagnostic map.
7. Bind the canonical AST to contract, compiler, temporal, CEL environment,
   schedule, and accepted input-schema versions.
8. Hash canonical UTF-8 bytes with SHA-256 and persist both bytes and digest.

## Lifecycle

Planned P4.2 transitions are:

```text
draft -> validated -> approved -> shadow -> suspended -> retired
  |          |           |          |           |
  +----------+-----------+----------+-----------+-> retired
```

`active` is reserved but unavailable. A P4.2 database constraint, service gate,
configuration gate, and negative test must reject it. `approved` means the
immutable compiler output is accepted for generated simulation or later shadow
eligibility. It does not mean operational activation.

Every transition requires department scope, RBAC, `If-Match`,
`X-HCAM-Reason`, actor, prior/new version, compiler/environment bindings, and an
audit plus transactional-outbox record. Rollback creates a transition selecting
a prior immutable version; it never edits historical bytes.

## Initial Hard Bounds

| Boundary | Planned default | Planned maximum |
| --- | ---: | ---: |
| Authoring document | 64 KiB | 128 KiB |
| Semantic nodes | 32 | 128 |
| Graph depth | 8 | 16 |
| Inputs per node | 8 | 16 |
| CEL source | 256 bytes | 512 bytes |
| CEL checked bytes | 16 KiB | 64 KiB |
| CEL checked-AST nodes | 64 | 128 |
| Temporal window | 60 seconds | 15 minutes |
| Events per state key/window | 256 | 4,096 |
| State keys per rule/partition | 1,024 | 16,384 |
| Rules per generated batch | 16 | 64 |
| Generated inputs per batch | 100 | 1,000 |
| Shadow comparison retention | 24 hours | 7 days |

Implementation evidence may lower defaults or maxima. Raising a maximum after
the start package is accepted requires a new digest-bound decision.
