# P4.7 Owner Decision Packet

Status: owner selections pending

Authority: `D-P4.7-PLAN-AUTH`

These are non-effective architecture choices for P4.7 Final Acceptance And
Phase 5 Handoff. Recommendations are engineering proposals, not owner
decisions. `continue`, silence, implementation preferences from another
subphase, or acceptance of this document do not select an option.

Record all twelve IDs explicitly. Composite selections are valid only where an
option states that capabilities coexist. No selection authorizes
implementation; selected decisions must first be reconciled into an exact
planning package and separately accepted.

## Recommended Profile

`C / C / C / C / C / B / C / C / B / B / B / A`

This profile creates a rigorous generated demonstration without making a demo
framework the product. It freezes deterministic inputs, validates semantics at
separate layers, seals an acyclic evidence and claims package, hands Phase 5 a
canonical consumer contract with optional standard projections, treats UI and
accessibility states as engineering contracts, and keeps Phase 5 authority
separate from Phase 4 acceptance.

## D-P4.7-001: Demonstration Orchestration Boundary

### A. Direct domain/repository orchestration

Call repositories and domain functions directly in one local script.

Benefits: fastest and simplest. Costs: bypasses HTTP/service authorization,
reason, ETag, idempotency, audit, and projection behavior, so it is weak
consumer evidence.

### B. HTTP-only black-box orchestration

Drive every step through the local HTTP API and observe only HTTP responses.

Benefits: realistic Phase 5 consumer boundary. Costs: event chronology and
internal generated-only assertions become harder to observe, and setup may be
slow or brittle.

### C. Canonical scenario engine with bounded adapters

Define one canonical scenario/step model. Use an in-process adapter that calls
the same application service boundaries for deterministic generated evidence,
plus separate HTTP and event projection checks. Direct persistence access is
forbidden.

Benefits: deterministic and fast while retaining consumer-contract evidence;
supports future HTTP/event adapters without rewriting scenarios. Costs: adapter
equivalence and bypass-prevention tests are mandatory.

### D. External workflow engine

Adopt a workflow product or orchestration service for the demonstration.

Benefits: rich visualization and retries. Costs: dependency, process,
deployment, credentials, network, and semantics exceed the current boundary.

Recommendation: **C**.

## D-P4.7-002: Acceptance Scenario Portfolio

### A. One golden narrative

Run one event-to-timeline success path.

Benefits: clear demonstration and low cost. Costs: cannot prove denial,
conflict, replay, correction, abstention, or degradation behavior.

### B. Golden path plus four basic failures

Add duplicate, authorization denial, provider outage, and correction cases.

Benefits: reasonable breadth. Costs: leaves lifecycle, concurrency, stale data,
worker recovery, and reconstruction interactions under-tested.

### C. Layered deterministic portfolio

Require one golden narrative plus eight mandatory variants: no-match/
abstention, duplicate/replay, late/conflict, authorization/isolation, reference
degradation, review/lifecycle denial, correction/retraction, and worker/
recovery degradation. Add bounded pairwise contract cases.

Benefits: strongest generated-only coverage per unit of complexity and aligned
with the threat model. Costs: larger fixture and assertion catalogue.

### D. Exhaustive state-space exploration

Generate every reachable combination of states and transitions.

Benefits: broad theoretical coverage. Costs: combinatorial explosion, poor
narrative value, difficult evidence review, and no proof of real-world safety.

Recommendation: **C**.

## D-P4.7-003: Deterministic Time, Identity, And Replay

### A. Fixed seed and wall-clock freeze

Set one seed and monkeypatch current time.

Benefits: simple. Costs: hidden UUID, ordering, timezone, async, and retry
nondeterminism can remain.

### B. Record then replay observed output

Treat the first successful run as the golden record.

Benefits: easy snapshot generation. Costs: the first run can freeze a defect,
and opaque runtime identifiers weaken review.

### C. Manifest-derived determinism with semantic replay

Freeze seed, logical epoch, timezone, identifier namespace, step quantum,
source/durable ordering, policy revisions, fixture hashes, normalization, and
allowed variance. Run two clean attempts and compare normalized semantic
digests.

Benefits: explicit, reviewable, and resistant to incidental runtime changes.
Costs: requires deterministic providers and careful normalization.

### D. Live time and random identifiers

Use production-like clocks and UUIDs and compare only final status.

Benefits: superficially realistic. Costs: poor reproducibility and weak
evidence.

Recommendation: **C**.

## D-P4.7-004: Assertion And Pass/Fail Oracle

### A. Final status only

Pass when the final timeline or alert reaches the expected state.

Benefits: easy to understand. Costs: intermediate security, chronology,
deduplication, and evidence failures can be hidden.

### B. Exact full snapshots

Byte-compare every output from a golden run.

Benefits: detects any change. Costs: brittle to harmless representation
changes and can encourage approval of unreadable snapshots.

### C. Layered semantic assertions with exact immutable inputs

Hash exact fixtures, schemas, policies, and canonical records, then evaluate
independent schema, authorization, chronology, identity, rule, review,
integrity, redaction, recovery, side-effect, replay, handoff, and accessibility
families. All mandatory layers must pass; skip/unknown/incomplete fail.

Benefits: catches meaningful defects while controlling allowed variance.
Costs: more assertion definitions and independent verifier work.

### D. AI/LLM qualitative judge

Ask a model whether a trace appears correct.

Benefits: flexible narrative assessment. Costs: nondeterministic, hard to
audit, model/dataset authority absent, and unsuitable as acceptance truth.

Recommendation: **C**.

## D-P4.7-005: Evidence Integrity And Provenance

### A. Flat file list with SHA-256

Record each artifact path and hash.

Benefits: simple and useful. Costs: weak derivation, producer, completeness,
and claim traceability.

### B. RFC 8785 JCS for every JSON file

Adopt JCS as the canonical encoding for all P4.7 evidence.

Benefits: standardized hashable JSON. Costs: can conflict with accepted H-CAM
canonicalization and adds migration/tooling obligations.

### C. H-CAM canonical evidence DAG with optional standards projections

Use an acyclic component index binding source commit, authorization, inputs,
producer, tool/version, parents, byte length, SHA-256, completeness, and
verification. Preserve accepted H-CAM canonical encoding; add independently
validated RFC 8785, PROV, and SLSA-shaped projections only where useful.

Benefits: strong traceability without changing existing authority or making a
conformance claim. Costs: more package and projection validation.

### D. Signed external attestation service

Upload evidence to a remote transparency or signing service.

Benefits: external trust anchor. Costs: network, credentials, privacy,
deployment, and operational governance are not authorized.

Recommendation: **C**.

## D-P4.7-006: Claims And Known-Limitations Governance

### A. Narrative limitations document

List caveats in Markdown beside the evidence review.

Benefits: readable. Costs: claims can drift away from evidence and are hard to
validate automatically.

### B. Machine-readable claims and limitations plus human summary

Every claim records scope, evidence class, supporting components, freshness,
limitations, status, and prohibited interpretations. Every limitation records
impact, mitigation, future evidence, owner, and affected claims. Generate a
human review from the same records.

Benefits: prevents unsupported claims while preserving reviewer readability.
Costs: requires disciplined vocabulary and cross-reference checks.

### C. Block closeout until every limitation is resolved

Treat any open limitation as failure.

Benefits: strict. Costs: impossible for generated-only work because real-world
validation is intentionally outside Phase 4.

### D. Allow descriptive claims without evidence binding

Use broad product language and a general disclaimer.

Benefits: fast presentation. Costs: misleading and incompatible with H-CAM's
evidence model.

Recommendation: **B**.

## D-P4.7-007: Phase 5 HTTP/API Handoff

### A. Existing OpenAPI snapshot only

Give Phase 5 the generated FastAPI OpenAPI document.

Benefits: low effort. Costs: does not fully explain role/scope, reason, ETag,
idempotency, event links, degradation, action availability, or UI states.

### B. Human endpoint guide only

Write examples and workflow descriptions without a machine-readable contract.

Benefits: approachable. Costs: drifts easily and cannot support compatibility
automation.

### C. Canonical operation catalogue plus pinned OpenAPI projection

Define each operation's purpose, audience, gate, schemas, auth/scope/reason,
ETag/idempotency, pagination/order/freshness, safe errors, examples, events,
actions, UI states, and compatibility class. Generate a pinned OpenAPI
projection and RFC 9457-compatible problem mapping.

Benefits: both machine and human usable; preserves H-CAM-specific security and
state semantics. Costs: requires catalogue-to-OpenAPI equivalence checks.

### D. Generated client SDK as the handoff authority

Treat one generated client as the supported interface.

Benefits: quick Phase 5 integration. Costs: language/tool lock-in and SDK bugs
can obscure the source contract.

Recommendation: **C**.

## D-P4.7-008: Event And Workflow Handoff

### A. Event-name list

List event names and example payloads.

Benefits: simple. Costs: omits producer/consumer, ordering, delivery,
correlation, correction, security, and version semantics.

### B. AsyncAPI-only authority

Adopt AsyncAPI as the canonical event and workflow description.

Benefits: established machine-readable event format. Costs: H-CAM domain
semantics and workflow acceptance rules may be forced into extensions.

### C. Canonical H-CAM catalogues with optional AsyncAPI, CloudEvents, and Arazzo projections

Keep event and workflow semantics in versioned H-CAM contracts. Generate
AsyncAPI 3.1, CloudEvents 1.0.2, and Arazzo 1.1 projections with explicit
mapping, validation, and non-conformance status until proven.

Benefits: rich interoperability without surrendering authority or selecting a
broker. Costs: projection maintenance and version-pinning work.

### D. Broker-specific topics and schemas

Design directly for Kafka, NATS, MQTT, or another broker.

Benefits: implementation specificity. Costs: premature infrastructure and
delivery coupling.

Recommendation: **C**.

## D-P4.7-009: UI State And Accessibility Handoff

### A. Screen and component list

Name the pages, panels, tables, dialogs, and forms Phase 5 should build.

Benefits: quick scope outline. Costs: does not define data states, action
authority, recovery, keyboard behavior, or accessibility.

### B. Typed backend-to-UI state matrix with WCAG/WAI-ARIA requirements

For every view/action, map loading, empty, partial, stale, degraded, denied,
conflict, failure, recovery, correction, and success to source facts, visible
text, actions, focus, keyboard, status announcements, error association,
non-color meaning, target/contrast expectations, and evidence state.

Benefits: gives Phase 5 implementable behavior and accessibility criteria
before visual design. Costs: larger handoff catalogue and future manual audit.

### C. Interactive prototype as the contract

Build a clickable UI prototype and infer behavior from it.

Benefits: easy stakeholder review. Costs: implementation is not authorized and
visual behavior alone is ambiguous.

### D. Main dashboard implementation now

Begin the Phase 5 frontend during P4.7.

Benefits: faster visible progress. Costs: violates phase and authorization
boundaries and risks designing against incomplete contracts.

Recommendation: **B**.

## D-P4.7-010: Consumer Compatibility And Versioning

### A. Exact snapshots only

Reject any handoff change that alters bytes.

Benefits: strong drift detection. Costs: treats compatible documentation and
additive evolution as breaking.

### B. Versioned compatibility matrix and change policy

Freeze canonical snapshots and classify documentation, optional additive,
new-capability, compatible behavioral, deprecation, breaking schema, breaking
semantic, and security-boundary changes. Record supported consumers,
deprecation, migration, and contract evidence.

Benefits: controlled evolution with explicit security semantics. Costs:
requires governance and consumer-contract tests.

### C. Permanent backward compatibility

Support every historical contract indefinitely.

Benefits: minimal consumer breakage. Costs: unbounded maintenance and can
preserve unsafe behavior.

### D. Latest version only

Phase 5 always updates immediately to repository head.

Benefits: simple producer workflow. Costs: high integration risk and no stable
handoff.

Recommendation: **B**.

## D-P4.7-011: Generated Operations And Reconstruction Pack

### A. Manual README commands

Document setup, run, and expected output commands.

Benefits: low effort. Costs: prerequisites, stop conditions, recovery, and
evidence can drift or be skipped.

### B. Typed non-operational runbook plus concise human guide

Define bounded preflight, fixture verification, execution order, expected
outputs, stop/failure codes, resume policy, cleanup, zero-retention check,
reconstruction, evidence sealing, and reviewer checklist in a machine-readable
contract with a human projection.

Benefits: repeatable and auditable while remaining generated-only. Costs:
requires runbook schema and verifier.

### C. Production operations manual

Write deployment, incident, backup, restore, scale, and on-call procedures.

Benefits: future operational value. Costs: unsupported because no operational
environment or targets are authorized.

### D. External test-management platform

Store runs and evidence in a hosted testing tool.

Benefits: collaboration and dashboards. Costs: remote data, credentials,
retention, licensing, and vendor governance are outside scope.

Recommendation: **B**.

## D-P4.7-012: Final Acceptance And Phase 5 Gate

### A. Exact Phase 4 closeout plus separate Phase 5 planning authorization

P4.7 technical evidence can earn P4.7-A through C. The owner then accepts one
exact source commit, evidence package, claims/limitations set, and handoff
digest to earn P4.7-D and close Phase 4. Phase 5 planning requires a separate
explicit decision.

Benefits: clear authority, exact progress, and no accidental phase expansion.
Costs: one additional owner gate before Phase 5 planning.

### B. P4.7 acceptance automatically authorizes Phase 5 planning

One acceptance closes Phase 4 and opens Phase 5 planning.

Benefits: fewer messages. Costs: conflates evidence acceptance with new work
authority.

### C. Partial final acceptance

Close Phase 4 while one or more P4.7 items remain incomplete.

Benefits: schedule flexibility. Costs: contradicts frozen weights and weakens
the handoff baseline.

### D. Automatic closeout when tests pass

No owner acceptance is required.

Benefits: automation. Costs: tests cannot accept residual risks or authorize a
phase boundary.

Recommendation: **A**.

## Required Owner Response Format

Record one option for every ID:

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
D-P4.7-011: B
D-P4.7-012: A
```

After explicit selection, the next permitted action is preparation of a
non-effective reconciled P4.7 planning package. Implementation remains blocked
until that exact package and a later exact start package are separately
accepted.
