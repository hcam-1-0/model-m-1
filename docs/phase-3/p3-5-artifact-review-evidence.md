# P3.5 Exact Artifact Review Evidence

Status: `artifact_evidence_complete_runtime_research_pending`.

The seven artifacts authorized by `D-P3.5-ARTIFACT-RESEARCH` were acquired into
the external quarantine at `E:\h-cam-research-cache\phase-3\p3-5`. The original
proposal remains immutable at SHA-256
`8A027E0C8310C900C7DCA7BDFF0144B9E4E003BCAC1A31853C501226165EAD69`.
No file was extracted or loaded into an OCR, font-rendering, or model runtime.

| Candidate | Bytes | SHA-256 |
| --- | ---: | --- |
| `OCR-L0` | 21,442,560 | `DA460F968CE9F88325AC3A34FA302077D6E9B0DCEFB16BA3137CD7796F879D06` |
| `OCR-L1` | 76,851,200 | `4EECC1C6A4623765042E6FC15446DA0DA110B7D875B6B72B2D351D2B2DBD4DA6` |
| `OCR-D0` | 8,069,120 | `AC8279D27FC7E8CDA559364F9A3C506F43984CF6BA5E1B7A06450458BFE07DFB` |
| `OCR-G0` | 1,418,394 | `FA69658614B4946A9AFAE8853D67E0689838803DFA3D12C2E35EC53EE6F8DF34` |
| `OCR-G1` | 8,515,761 | `8CBB1D139B63434B9E1154A3B51930A74EC1C9A6251B95D86D74D7F1CD706ED6` |
| `FONT-G0` | 672,904 | `9901D8552F1DD5D2C50DBD4CAA6F6E174E74E8264F06594AB259AE6E7B1AC428` |
| `FONT-D0` | 647,144 | `9CE7B04F60E363D8870E5997744CF85CF69D38A4D7D129D364D92A3B14B461D7` |

The total is 117,617,083 bytes. The Tesseract and font files match their exact
Git blob identities. All Paddle responses matched the proposal ETag,
Last-Modified, content type, and byte count.

The initial `F:` attempt stopped for insufficient space after one complete
artifact and receipt; no partial file remained. That verified duplicate is not
part of the canonical `E:` evidence set and was retained because workspace
policy blocked recursive cleanup.

## Passive Inspection

The three Paddle tar archives contain only regular files and directories. They
contain bounded Paddle inference parameter/configuration files, have no links
or special entries, and were inventoried without extraction. The two fonts
have valid bounded SFNT directories with `cmap`, `head`, `name`, layout, and
variable-font tables. The two Tesseract data files passed size/header checks.

Microsoft Defender scanned the quarantine with signature `1.457.345.0`, exited
with code `0`, and reported no threats. This is local scan evidence, not a
guarantee that an artifact is vulnerability-free or fit for deployment.

## License And Lineage

- PaddleOCR project and package sources identify Apache-2.0, but the three
  downloaded archives do not embed a license or complete training-dataset
  manifest. This remains a lineage limitation rather than a silent claim.
- The exact `tessdata_fast` and `tessdata_best` source revisions license their
  data under Apache-2.0.
- Both exact Google Fonts directories include OFL-1.1 license evidence.

Primary references: [PaddleOCR pinned license](https://github.com/PaddlePaddle/PaddleOCR/blob/2661c7c0ef5c613e8f93c6e93b2e052399f0f854/LICENSE),
[Tesseract fast pinned license](https://github.com/tesseract-ocr/tessdata_fast/blob/87416418657359cb625c412a48b6e1d6d41c29bd/LICENSE),
[Tesseract best pinned license](https://github.com/tesseract-ocr/tessdata_best/blob/e12c65a915945e4c28e237a9b52bc4a8f39a0cec/LICENSE),
[Gujarati OFL](https://github.com/google/fonts/blob/6a003b5eb672dc8bf5bff5937cf5863f8b175445/ofl/notosansgujarati/OFL.txt),
and [Devanagari OFL](https://github.com/google/fonts/blob/6a003b5eb672dc8bf5bff5937cf5863f8b175445/ofl/notosansdevanagari/OFL.txt).

## Remaining Gate

Artifact identity research is complete, but runtime research is not. Exact
Python wheels, transitive dependencies, native libraries, Tesseract engine,
runtime SBOM, and vulnerability review remain unresolved. `PLATE-D0` also
remains an unbuilt internal future artifact. At this artifact-review checkpoint,
no candidate was approved for execution and the early `D-P3.5-START` remained
non-effective. Later restricted authority is recorded separately in
[P3.5 generated-only start authorization](p3-5-start-authorization.md).

Canonical evidence is in
[`p3-5-artifact-review-evidence.json`](../../contracts/phase-3/p3-5-artifact-review-evidence.json)
and [`p3-5-artifact-sbom.cdx.json`](../../contracts/phase-3/p3-5-artifact-sbom.cdx.json).
