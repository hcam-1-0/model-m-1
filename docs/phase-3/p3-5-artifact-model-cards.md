# P3.5 Artifact Model Cards

Status: artifact identities reviewed; every runtime remains blocked.

## OCR-L0 And OCR-L1

`OCR-L0` is the PP-OCRv6 small generated-only Latin-primary baseline. `OCR-L1`
is the PP-OCRv6 medium generated-only quality comparison. They are general OCR
recognition models, not ANPR-specific models. H-CAM has not measured their
plate accuracy, character error rate, calibration, latency, or memory use.
Their archives do not include complete training-dataset manifests.

## OCR-D0

`OCR-D0` is the PP-OCRv5 Devanagari auxiliary lane. It may only produce a
separate abstaining auxiliary result and cannot override, rewrite, or increase
confidence in the Latin registration-mark lane. It has no H-CAM performance or
calibration evidence.

## OCR-G0 And OCR-G1

`OCR-G0` is the integerized Tesseract Gujarati fast data intended for a speed
baseline. `OCR-G1` is the Tesseract Gujarati best data intended for a quality
comparison. Both require a compatible Tesseract 4/5 LSTM engine; no exact local
engine is approved. The expected fast-versus-best tradeoff is not an H-CAM
benchmark result.

## Shared Prohibitions

These artifacts may not process real public, private, Government, police, or
scraped registration-mark media. They may not perform owner/vehicle lookup,
identity, cross-camera association, watchlist matching, alerting, enforcement,
pilot use, or deployment. No accuracy, legal, operational, or deployment claim
may be derived from metadata or future generated-only evidence.

The machine-readable cards and exact hashes are in
[`p3-5-artifact-model-cards.json`](../../contracts/phase-3/p3-5-artifact-model-cards.json).
