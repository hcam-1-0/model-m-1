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
- [ ] `D-P3.5-001` synthetic corpus and source policy is owner selected.
- [ ] `D-P3.5-002` detector and OCR portfolio is owner selected.
- [ ] `D-P3.5-003` normalization, abstention, and consensus is owner selected.
- [ ] `D-P3.5-004` privacy, resources, and evidence policy is owner selected.
- [x] A metadata-only eight-artifact proposal is prepared with immutable source
  identities where available, bounded sizes, empty network authority, and
  unresolved SHA-256 values.
- [ ] `D-P3.5-ARTIFACT-RESEARCH` authorizes exact quarantine acquisition only.
- [ ] Exact artifact/source manifests are reviewed and owner approved.
- [x] The exact early `D-P3.5-START` statement is preserved as non-effective
  intent with empty artifact and network allowlists.
- [ ] `D-P3.5-START` is confirmed against the exact reviewed packet and
  separately authorizes bounded implementation.

Current P3.5 status: `ready_for_owner_decisions`. Early start intent grants no artifact,
dataset, generation, training, inference, product code, media, real-plate,
storage, operational, or deployment authority.

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
