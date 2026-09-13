# P5.2 Command And Situational Awareness Threat Model

Status: proposed controls; implementation and runtime validation unauthorized

## Assets

- department scope and role projection;
- command snapshot revision, freshness, completeness, and degradation truth;
- camera and stream coverage/health summaries;
- alert, review, investigation, and workload summaries;
- spatial features, tiles, styles, layer registry, and drill-down references;
- operator session, selection, filters, viewport, and saved workspace state;
- audit, security, and low-cardinality operational signals.

No real Government, private, camera, media, evidence, identity, registration,
watchlist, or case data is authorized for this planning package.

## Trust Boundaries

```text
Browser shell
  | typed same-origin API boundary
  v
Server authorization and department scope
  | governed aggregate/spatial contracts
  v
Accepted camera, stream, intelligence, alert, investigation and health stores

Browser map renderer
  | renderer-neutral summaries only
  v
Same-origin bounded feature/tile/style resources
```

External providers, public tile services, cameras, ONVIF services, databases,
brokers, object stores, and model runtimes are outside the browser trust
boundary and remain unauthorized.

## Threats And Required Controls

| ID | Threat | Required control | Planned verification |
| --- | --- | --- | --- |
| `T01` | Cross-department feature, count, tile, list, or detail leakage | Server-side deny-by-default authorization on every operation; department derived from the session, not a trusted client parameter | Generated horizontal and vertical authorization vectors |
| `T02` | Role confusion caused by `operations.summary` using intelligence roles | Repair the producer role contract; no client-side role alias or hidden-route workaround | Explicit blocked-contract test for `P5.2-G01` |
| `T03` | Sensitive values in URLs, browser storage, telemetry, errors, or map styles | Opaque references; memory-only transient state; typed safe errors; static prohibited-field scan; low-cardinality signals | Source scan and generated hostile values |
| `T04` | Arbitrary tile/style/glyph/sprite/worker destination or credential exfiltration | Same-origin resources, exact destination allowlist, strict CSP, no credentials in URLs, no environment proxy behavior in producers | CSP and destination contract tests |
| `T05` | Malicious geometry causing excessive CPU, memory, WebGL work, or parser failure | Bbox, geometry type, coordinate, vertex, property, byte, feature, tile, zoom, and time bounds; server simplification; list fallback | Hostile geometry and payload-budget vectors |
| `T06` | Stale or partial data displayed as healthy/current | Per-source freshness, completeness, loss and degradation; no inferred green state; persistent status banner | Missing/stale/partial/degraded state matrix |
| `T07` | Event spoofing, duplication, or reordering changes displayed truth | Events are invalidation hints only; bounded dedupe and refetch; HTTP revision is authoritative | Duplicate, old, unknown and burst event vectors |
| `T08` | Client-side clustering or aggregation becomes an operational fact | Label clustering as display-only; authoritative aggregate/list drill-down; prohibit client risk/coverage conclusions | Contract and copy assertions |
| `T09` | Map selection is mistaken for identity, guilt, evidence, or confirmed alert | Typed feature-kind labels, uncertainty and review state, authoritative detail, no biometric/identity field | Semantic and prohibited-claim fixtures |
| `T10` | Hidden corrections or retractions leave an obsolete operational view | Revision-aware refetch, correction/retraction state, chronology link, selected-feature invalidation | Correction and supersession vectors |
| `T11` | Saved workspace leaks scope or restores an unauthorized selection | Server-owned opaque workspace, ETag, scope revalidation, bounded non-sensitive fields, revocation behavior | Scope-change, revocation and conflict tests |
| `T12` | Multiple windows continue after logout, role change, or kill switch | Per-window session validation, event/poll invalidation, fail-closed route state, no token broadcast | Generated independent-window state tests |
| `T13` | Accessibility failure prevents equivalent access to spatial records | Authoritative synchronized list/table, keyboard and focus contracts, non-color state, status announcements, map skip path | Static/component/browser tests and later manual AT gate |
| `T14` | Resource exhaustion on low-capability hardware | Profile-specific feature/tile/concurrency caps, list-first fallback, abort superseded requests, no unbounded animation/prefetch | Generated C1/C10/C50 and profile admission tests |
| `T15` | Raw server/provider details leak through errors | RFC 9457 safe mapping, bounded reason taxonomy, no raw exceptions, locators, SQL, URLs, coordinates or headers | Hostile problem-response fixtures and source scan |
| `T16` | Clickjacking, script injection, compromised worker, or dependency substitution | Existing CSP/security headers, same-origin worker, no unsafe HTML, exact dependency/lock/SBOM/provenance evidence | Build-time policy, dependency review and browser security checks |
| `T17` | Visual overlap, unstable layout, or map canvas resize hides status or controls | Stable grid tracks, minimum/maximum dimensions, overflow ownership, resize observer bounds, narrow/zoom/multi-monitor screenshots | Browser screenshots and overlap assertions in later scope |
| `T18` | Operator overload from unbounded alerts or flashing updates | Server budgets, deterministic pagination, grouped safe priority bands, reduced motion, polite bounded announcements | Burst fixtures, announcement budgets and motion tests |

## Fail-Closed State Priority

When states conflict, render the most restrictive truthful state:

```text
denied
  > incompatible or unsupported
  > failure
  > degraded
  > partial or unavailable
  > stale
  > loading or recovery
  > complete and fresh
```

This ordering does not collapse distinct causes in the underlying details. It
only prevents a less restrictive visual state from hiding a more serious
condition.

## Security Invariants

1. Browser visibility never grants backend authority.
2. The session, department and exact operation are checked on every request.
3. Coordinates, camera IDs, record IDs and user/department values never become
   telemetry dimensions.
4. No operational conclusion is produced from client-only geometry, clustering,
   sorting, cache state, profile selection, or missing data.
5. The map is disposable; lists and detail operations remain authoritative.
6. A low-resource mode preserves safety and accessibility semantics.
7. Any unknown destination, layer, feature kind, status, authority class,
   schema version, or error reason fails closed.

## Residual Risks Requiring Later Evidence

- exact MapLibre dependency and worker CSP behavior in supported browsers;
- map keyboard and screen-reader behavior with the selected implementation;
- real assistive-technology verification;
- capacity and memory bounds on declared laptop and control-room hardware;
- spatial producer query plans, PostGIS indexes, and server-side isolation;
- public-safety policy review of terminology, priority bands, time windows,
  retention and role assignments;
- security review of any future tile provider, geocoder, saved workspace or
  multi-window coordination mechanism.
