# P4.2 Rule Authoring And Evaluation Research Record

Status date: 2026-09-04

Status: primary-source research complete for planning; no implementation,
dependency change, rule execution, or activation is authorized.

## Research Question

P4.2 must turn a visual authoring document into one immutable, typed,
resource-bounded rule representation that can be evaluated deterministically
over generated P4.1 event and hypothesis fixtures. It must preserve the accepted
`D-P4.0-003:A` architecture: visual graph plus typed temporal nodes plus
constrained CEL. The research focused on how to do that without introducing an
arbitrary scripting surface, unbounded evaluation, hidden side effects, or a
second semantic source of truth.

## Findings

### 1. CEL remains the correct stateless predicate layer

The [CEL project](https://cel.dev/) describes CEL as non-Turing-complete,
side-effect-free, host-data-only, and suited to expressions that are evaluated
frequently but changed infrequently. The
[CEL language definition](https://github.com/cel-expr/cel-spec/blob/master/doc/langdef.md)
also makes clear that deterministic evaluation and strong type checking depend
on the embedding application supplying conforming values and a declared
environment.

H-CAM implication:

- compile and type-check on the control-plane path;
- evaluate only a stored, hash-bound checked expression;
- expose a closed scalar context rather than arbitrary JSON or dynamic values;
- provide no custom functions or extension libraries in P4.2;
- keep sequence, absence, windows, counters, schedules, cooldown, and other
  stateful behavior outside CEL in typed H-CAM nodes;
- require a Boolean result and treat every compile/evaluation error as a
  sanitized, fail-closed outcome.

### 2. The existing locked CEL dependency is reusable

The repository already locks `cel-expr-python==0.1.3`. The
[official CEL Python repository](https://github.com/cel-expr/cel-python)
identifies it as the Python wrapper for CEL C++, and documents declared variable
types, checked compilation, serialization/deserialization, and evaluation. It
also exposes optional custom functions and extensions, which P4.2 must not
enable.

H-CAM should reuse the exact locked dependency instead of adding a second CEL
engine. P4.2 must bind the wheel hash, version, license, platform support, SBOM,
and compatibility evidence already used by P3.4. It must create a separate
`hcam.p4-2.constrained-cel.v1` environment instead of weakening or mutating the
accepted P3.4 environment.

The wrapper documentation does not expose the same explicit static and runtime
cost controls documented by
[cel-go](https://github.com/cel-expr/cel-go/blob/master/examples/README.md#12-execution-cost-analysis).
P4.2 therefore cannot claim native CEL cost-limit parity. It must obtain a
strict bound by accepting only scalar variables, rejecting collection/message
construction, selectors, indexing, macros, comprehensions, extensions, and
custom functions, then structurally counting the checked AST under a small
source/AST/depth ceiling. A worker-level deadline and circuit breaker are
defense in depth, not a substitute for the static bound.

### 3. Compiler conformance needs positive and negative fixtures

The [CEL Policy conformance project](https://github.com/cel-expr/cel-policy)
uses explicit environment configuration, policy inputs, expected outputs, and
compile-error fixtures. It emphasizes static type agreement, scope/reference
validation, duplicate detection, and unreachable-branch rejection.

H-CAM will not claim CEL Policy conformance. It will adopt the evidence shape:

- environment manifest;
- accepted source and canonical checked representation;
- positive evaluation goldens;
- exact compile-error reason classes;
- cross-process replay;
- dependency/version drift failures;
- generated abuse cases.

### 4. Semantic and presentation documents need separate digests

[RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html) explains why a stable
canonical representation is needed before hashing JSON. H-CAM's canonical AST
must exclude canvas coordinates, labels, collapsed-panel state, viewport data,
comments, and other UI-only fields. Those fields remain in a separately hashed
authoring document.

The compiler must normalize semantic nodes, preserve order only where order is
meaningful, sort operands of commutative nodes by child digest, reject duplicate
keys and non-I-JSON values, and bind the resulting bytes to the compiler,
contract, temporal-semantics, CEL-environment, and input-schema versions.
Equivalent authoring layouts should produce the same semantic digest; a
semantic change must produce a new immutable rule version.

### 5. Event time and schedules must remain explicit

The Python [`zoneinfo` documentation](https://docs.python.org/3/library/zoneinfo.html)
documents IANA time-zone behavior and the `fold` distinction during ambiguous
clock transitions. P4.2 must evaluate temporal truth from P4.1 event time and
watermarks, not wall-clock arrival order. Absence becomes true only after the
relevant watermark closes the bounded interval. Schedule evaluation stores the
IANA zone, timezone-data version, UTC instant, local projection, and fold value
needed for deterministic replay.

### 6. Allowlisting and sanitized telemetry are mandatory

The [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
recommends allowlisting and server-side syntactic plus semantic validation.
The [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
recommends sanitizing untrusted event data and excluding credentials, sensitive
personal data, connection strings, and other high-classification data from
logs.

P4.2 therefore uses closed schemas and bounded enums at every layer. Logs and
metrics contain only low-cardinality stage/outcome codes. Rule source, user
labels, event values, identifiers, CEL text, checked bytes, and authoring
documents are not metric labels and are not copied into exceptions.

## Selected Planning Baseline

No new architecture choice is required. The accepted Phase 4 decisions already
select the baseline:

1. Visual authoring graph as a UI projection.
2. Canonical typed H-CAM AST as the semantic source of truth.
3. Typed temporal nodes for all stateful behavior.
4. A separate constrained scalar-only CEL environment for stateless Boolean
   predicates.
5. Immutable versions, generated simulation, non-operational shadow comparison,
   and rollback by selecting a prior version.
6. No `active` transition, operational alert, provider contact, dispatch, or
   enforcement under P4.2.

The only next owner decision is whether to authorize the exact bounded
`D-P4.2-START` package after reviewing its digest.

## Residual Questions For Implementation Evidence

These are validation tasks, not architecture decisions:

- prove the exact serialized checked-expression format is stable enough to bind
  inside one pinned dependency version;
- prove all prohibited CEL constructs fail before persistence;
- measure generated scalar-only evaluation cost and freeze conservative limits;
- prove canonical AST equality across input ordering and visual-layout changes;
- prove temporal goldens across late data, watermark closure, DST gaps/folds,
  process restarts, and exact replay;
- prove accepted P3.4 CEL and P4.1 correlation behavior remain byte-for-byte
  historically verifiable after additive P4.2 work.

None of these questions permits a model, dataset, camera, media stream,
external provider, Government/private data, operational activation,
deployment, Kubernetes, or remote Git action.
