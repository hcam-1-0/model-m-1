# P5.1 Toolchain Amendment R0

Status date: 2026-09-06

Status: non-effective; exact owner acceptance required

Package: `P5.1-TOOLCHAIN-AMENDMENT-R0`

Package SHA-256:
`70494C243226BE574C6D779D7C03BA9287B3260F278B74B78ADA4D395FE959C6`

Machine-readable package:
[`toolchain-amendment-r0.json`](../../../contracts/phase-5/p5-1/toolchain-amendment-r0.json)

## Why This Amendment Is Required

The accepted `P5.1-START-R0` package requires an already installed Node 24.x
LTS and pnpm 12.x. NVM contains Node `24.18.0`, but the local pnpm inventory is
limited to cached `9.15.0`, cached `10.33.0`, and installed `11.21.0`. No pnpm
12.x package is installed or cached, and the accepted package forbids
downloading or installing the package manager.

The W1 stop condition was applied before any frontend source, dependency,
lockfile, build, or test work. P5.1 product progress remains zero.

## Narrow Proposed Change

For this local implementation only:

- use exact already installed Node `24.18.0` through its NVM path;
- use exact already installed pnpm `11.21.0` through a direct hash-bound
  invocation under Node `24.18.0`;
- do not switch NVM globally;
- do not install, download, copy, update, or globally activate Node or pnpm;
- set the repository package-manager declaration to `pnpm@11.21.0`;
- reverify the exact Node executable, pnpm metadata, entry point, bundle,
  versions, and hashes before every dependency or build stage;
- stop closed if any bound runtime property changes.

The compatibility command returned `11.21.0` under Node `24.18.0` without
network access or filesystem writes. pnpm declares Node `>=22.13`, so the
selected Node version satisfies its declared engine.

## Unchanged Controls

Every other `P5.1-START-R0` control remains unchanged, including:

- the exact runtime and development dependency allowlists;
- official npm registry only, HTTPS, same-host redirects, no credentials, and
  no alternate sources;
- exact dependency versions after resolution, integrity, peer, engine,
  license, advisory, SBOM, and provenance evidence;
- lifecycle scripts disabled, frozen lockfile, and no Playwright browser
  download;
- eight frozen workstreams and weights;
- generated-only data and loopback-only application tests;
- no final-ui source import, backend changes, map/media/camera/model runtime,
  Government or private data, operational actions, containers, Kubernetes,
  deployment, P5.2, or remote Git.

This amendment awards no product points.

## Owner Acceptance Statement

Normalized statement bytes: `641`

Normalized statement SHA-256:
`F73D6E0C192AE261D49804948CA6BF99CA22CB2BEEAA23EE5C0E3CEB2F2AFD31`

```text
D-P5.1-TOOLCHAIN-AMENDMENT-R0-ACCEPTANCE: I, mayank-admin, accept P5.1 toolchain amendment package P5.1-TOOLCHAIN-AMENDMENT-R0 with SHA-256 70494C243226BE574C6D779D7C03BA9287B3260F278B74B78ADA4D395FE959C6. For this local P5.1 implementation only, bind exact installed Node 24.18.0 to exact installed pnpm 11.21.0 using the hash-bound direct invocation and controls in that package, without download, installation, NVM switching, global activation, or package-manager self-update. Every other P5.1-START-R0 scope, dependency allowlist, security boundary, validation gate, stop condition, prohibition, and no-remote-Git rule remains unchanged.
```
