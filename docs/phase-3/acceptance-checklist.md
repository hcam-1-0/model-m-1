# Phase 3 Acceptance Checklist

## Planning Readiness

- [x] Phase 2 owner acceptance is recorded.
- [x] Phase 3 and Phase 4 responsibilities are separated.
- [x] Required, deferred, prohibited, and high-risk capabilities are listed.
- [x] Control-plane and analytics data-plane boundaries are documented.
- [x] Versioned event-contract baseline and delivery semantics are documented.
- [x] Runtime candidates are evidence-driven and no production runtime is
  presented as selected.
- [x] Dataset, annotation, model, promotion, drift, rollback, and retirement
  governance are documented.
- [x] Security, privacy, human-review, audit, and kill-switch requirements are
  documented.
- [x] Accuracy, performance, slice, resilience, and scale validation are
  documented.
- [x] An ordered implementation backlog and six-person ownership model exist.
- [x] Current primary-source research and update caveats are recorded.
- [x] A role-based detector, tracker, and script-specific OCR portfolio is
  selected for future evaluation without claiming a production champion.
- [x] Phase 3 implementation status and its bounded authorization are recorded.

Planning status: accepted under `D-P3.0-001` on 2026-08-24.

## Implementation Entry Gate

- [x] Owner approves DR-0016, DR-0017, DR-0019, DR-0020, and DR-0021.
- [x] Owner accepts the P3.0 contracts-and-guardrails milestone scope for a
  future explicit start.
- [x] Owner explicitly instructs application implementation to start.
- [x] Tier A taxonomy and intended-use statement are owner approved; the owner
  may approve the taxonomy artifact without separate-person review.
- [ ] Exact selected model artifacts and datasets have license, provenance,
  security, and accountable-owner approval records.
- [x] Developer baseline `LAB-LAPTOP-01` is recorded for generated correctness
  and small CPU baselines only.
- [ ] Target accelerator/lab hardware for model/runtime promotion is recorded.
- [x] Synthetic-lab retention and access policy for derived analytics metadata
  is owner approved; executable enforcement remains a later entry gate.

The explicit start instruction authorizes P3.0 contract and guardrail work only.
No model download, dataset download, media capture, inference, or later milestone
may begin before its applicable taxonomy, provenance, hardware, retention, and
numeric gates are complete.

## P3.0 Progress

- [x] Model-independent analytics package boundary exists.
- [x] Assignment and four versioned event schemas are machine validated.
- [x] Deterministic generated fixtures and drift checks exist.
- [x] Strict-producer, compatible-consumer, bounds, and privacy tests pass.
- [x] Phase 3/4 alert boundary is executable in the contract.
- [x] Draft-only taxonomy, normalized geometry, and weekly time-window contract
  structures are machine validated.
- [x] Exact Tier A taxonomy, intended use, and geometry semantics are owner
  approved; site-specific geometry requires owner approval but no separate
  reviewer.
- [x] Activation-blocked assignment persistence, API, migration, revisions,
  audit, and outbox integration are implemented and locally validated.
- [x] Fail-closed runtime adapter interfaces and initial misuse/failure tests pass.
- [x] The P3.0 control-plane threat, validation-leak, migration-drift,
  authorization, audit, event, and observability test matrix is closed.
- [x] A fail-closed readiness verifier reports technical failures separately
  from ordered manual owner gates and emits a canonical documentation digest.
- [x] `mayank-admin` is the accountable owner and `mahin-eleveted` is the named
  optional reviewer; reviewer sign-off is not required for P3-G4.
- [x] `mayank-admin` explicitly accepted P3.0 as main developer and team lead;
  accountable-owner self-review is permitted for P3-G4.
- [x] P3.0 receives explicit owner acceptance after all exit evidence is reviewed.

## P3.1 Planning And Authorization

- [x] `P31-G1` P3.0 dependency, P3.1 scope, and non-authorization are explicit.
- [x] `P31-G2` Source tiers, manifest families, and generated fixtures are defined.
- [x] `P31-G3` Annotation, QA, split/leakage, metrics, and reproducibility are defined.
- [x] `P31-G4` Nine work packages, ownership, sequencing, risks, and developer
  hardware limits are defined.
- [x] `P31-G5` `mayank-admin` authorizes the bounded implementation scope under
  `D-P3.1-001`; accountable-owner review is sufficient and evidence remains
  mandatory.
- [x] Only deterministic generated metadata and programmatic assets are directly
  authorized; source tiers `S1` through `S5` retain their recorded restrictions.
- [x] External downloads, training, inference, cameras/media, P3.2, pilots, and
  deployment are explicitly excluded.
- [x] The offline planning verifier reports zero failures and zero manual gates.

Planning and authorization status: `authorized_for_implementation`. This is not
P3.1 implementation or acceptance.

## P3.1 Implementation Exit

- [x] Six contract families and canonical fixtures are implemented and tested.
- [x] Generated fixture suites and generated-only source proof pass.
- [x] Annotation, QA, grouped split, duplicate, and leakage checks pass.
- [x] Metric implementations match hand-computable deterministic goldens.
- [x] Candidate/source records expose every unresolved blocker.
- [x] Offline, GPU-free, secret-free CI drift verification is configured.
- [x] Proposed numeric gates are recorded as `proposal_only` and are not treated
  as promotion approval.
- [x] Regenerate and validate the baseline from the accepted clean source commit.
- [x] `mayank-admin` explicitly accepts the final P3.1 evidence and limitations
  in `D-P3.1-ACCEPTANCE`.

Implementation status: `accepted`. Technical failures: zero. Manual gates:
zero. P3.2 remains blocked and requires separate artifact and dataset approval.

## P3.2 Through P3.4 Accepted Milestones

- [x] P3.2 generated-only CPU detection is accepted under
  `D-P3.2-ACCEPTANCE`.
- [x] P3.3 anonymous stream-local tracking is accepted under
  `D-P3.3-ACCEPTANCE`.
- [x] P3.4 generated-only geometry and event primitives are accepted under
  `D-P3.4-ACCEPTANCE`.
- [ ] The independent PostGIS image deployment block is remediated and rescanned.

## P3.5 Planning And Owner Gates

- [x] Planning-only authorization is recorded under `D-P3.5-PLAN-AUTH`.
- [x] Existing plate/OCR candidates remain pending, blocked, and
  artifact-unresolved.
- [x] Current primary-source OCR, Unicode, Government-rule, font, and
  synthetic-data research is recorded without downloads.
- [x] Non-issuable corpus, stage contracts, normalization, abstention,
  consensus, zero-retention, resources, and generated evaluation are planned.
- [x] `D-P3.5-001` synthetic corpus and source policy selects option `A`.
- [x] `D-P3.5-002` detector and OCR portfolio selects option `A`.
- [x] `D-P3.5-003` normalization, abstention, and consensus selects option `A`.
- [x] `D-P3.5-004` privacy, resources, and evidence policy selects option `A`.
- [x] A metadata-only eight-artifact proposal is prepared with immutable source
  identities where available, bounded sizes, empty network authority, and
  unresolved SHA-256 values.
- [x] `D-P3.5-ARTIFACT-RESEARCH` authorizes exact seven-artifact quarantine
  acquisition only.
- [x] Seven artifacts have exact SHA-256, passive inspection, Defender scan,
  license evidence, model cards, and a CycloneDX artifact SBOM.
- [x] `P3.5-EXACT-ARTIFACT-REVIEW-R1` is accepted for package digest
  `54B02B80169604904C9945C1C6E692500CA8AA79253EEC27A63B4C4DB00B395C`.
- [x] `D-P3.5-RUNTIME-RESEARCH` authorizes isolated exact dependency research.
- [x] Exact Python packages, binary-wheel closure, SBOM, license metadata,
  vulnerability audit, Defender scan, and guarded imports are recorded.
- [ ] Tesseract 5 and its native dependency closure are reviewed before any
  `OCR-G0` or `OCR-G1` execution authority.
- [x] Exact runtime evidence is owner reviewed as part of final start approval.
- [x] The historical early `D-P3.5-START` statement remains preserved as
  non-effective intent at the time it was received.
- [x] Final `D-P3.5-START` is confirmed against digest
  `915F5E9246A7A656DF528DD54DA6018D7489C6875BF3A77D1A551BAD6EF9AF4D`
  and separately authorizes the exact bounded implementation allowlist.
- [x] `P35-W1` seed-only request, ephemeral token, and default-off policy
  contracts are deterministic and snapshot-verified.
- [x] `P35-W1` rejects imported token/text, file/URL/upload/bytes, camera/stream,
  owner/vehicle/watchlist, path traversal, and credential-shaped inputs without
  echoing values.
- [x] `P35-W1` evidence serialization rejects plate text, raw/normalized OCR,
  alternatives, and the complete ephemeral token model.
- [x] `P35-W3` produces exact deterministic ephemeral tokens across 20 replay
  runs using independent contract/development/validation/final-test namespaces.
- [x] `P35-W3` rejects corpus-wide token collisions, split/index errors,
  manifest tampering, holdout leakage, and count overflow.
- [x] `P35-W3` seals a token-free manifest with final test frozen, tuning
  disabled, zero accesses, and no token text or token-derived commitment.
- [x] `P35-W3` logical holdout labels are documented as non-rendering metadata;
  W2, fonts, rendering, OCR, models, media, APIs, and persistence remain blocked.
- [x] `P35-W4` creates only a bounded procedural generated frame, sealed
  ground-truth region, and model-free localization result.
- [x] `P35-W4` limits crops to `512 x 128`, keeps pixels ephemeral, and writes
  only token-free localization/crop descriptors to canonical evidence.
- [x] `P35-W4` rejects malformed frame bytes, region and quadrilateral
  tampering, digest changes, disabled execution, and production activation.
- [x] `P35-W4` focused/full-suite, package, readiness, and pre-commit validation
  is complete; clean-source evidence is regenerated after the local commit.
- [x] `P35-W5` through `P35-W8` generated-only OCR, normalization, abstention,
  and bounded anonymous consensus evidence are complete.
- [x] `P35-W9` aggregate closure, deterministic stress, offline package
  inspection, default-off/network denial, zero-retention, and rollback evidence
  are complete.
- [x] `D-P3.5-W10-ACCEPTANCE` binds the immutable 99-file package at commit
  `1611922b4f410aa0cdbce369e4f3c8838f53e19f` to digest
  `4AC016E2A23B001F338F822A25A90CA2E032947B842F14300146F0FF315B3D31`.

Current P3.5 status:
`accepted`.
Artifact and runtime evidence are accepted. Five exact artifacts and the exact
external runtime may be used for generated-only local work with zero network
actions. Tesseract OCR, training, cameras/media, real data, persistent plate
text, operational behavior, deployment, and P3.6 implementation remain
unauthorized. The later `D-P3.6-PLAN-AUTH` grants only P3.6 planning/research.

## P3.6 Planning Decision Status

- [x] `D-P3.6-PLAN-AUTH` authorizes planning and primary-source research only.
- [x] `D-P3.6-001` through `D-P3.6-005` are accepted by `mayank-admin`.
- [x] Portable CPU, local accelerated, and capacity-target profile policy is
  recorded without creating separate product contracts.
- [x] Kubernetes is bounded as an optional execution backend and runtime AUTO
  placement as advisory beneath H-CAM admission.
- [x] Balanced, Throughput, and Latency views preserve conjunctive evidence and
  every hard parity/security/lineage/freshness gate.
- [ ] `P36-G1` model champion and fallback are approved.
- [ ] `P36-G2` exact machine/runtime/driver/precision/workload manifests are
  approved.
- [ ] `P36-G4` exact artifact/dependency/container research is authorized.
- [ ] `P36-G5` exact implementation and runtime execution are authorized.
- [x] The received `D-P3.6-START` statement is preserved as non-effective
  intent and does not bypass blocked prerequisites.
- [x] `D-P3.6-INVENTORY-R0-AUTH` completed a sealed sanitized
  `LAB-LAPTOP-01` inventory without network, execution, or identifier exposure.
- [x] `P36-U2` exact official checkpoint metadata and a three-artifact,
  non-authorizing R0 proposal are sealed under package digest
  `2DEFD3262424E31E8EF04E7FEE773198BB7D75571C30D2AC27AF7683DD79A9BE`.
- [x] `D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE` accepts the planning package only.
- [x] `D-P3.6-U3B-001` through `004` accept `A/A/A/A` portable R1 admission
  planning policies without collection, profile, or execution authority.
- [x] `D-P3.6-U3C-001` through `004` accept `A/A/A/A` compatibility and
  generated C1 planning policies without acquisition or execution authority.
- [x] `D-P3.6-U3D-001` through `005` accept `A/A/A/A/A` storage, scanner, verdict,
  acquisition, and R1/R2 prerequisite policies against package digest
  `496F4A9C7D6325868283589EAA108F4A26C9CAE3F7BE49102685706CCC2AA16B`.
- [ ] An exact owner-supplied candidate quarantine root and separate bounded
  storage/scanner binding authorization exist; U3D policy acceptance alone does
  not authorize either action.
- [x] `F:\HCAM-Quarantine` was sealed as the exact U3E candidate root.
- [x] `D-P3.6-U3E-BINDING-R0-AUTH` accepted package digest
  `9978206EC0FAFA96D557FE371065B3FC5F7D38A85C74F3CC6708F873EC100B39`
  before the one bounded storage/scanner metadata attempt, which is consumed.
- [x] The U3E attempt failed closed on a broad-write ACL, skipped the atomic
  probe, removed the empty root, and retained no probe content.
- [x] U3F remediation decisions are sealed under digest
  `9EBE27812F6E1D8D52728248B33B54A852FECCD59E0BB8B0F919925461DF4F78`.
- [x] `D-P3.6-U3F-001` through `006` select `A/A/A/A/A/A` for the ACL,
  identity, root, Defender, ModelScan, and retry policies.
- [x] The exact U3G authorization package is sealed under digest
  `C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B`.
- [x] `D-P3.6-U3G-BINDING-R1-AUTH` exactly accepted the U3G digest before the
  one attempt; the authorization and attempt are consumed.
- [x] The U3G attempt failed closed at the exact DACL gate, skipped the atomic
  probe, removed the attempt-created empty root, and retained no probe content.
- [x] Defender status yielded no usable product version, so candidate hashing
  and cache-only WinVerifyTrust were skipped without executing a scanner.
- [x] The consumed authorization, result, and evidence records are bound by
  SHA-256 values `12DBCEA9...1070`, `417AB2F1...3226`, and
  `B1D454E1...8B4D`; no retry is authorized.
- [x] U3H planning-only failure analysis distinguishes confirmed U3G facts from
  high-confidence ACL-normalization and Defender-transport hypotheses without
  another machine query.
- [x] The six-choice U3H decision package is sealed under digest
  `19D4580E86AF04C0ABFB2D082678491F4551360A6A4C71DAE5C6481F98C32C7B`.
- [x] `D-P3.6-U3H-001` through `006` are explicitly selected as
  `A/A/A/A/A/A` in acceptance record SHA-256
  `802497CFBBF2279D91170DCD777A828A1E38BBC20A7E01EE2C1A41490E35EBE3`.
- [x] Selected U3H runner and storage policies are represented by separate,
  digest-bound, non-effective U3I/U3J packages. The runner package digest is
  `712B2A424E156659E85066E1D9393CDD6E41263FAC1138588531E49FE1739AE3`;
  the storage proposal-package digest is
  `8BC20745C4D00AED19C26D2C5FA82876DFE079427B1A6FA944E52FFA41F26398`.
- [x] `D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-AUTH` exactly accepts the runner
  package for contract-only source and generated harness implementation.
- [x] `D-P3.6-U3J-STORAGE-R2-PROPOSAL-ACCEPTANCE` exactly accepts the storage
  design; this remains planning-only and cannot authorize an attempt.
- [x] The contract-only runner source is parser-valid, all ten machine-action
  handlers fail closed as unimplemented, and all twenty generated vectors plus
  four structural/authorization checks pass without machine or network access.
- [x] `D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-ACCEPTANCE` exactly accepts
  implementation package digest
  `71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67`.
- [x] A separate non-effective runtime-binding authorization proposal is
  prepared and sealed under digest
  `37AA6C0684E291DC66F93FE4EDBC4E6FE0FA44101E63419B382BE59EA9FCFFA9`.
- [x] `D-P3.6-U3I-RUNTIME-BINDING-R0-AUTH` exactly authorized one read-only
  attempt before runtime path/version/size/hash/trust observation; that
  authorization is consumed.
- [x] The exact runtime and runner-source binding succeeded without executing
  either file. Evidence SHA-256 is
  `4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C`.
- [x] `D-P3.6-U3I-RUNTIME-BINDING-R0-ACCEPTANCE` accepts the exact evidence
  while its binding remains valid through `2026-09-01T19:36:06.820Z`.
- [x] The final U3K preparation package is sealed under SHA-256
  `4120AFF4823B1F10AC0BE902BCE7D3709EE02DFA5202A6B8A954EF83C69B837E`.
- [x] The non-effective U3L machine-handler implementation proposal is sealed
  under SHA-256
  `EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311`.
- [ ] `D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-AUTH` exactly accepts that
  package before any runner, module, generated verifier, evidence, or ledger
  implementation change.
- [ ] All ten U3K machine handlers are separately authorized, implemented,
  tested, sealed, and accepted before an executable U3K package is regenerated.
- [ ] The existing twenty contract vectors, all 64 generated handler vectors,
  exact source hashes, an accepted implementation package, a fresh runtime
  binding, a regenerated executable U3K package, and separate
  `D-P3.6-U3K-STORAGE-R2-AUTH` exist before any `F:` or ACL action.
- [ ] A Defender-only proposal is prepared only after successful storage
  evidence is separately accepted.
- [ ] An eligible exact local quarantine root and exact scanner command are
  bound in a regenerated R1 proposal before any acquisition authorization.
- [ ] The exact portable runtime/workload profile, accelerated-laptop profile,
  and capacity target are approved for `P36-G2`.

Current P3.6 status: architecture planning baseline accepted; implementation,
runtime execution, hardware tests, dashboard work, containers/Kubernetes,
media/data access, deployment, and remote Git remain unauthorized. Accepted
U3H planning selections produced sealed U3I/U3J proposals and both requested
owner statements are accepted. U3I's contract-only implementation evidence is
also accepted. Its separate runtime-binding authorization was consumed by one
successful read-only attempt, and exact evidence acceptance is recorded. The
final U3K preparation package is sealed but non-executable because all ten
machine handlers remain unimplemented. The U3L implementation proposal is
sealed and pending exact owner authorization. Source changes, generated test
execution, runner execution, another runtime observation, machine access, and
every retry remain unauthorized.

## Tier A Implementation Acceptance

- [x] Machine-validated contracts and compatibility tests pass.
- [ ] Synthetic/authorized dataset manifests and annotation QA pass.
- [ ] Numeric accuracy, calibration, latency, and throughput gates are approved.
- [ ] Portable detector, per-camera tracker, line/zone rules, and synthetic ANPR
  meet their approved gates.
- [ ] Runtime parity and C1/C10/C50 evidence are reproducible.
- [ ] Backpressure, outage, recovery, rollback, and kill-switch drills pass.
- [ ] RBAC, department isolation, audit, retention, and deletion tests pass.
- [ ] No prohibited media, biometric, credential, or sensitive telemetry data
  is found.
- [ ] Dependency, model, dataset, and artifact supply-chain reviews pass.
- [ ] Known limitations and residual risks are explicitly accepted or resolved.
- [ ] Phase 4 handoff contracts and boundary tests pass.
- [ ] Project owner explicitly accepts Phase 3.

## Separate Future Gates

Tier B/C capabilities, real-camera validation, evidence-media persistence,
cross-camera correlation, watchlists, Government integration, production
deployment, and statewide-scale claims each require separate authorization and
evidence. Phase 3 acceptance cannot approve them implicitly.
