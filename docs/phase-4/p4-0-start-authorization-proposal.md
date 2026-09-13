# P4.0 Start Authorization Proposal

Decision: `D-P4.0-START`

Package: `P4.0-START-R0`

Package SHA-256:
`58E490D767B810743FAF47B3709DF12B0071EEDDD5E50C96A3A7D1CE8E38DFB2`

Status: owner authorization required; non-effective.

Application baseline commit:
`e2ba37b1d7be9f3186feab5b25ff3c9ad32c1990`

Target local branch: `codex/phase4-contracts-guardrails`

Implementation branch base: the clean local planning checkpoint whose first
parent is the application baseline and whose only additions are the exact R2
acceptance and P4.0 start-proposal records. The checkpoint commit is reported
after sealing; this avoids a self-referential package digest.

Accepted planning baseline: `P4-PLANNING-R2`, SHA-256
`B8F4371A8DDD350F44321E70F5FB8CEE0DD27299A26082A40460086E80DDEA63`.

## Purpose

This package converts the accepted Phase 4 architecture into one bounded P4.0
implementation decision. It replaces repeated source, test, remediation, and
evidence approval messages with one exact local build authority while retaining
fail-closed scope, immutable accepted records, exact evidence, and a separate
P4.0 exit acceptance.

The package is not effective until `mayank-admin` accepts its exact SHA-256.
The current planning acceptance did not authorize implementation.

## Authorized Result

After exact owner authorization, P4.0 may produce:

- closed, versioned contracts for chronology, bounded GeoJSON, provenance,
  intelligence rules, evidence-first hypothesis graphs, flat projections,
  AMEC lane results, alert aggregates, provider metadata, review decisions,
  investigation timeline entries, retention holds, and future operator states;
- default-deny validation that rejects identity assertions, biometric or
  sensitive-trait inference, raw provider data, arbitrary destinations,
  credentials, executable expressions, authority escalation, and unbounded
  payloads;
- additive revision `0012_intelligence_control_plane`, descending from
  byte-exact revision `0011_geometry_events`;
- the eleven planned intelligence stores, application department filters, and
  forced PostgreSQL row-security defense in depth;
- a default-off API skeleton for draft control-plane records and bounded read
  models, using department scope, typed roles, reasons, ETags, audit, no-store,
  and the existing transactional outbox;
- generated-only fixtures, negative tests, migration evidence, a threat model,
  readiness validation, and a separately reviewable P4.0 acceptance proposal.

P4.0 may define optional lane, provider, alert, timeline, and UI-facing state
contracts. It may not execute those capabilities.

## Runtime Boundary

P4.0 is a contract and control-plane foundation. It contains no correlation
worker, model lane, rule evaluator, provider transport, provider query, alert
transition worker, notification, dispatch, or enforcement integration.

The generated control plane is disabled by default and forbidden in production.
Provider records contain metadata and opaque policy references only, are forced
to `enabled=false`, and contain no locator, query payload, username, password,
token, certificate, or secret value.

Every police-intelligence record has `mandatory_review` authority. Generated or
system-health contracts may represent bounded automation, but cannot confirm
identity, threat, guilt, intent, or an enforcement decision. Future autonomous
action remains absent or hard-disabled.

## Data Boundary

All executable tests and examples use invented, non-issuable generated records.
No real names, registration marks, faces, biometric templates, watchlists,
cases, vehicle-owner records, camera identifiers, media, location histories,
Government records, or private records are allowed.

References are opaque, digest-bound identifiers. Source media is never copied.
No external provider or network destination is contacted.

## Persistence And Compatibility

Revision `0012_intelligence_control_plane` must be additive and downgrade to
`0011_geometry_events` without modifying any earlier migration. Historical
Phase 3 readiness evidence continues to validate its own accepted boundary.
The current application schema head advances to `0012`, while an explicit
Phase 3 boundary constant preserves the meaning of `0011`.

SQLite remains the single-process development path. PostgreSQL/PostGIS tests
must prove constraints, forced row security, non-superuser assumptions, and
direct cross-department denial. A disposable local PostgreSQL/PostGIS service is
permitted only after owner authorization, only when its image already exists,
only with generated data and local connectivity, and only for resources created
by the P4.0 test run. Pulling or building an image is not authorized.

The existing `stream_event_outbox` and audit log remain shared infrastructure.
P4.0 may persist unpublished generated-only outbox records for atomicity tests,
but may not run a dispatcher or publish operational events.

## Compatibility Transitions

Seven current files may change, each bound to the pre-change SHA-256 in the JSON
package. Changes are limited to application registration, default-off settings,
new typed roles, revision/readiness requirements, generated test fixtures, the
current migration-head assertion, and additive CI checks.

The following remain immutable:

- every accepted R2 planning file and `planning-package.json`;
- the R2 acceptance record and this proposal's source acceptance summary;
- all existing Phase 3 contracts, decisions, evidence, documentation, and
  migrations through `0011_geometry_events`.

No accepted historical package may be silently resealed to match new bytes.

## Combined Local Build Authority

Exact owner authorization permits up to eight coherent local source, generated
test, documentation, evidence, and repair cycles within the path allowlists.
It also permits local checkpoint commits on
`codex/phase4-contracts-guardrails` without push.

It does not permit dependency or lockfile changes, downloads, external network
access, remote Git, destructive changes to unrelated local resources, or any
path outside the package. A scope or immutable-hash mismatch stops work.

## Completion Gates

The technical package cannot exceed **8 / 100 Phase 4 points** or **8 / 10 P4.0
points** before separate owner acceptance. It must show:

- canonical positive and negative contract fixtures;
- prohibited-field and authority-escalation denial;
- SQLite upgrade, downgrade, re-upgrade, and drift evidence;
- PostgreSQL/PostGIS forced row-security and department-isolation evidence;
- API RBAC, department, ETag, reason, no-store, audit, and outbox evidence;
- production denial and absence of all runtime or external integration paths;
- at least 90% branch coverage for the new intelligence package;
- clean focused and full tests, Ruff, package build, dependency check, and
  Phase 4.0 readiness result;
- unchanged accepted Phase 3 and R2 artifacts;
- reproducible evidence and package digests from a clean local checkout.

Only a later exact owner acceptance of that evidence earns `P4.0-D`, making
P4.0 **10 / 10** and Phase 4 **10 / 100**. P4.1 remains unauthorized.

## Continuing Prohibitions

This package does not authorize models, datasets, artifacts, inference,
cameras, ONVIF, Sentinel, streams, media, recording, snapshots, playback,
external providers, credentials, secrets, Government or private data, identity
or biometric processing, operational alerts, notifications, dispatch,
enforcement, autonomous action, Kubernetes, cloud, pilot, production,
deployment, push, pull, fetch, PR, merge, or release.

## Exact Owner Statement

```text
D-P4.0-START: I, mayank-admin, accept P4.0 start package P4.0-START-R0 with SHA-256 58E490D767B810743FAF47B3709DF12B0071EEDDD5E50C96A3A7D1CE8E38DFB2 and authorize its exact bounded local generated-only implementation scope. This does not authorize models, datasets, inference, cameras or media, external providers, Government or private data, operational alerts, dispatch or enforcement, Kubernetes or deployment, or remote Git.
```
