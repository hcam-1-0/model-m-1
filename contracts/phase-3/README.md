# Phase 3 Analytics Contracts

This directory contains reviewed, deterministic snapshots for the additive
Phase 0-3 API/database surface and the model-independent P3.0 analytics boundary:

- `analytics-contracts.json`: JSON schemas for assignment, versioned metadata
  events including stream-local lifecycle v2, draft taxonomy, normalized
  geometry/schedules, and the runtime adapter boundary;
- `fixtures/`: generated-only golden documents used for producer/consumer
  compatibility and deterministic serialization tests, including an explicitly
  unconfigured runtime result.
- `openapi.json`: the current FastAPI contract, including the activation-blocked
  analytics-assignment API;
- `database.json`: the current Alembic `0011_geometry_events` schema, including
  assignments, generated runs, anonymous stream-local tracking, normalized
  geometry/rules/events, and database guard constraints.
- `p3-0-owner-decisions.json`: the machine-readable owner approval record for
  P3-G1 through P3-G3, including the exact Tier A scope, synthetic-lab metadata
  policy, accountable owner, optional reviewer, and non-authorization boundary.
  P3-G4 records the accountable-owner self-review exception and effective P3.0
  acceptance; the same owner-review mode now applies to later model promotion,
  operational geometry, datasets, and deployment.
- `p3-1-authorization.json`: the exact `D-P3.1-001` planning authorization,
  generated-only source policy, nine work packages and exit gates, developer
  hardware profile, accountable-owner review mode, and explicit exclusions.
  It authorizes bounded P3.1 implementation but does not claim implementation
  completion or authorize external downloads, inference, cameras/media, P3.2,
  pilots, or deployment.
- `p3-1/`: the generated-only P3.1 implementation package. It contains the six
  versioned evaluation contract schemas, seven generated fixture/QA/split
  suites, 11 metadata-only blocked candidate manifests, source dossier, metric
  golden report, baseline run, and evidence index. All artifacts are JSON,
  bounded to one MiB, canonical, hashed, media-free, and reproducible offline.
- `p3-1-acceptance.json`: the exact `D-P3.1-ACCEPTANCE` owner decision bound to
  the unchanged 28-artifact package digest, clean baseline commit, reviewed
  repository head, accepted limitations, and explicit non-authorization.
- `p3-2-acceptance.json`: the exact accepted generated-input CPU detection
  package and continuing non-authorization boundary.
- `p3-3-*-source.json`, policy/runtime/generated-suite manifests, and
  `p3-3/evaluation-report.json`: exact tracker/evaluator provenance and
  generated-only parity evidence.
- `p3-3-sbom.cdx.json`: deterministic CycloneDX runtime inventory generated
  from the audited lock.
- `p3-3-validation-evidence.json`: bounded local test, PostgreSQL, coverage,
  package, audit, and prohibited-input results.
- `p3-3-acceptance.json`: exact-digest owner acceptance of the immutable
  generated-only P3.3 package and its continuing non-authorization boundary.
- `p3-4-planning-authorization.json`: exact planning-only authorization,
  accepted P3.3 baseline, deliverables, and prohibited actions.
- `p3-4-entry-gates.json`: accepted geometry-engine, rule-semantics,
  event-time, and persistence/evidence decisions plus the pending separate
  implementation-start gate.
- `p3-4-owner-decisions.json`: exact owner-selected hybrid geometry,
  visual/CEL rules, deterministic time, and bounded persistence baseline with
  continuing non-authorization.
- `p3-4-start-authorization.json`: exact baseline-bound generated-only local
  implementation authorization, authorized work, and continuing exclusions.
- `p3-4-c10-evidence.json`: five sealed generated geometry/event scenarios,
  expected outputs, state traces, and deterministic replay hashes.
- `p3-4-dependencies.json`, `p3-4-sbom.cdx.json`, and
  `p3-4-container-vulnerability-review.json`: exact Python/native provenance,
  SBOM, and the unresolved PostGIS image deployment block.
- `p3-4-validation-evidence.json`: test, coverage, migration, packaging,
  dependency-audit, Docker, and prohibited-input evidence.
- `p3-4-acceptance.json`: exact-digest owner acceptance of the immutable
  generated-only P3.4 package and its continuing non-authorization boundary.
- `p3-5-planning-authorization.json`: exact planning-only authorization based
  on accepted P3.4, with all implementation and artifact actions prohibited.
- `p3-5-research-sources.json`: primary-source, no-download research evidence
  for OCR, Unicode, registration-mark constraints, fonts, and synthetic data.
- `p3-5-artifact-review-proposal.json`: metadata-only recommended `A/A/A/A`
  acquisition proposal with eight blocked artifact slots, exact source
  identities where available, empty network authority, and unresolved hashes.
- `p3-5-owner-decisions.json`: exact owner approval of the recommended
  `A/A/A/A` technical baseline without implementation authority.
- `p3-5-artifact-research-authorization.json`: proposal-digest-bound authority
  for exactly seven HTTPS quarantine downloads with no redirects, proxies,
  extraction, runtime loading, or implementation.
- `p3-5-artifact-review-evidence.json`: exact SHA-256 values, passive archive,
  traineddata/font inspection, Defender evidence, and remaining runtime blocks.
- `p3-5-artifact-review-acceptance.json`: exact package-digest and evidence-hash
  owner acceptance with all runtime and implementation boundaries preserved.
- `p3-5-artifact-sbom.cdx.json`: CycloneDX 1.6 inventory for all seven exact
  artifacts, source identities, licenses, and blocked runtime state.
- `p3-5-artifact-model-cards.json`: five OCR roles, intended generated-only use,
  limitations, and continuing execution blocks.
- `p3-5-runtime-review-proposal.json`: Python 3.12 package/runtime proposal with
  no package download, dependency change, or implementation authority.
- `p3-5-runtime-research-authorization.json`: digest-bound authority for an
  external binary-wheel dependency closure, SBOM, scans, audit, and import-only
  proof with no repository dependency or model-runtime authority.
- `p3-5-runtime-research-evidence.json`: exact CPython and binary-wheel closure,
  scan and audit results, guarded import behavior, external evidence hashes,
  and continuing implementation blocks.
- `p3-5-runtime-sbom.cdx.json`: CycloneDX 1.6 inventory of all 67 packages, 67
  wheels, and 185 native files, with every component runtime unauthorized.
- `p3-5-runtime-license-review.json`: normalized metadata for all 67 package
  licenses and review flags; it grants no legal or redistribution approval.
- `p3-5-entry-gates.json`: four approved technical choices, accepted artifact
  and runtime evidence, and the completed final `D-P3.5-START` gate.
- `p3-5-start-authorization.json`: the effective digest-bound generated-only
  start, five exact loadable artifacts, two reviewed-but-blocked Tesseract
  artifacts, an empty network allowlist, and continuing prohibitions.
- `p3-5-anpr-contracts.json`: reviewed W1 schemas and policy constants for the
  seed-only generated request, visible non-issuable `SYN` token, default-off
  execution, prohibited inputs, resource ceilings, and zero retention.
- `fixtures/p3-5-generated-request-v1.json`: canonical seed-only generated
  request with no plate text, file, URL, bytes, camera, or identity field.
- `fixtures/p3-5-sealed-splits-v1.json`: digest-bound 20-entry W3 split
  manifest with independent seed namespaces, final-test-only logical holdouts,
  and no token text or token-derived commitment.
- `fixtures/p3-5-ground-truth-crop-v1.json`: canonical W4 model-free
  localization result and ephemeral-crop descriptor with generated lineage,
  bounded geometry, and no pixels or plate text.
- `p3-5-latin-ocr-evaluation.json`: canonical W5 identifier-free generated
  aggregate evidence for exact `OCR-L0` and `OCR-L1`, with no OCR strings,
  alternatives, samples, regions, pixels, or final-test use.
- `p3-5-auxiliary-script-evaluation.json`: canonical W6 identifier-free
  aggregate evidence for exact Devanagari `OCR-D0`, deterministic `FONT-D0`
  and `FONT-G0` rendering, and zero Gujarati OCR/Tesseract execution.
- `p3-5-normalization-evaluation.json`: canonical W7 identifier-free aggregate
  contract evidence for pinned NFC/grapheme semantics, separate candidate
  calibration fixtures, mandatory abstention, and zero text/grapheme retention.
- `p3-5-consensus-evaluation.json`: canonical W8 identifier-free aggregate
  contract evidence for bounded exact-string voting, anonymous grouping,
  lifecycle/overload behavior, mandatory abstention, and zero text retention.
- `p3-5-w9-scope-proposal.json`: non-authorizing W9 closure proposal with four
  bounded options, the recommended generated-contract-only scope, exact
  continuing prohibitions, and required `D-P3.5-W9-START: A` owner statement.
- `p3-5-w9-start-authorization.json`: owner-authorized Option A bound to the
  exact planning digest, proposal hash, baseline head, actions, path allowlist,
  zero network actions, and continuing prohibitions.
- `p3-5-w9-closure-evidence.json`: canonical aggregate-only closure evidence
  for W1-W8 hashes, deterministic bounded resource replay, default-off/network
  denial, package inventory digests, zero retention, and source-only rollback.
- `p3-5-acceptance.json`: exact `D-P3.5-W10-ACCEPTANCE` owner decision bound
  to the immutable 99-file package, accepted Git commit, W9 evidence hash,
  documented limitations, and explicit non-authorization of P3.6.
- `p3-6-planning-authorization.json`: exact planning and primary-source
  research authority with downloads, runtime execution, hardware tests,
  containers, implementation, deployment, media/data access, and remote Git
  prohibited.
- `p3-6-research-sources.json`: read-only official-source findings for
  OpenVINO, ONNX Runtime, TensorRT, DeepStream, Triton, Kubernetes/NVIDIA device
  scheduling, MLPerf methodology, OCI, SLSA, and CycloneDX.
- `p3-6-owner-decisions.json`: accepted staged runtime, fail-closed scheduler,
  switchable evidence views, immutable compatibility bundle, and two-gate
  hardware strategy, with explicit continuing non-authorization.
- `p3-6-capability-profile-policy.json`: portable CPU, local accelerated, and
  capacity-target profile invariants, adaptive resource dimensions, future
  control-surface policy, and exact-manifest requirements.
- `p3-6-phase-minus-1-alignment.json`: exact shared-contract and deployment
  revisions, ownership partition, decision crosswalk, effective profile aliases,
  capacity-target/evidence-tier semantics, and unchanged execution gates.
- `p3-6-start-intent.json`: exact received `D-P3.6-START` statement, its
  non-effective state, gate snapshot, allowed planning effect, and continuing
  non-authorization.
- `p3-6-unblock-plan.json`: ordered model, sanitized inventory, capability
  manifest, and digest-bound start prerequisites without executable authority.
- `p3-6-inventory-authorization.json`: exact owner authorization, action and
  sanitization allowlists, prohibited actions, and the sealed inventory result.
- `p3-6-inventory-lab-laptop-01-r0.json`: sanitized Windows, CPU, memory,
  display-driver, fixed-storage, and installed-tool observations with no
  identifiers, network use, runtime execution, or performance claim.
- `p3-6-entry-gates.json`: accepted P3.5 baseline and owner architecture
  choices, passed `P36-G3`, recorded non-effective start intent, blocked
  model/hardware/artifact/start prerequisites, and the planning-only state.
- `p3-6-model-artifact-research-sources.json`: exact official-source metadata
  for proposed D-FINE-N and RF-DETR Small/Large checkpoints, upstream benchmark
  context, licenses, export paths, and unresolved evidence without downloads.
- `p3-6-model-artifact-research-proposal.json`: three-object, sequential,
  exact-host, exact-size, no-load quarantine proposal with unresolved storage
  and scanner bindings and every executable authority set false.
- `p3-6-model-artifact-research-package.json`: three-file immutable R0 planning
  manifest whose file SHA-256 is
  `2DEFD3262424E31E8EF04E7FEE773198BB7D75571C30D2AC27AF7683DD79A9BE`.
- `p3-6-portable-cpu-research-sources.json`: official ONNX Runtime threading,
  provider, graph-optimization, and installation findings plus existing
  repository evidence, with zero artifacts, runtime executions, or hardware
  tests.
- `p3-6-portable-cpu-profile-proposal.json`: exact Phase -1 and sanitized
  inventory bindings, conservative CPU candidate envelope, generated C1
  workload proposal, explicit unknowns, and all activation/execution authority
  false.
- `p3-6-portable-cpu-profile-package.json`: three-file immutable non-executable
  R0 planning manifest whose file SHA-256 is
  `56A7C816C108802948E24C84D481572D8EF10CA7B1EAE1AA3D389B4234A51D7B`.
- `p3-6-inventory-admission-research-sources.json`: exact local Phase -1
  inventory, placement, and deployment records plus official NIST inventory
  and zero-trust research, with no remote Git, artifact, runtime, or hardware
  action.
- `p3-6-inventory-admission-gap.json`: fifteen exact differences between
  historical P3.6 laptop R0 and the shared v1alpha1 inventory contract, with
  fail-closed admission effects.
- `p3-6-inventory-admission-decision-packet.json`: four independent A-D owner
  choices for canonical R1 strategy, freshness, trust binding, and expiry.
- `p3-6-inventory-admission-package.json`: four-file immutable non-executable
  planning manifest whose file SHA-256 is
  `CB4AC7FF7682D21B6938C50A8533B3C63D6919B4555D188C994ADA209A7B161A`.
- `p3-6-portable-cpu-profile-acceptance.json`: exact owner acceptance of the
  portable CPU planning package without profile activation, collection,
  implementation, or runtime authority.
- `p3-6-inventory-admission-owner-decisions.json`: accepted `A/A/A/A` policy
  selections for canonical R1 strategy, 24-hour freshness plus invalidation,
  digest-bound trust, and fail-closed expiry without R1 collection authority.
- `p3-6-model-artifact-research-acceptance.json`: exact metadata-only owner
  acceptance for `DET-E1/B1/A1` with acquisition, loading, scanning,
  conversion, execution, comparison, and promotion blocked.
- `p3-6-inventory-r1-research-sources.json`: official Microsoft, Python, and
  FFmpeg documentation plus exact pinned H-CAM contract evidence supporting a
  minimized local-only R1 proposal without running any collection action.
- `p3-6-inventory-r1-trust-policy.json`: proposed owned-local, network-denied,
  generated-only trust snapshot; its digest grants no admission or execution
  authority.
- `p3-6-inventory-r1-collector-spec.json`: exact one-attempt local CIM and
  metadata action allowlist, field projection, 10/60-second timeouts, explicit
  unknowns, redaction, canonical hashing, outputs, and fail-closed behavior.
- `p3-6-inventory-r1-authorization-proposal.json`: non-effective
  `D-P3.6-INVENTORY-R1-AUTH` proposal with one-attempt, 24-hour owner gate and
  continuing prohibitions.
- `p3-6-inventory-r1-authorization-package.json`: five-file immutable R0
  authorization manifest whose file SHA-256 is
  `710D52D5BC9A24A42CCB379355C062095795554F261316C37714819F0DFDDAA7`;
  the sealed package is not owner acceptance and authorizes no collection.
- `p3-6-inventory-r1-authorization.json`: exact owner acceptance record for the
  sealed package, now closed after consuming its one authorized local attempt.
- `p3-6-inventory-lab-laptop-01-r1.json`: sanitized shared-schema node inventory
  with SHA-256
  `FB061C906D1CE5F7FE3B32B70F6CA5134C486F474E2618B23884466C2E58C76F`;
  it is factual inventory, not profile activation or compatibility evidence.
- `p3-6-inventory-r1-collection-evidence.json`: bounded action outcomes,
  immutable input bindings, exact schema-validation status, and R1 hash for the
  consumed attempt; its SHA-256 is
  `3658758FCC7342B7865C7C0FD340FD408B38562BB1D365B757A74C8B6347FA72`.
- `p3-6-portable-r1-admission-gap.json`: exact static reconciliation of R1 and
  the accepted portable CPU R0 proposal against the Phase -1 resolver,
  compatibility, placement, evidence, and deployment contracts; it records 22
  remaining gaps without execution or implementation.
- `p3-6-portable-r1-decision-packet.json`: four independent A-D choices for
  refresh timing, strict resolver admission, compatibility-bundle depth, and
  generated C1 validation shape, with `A/A/A/A` recommended and unselected.
- `p3-6-portable-r1-admission-package.json`: immutable three-file non-effective
  owner-review manifest whose SHA-256 is
  `471146FAD62F926648C71ED3FE5359F74DC47E8870562E3EAE92AAD1ED5A269F`.
- `p3-6-portable-r1-owner-decisions.json`: exact owner acceptance of
  `D-P3.6-U3B-001` through `004` as `A/A/A/A` planning policy only, preserving
  all collection, profile, execution, implementation, deployment, and remote
  Git prohibitions.
- `p3-6-portable-compatibility-validation-research-sources.json`: bounded
  official ONNX Runtime and local accepted-policy source ledger with zero
  acquisition or execution actions.
- `p3-6-portable-compatibility-validation-proposal.json`: exact planning-only
  CPU runtime candidate, deterministic generated `CONTRACT` plus C1 `INFER`
  workload, hard safety gates, and immutable compatibility lifecycle.
- `p3-6-portable-compatibility-validation-decision-packet.json`: four
  independent U3C A-D owner choices with `A/A/A/A` recommended and all
  selections null.
- `p3-6-portable-compatibility-validation-package.json`: immutable
  non-authorizing four-file owner-review manifest whose SHA-256 is
  `9727D15FDAA49A0DEE06327A41E772762F3D7A2560A5F4BDEFAA6EC3FDEFCD3A`.
- `p3-6-portable-compatibility-validation-owner-decisions.json`: exact owner
  acceptance of `D-P3.6-U3C-001` through `004` as `A/A/A/A` planning policy
  only; its SHA-256 is
  `FECF3EF71F5A7550871C91BF3A58BFA9D279A88C312A4E96019EC2457821CA77`.
- `p3-6-portable-r1-supply-chain-prerequisite-research-sources.json`: bounded
  official Defender, ModelScan, PyTorch, and CycloneDX research ledger with
  zero storage, scanner, download, load, or execution actions.
- `p3-6-portable-r1-supply-chain-prerequisite-proposal.json`: exact
  non-executable storage, passive scanner, fail-closed verdict, sequential
  acquisition, ML-BOM, and passive R1 versus generated-only R2 policy proposal.
- `p3-6-portable-r1-supply-chain-prerequisite-decision-packet.json`: five
  independent U3D A-D owner choices with `A/A/A/A/A` recommended and all
  selections null.
- `p3-6-portable-r1-supply-chain-prerequisite-package.json`: immutable
  non-authorizing four-file owner-review manifest whose SHA-256 is
  `496F4A9C7D6325868283589EAA108F4A26C9CAE3F7BE49102685706CCC2AA16B`.
- `p3-6-portable-r1-supply-chain-prerequisite-owner-decisions.json`: exact
  owner acceptance of `D-P3.6-U3D-001` through `005` as `A/A/A/A/A` planning
  policy only; its SHA-256 is
  `F68BDE02AF96E3992A8C64F1F01A85CAC960F529946EA12FA4899D9EBFC197A9`.
- `p3-6-quarantine-scanner-binding-r0-research-sources.json`: exact owner `F:`
  input and accepted local-policy ledger with zero storage, scanner, download,
  runtime, media, container, or remote Git actions.
- `p3-6-quarantine-scanner-binding-r0-action-spec.json`: exact one-attempt
  `F:\HCAM-Quarantine` storage attestation, 4096-byte atomic probe, bounded
  Defender/ModelScan metadata, sanitization, timeout, cleanup, and failure rules.
- `p3-6-quarantine-scanner-binding-r0-authorization-proposal.json`: exact
  non-effective `D-P3.6-U3E-BINDING-R0-AUTH` proposal and acceptance template.
- `p3-6-quarantine-scanner-binding-r0-authorization-package.json`: immutable
  non-effective four-file owner-review manifest whose SHA-256 is
  `9978206EC0FAFA96D557FE371065B3FC5F7D38A85C74F3CC6708F873EC100B39`.
- `p3-6-quarantine-scanner-binding-r0-authorization.json`: exact accepted U3E
  owner statement and consumed single-attempt boundary.
- `p3-6-quarantine-scanner-binding-r0-result.json`: sanitized failed-closed
  storage, ACL, Defender, ModelScan, and continuing-gate result.
- `p3-6-quarantine-scanner-binding-r0-evidence.json`: bounded per-action
  evidence showing the broad-write ACL failure, skipped probe, empty-root
  cleanup, and zero retained probe content.
- `p3-6-quarantine-remediation-r1-research-sources.json`: primary-source ACL,
  Defender, WinVerifyTrust, ModelScan, and consumed-U3E evidence ledger.
- `p3-6-quarantine-remediation-r1-decision-packet.json`: six non-executable
  U3F owner choices for secure root creation, explicit principals, existing
  root policy, Defender trust, ModelScan bootstrap, and retry scope.
- `p3-6-quarantine-remediation-r1-proposal.json`: machine-readable recommended
  `A/A/A/A/A/A` sequence and current zero-action boundary.
- `p3-6-quarantine-remediation-r1-decision-package.json`: immutable U3F
  decision package whose SHA-256 is
  `9EBE27812F6E1D8D52728248B33B54A852FECCD59E0BB8B0F919925461DF4F78`.
- `p3-6-quarantine-remediation-r1-owner-decisions.json`: explicit U3F
  `A/A/A/A/A/A` owner acceptance that authorizes package preparation only.
- `p3-6-quarantine-remediation-r1-action-spec.json`: exact thirteen-action
  security-at-create, DACL verification, atomic probe, and read-only Defender
  hash/WinVerifyTrust specification.
- `p3-6-quarantine-remediation-r1-authorization-proposal.json`: non-effective
  U3G one-attempt owner-authorization proposal and exact acceptance template.
- `p3-6-quarantine-remediation-r1-authorization-package.json`: immutable U3G
  authorization package whose SHA-256 is
  `C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B`.
- `p3-6-quarantine-remediation-r1-authorization.json`: consumed U3G
  authorization record, SHA-256
  `12DBCEA9BB4C7AECDED5A42CCE2962CFBB689488F1B713990687DE876AC01070`.
- `p3-6-quarantine-remediation-r1-result.json`: sanitized failed-closed storage
  and Defender result, SHA-256
  `417AB2F17C42FD6313CC2798AC055EEF75AB16F0431BE6486619C762FA253226`.
- `p3-6-quarantine-remediation-r1-evidence.json`: bounded action, cleanup, and
  non-authorization evidence, SHA-256
  `B1D454E1F1390C0FB7D594D80197BA87DA75B5D4216CBF9177F8883E46268B4D`.
- `p3-6-quarantine-failure-analysis-r2-research-sources.json`: consumed-U3G
  facts, Microsoft ACL/PowerShell/Defender sources, confidence-qualified causal
  analysis, and zero-action research evidence.
- `p3-6-quarantine-failure-analysis-r2-decision-packet.json`: six non-executable
  U3H owner choices for allow-mask normalization, independent DACL tuples,
  Defender transport/fallback, split attempts, and runner reviewability.
- `p3-6-quarantine-failure-analysis-r2-proposal.json`: machine-readable
  recommended `A/A/A/A/A/A` sequence and continuing zero-authority boundary.
- `p3-6-quarantine-failure-analysis-r2-decision-package.json`: immutable U3H
  failure-analysis decision package whose SHA-256 is
  `19D4580E86AF04C0ABFB2D082678491F4551360A6A4C71DAE5C6481F98C32C7B`.
- `p3-6-quarantine-failure-analysis-r2-owner-decisions.json`: exact
  `A/A/A/A/A/A` planning-policy acceptance whose SHA-256 is
  `802497CFBBF2279D91170DCD777A828A1E38BBC20A7E01EE2C1A41490E35EBE3`;
  it authorizes proposal preparation only and no implementation or machine
  action.
- `p3-6-quarantine-transaction-runner-r0-source-proposal.txt`: deliberately
  non-executable, human-reviewable static transaction and default-deny dispatch
  proposal with no handler bodies or machine access.
- `p3-6-quarantine-transaction-runner-r0-source-contract.json`: proposed
  runtime, interface, static action, sanitization, evidence, and sequencing
  contract; it binds no observed runtime.
- `p3-6-quarantine-transaction-runner-r0-contract-tests.json`: twenty sealed
  generated-only contract vectors with no harness, machine facts, or execution.
- `p3-6-quarantine-transaction-runner-r0-implementation-authorization-proposal.json`:
  exact U3I implementation-only proposal and owner statement template.
- `p3-6-quarantine-transaction-runner-r0-implementation-authorization-package.json`:
  immutable non-effective U3I package whose SHA-256 is
  `712B2A424E156659E85066E1D9393CDD6E41263FAC1138588531E49FE1739AE3`;
  owner implementation authorization is accepted and execution remains blocked.
- `p3-6-quarantine-transaction-runner-r0-implementation-authorization.json`:
  exact implementation-only owner authorization whose SHA-256 is
  `CD81871C6B6F560CDC01E9D6AA919B71F9E108DEB3AEA3C04B17BAF28C60D525`.
- `tools/phase36_quarantine_transaction_runner.ps1`: contract-only static
  ten-action runner source; every machine-action handler is deliberately
  unimplemented and fails closed.
- `p3-6-quarantine-transaction-runner-r0-implementation-evidence.json`:
  generated-vector, static-source, parser, limitation, and non-access evidence
  whose SHA-256 is
  `AF3282F94095EB2368E7A91478B244F851F5B5B84C2F6FD73B667AB2D6D81291`.
- `p3-6-quarantine-transaction-runner-r0-implementation-package.json`:
  immutable implementation-evidence package whose SHA-256 is
  `71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67`;
  owner implementation acceptance is recorded, while all runtime/machine
  authority remains blocked.
- `p3-6-quarantine-transaction-runner-r0-implementation-acceptance.json`:
  exact owner acceptance of the contract-only implementation package;
  acceptance-record SHA-256 is
  `70F2EE1133648F16CA6298C25FB6C46F56AA7C88FBA97553BDD0A2F55D90C63A`.
- `p3-6-quarantine-transaction-runner-r0-runtime-binding-research-sources.json`,
  `p3-6-quarantine-transaction-runner-r0-runtime-binding-action-spec.json`,
  `p3-6-quarantine-transaction-runner-r0-runtime-binding-authorization-proposal.json`,
  and
  `p3-6-quarantine-transaction-runner-r0-runtime-binding-authorization-package.json`:
  non-effective one-attempt read-only PowerShell 7 runtime-binding proposal;
  package SHA-256 is
  `37AA6C0684E291DC66F93FE4EDBC4E6FE0FA44101E63419B382BE59EA9FCFFA9`;
  exact `D-P3.6-U3I-RUNTIME-BINDING-R0-AUTH` was recorded and consumed for one
  bounded read-only attempt.
- `p3-6-quarantine-transaction-runner-r0-runtime-binding-authorization.json`,
  `p3-6-quarantine-transaction-runner-r0-runtime-binding-result.json`, and
  `p3-6-quarantine-transaction-runner-r0-runtime-binding-evidence.json`:
  sanitized records for the successful exact PowerShell 7 and runner-source
  binding. Their SHA-256 values are respectively
  `1C3144D82EA1B41B3FBBE7E70F5BF74ED5EE5ACC709CAB272E2CBD287253648F`,
  `643226F1436CACB8E12994A6A81CEB1529E34BA5B289C1766E219A714267F7B7`,
  and `4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C`.
  The binding expires at `2026-09-01T19:36:06.820Z`; exact
  `D-P3.6-U3I-RUNTIME-BINDING-R0-ACCEPTANCE` is recorded. Neither the runtime
  nor runner was executed.
- `p3-6-quarantine-transaction-runner-r0-runtime-binding-acceptance.json`:
  exact owner acceptance of the read-only evidence; SHA-256 is
  `F19E6660FBD9545F74B8B532F6A9EB4D01ACF0543DE45CD54C8CB41C868DB54E`.
- `p3-6-quarantine-storage-r2-final-u3k-authorization-proposal.json` and
  `p3-6-quarantine-storage-r2-final-u3k-authorization-package.json`: final U3K
  preparation artifacts sealed under package SHA-256
  `4120AFF4823B1F10AC0BE902BCE7D3709EE02DFA5202A6B8A954EF83C69B837E`.
  The package is non-effective: all ten machine handlers are unimplemented,
  so `D-P3.6-U3K-STORAGE-R2-AUTH` is not requestable against it.
- `p3-6-quarantine-machine-handlers-r0-{research-sources,implementation-contract,generated-test-plan,implementation-authorization-proposal,implementation-authorization-package}.json`:
  immutable U3L machine-handler implementation proposal under
  package SHA-256
  `EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311`.
  It specifies 64 generated-only vectors and an exclusive `CreateDirectoryW`
  security-at-create correction. Exact owner implementation authorization was
  recorded and consumed without changing the proposal package.
- `p3-6-quarantine-machine-handlers-r0-{implementation-evidence,implementation-package}.json`:
  exact non-observational U3L source and generated/static evidence sealed under
  implementation package SHA-256
`79F29A6828DDBBE5E0967C4498C753DD19D547714CF8934AEFD93A9D6299B3D7`.
  The package binds the runner, pure handler, Windows adapter, 64-vector
  verifier, compatibility tests, evidence, and human review.
- `p3-6-quarantine-machine-handlers-r0-implementation-acceptance.json`: exact
  `D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE` record whose
  SHA-256 is
  `06085F3E296B450204FC0E8171314581F40853A11B0AA74161238C390A05B631`.
  Acceptance permits preparation of a separate non-effective validation and
  fresh-runtime-binding planning package only. PowerShell parsing/import/
  execution, runtime or machine observation, storage, `F:`, ACL, probes,
  scanners, acquisition, deployment, and remote Git remain unauthorized.
- `p3-6-quarantine-generated-validation-runtime-binding-r1-research-sources.json`,
  `p3-6-quarantine-generated-validation-runtime-binding-r1-plan.json`,
  `p3-6-quarantine-generated-validation-harness-r0-implementation-authorization-proposal.json`,
  and
  `p3-6-quarantine-generated-validation-harness-r0-implementation-authorization-package.json`:
  non-effective U3M planning package sealed under SHA-256
  `F92CB073156BDEFF1832D2BB0634D25005E89D58EE01CA130073F2466A0DCEE1`.
  Its source-only implementation is accepted under
  `D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE`. The next
  decision is `D-P3.6-U3N-GENERATED-VALIDATION-RUNTIME-BINDING-R1-AUTH`
  against non-effective U3N package SHA-256
  `E980CDD3CF6D560EFD832188B8659BE5C0B89C528CEDE46FF1726645CE569C2E`.
  Package preparation grants no PowerShell parsing, import, execution, fresh
  runtime observation, storage, machine, or remote Git action.
- `p3-6-quarantine-storage-r2-action-spec.json`: storage-only ten-action design
  with exact `Modify | Synchronize` normalization, independent DACL tuple
  checks, generated zero-retention probe, and no Defender actions.
- `p3-6-quarantine-storage-r2-authorization-proposal.json`: separate U3J
  planning-acceptance proposal plus the blocked future U3K execution sequence.
- `p3-6-quarantine-storage-r2-authorization-proposal-package.json`: immutable
  non-effective U3J proposal package whose SHA-256 is
  `8BC20745C4D00AED19C26D2C5FA82876DFE079427B1A6FA944E52FFA41F26398`;
  the planning design is accepted, but it is not a storage execution package
  and grants no machine authority.
- `p3-6-quarantine-storage-r2-proposal-acceptance.json`: exact planning-only
  owner acceptance whose SHA-256 is
  `6F68EB164DC662086F7444D49638FFAB95F7FF1586469BB5E5E2DC876185AAA5`.

Verify all tracked snapshots:

```powershell
uv run --locked --extra dev python tools/analytics_contracts.py check
uv run --locked --extra dev python tools/release_contracts.py check
uv run --locked --extra dev python tools/phase31_readiness.py --strict
uv run --locked --extra dev python tools/phase31_contracts.py check --require-clean-source
uv run --locked --extra dev python tools/phase31_implementation_readiness.py --strict
uv run --locked --extra dev python tools/phase32_entry_readiness.py
uv run --locked --extra dev --extra analytics python tools/phase32_implementation_readiness.py
uv run --locked --extra dev --extra analytics python tools/phase33_tracking_evidence.py check
uv run --locked --extra dev --extra analytics python tools/phase33_sbom.py check
uv run --locked --extra dev --extra analytics python tools/phase33_implementation_readiness.py --require-clean-source --require-acceptance
uv run --locked --extra dev python tools/phase34_readiness.py --strict
uv run --locked --extra dev --extra analytics python tools/phase34_c10_evidence.py check
uv run --locked --extra dev --extra analytics python tools/phase34_supply_chain.py check
uv run --locked --extra dev --extra analytics python tools/phase34_implementation_readiness.py --require-clean-source --require-acceptance
uv run --locked --extra dev python tools/phase35_readiness.py --strict --require-clean-source
uv run --locked --extra dev python tools/phase35_contracts.py check
uv run --locked python tools/phase35_latin_ocr.py check-evidence
uv run --locked python tools/phase35_auxiliary_ocr.py check-evidence
uv run --locked python tools/phase35_normalization.py check-evidence
uv run --locked python tools/phase35_consensus.py check-evidence
uv run --locked --extra dev python tools/phase35_w9_closure.py check-evidence
uv run --locked python tools/phase35_artifact_research.py --all --root 'E:\h-cam-research-cache\phase-3\p3-5'
uv run --locked python tools/phase35_artifact_inspect.py --root 'E:\h-cam-research-cache\phase-3\p3-5'
uv run --locked --extra dev python tools/phase35_runtime_research.py all --root 'E:\h-cam-research-cache\phase-3\p3-5-runtime'
```

Rewriting snapshots requires an explicit review acknowledgement:

```powershell
uv run --locked --extra dev python tools/analytics_contracts.py write --acknowledge-reviewed-change
uv run --locked --extra dev python tools/release_contracts.py write --acknowledge-reviewed-change
uv run --locked --extra dev python tools/phase31_contracts.py write --acknowledge-generated-only-evidence
uv run --locked --extra dev python tools/phase35_contracts.py write --acknowledge-reviewed-change
```

Taxonomy and geometry fixtures remain `draft`. The accepted P3.2 and P3.3
runtime slices are generated-only, default-off, and production-forbidden.
P3.4 generated-only local implementation is built, technically validated, and
accepted under `D-P3.4-ACCEPTANCE`. The PostGIS validation image remains
deployment-blocked.
These contracts do not authorize camera access, raw-media persistence, external
datasets, identity, cross-camera association, Government matching, alerts,
or deployment. P3.5 technical choices, exact artifact evidence, and restricted
runtime evidence are owner accepted. The final digest-bound `D-P3.5-START`
authorizes only the enumerated local generated-only work packages, five exact
artifacts, and reviewed external runtime with zero network access. Cameras,
media, real/private/Government data, training, Tesseract execution, deployment,
P3.6, and remote Git operations remain prohibited.
The immutable W1-W9 package is accepted under `D-P3.5-W10-ACCEPTANCE`; that
acceptance preserves every prohibition above and grants no P3.6 authority.
`D-P3.6-PLAN-AUTH` now grants only P3.6 documentation planning and read-only
primary-source research. It grants no download, artifact, runtime, hardware,
container, implementation, media/data, deployment, remote Git, or P3.7 action.
`P35-W1` adds only the reviewed ANPR contracts and fail-closed guardrails. It
does not add a generator, OCR runtime, artifact loader, API, worker, migration,
or persistence path.
`P35-W3` adds deterministic in-memory token generation and token-free sealed
split manifests. Logical holdout labels do not load fonts, render images, run
OCR/models, or widen W2 or later-package authority.
`P35-W4` adds a stdlib-only procedural geometry marker, exact ground-truth
localization, and a bounded ephemeral crop. It loads no model, font, artifact,
or media and persists neither pixels nor generated plate text.
`P35-W5` adds a code-defined generated Latin renderer and exact external
`OCR-L0`/`OCR-L1` adapters. Raw OCR exists only in memory; tracked evidence is
identifier-free aggregate data. Frozen final-test samples remain unopened.
`P35-W6` adds a closed standalone-grapheme generator, exact external
`OCR-D0`/`FONT-D0` Devanagari execution, and `FONT-G0` Gujarati rendering only.
Raw text and pixels remain ephemeral; Gujarati OCR and Tesseract remain blocked.
`P35-W7` adds raw-preserving NFC derivation, exact-runtime extended-grapheme
metrics, separate identity-calibration contract fixtures, and mandatory
abstention. It persists no OCR text, normalized text, grapheme values, or
identifiers. No quality threshold is approved.
`P35-W8` adds bounded in-memory consensus keyed only by anonymous stream,
tracker epoch, and track. Exact-string confidence-weighted votes are ephemeral;
all results abstain, and tracked evidence contains only identifier-free counts.

## P3.6 U3M Source-Only Validation Harness Implementation

`D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-AUTH` was consumed against
authorization-package SHA-256
`F92CB073156BDEFF1832D2BB0634D25005E89D58EE01CA130073F2466A0DCEE1`.
The resulting exact implementation package is
`p3-6-quarantine-generated-validation-harness-r0-implementation-package.json`
with SHA-256
`D34FF5AA704DE4A0215C0EA5FDE440B8A4311E31CCC3EA6BB77939E7D3223F6A`.
It binds the inert four-mode harness, 20 contract vectors, 64 handler vectors,
Python-only generated/reference and source-text checks, and non-observational
evidence. Exact `D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE`
is recorded in
`p3-6-quarantine-generated-validation-harness-r0-implementation-acceptance.json`
with SHA-256
`25FE4348FA7A38A7B8625463CBAEE1E2536340D4D2F7638F19404B9F76832AA9`.
The separately prepared, non-effective U3N authorization package is
`p3-6-quarantine-generated-validation-runtime-binding-r1-authorization-package.json`
with SHA-256
`E980CDD3CF6D560EFD832188B8659BE5C0B89C528CEDE46FF1726645CE569C2E`.
Its exact pending decision is
`D-P3.6-U3N-GENERATED-VALIDATION-RUNTIME-BINDING-R1-AUTH`. No PowerShell,
runtime, machine, storage, network, model, media, deployment, or remote Git
action is authorized by package preparation.

## P3.6 U3N Failure And U3O Remediation Gate

The exact U3N authorization was recorded and its single attempt was consumed.
The attempt failed closed with sanitized reason
`generated_validation_process_failed`; result SHA-256 is
`AD3A8B62105C4DF85E613024C034CECB8DB66C583E7DB49BDA1D4EB09772A8F7`
and evidence SHA-256 is
`0EAA18F17307799430955E06EF50779BF4696300DF368680CBE5CB5913E93C42`.
No retry occurred, no prohibited action was recorded, and U3K remains blocked.

Source-only analysis identified a high-confidence, runtime-unconfirmed module
autoload conflict. The non-effective R1 remediation package is sealed under
SHA-256
`17B2142E7F3502724C6653371556DA17F7231D6C56AB0421EC39725556EAA338`.
Exact
`D-P3.6-U3O-VALIDATION-HARNESS-R1-REMEDIATION-IMPLEMENTATION-AUTH` is pending.
Until it is explicitly accepted, no harness/test modification, PowerShell,
runtime retry, U3P/U3K preparation, machine/storage action, deployment, or
remote Git action is authorized.
