# P3.5 Start Intent Record

Status: `historical_intent_superseded_by_digest_bound_authorization`.

On 2026-08-26, `mayank-admin` supplied the exact statement
`D-P3.5-START`. The statement is preserved in
[`p3-5-start-authorization.json`](../../contracts/phase-3/p3-5-start-authorization.json),
and was not effective implementation authorization when received because its
disclosed prerequisites were not complete. It is retained as historical audit
evidence and is superseded by the later final record described in
[P3.5 generated-only start authorization](p3-5-start-authorization.md).

## Prerequisite State

| Prerequisite | Current state |
| --- | --- |
| `D-P3.5-001` synthetic corpus and source policy | Option `A` owner approved |
| `D-P3.5-002` detector and OCR portfolio | Option `A` owner approved |
| `D-P3.5-003` normalization, abstention, and consensus | Option `A` owner approved |
| `D-P3.5-004` privacy, resources, and evidence policy | Option `A` owner approved |
| Exact model/font artifact review | Seven-artifact evidence complete and owner accepted |
| `D-P3.5-RUNTIME-RESEARCH` | Exact dependency closure, runtime SBOM, vulnerability review, Defender scan, and guarded imports complete and owner accepted |

The recommended technical baseline was selected with:

```text
D-P3.5-001: A
D-P3.5-002: A
D-P3.5-003: A
D-P3.5-004: A
```

Those selections do not authorize implementation. The separate artifact gate
authorized only the now-complete exact seven-file quarantine research. It does
not authorize runtime dependency research.

## Why The Early Statement Was Not Effective

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

The early statement could not authorize undisclosed future artifacts or network
actions. After the exact packet was prepared and presented, `mayank-admin`
confirmed `D-P3.5-START` against package digest
`915F5E9246A7A656DF528DD54DA6018D7489C6875BF3A77D1A551BAD6EF9AF4D`.

## Current Boundary

The current boundary is defined only by the final machine-readable start
authorization. It permits five exact artifacts and selected generated-only
local work packages with zero network actions. Training, Tesseract execution,
camera/media access, real registration marks, Government or owner records,
identity, watchlist matching, operational alerts, deployment, P3.6, and remote
Git actions remain prohibited.
