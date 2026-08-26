# P3.5 W5 Exact Latin PaddleOCR Baseline

## Status

`P35-W5_exact_Latin_Paddle_OCR_adapters_and_generated_evaluation` is locally
implemented and generated-only validated under the effective
`D-P3.5-START` allowlist. This record does not accept the package, promote a
model, choose a quality threshold, authorize a camera or media input, or widen
the existing Phase 3 boundary.

## Implemented Boundary

W5 adds:

- an in-memory 5x7 code-defined Latin/digit/hyphen renderer for deterministic
  `DATA-PLATE-GEN-R0` tokens;
- exact raw-output contracts for `OCR-L0` and `OCR-L1` with immutable artifact,
  dictionary, renderer, adapter, and runtime lineage;
- strict scalar, script, whitespace, alternative, confidence, latency, and
  result-shape validation;
- an `E:`-only archive extractor that requires the authorized SHA-256 and exact
  three-file inventory, rejects traversal, links, special entries, duplicates,
  expansion beyond bounds, symlink roots, and unexpected existing content;
- an isolated CPython 3.12.13 worker using PaddleOCR 3.7.0,
  PaddlePaddle 3.3.1, CPU `paddle_static`, and explicit local `model_dir`;
- socket creation, name-resolution, and connection denial before PaddleOCR is
  imported, plus offline environment flags and external-only cache/temp roots;
- identifier-free aggregate evaluation with no OCR output, alternative,
  generated token, sample ID, region ID, crop pixels, path, or media retained;
- development-then-validation sampling that cannot open the frozen final-test
  split;
- exactly 20 output/confidence replay checks per candidate.

No repository dependency, lockfile, migration, API, worker service, database,
container, model, font, image, or video artifact was added.

## Exact Artifacts

| Candidate | Archive SHA-256 | Extracted inventory SHA-256 |
| --- | --- | --- |
| `OCR-L0` / `PP-OCRv6_small_rec` | `DA460F968CE9F88325AC3A34FA302077D6E9B0DCEFB16BA3137CD7796F879D06` | `692cd53d9fb002538e81c9e0b91a6636ade0a82dc9a914809c3598cec686bf84` |
| `OCR-L1` / `PP-OCRv6_medium_rec` | `4EECC1C6A4623765042E6FC15446DA0DA110B7D875B6B72B2D351D2B2DBD4DA6` | `7a12028567618504b96caf997e7afdf77ceea54dbab142c09299e3844d53fb6f` |

The reviewed model archives and extracted files remain outside Git under
`E:\h-cam-research-cache\phase-3`. No W5 path uses `B:`.

The shared embedded recognition dictionary is pinned as
`sha256:a98ac29121eec9aef70836341b9d35806da7939b4f0fe1e20443acc00d915adc`.
PaddleOCR's official text-recognition interface supports an explicit local
`model_dir`; W5 always supplies that path and never relies on a default model
download. See the [PaddleOCR text-recognition module documentation](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/module_usage/text_recognition.en.md).

## Generated Baseline

The tracked evidence is
`contracts/phase-3/p3-5-latin-ocr-evaluation.json`, SHA-256
`3AEA54734015CCE7E6C8CCABFDBE02310F028268393EACD9A31B4BA6DFA42A20`.
Each candidate processed the same 12 generated samples: eight development and
four validation samples. Nine were single-line and three were two-line.

| Metric | OCR-L0 | OCR-L1 |
| --- | ---: | ---: |
| Valid bounded outputs | 12/12 | 12/12 |
| Exact raw matches | 7/12 | 9/12 |
| Single-line exact matches | 7/9 | 9/9 |
| Two-line exact matches | 0/3 | 0/3 |
| Raw edit distance / reference scalars | 18/156 | 15/156 |
| Replay output deterministic | yes, 20/20 | yes, 20/20 |
| Blocked network attempts | 1 | 1 |
| Network access performed | no | no |
| Measured p50 latency | 45.8982 ms | 474.2033 ms |
| Measured p95 latency | 262.3148 ms | 674.4527 ms |

Latency is a one-run local-laptop observation, not a service-level objective or
capacity claim. The blocked network-attempt count records guard activity only;
no destination, request, or external response was retained.
The Python socket guard is defense in depth for this isolated local run; it is
not a substitute for host or deployment egress controls. Deployment remains
unauthorized.

## Interpretation

The medium challenger produced the stronger generated raw-match baseline, but
W5 does not select it. The two-line results show that passing a whole two-line
crop to a line recognizer is not sufficient. A future bounded improvement can
evaluate deterministic row segmentation or a separately reviewed multi-line
recognition strategy, but it must not tune against the frozen final-test split.

The renderer is intentionally narrow and code-defined. Results do not estimate
accuracy on real plates, CCTV, adverse weather, compression, Indian
registration formats, public datasets, private data, or Government data.
No quality threshold or model-promotion decision has been made.

## Verification

```powershell
uv run --frozen python tools\phase35_latin_ocr.py extract --candidate all
uv run --frozen python tools\phase35_latin_ocr.py check-evidence
uv run --frozen python tools\phase35_contracts.py check
uv run --frozen python -m pytest tests\test_analytics_anpr_ocr.py tests\test_phase35_latin_ocr.py -q
```

Re-running inference changes measured latency fields and is therefore a new
evidence observation. It must not silently overwrite accepted evidence.

## Continuing Prohibitions

- no physical camera, ONVIF, Sentinel, stream, file, URL, upload, or arbitrary
  image input;
- no real, public, private, scraped, Government, police, registration, owner,
  vehicle, watchlist, or identity data;
- no plate-text persistence, normalization, record lookup, alert, enforcement,
  cross-camera linkage, or deployment;
- no model download, training, fine-tuning, `PLATE-D0`, Tesseract, unlisted
  model/font/dictionary, P3.6 work, remote push, pull request, or merge.
