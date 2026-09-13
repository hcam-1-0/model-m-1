# P4.2 Rule Authoring And Evaluation Threat Model

Status date: 2026-09-04

Status: planning only; controls are implementation and evidence requirements,
not claims of current protection.

## Protected Assets

- accepted Phase 3, P4.0, and P4.1 evidence and behavior;
- department isolation and authorized rule scope;
- immutable rule meaning, compiler provenance, versions, and digests;
- deterministic event-time and temporal state;
- operator trust in simulation/shadow labels and lifecycle status;
- availability of control-plane and generated evaluation services;
- audit integrity without leaking rule content or event values;
- the boundary preventing rules from becoming alerts or actions.

## Untrusted Inputs

Visual documents, CEL source, labels, descriptions, schedules, node IDs, graph
topology, lifecycle requests, ETags, generated fixture values, P4.1 database
rows, serialized checked expressions, worker checkpoints, and database contents
are untrusted until each boundary validates them.

## Threats And Required Controls

| Threat | Required control | Evidence |
| --- | --- | --- |
| Visual canvas differs from executable meaning | Separate presentation and semantic documents; compiler output is sole authority; bind both digests | Layout metamorphic and round-trip tests |
| Duplicate keys or ambiguous JSON alter digest | Strict parser, duplicate rejection, finite values, canonical UTF-8 serialization | Canonicalization negatives and golden bytes |
| Cycle, dangling edge, hidden node, or unreachable branch | Typed DAG, one output, full reachability, closed arity and port types | Generated graph abuse suite |
| Node IDs or input order make equivalent rules drift | Canonical renumbering; commutative child sorting; ordered-node preservation | Permutation and semantic-change tests |
| CEL escapes into code or host capabilities | No eval/exec/subprocess; no extensions/custom functions; scalar-only host context; structural checked-AST allowlist | Static imports plus compile/evaluate negatives |
| CEL work exhausts CPU or memory | No collections/macros/comprehensions; source/AST/depth/literal/cost ceilings; bounded batches; deadline and circuit breaker | Worst-case generated budget tests |
| Unchecked or swapped CEL is executed | Compile only on control plane; persist checked bytes; bind source/environment/AST digest; reverify before deserialize | Corruption and TOCTOU tests |
| Native CEL dependency crashes or drifts | Exact lock/wheel hashes; compatibility suite; typed failure closes run; no fallback interpreter | Supply-chain and injected-failure tests |
| Arrival order changes temporal truth | P4.1 event time, sequence, watermark, and lateness semantics only | Permutation and replay goldens |
| Absence fires before the system can know absence | Require watermark closure after bounded interval | Late-event and boundary tests |
| DST gap/fold changes schedule behavior | IANA zone plus timezone-data version; store UTC/local/fold projection | DST transition goldens |
| State grows without bound | Fixed windows, keys, events, rules, and checkpoint limits; no silent eviction | Resource exhaustion tests |
| Restart, retry, or worker race duplicates output | Deterministic evaluation key, lease, unique constraint, transaction, append-only revision | Concurrency and recovery tests |
| Late correction rewrites history | Append evaluation revision/retraction; retain prior inputs and digests | Correction chain tests |
| Cooldown or overload silently hides activity | Preserve suppressed count, reason, representative evidence, and health state | Saturation and accounting tests |
| Mutable rule changes after approval | Immutable validated version; every edit creates a new version; hash all dependencies | Mutation and digest-drift tests |
| Rollback edits history | Select prior immutable version via new lifecycle event | Rollback reconstruction test |
| Shadow rule affects operations | `operational=false`; no alert/provider/routing/action dependency; shadow sink only | End-to-end negative side-effect tests |
| Unauthorized activation occurs | `active` absent or rejected in schema, DB, service, settings, and tests | Multi-layer activation denial |
| Cross-department rule or state access | Scope resolution, RBAC, forced PostgreSQL RLS, non-owner product roles | API and direct SQL isolation tests |
| Diagnostics leak rules or event values | Bounded reason codes; no source/labels/IDs/payloads in metrics or exceptions | Log/metric capture tests |
| Generated fixture is mistaken for operational evidence | `generated_only=true`, non-issuable IDs, visible mode, package limitations | Fixture and evidence claim checks |
| Historical verifier is weakened by new source | Verify accepted source from exact local Git commit and immutable package bindings | P4.0/P4.1 historical readiness tests |

## Trust Boundaries

1. API boundary: size, schema, authentication, department, permission, reason,
   ETag, and no-store controls.
2. Authoring boundary: presentation and semantics are separated and digested.
3. Compiler boundary: typed DAG, canonicalization, checked CEL, schedule, and
   static resource budgets.
4. Persistence boundary: immutable versions, append-only lifecycle, forced row
   security, and unique idempotency keys.
5. Evaluator boundary: exact compilation binding, generated inputs only,
   bounded temporal state, deadline, and circuit breaker.
6. Output boundary: non-operational evaluation evidence only; no alert,
   provider, notification, routing, dispatch, or enforcement interface.
7. Evidence boundary: exact generated/static/PostgreSQL results and explicit
   limitations; no operational or scale claim.

## Failure Policy

Malformed, unsupported, ambiguous, oversized, unbounded, cross-scope,
out-of-order, stale, corrupted, or digest-mismatched inputs fail closed with a
typed low-cardinality reason. Incomplete temporal truth remains `pending` or
`abstained`. Resource exhaustion closes the affected generated run visibly.
There is no permissive parser, fallback interpreter, wall-clock substitution,
implicit activation, partial positive result, or operational fail-open mode.

## Residual Risk

Even after the planned controls pass, P4.2 generated evidence will not establish
real-world rule utility, fairness, accuracy, evidentiary admissibility, operator
comprehension, production availability, or deployment safety. The CEL wrapper
is a native extension and must remain pinned and independently monitored.
Operational activation requires later legal, privacy, security, human-factors,
data, performance, deployment, and accountable-owner gates.
