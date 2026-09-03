# P3.6 U4B Outer Attempt Controller R0 Source Implementation Authorization Proposal

## Purpose

This non-effective proposal defines a future additive, package-bound outer
attempt controller to close the reproducibility and diagnostic gaps exposed by
the consumed U3Z R1 `binding_failed` result. It does not implement or execute
that controller.

## Accepted Direction

`D-P3.6-U4A-U3Z-R1-FAILURE-ANALYSIS-DECISIONS` selected `A/A/A/A`:

- add a source-controlled outer attempt controller without modifying accepted
  U3Y or U3Z artifacts;
- use bounded typed stage and fixed-parent-index reasons;
- materialize exactly three ordered typed parent records and compute all-valid
  through an explicit fixed-length reduction;
- require source acceptance, generated controller validation, and only then a
  separately authorized new runtime attempt.

The accepted failure analysis does not claim that a parent directory, runtime
binary, U3Z harness, or controller R1 is defective. The previous evidence only
localizes failure to fixed-parent-set validation in the unbound outer attempt
controller.

## Proposed Controller

If separately authorized, the additive controller will use a typed default-deny
state machine for one operation: `generated_contract_validation_v1`. Its eleven
ordered stages cover authorization, fixed parents, runtime identity and trust,
source preflight, process bounds, result validation, postflight identity, and
evidence sealing. Unknown operations, stages, fields, or reason codes terminate
closed.

The parent-set contract contains exactly three records with indexes `0`, `1`,
and `2`. Each record exposes only booleans and an allowlisted reason. The
controller may not retain paths, ACLs, ownership, raw attributes, exceptions,
process output, environment, identity, or security material.

## Future Implementation Surface

If exact digest-bound authorization is later received, implementation is
limited to eleven additive artifact paths: one runtime-independent contract,
one PowerShell source, one machine-disabled Python reference, one generated
vector manifest, four generated/static test modules, source evidence, a sealed
implementation package, and a human evidence review. Existing synchronization
is limited to the explicitly listed canonical ledgers, documentation indexes,
and LF registry.

Source evidence requires at least 384 generated vectors and at least 95% branch
coverage for the machine-disabled Python reference. PowerShell may not be
parsed, imported, dot-sourced, or executed during source implementation.

## Later Gates

Source implementation must be sealed and separately accepted. Generated-only
PowerShell controller validation then requires another package and exact
authorization. A new runtime attempt requires successful accepted generated
validation plus another digest-bound authorization. U3K remains later and
separate.

## Current Gate

`D-P3.6-U4B-OUTER-ATTEMPT-CONTROLLER-R0-IMPLEMENTATION-AUTH` is pending. This
proposal grants no source, contract, vector, test, model, or product
implementation; no PowerShell execution; no Python machine access; no runtime,
machine, storage, network, scanner, model, camera, media, private or Government
data, container, Kubernetes, deployment, retry, U3K, commit, push, or remote Git
authority.
