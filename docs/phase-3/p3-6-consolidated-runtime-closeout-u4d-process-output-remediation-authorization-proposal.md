# P3.6 U4D Process-Output Remediation Authorization Proposal

## Purpose

This non-effective proposal defines a source-only remediation for the consumed
consolidated runtime-closeout R1 failure. The accepted evidence proves that the
package, runtime trust, fixed-parent set, and all source bindings passed. It
proves only that one or more output predicates failed at the first generated
validation child; it does not distinguish stdout overflow, nonzero stderr,
exit status, framing, JSON, schema, or result-identity failure.

## Accepted Direction

`D-P3.6-U4C-CLOSEOUT-R1-FAILURE-ANALYSIS-DECISIONS` selected `A/A/A/A/A`:

- split process start, timeout, exit, stdout, stderr, framing, JSON, schema,
  and identity failures into bounded sanitized reasons;
- replace the unsealed in-memory child driver with an additive,
  source-controlled and hash-bound PowerShell validation harness;
- emit exactly one UTF-8 JSON line through `System.Console.Out`, with no BOM,
  CLIXML, or non-data stream output and with zero stderr;
- require at least 320 generated/static vectors before another runtime attempt;
- retain two gates: this source-build authorization and a later exact-digest
  runtime-closeout R2 authorization.

No raw stdout, stderr, exception, fixture, path, environment, identity, or
security material may be retained, including hashes of raw streams.

## Proposed Source Surface

If the exact package is authorized, U4D may create seventeen additive paths:
the process-output contract, PowerShell child harness, machine-disabled Python
reference, generated vectors, five generated/static test modules, source
evidence and review, and a non-effective R2 action spec and authorization
package. Work is bounded to six in-scope revision and reseal cycles.

The only historical compatibility edit is
`tests/test_phase36_consolidated_runtime_closeout_authorization_proposal.py` at
pre-edit SHA-256
`E8001AFD5B558EEBA51A0714C02DCD2C9F22B65F93A74AF4D3323130983B82EF`.
It may replace only the obsolete assertion that all seven future outputs are
absent. The replacement must preserve the seven exact unique paths, require
the consumed authorization/result/evidence to exist, and require the Phase 3
acceptance plus three U3K outputs to remain absent.

## Validation Boundary

Python may run generated fixtures and a machine-disabled reference plus
source-text, cross-language, hash, JSON, Ruff, and diff checks. It may not use
filesystem runtime discovery, registry, environment, network, native APIs,
subprocesses, a machine controller, or fallback behavior. PowerShell may not
be parsed, imported, dot-sourced, or executed during the source build.

The source build must preserve all sixteen immutable accepted inputs
byte-exact and must demonstrate at least 95% branch coverage for the Python
reference. Any path, scope, immutable-hash, or six-cycle failure stops closed.

## Later Runtime Gate

A successful source build may prepare one non-effective, final-digest-bound
`D-P3.6-CONSOLIDATED-RUNTIME-CLOSEOUT-R2-AUTH` package. It grants no runtime
authority. The owner must receive and explicitly authorize its final digest
before any PowerShell execution or machine observation. R2 permits at most one
attempt, and U3K can begin only after all 500 generated cases are accepted in
that same authorized attempt.

## Current Gate

`D-P3.6-U4D-PROCESS-OUTPUT-REMEDIATION-IMPLEMENTATION-AUTH` is pending. No
harness, contract, vector, test, evidence, or product implementation is
authorized. PowerShell execution, Python machine access, runtime or hardware
observation, storage, `F:`, `B:`, scanners, network, downloads, artifacts,
models, inference, cameras, media, private or Government data, containers,
Kubernetes, deployment, retry, U3K, Phase 3 closeout, commit, push, and remote
Git all remain blocked.
