# P5.3 Validation Record

Status date: 2026-09-08

## Frontend Validation

| Gate | Result |
| --- | --- |
| Toolchain | Pass: exact Node 24.18.0 and pnpm 11.21.0 binding |
| Workspace | Pass: 8 applications, 22 packages, 73 internal dependency edges, one lockfile |
| P5.3 formatting | Pass |
| ESLint | Pass with zero warnings |
| Strict TypeScript | Pass for all workspaces |
| Unit/component tests | Pass: 123 tests in 53 files |
| Coverage | Pass: 98.14% statements, 97.03% branches, 97.37% functions, 98.56% lines |
| Critical branch coverage | Pass: every critical P5.3 domain and media-adapter file meets the 95% gate |
| Production builds | Pass: all 8 portals, 6,087,117 aggregate bytes, zero source maps |
| Operations split | Pass: 278,555-byte initial JavaScript and 575,516-byte deferred HLS chunk |
| Storybook | Pass: 14 stories with telemetry disabled |
| Browser/accessibility | Pass: 27 Edge checks, 1 intentional skip, zero unexpected/flaky results, zero axe violations |
| Synthetic media | Pass: C1/C4/C10, 10 streams, 30 renditions, 480 generated assets |
| Dependency audit | Pass: zero findings at every severity |
| SBOM | Pass: CycloneDX evidence with 427 components |
| Source manifest | Pass: 263 bounded frontend source files |

Desktop and mobile captures show admitted and held tiles, authoritative stream
status, stable media dimensions, pause/resume/release controls, and responsive
navigation without blank rendering, incoherent overlap, or horizontal
clipping. Browser checks cover HLS playback, admission, recovery, profile
changes, fallback, teardown, storage absence, reduced motion, forced colors,
and accessible non-video state.

## Generated Media

Synthetic media was created only from `lavfi_testsrc2`, without audio or input
media. The run produced 238,578,298 bytes across 480 assets, generated an exact
manifest, and removed the binary assets after evidence collection. No real
camera, provider, network stream, private data, or Government data was used.

## Repository Regression

The complete local Python repository suite passed after the authorized P5.2
historical-readiness test transition:

- **4,232 passed**;
- **16 skipped**, all requiring unavailable `HCAM_POSTGRES_TEST_URL`;
- **119 subtests passed**;
- **0 failed**;
- one known Starlette/httpx deprecation warning.

The P5.2 transition changes only mutable current-checkout assumptions in its
test. Accepted P5.2 source, evidence, package, digests, and behavior remain
unchanged and are checked through the accepted technical commit's Git objects.

## Formatting Baseline

The scoped P5.3 formatter gate passes. The repository-wide formatter reports
five pre-existing generated JSON files from P5.1/P5.2; they were not modified
because they are accepted historical evidence. This warning is recorded and
does not hide a P5.3 formatting failure.

## Limitations

- PostgreSQL/PostGIS integration was not configured.
- Manual screen-reader evidence and separately witnessed 200% zoom evidence
  remain unavailable; no production accessibility claim is made.
- C1/C4/C10 are deterministic generated validation sizes, not hardware or
  production capacity claims.
- WHEP is default-off and tested only through generated contracts.
- No real-camera, transport, codec, latency, provider, or deployment claim is
  made.
