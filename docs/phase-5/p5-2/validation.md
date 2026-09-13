# P5.2 Validation Record

Status date: 2026-09-08

## Frontend Validation

| Gate | Result |
| --- | --- |
| Toolchain | Pass: exact Node 24.18.0 and pnpm 11.21.0 binding |
| Workspace | Pass: 8 applications, 19 packages, 62 internal dependency edges, one lockfile |
| Formatting | Pass |
| ESLint | Pass with zero warnings |
| Strict TypeScript | Pass for all workspaces |
| Unit/component tests | Pass: 68 tests in 11 files |
| Coverage | Pass: 98.90% statements, 97.29% branches, 99.35% functions, 99.49% lines |
| Critical branch coverage | Pass: command, authorization, contracts, GIS admission, and renderer packages meet the 95% gate |
| Production builds | Pass: all 8 portals, 5,514,111 aggregate bytes, zero source maps |
| Bundle policy | Pass: generated marker policy, no stream locator, and no source-map violations |
| Storybook | Pass with telemetry disabled |
| Browser/accessibility | Pass: 15 Edge checks, 1 intentional desktop skip, zero unexpected/flaky results, zero axe violations |
| Dependency audit | Pass: zero findings at every severity |
| SBOM | Pass: CycloneDX 1.6 with 426 components |
| Source manifest | Pass: 198 bounded frontend source files |

Desktop and mobile visual captures show the Command and GIS workspaces without
blank rendering, incoherent overlap, horizontal clipping, or loss of the
authoritative table. The GIS source-state filter, fit-to-generated-extent,
selection synchronization, renderer fallback, mobile navigation, separate
loopback window, reduced motion, and forced-colors paths were exercised.

## Repository Regression

The complete existing Python repository suite, excluding only the not-yet-
sealable P5.2 exit-verifier test, passed in one local run:

- **4,223 passed**;
- **16 skipped**, all requiring unavailable `HCAM_POSTGRES_TEST_URL`;
- **119 subtests passed**;
- **0 failed**;
- one known Starlette/httpx deprecation warning.

The dedicated P5.2 exit verifier is executed after the non-effective evidence
package is generated and is recorded separately from the existing-suite count.
Temporary and bytecode output was directed to `F:/HCAM-Task-Storage`.

## Limitations

- PostgreSQL/PostGIS integration was not configured.
- Manual screen-reader evidence and separately witnessed 200% zoom evidence
  remain unavailable; no production accessibility claim is made.
- No real provider, tile, network feed, camera, media, Government/private data,
  model, inference, hardware capacity, operational action, container,
  Kubernetes runtime, deployment, or remote Git operation was used.

Within those declared generated-only boundaries, P5.2 technical validation is
**pass**.
