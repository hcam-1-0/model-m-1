# P4.1 Correlation Foundation Start Authorization Proposal

Status date: 2026-09-04

Decision: `D-P4.1-START`

Package: `P4.1-START-R0`

Package path: `contracts/phase-4/p4-1-start-authorization-package.json`

Package SHA-256:
`43EDF72ADE8328AEABE0F295ACC649F76229D233F8B0FB7E2D1D5C2E43B9ECA6`

Status: owner authorization required; non-effective.

## Purpose

This proposal authorizes one bounded local implementation of P4.1. The work
turns generated Phase 3 event envelopes into deterministic, evidence-linked,
non-operational correlation hypotheses. It includes ingress validation,
deduplication, partitioning, event-time windows, the mandatory deterministic
AMEC lane, typed unavailable optional lanes, arbitration, canonical hypothesis
graphs, append-only revisions, persistence, read-only projections,
observability, tests, and evidence.

It does not authorize P4.2 or later work.

## Historical Evidence Transition

P4.0 accepted evidence is bound to implementation commit
`2e35bd28aa33c2ebed6fa0bd6486fb26a7d9655d`. Its current readiness verifier
still compares accepted source-component hashes with mutable live files. P4.1
must evolve some of those files, so leaving that behavior unchanged would
mistake authorized forward development for historical evidence corruption.

The package therefore authorizes one narrow verifier transition:

- P4.0 source components are verified from local Git objects at the accepted
  implementation commit;
- P4.0 package, evidence, acceptance, component digests, and accepted commit
  remain unchanged;
- missing or mismatched commits, objects, paths, hashes, or bindings fail
  closed;
- regression tests prove that the transition preserves, rather than weakens,
  P4.0 verification.

No accepted P4.0 artifact may be rewritten or resealed.

The current pre-authorization result is explicit: the P4.0 readiness tool
passes 16 of 17 checks and fails only `changed_paths_allowlisted`, because its
original P4.0 allowlist does not recognize the new P4.1 planning files. No
accepted component, package, acceptance, or Phase 3 integrity check failed.
P4.1-W1 must repair this expected fail-closed transition state before any other
P4.1 work proceeds.

## Authorized Result

If accepted exactly, the package permits:

1. Recording the exact owner authorization statement.
2. Creating local branch `codex/phase4-correlation-foundation` from the clean
   P4.1 planning checkpoint.
3. Changing only the package's exact additive and existing-path allowlists.
4. Running the mandatory deterministic CPU lane against repository-owned
   generated JSON fixtures only.
5. Running generated/static tests, SQLite migration tests, and the optional
   cached local PostgreSQL/PostGIS test service under the package's isolation
   conditions.
6. Performing at most eight bounded source/test/evidence remediation cycles.
7. Creating local checkpoint commits without push.
8. Stopping at technical completion and preparing a separate, non-effective
   P4.1 evidence acceptance proposal.

## Major Safety Boundaries

- Runtime remains default-off and production-forbidden.
- Application startup cannot automatically start the correlation worker.
- No public event-ingestion, correlation-start, replay, or correction mutation
  endpoint is authorized.
- The Phase 3 outbox is a read-only projection; its schema and publication
  state cannot change.
- Only the deterministic CPU lane may execute, and only on generated fixtures.
- Probabilistic, temporal-graph, model-first, and ensemble runtime lanes remain
  typed but unavailable. Generated lane-result fixtures may test arbitration.
- No output can assert identity, guilt, intent, sensitive traits, or predicted
  criminal risk.
- Every hypothesis remains generated-only, non-operational, and subject to
  mandatory human review.
- P4.1 cannot create alerts, call providers, compile or activate rules, send
  notifications, dispatch resources, or perform enforcement.
- No network, credential, camera, media, model, dataset, artifact, private data,
  Government data, Kubernetes, deployment, or remote Git access is permitted.

## Progress Effect

Accepting this start package authorizes work but earns no progress points.
Progress remains:

- Phase 4: **10/100 (10.00%)**.
- P4.1: **0/15 (0.00%)**.

Passing every technical gate can earn 13 P4.1 points, producing Phase 4
**23/100 (23.00%)** and P4.1 **13/15 (86.6667%)**. The last 2 P4.1 points require
separate exact owner acceptance of the final evidence package, producing Phase
4 **25/100 (25.00%)** and P4.1 **15/15 (100.00%)**.

## Exact Owner Statement

To authorize implementation, the owner must provide this exact decision with
the package digest unchanged:

```text
D-P4.1-START: I, mayank-admin, accept P4.1 start package P4.1-START-R0 with SHA-256 43EDF72ADE8328AEABE0F295ACC649F76229D233F8B0FB7E2D1D5C2E43B9ECA6 and authorize its exact bounded local generated-event correlation implementation scope, including the historical P4.0 verifier transition. This does not authorize models, datasets, artifacts, inference, optional model lanes, cameras or media, external providers, Government or private data, rule activation, operational alerts, dispatch or enforcement, Kubernetes or deployment, or remote Git.
```

Any modification to the package requires a new digest and a new exact owner
statement.
