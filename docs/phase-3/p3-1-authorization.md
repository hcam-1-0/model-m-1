# P3.1 Planning And Authorization Record

Decision ID: `D-P3.1-001`

Date: 2026-08-24

Status: `authorized_for_implementation`.

Accountable owner: `mayank-admin`.

Machine record:
[`p3-1-authorization.json`](../../contracts/phase-3/p3-1-authorization.json).

## Owner Instruction

The owner directed the project to complete P3.1 planning and authorization.
This instruction accepts the plan in [P3.1 plan](p3-1-plan.md) and authorizes
its bounded implementation scope.

## Authorized Work

- P3.1 contract and manifest code;
- deterministic generated fixtures and programmatic synthetic assets;
- annotation, QA, split, duplicate, and leakage validators;
- offline generated-fixture metric reports;
- metadata-only candidate records;
- source/license/provenance research without downloads;
- reproducibility tooling and evidence indexing; and
- owner-controlled approval records under DR-0026.

## Source Authorization

Only source tier `S0`, generated metadata and programmatic assets without
external source material, is authorized for direct use.

`S1` team-created media requires an exact owner record before use. `S2` public
datasets/fonts and `S3` model code/artifacts are research-only and cannot be
downloaded. `S4` private-camera media and `S5` Sentinel/Government/private/
scraped data are prohibited in P3.1.

## Review Policy

Accountable-owner review is sufficient. A separate reviewer is optional. This
does not waive evidence, license, provenance, privacy, security, QA,
reproducibility, retention, deletion, rollback, or audit requirements.

## Hardware Baseline

`LAB-LAPTOP-01` is authorized for generated correctness and small CPU baselines.
It cannot support production, GPU, C10/C50, or statewide claims.

## Non-Authorization

This decision does not authorize external downloads, training, fine-tuning,
model export, inference, decoding, cameras, Sentinel video, real/private/
Government data, raw-media persistence, operational alerts, P3.2, pilots, or
deployment.

## Completion Meaning

P3.1 planning and authorization are complete. P3.1 implementation is not
complete. P3.1 may be accepted only after every exit gate in the machine record
has reproducible repository evidence and explicit owner acceptance.
