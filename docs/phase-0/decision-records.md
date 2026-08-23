# Decision Records

These are Phase 0 architecture decisions. They are intentionally concise and
can be promoted to full ADR files later if the repo grows.

## DR-0001: Camera Registry Is The First Core Domain

Status: accepted.

Decision: Phase 1 starts with the camera registry instead of AI inference,
operator UI, or production video recording.

Rationale:

- Every later module needs stable camera identity and source mapping.
- Sentinel probe already proves a useful metadata/state shape.
- Registry work is safe, testable, and does not require storing video.
- It gives the six-person team a shared contract before splitting work.

Consequences:

- AI and UI work should depend on registry APIs instead of direct Sentinel
  calls.
- Phase 1 implementation should import `hcam.camera_registry.seed.v1`.

## DR-0002: Sentinel Is A Reference Adapter, Not The Product Backend

Status: accepted.

Decision: Sentinel integration remains isolated as a safe reference environment
adapter.

Rationale:

- It is useful for environment validation and data-shape discovery.
- It is not an official production data contract.
- Keeping it isolated lets future official APIs replace it cleanly.

Consequences:

- Product code should use normalized registry data.
- Sentinel-specific fields remain under source/provenance sections.

## DR-0003: No Video Storage During Phase 0

Status: accepted.

Decision: Phase 0 stores only JSON metadata, camera state, summaries, and
registry seeds. It does not store CCTV footage, frames, or clips.

Rationale:

- Keeps the work inside safe reference/testing boundaries.
- Avoids accidental sensitive data retention.
- Makes the repo safe to share with collaborators.

Consequences:

- `fixtures/sentinel/*.json` remains ignored by Git.
- Future evidence storage must be designed with retention and authorization.

## DR-0004: Start As Single Repo, Keep Service Boundaries Explicit

Status: accepted by the project owner on 2026-08-18.

Decision: Phase 1 should stay in `mayankthakor227/h-cam-2.0` while maintaining
clear module boundaries for future split-out.

Rationale:

- The project is early and the team needs fast iteration.
- Premature multi-repo work increases coordination overhead.
- Clear modules preserve the option to split later.

Consequences:

- Initial backend code should be modular.
- Contracts and schemas should be stable enough for future repo extraction.

## DR-0005: Python Backend For Phase 1

Status: accepted by the project owner on 2026-08-18.

Decision: Use Python with FastAPI-style architecture for the first backend
foundation.

Rationale:

- Existing Sentinel tooling is Python.
- Camera registry import, validation, and APIs fit Python well.
- The team can validate behavior quickly on personal laptops.

Consequences:

- A later high-throughput video pipeline may still use specialized runtimes.
- Backend tests and CI should be added before expanding features.
