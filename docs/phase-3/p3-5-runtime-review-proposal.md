# P3.5 Runtime Review Proposal

Status: `proposal_prepared_owner_authorization_pending`.

Artifact acquisition did not authorize Python packages, native runtimes,
lockfile changes, archive extraction, or model execution. The next safe step is
`D-P3.5-RUNTIME-RESEARCH`, a separate metadata/dependency quarantine gate.

## Proposed Baseline

- isolated CPython `3.12.13`, already available locally;
- `paddleocr==3.7.0` for the reviewed PP-OCRv6/PP-OCRv5 model families;
- `paddlepaddle==3.3.1` CPU runtime for Windows x86-64 and CPython 3.12;
- `Pillow==12.3.0` for deterministic generated plate rendering;
- `regex==2026.7.19` for UAX #29 extended grapheme clusters;
- keep Tesseract execution blocked until an exact Tesseract 5 engine build and
  native SBOM are selected and reviewed.

PaddleOCR 3.7.0 and PaddlePaddle 3.3.1 both publish CPython 3.12-compatible
metadata; the project currently defaults to Python 3.14.6, so P3.5 must not use
that default for Paddle runtime work. [PaddleOCR package](https://pypi.org/project/paddleocr/3.7.0/),
[PaddlePaddle package](https://pypi.org/project/paddlepaddle/3.3.1/),
[Pillow package](https://pypi.org/project/pillow/12.3.0/), and
[`regex` package](https://pypi.org/project/regex/2026.7.19/).

The grapheme contract remains bound to [Unicode UAX #29 revision 47](https://www.unicode.org/reports/tr29/).
Tesseract documentation confirms that current traineddata requires an engine
and that newer Windows installers are third-party, so H-CAM will not silently
adopt an unreviewed binary. [Tesseract installation documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html).

## Effect Of The Proposed Decision

If explicitly authorized, runtime research may resolve an isolated Python 3.12
dependency closure outside the worktree, acquire exact package artifacts into
quarantine, generate a package/native SBOM, run license and vulnerability
checks, and prove imports without loading model or font artifacts. It still
would not authorize application code, repository dependency changes, synthetic
generation, training, inference, cameras/media, real data, deployment, or
remote Git actions.

Canonical proposal:
[`p3-5-runtime-review-proposal.json`](../../contracts/phase-3/p3-5-runtime-review-proposal.json).
