# P3.5 Generated-Only Start Authorization

Decision: `D-P3.5-START`

Owner: `mayank-admin`

Status: `owner_authorized_generated_only_staged`

Authorized at: `2026-08-26T16:18:08Z`

Evidence package digest:
`915F5E9246A7A656DF528DD54DA6018D7489C6875BF3A77D1A551BAD6EF9AF4D`

Evidence repository head: `1edfd0a13208d9b359cc5e563bbc406bba214e26`

The owner supplied the exact `D-P3.5-START` decision after the four technical
choices, exact artifact review, restricted runtime research, and clean-source
evidence were complete. This resolves the earlier non-effective start intent.

## Authorized Scope

Implementation is local, generated-only, default-off, production-forbidden,
zero-retention, and network-denied. The authorized work is:

- contracts, non-issuable token policy, and prohibited-input guardrails;
- deterministic programmatic generation and sealed split manifests;
- plate-localization contracts and generated ground-truth crop path only;
- Latin `OCR-L0/L1` Paddle adapters and generated evaluation;
- Devanagari `OCR-D0` Paddle lane and Gujarati font rendering only;
- normalization, confidence, abstention, and bounded temporal consensus;
- identifier-free aggregate evaluation, security evidence, and documentation.

No public API, camera path, upload, URL, arbitrary file input, background
worker, or persistent plate-text store is authorized.

## Loadable Artifacts

Only these five exact reviewed artifacts may be loaded:

| Candidate | Permitted use |
|---|---|
| `OCR-L0` | Safe local extraction and generated-only Paddle inference |
| `OCR-L1` | Safe local extraction and generated-only Paddle inference |
| `OCR-D0` | Safe local extraction and generated-only Paddle inference |
| `FONT-G0` | Deterministic generated Gujarati rendering |
| `FONT-D0` | Deterministic generated Devanagari rendering |

Every load requires the exact SHA-256 recorded in
`p3-5-start-authorization.json`. No artifact download is authorized.

## Runtime Boundary

The only runtime is the reviewed external CPython 3.12.13 closure under
`E:\h-cam-research-cache\phase-3\p3-5-runtime`, containing the exact
`paddleocr`, `paddlepaddle`, `Pillow`, and `regex` roots and the 319-component
runtime SBOM. It may be recreated only from the exact local wheelhouse.

Repository dependency/lockfile and container changes remain prohibited.
Runtime network access is denied. Auto-download behavior must fail closed.

## Reviewed But Blocked

`OCR-G0` and `OCR-G1` remain blocked because the exact Tesseract 5 engine and
native dependency SBOM are unresolved. Gujarati font rendering does not
authorize Gujarati OCR execution.

`PLATE-D0` training, fine-tuning, checkpoint creation, and model inference are
also blocked. The authorized localization slice is limited to contracts and
generated ground-truth crop behavior.

## Continuing Prohibitions

- all network actions;
- unlisted artifacts, dependencies, models, fonts, dictionaries, and data;
- training, fine-tuning, and derived checkpoint creation;
- real, public, private, scraped, Government, police, or registration data;
- physical cameras, Sentinel streams, ONVIF media, uploads, and recordings;
- owner/vehicle lookup, watchlists, identity, cross-camera linkage, alerts, or
  enforcement;
- raw or normalized plate text in databases, logs, metrics, traces, exports,
  backups, or evidence files;
- pilot, production, statewide deployment, or P3.6 work;
- remote Git push, pull request, or merge.

Anything not explicitly listed in the machine-readable start record remains
prohibited. Final P3.5 acceptance will require a new clean digest and explicit
owner review; this start decision is not acceptance.
