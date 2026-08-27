# P3.5 W7 Normalization, Grapheme Metrics, Calibration, And Abstention

Status: `validated_generated_contract_fixture`.

Work package:
`P35-W7_normalization_grapheme_metrics_calibration_and_abstention`.

Authorization: `D-P3.5-START`, limited to local, generated-only,
production-forbidden, zero-retention, network-denied implementation.

## Implemented Boundary

W7 adds an internal, non-API normalization stage after the existing ephemeral
OCR hypotheses. It accepts only the typed Latin `OCR-L0/L1` and Devanagari
`OCR-D0` generated hypotheses already defined by W5 and W6. There is no file,
URL, upload, camera, stream, arbitrary text, database, worker, or public API
entry point.

The stage performs these operations in order:

1. strict UTF-8, scalar, control, bidi, whitespace, script, and size checks;
2. raw-preserving NFC derivation using Unicode data `15.0.0`;
3. extended grapheme segmentation using exact `regex==2026.7.19`;
4. closed Latin uppercase display derivation with separator preservation;
5. exact non-issuable `SYN-XXXX-XXXX` grammar classification;
6. identity-only generated calibration with five equal-width bins;
7. mandatory abstention because no quality threshold is owner-approved.

Raw OCR output is never changed. NFKC/NFKD, transliteration, dictionary
completion, separator insertion, edit-distance correction, confusable
substitution, language-model completion, owner/vehicle/Government lookup, and
operational acceptance are absent and prohibited.

## Runtime Pin

Extended grapheme segmentation is lazy and fail-closed. It runs only under the
reviewed external runtime:

- CPython `3.12.13`;
- Unicode data `15.0.0`;
- `regex==2026.7.19`;
- root `E:\h-cam-research-cache\phase-3\p3-5-runtime`.

The repository environment does not gain `regex`; `pyproject.toml`, `uv.lock`,
containers, and deployment manifests are unchanged. Missing or changed runtime
versions produce a bounded safe reason and no fallback segmenter is selected.
No W7 path uses `B:`; the only `B:\` source literals are denial assertions.

## Ephemeral Result

`EphemeralPlateNormalizationV1` keeps only process-local derived semantics:

- a digest bound to the raw hypothesis and lineage;
- NFC value, extended grapheme list, and display candidate;
- normalization, grapheme, calibration, abstention, regex, and Unicode versions;
- format family and safe validation outcomes;
- raw and identity-calibrated confidence;
- transform flags and the mandatory abstention reason.

The model is deliberately rejected by canonical evidence serialization. Its
NFC value, display candidate, grapheme values, digest, raw text, alternatives,
and sample/region/result IDs cannot enter tracked evidence.

## Aggregate Evidence

Canonical evidence:
`contracts/phase-3/p3-5-normalization-evaluation.json`.

SHA-256:
`1F233E044976B0B28BD0261CA5B6324403C45B2A158C852B34DCBB7A0144EE8A`.

The evidence is a deterministic contract-semantics fixture, not a model-quality
or real-world accuracy benchmark.

| Slice | References | Hypotheses | Classified synthetic | Unrecognized | Abstained | Grapheme edit distance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Latin | 12 | 12 | 9 | 3 | 12 | 35 |
| Devanagari | 12 | 12 | 0 | 12 | 12 | 3 |
| Gujarati render reference | 12 | 0 | 0 | 0 | 0 | 0 |

Latin fixture differences intentionally cover case derivation and malformed
separator placement without autocorrection. Devanagari remains an independent
auxiliary observation and cannot become or increase confidence in a core plate
result. Gujarati contributes generated rendering-reference grapheme counts
only; Gujarati OCR and Tesseract execution remain zero.

Each of `OCR-L0`, `OCR-L1`, and `OCR-D0` has a separate ten-observation,
five-bin identity-calibration contract fixture. These values prove deterministic
binning, ECE/Brier calculation, and candidate isolation. They do not calibrate
the actual OCR models, set a quality threshold, promote a candidate, or support
an operational claim.

## Evidence Controls

- 20/20 aggregate replay is deterministic.
- One Python socket attempt is blocked; network access is false.
- Model execution and model download counts are zero.
- External text, media/camera, and real registration-mark counts are zero.
- Gujarati OCR, Tesseract, and consensus execution counts are zero.
- Operational acceptance count is zero.
- Raw, normalized, grapheme, alternative, and identifier persistence are false.
- Plate-text retention remains zero hours.
- Quality threshold, promotion, and deployment decisions remain false.

## Validation

- focused W7 tests: `20 passed`;
- combined W7, contract, readiness, and guardrail tests: `99 passed`;
- normalization module branch coverage: `100%`;
- canonical evidence check: passed;
- exact external runtime preview/write check: passed;
- complete repository suite: `925 passed`, eight expected PostgreSQL skips,
  `119` subtests passed, and one existing Starlette/httpx deprecation warning;
- total branch coverage: `90.70%`, above the required `90%` floor;
- repository-wide Ruff, compileall, contract drift, and strict P3.5 readiness:
  passed;
- sdist and wheel build from source with no isolation: passed in a fresh output
  directory after the existing repository `dist` artifact could not be
  overwritten on Windows;
- `uv pip check`: all `76` installed packages compatible;
- built wheel: `107` entries, W7 normalization module present, direct wheel
  import passed, and zero model-weight, font, trained-data, image, video, audio,
  NumPy-array, or other enumerated prohibited payloads;
- wheel SHA-256:
  `FE8DAAD67FA766F45F5163ABEF6D1B9F9CC9EFED21F7CCCDF0C1F0A690C4CA50`;
- sdist SHA-256:
  `DF9D9850221D860A551F240077BFAE6A8C18F653A1EBAB60D5776F5B7716EAC7`.

## Continuing Blocks

W7 does not authorize or implement an operational quality threshold, model
promotion, actual-model calibration evidence, consensus, persistence, API
response, alert, lookup, enforcement, camera/media access, real data, P3.6,
deployment, or remote Git operation. `P35-W8` consensus remains not started.
