# P5.1 Validation Record

Status date: 2026-09-07

## Frontend Validation

The accepted local toolchain was invoked directly with Node `24.18.0` and
pnpm `11.21.0`. No NVM switch, global activation, package-manager update, or
dependency installation occurred after the accepted materialization.

| Gate | Result |
| --- | --- |
| Workspace topology | Pass: 7 applications, 16 packages, 39 dependency edges, one lockfile |
| Formatting | Pass |
| ESLint | Pass with zero warnings |
| Strict TypeScript | Pass for all workspaces and isolated Storybook configuration |
| Unit/component tests | Pass: 39 tests in 11 files |
| Coverage | Pass: 98.51% statements, 95.78% branches, 98.88% functions, 99.16% lines |
| Critical contract branch coverage | Pass: all five measured packages at or above 95% |
| Production builds | Pass: all 7 portals, 2,166,198 aggregate bytes, zero source maps |
| Storybook | Pass: 6 stories, telemetry disabled |
| Browser/accessibility | Pass: 5 expected checks, 1 project-design skip, zero unexpected or flaky results, zero axe violations |
| Visual review | Pass at desktop and mobile; no overlap or horizontal clipping |
| Dependency audit | Pass: zero informational through critical findings |
| SBOM | Pass: CycloneDX 1.6 with 372 components |

Manual screen-reader evidence remains explicitly unavailable. Reflow was
automated, while separate manual confirmation at 200% zoom remains pending.
No production accessibility claim is made.

## Python Repository Regression

The repository suite was partitioned into bounded subsystem groups after the
monolithic run exhausted `C:` and a later mixed group exceeded its family
timeout. This partition covers all 298 top-level Python test modules plus the
dedicated P5.1 verifier module.

| Group | Passed | Skipped | Subtests |
| --- | ---: | ---: | ---: |
| Analytics | 325 | 0 | 0 |
| Phase 0-2 and camera | 124 | 0 | 88 |
| Phase 3 | 2,810 | 2 | 0 |
| Phase 4 | 610 | 8 | 0 |
| Phase 5 and P5.1 verifier | 52 | 0 | 0 |
| ONVIF and capability | 116 | 0 | 0 |
| Stream and playback | 88 | 0 | 0 |
| Infrastructure, security, and other | 98 | 6 | 31 |
| **Total** | **4,223** | **16** | **119** |

All skips require the unavailable `HCAM_POSTGRES_TEST_URL` integration
environment. No failing test remains.

The first Phase 4 run produced six readiness failures because the reused main
checkout virtual environment supplied the wrong editable `hcam` package.
Pinning `PYTHONPATH` to the active worktree's `app` and repository roots made
all six pass without modifying product code, historical evidence, or tests.

## Known Limitations

- No configured PostgreSQL/PostGIS integration database was available.
- No manual screen-reader run or separately witnessed 200% zoom run occurred.
- No map renderer, tile provider, camera, media, model, inference, container,
  Kubernetes, deployment, real provider, or operational network was used.
- No Government, police, private, biometric, case, investigation, or evidence
  data was used.
- Generated build trees were preserved outside the repository on `F:` after
  local disk pressure and are deliberately excluded from Git.

Within those declared boundaries, the P5.1 technical validation result is
**pass**.
