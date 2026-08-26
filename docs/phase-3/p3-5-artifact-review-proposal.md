# P3.5 Artifact Review Proposal R0

Status: `proposal_prepared_blocked`.

This is a metadata-only proposal for the recommended `A/A/A/A` P3.5
baseline. It is not an approval record, download manifest, runtime manifest, or
implementation authorization.

Machine-readable proposal:
[`p3-5-artifact-review-proposal.json`](../../contracts/phase-3/p3-5-artifact-review-proposal.json).

## Proposed Artifact Surface

| Role | Proposed artifact | Pre-acquisition identity | Blocking evidence |
| --- | --- | --- | --- |
| `OCR-L0` | PP-OCRv6 small inference archive | Exact official URL, 21,442,560 bytes, content type, ETag | SHA-256, weight terms, lineage, model card, SBOM, runtime |
| `OCR-L1` | PP-OCRv6 medium inference archive | Exact official URL, 76,851,200 bytes, content type, ETag | SHA-256, weight terms, lineage, model card, SBOM, runtime |
| `OCR-D0` | Devanagari PP-OCRv5 mobile inference archive | Exact official URL, 8,069,120 bytes, content type, ETag | SHA-256, weight terms, lineage, model card, SBOM, runtime |
| `OCR-G0` | Tesseract fast `guj.traineddata` | Immutable commit, Git blob SHA-1, 1,418,394 bytes | SHA-256, runtime, model card, SBOM |
| `OCR-G1` | Tesseract best `guj.traineddata` | Immutable commit, Git blob SHA-1, 8,515,761 bytes | SHA-256, runtime, model card, SBOM |
| `FONT-G0` | Noto Sans Gujarati variable TTF | Immutable Google Fonts commit, Git blob SHA-1, 672,904 bytes | SHA-256, exact OFL binding, font validation, SBOM |
| `FONT-D0` | Noto Sans Devanagari variable TTF | Immutable Google Fonts commit, Git blob SHA-1, 647,144 bytes | SHA-256, exact OFL binding, font validation, SBOM |
| `PLATE-D0` | Generated-only H-CAM derivative of `DET-R0` | No upstream download; future internal build | Corpus choice, derivative-training authority, build lineage, hash, model card, SBOM |

The Paddle documentation identifies the proposed recognition families, but
published documentation metrics are not H-CAM plate-domain measurements. HTTP
`HEAD` was used only to record size, content type, ETag, and modification
metadata. No model body was fetched.

The Tesseract and font proposals use immutable repository commits and Git blob
identities. Those identities are useful before acquisition but do not replace
the SHA-256 that H-CAM will calculate after a separately authorized quarantine
download.

## Environment Findings

- Python 3.12.13 is already available locally, but the current project command
  resolves Python 3.14.6. Paddle package compatibility has not been established.
- Docker Desktop is available and its server reports version 29.7.2. No P3.5
  image or container action is authorized.
- A Tesseract executable is not installed. The Gujarati candidates therefore
  cannot execute even if their traineddata files were present.

These facts prohibit choosing a runtime by assumption. Exact Paddle,
PaddleOCR, Tesseract, Unicode/grapheme, image, and packaging dependencies still
need compatibility, license, vulnerability, SBOM, and reproducibility review.

## Required Quarantine Gate

Some upstreams do not publish SHA-256 values for the exact proposed files. H-CAM
therefore needs a narrow research gate before final `D-P3.5-START`:

`D-P3.5-ARTIFACT-RESEARCH`

If later authorized, it permits only:

1. HTTPS `GET` for the exact URLs in the machine-readable proposal;
2. no redirects or environment proxies;
3. download into a non-runtime local quarantine capped at 256 MiB total;
4. size, content-type, immutable-source/ETag, archive, malware, and parser checks;
5. SHA-256 calculation, license/lineage review, model cards, and SBOM generation;
6. no extraction before archive safety checks;
7. no model loading, generation, training, inference, application changes, or
   runtime use.

Any redirect, changed size/ETag, unexpected content type, archive violation,
malware finding, license ambiguity, or dependency incompatibility fails closed.

## Remaining Owner Sequence

1. Select `D-P3.5-001` through `D-P3.5-004`.
2. Review and authorize `D-P3.5-ARTIFACT-RESEARCH` for the exact proposal.
3. Produce the hash, scan, license, lineage, model-card, SBOM, and runtime packet.
4. Confirm `D-P3.5-START` against that immutable packet digest.

Until all four steps complete, implementation and every artifact/network action
remain prohibited.
