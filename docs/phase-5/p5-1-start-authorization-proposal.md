# P5.1 Start Authorization Proposal

Status date: 2026-09-06

Status: non-effective; exact owner authorization required

Package: `P5.1-START-R0`

Package SHA-256:
`3B4A0CDD44185A94E7C04FB9038032EDDB1EB145E3C551A5A12BA81BD4A2A66E`

Bound-input digest:
`4C44F600C3BAB1D7D997391BDF880AC2BD3CBEDA565A5DF274F5753B381DCFE2`

Machine-readable package:
[`p5-1-start-authorization-package.json`](../../contracts/phase-5/p5-1-start-authorization-package.json)

## Purpose

This package is the proposed implementation gate for P5.1 Shared Application
Foundation. It binds the accepted `P5.1-PLANNING-R1` architecture, the exact
`B/A/A/A/A/A/A/A/A/A/A/A` owner profile, P5.0 acceptance, the Gujarat GIS
parity-first no-downgrade contract, and the existing generated-only planning
documents.

The package is not effective until the owner accepts its exact SHA-256. Its
preparation does not authorize implementation, dependency activity, build or
runtime execution, commit, or remote Git.

## Proposed Effect

Exact acceptance would authorize one bounded local implementation sequence:

1. Record the exact start decision and create one local planning/start
   checkpoint commit without push.
2. Verify an already installed Node 24.x LTS and pnpm 12.x toolchain. Stop if
   either approved runtime lane is unavailable.
3. Resolve only the package allowlist through the official npm registry,
   produce exact integrity, engine, peer, license, advisory, SBOM, provenance,
   and lockfile evidence, and install with lifecycle scripts disabled.
4. Implement the eight frozen P5.1 workstreams under the isolated `frontend/`
   workspace and the bounded contract, fixture, test, evidence, and status
   paths.
5. Run local generated-only lint, type, unit, component, story, build, browser,
   security, accessibility, and complete repository regression validation.
6. Perform at most twelve in-scope remediation, validation, and reseal cycles.
7. Create local checkpoint commits without push and prepare a separate
   non-effective P5.1 exit-acceptance proposal.

## Frozen Workstreams

| Workstream | Scope | Weight |
| --- | --- | ---: |
| P5.1-W1 | Workspace, independent builds, dependency policy, lockfile, and supply-chain evidence | 1.5 |
| P5.1-W2 | Shared shell, navigation, routing, responsive behavior, and window contracts | 1.5 |
| P5.1-W3 | Design system, semantic controls, accessibility, themes, stories, and visual baselines | 1.5 |
| P5.1-W4 | Typed API, runtime schemas, safe errors, GIS contracts, and playback contracts | 1.5 |
| P5.1-W5 | Session, CSRF, reauthentication, authorization, department, and capability context | 1.5 |
| P5.1-W6 | Server state, concurrency, invalidation events, polling, and degraded states | 1.5 |
| P5.1-W7 | English/Gujarati/Hindi, time projection, resource profiles, URL state, and preferences | 1.5 |
| P5.1-W8 | Observability, source-adoption evidence, validation, readiness, and owner acceptance | 1.5 |

The frozen P5.1 total remains 12 points. No scope or weight rebaseline is
introduced by this package.

## Workspace Boundary

The implementation workspace is isolated under `frontend/`:

- seven independently buildable applications: Command, Operations,
  Intelligence, Investigation, Evidence, Admin, and Security;
- H-CAM-owned packages for shell, navigation, tokens, UI, contracts, API,
  session, query policy, event invalidation, capabilities, localization, GIS
  contracts, playback contracts, observability, fixtures, and test support;
- bounded scripts, tests, evidence, Phase 5 contracts, generated fixtures, and
  documentation;
- one additive frontend CI workflow without changing the existing Python CI;
- four existing files may change only for Phase 5 navigation, status,
  implementation evidence, and exact progress.

The package sets file-count, byte-count, extension, canonical-path, reparse,
and generated-artifact bounds. Existing backend source, migrations, Python
dependencies, accepted evidence, and untracked local output remain outside the
implementation scope.

## Dependency Gate

The package does not grant broad package-manager access. After exact start
acceptance, resolution is limited to the named runtime and development package
allowlists and `https://registry.npmjs.org/`.

- React and React DOM must resolve together in stable `19.2.x`.
- React Router must resolve in stable `8.3.x`.
- Every other package must resolve to one stable non-prerelease exact version
  in its selected current major and satisfy all peer and engine constraints.
- Exact metadata, integrity, license, advisory, and provenance results must be
  recorded before materializing dependencies.
- Installation must use the frozen lockfile, ignore lifecycle scripts, and
  disable Playwright browser downloads.
- Git, file, HTTP, tarball, alternate-registry, private-package, credential,
  lifecycle-script, native-build, unknown-license, and unresolved high or
  critical vulnerability paths stop closed.

No GIS renderer, media transport, camera protocol, runtime federation,
database client, broker client, model client, provider SDK, analytics,
advertising, replay, or fingerprinting dependency is allowed in P5.1.

## Runtime And Data Boundary

Local application and browser validation would use deterministic generated,
non-issuable fixtures and a loopback-only fixture service. A compatible
already installed browser may be used; browser download is not authorized.

No map or tile service, provider, camera, ONVIF endpoint, stream, media,
Government or private data, model, inference service, broker, telemetry
backend, database, container, Kubernetes cluster, or deployment target may be
contacted or executed.

## Acceptance Gates

Technical completion requires all eight workstream evidence sets, independent
portal builds, strict type and runtime-schema checks, session and CSRF tests,
department and capability denial tests, event/HTTP authority checks, all
required UI states, complete English/Gujarati/Hindi catalogues, safe-low
functional completeness, GIS parity without a renderer, playback contracts
without media runtime, minimized telemetry, no imported final-ui source,
generated-only fixtures, coverage thresholds, supply-chain evidence, full
repository regression, and clean-source reproducibility.

Automated accessibility evidence cannot replace manual review. Any incomplete
manual keyboard, zoom, contrast, reduced-motion, screen-reader, or workflow
review remains explicit and prevents final P5.1 acceptance.

## Exact Progress

- P5.1 planning acceptance: **100.0000%**, change **+100.0000 percentage
  points** from pending to accepted.
- P5.1 product: **0/12 (0.0000%)**, change **+0.0000 percentage points**.
- Phase 5 product: **8/100 (8.0000%)**, change **+0.0000 percentage points**.
- Maximum before separate exit acceptance: P5.1 **10.5/12 (87.5000%)** and
  Phase 5 **18.5/100 (18.5000%)**.
- After exact exit acceptance: P5.1 **12/12 (100.0000%)** and Phase 5
  **20/100 (20.0000%)**.

Preparation and acceptance of this start package award no product points.

## Owner Authorization Statement

Accept only if both digests above match the local files exactly:

Normalized statement bytes: `847`

Normalized statement SHA-256:
`381A09196A9E742EB15ED485EED8EB16429C1F12A543BD3652EE12F8A7EB8C8B`

```text
D-P5.1-START: I, mayank-admin, accept P5.1 start package P5.1-START-R0 with SHA-256 3B4A0CDD44185A94E7C04FB9038032EDDB1EB145E3C551A5A12BA81BD4A2A66E and bound-input digest 4C44F600C3BAB1D7D997391BDF880AC2BD3CBEDA565A5DF274F5753B381DCFE2 and authorize its exact bounded local generated-only Shared Application Foundation implementation scope, guarded allowlisted frontend dependency resolution and lockfile creation, source and test implementation, build and browser validation, evidence generation, and local checkpoint commits without push. This does not authorize source import, unapproved dependencies or network access, backend API routes or migrations, maps, tiles, providers, cameras or media, Government or private data, models, datasets, artifacts or inference, operational actions, containers, Kubernetes, deployment, P5.2, or remote Git.
```

Until that exact statement is accepted, every proposed effect in this document
remains closed.
