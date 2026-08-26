# P3.5 Synthetic ANPR Plan

Status: planning complete under `D-P3.5-PLAN-AUTH`; technical decisions
`D-P3.5-001` through `D-P3.5-004` approve the recommended `A/A/A/A` baseline.
Exact seven-artifact quarantine research is authorized under
`D-P3.5-ARTIFACT-RESEARCH` and its exact evidence is complete.
`D-P3.5-RUNTIME-RESEARCH` and the early `D-P3.5-START` remain non-effective
until exact runtime review is complete and accepted.

Planning authority: `D-P3.5-PLAN-AUTH`.

Accepted dependency: P3.4 under `D-P3.4-ACCEPTANCE` for package digest
`11CCD757E2308F56EE5912B70861B8A977DBD8B7CEE8DBD434265A28988EF8AF`.

## Objective

Design a generated-only, multilingual-aware ANPR reference that proves the
software contracts for plate-region localization, OCR, normalization,
confidence, abstention, and bounded temporal consensus without processing a
real registration mark or creating a searchable plate database.

P3.5 is an engineering and correctness milestone. It cannot establish
real-CCTV accuracy, legal conformance, owner identity, watchlist matching,
operational alerting, enforcement suitability, or deployment readiness.

## Planning Boundary

P3.5 planning defines:

- deterministic programmatic generation of non-issuable synthetic plate tokens;
- independently versioned localization, OCR, normalization, and consensus stages;
- a Latin registration-mark lane and isolated Devanagari/Gujarati auxiliary
  script lanes;
- raw-output preservation, NFC normalization, grapheme-aware metrics, ranked
  alternatives, confidence calibration, and abstention;
- ephemeral processing under the existing zero-retention plate-text policy;
- generated-only evaluation, resource limits, provenance, supply-chain review,
  security controls, rollback, and acceptance evidence;
- four owner technical decisions and one separate implementation-start gate.

Planning plus the separate research decision authorizes only the seven exact
quarantine downloads. It does not authorize dependencies, extraction, runtime
loading, generation, training, fine-tuning, export, inference, application code, migrations, APIs, workers,
storage, cameras, media, real registration marks, owner or vehicle records,
Government databases, watchlists, alerts, deployment, P3.6, or remote Git
actions.

## Existing Foundation

P3.5 reuses rather than replaces:

- accepted P3.2 generated-only `DET-R0` execution and model-artifact controls;
- accepted P3.3 anonymous stream-local tracks and tracker epochs;
- accepted P3.4 deterministic event lineage and production-forbidden controls;
- P3.1 candidate manifests for `PLATE-D0`, `OCR-L0`, `OCR-L1`, `OCR-D0`,
  `OCR-G0`, and `OCR-G1`, all of which remain blocked and unapproved;
- synthetic ANPR metric contracts for plate overlap, exact match, and character
  error;
- department scope, RBAC, audit, ETags, model lineage, transactional outbox,
  aggregate metrics, and fail-closed activation patterns;
- P3.0 metadata policy class `derived.analytics.plate_text`, which has no
  access roles and a maximum retention of zero hours.

P3.5 cannot weaken those controls. In particular, a plate observation cannot
become a tracker key, entity identity, cross-camera join key, owner lookup key,
or alert by implication.

## Architecture

```text
Deterministic seed + approved generator manifest
        |
        v
Non-issuable token generator -----> script/layout/parameter ground truth
        |
        v
Programmatic plate renderer ------> masks + quadrilateral + crop truth
        |
        v
Programmatic scene compositor ----> generated frame reference (never stored)
        |
        v
PLATE-D0 localization adapter ----> bounded plate-region hypotheses
        |
        v
Rectification + quality gate -----> reject/abstain reason
        |
        v
Closed script router
   |          |             |
   v          v             v
Latin OCR   Devanagari    Gujarati
L0/L1      D0 auxiliary  G0/G1 auxiliary
   |          |             |
   +----------+-------------+
              |
              v
Raw ranked hypotheses + exact model confidence
              |
              v
NFC + grapheme segmentation + closed normalization rules
              |
              v
Format hypothesis + calibration + explicit abstention
              |
              v
Optional synthetic stream-local temporal consensus
              |
              +----> ephemeral result returned to test harness
              +----> identifier-free aggregate evaluation only
```

Every stage has an immutable version, canonical configuration digest, bounded
input/output schema, timeout, maximum alternatives, and lineage. A downstream
stage cannot rewrite upstream evidence.

## Data Source And Generator

### Source Classes

P3.5 defines only one directly recommended source:

`DATA-PLATE-GEN-R0`: deterministic programmatic assets with no natural-image,
camera, public-dataset, scraped, private, Government, owner, or real
registration source.

Any external synthetic dataset, real plate corpus, stock background, font,
texture, or source archive is a separate artifact with its own license,
provenance, security, purpose, and owner gate. Calling a dataset synthetic does
not make it automatically eligible.

### Non-Issuable Token Policy

Generated core tokens use a visible `SYN` namespace and are classified as
`synthetic_non_issuable`. They exercise uppercase Latin letters, ASCII digits,
spacing, one-line/two-line layout, and OCR confusables without claiming to be a
valid registration mark.

The generator must reject:

- a token that passes an approved production registration grammar;
- a token imported from user, file, URL, environment, database, or network;
- a real state/district/series allowlist unless separately approved;
- any owner, vehicle, location, watchlist, or case identifier;
- uncontrolled free text or a token longer than the bounded schema;
- an unassigned Unicode code point or disallowed script mixture.

The corpus manifest records generator version, seed hierarchy, token class,
script, layout, font artifact digest, rendering parameters, split assignment,
and canonical sample digest. No generated sample moves between train,
validation, and final test splits after freeze.

### Rendering Factors

The proposed generator varies only explicit, bounded factors:

- plate aspect ratio, single/two-line layout, border, safe synthetic colors,
  glyph size, spacing, and alignment;
- font family and weight from an exact reviewed artifact set;
- projective transform, rotation, scale, blur, noise, compression,
  illumination, glare approximation, shadow, partial occlusion, truncation,
  and low-resolution rendering;
- programmatic backgrounds, vehicle-like geometric surfaces, and clutter;
- front/rear style category as a synthetic rendering label only.

Every factor is present in the sample manifest. Hidden random augmentation is
prohibited. The generator emits exact plate mask, quadrilateral, bounding box,
token, script, and grapheme ground truth before the in-memory image is deleted.

## Plate Localization

`PLATE-D0` is a dedicated one-class `vehicle.registration_plate_region`
candidate derived only after an H-CAM detector family is explicitly approved
for synthetic training. P3.2 acceptance of the `DET-R0` artifact does not
automatically approve derivative training or a plate checkpoint.

The localization contract accepts only an in-memory generated frame carrying
the `DATA-PLATE-GEN-R0` provenance marker. It returns at most eight hypotheses:

- normalized axis-aligned box and optional four-point quadrilateral;
- confidence before policy filtering;
- model, weights, preprocessing, postprocessing, taxonomy, and runtime versions;
- source sample ID and generator version;
- bounded quality fields and safe reason code.

It returns no crop bytes, image path, media URL, owner field, plate text, or
track identity. Rectification is a separate deterministic transform whose
matrix and digest are recorded for evaluation but whose pixels remain
ephemeral.

## OCR Portfolio

### Core Latin Lane

The recommended discovery portfolio is:

- `OCR-L0`: PP-OCRv6-small as the balanced baseline candidate;
- `OCR-L1`: PP-OCRv6-medium as the accuracy challenger;
- deterministic Tesseract `eng` or a generated-only trivial recognizer may be
  retained as an independent diagnostic baseline if exact artifacts pass review.

Neither PP-OCRv6 model is approved by planning. Exact weights, source revision,
model format, dictionary, preprocessing, runtime, license, lineage, hash,
model card, SBOM, and plate-domain evidence remain unresolved.

### Auxiliary Script Lanes

- `OCR-D0`: `devanagari_PP-OCRv5_mobile_rec` planning candidate;
- `OCR-G0`: Tesseract Gujarati `tessdata_fast` baseline candidate;
- `OCR-G1`: Tesseract Gujarati `tessdata_best` accuracy challenger.

These lanes process only explicitly generated auxiliary text. They cannot
produce or modify the core registration-mark value, transliterate into Latin,
validate an owner/vehicle record, or raise the core confidence. Results are
reported independently by script, font, grapheme, and degradation slice.

### Script Router

The router uses a closed requested script from trusted generator metadata in
P3.5. It does not infer language, ethnicity, nationality, or identity from a
real image. A mismatch between requested script and OCR output causes
abstention. Mixed-script output is rejected unless the exact generated fixture
declares a bounded permitted mixture.

## OCR Result Contract

`OcrHypothesisV1` contains:

- opaque result and region IDs;
- stage, engine, artifact, dictionary, preprocessing, and runtime versions;
- declared script lane;
- raw UTF-8 output exactly as emitted by the engine;
- raw engine confidence and token/grapheme alternatives when available;
- deterministic latency and safe failure metadata for generated evaluation;
- source generator/sample and rectification lineage;
- `synthetic_only: true` and `review_state: unreviewed`.

Maximum output is 32 Unicode scalar values, 16 grapheme clusters, and five
ranked alternatives. Invalid UTF-8, unassigned code points, control characters,
bidirectional overrides, unexpected whitespace, output over limits, NaN/inf
confidence, unsupported script, or malformed alternatives fail closed.

## Normalization And Format Semantics

Normalization is a derived hypothesis, never an edit to raw OCR.

The pipeline applies in order:

1. UTF-8 and Unicode scalar validation;
2. NFC canonical normalization;
3. extended grapheme clusters segmented using a pinned Unicode data version;
4. outer whitespace trim and explicitly versioned separator handling;
5. lane-specific case mapping for Latin only;
6. closed character allowlist;
7. non-issuable synthetic grammar classification;
8. confidence calibration and abstention policy.

NFKC/NFKD, transliteration, dictionary completion, edit-distance autocorrection,
Government-record lookup, owner lookup, language-model completion, and silent
confusable substitution are prohibited. Optional confusable alternatives such
as `O/0`, `I/1`, or `B/8` remain ranked alternatives with their own confidence;
the system does not choose one merely because it fits a format.

`PlateNormalizationV1` stores in memory:

- raw-hypothesis digest;
- NFC value and grapheme list;
- normalized display candidate;
- normalization and Unicode versions;
- format family `synthetic_non_issuable` or `unrecognized`;
- validation outcomes and safe reason codes;
- whether any separator/case transform occurred;
- calibrated confidence and abstention state.

## Confidence And Abstention

The result abstains when any hard gate fails, including:

- no plate region or multiple unresolved overlapping regions;
- region below size/quality thresholds;
- unsupported or mismatched script;
- malformed output or prohibited character;
- model confidence below its frozen slice gate;
- normalization or grammar rejection;
- L0/L1 disagreement beyond the approved threshold;
- calibration error outside the approved bound;
- temporal instability, duplicate conflict, timeout, overload, or resource cap;
- missing artifact, source, generator, or configuration lineage.

Abstention is a valid result and is measured. No fallback may silently switch
models, scripts, runtime providers, or normalization policies.

## Stream-Local Temporal Consensus

Temporal consensus is optional and generated-only. It groups OCR observations
only by accepted P3.3 stream-local track ID and tracker epoch for a maximum of
five observations or two seconds of event time, whichever closes first.

The consensus contract:

- never uses plate text as a grouping key;
- never joins streams, cameras, tracker epochs, assignments, or departments;
- retains ranked hypotheses in memory only;
- uses deterministic confidence-weighted voting over exact normalized strings;
- requires an approved minimum support and margin;
- abstains on unresolved disagreement;
- closes on track end, epoch reset, timeout, count limit, or overload;
- emits no persistent plate text, watchlist request, alert, or identity.

The aggregate evaluation may record consensus success/failure counts by
generator slice but no token, region, track, camera, or sample identifier.

## Storage, API, And Retention

The recommended P3.5 reference has no plate-text database table, search index,
cache, outbox payload, audit value, log value, metric label, export, backup,
snapshot, or API response outside the local generated test harness.

This preserves the accepted P3.0 policy:

- classification: `derived.analytics.plate_text`;
- access roles: none;
- maximum retention: zero hours;
- export: denied;
- legal hold: unavailable without separate approval;
- training reuse: denied without new purpose approval.

Persisted evidence is limited to identifier-free aggregates, exact artifact and
configuration digests, counts, latency distributions, metric values, slice
names from a closed low-cardinality catalog, failure reason counts, and the
test harness version. Audit records may state that a generated run occurred but
contain no OCR text or alternative.

Any future operator review, plate search, case attachment, evidence retention,
watchlist, owner lookup, or Government database integration requires a new data
classification, purpose, RBAC, reason, retention, deletion, audit, legal-hold,
export, and owner authorization package. P3.5 cannot pre-authorize it.

## Security And Misuse Controls

- runtime default-off and forbidden in production;
- generated provenance checked at every stage, not only at entry;
- no file path, URL, upload, camera, stream, or arbitrary byte API;
- exact local artifact roots with traversal/symlink/size/hash validation;
- no environment proxy or network access during execution;
- parser and output limits before allocation or normalization;
- model and font archives scanned before extraction in a future authorized
  quarantine workflow;
- no pickle, arbitrary code model format, remote custom op, or auto-download;
- logs, traces, metrics, exceptions, database rows, and audits redacted by
  construction;
- fail-closed startup on missing approval, artifact, Unicode data, dictionary,
  generator, or policy version;
- one kill switch disables all P3.5 execution without changing P3.2-P3.4.

## Resource Bounds

Initial planning ceilings:

| Resource | Proposed ceiling |
| --- | --- |
| Generated source frame | 1280 x 720, in memory only |
| Plate regions per frame | 8 |
| Rectified crop | 512 x 128, in memory only |
| OCR alternatives per region | 5 |
| Unicode scalars per alternative | 32 |
| Grapheme clusters per alternative | 16 |
| OCR engines attempted per lane | 2 |
| Consensus observations | 5 |
| Consensus event-time window | 2 seconds |
| Active consensus states per stream | 256 |
| Generated samples per local evidence run | 10,000 maximum |
| Per-stage timeout | Frozen only after a generated baseline |
| Plate-text retention | 0 hours |

Numeric latency gates remain proposals until measured on the documented
`LAB-LAPTOP-01` profile. No statewide capacity or real-time deployment claim is
permitted.

## Evaluation Plan

### Dataset Splits

The generator uses independent seed namespaces for contract fixtures,
development, validation, and final test. Fonts, token seeds, layouts, and
degradation combinations are split by manifest, not by file name. The final
test manifest is sealed before tuning and access is audited.

At least one holdout generator configuration and one holdout font family are
reserved to expose renderer overfitting. Synthetic evidence always reports the
generator family and cannot be mixed with future real/authorized evidence.

### Stage Metrics

Plate localization:

- precision, recall, average precision, IoU distribution, and miss/duplicate
  rate by size, perspective, blur, occlusion, illumination, layout, and clutter.

OCR:

- exact raw match, NFC exact match, grapheme-cluster error rate, code-point error
  rate, top-k coverage, confidence calibration, and abstention coverage;
- separate Latin, Devanagari, and Gujarati reports;
- separate crop-ground-truth OCR and detector-produced-crop OCR.

Normalization:

- exact transform agreement, invalid acceptance rate, valid rejection rate,
  confusable alternative coverage, and proof that raw output is unchanged.

End to end:

- exact synthetic token match, localization-to-OCR attribution, consensus gain,
  consensus error, duplicate result rate, deterministic replay, timeout,
  overload, restart, and kill-switch behavior.

### Proposed Exit Gates

Numeric quality thresholds remain owner decisions after a generated baseline.
Hard non-numeric gates are:

- zero real, public, private, Government, police, scraped, or camera media;
- zero real registration marks, owner records, watchlist records, or Government
  database records;
- exact deterministic generator and pipeline replay across 20 runs;
- zero persisted OCR strings or alternatives;
- zero cross-stream/camera/epoch consensus;
- zero raw-output mutation;
- 100% rejection of prohibited input paths and malformed output fixtures;
- exact artifact, font, dictionary, source, license, hash, model card, SBOM,
  vulnerability, and approval evidence for every future runtime component;
- full test, migration-no-change, packaging, archive, log/redaction, and
  production-forbidden evidence;
- explicit owner acceptance of the final clean-source digest.

## Work Packages

The plan proposes the following sequence after a separate `D-P3.5-START`:

1. `P35-W1` contracts, generated token policy, and prohibited-input guardrails;
2. `P35-W2` exact source/artifact/font review and quarantine manifests;
3. `P35-W3` deterministic generator and sealed split manifests;
4. `P35-W4` plate localization adapter and generated crop evidence;
5. `P35-W5` Latin OCR adapter and baseline/challenger evaluation;
6. `P35-W6` isolated Devanagari and Gujarati auxiliary adapters;
7. `P35-W7` normalization, grapheme metrics, calibration, and abstention;
8. `P35-W8` bounded synthetic track-local consensus;
9. `P35-W9` aggregate evidence, security, resource, packaging, and rollback;
10. `P35-W10` clean-source validation and independent final owner acceptance.

No work package may start merely because the plan exists. Exact authorized
work and artifact permissions must be stated in `D-P3.5-START`.

## Risks And Controls

| Risk | Control |
| --- | --- |
| Synthetic token collides with a real mark | `SYN` namespace, explicit non-issuable grammar, no imported text |
| Synthetic evidence is overstated | Separate evidence class and explicit no-real-world-performance claim |
| OCR output becomes an identity | Observation-only contract, zero persistence, no text grouping key |
| Indic combining characters distort metrics | NFC plus UAX #29 grapheme-cluster reporting |
| Normalizer invents a plausible mark | Raw preservation, no autocorrection/transliteration/lookup, abstention |
| Auxiliary script changes core mark | Isolated lanes with no confidence or value feedback into core result |
| Model or font license is assumed | Exact artifact-level review before acquisition or execution |
| Auto-download escapes review | Offline artifact root, network disabled, no runtime download |
| Plate text leaks through telemetry | Identifier-free aggregates and negative redaction tests |
| Temporal consensus creates tracking identity | Existing anonymous stream/epoch key only, two-second/five-sample bound |
| Synthetic-to-real domain gap is hidden | No real-CCTV accuracy or deployment claim; separate future evidence gate |

## Owner Entry Gates

The owner must decide:

1. `D-P3.5-001`: synthetic corpus, token grammar, and source policy;
2. `D-P3.5-002`: plate detector and OCR portfolio;
3. `D-P3.5-003`: normalization, confidence, abstention, and consensus semantics;
4. `D-P3.5-004`: zero-retention privacy, resources, evaluation, and acceptance;
5. `D-P3.5-START`: exact implementation and artifact authorization.

The first four technical decisions do not start implementation. `continue`,
planning approval, or acceptance of another phase cannot substitute for the
explicit `D-P3.5-START` decision.

The owner supplied `D-P3.5-START` before the four technical decisions and exact
artifact review. That statement is preserved as intent, not implementation
authority, because it cannot bind artifacts and network actions that have not
yet been disclosed. See [P3.5 start intent](p3-5-start-intent.md).

Metadata-only proposal R0 now identifies eight recommended artifact slots and
current runtime gaps. It performs no acquisition and does not resolve SHA-256,
license, lineage, model-card, SBOM, or compatibility evidence. See
[P3.5 artifact review proposal](p3-5-artifact-review-proposal.md).

Machine-readable gate status:
[`p3-5-entry-gates.json`](../../contracts/phase-3/p3-5-entry-gates.json).
