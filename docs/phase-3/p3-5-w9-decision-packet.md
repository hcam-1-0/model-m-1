# P3.5 W9 Owner Decision Packet

Status: Option A owner authorized under `D-P3.5-W9-START`; implementation in
progress; W10 remains separate and unauthorized.

Decision ID: `D-P3.5-W9-START`.

Machine-readable proposal:
[`p3-5-w9-scope-proposal.json`](../../contracts/phase-3/p3-5-w9-scope-proposal.json).

Current validated dependency:

- repository head: `b282f1bf45e38bcdfd49f976e974ce92e9d5f08b`;
- P3.5 W1-W8 package digest:
  `96A35F98059918181FD59687BA96A4283ED9885BAD7D34FE1915D6288174C3DF`;
- W8 evidence SHA-256:
  `58E7E4479DEB554D4B99F0CC1868B4DA61E9DED292E3F11942B740AEF02FC124`.

## Why A New Decision Is Required

The effective `D-P3.5-START` record authorizes the zero-retention aggregate
evidence, security, and documentation portion named `P35-W8` in that record.
The broader plan item named `P35-W9` also includes resource, packaging, and
rollback work. Those additions are not enumerated in the effective allowlist.

`continue`, acceptance of W8, or the existing P3.5 start record cannot widen
that authority. This packet defines the exact next scope before execution.

## A. Narrow Generated-Only Closure (Recommended)

Consolidate the already validated W1-W8 results without reopening model,
dataset, or final-test work.

Allowed work:

- build a stdlib-only aggregate evidence checker and canonical manifest;
- prove that the new W9 canonical evidence contains no plate text, OCR
  alternatives, pixels, media, stream/track identifier values, owner data, or
  Government data;
- run bounded deterministic resource stress using generated contract fixtures
  only, without OCR/model execution;
- build wheel and sdist locally, inspect their inventories, and record only
  aggregate counts and cryptographic digests in tracked evidence;
- prove default-off behavior and document the local rollback procedure;
- update tests, CI checks, readiness records, documentation, and backlog;
- prepare the clean-source package for the separate W10 acceptance gate.

The machine-readable proposal fixes an exact file allowlist for this option.
Adding or changing any other path requires a new decision or an amendment bound
to a reviewed proposal digest.

Limits:

- no application runtime or product behavior changes;
- no use of the external `E:` model/runtime cache and no access to `B:`;
- no model or font execution, artifact download, network access, or final-test
  sample opening;
- no new dependency, lockfile, container, migration, API, worker, database,
  persistence, alert, lookup, camera, media, deployment, or P3.6 work;
- generated build archives remain ignored and untracked; only aggregate package
  metadata may be committed;
- W9 completion does not accept P3.5. W10 clean-source validation and explicit
  owner acceptance remain separate.

This is recommended because W5-W8 already pin the exact generated-only runtime
and behavioral evidence. Re-running models would add cost and supply-chain
exposure without resolving a currently open technical question.

## B. Exact Runtime Revalidation

Perform all Option A work and rerun the already approved `OCR-L0`, `OCR-L1`,
`OCR-D0`, `FONT-D0`, and `FONT-G0` generated-only evaluations in the reviewed
external `E:` runtime.

Additional limits:

- the existing exact artifacts and runtime are the complete allowlist;
- runtime network access remains denied;
- no download, training, final-test access, threshold selection, promotion,
  `PLATE-D0`, Gujarati OCR, or Tesseract execution;
- raw text and pixels remain ephemeral and tracked evidence stays aggregate.

Benefit: confirms that the external runtime still reproduces the accepted
baselines. Cost: repeats already validated work and expands time, environment,
and supply-chain handling.

## C. Maximum Generated Benchmark

Perform Option B with a larger generated benchmark, up to the existing 10,000
sample resource ceiling, and collect bounded latency and resource
distributions.

This option requires a second exact execution plan before work starts. That
plan must specify sample counts, split use, time and memory ceilings, artifact
allowlists, abort conditions, evidence fields, and whether any frozen holdout
may be opened. No holdout is authorized by selecting C alone.

Benefit: stronger generated-only resource characterization. Cost: highest
runtime burden and a greater risk of accidental tuning against held-out data.
It still cannot establish real-CCTV accuracy or deployment readiness.

## D. Defer W9

Preserve the validated W8 state and perform no W9 implementation.

Benefit: no added technical or governance surface. Cost: aggregate closure,
package inspection, rollback proof, and W10 preparation remain incomplete.

## Continuing Prohibitions

Every option preserves the following unless a later exact authorization says
otherwise:

- real, public, private, Government, police, or scraped plate/media data;
- real registration marks and owner, vehicle, watchlist, or Government records;
- cameras, ONVIF, Sentinel streams, files, URLs, uploads, and external text;
- identity, biometrics, re-identification, cross-camera linkage, alerts,
  autonomous action, or enforcement;
- training, fine-tuning, `PLATE-D0`, Tesseract, `OCR-G0`, and `OCR-G1`;
- plate-text persistence, APIs, workers, migrations, databases, search, exports,
  backups, logs, traces, or metric labels containing identifiers;
- dependency, lockfile, container, deployment, P3.6+, remote push, pull request,
  or merge changes.

## Required Owner Statement

To select the recommended scope, the owner must provide exactly:

> D-P3.5-W9-START: A

That statement authorizes only Option A as written in this packet and the
machine-readable proposal. It does not authorize W10 acceptance, deployment,
or any continuing prohibition.

Selections `B`, `C`, or `D` must use the same decision ID and selected letter.
No work is authorized by silence, `continue`, `accepted`, or a decision that
omits `D-P3.5-W9-START`.

## Owner Decision Record

On 2026-08-27, `mayank-admin` supplied:

> D-P3.5-W9-START: A

The decision is effective only against proposal SHA-256
`62B711EAF2C1EDD21CBCD07751D9A30EF6FA61C11E9ECB190CE6614FE67AB796`,
planning package digest
`9BCC9E9C068E03E94E5461AABDE3B50A4766498406643EE253AF66ECAD8A9B7B`,
and authorization repository head
`6d546fbe1a074e4090fa6d006a67421a27746afe`. See the
[W9 narrow closure authorization](p3-5-w9-start-authorization.md).
