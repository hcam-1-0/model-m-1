# P3.2 Owner Acceptance

Decision: `D-P3.2-ACCEPTANCE`

Status: accepted by accountable owner `mayank-admin` on 2026-08-25.

Machine-readable record:
[`p3-2-acceptance.json`](../../contracts/phase-3/p3-2-acceptance.json).

## Owner Statement

The owner submitted:

> P3.2 acceptance

This statement was received directly after presentation of the sole pending
P3.2 gate and exact package digest. It is therefore recorded as acceptance of:

`F8673BE6AD8D8CABFA4636DA1505DE4C816398B115073B1F5261B03D2B0C7BCF`

No broader authorization is inferred.

## Accepted Evidence

- Scope: `phase3.p3_2.generated_only_cpu_detection`.
- Package files: 72 immutable digest-bound files.
- Model artifact: `DET-R0-ONNX-UPSTREAM-0.1.1RC0`.
- Artifact SHA-256:
  `427CC366D34E27FF7A03E2899B5E3671425C262EA2291F88BB942BC1CC70B0F7`.
- Input source: deterministic `DATA-GEN-R0` only.
- Runtime: ONNX Runtime 1.29.0 with `CPUExecutionProvider` only.
- Full repository tests: 645 passed, 119 subtests passed, 91.04% coverage.
- PostgreSQL 18: migration upgrade/downgrade/re-upgrade and five integration
  tests passed.
- Package and dependency checks: wheel/sdist, isolated installation,
  compatibility, and vulnerability audit passed.

## Effect

P3.2 is accepted. This closes only the generated-input CPU detection slice,
including its default-off runtime, generated-lab activation, anonymous
normalized observations, transactional outbox, retention, observability, and
documented fail-closed behavior.

The accepted 72-file package is not modified by this post-package decision.
Pre-acceptance status language inside that package remains immutable evidence;
this acceptance record and the readiness report provide the current status.

## Continuing Boundaries

This acceptance does not authorize physical cameras, ONVIF media, Sentinel
streams, real or public datasets, Government or private data, model training or
modification, identity or biometric processing, watchlists, vehicle-owner
lookup, sensitive-trait or criminality inference, operational alerts,
autonomous action, enforcement, pilot or production deployment, performance
claims, artifact redistribution, or remote Git actions.

P3.3 and all later work remain unauthorized until separately planned and
explicitly approved.
