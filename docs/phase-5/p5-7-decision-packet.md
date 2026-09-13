# P5.7 Owner Decision Packet

Status date: 2026-09-12

Status: twelve decisions pending; implementation remains closed

## How To Decide

Each decision selects architecture and acceptance policy only. Selection does
not authorize implementation, dependency changes, browser execution, real
systems/data, deployment, final acceptance, or remote Git. After all twelve
selections, a reconciled planning package and separate exact start package are
still required.

## D-P5.7-001: Final Acceptance Policy

### A. Strict mandatory gates with explicit environment limitations, recommended

Require every selected mandatory test cell to pass, zero unresolved blocker or
critical failures, no unexplained skips, immutable predecessor evidence, and a
complete limitation register. Missing optional environments may remain
`blocked` only when the accepted profile explicitly allows that limitation.

This gives the strongest honest local milestone without pretending that
generated or unavailable environments were validated.

### B. Risk-tiered acceptance with owner exceptions

Allow noncritical failed mandatory cells through scoped, expiring exceptions
with compensating controls. Useful for time pressure, but exception governance
can obscure systematic quality debt.

### C. Aggregate quality-score threshold

Accept above a weighted score such as 95 percent. Easy to summarize, but a high
score can hide one severe accessibility, isolation, truth, or security failure.

### D. Demonstration acceptance only

Accept when the golden demo works. Fast, but insufficient for an enterprise
operator platform and inconsistent with the frozen P5.7 scope.

## D-P5.7-002: Cross-Portal Journey Portfolio

### A. Fourteen canonical journeys plus bounded pairwise variants, recommended

Use J01-J14 as mandatory narratives, materialize generated negative/recovery
variants, and apply pairwise browser/locale/viewport/profile coverage. This
gives broad interaction coverage without an unbounded Cartesian explosion.

### B. Six core journeys only

Focus on alert, investigation, evidence, camera/live, administration, and
degradation. Faster, but leaves correction, revocation, localization,
supply-chain, and no-provider behavior weakly integrated.

### C. Full Cartesian journey matrix

Run every journey against every browser, locale, viewport, profile, workload,
and state. Maximum breadth but impractical, slow, and likely to generate noisy
duplicate evidence.

### D. Portal-specific tests without cross-portal narratives

Cheapest, but misses the highest-risk handoff, teardown, chronology, and
authority failures.

## D-P5.7-003: Browser Compatibility Baseline

### A. Tiered Edge plus Chromium, Firefox, and WebKit, recommended

Run every portal and critical journey in installed Microsoft Edge, smoke and
critical journeys in Playwright Chromium/Firefox/WebKit, and explicit
unsupported behavior for unavailable engines. Do not download automatically.

### B. Microsoft Edge only

Matches the current Windows operator environment and is efficient, but does
not validate engine portability.

### C. Every journey in all four browser targets

Stronger breadth than A but substantially increases runtime and failure
triage, especially for identical generated paths.

### D. Physical-device and enterprise browser fleet

Best field confidence, but requires hardware, managed browser images, network,
and a separate authorization/environment that P5.7 planning does not have.

## D-P5.7-004: Accessibility Evidence Baseline

### A. WCAG 2.2 AA layered evidence with WCAG-EM-style reporting, recommended

Combine axe/ACT-aligned automation, semantic/component assertions, keyboard,
focus, zoom/reflow, target-size, contrast, reduced-motion, error-state,
authoritative-alternative, and explicit manual screen-reader protocols. A
conformance claim remains blocked until the declared manual evaluation is
actually performed by qualified evaluators.

### B. Automated axe checks only

Fast and repeatable but cannot establish keyboard usability, meaningful focus,
screen-reader flow, reflow quality, or complete WCAG conformance.

### C. Manual review only

Captures human usability but is difficult to reproduce and weak at large
systematic rule coverage.

### D. WCAG 2.2 AAA as the release target

Ambitious but not generally achievable across all content and not justified by
the accepted product requirements. Individual AAA improvements can still be
recorded under A.

## D-P5.7-005: Localization And Time Baseline

### A. English, Gujarati, Hindi, pseudo-expansion, and UTC separation, recommended

Require message completeness and semantic equivalence for `en-IN`, `gu-IN`,
and `hi-IN`; 30/60/100 percent expansion; hostile Unicode; `Asia/Kolkata` and
UTC display; explicit `Intl` formatting; and canonical locale-independent
ordering.

### B. English only for final acceptance

Lowest effort but contradicts the planned Gujarat operator context and hides
layout/semantic defects in Gujarati and Hindi.

### C. Add every scheduled Indian language now

Broad future reach, but translation ownership and validation are not defined
and would dilute evidence quality.

### D. Automatic machine translation at runtime

Dynamic but creates network/model/privacy/accuracy risks and is outside scope.

## D-P5.7-006: Viewport, Device, And Profile Matrix

### A. Seven deterministic viewports with pairwise resource profiles, recommended

Use mobile, tablet, constrained laptop, standard desktop, full HD, control
room, and logical dual-display viewports. Apply R01-R06 through a bounded
pairwise matrix and run all critical low-resource/standard/control-room cells.
Emulation remains explicitly distinct from physical-device evidence.

### B. Desktop and control-room only

Optimizes the primary operating context but leaves tablet, mobile continuity,
constrained laptop, and reflow risk under-tested.

### C. Full Cartesian viewport/profile/browser/locale matrix

Maximum combinations but excessive cost and duplicated evidence.

### D. Physical device and multi-monitor lab only

Higher physical fidelity but unavailable within the current generated-only
boundary and poor as the only deterministic regression layer.

## D-P5.7-007: Performance And Bundle Gates

### A. Context-qualified hard budgets with explicit exceptions, recommended

Gate interaction, LCP/CLS reference metrics, long tasks, route/table/map
readiness, query fan-out, event recovery, generated media admission/teardown,
Chromium heap diagnostics, initial/deferred bundle sizes, and profile
convergence. Every result records environment, workload, percentile, and
limitation. No automatic budget relaxation.

### B. Core Web Vitals only

Familiar but misses operator-specific tables, maps, query fan-out, media,
teardown, and resource-profile behavior.

### C. Advisory performance reporting

Avoids blocking release but permits severe regressions to remain unresolved.

### D. Throughput-first acceptance

Prioritizes C50 totals even when interaction, accessibility, or low-resource
usability degrades. This conflicts with functionally complete low-resource
requirements.

## D-P5.7-008: Scale Methodology

### A. Deterministic generated C1/C10/C50 workloads, recommended

Use typed domain work items, generated event bursts, paginated tables, bounded
maps/graphs, and deterministic media admission. Compare state digests and
budgets across profiles. Describe results as UI/workflow scale only.

### B. C1 functional validation only

Efficient but cannot expose queueing, pagination, rendering, fan-out, or
degradation defects.

### C. Generated stress beyond C50

Useful later for finding limits, but the accepted model has no production-like
backend or hardware baseline. Run only as non-gating research after C50.

### D. Fifty real cameras and operational data

Would provide different evidence but is explicitly outside scope and requires
authorized infrastructure, media, privacy, and operational controls.

## D-P5.7-009: Resilience And Recovery Validation

### A. Deterministic typed fault matrix with fail-closed convergence, recommended

Inject generated HTTP, event, session, concurrency, map, media, profile, and
storage-state failures. Require bounded retry, explicit degraded states,
authoritative refetch, teardown, focus recovery, and stable terminal digests.

### B. Happy-path plus a few manual failures

Faster but difficult to reproduce and insufficient for the accepted degraded
state model.

### C. Randomized chaos in the browser suite

May discover novel issues but harms reproducibility. Random exploration may be
added as non-gating evidence only after deterministic faults pass.

### D. Real service/network outage exercises

Valuable for deployment validation but outside generated-only P5.7 and not
possible without authorized services and network.

## D-P5.7-010: Security And Privacy Validation

### A. Layered generated security, redaction, storage, and supply-chain gates, recommended

Use hostile generated inputs, sink and bundled-content inventories, CSP/CSRF
expectation tests, browser storage inspection, department/scope isolation,
telemetry bounds, secret/private-field denial, dependency/SBOM/license checks,
and explicit stale-vulnerability limitations. Do not claim production security.

### B. Add external DAST and vulnerability scanners now

Potentially useful but requires scanner execution, network, update feeds, and
separate retention/trust boundaries.

### C. Manual security checklist only

Readable but weakly repeatable and easy to drift from the actual artifacts.

### D. Defer security to deployment

Unacceptable for a public-safety platform because preventable client and
supply-chain failures would reach a later stage.

## D-P5.7-011: Build, SBOM, And Provenance Baseline

### A. Exact local repeatability plus provenance limitations, recommended

Bind source commit, toolchain, lockfile, installed tree, build command,
environment, output inventory, SBOM/license state, and artifact hashes. Run two
clean same-environment builds if later authorized and compare normalized
outputs. Call it local repeatability, not independent reproducibility or SLSA
compliance.

### B. One successful build and hash

Cheaper but cannot detect nondeterministic output.

### C. Independent second-machine or hosted-builder reproduction

Stronger evidence and a future goal, but requires another trusted environment,
artifact transfer, and separate authorization.

### D. Signed SLSA provenance and release attestation now

Strong future release architecture, but key custody, builder trust, signatures,
distribution, and verification are not available in this phase.

## D-P5.7-012: Evidence Seal And Final Owner Gate

### A. Digest-bound evidence graph and separate exact owner acceptance, recommended

Seal requirements, journeys, matrices, results, environment, artifacts,
limitations, claims, release manifest, source/evidence commits, and canonical
component digest. Revalidate from the sealed package, then require an exact
owner statement for the final 1/12 point.

### B. Automatic acceptance when CI is green

Efficient, but CI cannot judge environment limitations, unsupported claims,
unperformed manual checks, or owner risk decisions.

### C. Human sign-off without exact package digest

Simple but ambiguous about which source, outputs, failures, and limitations
were accepted.

### D. Majority test pass threshold

Allows one severe failure to be hidden by many low-risk passes and is rejected.

## Recommended Selection Statement

```text
D-P5.7-001: A
D-P5.7-002: A
D-P5.7-003: A
D-P5.7-004: A
D-P5.7-005: A
D-P5.7-006: A
D-P5.7-007: A
D-P5.7-008: A
D-P5.7-009: A
D-P5.7-010: A
D-P5.7-011: A
D-P5.7-012: A
```

This selection records architecture choices only. It does not authorize
implementation, browser/runtime execution, dependencies, real systems/data,
deployment, final Phase 5 acceptance, or remote Git.
