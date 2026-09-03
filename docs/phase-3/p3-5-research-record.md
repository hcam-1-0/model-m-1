# P3.5 Synthetic ANPR Research Record

Status: primary-source planning research complete; no artifact, model, font,
dataset, package, or media download was performed.

Machine-readable sources:
[`p3-5-research-sources.json`](../../contracts/phase-3/p3-5-research-sources.json).

## Research Questions

1. Which OCR families are credible candidates for Latin, Devanagari, and
   Gujarati generated text?
2. How should Unicode normalization and character metrics handle Indic scripts?
3. What registration-mark properties may inform synthetic rendering without
   creating a legal, owner-record, or real-data claim?
4. Which synthetic generation methods are useful, and which limitations must
   remain explicit?
5. What evidence is required before any exact model, font, or dataset can enter
   implementation?

## Findings

### OCR Portfolio

Current official PaddleOCR documentation lists PP-OCRv6 tiny, small, and medium
recognition tiers. The documentation also warns that PP-OCRv6 and earlier model
metrics may use different evaluation sets and are not directly comparable.
These figures are discovery evidence only; none measures Indian plate-domain
accuracy.

The official PaddleOCR catalog separately lists
`devanagari_PP-OCRv5_mobile_rec` with Devanagari-letter and number support. It
does not establish H-CAM plate performance, artifact eligibility, weight
licensing, or approved lineage.

Tesseract's official data documentation distinguishes integer
`tessdata_fast` from slower floating-point `tessdata_best` and lists Gujarati
traineddata. This supports a low-cost baseline/challenger comparison, not a
claim that generic Gujarati OCR is suitable for registration marks.

### Core Mark Versus Auxiliary Script

The official Central Motor Vehicles Rules describe registration-mark display,
security plates, and letter/numeral dimensions. P3.5 must not turn that source
into an unreviewed legal grammar. The core synthetic registration-mark lane is
therefore restricted to uppercase Latin letters and ASCII digits with explicit
non-issuable generated tokens.

Gujarati and Devanagari remain separately labeled auxiliary-text experiments.
They cannot overwrite, transliterate into, validate, or raise confidence for a
core registration-mark hypothesis. A future operational rule interpretation
requires a separately approved legal/transport-domain review.

### Unicode Semantics

Unicode Standard Annex #15 defines NFC as canonical decomposition followed by
canonical composition and cautions against blindly applying compatibility
normalization. P3.5 should preserve raw model output, derive an NFC form, and
never use NFKC as an invisible correction step.

Unicode Standard Annex #29 defines extended grapheme clusters. Gujarati and
Devanagari quality reports should compute edit operations over grapheme
clusters in addition to code points so combining sequences are not mislabeled
as multiple independent user-perceived characters.

### Synthetic Generation

The SynthText paper demonstrates geometry-aware rendering and compositing for
text localization. Later primary research also documents a substantial
synthetic-to-real domain gap. H-CAM may borrow planning ideas such as
perspective, blur, illumination, background, border, and occlusion variation,
but this authorization permits no SynthText data/code download and no natural
image backgrounds.

The recommended P3.5 generator uses programmatic backgrounds and shapes only.
It records every seed and parameter, emits exact masks/quadrilaterals, and uses
an explicit `SYN` token namespace that cannot be treated as a real registration
mark. Official Noto Gujarati and Devanagari repositories are candidate font
sources, but exact release, file, hash, OFL notice, embedding, and redistribution
review remain implementation-entry gates.

## Planning Conclusions

- Keep plate localization, OCR, normalization, and temporal consensus as
  independently versioned stages with separate metrics.
- Use PP-OCRv6 small/medium only as Latin discovery candidates; preserve the
  existing Devanagari PP-OCRv5 and Gujarati Tesseract candidate lanes.
- Preserve raw output and confidence; derive NFC and grapheme-aware alternatives
  without replacing the source hypothesis.
- Require explicit abstention for unsupported scripts, malformed output,
  low confidence, disagreement, and out-of-grammar results.
- Keep all plate text ephemeral under the existing zero-retention policy.
- Persist only aggregate, identifier-free evaluation evidence unless the owner
  separately changes the metadata policy.
- Treat synthetic-only results as correctness and engineering evidence, never
  as real-CCTV accuracy, legal conformance, operational readiness, or deployment
  evidence.

## Sources

- [PaddleOCR text recognition documentation](https://www.paddleocr.ai/main/en/version3.x/module_usage/text_recognition.html)
- [PaddleOCR multilingual pipeline catalog](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/pipeline_usage/OCR.en.md)
- [Tesseract data files](https://github.com/tesseract-ocr/tessdoc/blob/main/Data-Files.md)
- [Unicode normalization, UAX #15](https://www.unicode.org/reports/tr15/)
- [Unicode text segmentation, UAX #29](https://www.unicode.org/reports/tr29/)
- [Central Motor Vehicles Rules, India Code](https://upload.indiacode.nic.in/showfile?actid=AC_CG_61_1084_00001_00001_1554966634246&filename=the_central_motor_vehicles_rules%2C_1989.pdf&type=rule)
- [Synthetic Data for Text Localisation in Natural Images](https://openaccess.thecvf.com/content_cvpr_2016/html/Gupta_Synthetic_Data_for_CVPR_2016_paper.html)
- [Revisiting Scene Text Recognition: A Data Perspective](https://openaccess.thecvf.com/content/ICCV2023/papers/Jiang_Revisiting_Scene_Text_Recognition_A_Data_Perspective_ICCV_2023_paper.pdf)
- [Noto Gujarati](https://github.com/notofonts/gujarati)
- [Noto Devanagari](https://github.com/notofonts/devanagari)
