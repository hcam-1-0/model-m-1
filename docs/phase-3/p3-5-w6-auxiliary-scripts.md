# P3.5 W6 Auxiliary Scripts

Status: `validated_generated_baseline` under the exact `D-P3.5-START`
generated-only allowlist. This is not model promotion, operational validation,
camera authorization, or deployment approval.

## Implemented Boundary

`P35-W6_exact_Devanagari_Paddle_OCR_lane_and_Gujarati_font_rendering_only`
adds two isolated auxiliary-script paths:

- Devanagari: deterministic internal text generation, exact `FONT-D0`
  rendering, and exact `OCR-D0` PaddleOCR recognition;
- Gujarati: deterministic internal text generation and exact `FONT-G0`
  rendering only.

The paths cannot create, replace, normalize, transliterate, or raise confidence
in the Latin registration-mark result. They accept no caller text, file, URL,
upload, camera, stream, or media input. Gujarati OCR execution stayed at zero,
and neither blocked Tesseract artifact was loaded.

## Exact Artifacts

| Candidate | Role | SHA-256 |
| --- | --- | --- |
| `OCR-D0` | Generated-only Devanagari auxiliary OCR | `AC8279D27FC7E8CDA559364F9A3C506F43984CF6BA5E1B7A06450458BFE07DFB` |
| `FONT-D0` | Generated Devanagari rendering | `9CE7B04F60E363D8870E5997744CF85CF69D38A4D7D129D364D92A3B14B461D7` |
| `FONT-G0` | Generated Gujarati rendering only | `9901D8552F1DD5D2C50DBD4CAA6F6E174E74E8264F06594AB259AE6E7B1AC428` |

The model archive is safely extracted only to the external runtime under
`E:\h-cam-research-cache\phase-3\p3-5-runtime`. Its extracted inventory is
`sha256:e7f6b0b7cf6e937e56540ba5254d6aed9a1958e5b3bca3a3e7c41b29673a2cb6`.
The repository contains no model, font, image, or media artifact. No W6 path uses `B:`.

## Rendering Constraint

The reviewed Pillow 12.3.0 runtime has FreeType but no HarfBuzz or RAQM. W6
therefore uses `basic_freetype_no_raqm` and a closed, code-defined vocabulary
of standalone letters and digits only. Combining marks, conjuncts, complex
shaping, mixed scripts, arbitrary external text, controls, bidi overrides, and
unexpected whitespace fail closed.

This restriction is material. The evidence is not a claim about general
Devanagari or Gujarati OCR, full orthographic coverage, real plates, or
production typography.

## Isolation And Retention Controls

- exact CPython 3.12.13, PaddleOCR 3.7.0, PaddlePaddle 3.3.1, Pillow 12.3.0,
  and regex 2026.7.19 are revalidated by the isolated worker;
- model and font paths, file sizes, hashes, model members, and the embedded
  dictionary configuration are revalidated before execution;
- socket creation, connection, and name resolution are denied before Paddle is
  imported;
- only CPU `paddle_static` execution against explicitly supplied local model
  paths is allowed;
- generated text, OCR text, alternatives, pixels, sample IDs, and region IDs
  exist only in process memory;
- exceptions and worker failures are reduced to bounded reason codes;
- tracked evidence contains identifier-free aggregates only;
- retention remains zero hours.

## Generated Observation

The tracked 12-sample observation covers four samples in each of `clean`,
`low_contrast`, and `downscaled`, with 48 standalone reference graphemes:

| Slice | Valid outputs | Exact raw matches | Scalar edit distance |
| --- | ---: | ---: | ---: |
| Clean | 4/4 | 4/4 | 0 |
| Low contrast | 4/4 | 3/4 | 1 |
| Downscaled | 4/4 | 3/4 | 1 |
| Total | 12/12 | 10/12 | 2 |

`OCR-D0` replay was deterministic for 20/20 runs. Both `FONT-D0` and `FONT-G0`
rendered 12/12 generated samples and produced identical pixels for 20/20 replay
runs. One Python network attempt was blocked; network access performed remained
false. Gujarati OCR, Tesseract, final-test, external text, camera/media, real
registration-mark, and model-download counts all remained zero.

Canonical aggregate evidence:

- `contracts/phase-3/p3-5-auxiliary-script-evaluation.json`
- SHA-256 `1E58A84AD522EB852F6EECFDCF1BAF38FCDC4337B414836B64EBCD4DADBCB955`

These results are a generated baseline only. No accuracy threshold, confidence
calibration, promotion, legal suitability, operational suitability, or
deployment decision has been made.

## Validation Results

- 68 focused W6, contract-drift, and P3.5-readiness tests passed;
- the complete repository suite passed 903 tests with eight expected
  PostgreSQL skips and one existing Starlette/httpx deprecation warning;
- total branch coverage was 90.66%; the new auxiliary module was 99%;
- Ruff, compileall, canonical contract/evidence checks, and strict P3.5
  readiness passed;
- source distribution and wheel builds passed, and `uv pip check` found no
  dependency conflict;
- the wheel imports the W6 auxiliary API, contains the auxiliary module, and
  contains no model, font, trained-data, image, or media payload.

## Verification

```powershell
uv run --locked python tools/phase35_auxiliary_ocr.py extract
uv run --locked python tools/phase35_auxiliary_ocr.py check-evidence
uv run --locked --extra dev python tools/phase35_contracts.py check
uv run --locked --extra dev python tools/phase35_readiness.py --strict
```

Regenerating the exact-runtime observation is an explicit new measurement and
may change latency fields and the evidence digest. CI validates the tracked
aggregate and never loads external artifacts or executes PaddleOCR.
