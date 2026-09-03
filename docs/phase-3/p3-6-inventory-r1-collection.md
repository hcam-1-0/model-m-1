# P3.6 Inventory R1 Authorized Collection Record

Status: completed on 2026-08-30; the single authorized attempt succeeded and is
consumed. This record grants no continuing collection or implementation
authority.

## Decision Binding

`mayank-admin` accepted `D-P3.6-INVENTORY-R1-AUTH` against immutable package
digest
`710D52D5BC9A24A42CCB379355C062095795554F261316C37714819F0DFDDAA7`.
The acceptance authorized one sanitized local read-only attempt on logical node
`LAB-LAPTOP-01` within 24 hours, limited to actions `R1-A01` through `R1-A09`
from the bound collector specification.

The accepted package binds:

- collector specification SHA-256
  `31FA80AA79B90AEA32CED930FA535BA03C96A39469F2E8AE2DD00D45060BDDC6`;
- owned-local generated-only trust policy SHA-256
  `E76D0C56476A98AADDBC7880AD75858B5B61D45CE95802E3FB39557E226C6106`;
- shared `v1alpha1` inventory schema SHA-256
  `C9947BE12888C0A05B29DA0266E2359B107024AF07E536AE10BAC55457C5C7D3`;
- 10-second per-action and 60-second transaction bounds; and
- zero network access, zero raw-output persistence, and no retry after failure.

## Result

The attempt started at `2026-08-30T17:57:21.073Z` and completed at
`2026-08-30T17:57:28.541Z`. It produced:

| Record | SHA-256 |
| --- | --- |
| [`p3-6-inventory-lab-laptop-01-r1.json`](../../contracts/phase-3/p3-6-inventory-lab-laptop-01-r1.json) | `FB061C906D1CE5F7FE3B32B70F6CA5134C486F474E2618B23884466C2E58C76F` |
| [`p3-6-inventory-r1-collection-evidence.json`](../../contracts/phase-3/p3-6-inventory-r1-collection-evidence.json) | `3658758FCC7342B7865C7C0FD340FD408B38562BB1D365B757A74C8B6347FA72` |

The R1 inventory passed the exact pinned shared schema. Its observation time is
`2026-08-30T17:57:26.397Z`, and its maximum policy validity ends at
`2026-08-31T17:57:26.397Z`. Expiry makes it ineligible for a new admission
decision; existence of the historical record does not extend freshness.

The collection intentionally preserved `unknown` for capabilities outside the
allowlist. In particular, it does not establish accelerator availability,
instruction-set compatibility, container or Kubernetes support, scheduler
capability, model/runtime compatibility, decoder capacity, or deployable
resource limits.

No reusable collector or product code was created. The attempt used an
ephemeral, digest-bound orchestration process and persisted only the sanitized
R1 and bounded evidence records. Raw command output was not persisted.

## Gate Effect

This result closes only the pending R1 collection action:

- the owner authorization is accepted, completed, consumed, and no longer
  effective;
- historical R0 remains unchanged;
- R1 is a factual shared-schema input, not an approved capability profile;
- `portable_cpu` remains resolver-ineligible and inactive; and
- `P36-G2` remains `blocked` pending exact runtime, resource, workload,
  compatibility, generated validation, and additional profile evidence.

`P36-G1`, `P36-G4`, and `P36-G5` are unchanged.

## Continuing Prohibitions

The decision and completed attempt do not authorize:

- another inventory attempt or a reusable collector;
- profile resolution, activation, admission, or placement;
- model or AI runtime import, loading, inference, or benchmarking;
- hardware, accelerator, performance, stress, capacity, or thermal testing;
- containers, Docker, Kubernetes, or scheduler actions;
- cameras, streams, media, datasets, private data, or Government data;
- network or external-environment access;
- deployment; or
- remote Git operations.

A new attempt after expiry or invalidation requires a new explicit,
digest-bound authorization.
