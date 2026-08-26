# P3.5 W1 Contracts And Guardrails

Work package: `P35-W1`

Status: `validated_complete`

Authority: `D-P3.5-START`

This package establishes the generated-only ANPR boundary before any generator,
OCR adapter, or model execution is introduced. It adds no endpoint, database
table, migration, worker, setting, external dependency, artifact extraction, or
network action.

## Implemented Contracts

The machine-readable bundle is
[`p3-5-anpr-contracts.json`](../../contracts/phase-3/p3-5-anpr-contracts.json).
It defines:

- `GeneratedTokenRequestV1`: a strict seed-only source request;
- `EphemeralSyntheticTokenV1`: in-memory ground truth that is explicitly
  persistence-prohibited;
- `SyntheticAnprExecutionPolicyV1`: default-off, generated-only, zero-network,
  zero-download, zero-retention execution policy;
- fixed request, nesting, node, and local-sample ceilings;
- one approved source, `DATA-PLATE-GEN-R0`;
- one input mode, `deterministic_seed_only`.

The tracked request fixture contains only immutable generator/policy versions,
seed, sample index, script, layout, source, and synthetic classification. It has
no token, text, file, URL, upload, bytes, camera, stream, owner, vehicle,
watchlist, or registration field.

## Non-Issuable Token Policy

Core synthetic tokens use the exact visible shape `SYN-XXXX-XXXX`, represented
by `^SYN-[A-Z0-9]{4}-[A-Z0-9]{4}$`. The payload must contain at least one ASCII
uppercase letter and one ASCII digit.

The policy is disjoint by construction: every value outside the visible `SYN-`
namespace is denied. This rejects real-looking registration strings without
embedding or claiming an authoritative Government registration grammar. Lower
case, Indic script mixing, controls, extra separators, excessive length,
letters-only payloads, and digits-only payloads fail closed.

The token object exists only for ephemeral generated ground truth. It cannot be
serialized by the P3.5 evidence serializer.

## Prohibited-Input Guard

`authorize_generated_request` performs these checks before returning a typed
request:

1. recursively rejects prohibited keys at any nesting level;
2. rejects bytes and non-JSON values;
3. rejects URL, data URI, file URI, absolute path, UNC path, traversal, bearer,
   and private-key-shaped values;
4. enforces depth, node-count, and 4 KiB request ceilings;
5. requires an explicitly enabled development/test policy;
6. applies strict Pydantic validation with unknown fields forbidden;
7. collapses validation failures to low-cardinality value-redacted reason codes.

Reason codes include `runtime_disabled`, `production_forbidden`,
`prohibited_input_field`, `prohibited_input_value`,
`arbitrary_bytes_prohibited`, `document_too_large`, `document_too_deep`,
`document_too_many_nodes`, `invalid_generated_request`,
`invalid_synthetic_token`, and `plate_text_persistence_prohibited`.

No rejected token, URL, path, credential-shaped value, or free text is included
in the boundary exception message.

## Zero-Retention Guard

`canonical_anpr_evidence_json` rejects:

- the complete ephemeral token model;
- `token`, `plate_text`, `plate_number`, `registration_mark`, `raw_text`,
  `normalized_text`, `ocr_text`, and `alternatives` at any nesting level;
- non-JSON or oversized evidence documents.

The contract permits identifier-free aggregate evidence only. W1 creates no
persistence implementation and no plate-text-bearing log, metric, event, audit,
database, export, cache, or backup path.

## Deterministic Verification

```powershell
uv run --locked --extra dev python tools/phase35_contracts.py check
uv run --locked --extra dev pytest -q tests/test_analytics_anpr_guardrails.py tests/test_phase35_contracts.py
uv run --locked --extra dev python tools/phase35_readiness.py --strict --json
```

Snapshot rewriting requires the explicit
`--acknowledge-reviewed-change` argument. CI verifies the tracked bundle and
fixture on Python 3.12, 3.13, and 3.14.

## Continuing Blocks

No generator, OCR runtime, model loading, or API is added by W1. `P35-W2`,
downloads, repository dependency changes, training, `PLATE-D0`, Tesseract,
cameras, media, arbitrary input, real/private/Government data, owner/vehicle
lookup, watchlists, alerts, deployment, P3.6, and remote Git operations remain
outside this work package.
