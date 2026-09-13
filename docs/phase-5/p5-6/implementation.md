# P5.6 Administration, Security, And Operations Implementation

## Scope

P5.6 implements generated-only Admin Center, Security Center, and additive Platform Operations surfaces. Command Center remains the primary dashboard. Existing P5.3 Camera Catalogue, Camera Detail, Stream Diagnostics, Live Workspace, and Monitor Wall routes remain preserved inside Operations Center.

## Control Model

Administrative changes are typed, revisioned, non-effective proposals. Authorization is server-authoritative, default-deny, department and purpose scoped, and represented with PostgreSQL row-security equivalence. Static and dynamic separation of duty reject self-approval. Strong ETags, revisions, policy revisions, idempotency keys, receipts, and deliberate conflict reconsideration define concurrency behavior.

Security views keep operational, security, audit, evidence, and administrative signal lanes separate. Secret references are opaque and never resolved. Provider, certificate, audit, compliance, exception, attestation, and supply-chain records are generated projections with explicit freshness, completeness, and limitations.

Platform Operations adds qualified service, dependency, queue, worker, circuit, storage, database, event-bus, media-edge, AI-runtime, SLO, degradation, maintenance, recovery, capacity, and topology projections. They are not live telemetry, production targets, hardware claims, deployment states, or executable operations.

## Dynamic Profiles

Low-resource, enhanced-workstation, control-room, owned-GPU-lab, future-server, and future-Kubernetes profiles may change density and rendering only. Authority, truth qualification, scope, available actions, security, and accessibility remain invariant.

## Generated Validation

The deterministic fixture set contains exactly 1,120 generated contract cases under seed `HCAM-P5.6-R0-2026-09-10`, C1/C10/C50 functional workloads, two canonical replays, 48 preserved producer gaps, and 72 threat controls. It contains no real identities, telemetry, secrets, providers, cameras, media, models, operational actions, scanner results, backup/restore execution, containers, Kubernetes execution, or deployment evidence.
