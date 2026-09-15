# P4.2 Start Authorization Proposal

Status date: 2026-09-04

Status: non-effective proposal; exact owner authorization is required before
implementation or rule execution.

## Package

- package ID: `P4.2-START-R0`
- decision ID: `D-P4.2-START`
- path: `contracts/phase-4/p4-2-start-authorization-package.json`
- SHA-256:
  `F1C4B64883A23240FB787E5203CD62395AA025304247028392BCF20218C3D263`
- planning branch: `codex/phase4-rule-authoring-planning`
- planned implementation branch: `codex/phase4-rule-authoring-evaluation`
- accepted base commit: `53242f160e1d6f6d3913fd6479d1d4486f53d094`
- authorization expiry if accepted: 2026-10-04

## Effect

Exact acceptance authorizes one coherent local P4.2 implementation under the
package's path allowlist and boundaries. It includes the P4.1 historical
readiness transition, contracts, generated fixtures, canonical typed compiler,
separate scalar-only constrained CEL adapter, typed temporal evaluator,
immutable lifecycle, migration `0014`, generated-only persistence and APIs,
observability, local validation, evidence sealing, and local checkpoint commits
without push.

It reuses only the existing locked `cel-expr-python==0.1.3` dependency. It does
not authorize changing or downloading dependencies. It permits no more than
eight in-scope source/test/documentation/evidence remediation and reseal cycles.

The implementation must remain generated-only, `operational=false`, default
off, production-forbidden, and unable to reach an `active` rule state. It may
produce simulation and shadow evaluation evidence, but no alert, provider call,
notification, route change, dispatch, enforcement, or other operational action.

## Exact Owner Statement

```text
D-P4.2-START: I, mayank-admin, accept P4.2 start package P4.2-START-R0 with SHA-256 F1C4B64883A23240FB787E5203CD62395AA025304247028392BCF20218C3D263 and authorize its exact bounded local generated-only rule-authoring, canonical-compilation, scalar-only constrained-CEL, typed-temporal-evaluation, immutable-lifecycle, persistence, API, observability, validation, and evidence scope, including the hash-bound P4.1 historical-verifier transition, reuse of the already locked cel-expr-python 0.1.3 dependency, up to eight in-scope remediation/reseal cycles, and local checkpoint commits without push. Rules remain default-off, production-forbidden, operational=false, and unable to enter active state; simulation and shadow results are evidence only. This does not authorize dependency or lockfile changes, installs or downloads, models, datasets, artifacts, inference, cameras or media, external providers or network egress, Government or private data, operational alerts, notification, routing, dispatch or enforcement, Kubernetes or deployment, release, or remote Git.
```

Only this exact statement, or an unambiguous acceptance naming the exact package
ID and digest, makes the start decision effective. `continue`, general approval,
or acceptance of the plan without the package digest does not authorize
implementation.

## Progress Effect

Accepting the start package alone earns no frozen P4.2 points. Progress remains
P4.2 **0/15 (0.0000%)** and Phase 4 **25/100 (25.00%)** until complete weighted
technical gates pass. Technical completion may earn 13 points; the remaining
two require a separate exact evidence-package acceptance.
