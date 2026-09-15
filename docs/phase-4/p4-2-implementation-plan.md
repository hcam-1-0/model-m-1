# P4.2 Rule Authoring And Evaluation Implementation Plan

Status date: 2026-09-04

Planning status: prepared; implementation remains unauthorized until the owner
accepts the exact `P4.2-START-R0` package digest.

## 1. Objective

P4.2 turns bounded visual rule documents into immutable typed ASTs, evaluates
their stateful temporal nodes deterministically over generated P4.1 event and
hypothesis fixtures, and records non-operational simulation and shadow evidence.

P4.2 is a policy compiler and bounded evaluator. It is not a video analytics
stage, alerting system, integration layer, dispatch system, or deployment
milestone. It consumes structured generated metadata only and produces rule
evaluation evidence only.

## 2. Frozen Progress Boundary

The accepted Phase 4 work breakdown assigns 15 of 100 Phase 4 points to P4.2:

| Work item | Points | Completion rule |
| --- | ---: | --- |
| P4.2-A: visual graph and canonical typed AST | 4 | Round-trip, lifecycle, version, digest, type, depth, reachability, canonicalization, and cost gates all pass |
| P4.2-B: stateful temporal nodes | 5 | Sequence, window, duration, absence, aggregate, schedule, cooldown, correction, replay, and bounded-state goldens all pass |
| P4.2-C: constrained CEL host | 4 | Closed environment, structured checked-AST validation, Boolean type, compile-once, dependency binding, abuse, and evaluation gates all pass |
| P4.2-D: evidence and owner acceptance | 2 | Exact reproducible evidence is sealed and separately accepted by the owner |

Progress remains **25/100 Phase 4 points (25.00%)** and **0/15 P4.2 points
(0.0000%)** while this planning package is prepared. Technical completion can
earn at most 13/15 P4.2 points, raising Phase 4 to 38/100. The final two points
require separate exact owner acceptance and would raise Phase 4 to 40/100.
Planning documents, source lines, elapsed time, and test count do not receive
partial weighted credit.

## 3. Binding Inputs

P4.2 must preserve:

- accepted Phase 4 planning package `P4-PLANNING-R2`, SHA-256
  `B8F4371A8DDD350F44321E70F5FB8CEE0DD27299A26082A40460086E80DDEA63`;
- `D-P4.0-003:A`: visual graph, typed temporal nodes, constrained CEL,
  immutable versions, shadow evaluation, and rollback;
- `D-P4.0-004:A+B+C`: mandatory human review for police-intelligence output,
  with autonomous dispatch hard-disabled;
- accepted P4.0 contracts and guardrails without rewriting their evidence;
- accepted P4.1 evidence package SHA-256
  `D6302447DCF7C1ADB769E11FD36ACE1519552E0F982A23EDA86D64EC73351805`;
- accepted P4.1 canonical component digest
  `C3AD198C6EF8F9C49970B83F2B383F1C4F8D524C6085D115F392B54D2F348379`;
- P4.1 event identity, ordering, partition, watermark, window, chronology,
  hypothesis, revision, abstention, and department-isolation semantics;
- accepted P3.4 geometry rule and constrained-CEL behavior as an immutable
  predecessor, not a mutable shared runtime;
- the existing locked `cel-expr-python==0.1.3` dependency and exact lockfile;
- generated-only, `operational=false`, `mandatory_review`, no-store, audit,
  row-security, transactional-outbox, and production-denial boundaries.

## 4. Non-Goals And Prohibitions

P4.2 does not include:

- camera, ONVIF, Sentinel, stream, frame, image, recording, playback, or media
  access;
- model, checkpoint, dataset, artifact, inference, accelerator, training,
  evaluation, or benchmark work;
- real, private, personal, biometric, vehicle-owner, case, watchlist,
  Government, or police data;
- provider credentials, network egress, external lookup, or integration;
- operational rule activation or startup workers;
- operational alerts, notification, routing, dispatch, enforcement, or
  autonomous action;
- arbitrary scripting, Python evaluation, JavaScript, SQL fragments, dynamic
  code, user extensions, or custom CEL functions;
- production, cloud, Kubernetes, deployment, release, or remote Git activity.

## 5. Architecture

```text
bounded visual authoring document
    -> server-side schema and policy validation
    -> semantic/presentation separation
    -> typed DAG validation and canonical renumbering
    -> constrained scalar CEL compile and checked-AST inspection
    -> static graph/temporal/CEL resource budget
    -> immutable compilation record and semantic digest
    -> attributable validated/approved/shadow lifecycle
    -> generated P4.1 event/hypothesis replay
    -> bounded temporal state machine
    -> non-operational evaluation revision
    -> optional shadow comparison evidence
```

The control plane is the only compilation path. The evaluator accepts no source
text, visual document, mutable rule, unchecked AST, or runtime-provided
function. It accepts only an approved/shadow-eligible immutable compilation
whose digests and environment versions are reverified.

## 6. Semantic Model

### Visual document versus executable meaning

The visual document supports future Phase 5 UI needs such as node coordinates,
groups, labels, comments, and viewport state. It is not executable. Semantic
fields compile into `CanonicalRuleAstV1`; presentation fields receive a separate
digest and cannot alter evaluation.

Compilation fails when the graph has unknown fields, duplicate node IDs,
cycles, dangling inputs, unreachable nodes, multiple outputs, invalid arity,
type mismatch, prohibited node kinds, invalid schedules, or exceeded resource
bounds.

Canonicalization must make harmless ordering and presentation changes stable:

- ordered temporal inputs preserve declared order;
- commutative Boolean inputs sort by child semantic digest;
- canonical node IDs are independent of UI IDs and positions;
- finite numeric, duration, enum, schedule, and string representations are
  normalized under an explicit version;
- the final digest binds contract, compiler, temporal-semantics, CEL
  environment, schedule, and accepted input-schema versions.

### Typed nodes

The initial closed node families are source match, CEL predicate, Boolean
composition, ordered sequence, bounded window, until, duration, absence, count,
rate, distinct-stream count, schedule gate, cooldown, repeat limit, and a
non-operational review-candidate output.

The compiler uses a typed port system rather than accepting arbitrary JSON
between nodes. Candidate types are `event_match`, `hypothesis_match`, `bool`,
`bounded_int`, `bounded_rate`, `temporal_match`, and
`review_candidate_nonoperational`. No implicit cast may change node meaning.

### Temporal truth

All stateful nodes use P4.1 event time, source order where declared, watermark,
allowed lateness, chronology confidence, and partition semantics. Arrival time
cannot silently become event time.

- `sequence` requires its ordered inputs in one bounded interval;
- `within` constrains completion relative to its first causal input;
- `for_at_least` becomes true only after observed duration under the configured
  gap policy;
- `absence` becomes true only after the watermark closes its interval;
- `count`, `rate`, and `distinct_stream_count` use explicit event membership and
  bounded denominators;
- `cooldown` suppresses repeated output but preserves a visible suppressed
  count;
- `repeat_limit` stops output at its cap without deleting underlying evidence;
- schedule opening initializes without backfill; schedule closing terminates
  pending state with a typed reason rather than inventing an event;
- late correction, source correction, hypothesis supersession, and retraction
  append an evaluation revision instead of rewriting prior truth.

State is keyed by department, rule ID/version, accepted scope digest, P4.1
partition, and declared grouping key. A version, scope, compiler, environment,
schedule, schema, or retention change forces a typed checkpoint close and new
state generation.

## 7. Constrained CEL Profile

P4.2 creates `hcam.p4-2.constrained-cel.v1` without changing the accepted P3.4
profile.

The profile:

- uses exact declared scalar variables and requires a Boolean return;
- calls `cel.NewEnv` with no custom functions and no extensions;
- always enables checking and persists serialized checked output;
- structurally decodes and inspects the checked expression rather than relying
  on a token denylist as the security authority;
- rejects dynamic values, collections, messages, selectors, indexing, macros,
  comprehensions, regex, custom calls, unknown overloads, and object creation;
- allows only a closed operator/overload table;
- limits source bytes, checked bytes, AST node count, depth, literal sizes, and
  total static cost;
- recompiles on the control plane and compares canonical checked bytes and
  digest before lifecycle promotion;
- deserializes and evaluates only hash-bound checked bytes on the data plane;
- receives no network, filesystem, environment, SQL, secret, provider, camera,
  alert, notification, dispatch, or enforcement capability.

Because the locked Python wrapper does not document native cost-limit APIs,
the executable profile remains scalar-only and excludes constructs whose work
depends on collection cardinality. Generated performance evidence must freeze a
conservative batch deadline and circuit-breaker policy. An evaluation timeout,
native-extension failure, digest drift, or type mismatch closes the affected
generated run and produces no positive result.

## 8. Lifecycle And Authority

P4.2 implements immutable states `draft`, `validated`, `approved`, `shadow`,
`suspended`, and `retired`. The `active` state and transition are absent or
rejected at the contract, database, service, configuration, and test layers.

Rules are immutable after validation. Editing creates a new version. Approval
binds exact semantic, authoring, compiler, CEL, schedule, policy, and scope
digests. Shadow evaluation is generated/non-operational evidence and cannot
create an alert, contact a provider, affect routing, or execute an action.
Rollback selects a prior immutable approved version and records a new lifecycle
event; it never mutates history.

Mutations require department scope, `camera.editor` or `platform.admin`, an
`If-Match` value, `X-HCAM-Reason`, attributable actor, and immutable audit plus
transactional-outbox record. Read projections remain department-scoped and
`Cache-Control: no-store`.

## 9. Work Packages

### P4.2-W1: Historical verification transition

Keep every accepted P4.0 and P4.1 package, evidence record, acceptance, digest,
and source commit immutable. Transition the P4.1 readiness checker to verify
accepted implementation components from local Git objects at technical commit
`ad44f3e3af292e5a134b45566fc16f09884861a2`, while continuing to verify current
immutable package and acceptance records. Missing objects, paths, hashes, or
bindings fail closed.

### P4.2-W2: Contracts and generated fixtures

Implement strict V1/V2 authoring, graph, AST, CEL, schedule, compilation,
lifecycle, evaluation, revision, shadow-comparison, and checkpoint contracts.
Generate deterministic positive, negative, metamorphic, temporal, DST,
correction, overload, and abuse fixtures. Do not include real identifiers,
free-form observations, camera data, or provider records.

### P4.2-W3: Canonical compiler

Implement semantic/presentation separation, typed-DAG validation, reachability,
canonical node normalization, stable digesting, compiler diagnostics, and
version bindings. Prove layout-only edits preserve semantic digest, semantic
edits change it, and all ordering/type/cycle/budget violations fail.

### P4.2-W4: CEL adapter

Create the independent P4.2 CEL environment using the existing locked official
wrapper. Add structured checked-AST inspection, closed scalar context,
operator/overload allowlist, Boolean enforcement, canonical serialization,
compile-once behavior, dependency identity evidence, and fail-closed evaluation.
Do not alter P3.4 CEL behavior.

### P4.2-W5: Temporal evaluator

Implement pure deterministic temporal-node transitions first, followed by a
bounded generated harness over P4.1 fixtures. Preserve watermark and chronology
semantics, visible pending/suppressed/abstained states, correction revisions,
exact replay, and no-silent-eviction behavior.

### P4.2-W6: Persistence and concurrency

Add migration `0014_rule_authoring_evaluation`. Evolve
`intelligence_rules` into immutable version records while preserving accepted
P4.0 rows. Add compilation, scope membership, schedule, lifecycle, checkpoint,
evaluation revision, and shadow-comparison stores. Apply department filters,
forced PostgreSQL row security, optimistic concurrency, unique idempotency
keys, leases, and transactional outbox. SQLite remains a single-worker
development boundary.

### P4.2-W7: Control-plane API and observability

Add bounded draft, compile-preview, validate, approve, shadow-eligibility,
suspend, retire, version-list, compilation-read, and evaluation-read contracts.
No public endpoint starts evaluation or activates a rule. A repository-owned
CLI/harness may run only generated scenarios when the default-false,
production-forbidden P4.2 flag is explicitly enabled.

Metrics use only bounded labels such as stage, outcome, node family, lifecycle
transition, and resource-limit class. Rule IDs, actor IDs, department names,
source text, user labels, event values, and digests are prohibited labels.

### P4.2-W8: Validation, evidence, and acceptance

Run focused tests, branch coverage, full regression, Ruff, compile checks,
source/wheel builds, lock/SBOM/license/vulnerability checks, migration cycles,
PostgreSQL row-security and concurrency tests, historical readiness, and clean
source regeneration. Seal exact evidence and prepare a separate non-effective
owner acceptance proposal.

## 10. Planned Persistence

| Store | Purpose | Principal controls |
| --- | --- | --- |
| `intelligence_rules` | Immutable logical rule versions | composite logical ID/version uniqueness, generated-only, operational false |
| `intelligence_rule_compilations` | Canonical AST and checked CEL bindings | immutable bytes/digests, compiler/environment versions |
| `intelligence_rule_scope_members` | Explicit generated scope membership | department match, bounded count, no implicit wildcard |
| `intelligence_rule_schedules` | Versioned IANA schedules | canonical UTC/local/fold semantics |
| `intelligence_rule_lifecycle_events` | Attributable transitions | append-only actor/reason/prior/new/ETag |
| `intelligence_rule_state_checkpoints` | Current bounded temporal state | versioned key, watermark, lease, counters |
| `intelligence_rule_evaluation_revisions` | Deterministic generated/shadow outcomes | append-only input/output digests, non-operational |
| `intelligence_rule_shadow_comparisons` | Baseline-versus-candidate evidence | bounded retention, no routing effect |

The migration must preserve P4.0 and P4.1 downgrade/upgrade compatibility and
must not modify Phase 3 tables or `stream_event_outbox` publication state.

## 11. Planned API Surface

```text
POST /intelligence-rules
POST /intelligence-rules/compile-preview
GET  /intelligence-rules
GET  /intelligence-rules/{rule_id}
GET  /intelligence-rules/{rule_id}/versions
GET  /intelligence-rule-compilations/{compilation_id}
POST /intelligence-rules/{rule_id}/validate
POST /intelligence-rules/{rule_id}/approve
POST /intelligence-rules/{rule_id}/mark-shadow-eligible
POST /intelligence-rules/{rule_id}/suspend
POST /intelligence-rules/{rule_id}/retire
GET  /intelligence-rules/{rule_id}/evaluations
GET  /intelligence-rules/{rule_id}/shadow-comparisons
```

`compile-preview` returns bounded diagnostics and digests but persists nothing.
No route accepts raw event input, starts a worker, activates an operational rule,
creates an alert, or invokes a provider.

## 12. Test Matrix

- contracts: unknown fields, duplicate keys, invalid IDs, non-finite values,
  oversized documents, prohibited content, and version incompatibility;
- graph: cycles, dangling/unreachable nodes, arity/type errors, multiple
  outputs, depth/node/fan-in/cost bounds, commutative stability, ordered-node
  sensitivity, and visual round-trip;
- CEL: unknown variables, unchecked expressions, non-Boolean returns,
  collections, macros, comprehensions, functions, extensions, selectors,
  indexing, object construction, long literals, depth/cost/size limits,
  corrupted checked bytes, environment drift, and runtime errors;
- temporal: sequence permutations, boundaries, same-timestamp tie rules,
  lateness, watermark closure, absence, duration gaps, aggregate denominators,
  distinct count, schedule open/close, DST gap/fold, cooldown, repeat limits,
  correction, supersession, retraction, restart, replay, and overflow;
- lifecycle: all allowed and denied transitions, immutable versions, ETags,
  RBAC, reasons, audit, rollback, and hard rejection of `active`;
- isolation: cross-department API and direct PostgreSQL row-security negatives,
  including owner/superuser/`BYPASSRLS` role safeguards;
- concurrency: duplicate compile/transition/evaluation claims, expired leases,
  transactional rollback, and outbox idempotency;
- security: no hidden startup worker, no runtime mutation endpoint, no imports
  for network/files/subprocess/eval/exec, no sensitive logs/metrics, and no
  operational alert/provider/action path;
- compatibility: P3.4, Phase 3 release/readiness, P4.0 historical readiness,
  P4.1 historical readiness, migration cycles, and full repository regression;
- evidence: generated-only provenance, exact hardware/runtime declaration,
  dependency identity, at least 90% branch coverage for new P4.2 modules, clean
  regeneration, and explicit claim limitations.

## 13. Stop Conditions

Stop without partial promotion if:

- an accepted P4.0/P4.1 artifact or source binding changes unexpectedly;
- CEL checked output cannot be structurally inspected and bounded;
- any authoring-only field can change the semantic digest;
- canonical results differ across generated permutations or replay;
- an absence result is emitted before watermark closure;
- state eviction, correction, suppression, or overload becomes silent;
- an `active` or operational path is reachable;
- a cross-department row is visible through application or database access;
- source, logs, metrics, or exceptions retain prohibited values;
- a new dependency, network action, model/data/media access, deployment action,
  or remote Git action would be required.

## 14. Delivery Sequence

1. Preserve this plan, research, contract catalog, threat model, and exact start
   package on the isolated planning branch.
2. Obtain exact `D-P4.2-START` owner authorization.
3. Perform the P4.1 historical-verifier transition first.
4. Implement contracts, generated fixtures, canonical compiler, and CEL adapter.
5. Implement pure temporal nodes, generated evaluator, persistence, lifecycle,
   API, observability, and migration.
6. Run focused, property, generated, PostgreSQL, compatibility, full-suite,
   packaging, supply-chain, and clean-source validation.
7. Seal one evidence package and request separate exact P4.2 acceptance.

The owner may authorize the entire bounded local generated-only implementation
in one start decision. Intermediate routine edits and validation do not require
separate approvals as long as every path and boundary remains inside that exact
package. Any scope expansion requires a new digest-bound authorization.
