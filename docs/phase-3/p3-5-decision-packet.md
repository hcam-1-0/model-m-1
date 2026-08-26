# P3.5 Owner Decision Packet

Status: planning complete under `D-P3.5-PLAN-AUTH`; no technical option is
owner approved. The exact `D-P3.5-START` statement was received early but is
non-effective until the technical choices and exact artifact review are complete.

Planning package: [P3.5 synthetic ANPR plan](p3-5-plan.md).

Machine-readable gates:
[`p3-5-entry-gates.json`](../../contracts/phase-3/p3-5-entry-gates.json).

## Decision Rules

- Each selection freezes a planning baseline; it does not download or approve
  an artifact and does not start implementation.
- Options that alter the accepted P3.0 zero-retention plate-text policy require
  an explicit policy-change decision before implementation.
- Exact model, font, dictionary, generator, and dependency artifacts need
  source, version, license, lineage, hash, model card, SBOM, vulnerability, and
  owner approval evidence.
- `D-P3.5-START` remains separate from `D-P3.5-001` through `D-P3.5-004`.

## D-P3.5-001: Synthetic Corpus And Token Policy

### A. Strict Procedural Non-Issuable Corpus (Recommended)

Use only H-CAM-generated programmatic shapes and backgrounds. Core OCR labels
use a visible `SYN` namespace and must fail any future production registration
grammar. Generated Devanagari and Gujarati strings are auxiliary script tests,
not registration marks. Every sample is reproducible from a seed and manifest.

No natural image, public dataset, scraped media, real registration mark,
Government record, owner record, or imported text is allowed. Exact font files
remain separately gated artifacts.

Benefits:

- strongest privacy and provenance boundary;
- deterministic masks, quadrilaterals, labels, and degradation parameters;
- no accidental real registration-mark or owner-data ingestion;
- generated fixtures can be reproduced without network access.

Costs:

- largest synthetic-to-real domain gap;
- no real-world accuracy or legal-format claim;
- detector and OCR performance may not transfer to CCTV conditions.

### B. Procedural Plus Reviewed Public Synthetic Sources

Add one or more public synthetic text/plate datasets after exact license,
source, content, geography, privacy, and security review.

Benefit: broader rendering diversity. Cost: source contamination, license,
hidden-real-data, and reproducibility risk. This option needs a separate dataset
approval and is not authorized by selecting it.

### C. Separately Authorized Real Or Government Plate Corpus

Plan for controlled real data supplied under an official purpose, access,
retention, security, and legal framework.

Benefit: relevant domain evidence. Cost: materially expands privacy, legal,
security, operational, and governance scope. This option is outside the current
synthetic P3.5 milestone and is not recommended here.

### D. OCR-Crop Fixtures Only

Generate rectified text crops but no full frame, compositor, or plate detector
training set.

Benefit: smallest implementation. Cost: does not validate plate localization or
end-to-end ANPR and leaves `PLATE-D0` blocked.

Recommended selection:

`strict_procedural_non_issuable_synthetic_corpus`.

## D-P3.5-002: Detector And OCR Portfolio

### A. Staged Hybrid Portfolio (Recommended)

Use distinct roles:

- `PLATE-D0`: one-class detector derived from an explicitly approved H-CAM
  detector architecture and trained only on approved generated data;
- `OCR-L0`: PP-OCRv6-small discovery baseline for uppercase Latin/digits;
- `OCR-L1`: PP-OCRv6-medium challenger;
- `OCR-D0`: Devanagari PP-OCRv5 mobile auxiliary lane;
- `OCR-G0`: Tesseract Gujarati `tessdata_fast` auxiliary baseline;
- `OCR-G1`: Tesseract Gujarati `tessdata_best` auxiliary challenger;
- no VLM, LLM, cloud OCR, or remote service in the reference path.

Every candidate remains blocked until its exact artifact passes review. A
published upstream metric is not a plate-domain promotion gate.

Benefits:

- best separation of detector, core Latin OCR, and local-script evidence;
- balanced and accuracy challengers remain independently measurable;
- Gujarati does not depend on unsupported assumptions about a Latin model;
- no general-purpose generative model can hallucinate a plausible mark.

Costs:

- multiple runtimes and dictionaries increase supply-chain and packaging work;
- confidence values cannot be compared until separately calibrated;
- generic OCR candidates may fail synthetic plate crops and be rejected.

### B. PaddleOCR-Only Portfolio

Use Paddle families for localization/recognition and drop Tesseract.

Benefit: fewer runtime families. Cost: current planning evidence does not
establish a dedicated Gujarati candidate or plate-domain suitability; script
coverage and artifact terms still need proof.

### C. Tesseract-Only OCR Portfolio

Use Tesseract language models for Latin, Devanagari, and Gujarati after exact
artifact review.

Benefit: one mature OCR runtime. Cost: weaker modern scene-text baseline,
limited rectification robustness, and no guarantee that generic language
traineddata handles plate crops.

### D. Fully Internal OCR Training

Train all OCR models from generated data and avoid pretrained weights.

Benefit: controlled training lineage. Cost: largest engineering and validation
burden, likely poor generalization, and still requires reviewed fonts,
dictionaries, training code, dependencies, and compute.

Recommended selection:

`staged_plate_detector_latin_primary_and_auxiliary_script_portfolio`.

## D-P3.5-003: Normalization, Abstention And Consensus

### A. Raw-Preserving NFC, Grapheme-Aware Abstaining Consensus (Recommended)

Preserve raw OCR exactly. Derive NFC, segment extended grapheme clusters,
apply only a closed versioned allowlist/format transform, retain confusables as
ranked alternatives, calibrate each model independently, and abstain on low
confidence or disagreement.

Optional consensus uses at most five observations or two seconds from one
accepted anonymous stream-local track and tracker epoch. It groups by track,
never by plate text, and stores no result.

Benefits:

- auditable distinction between recognition and normalization;
- correct metric treatment for Indic combining sequences;
- no silent correction into a plausible registration mark;
- bounded temporal stability without cross-camera identity.

Costs:

- higher abstention rate;
- requires calibration and explicit alternative semantics;
- some format-fixable outputs remain unresolved by design.

### B. Single-Frame Strict Recognition

Use raw plus NFC and abstention but no temporal consensus.

Benefit: simplest privacy and state boundary. Cost: loses a useful generated
test of repeated-observation stability and may abstain more often.

### C. Grammar-First Autocorrection

Automatically substitute confusable characters and choose the candidate that
best fits a registration grammar.

Benefit: higher apparent exact match. Cost: can invent plausible values and
hide model uncertainty. Not recommended for evidence or operational use.

### D. VLM/LLM Correction Or Translation

Send crop/output context to a general-purpose model for correction,
transliteration, or completion.

This is prohibited in P3.5 because it expands data handling, nondeterminism,
hallucination, network, model, and supply-chain risk and prevents exact replay.

Recommended selection:

`raw_preserving_nfc_grapheme_aware_abstaining_consensus`.

## D-P3.5-004: Privacy, Persistence, Resources And Evidence

### A. Ephemeral Text And Aggregate Evidence (Recommended)

Keep every raw/normalized OCR string and alternative in memory only. Persist no
plate-text table, event, outbox value, API result, log, trace, audit value,
metric label, cache, export, backup, or search index. Persist only
identifier-free aggregate metrics and artifact/configuration digests.

Preserve the accepted P3.0 policy of zero plate-text retention and no access
roles. Use the resource ceilings and generated-only exit evidence in the P3.5
plan. Final implementation acceptance remains exact-digest and independent.

Benefits:

- no plate database or search surface;
- no metadata-policy expansion;
- smallest misuse and breach impact;
- clear separation between reference correctness and operational capability.

Costs:

- no operator review workflow or per-sample retrospective debugging;
- debugging must use deterministic seeds and reproduce in memory;
- future operational use requires a new data-governance design.

### B. Restricted Synthetic Text For 24 Hours

Persist generated tokens and hypotheses for local debugging with
`platform.admin`, reason-required access, and automatic deletion.

Benefit: easier debugging. Cost: changes the accepted zero-retention policy and
creates storage, RBAC, deletion, backup, export, and audit obligations. It
requires an explicit metadata-policy amendment before implementation.

### C. Searchable Plate Observation Store

Persist normalized values, alternatives, track references, and search APIs.

Benefit: closer to an operational product. Cost: creates a high-risk
surveillance datastore and enables correlation. This is outside P3.5 and is not
recommended or authorized.

### D. Metrics-Free Contract Prototype

Build schemas and unit tests only, with no OCR execution or aggregate evidence.

Benefit: minimal risk. Cost: cannot evaluate candidate suitability, calibration,
abstention, or end-to-end behavior.

Recommended selection:

`ephemeral_plate_text_aggregate_evidence_and_zero_retention`.

## D-P3.5-START: Separate Implementation Gate

### A. Staged Generated-Only Start After Exact Artifact Review (Recommended)

After `D-P3.5-001` through `D-P3.5-004` are accepted, prepare and review exact
model, font, dictionary, generator, dependency, and runtime manifests. Only
then may `D-P3.5-START` authorize:

- contracts, guardrails, deterministic generator, adapters, normalization,
  generated consensus, and aggregate evaluation defined by the accepted plan;
- exact approved artifact acquisition into a constrained local quarantine;
- generated-only local training/evaluation explicitly listed in the start
  record;
- default-off, production-forbidden execution and local evidence commits.

The start record must list every allowed artifact and network action. Anything
not listed remains prohibited.

### B. Contracts And Generator Start Only

Authorize schemas, guardrails, and deterministic programmatic generator work,
but no model/font download, training, or inference.

Benefit: safest first implementation slice. Cost: P3.5 remains incomplete and
cannot evaluate OCR or localization.

### C. OCR-Crop Reference Start Only

Authorize generated crop fixtures and one exact OCR candidate, but no full-frame
plate detector or temporal consensus.

Benefit: smaller artifact surface. Cost: no end-to-end ANPR or localization
evidence.

### D. Defer P3.5 Implementation

Keep all P3.5 candidates blocked and move no implementation work forward.

Recommended start policy:

`authorize_only_after_decisions_001_through_004_and_exact_artifact_review`.

## Owner Decision Record

On 2026-08-26, `mayank-admin` selected the recommended baseline with:

> D-P3.5-001: A
>
> D-P3.5-002: A
>
> D-P3.5-003: A
>
> D-P3.5-004: A

This accepted the four technical planning choices only. The separate exact
`D-P3.5-ARTIFACT-RESEARCH` statement authorizes the seven proposal-bound
quarantine downloads, but no extraction, runtime loading, or implementation.

After exact artifact and source manifests are prepared and reviewed, the owner
must separately identify `D-P3.5-START`. A response such as `continue`, `start`,
or `accepted` without that decision ID is not implementation authorization.

`mayank-admin` supplied the exact start identifier on 2026-08-26 before the
required choices and manifests existed. It remains start intent only. A final
confirmation against the completed exact review packet digest is still
required.
