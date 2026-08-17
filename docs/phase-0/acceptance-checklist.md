# Acceptance Checklist

Phase 0 is accepted when every required gate has current evidence.

## Product And Scope

- [x] Product mission is documented.
- [x] Primary users are documented.
- [x] Product surfaces are documented.
- [x] Phase 0 non-goals are documented.
- [x] Phase 1 entry direction is documented.

## Architecture

- [x] Modular architecture baseline is documented.
- [x] Camera registry is identified as the first core domain model.
- [x] Sentinel adapter is isolated as a reference environment adapter.
- [x] Phase 1 service boundaries are documented.

## Safety And Governance

- [x] Data classes are documented.
- [x] Phase 0 no-video-storage rule is documented.
- [x] Unauthorized data access is explicitly prohibited.
- [x] Watchlist/biometric/government database integration is blocked until
  authorization and policy exist.
- [x] Audit requirements are documented for future sensitive workflows.

## Environment Validation

- [x] Sentinel metadata command exists.
- [x] Sentinel camera state command exists.
- [x] Metadata-only stream test command exists.
- [x] Snapshot command exists.
- [x] Offline summary command exists.
- [x] Registry export command exists.
- [x] Generated fixtures are ignored by Git.

## Test And CI

- [x] Python compile check is documented.
- [x] Unit test command is documented.
- [x] GitHub Actions CI exists.
- [x] Phase 0 docs are covered by structure tests.

## Phase 0 Exit Review

- [ ] Review Phase 0 docs with project owner.
- [ ] Confirm official challenge constraints and dataset rules before any
  sensitive integration.
- [ ] Decide Phase 1 repository structure and backend stack.
- [ ] Create Phase 1 implementation issues.
- [ ] Start camera registry backend implementation.
