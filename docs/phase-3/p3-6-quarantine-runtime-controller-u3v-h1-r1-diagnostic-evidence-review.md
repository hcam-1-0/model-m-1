# P3.6 U3V H1 R1 Diagnostic Source Evidence Review

## Review state

- Decision: `D-P3.6-U3V-H1-R1-DIAGNOSTIC-IMPLEMENTATION-AUTH`
- Authorization package SHA-256:
  `745C50AEB4DB61147C541F897F5E78987F64D9C3B137559F7CA811C0A6A5FD33`
- Authorization recorded: 2026-09-02
- Source implementation: complete
- Owner source implementation acceptance pending
- Runtime diagnostic package preparation: not authorized

## Implemented surface

The implementation is additive and limited to the authorized U3V source
surface. It defines a versioned diagnostic contract, a future-runtime
PowerShell H1 R1 source, a machine-disabled Python policy reference, exactly
128 generated-only mutation vectors, and one static differential test module.

The accepted historical H1 harness, controller contract, 192 controller
vectors, PowerShell controller, Python policy oracle, consumed U3T R1 records,
failure analysis, U3U decision packet, planning package, and acceptance remain
byte-exact.

## Source identities

| Artifact | SHA-256 |
|---|---|
| Diagnostic contract | `F0E41634760E3697F74EA2DEA44E7B2004392557E3167504BD69F2D78A4DC3CB` |
| PowerShell H1 R1 source | `CD868E3F06CA12AC424B2C4C221F6425FCD0DA289C527DED462121333513B1C9` |
| Python reference classifier | `9185F6DD724BC3703B402C696AC89FBE2D455BCEF2BC0C1D5C87BB4F719FFFCC` |
| Generated vector manifest | `B7D39E5A7160436D43FA4C0FE2D530CEC7DD89352949CD6EC619CD41D8639F70` |
| Static differential test | `E6DD3A1D0DF057A0A66E4C4C61109C06577D949D0954DF511DF998678EF6A87C` |
| Authorized compatibility transition | `1BE483D2D6203448C6E84AF3F28D269AC859A0A26C287ED834054C30873AF90A` |
| Amended U3V proposal transition test | `0DA6E293DE0072277B4D3A5E50C245D06A35D27A7B17C9AA4A1699EB838A9827` |

## Generated evidence

- Exactly 128 deterministic generated-only vectors are present.
- Every one of the eleven allowlisted terminal reason codes is covered.
- All eight typed diagnostic groups and all three controller reason families
  are covered.
- Every generated output is bounded to at most 4096 UTF-8 bytes.
- Output projections retain zero raw controller bytes and contain no candidate
  values, type names, candidate keys, raw projection, exception, stdout,
  stderr, environment, identity, or security material.
- The focused generated/static suite passed: 7 passed, 2 package-seal tests
  deselected before evidence assembly.
- Python-reference branch coverage is 99%, exceeding the 95% requirement.
- Ruff passed for the Python reference and static differential test.
- The contract, Python projection, and embedded PowerShell canonical projection
  are equal under duplicate-key-rejecting JSON validation.

## Compatibility amendment

`D-P3.6-U3V-COMPATIBILITY-TEST-ALLOWLIST-AMENDMENT` was recorded against
authorization package SHA-256
`745C50AEB4DB61147C541F897F5E78987F64D9C3B137559F7CA811C0A6A5FD33`
and provisional implementation package SHA-256
`489174B8FF369FA3A00BD8EB734E31F6FAF75D00D14EF28E0A7311E67FCF8F3C`.
The exact 1,703-byte statement has SHA-256
`9BE9C3F3D2BB9ABE11A84CCCE2E4DDF79B3370AF017AD9E0B56E29C2426B541E`.
Only
`tests/test_phase36_quarantine_runtime_controller_u3v_h1_r1_diagnostic_proposal.py`
was transitioned from obsolete pre-authorization state assertions to source
complete, owner acceptance pending, and runtime gates closed. The focused
proposal and implementation package validation passed: 16 passed.

## Execution boundary

PowerShell was not parsed or executed. The PowerShell H1 R1 source was not
imported or dot-sourced. The machine-disabled Python reference used only
generated in-memory fixtures and had no filesystem runtime, registry,
environment, network, native API, subprocess, machine-controller, or fallback
surface.

No runtime, manifest, hardware, machine, storage, `F:`, `B:`, ACL, probe,
cleanup, Defender, scanner, network, download, artifact, model, inference,
camera, media, data, container, Kubernetes, profile activation, deployment,
another attempt, U3K, or remote Git action occurred or became authorized.

## Remaining gate

The sealed implementation package requires separate exact owner acceptance.
Only after that acceptance may a separate non-effective runtime diagnostic
authorization proposal be prepared. Source completion does not authorize that
proposal’s execution, another attempt, or U3K.
