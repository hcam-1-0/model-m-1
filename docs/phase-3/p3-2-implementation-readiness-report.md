# P3.2 Implementation Readiness Report

Status: `accepted`

Scope: `phase3.p3_2.generated_only_cpu_detection`

Decision recorded: [`D-P3.2-ACCEPTANCE`](p3-2-acceptance.md)

## Authorized Result

The exact `DET-R0-ONNX-UPSTREAM-0.1.1RC0` artifact is usable through the
default-off ONNX Runtime CPU adapter with deterministic `DATA-GEN-R0` inputs.
The implementation provides generated-lab assignment activation, anonymous
normalized observations, transactional outbox records, bounded retention,
aggregate observability, and fail-closed runtime behavior.

This result does not authorize cameras, ONVIF media, Sentinel streams, real or
public datasets, Government or private data, training, identity or biometric
processing, operational alerts, deployment, artifact redistribution, or remote
Git actions.

## Final Evidence

| Check | Result |
| --- | --- |
| Analytics and release contract drift | Pass |
| P3.0 and accepted P3.1 compatibility | Pass; accepted history remains unchanged |
| Full repository tests | 645 passed, 5 PostgreSQL-only skips, 119 subtests passed |
| Branch coverage | 91.04%; required minimum 90% |
| PostgreSQL 18 migration | Upgrade to `0009`, downgrade to `0008`, and re-upgrade passed |
| PostgreSQL integration | 5 passed, including concurrent claims and queue deduplication |
| Ruff and compile validation | Pass |
| Dependency compatibility | 72 installed packages compatible |
| Dependency vulnerability audit | No known vulnerabilities |
| Wheel and source distribution | Build and isolated install passed for `hcam-core 0.2.0` |
| Archive boundary | 79 wheel members and 383 sdist members; no `.onnx` file bundled |
| Generated real-model E2E | Succeeded in 206 ms; exact artifact digest verified |
| Frame lifetime and replay | Zero retained leases; idempotent replay passed |

The generated block fixture produced zero candidates at the approved
threshold. This is execution and safety evidence only. It is not model
accuracy, representativeness, fairness, latency, capacity, pilot, or deployment
evidence.

## Package Binding

The canonical package includes every P3.2 implementation, contract, migration,
test, workflow, documentation, dependency-lock, and compatibility-verifier
change. This report is intentionally outside the digest to avoid self-reference.

Final package SHA-256:
`F8673BE6AD8D8CABFA4636DA1505DE4C816398B115073B1F5261B03D2B0C7BCF`

## Acceptance Result

Accountable-owner acceptance of the exact final package digest was recorded on
2026-08-25. The strict implementation verifier reports `accepted` with zero
failures and zero manual gates. P3.3 and every prohibited capability remain
unauthorized until a separate decision explicitly changes those boundaries.
