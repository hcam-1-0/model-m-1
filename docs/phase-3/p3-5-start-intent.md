# P3.5 Start Intent Record

Status: `received_prerequisites_pending`.

On 2026-08-26, `mayank-admin` supplied the exact statement
`D-P3.5-START`. The statement is preserved in
[`p3-5-start-authorization.json`](../../contracts/phase-3/p3-5-start-authorization.json),
but it is not effective implementation authorization because its disclosed
prerequisites were not complete when it was received.

## Prerequisite State

| Prerequisite | Current state |
| --- | --- |
| `D-P3.5-001` synthetic corpus and source policy | Pending owner selection |
| `D-P3.5-002` detector and OCR portfolio | Pending owner selection |
| `D-P3.5-003` normalization, abstention, and consensus | Pending owner selection |
| `D-P3.5-004` privacy, resources, and evidence policy | Pending owner selection |
| Exact model, font, dictionary, generator, dependency, and runtime review | Not prepared; depends on the selections above |

The recommended technical baseline can be selected with:

```text
D-P3.5-001: A
D-P3.5-002: A
D-P3.5-003: A
D-P3.5-004: A
```

Those selections authorize preparation and review of the exact proposed
artifact packet only. They do not authorize downloads or implementation.

## Why The Start Is Not Yet Effective

The start policy requires an exact allowlist. A valid final record must bind:

- the four owner-selected technical decisions;
- each model, weight, font, dictionary, source, generator, package, runtime,
  container, and Unicode artifact by immutable source and digest;
- every permitted host, URL, redirect host, content type, size ceiling, and
  network action;
- the local quarantine, scanning, extraction, SBOM, license, lineage, and
  rollback rules;
- the exact generated-only work packages allowed to run;
- all continuing prohibitions.

The early statement cannot authorize undisclosed future artifacts or network
actions. After the exact packet is prepared and presented, `mayank-admin` must
confirm `D-P3.5-START` against that packet digest.

## Current Boundary

Implementation remains off. No model, font, dictionary, dataset, package, or
source artifact may be downloaded. No dependency, lockfile, container,
application, migration, API, worker, or storage change may be made. Synthetic
generation, training, inference, camera/media access, real registration marks,
Government or owner records, identity, watchlist matching, operational alerts,
deployment, P3.6, and remote Git actions remain prohibited.
