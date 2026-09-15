# P5.7 Contract And Evidence Gap Matrix

Status date: 2026-09-12

Status: planning inventory; no producer, test, runtime, or deployment implementation authorized

## Reading The Matrix

These gaps are not defects by definition. They are missing final validation,
evidence, or authoritative producer contracts that must be implemented,
blocked, or explicitly carried as limitations before Phase 5 acceptance.

- **B**: blocks P5.7 technical completion unless implemented and passed.
- **C**: conditionally blocks when the selected owner profile requires it.
- **L**: may remain as an explicit release limitation; it cannot be shown as
  passed or silently omitted.

## Journey, Replay, And Chronology Gaps

| ID | Class | Gap | Required disposition |
| --- | --- | --- | --- |
| P5.7-G01 | B | No canonical manifest spans all nine operator surfaces. | Define exact surfaces, routes, prerequisites, states, and terminal assertions. |
| P5.7-G02 | B | No final generated cross-portal journey catalogue is sealed. | Materialize J01-J14 with stable IDs and bounded steps. |
| P5.7-G03 | B | Existing subphase replays do not share one final seed/clock policy. | Define canonical seed, virtual clock, ID, and ordering rules. |
| P5.7-G04 | B | Cross-portal handoff parameters are not validated as one chain. | Validate allowlisted opaque parameters and reject injection/overreach. |
| P5.7-G05 | B | Event invalidation and authoritative HTTP confirmation are tested per domain, not end to end. | Add gap, duplicate, delay, refetch, and convergence assertions. |
| P5.7-G06 | B | Correction/retraction impact is not replayed through Command, Intelligence, Investigation, and Evidence together. | Validate append-only propagation without erasure or truth inflation. |
| P5.7-G07 | B | No final chronology check binds record sequence, event time, display time, and localized time. | Verify canonical ordering and qualified dual-time display. |
| P5.7-G08 | B | No deterministic cleanup assertion covers drafts, queries, events, selections, and generated media across all surfaces. | Add logout, department switch, capability revoke, and teardown checks. |

## Contract And Compatibility Gaps

| ID | Class | Gap | Required disposition |
| --- | --- | --- | --- |
| P5.7-G09 | B | No single catalogue maps all Phase 5 request, response, event, problem, and command versions. | Build a canonical compatibility manifest. |
| P5.7-G10 | B | Consumer compatibility across current and one accepted prior contract revision is not final-gated. | Define forward/backward acceptance and explicit unsupported behavior. |
| P5.7-G11 | B | Strong ETag behavior is not validated across every consequential generated workflow. | Test `If-Match`, 412, refetch, compare, reconsider, and no silent retry. |
| P5.7-G12 | B | Idempotency-key reuse, mismatch, lost response, and terminal receipt behavior lack a cross-domain matrix. | Add stable command identity and replay assertions. |
| P5.7-G13 | B | RFC 9457 safe-problem shape and redaction are not verified across all portals. | Validate allowlisted types, status, title, safe detail, and no internals. |
| P5.7-G14 | B | Pagination stability and department isolation are not checked across every list/aggregate. | Add cursor, sort, mutation-between-pages, total, and scope checks. |
| P5.7-G15 | B | Unknown enum, event, state, capability, and profile behavior is not uniform. | Freeze fail-closed fallback and upgrade guidance. |
| P5.7-G16 | B | Producer gaps from P5.0-P5.6 lack one deduplicated final disposition register. | Merge by semantic owner while preserving every historical ID and source. |

## Accessibility Gaps

| ID | Class | Gap | Required disposition |
| --- | --- | --- | --- |
| P5.7-G17 | B | No WCAG-EM-style scope and accessibility-support baseline exists. | Define product scope, AA target, browser/AT baseline, sample, and reporting. |
| P5.7-G18 | B | Automated axe results are not separated from manual and semantic evidence in one final model. | Preserve evidence lane and method per result. |
| P5.7-G19 | B | No all-portal keyboard journey verifies entry, composite navigation, escape, and focus return. | Add deterministic keyboard-only paths. |
| P5.7-G20 | B | Focus-not-obscured behavior is not measured with sticky headers, drawers, dialogs, and alerts. | Add browser geometry assertions and manual review protocol. |
| P5.7-G21 | B | Zoom/reflow at 200 and 400 percent is not final-gated for representative high-density views. | Define sampled views plus universal overflow checks. |
| P5.7-G22 | B | Target-size checks and exception recording are incomplete. | Validate 24-by-24 CSS-pixel target or typed exception. |
| P5.7-G23 | B | Screen-reader evidence lacks an exact execution protocol and unsupported state. | Define AT/browser/version, steps, expected announcements, and evidence. |
| P5.7-G24 | B | Authoritative alternatives are not compared semantically to every map/graph/chart/video/topology state. | Add bidirectional equivalence and stale/error parity checks. |

## Localization And Layout Gaps

| ID | Class | Gap | Required disposition |
| --- | --- | --- | --- |
| P5.7-G25 | B | English, Gujarati, and Hindi message completeness is not measured across all portals. | Inventory stable message IDs and missing/fallback behavior. |
| P5.7-G26 | B | Long-text expansion lacks 30/60/100 percent deterministic fixtures. | Add wrapping, clipping, occlusion, and action-label checks. |
| P5.7-G27 | B | Locale-sensitive number, percentage, list, date, time, and relative-time output lacks canonical fixtures. | Bind explicit locale/timezone and canonical machine values. |
| P5.7-G28 | B | Unicode controls, mixed scripts, normalization, and confusable display behavior are not final-gated. | Add bounded hostile fixtures and safe visible representation. |
| P5.7-G29 | B | Active document and internal language changes are not universally declared. | Verify `lang` semantics and accessible announcements. |
| P5.7-G30 | B | Mobile/tablet/laptop/desktop/control-room layout coverage is fragmented across subphases. | Create one viewport and orientation matrix. |
| P5.7-G31 | C | Multi-monitor evidence is currently viewport projection only. | Record projection limitation or authorize physical multi-monitor validation later. |
| P5.7-G32 | B | Resource-profile switches are not compared for semantic, scope, authority, and focus invariance across every portal. | Add deterministic before/after equivalence. |

## Browser And Performance Gaps

| ID | Class | Gap | Required disposition |
| --- | --- | --- | --- |
| P5.7-G33 | C | Current browser baseline is installed Edge/Chromium-style execution, not accepted Chromium/Firefox/WebKit coverage. | Select required engines and blocked-runtime policy; require each selected and available approved engine. |
| P5.7-G34 | B | Browser versions and executable identities are not bound to final results. | Record engine, channel, version, source, and environment. |
| P5.7-G35 | B | No all-portal cold/warm performance manifest exists. | Define route, interaction, layout, long-task, and readiness budgets. |
| P5.7-G36 | B | Initial and deferred bundle budgets are incomplete for several portals. | Set per-app initial JS/CSS and optional chunk budgets. |
| P5.7-G37 | B | GIS map-idle and authoritative-table readiness are not measured together. | Gate table readiness independently and map readiness secondarily. |
| P5.7-G38 | B | Query fan-out, deduplication, cancellation, and stale-result suppression lack final browser evidence. | Measure exact requests per journey and transition. |
| P5.7-G39 | C | Browser heap measurement is engine-specific and absent from accepted evidence. | Use bounded Chromium diagnostic with explicit non-portable limitation. |
| P5.7-G40 | B | Generated media admission, first-frame, stall recovery, and teardown budgets are not part of one final matrix. | Add no-network C1/C10/C50 generated media checks. |

## Resilience And Concurrency Gaps

| ID | Class | Gap | Required disposition |
| --- | --- | --- | --- |
| P5.7-G41 | B | No unified deterministic fault catalogue spans HTTP, events, maps, media, sessions, and profiles. | Define typed faults and expected safe terminal states. |
| P5.7-G42 | B | Event duplicate/out-of-order/delay/gap behavior is not compared across every consumer. | Add sequence, dedupe, gap, pause, and refetch checks. |
| P5.7-G43 | B | Retryability is not centrally verified against safe problem reasons and command class. | Allow bounded query retry; prohibit automatic consequential retry. |
| P5.7-G44 | B | Session expiry and reauthentication-required behavior lacks a cross-portal state-retention policy test. | Minimize drafts, clear sensitive state, and require explicit resume. |
| P5.7-G45 | B | Department/role/capability transitions do not have one cache and event teardown proof. | Verify query keys, subscriptions, selections, grants, and history state. |
| P5.7-G46 | B | Profile downgrade during map/media/graph work lacks convergence and semantic equivalence proof. | Add in-flight cancellation, fallback, focus, and invariant checks. |
| P5.7-G47 | B | Route-level error boundaries are not tested for containment across all portals. | Prove bounded failure, safe details, focus recovery, and navigation. |
| P5.7-G48 | B | Flake classification, retry policy, and quarantine rules are not frozen. | No retry by default; separate environment/transient/product failure with evidence. |

## Security And Privacy Gaps

| ID | Class | Gap | Required disposition |
| --- | --- | --- | --- |
| P5.7-G49 | B | CSP expectations and browser enforcement/report-only evidence are not final-defined. | Freeze header projection, resource allowlist, violation handling, and limitation. |
| P5.7-G50 | B | CSRF requirements are not traced to every state-changing backend contract. | Map method, origin, token/fetch-metadata, same-site, and rejection behavior. |
| P5.7-G51 | B | Dangerous HTML, URL, style, SVG, map-style, and message rendering sinks lack one static/runtime register. | Inventory sinks and require safe rendering/adapters. |
| P5.7-G52 | B | Browser storage policy is not validated across local/session storage, IndexedDB, Cache API, history, and clipboard. | Prohibit sensitive classes and verify teardown. |
| P5.7-G53 | B | Cross-window and multi-monitor messaging origin/source validation is not final-gated. | Bind allowed origins, message versions, source windows, and teardown. |
| P5.7-G54 | B | Telemetry redaction and cardinality bounds are not exercised across every portal and failure path. | Validate allowlisted attributes and no identity/resource labels. |
| P5.7-G55 | B | Authorization and department isolation remain generated client evidence only. | Keep backend/RLS proof as explicit predecessor/environment requirement. |
| P5.7-G56 | B | Screenshots, traces, reports, and console capture lack one retention and sanitization contract. | Default to zero sensitive retention and bounded generated-only artifacts. |

## Supply Chain, History, And Release Gaps

| ID | Class | Gap | Required disposition |
| --- | --- | --- | --- |
| P5.7-G57 | B | Lockfile, installed tree, SBOM, license, and dependency manifest are not reconciled in one final record. | Bind exact versions, integrity, source, license, and completeness. |
| P5.7-G58 | L | Vulnerability observations may be stale because refresh is not authorized. | Record observation time/source and prohibit `no known vulnerabilities` claims. |
| P5.7-G59 | B | Final build inputs, commands, outputs, and hashes lack one release manifest. | Seal source commit, environment, toolchain, commands, outputs, and digests. |
| P5.7-G60 | C | Reproducible-build evidence is not defined. | Select same-machine repeatability or independent-environment reproduction; qualify result. |
| P5.7-G61 | B | Phase 0 through P5.6 immutable readiness is split across historical verifiers. | Create an aggregate verifier that preserves accepted Git-object checks. |
| P5.7-G62 | B | No final claims and unsupported-feature register prevents marketing overstatement. | Allowlist exact claims and bind each to evidence and limitations. |
| P5.7-G63 | B | Waiver/exception policy for failed budgets or optional cells is not defined. | Require typed scope, owner, evidence, expiry, compensating control, and no blocker waiver by default. |
| P5.7-G64 | B | Final owner acceptance package and post-acceptance state transition are not yet designed as machine-readable contracts. | Seal exact package, progress transition, closed gates, and separate acceptance statement. |

## Summary

| Class | Count | Meaning |
| --- | ---: | --- |
| Blocking | 59 | Must be implemented and pass under the selected final baseline. |
| Conditional | 4 | Required only if selected or if the relevant runtime/evidence is available and declared mandatory. |
| Limitation | 1 | May remain open only as an explicit, claim-limiting record. |
| Total | 64 | Complete final contract/evidence gap inventory. |

Planning completion does not close these gaps. They become implementation
work only after exact planning acceptance and P5.7 start authorization.
