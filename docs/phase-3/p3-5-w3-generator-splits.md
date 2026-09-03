# P3.5 W3 Deterministic Generator And Sealed Splits

Work package: `P35-W3`

Status: `validated_complete`

Authority: `D-P3.5-START`

This package adds deterministic generation of visible non-issuable synthetic
tokens and a sealed, token-free split manifest. It consumes only the reviewed
`SyntheticCorpusPlanV1` seed hierarchy and the default-off W1 execution policy.
It does not accept text, files, URLs, uploads, bytes, cameras, streams, owner or
vehicle records, watchlists, or other external entropy.

## Generator

The implementation uses domain-separated SHA-256 over canonical JSON. It does
not use `random`, environment state, system time, network data, process state,
or platform-dependent hashing. The generator:

- requires the exact generator, token-policy, and split-policy versions;
- derives one request ID and unsigned 32-bit seed from the plan, split
  namespace, and zero-based sample index;
- selects the single-line or two-line layout deterministically;
- emits the exact `SYN-XXXX-XXXX` shape in memory;
- forces at least one ASCII uppercase letter and one ASCII digit;
- validates every request through the W1 generated-only boundary;
- fails closed if a token collision occurs anywhere in a corpus build.

The generated token object remains `EphemeralSyntheticTokenV1`. W3 adds no
token serializer, file writer, cache, database, event, log, metric label, API,
or export path.

## Seed Namespaces

The four independent namespaces are:

- `p35w3:contract_fixture:v1`;
- `p35w3:development:v1`;
- `p35w3:validation:v1`;
- `p35w3:final_test:v1`.

The canonical fixture has 4 contract, 8 development, 4 validation, and 4 final
test entries. Request IDs, sample IDs, and sample-spec digests are unique and
split indexes are contiguous. Changing the root seed or plan ID changes the
requests, ephemeral tokens, manifest entries, and manifest digest.

## Sealed Manifest

[`p3-5-sealed-splits-v1.json`](../../contracts/phase-3/fixtures/p3-5-sealed-splits-v1.json)
contains 20 token-free entries. Each entry records only:

- deterministic request and sample identifiers;
- a digest of the token-free sample specification;
- split and independent seed namespace;
- sample index and layout;
- logical generator-profile and font-partition labels;
- synthetic/non-issuable classification.

The SHA-256 manifest digest binds canonical content. Models reject changed
content with the old digest, duplicate identifiers/digests, reordered entries,
non-contiguous indexes, count drift, namespace mismatch, or holdouts outside
final test.

The logical `font_partition` labels do not identify, load, or render a font.
They reserve separation for a later explicitly authorized rendering package.
Likewise, `generator_profile=holdout` is a partition label, not a second image
generator or hidden augmentation path.

Final test is fixed with `final_test_frozen=true`,
`final_test_tuning_allowed=false`, and zero recorded accesses. At least one
final-test entry reserves the generator holdout and at least one reserves the
font holdout. Non-final entries must remain `primary` for both dimensions.

## Zero Retention

The sealed manifest fixes:

- `token_text_persisted=false`;
- `token_commitment_persisted=false`;
- `duplicate_token_count=0`;
- `external_input_count=0`.

It contains no `token` key, `SYN-` value, token hash/commitment, plate text, OCR
alternative, camera/stream identifier, or owner/vehicle/Government field. Token
uniqueness is checked in memory before the strings are discarded from the
manifest build.

## Verification

```powershell
uv run --locked --extra dev --extra analytics python tools/phase35_contracts.py check
uv run --locked --extra dev --extra analytics pytest -q tests/test_analytics_anpr_generator.py tests/test_phase35_contracts.py
uv run --locked --extra dev --extra analytics python tools/phase35_readiness.py --strict --json
```

Tests require 20 exact replay runs and cover deterministic seed changes,
cross-split ID separation, token grammar and uniqueness, final-test freeze,
holdout leakage, manifest tampering, count ceilings, disabled execution,
invalid split/index rejection, token-free serialization, and a forced token
collision.

## Continuing Blocks

No rendering, OCR, model, artifact, media, API, migration, worker, database,
external dependency, network action, real/private/Government data, camera,
stream, owner/vehicle lookup, watchlist, alert, deployment, P3.6, remote push,
pull request, or merge is added by W3. `P35-W2` remains blocked. W3 does not
authorize any later package beyond the exact existing `D-P3.5-START` allowlist.
