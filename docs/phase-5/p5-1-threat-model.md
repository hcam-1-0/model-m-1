# P5.1 Shared Application Foundation Threat Model

Status: proposed planning control baseline

Authority: `D-P5.1-PLAN-AUTH`

## Assets

- operator session and reauthentication state;
- department, role, purpose, field, action, and feature capabilities;
- authoritative HTTP resources, ETags, idempotency keys, and reason contracts;
- investigation, evidence, alert, camera, and operational metadata projections;
- route, query, event, error, localization, workspace, and capability contracts;
- UI source, dependencies, build output, source maps, and provenance;
- Gujarat GIS visual, interaction, safety, and accessibility parity;
- auditability of operator intent and server outcomes.

## Trust Boundaries

1. Operator and browser.
2. Portal application and shared workspace packages.
3. Browser and same-origin BFF.
4. BFF and H-CAM backend services.
5. HTTP authority and non-authoritative event delivery.
6. Browser memory, URL, and local preference storage.
7. H-CAM source and pinned final-ui reference source.
8. Build tools, dependency registry metadata, and produced assets.
9. Browser capability observations and server policy ceiling.
10. Independent windows and operator workspaces.

## Threats And Required Controls

| Threat | Example | Required P5.1 control |
| --- | --- | --- |
| Client authority escalation | Hidden route or edited capability enables a command | Server reauthorizes every request; client defaults denied; route and action manifests are projections only |
| Department confusion | Cached record from department A appears after switching to B | Context-keyed cache, cancellation, event disconnect, memory teardown, bootstrap barrier, isolation tests |
| CSRF | Malicious origin submits a state change using session cookies | Synchronizer token in custom header, Origin and Fetch Metadata checks, SameSite defense, unsafe methods fail closed |
| Session theft | Script or URL exposes a token | Secure HttpOnly host cookie, no browser bearer-token storage, no token in URL/log/telemetry, CSP and XSS controls |
| XSS and injection | Untrusted label becomes executable markup | Contextual escaping, no arbitrary HTML, strict CSP, Trusted Types evaluation, schema and length bounds |
| Contract confusion | Response shape or enum changes silently | Pinned schema digest, strict runtime validation, explicit compatibility policy, fail-closed authority/state enums |
| Over-broad network | Component fetches arbitrary locator | Same-origin transport, operation-ID registry, no arbitrary URL API, CSP `connect-src`, static import checks |
| Unsafe retries | A review or mutation is repeated | Commands default no retry; idempotency, ETag, reason, explicit operator recovery |
| Event spoof/replay | Event enables a control or overwrites newer state | Typed envelope, scope/version/sequence checks, invalidate then HTTP revalidate, event never grants authority |
| Stale truth | Operator acts on old data | Visible observation/freshness/completeness, stale command denial, bounded revalidation |
| Sensitive persistence | Search, IDs, evidence, or cache remains on disk | Memory default, URL allowlist, bounded harmless preference schema, no persistent query cache/service worker baseline |
| URL disclosure | Free text or sensitive identifier enters browser history | Typed route/query allowlist with opaque IDs and bounded enums only |
| Error disclosure | RFC problem detail leaks internal data | Safe mapper retains only allowlisted codes and fields; raw payload and exception discarded |
| Telemetry disclosure | Resource IDs or coordinates become labels | Low-cardinality schema, prohibited-field tests, no payloads/free text/URLs/identities |
| Capability fingerprinting | Raw GPU or hardware identity is collected | Coarse purpose-bound feature probes, no vendor IDs, no persistent fingerprint, safe-low default |
| Resource exhaustion | Dense grids/maps freeze a laptop | Profile budgets, virtualization, cancellation, concurrency limits, deterministic degradation, stable layout |
| Inaccessible control | Map-only or pointer-only action blocks an operator | Native-first semantics, keyboard/focus contract, accessible list/table equivalence, manual evidence |
| Localization ambiguity | Translated label changes legal/operational meaning | Stable IDs, reviewed catalogues, canonical codes/timestamps, no business logic from localized strings |
| Cross-window leakage | Sensitive state broadcasts between control-room windows | Independent data sessions, no resource BroadcastChannel, server workspaces with version checks |
| Portal coupling | One app imports another and inherits hidden behavior | One-way package graph, public exports, cycle and forbidden-import checks |
| Supply-chain compromise | Dependency or build plugin injects code | Exact pins, lockfile integrity, license/SBOM/vulnerability/provenance evidence, controlled scripts, reproducible build |
| Source-adoption contamination | Legacy reference or outputs enter production bundle | Hash-bound intake, path allowlist, provenance, build exclusion, bundle scan, parity migration |
| GIS degradation | WebGL failure removes situational access | Capability gate, typed unavailable state, complete list/table path, no-downgrade parity tests |
| Service worker residue | Prior data remains available after logout | No service worker baseline; future use needs separate threat model and purge evidence |
| Clickjacking | Operator UI is embedded by another site | CSP `frame-ancestors`, compatible frame headers, no unsafe embedding |
| Reverse tabnabbing | External link controls the operator tab | No arbitrary external links; allowlist and `noopener`/`noreferrer` where approved |

## High-Risk Data Exclusions

The shared foundation must not place any of the following in a URL, local
storage, telemetry attribute, console log, client exception report, source map,
or generated planning/test fixture:

- credentials, secrets, session identifiers, CSRF values, bearer tokens;
- stream, camera, ONVIF, provider, map, tile, or storage locators;
- names, faces, plates, owner/registration data, watchlist terms, biometrics;
- investigation narratives, evidence content, source bytes, legal holds;
- precise coordinates, free-form operational reasons, raw server errors;
- Government, police, private, or personal data.

## Security Invariants

1. Navigation visibility never equals authorization.
2. An event never confirms a mutation or grants capability.
3. A stale or incompatible capability state cannot enable an action.
4. Department change completes teardown before new data can render.
5. Mutation retries require a user-visible, contract-defined path.
6. Raw external or backend error content never reaches presentation or
   telemetry.
7. Safe-low resource mode cannot remove policy, review, provenance, or
   accessibility information.
8. Profile detection cannot collect a durable hardware fingerprint.
9. Legacy source cannot enter a production bundle before provenance and parity
   gates pass.
10. GIS renderer failure cannot remove the equivalent operational list path.

## Planned Verification

- package graph and forbidden-import scans;
- route and operation allowlist checks;
- API, problem, event, capability, URL, preference, and telemetry hostile
  vectors;
- CSRF, Origin, Fetch Metadata, session expiry, logout, and reauthentication
  scenarios;
- XSS payload corpus across text, labels, tables, map properties, and errors;
- department-switch cancellation, cache destruction, and stale-event tests;
- ETag conflict, idempotency, duplicate command, and unsafe-retry tests;
- storage, history, console, telemetry, source-map, and bundle prohibited-field
  scans;
- low-resource exhaustion, cancellation, downgrade, and recovery tests;
- keyboard, focus, zoom, contrast, forced-colors, reduced-motion, screen-reader,
  and list-equivalence evidence;
- English, Gujarati, Hindi, pseudo-locale, long-text, timezone, and script tests;
- dependency integrity, license, SBOM, vulnerability, provenance, install-script,
  and reproducible-build evidence;
- final-ui source intake, build-exclusion, attribution, and GIS parity checks.

## Residual Risks Requiring Later Evidence

- exact CSP feasibility depends on the final build output, map workers, and
  deployment headers;
- browser accessibility requires human testing beyond automated tools;
- dependency vulnerability and maintenance state can change after planning;
- locale quality requires qualified human review;
- capability and performance budgets require execution on declared hardware;
- source adoption requires license, asset, attribution, and authorship review;
- GIS and media compatibility require later approved browser/runtime tests;
- no planning artifact proves production security or operational readiness.

## Stop Conditions

Future implementation must stop closed if it would require browser credentials,
direct camera/provider/map access, arbitrary destinations, real data, hidden
authority, unsafe retries, persistent resource caches, unbounded telemetry,
accessibility removal, GIS workflow downgrade, an unreviewed dependency, an
unattributed source import, or a change to accepted historical artifacts.

This threat model is planning only and does not authorize implementation or
execution.
