# P5.0 Security Controls

Status date: 2026-09-06

Scope: generated-only operator contracts; no operational runtime

## Trust Boundary

P5.0 assumes a future same-origin backend-for-frontend. The browser is an
untrusted presentation and interaction client. It does not become an authority
for role, department, capability, freshness, review, ETag, reason,
idempotency, evidence, or action outcomes.

The following direct browser paths are closed by contract:

- camera, ONVIF, RTSP, HLS, WHEP, recording, and snapshot endpoints;
- databases, event brokers, evidence stores, and model runtimes;
- map, reference-data, workflow, telemetry, or other external providers;
- credentials, tokens, secret references, certificates, and private keys;
- persistent storage of sensitive application state.

P5.0 does not implement the BFF or claim those controls exist in a deployed
system. It defines the boundary that later runtime work must prove.

## Server-Authoritative Capability Model

Every action is constrained by three ordered gates:

1. The server must allow the action for the current user and department.
2. The accepted policy ceiling must include the action and must not deny it.
3. The active resource profile must support its presentation cost.

A denial at any gate is final for the client. The resource profile can disable
dense visualization or multi-monitor presentation, but it cannot create a role,
grant a command, cross department scope, or override the policy ceiling.

The generated capability matrix explicitly denies direct camera/provider
access, identity confirmation, recording, snapshots, operational dispatch, and
autonomous actions.

## Data Minimization

Generated payload validation recursively rejects these field classes:

- usernames, passwords, credentials, tokens, and authorization values;
- secrets, secret references, certificates, and private keys;
- camera, stream, HLS, and other media locators;
- raw media bytes;
- registration-like text that could be mistaken for an issuable vehicle mark.

All generated payload roots declare `generated_only: true`. Fixture namespaces
use `syn_case_` or `syn_gis_` identifiers and do not carry realistic names,
plates, addresses, biometric values, watchlists, cases, or evidence.

## Navigation And Browser State

Routes are local canonical paths. Each route defines an exact set of allowed
query keys. Query values use a bounded safe-character grammar. Unknown keys,
excess keys, path traversal, absolute URLs, protocol-relative paths,
fragments, and credential-bearing values are rejected.

Sensitive state is prohibited in URLs. The contract does not authorize use of
local storage, session storage, IndexedDB, service-worker caches, or browser
logs for sensitive records.

## Error And Telemetry Boundary

`SafeProblemV1` permits only:

- a low-cardinality reason code;
- a localization key;
- one allowlisted recovery action;
- an optional bounded retry delay used only with retry;
- an optional opaque, format-bounded trace reference.

Raw exceptions, response bodies, locators, credentials, media, identifiers,
and security material are absent. Future telemetry must preserve the same
minimized projection.

## GIS Safety

GIS features are generated-only, bounded, and non-operational. Coordinates
must be finite and within longitude/latitude ranges. Polygon rings must close
and contain at least three unique positions. Viewports are ordered and bounded.
Confidence and uncertainty are present together or absent together.

The GIS contract always preserves freshness and correction state. Optional 3D
cannot become authoritative, cannot remove the accessible list, and is default
off. No map provider or network locator is represented in a GIS contract.

## Accessibility As A Safety Control

The map, graph, timeline, data grid, and media surfaces each require an
equivalent non-visual or structured alternative. Alternatives preserve
selection, order, freshness, correction state, and available actions. This
prevents a visual-only path from hiding stale, denied, corrected, or degraded
state from keyboard or assistive-technology users.

## Threat-To-Control Mapping

| Threat | P5.0 control |
| --- | --- |
| Client fabricates authority | Server decision plus policy ceiling; client cannot expand authority |
| Cross-department data leakage | Every producer binding is department scoped |
| Sensitive data enters URL | Exact query-key allowlist and bounded value grammar |
| Locator or credential reaches client fixture | Recursive prohibited-field rejection |
| Realistic generated identifier is mistaken for real data | Synthetic namespace and registration-pattern rejection |
| Resource downgrade hides safety state | Policy and accessibility semantics must remain preserved |
| Map becomes sole source of truth | Authoritative 2D plus accessible list equivalence |
| Optional 3D changes operator authority | Guarded, default-off, supplementary-only contract |
| Raw backend failure leaks detail | Sanitized safe-problem contract with no raw detail |
| Stale producer result looks current | Explicit freshness and surface-state contracts |
| UI issues operational command | All P5.0 actions are non-operational and runtime is absent |

## Closed Gates

Security contracts do not authorize security effectiveness claims. Browser
headers, session cookies, CSRF defenses, CSP, CORS, trusted types, sanitizers,
authentication, authorization middleware, audit persistence, network policy,
provider controls, secrets management, scanning, deployment, and penetration
testing remain future implementation and validation gates.
